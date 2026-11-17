# OPS-N2 — candidat final à geler

17 novembre 2026, 13:50 UTC. Worktree add4, branche `feature/notifications-interface`, Draft PR16 : https://github.com/TheoxProject/RaceAtlas/pull/16. Base/main `014bda3480d0f8c0233f8e6f68d0ae82886b83db`, HEAD/origin avant publication `e5ecbb127ff30f90d61f176f94fce4a2304eea41` ; nouveau SHA exact communiqué au gel après commit/push.

- N2A : APPROVE ciblé exact8581/F1-F2 CLOSED, CI44048466660 development1016/118 historiques.
- N2B1 : APPROVE ciblé exacte5ecbb1 (comment6949430174), CI44092575080 development1017backend292,49s/138frontend. Ancien FAIL429 CI44088350671 conservé dans le handoff ; admission20/60 inchangée.
- N2B2 : preuves navigateur DONE, acceptation complète N2 TODO. Nouveau fichier `test_notifications_ui_e2e.py` seulement : vrais imports synchronize, deux comptes/scopes, quatre statuts, 52messages/50visibles/ACK horspage, nouvelle source encore non lue, retrait/réajout baseline ; mobile390 absence→à vérifier→ACK→restauration, calendrier décembre/clavier/focus/caméra conservés.

Commandes réelles : `pytest tests/backend/test_notifications_ui_e2e.py -q --tb=short --junitxml=.local-tools/ops-n2b2-browser-controls.xml` : **2 PASS96,13s**, session9397 exit0. Incidents de harnais précédents : initial2FAIL8,382s (labels parsés contiennent les conditions) ; labels2FAIL37,99s (panneau Explorer recouvre Summit ; zéro prend le pluriel). Corrections de parcours/assertions seulement, pas défaut produit ni hausse de seuil. Ruff check et format --check complets : PASS101 ; `git diff --check <base>` PASS.

Deux PNG synthétiques vus réellement : `.local-tools/notifications-ui-screenshots/desktop.png` et `mobile.png`. Whitelist CI ajoute seulement ces fichiers réguliers non symlinks, destinations notifications-*, rétention1jour inchangée. Aucun changement frontend/backend/API/source/auth/DB/ICS/deps/CIselection ; build d9/e5 réutilisé à diff nul. Pas nouvelle prétention de verdict Tester ou CI pour le prochain SHA.

Environnement : PG9780/127.0.0.1:55434 existant, schéma b806, `_test` seulement ; `_review` réservée. Venv Python/Chromium1a1e réutilisés, DateProxy et horloge admission TESTONLY (pauses explicites61s), aucune horloge session/CSRF/DB/RAF modifiée. Tous browsers/serveurs/runtimes fermés avant dispose ; aucun Python/Chrome restant, aucune commande pending. Zéro email réel/liveFFC/DNS/service/DB distante/déploiement/achat/tag.

Prochaine action sûre : publier le candidat cohérent, communiquer SHA exact puis STOP éditions pour acceptation COMPLÈTE N2 et CI integrated demandée par Root. Ne pas rejouer les tests verts ni commencer la suite avant merge/mainCI. Le verdict ciblé e5 et ses preuves sont historiques ; le nouveau SHA demande renouvellement complet.
