# RaceAtlas — lot8 OPS-N2 en cadrage

16nov2026 18:33UTC. Branche isolée feature/notifications-interface, checkout add4. Base/local avant cadrage014bda3480d0f8c0233f8e6f68d0ae82886b83db, origin/main identique validé. PR N2 à ouvrir après commit de cadrage. Aucun code N2 encore implémenté. Root écrit mission/checkpoint ; transfert Developer seul writer après Draft.

## N1 intégré — preuves durables

[PR15](https://github.com/TheoxProject/RaceAtlas/pull/15) merged : head revu60611f19763b112e798600293efa92783d9b5e0d, [APPROVE complet N1](https://github.com/TheoxProject/RaceAtlas/pull/15#issuecomment-6924953718), merge014bda3480d0f8c0233f8e6f68d0ae82886b83db ; arbre identiquefc0609c828146ed50288bd0e653877d6a93f1191 vérifié fetch/diff. Ready43926697034 SUCCESS967backend284,05s/118frontend ; main43928375559 SUCCESS967backend280,55s/118frontend, guards avant/après. [Intégration durable](../lot-8/n1-integration.md). P2 ordre global et accusé perdu fermés, historiques/limites conservés.

## Mission et statuts

[Mission N2](../lot-8/notifications-mission.md), mission lot8/source et handoffs existants restent sources de vérité.

| Tâche | État |
|---|---|
| OPS-N1 journal/baselines/projection/sync/absence | DONE intégré et mainCI vert |
| OPS-N2-0 cadrage/branche/Draft | IN_PROGRESS |
| OPS-N2A services/routes/contrats/snapshot/ACK | TODO, premier jalon à attribuer |
| OPS-N2B Ma saison/store/UI/browser | TODO, après revue N2A |
| OPS-E erreurs/couverture/quotas simulés | TODO |
| OPS-B backup/restore nouvelle DB locale synthétique | TODO |
| OPS-V matrice V1/candidat | TODO |

Décisions propriétaire acquises : Changements récents dans Ma saison, compteur nouveautés ; Marquer comme lues = TOUTES notifications déjà disponibles, même non affichées. Unsave retire SES messages, autres scopes/comptes intacts, réajout baseline fraîche. Pas question en attente. Pas email de course ni source live.

## Prochain geste et environnement

Prochaine action sûre : commit/push cadrage et preuve N1, Draft PR précoce et inspection CI du SHA ; attribuer N2A borné au Developer, qui sera seul writer suivi, Tester au gel sans édition. GET/count/page snapshot commun, ACK ALL snapshot de son unique INSERTSELECT après Account lock, pas batch256 tronquant. Pas d'UI/API déjà présumée livrée, pas de verdict N1 copié au prochain SHA.

PG17 existant add4/.local-tools/pgdata-lot2-native, dernierPID9780/127.0.0.1:55434, _test Developer et _review Tester tous deuxb806e44f7901. Vérifier natif avant réemploi, pas initdb/reseed/piddelete ni ancien checkout contre schéma actuel. Venv Python/Node24/pnpm10/browsers worktree1a1e réutilisables. Aucun Python/Chrome/runtime de tests restant au transfert ; runtime.close avant Engines, Nodes externes préservés. Copie personnelle main2e03cd8 et autres worktrees intacts.

Resend Free/domaineemailraceatlas.ucthonon.fr non activé, APP_BASE_URL Render inconnue ; droits source/terrain/capacité Free restent à qualifier. Aucun email réel/DNS/service/remoteDB/deploy/live/tagfinal autorisé. Quotas non mesurables, pas de reprise automatique promise.
