# N2B1 — candidat correction CI admission, cycle1

17 Nov 2026 13:24:18 UTC. add4/feature/notifications-interface / [DraftPR16](https://github.com/TheoxProject/RaceAtlas/pull/16), base014bda3480d0f8c0233f8e6f68d0ae82886b83db ; HEAD/origin avant publicationd9d182dc2fa4e87e0bfcca80bd26b72c4ecc84e4. Tester APPROVE ciblé unit d9 historique, rapport archivé ; **CI44088350671/job134056681973 FAIL1/1015backendPASS355,66s,138frontendPASS**, pas gatevert.

Cause vérifiée directement dans logs GitHub :51requêtes privées,21GETme en50s =17×200+3×401 admis puis1×429. GETme admet l’action read avant auth, seuil peer20/min atteint ; global60 non atteint. Aucun doublon auto démontré/aucune correction frontend. Analyse metadata ignorée ops-n2b1-ci-failure-analysis.json (pas headers/body/cursors).

Correction TESTONLY dans test_accounts_ui_e2e.py : fixture horloge admission._now locale/thread-safe, auth._now global inchangé ; unitaire prouve20×401 admis puis429, refus à59s non prolongé, reprise401admisà61s. Browser existant attend fin de pipelineAlice puis avance61svirtuelles avantBob ; mêmes politiques20/60, mêmes préflights CSRF→GETme→op, aucune clocksession/CSRF/DB/DateProxy/RAF ni délai caméra modifié. Statuts bornés par phase, aucune baisse d’assertions.

## Preuves exécutées _test

- `pytest tests/backend/test_accounts_ui_e2e.py -k browser_admission_clock -q --tb=short --junitxml=.local-tools/ops-n2b1-ci-admission.xml` : **1PASS9,85s**, quotas réels/refus/récupération.
- Même fichier `-k test_season_scope_actions_map_two_accounts_outside_public_filters --junitxml=.local-tools/ops-n2b1-ci-browser.xml` : **1PASS55,97s**, UNbrowserrun, session42252 exit0. PhaseAlice14×200+3×401=17reads ; phaseBob5×200 ; zéro429 avec pausevirtuelle61s. Metadata ops-n2b1-ci-browser-phases.json. Caméra60°/10s/DEM>100, acteurs/scopes/métiers/filtres intacts.
- Ruff check/format100 et range base..HEAD PASS avantcommit, à revalider après. Runtime frontend/backend/contracts/API/source/auth/DB/ICS/CI/deps byte-inchangé : unit71+2sondes reviewer d9 et lint/build conservés sans replay.

Developer seul writer, Tester STOP/_review réservée. PG9780/127.0.0.1:55434b806 confirmé natif, _test seulement ; aucune commande/session/test pending, browser/serveur/runtime fermés avant dispose. Pas1016local ni nouveau scénarioSync N2B2 (toujours TODO après gate corrigé). N2A gate8581 reste historique ; pas verdict copié au nouveauSHA.

**Prochain geste : commit/push cohérent, GEL nouveauSHA et STOP pour contre-revue/CI.** Le débit rapide du harnais est modélisé par pause contrôlée, pas limite production élargie ; l’UI peut honnêtement rencontrer429 et demande reprise explicite. Futur N2B2 respectera ces quotas avec le helper scoped, sans flush ni retry jusqu’au vert. Aucun acte externe autorisé.