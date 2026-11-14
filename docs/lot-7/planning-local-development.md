# PLAN-A+B — Vérification locale Windows

## Correction portable PLAN-F1

Le premier candidat aa07746 a obtenu113PASS/1FAIL chez Tester sous Windows/CP1252, même si CI Linux853/67 était verte. Le test subprocess seul lisait le JSON UTF8 avec l’encodage texte local ; code runtime inchangé. Commande réellement exécutée, sans DB :

```powershell
$env:PYTHONIOENCODING='cp1252'
$env:PYTHONUTF8='0'
& C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe -m pytest tests/backend/test_planning_ics.py -q --tb=short --junitxml=.local-tools/plan-f1-codec.xml
```

**22 PASS3,50s**. Le harness enfant décode explicitement son stdin binaire en UTF8 et vérifie les deux contextes CP1252/mode0 et UTF8/mode1 sans dépendre du parent. Ces variables servent uniquement à la commande de régression, pas au runtime RaceAtlas. Aucun PYTHONUTF8 global requis ni assertion relâchée. Réutiliser les113 succès produit/16sondes indépendantes après diff nul runtime, pas de rerun backend complet ou DB pour cette seule correction. Ruff lint/format78, Node26contrats/diff PASS.

## Candidat final ICS

Sur les mêmes Python/PG/_test opt-in ci-dessous, commande réellement exécutée :

```powershell
& C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe -m pytest tests/backend/test_planning_ics.py tests/backend/test_personal_calendar.py tests/backend/test_private_planning.py tests/backend/test_auth_http_sessions.py tests/backend/test_foundation.py tests/backend/test_catalog_options.py -q --tb=short --maxfail=3 --junitxml=.local-tools/plan-b-final.xml
```

**113 PASS97,59s**,21+21+19+29+20+3, migration upgrade/check/base/upgrade/check incluse. Après ce run, test `test_planning_ics.py::test_new_process_restart_host_and_timezone_do_not_change_uid_or_bytes` ajouté puis exécuté seul :1PASS3,47s (`.local-tools/plan-b-process-formatted.xml`), produit inchangé. Total114 via113+1. Schéma actuel **a74d915e3c02**, ne pas exécuter un ancien worktree contre cette base migrée. Ruff lint/format78, Node26contrats, planningrefs17, pipcheck/diff PASS. Parser dev-only icalendar7.3.0/dateutil4.0.0 installés via runtimepip --python, provenance/licences dans docs/third-party. GET/HEAD `/api/v1/me/calendar.ics` existe maintenant ; aucune UI/feed. [Handoff final](planning-ics-handoff.md). Ne pas relancer les113 verts pour un checkpoint documentaire.

## Historique PLAN-A (avant ICS)


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
