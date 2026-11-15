# PR14 — CI-F2, candidat à publier puis figer

15nov2026. `feature/accounts-ui`, DraftPR14/baseb55f4c66e579046c09ee5cd8745fbeed4f566848, head avant commit195dc2b5eaedf8ad74f13d189e611393b80a9ce7. **Ready43740601544 FAIL889PASS/2FAIL393,78s** : Summit60°/10s sanssnapshot+capturetimeout avantcompte ; retourNovembrecount1 absent15s. Anciennes integrated891/118 et APPROVE195 sont historiques, pas verdict du prochainSHA. Ready43736947900FAIL890/1 (Janvier) et correctionsCI-F1 restent conservés dans Git/rapports, aucun échec effacé.

## Delta borné

Un seul fichier de test : `test_accounts_ui_e2e.py`. Barrière existante généralisée Janvier/Novembre : requestfinished sur races200/map200/témoinlimit1, écoutes avant select et filtre/dates/query/limites attendus, validation corps publics/IDs et versions égales sans les logger, puis attente UI15s identique. Assertions acteurs/scopes/horsfiltres/caméra exactes conservées.

Auth : observateur caméra existant installé AVANT Summit (cache hôte moteur/dataset/frames/easing/stops/contexte au timeout). **Aucun changement deadline10s/pitch60°/DEM>100, readiness source, moteur, horloge ou produit.** Garde sur capture d'échec auth : si screenshot timeout, préserver l'exception/diagnostic d'origine. Cette seule branche d'erreur ajoutée après ciblés ne change pas les attendus métier ; lecture Tester requise au SHA final.

Capture Ready2 `.local-tools/pr14-ready2-failure/season-desktop.png` réellement vue : novembre/Route/querycorrecte/1course et panneau présents au finally, pas preuve du respect des15s précédentes. Corps reçus/version/témoin et présentation sont des phases distinctes ; pas de SLAproduit nouveau. **Instrumentation caméra et PASS local ne démontrent pas résolution du timeoutSummit** : no-snapshot signifiait observateur absent ; lectures/bindings peuvent influencer ordonnancement/charge SwiftShader. Pas de causeunique GPU/transport prouvée, pas de préwarm ou workaround supposé.

## Vérifications réelles

`pytest tests/backend/test_accounts_ui_e2e.py -k 'compiled_signup_explicit_confirmation_login_and_late_401_keep_discovery or season_scope_actions_map_two_accounts_outside_public_filters' -q --tb=short --junitxml=.local-tools/pr14-ci-f2-targeted.xml -rP` : **2PASS47,75s** (auth19,309s, desktop27,482s). Un seul run ciblé, pas de retries jusqu'auvert. Timings de validation/publication émis sous `PUBLIC_MONTH_SELECTION_TIMING`, événements classés/status/versionségales seulement ; aucun corps/header privé. Environnement local_test opt-in/PG38028/55434, DateProxy/ressourcesofflines, Reactcompilé existant inchangé, DevelopmentRAM. Runtimes/serveurs/browsers fermés.

Ruff check + format --check raceatlas/migrations/tests/backend/ops-ci-selection : **PASS82**. Range diffcheckb55..HEAD à vérifier aprèscommit également. Nulldiff frontend/backendproduit/contrats/CI/pins/migrations vs195 : preuves antérieures réutilisables explicitement, pas ancien verdict copié. Aucun replay complet local/autresbrowsers/build/install. Aucun changement map_support/test_e2e partagé.

Prochaine action : commit/push cohérent, annoncerSHAexact puis STOP pour acceptation FINALECOMPLÈTE renouvelée PR14 et integrated exacte (ci:full), Ready puis mainCI avant lot8. Lot8owner : Changementsrécents dansMaSaison/compteur/marquerlues ; retirer scope retireSESnotifications seulement, sanshistorique ni impactautreslistes. Aucune implémentation8 ici, aucun mailréel/DNS/remoteDB/deploy/collecte.
