# Handoff développeur — lot 3, correction 2

Branche `feature/auditable-sync`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/5. Base intégrée `f33d837844abdc51ebcafc066da3c16cb4982f34`. Checkpoint source C2 publié : `9467f30ea3ae599892b904fb514a175b952b1f3d`. Le commit contenant ce handoff final et le checkpoint constitue le candidat : relever HEAD et le comparer au distant/PR. Aucun APPROVE du nouveau candidat acquis.

## Périmètre réel livré

- Six nouvelles tables d'audit/cache/révisions/alias via migration statique `65107930ec01` ; cette migration publiée reste inchangée.
- **SourceRecord reçoit un champ interne `presence_checked_at`** et une contrainte de cohérence via nouvelle migration statique `8a95eb41f220`. Nécessaire pour distinguer dernière fiche et dernière preuve de présence OU absence. API/contrats/sérialisation publics inchangés.
- `raceatlas/sync/` : import local explicitement invoqué, transactions possédées et verrou PostgreSQL, savepoints item, audit minimal, alias/groupement/scopes attestés, empreintes idempotentes et résolution/cache communal injecté hors réseau. Aucun transport, ordonnanceur ou déploiement.
- Tests d'intégration PostgreSQL/API, contraintes et backfill pré-migration ; usage Windows dans `docs/lot-3/local-development.md`, checkpoint consolidé.

Les IDs internes restent opaques et stables. Les graphes de scopes identiques restent en place ; changement/réorganisation sans preuve en revue, jamais de rapprochement par rang, nom ou slug. Les contradictions sont comparées par identité persistante résolue avant mutation, avec preuves validées sur une baseline unique. Les nouvelles décisions concurrentes de clé principale sont mises en revue plutôt que choisies par ordre. Aucune catégorie/restriction inventée ; empreinte sans tokens/checkdates/HTML/participants.

Les fenêtres indépendantes peuvent conserver leurs faits positifs, mais l'inférence d'absence attend le succès du périmètre entier du run, présence globale dédupliquée. Absence contrôlée uniquement `to_verify`, jamais annulation ; annulation historique conservée. Audit d'exécution distinct des révisions métier. Une indisponibilité PostgreSQL peut empêcher l'audit : exception propagée sans réussite annoncée.

## Correction2 — règle de fraîcheur

La présence ne peut plus être rétablie par un snapshot antérieur à une absence contrôlée. La baseline immuable prend le maximum des dernières preuves connues ; elle est vérifiée avant tout géocodeur ou application de preuve/graphes. Une égalité avec une absence n'établit pas une présence plus récente. Une répétition d'absence avance le repère même si déjà to_verify, sans toucher au timestamp de fiche ni créer une révision métier.

Aucune autorité ne vient d'un consensus prévu. Un historique reste non mutatif ; seulement après réussite effective d'un item suffisamment frais du même run, un doublon strictement identique peut devenir `historical_duplicate` dans l'audit. Sans réussite effective, les historiques restent stale/error. Échecs timestamp futur, fournisseur ou stockage ne changent pas cette règle. Les doublons admissibles plus anciens que des écritures réussies du même run n'abaissent aucun timestamp.

Une erreur géocodeur conserve son cache/diagnostic mais **ne modifie pas l'item source**. Une autre fenêtre positive indépendante reste committable. Les centres connus sont préservés ; aucun historique ne crée de centre ou de preuve. Cette décision conservatrice remplace l'ancien comportement qui pouvait compter un item comme positif malgré l'erreur fournisseur.

Le backfill repose sur de vrais audits de fenêtres/runs réussis, excluant un positif de n'importe quel alias/fenêtre du run. Il répare les présences historiques erronées plus anciennes **ou égales** à une preuve d'absence réelle, sans altérer une présence légitime sans absence. Colonne nullable pour compatibilité seed/anciens writers, fallback checked_at ; importeur remplit le champ. Contrainte présence>=fiche. Les tests descendent réellement au schéma précédent, créent l'état antérieur, remontent et vérifient données/drift ; aucune migration distante.

## Vérifications du candidat

Environnement réutilisé : Python3.12.14, PostgreSQL17.11 uniquement `127.0.0.1:55434/raceatlas_lot2_test`, Chromium en cache. Aucun accès à la base Tester ou à une base distante. Commandes depuis racine :

```powershell
$python='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL='postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB='1'
$env:PLAYWRIGHT_BROWSERS_PATH='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
& $python -m pytest -q --tb=short
& $python -m ruff check raceatlas migrations tests/backend
& $python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
git diff --check
```

**Résultat final C2 :205/205pytest PASS en118,24s**, aucun skip (110lot3+95antérieurs dont3Chromium).86tests sync ciblés PASS en62,97s ; Ruff lint/format26fichiers PASS,26contrats PASS, diff-check PASS. Migration aller-retour, backfill sur données/audits pré-migration, contraintes SQL et API/schéma réellement exécutés. Source C2 publiée au9467f30e : CI intermédiaire verte https://github.com/TheoxProject/RaceAtlas/actions/runs/42899106770 ; ce résultat ne remplace pas CI/revue du commit documentaire final.

Frontend/dépendances inchangés dans C2 ; revue précédente vérifiait3tests React avec `--pool=threads --maxWorkers=1` après timeout du fork local, lint/build/pip PASS. Aucun changement de configuration produit pour ce runner. Les parcours Chromium historiques sont dans la suite globale.

## Historique succinct et limites

- Premier lot3 :160tests PASS, Tester REQUEST CHANGES F1/P1 sur92059d3 (contradiction entre alias d'une même course). C1 au228074c :180tests PASS ; Tester confirme F1 corrigé puis REQUEST CHANGES F2/P1 sur fraîcheur présence/absence. CI antérieures vertes mais périmées pour ce candidat.
- C2 : ajout du repère durable et gardes ci-dessus,25régressions. Premier SQL local utilisait un alias réservé, rollback puis correction ; tests ont révélé l'alignement avant flush des scopes et le replay historique, corrigés avant86tests ciblés PASS. Ces résultats ne remplacent pas la nouvelle revue.
- Rapports/repros conservés dans `.local-tools/tester-report-lot3-228074c.md`, `tester-presence-freshness-lot3-c1.py`, `tester-failed-fresh-alias-lot3-c1.py` ; ne pas exécuter aveuglément les scripts de revue ciblant la base du Tester.

Les centres sont validés via LocationFact explicite, INSEE/département/provenance et cache versionné positif7j/négatif1j/erreur5min. Rectangle numérique large lon1–8/lat43–48 : garde de plausibilité, **pas preuve polygonale/GIS**. HTML synthétique et droits/compatibilité FFC live restent ouverts. Rétention et exploitation récurrente à valider au lot8 ; aucun workflow actif.

Décision propriétaire futur lot5 : **Altitude2.5D initial, Summit3D à la demande**, explicitement résolue. Aucun arbitrage produit en attente. Silence jamais accord. Pas d'achat, collecte, service live, mutation production, déploiement ou release finale.

Tester doit relever le SHA exact, confirmer propreté, puis vérifier sa base locale jetable `raceatlas_lot2_review` uniquement (migrations/reset expressément autorisés là). Ne pas relancer initdb. Revue/CI exactes requises ; preuves finales dans PR sans modifier le SHA gelé. Maximum3cycles de correction, cette livraison est C2. Aucun APPROVE par épuisement.

Tous les tests développeur sont terminés ; aucun processus de test actif, PostgreSQL local laissé actif. Éditions suivies arrêtées après le commit/push final. Scan UTF8/mojibake des documents modifiés effectué avant gel.
