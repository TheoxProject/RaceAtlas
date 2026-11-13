# ACC-01 — fondation intégrée, lot 7 en cours

[PR11](https://github.com/TheoxProject/RaceAtlas/pull/11) fusionnée et confirmée par GitHub le 12 novembre 2026. SHA approuvé : **d264ae0ac7c5586e65966922caadbfe91abd811d** ; merge main : **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Arbre identique : **58f7a7e23ed3d0626735e2f762066de1ab55a8da**. Base précédente : 51856c9940a2b0e16c9f05d61a9f1726ae8701d9.

## Gates exécutés

- Developer : 43 nouveaux tests PG puis 88 régressions pertinentes ; après correction, 68 tests planning PASS25,14s. Migration upgrade/check/downgrade/upgrade/check, Ruff43 et contrats26 PASS.
- Tester R1 exact5a664068fd6d5faa08c75478f09a2fc50202f504 : REQUEST CHANGES malgré 131 tests PASS61,70s. Deux défauts internes reproduits : acteur pending-delete chargé/expiré ; IDs NUL/surrogate envoyés au driver. Ni exposition HTTP ni corruption de transaction démontrée.
- Correction cycle1 : garde pending-delete avant attribut/autoflush, rejet NUL/UTF-8 invalide avant query ; IDs synthétiques non UUID préservés. Aucun broad catch ou route d'auth factice.
- Tester final : **APPROVE exact d264ae0**, 80 tests/sondes PASS28,54s, Ruff43/contrats26/diff PASS. Matrice complète ACC-01 avec réutilisation explicite des preuves compatibles pour chemins inchangés ; rapport complet publié dans PR11. Aucun verdict global lot7.
- [CI PR43281879288](https://github.com/TheoxProject/RaceAtlas/actions/runs/43281879288) SUCCESS : **457 backend209,86s / 67 frontend**, lint/format/contrats/build/dépendances. Source d264ae0 vérifiée avant/après ; base/main courants et mergeabilité vérifiés avant fusion.
- [CI main43282947407](https://github.com/TheoxProject/RaceAtlas/actions/runs/43282947407) SUCCESS : **457 backend212,75s / 67 frontend** et mêmes checks, source5e2c84a vérifiée avant/après. Résultat réconcilié le13nov07:21UTC après interruption ; aucun travail de fond promis pendant celle-ci.

## Comportement et limites

Account privé, SavedEntry unique compte+scope, quatre statuts déclaratifs, FK scope RESTRICT/compte CASCADE, course dérivée du scope. Upsert concurrent, révision1/+1 sur vrai changement et no-op stable ; timestamps privés UTC. Tests réels PG/imports synthétiques protègent favoris pendant renommage/report/réorganisation attestée/replay/refus/absence→to_verify. Catalogue public inchangé.

Cette fondation ne connecte personne : Account persistant de même Session ORM est le contrat interne, pas une preuve d'authentification. Aucun credential, session, API privée, formulaire ou ICS livré ici. La migration c40a7162b901 reste manuelle hors fixtures jetables ; rien n'est appliqué à distance ou au démarrage/build.

Décisions explicites enregistrées après fusion : **email+mot de passe → confirmation email avant connexion**, export ICS par défaut **Prévues et Inscrit**. Aucun domaine/expéditeur. Premier déploiement privé après lot8/candidat V1, activation et services soumis à autorisation séparée. Suite : [ACC-02](auth-mission.md), puis API planning/ICS et UI ; lot7 reste ouvert.
