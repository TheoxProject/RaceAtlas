# UI-2A — contrôles courants

Même environnement réutilisé ci-dessous, uniquement `_test` opt-in/PG38028/55434/schémaa74. Aucun install/deps/nouveau schéma.

- Depuis frontend : `node node_modules/vitest/vitest.mjs run src/season.test.js src/privateAccount.test.js src/SeasonPanel.test.jsx src/AccountPanel.test.jsx --pool=threads --maxWorkers=1` :30PASS13,01s. OptionCLI threads pour startupfork Windows, configuration repo inchangée.
- `node node_modules/eslint/bin/eslint.js . --max-warnings 0` PASS ; `node node_modules/vite/bin/vite.js build` PASS5,64s.
- Venvpytest `tests/backend/test_accounts_ui_e2e.py::test_season_scope_actions_map_two_accounts_outside_public_filters -q --tb=short --junitxml=.local-tools/ui2a-desktop-complete.xml` :1PASS40,94s.
- Venvpytest mêmefichier `::test_season_two_cookie_devices_do_not_share_private_identity ... --junitxml=.local-tools/ui2a-devices.xml` :1PASS14,26s.
- Mobile `::test_mobile_calendar_scopes_and_season_keep_month_and_private_scope` PASS dans premier run2A (`-k 'season_scope or mobile_calendar_scopes'`, JUnit ui2a-browser-first.xml), desktopFAIL initial conservé. Ne pas déclarer une campagne3PASS inexistante ; les3parcours ont des preuves distinctes.
- Ruff82/Node26contrats/diff PASS, pas campagne backend complète locale. Capture2PNG season-desktop/mobile whitelisted bornée, jamais HAR/headers/body/proofs bruts.

Le candidat gelé et les limites figurent au [handoff](accounts-ui-handoff.md). Ne pas lancer vieuxcheckout contre_test migrée, aucun _review, aucun test retenu ; fermer runtime avantEngine.dispose. UI-2B non commencé.

## Historique UI-1

# UI-1 — commandes ciblées Windows

Réutiliser venv Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, Node24/pnpm10.20 et Chromium existants. PG17 PID38028/port55434/cluster `.local-tools/pgdata-lot2-native`, schémaa74d915e3c02 ; vérifier processus/statut, jamais initdb/reseed/anciencheckout. `_test` Developer et `_review` Tester séparés.

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB='1'
$env:PLAYWRIGHT_BROWSERS_PATH='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
# Alias documentaire : $uiPython doit pointer vers la venv ci-dessus.
$uiPython='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
& $uiPython -m pytest tests/backend/test_account_read_context.py tests/backend/test_auth_http_sessions.py tests/backend/test_auth_http_foundation.py -q --tb=short --maxfail=2 --junitxml=.local-tools/ui1-read-context-final.xml
& $uiPython -m pytest tests/backend/test_ci_selection.py -q --tb=short --junitxml=.local-tools/ui1-ci-selection.xml
& $uiPython -m pytest tests/backend/test_accounts_ui_e2e.py -q --tb=short --maxfail=2 --junitxml=.local-tools/ui1-browser-final.xml
& $uiPython -m ruff check raceatlas migrations tests/backend ops/ci_selection.py
& $uiPython -m ruff format --check raceatlas migrations tests/backend ops/ci_selection.py
node --test tests/contracts/contracts.test.mjs
```

Résultats acquis87PASS40,02s /17PASS0,10s /2PASS26,09s, puis desktop enrichi1PASS31,27s (ui1-browser-context-fixed.xml) ; migration roundtrip fixture comprise. Pas de campagne853/862locale répétée. Browser utilise frontend/dist compilé et server/runtime éphémères fermés, provider mémoire sans réseau ni debug route. Variables de test synthétiques dans fixture seulement.

Depuis `frontend/` : `node node_modules/vitest/vitest.mjs run src/privateAccount.test.js` (13PASS), puis fichier `src/AccountPanel.test.jsx` (5PASS). Exécuter isolément si incident Windows forks ; ne pas modifier la configuration pour le masquer. `node node_modules/eslint/bin/eslint.js . --max-warnings 0` puis `node node_modules/vite/bin/vite.js build`. Build dernier3,50s PASS, warning taille MapLibre existant, pas artefactdist commité. App9 tests passés, preuve initiale conservée ; CI passe tous les frontend.

Sélecteur CI : docs-only annonce aucun backend, coutures connues et tests ajoutés/modifiés sélectionnés, inconnu/deps/migration/conftest retombent full. À fusion finale job intégré complet obligatoire ; [guide](../readiness/ci-validation.md). Pas de relance longue pour checkpoint documentaire, toujours vérifier qu'un ancien processus est terminé avant commande.

UI-2B candidat final : tests pure Node41PASS (accountSensitive/calendarDownload/privateAccount/season), composants10PASS, browsers ciblés3PASS : commandes et JUnit exacts dans [handoff](accounts-ui-handoff.md). Utiliser uniquement _test ; statut PG doit être vérifié via commande native autorisée (visibilité sandbox trompeuse observée). Quotas conservés : scénarios sécurité indépendants, pas un long enchaînement de connexions saturant GETme. Deux PNG whitelist supplémentaires calendar-export-desktop/security-mobile, valeurs synthétiques uniquement. Réutilisation UI-2A explicite, pas verdict transféré.
