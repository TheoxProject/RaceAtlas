# Lot 3 — Utilisation locale et modèle d'audit

Ce lot ajoute une bibliothèque Python d'import **explicite et hors réseau**, sans tâche planifiée, client FFC live ou géocodeur réseau. `synchronize(engine, batches, ...)` possède sa connexion et ses transactions ; il n'accepte pas de Session appelante et ne commite aucun travail externe. Cette entrée de développement refuse les hôtes PostgreSQL autres que localhost/127.0.0.1/::1. Les migrations et tests ci-dessous restent réservés aux bases locales jetables.

## Vérifier sous Windows

Depuis la racine, réutiliser l'environnement indiqué dans `docs/coordination/CURRENT_STATE.md` :

```powershell
$python = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL='postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB='1'
$env:PLAYWRIGHT_BROWSERS_PATH='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
& $python -m pytest -q
& $python -m ruff check raceatlas migrations tests/backend
& $python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
```

Migration head `8a95eb41f220` : ajoute un repère interne de présence/absence à SourceRecord, après `65107930ec01` inchangée. Backfill des audits réels et réparation conservatrice des anciennes présences erronées ; aucune modification du contrat public ni de sa sérialisation. Les fixtures pytest exécutent upgrade/check/downgrade/upgrade/check et réinitialisent les tables d'audit/cache et métier. Ne jamais pointer une base à conserver. Pour une autre base **locale de développement préalablement autorisée**, appliquer la migration par la commande Alembic documentée au lot 1 ; aucun démarrage ne migre implicitement.

## Construire un import synthétique

Exemple Python à exécuter à la racine avec une base locale jetable migrée. Il ne télécharge rien et ne réinitialise rien :

```python
from datetime import date, datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine
from raceatlas.ffc import WindowRequest, parse_calendar, parse_race
from raceatlas.sync import WindowBatch, synchronize

now = datetime.now(timezone.utc)
calendar = parse_calendar(
    Path('fixtures/ffc/calendar.synthetic.html').read_text(encoding='utf-8'),
    source_url='https://competitions.ffc.fr/calendrier/', checked_at=now,
    requested=WindowRequest(date(2026, 11, 10), date(2026, 11, 16), '26'),
)
# Deux identités entièrement fictives ; le même corps synthétique sert d'exemple.
body = Path('fixtures/ffc/race.synthetic.html').read_text(encoding='utf-8')
details = tuple(parse_race(
    body,
    source_url=f'https://competitions.ffc.fr/calendrier/competition/{key.season}/{key.race_number}/synthetic/',
    checked_at=now,
) for key in calendar.keys)
engine = create_engine('postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test')
try:
    result = synchronize(engine, [WindowBatch(calendar, details)], checked_at=now, synthetic=True)
    print(result)
finally:
    engine.dispose()
```

Répéter le même import conserve les IDs, scopes/règles et révisions métier, mais ajoute un audit d'exécution. Les tokens aléatoires, dates de contrôle, slug et zones étrangères au métier ne participent pas à l'empreinte. Espaces de présentation normalisés ; labels source/règles conservés comme signaux d'ambiguïté, jamais comme preuve de rapprochement.

## Transactions, identité et reprise

- `import_run` identifie une exécution et sa version parseur, provenance synthétique, horodatages/verdict et compteur de présences à vérifier. `import_window` conserve les fenêtres demandées/effectives, département, compteurs et diagnostics ; `import_item` décrit chaque résultat et les faits minimaux nécessaires à la revue. Jamais de HTML complet ou participants.
- Verrou consultatif PostgreSQL de session : un deuxième importeur retourne `import_busy`. Les fenêtres sont committées séparément, les items protégés par savepoints. Un item en échec ne laisse pas de remplacement à moitié réalisé ; les autres faits positifs peuvent être conservés. Le fournisseur injecté ne reçoit aucune Session et ne doit pas produire d'effets externes.
- Les erreurs de parsing peuvent être transmises via `DetailFailure(key, error.diagnostic.code)`, sans message brut. Détail absent, conflit de doublons, fenêtre incohérente, référence périmée, erreur de stockage ou géocodeur restent audités. Les erreurs fournisseur sont des codes sûrs, jamais leurs exceptions/réponses. Si PostgreSQL lui-même est inaccessible ou perd la connexion, l'écriture d'audit peut devenir impossible : l'exception est propagée, aucune réussite garantie.
- L'inférence d'absence est **différée jusqu'à réussite du périmètre entier du run**. Présence globale dédupliquée entre fenêtres ; clé observée ailleurs jamais absente. Une fenêtre vide plus ancienne qu'une observation existante ne permet aucune conclusion. Ensuite seules les courses de la période/département demandés passent éventuellement à `source_presence=to_verify`, jamais à `cancelled` ; une annulation sourcée reste préservée. La couverture technique ne prouve pas l'exhaustivité intrinsèque FFC.
- `source_revision` contient un instantané métier minimal, son empreinte et la référence/version source. Aucun nouveau snapshot si les faits sont identiques ; un retour ultérieur à d'anciens faits crée une vraie nouvelle révision. Modifier titre/date/groupement ne modifie pas les IDs internes.
- Scopes/règles identiques : graphe existant laissé en place, aucun rapprochement par rang. Tout changement/réorganisation ambigu est une observation `needs_review` dans l'audit, sans remplacer le graphe historique. Un changement réellement attesté exige une `IdentityAttestation` complète et bijective ; aucune règle transférée entre scopes. Une observation partielle ne peut pas vider les faits connus.
- `AliasProof` lie une nouvelle saison/numéro à une course existante, avec clé/révision attendues, preuve non vide et date de décision. Les anciennes références restent dans `source_alias` ; la clé principale change uniquement sur cette décision explicite. URL/date de contrôle restent celles de la dernière observation acceptée, qui peut passer par une ancienne référence conservée ; sa clé effective est aussi enregistrée dans audit item Conflit ou preuve périmée refusés. Rejouer la même décision déjà enregistrée est idempotent.
- `CompetitionProof` requiert une preuve et révision attendue ; cible existante ou retrait explicitement attesté. Les preuves de groupement/identité sont référencées dans l'audit item. Leur replay exact ne recrée pas une révision.


### Fraîcheur des preuves de présence et d'absence

`source_record.checked_at` reste le contrôle de la dernière fiche acceptée. Le nouveau `presence_checked_at` conserve le dernier contrôle pertinent de présence **ou d'absence**, même quand une course reste déjà `to_verify`. Ce repère interne n'est pas ajouté aux réponses contractuelles. Les anciens writers/seed peuvent laisser la colonne nullable ; l'importeur utilise alors checked_at comme baseline et renseigne le repère sur ses écritures. Une contrainte PostgreSQL interdit un repère de présence antérieur à la fiche.

La baseline est figée au début du run. Une observation plus ancienne ne peut ni rétablir present ni appliquer une preuve d'alias/groupement ou une localisation ; aucun appel géocodeur pour cette observation. Après une absence contrôlée, un timestamp **égal** n'est pas réputé plus récent : seul un vrai retour ultérieur rétablit la présence. Quand la course était déjà présente, les répétitions au même timestamp restent idempotentes.

Les vieux enregistrements sont des no-ops audités, jamais une autorité prêtée par un consensus planifié. Si un item suffisamment frais réussit réellement dans le même run, un ancien doublon dont les faits sont strictement identiques peut devenir `historical_duplicate` dans l'audit, sans aucune mutation. Sans cette réussite effective (timestamp futur, échec fournisseur ou stockage), l'ancien reste stale/error. Aucun changement de révision métier ou recul de fraîcheur pour un doublon. Les différents ordres de fenêtres conservent le même état.

La migration retrouve les absences dans les fenêtres réussies des runs réussis, excluant toute course positivement vue via **n'importe quel alias/fenêtre du même run**. Elle traite l'égalité conservativement uniquement lorsqu'une vraie preuve d'absence existe ; une ligne présente sans audit d'absence ne change pas d'état. Les tests exercent de vrais états pré-migration et les données conservées, sans base distante.

## Communes et cache

La localisation n'est jamais extraite du titre/slug : fournir une `LocationFact` explicitement liée à la clé source, avec nom de commune, département, preuve et code INSEE si établi. Ce choix évite d'élargir silencieusement le dialecte HTML synthétique du lot 2. Fournir un `OfflineProvider(name, version, lookup)` injecté ; aucun transport n'est livré. `lookup` renvoie zéro, un ou plusieurs `CenterCandidate` documentés. Les tests sont le seul fournisseur livré.

Le cache persistant est séparé par fournisseur/version/nom normalisé/INSEE/département. Positif 7 jours, négatif 1 jour, erreur 5 minutes ; les appels répétés utilisent le cache, l'expiration autorise une nouvelle tentative. Aucun centre pour résultat ambigu, nom/code/département incompatibles, coordonnées non finies/booléennes/inversées, précision autre que `commune_center` ou provenance inconnue. Aucun faux centre lors d'erreur ou de résultat vide. Un centre existant est conservé si le nouveau fournisseur échoue ou si la source ne fournit plus de fait de localisation. Changement de département avec centre connu : revue avant mutation, jamais FK incohérente.

Un contrôle numérique délibérément large (`longitude` 1–8, `latitude` 43–48) écarte les axes inversés et centres manifestement éloignés. **Ce rectangle n'est pas un test polygonal d'appartenance à AURA ou à un département** ; l'identité officielle et la qualité du centre reposent toujours sur la provenance explicitement fournie. Aucun jeu de limites administratives, service GIS ou fournisseur live ajouté. Deux réponses contradictoires pour le même INSEE sont mises en erreur plutôt que de déplacer silencieusement toutes les courses.

Les courses non localisées restent disponibles via l'API détail, `location=null`. Un résultat négatif est valide ; une erreur/ambiguïté de fournisseur conserve son cache/diagnostic mais ne modifie aucun fait, preuve, centre ou présence de l'item. Elle empêche les conclusions d'absence du run ; les fenêtres indépendantes réussies restent exploitables. Le renouvellement/élagage opérationnel des audits relève du lot 8 avant activation récurrente ; aucun stockage de source live ne s'accumule via ordonnanceur dans ce lot.
