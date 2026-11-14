# PLAN-A — Vérification locale Windows

Réutiliser Python3.12.14 de `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. PostgreSQL17.11 existant sur127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, PID38028 confirmé le14nov. Vérifier le statut et les processus avant les tests ; ne pas initdb, recréer ou arrêter globalement les processus. Base Developer `_test`, Reviewer `_review` distincte. Le schéma actuel reste **f61d338ab204**, aucune migration PLAN-A.

```powershell
& C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/pgsql/bin/pg_ctl.exe status -D .local-tools/pgdata-lot2-native
$env:TEST_DATABASE_URL='postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB='1'
& C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe -m pytest tests/backend/test_private_planning.py tests/backend/test_planning.py tests/backend/test_auth_http_sessions.py tests/backend/test_foundation.py tests/backend/test_catalog_options.py -q --tb=short --maxfail=3 --junitxml=.local-tools/plan-a-final.xml
```

Résultat exécuté :139 PASS118,877s (19+68+29+20+3). Le JUnit complet a été conservé avant interruption et réconcilié le14nov ; ne pas refaire ce run pour la seule reprise. Les fixtures disposent leurs runtimes auth avant leurs Engines et n'utilisent que la base jetable explicite ; leur cycle de migration vérifie upgrade/check/base/upgrade/check. Network email et source interdits par les sondes ; source importée uniquement depuis fixtures synthétiques, geocoder OfflineProvider.

```powershell
& C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe -m ruff check raceatlas migrations tests/backend
& C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
& C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -m pip --python C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe check
git diff --check
```

PASS : Ruff lint,73 fichiers formatés,26 contrats publics Node, pip check. Le test de contrat PLAN-A valide les réponses réelles avec JSON Schema/FormatChecker ; le contrôle complémentaire de références a résolu17 cibles locales des deux nouveaux fichiers. Aucun paquet réinstallé ; la venv n'a pas de module pip, utiliser le runtime ci-dessus. Pas de frontend/build/browser ou full791 local nécessaire pour ces seuls modules backend.

La Session auth demeure READ COMMITTED et AccountFlowSession ; ne pas convertir globalement à REPEATABLE READ. Les tests cap/taille peuvent réduire `PlanningLimits` côté serveur uniquement. Les requêtes publiques de filtre ne sont pas acceptées sur l'API personnelle. `/api/v1/me/calendar.ics` reste404 jusqu'à PLAN-B ; ne pas installer son parseur ni migrer un futur schéma pendant la revue PLAN-A.
