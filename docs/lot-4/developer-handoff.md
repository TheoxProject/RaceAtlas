# Handoff développeur — lot4

Branche `feature/catalog-filters`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/6, base `48a2c3766276c92b2074139847c95e8d6a7b3916`. Dernier jalon code publié/testé **9364442f4c6034b389dcac80cd46105d045b687e**. Le commit contenant ce handoff et le checkpoint final est le candidat : relever son SHA exact et le comparer au distant/PR. Aucun APPROVE lot4 ni merge acquis. Après publication finale, Developer arrête les éditions suivies pour la revue.

## Fichiers et décisions

- `raceatlas/catalog/{validation,cursor,selection,coverage}.py` et `__init__.py` : validation contractuelle bornée, curseurs, sélection PostgreSQL unique, projection et audits. Aucune dépendance à l'oracle de fixtures.
- `raceatlas/__init__.py` : routes réelles et gestionnaire d'erreurs catalogue structurées.
- `raceatlas/models.py`, nouvelle migration `b7f4208ac112_add_catalog_snapshot_revision.py` : état singleton et compteur transactionnel, dix triggers statement, fonction de normalisation sans extension, ordre monotone des audits. Aucune ancienne migration modifiée.
- `pyproject.toml`, `requirements.txt` : jsonschema4.25.1 en runtime, déjà présent dans l'environnement.
- `tests/backend/test_catalog{,_validation,_sync}.py`, ajustements nécessaires `test_foundation.py` : scénarios réels et régressions ; API inconnues restent404.
- `docs/lot-4/{mission,local-development,developer-handoff}.md`, `docs/coordination/CURRENT_STATE.md` : périmètre, usage, preuves et suite sûre.

Contrats, fixtures historiques et frontend préservés. SQL sélectionne les IDs et compte les résultats ; graphes chargés pour la seule page<=200. Catégories référencées dynamiquement ; ET doit trouver toutes les catégories dans le même scope confirmé, avec restrictions corrélées et admissibilité personnelle non évaluée. Une Feature par course, centres sourcés seulement.

Le curseur public porte version/hash filtre/offset et un checksum non secret. Changements catalogue409, filtre différent ou corruption400 ; tri date/ID stable. Rayon : deux flux de même offset/limite (confirmées et candidates non localisées), continuation jusqu'à épuisement des deux ; page vide avec curseur possible. Voir `local-development.md` pour les conséquences UI.

Chaque requête utilise un seul snapshot read-only REPEATABLE READ pour version, compteurs, graphes et couverture ; le pool est restauré ensuite. Triggers sur écritures manuelles/seed/import/audits, rollback non invalidant. Audit historique sans ordre fiable incomplet ; audits nouveaux triés par création DB, dernière tentative échouée visible et dernier succès conservé ; un échantillon synthétique ne prouve jamais la complétude FFC.

## Commandes et résultats observés

Python3.12.14, PostgreSQL17.11 local uniquement Developer `_test`, navigateur Chromium en cache. Depuis racine :

```powershell
$python = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
$env:PLAYWRIGHT_BROWSERS_PATH = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
& $python -m pytest -q --tb=short
& $python -m ruff check raceatlas migrations tests/backend
& $python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
Push-Location frontend
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vitest/vitest.mjs run --pool=threads --maxWorkers=1
node node_modules/vite/bin/vite.js build
Pop-Location
& 'C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m pip --python $python check
git diff --check
```

**304/304pytest PASS en90,46s**, aucun skip, dont99tests catalogue et3Chromium antérieurs. Les tests exécutent migration upgrade/check/downgrade/upgrade/check,9scénarios Flask/PostgreSQL conformes aux schémas, parcours limite1 partagé carte/catalogue, rayon avec flux vide et continuation, catégories u15, Unicode nom/commune/organisateur et métacaractères littéraux, années civiles/multijours, triggers et rollback, import offline→API/carte, deux courses au même centre, couverture échec/reprise/legacy, erreurs publiques et snapshot concurrent réel entre compteurs et graphes (une autre connexion commit avant la fin de lecture).

Ruff lint/format **35fichiers PASS**, **26contrats Node PASS**, frontend ESLint PASS, **3/3Vitest PASS en5,03s** avec threads1, build Vite PASS, pip check PASS. Le build précède les parcours Chromium. Les trois tests frontend ont réellement été exécutés.

Expansion ciblée initiale :15échecs/58succès. Défaut réel d'espace NBSP corrigé dans la fonction SQL (classe explicite des espaces Unicode cohérente avec Python) ; NUL/surrogates isolés également rejetés avant DB. Autres échecs dus aux attentes nouvelles des tests : Error est plat, et DELETE SQL brut violait les FK du graphe ; corrigés côté tests sans affaiblir les contraintes. Puis98tests ciblés PASS en23,16s ; scénario de centre importé et continuation rayon renforcée inclus dans le global304PASS. Aucun défaut local connu restant.

## Revue indépendante et limites

Tester : confirmer SHA/propreté/base, lire mission/contrats/handoff, utiliser **seulement** `raceatlas_lot2_review` avec opt-in jetable. PostgreSQL existant actif ; ne pas réinitialiser le cluster, ne pas partager la DB Developer. Rejouer les commandes ci-dessus en changeant uniquement la base, puis examiner les cas négatifs ET interscopes/races, parité après toutes les pages, invalidation des audits/écritures et couverture prudente. Aucun fichier produit à éditer pendant revue. Le verdict doit nommer le SHA exact ; tout commit ultérieur l'invalide. Coordinator contrôle CI/mergeabilité/base avant intégration.

Pagination OFFSET et recherches sans extension : aucune performance sur collecte régionale réelle revendiquée. L'ordre des audits représente la création DB des tentatives ; les anciens audits ne sont pas reconstruits depuis UUID/timestamps. Données/fournisseurs synthétiques, droits FFC réels toujours à établir. Aucun client live, scheduler, collecte large, service payant, mutation distante ou déploiement. Choix propriétaires futurs préservés dans le checkpoint. Aucun processus de test Developer actif ; cluster conservé pour revue.
