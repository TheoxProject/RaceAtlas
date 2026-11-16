# OPS-N1A — vérification locale Windows

Réutiliser Python3.12.14 : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. PostgreSQL17 existant, cluster absolu `C:/Users/theop/.codex/worktrees/add4/RaceAtlas/.local-tools/pgdata-lot2-native`, loopback55434. Contrôler le processus avant toute commande ; aucun initdb/reseed/ancienne copie sur nouveau schéma.

```powershell
$n1Python='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL='postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB='1'
& $n1Python -m pytest tests/backend/test_notifications.py -q --tb=short --junitxml=.local-tools/ops-n1a-initial.xml
& $n1Python -m pytest tests/backend/test_notifications.py tests/backend/test_planning.py tests/backend/test_private_planning.py -q --tb=short --junitxml=.local-tools/ops-n1a-extended.xml
& $n1Python -m pytest tests/backend/test_planning.py tests/backend/test_notifications.py -k 'nonrepresentable or database_restricts or large_batch or transaction_modes or invalid_batch or invalid_or_oversized or effective_external' -q --tb=short --junitxml=.local-tools/ops-n1a-corrections.xml
& $n1Python -m ruff check raceatlas migrations tests/backend ops/ci_selection.py
& $n1Python -m ruff format --check raceatlas migrations tests/backend ops/ci_selection.py
node --test tests/contracts/contracts.test.mjs
```

Commandes historiques, PAS une invitation à tout rejouer :12PASS, puis97PASS/10FAIL, puis23PASS reciblés ; [handoff](developer-handoff.md) détaille correction/réutilisation. Fixture de session effectue roundtrip complet migration ; test backfill effectue en plus downgrade a74/upgrade avec données existantes. Ces opérations nécessitent `_test` jetable opt-in. `_review` appartient au Tester et ne doit pas recevoir les tests Developer.

16nov reprise : schéma `_test` b806e44f7901, `_review` a74d915e3c02 ; PG PID9780. Le démarrage explicite du cluster EXISTANT, s'il est réellement arrêté et autorisé : `pg_ctl start -D <chemin-absolu-vérifié> -o "-h 127.0.0.1 -p 55434" -l <log-workspace> -w`. Sans `-o`, le port défaut ne garantit pas55434. Ne pas effacer un PID aveuglément, ne pas lancer de serveur concurrent.

ScopeGuard/record supportent Session Engine ou Connection unique transactionnelle READ COMMITTED, root et nested effectifs contrôlés. Tout caller source futur doit prendre les guards AVANT ses mutations/SAVEPOINT ; aucune synchro live/récurrente installée par ce jalon. Aucun changement frontend/HTTP/auth/ICS/CI/deps, aucune requête réelle fournisseur. Tous runtimes doivent être fermés avant dispose des Engines.
