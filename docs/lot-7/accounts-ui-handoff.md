# PR14 — correction CI-F1 (candidat à publier puis figer)

15nov2026 17:11UTC. Branche `feature/accounts-ui`, PR14 Draft/baseb55f4c66e579046c09ee5cd8745fbeed4f566848 ; head avant commitc139a5d6a1685307cb16f7a2cac08fefe52603ec. **CI Ready43736947900 FAIL890PASS/1FAIL392,58s**, countJanvier absent15s, conservée. Anciennes full891/118 et APPROVEc139 restent historiques, pas verdict du prochainSHA.

Seul code modifié : test_accounts_ui_e2e.py, scénario desktop Ma saison. Écoutes requestfinished armées AVANT selectJanvier, rattachées dates/query/limites attendues, pour races200/map200 ET témoinraceslimit1 requis par loadSelection. Validation200/JSONpublics vides/versionségales sans corps ni headers loggés ; ensuite attenteUI15s inchangée. Caméra60°/DEM>100/10s et assertions acteurs/scopes/horsfiltres intactes. Timings hôte bornés/état minimal suréchec. Capture CI réellement vue :0course/Janvier/Route/étatvide ; avec les200, mélange transport/rendu plausible, pas de cause totale ni bugproduit prouvé.

Commande `_test`, offline/DateProxy : `pytest tests/backend/test_accounts_ui_e2e.py -k season_scope_actions_map_two_accounts_outside_public_filters -q --tb=short --junitxml=.local-tools/pr14-ci-f1-desktop-final.xml -rP` : **1PASS26,77s**, trois réponses200/corps validés/versionségales à5000ms depuis sélection, UIready même mesure. Premier instrumenté1PASS27,19s avait créé3tâches PlaywrightTargetClosed par appels Response.finished redondants ; retirés, requestfinished garantit déjà transport fini, run final sans ces erreurs. Aucun retry masquant un FAIL.

Ruff check/format82 PASS ; diff de range depuisb55 PASS. Runtime/frontend/backend/contrats/CI/pins/migrations strictement identiquesc139, preuves immuables réutilisables explicitement, pas verdict copié. Aucune campagne complète locale. Runtimes/serveurs/browsers fermés, PG38028 conservé. Interruptionquota après ciblé : commande documentaire rejetée SANS exécution, reprise explicite puis JUnit1/0/0 réconcilié sans rerun.

Prochaine action : commit/push puis GEL exact pour acceptation indépendante FINALECOMPLÈTE PR14 et integrated exacte, puis Ready/mainCI avant lot8. Aucun mailréel/DNS/remoteDB/deploy/collecte. SHA exact communiqué au push, aucune commande pendante.

## Handoff précédent conservé — preuves historiques
# PR14 — candidat UI-1 + UI-2A + UI-2B

Branche `feature/accounts-ui`, [PR14](https://github.com/TheoxProject/RaceAtlas/pull/14), base `b55f4c66e579046c09ee5cd8745fbeed4f566848`. SHA final communiqué après ce commit/push puis arrêt des éditions. UI-1 exact `bbc4e1f09ddb72a8fb4f9d42d08fa712ceb56022` et UI-2A exact `9e9e196c63f18e482d9768a20a4dce2e4306ea0c` ont leurs APPROVE ciblés ; ce ne sont pas des verdicts pour ce candidat final. Checkpoint UI-2B `e1f06dcbc39ee38ef9ed4d3fcabc45814f29d396` : CI43733669390 development SUCCESS293backend217,22s/116frontend, Ruff82/contrats/build/gardes SHA. Acceptation COMPLÈTE PR14 et CI **integrated** exact restent obligatoires avant fusion, puis mainCI.

## Changements UI-2B

- `privateAccount.js` : préflight CSRF→GETme portant ce proof et acteur attendu→opération même proof ; sensibles204 EXACT, ICS200 EXACT.403 réauth conserve le compte.2xx inattendue ou réseau interrompu = résultat inconnu, ni succès ni rollback supposé, aucun retry. Ancienne réponse ne publie pas après switch/ABA.
- `calendarDownload.js` / SeasonPanel : MIME text/calendar, lecture réelle par chunks≤2Mio (Content-Length indicatif), cancel sur refus/contexte périmé ; lease après await puis immédiatement avant BlobURL/click, révocation différée ou cleanup idempotent. Fichier personnel statique Prévues+Inscrit, sans filtres publics ni abonnement.
- AccountSecurityPanel/AccountPanel/CSS : logout courant/global, nouveau mot de passe exact Unicode+confirmation et suppression explicite. Current password legacy conservé sans normalisation, champs effacés à fin/abandon sans promesse de zeroisation. Dialog/focus mobile conservés.
- Trois scénarios navigateur ajoutés ; whitelist CI ajoute uniquement `calendar-export-desktop` et `security-mobile` aux PNG synthétiques réguliers/non-symlinks, rétention1jour. Aucun backend/migration/contrat/dépendance modifié depuis UI-2A.

## Commandes et résultats observés

Depuis `frontend/` :
- `node node_modules/vitest/vitest.mjs run src/accountSensitive.test.js src/calendarDownload.test.js src/privateAccount.test.js src/season.test.js --environment=node --pool=threads --maxWorkers=1` : **41PASS3,17s**.
- `node node_modules/vitest/vitest.mjs run src/AccountSecurityPanel.test.jsx src/SeasonPanel.test.jsx src/AccountPanel.test.jsx --pool=threads --maxWorkers=1` : **10PASS18,19s**, composants inchangés depuis.
- ESLint PASS ; Vite build **9,01s PASS**, avertissement taille bundle MapLibre existant. Pas de dist commité.

Python natif réutilisé, `_test` opt-in seulement, Chromium/DateProxy/offline :
- `pytest tests/backend/test_accounts_ui_e2e.py -k 'mobile_security_reauth or mobile_password_and_delete' -q --tb=short --junitxml=.local-tools/ui2b-security-split.xml` : **2PASS24,17s**. Deux appareils : logout courant préserve autre session, global/change révoquent réellement ;403 garde acteur, nouveau PW permet login, suppression purge A/sauvegardes/cache sans toucher B ni epoch/révision publics.
- `pytest tests/backend/test_accounts_ui_e2e.py -k calendar_download_uses -q --tb=short --junitxml=.local-tools/ui2b-download-public-context.xml` : **1PASS13,68s**. Janvier/Route affiche0course publique mais export contient les2scopes planned/registered parmi4sauvegardes ; parser indépendant icalendar,2UID/dates exclusives.202 inattendue refusée ; vrai logout204 committé puis réponse réseau perdue reste inconnu, pas retry, GETme explicite constate révocation. Carte/caméra/filtres/période/focus conservés. Seules captures d'échec ajoutées ensuite, attentes métier inchangées.
- Ruff check + format --check `raceatlas migrations tests/backend ops/ci_selection.py` : **PASS82fichiers** ; `node --test tests/contracts/contracts.test.mjs` : **26PASS** ; diff --check PASS final.

Incidents conservés : nouveaux mocks GETme confondaient DELETEme (6PASS/2FAIL puis corrigés) ; premier browser2FAIL30,42s (SUMMARY attendu erroné + ancien acteur correctement refusé), puis1PASS/1FAIL27,16s (enchaînement artificiel dépassait vrai quota de lectures). Scénarios séparés selon opérations indépendantes avec quotas inchangés ; aucun timeout relevé. PG sandbox semblait absent, contrôle natif a confirmé PID38028/55434 actif ; tentative start a refusé lock existant sans effet, aucun PID/data supprimé ni initdb.

Captures synthétiques **vues** : `.local-tools/accounts-ui-screenshots/calendar-export-desktop.png` et `security-mobile.png`. UI-1/UI-2A chemins inchangés réutilisent explicitement leurs preuves (dont carte Summit60°/DEM réel et calendrier390) ; limite Reviewer jsdom NONPASS distincte de CI97 et4browsers UI-2A. Pas de campagne backend complète locale répétée. Les nouveaux flows ne prouvent pas une délivrabilité externe.

Prochaine action : revue indépendante COMPLÈTE UI-1+2A+2B au SHA final + label `ci:full`/integrated par Coordinator. Aucun autre lot avant fusion/mainCI. Aucun email réel/Resend/DNS/service/remoteDB/achat/déploiement/collecte. Runtimes/serveurs/browsers de test fermés avant Engine.dispose ; PG local conservé.
