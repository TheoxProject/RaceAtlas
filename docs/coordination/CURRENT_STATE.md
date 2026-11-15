# Point de reprise RaceAtlas — lot8 OPS-N1

15 novembre2026 18:22UTC. Branche feature/operations-readiness, checkout isolé C:/Users/theop/.codex/worktrees/add4/RaceAtlas. Base/local avant cadrage c74086365df62bf1c71623e080bb1f649c9981f5 ; origin/main identique vérifié. PR lot8 à créer après commit de cadrage. Aucun lot8 produit encore implémenté.

## Gates acquis

[PR14](https://github.com/TheoxProject/RaceAtlas/pull/14) merged : head revu de4e7c449a0e6f6124d9238381ad9a263a066787, APPROVE complet [rapport](https://github.com/TheoxProject/RaceAtlas/pull/14#issuecomment-6898826817), merge c74086365df62bf1c71623e080bb1f649c9981f5, arbre identique1663a7d19bf3610696156156291f5abeb5693154. Ready43744817098 SUCCESS891backend357,92s/118frontend ; main43745685937 SUCCESS891backend262,96s/118frontend, gardes source avant/après. [Intégration durable](../lot-7/accounts-ui-integration.md). Trois corrections ciblées CI historiques conservées, aucune cause générale du renderer affirmée.

## Mission et tâches

[Mission lot8](../lot-8/mission.md) fait foi. Root termine cadrage puis Developer sera seul writer suivi après transfert explicite ; Tester lecture/test exact sans édition.

| ID | État |
|---|---|
| OPS-N0 cadrage/branche/Draft | IN_PROGRESS |
| OPS-N1 journal/scopes/baseline/projection/cascades/concurrence | TODO |
| OPS-N2 API et Changements récents Ma saison | TODO |
| OPS-E erreurs/couverture/quotas simulés | TODO |
| OPS-B backup/restore nouvelle DB locale synthétique | TODO |
| OPS-V validation V1/candidat | TODO |

Décisions propriétaire acquises : Changements récents dans Ma saison, compteur nouveautés et Marquer comme lues ; unsave scope retire SES notifications, autres scopes/comptes préservés, réajout baseline fraîche. Pas question en attente. N1 : aucun verdict ni test encore, pas fin lot8 au seul N1.

## Environnement et prochaine action

PG17.11 existant loopback55434/dernierPID38028, cluster .local-tools/pgdata-lot2-native ; vérifier nativement avant réemploi, pas initdb/reseed aveugle. DeveloperDB raceatlas_lot2_test, TesterDB raceatlas_lot2_review, aperçu raceatlas_map_demo préservé ; tous schéma initial a74. Python3.12.14/venv et browsers réutilisables dans worktree1a1e, Node24/pnpm10 cache existant. Fermer runtimes avant Engines. Aucun test/serveur/browser restant au transfert, agents PR14 STOP/sourceRELEASED, Nodes externes intacts. Autres worktrees/copie personnelle main inchangés.

Prochaine action sûre : commit/push cadrage N0, Draft PR précoce+suivi CI du SHA, puis attribuer OPS-N1 borné au Developer. Ciblés locaux, checkpoints cohérents ; gel exact pour revue indépendante et integrated complète avant fusion/mainCI. Ne pas répéter toute auth/ICS locale si immuable. Pas écriture concurrente ni edit du SHA sous revue.

Resend Free choisi, raceatlas.ucthonon.fr email uniquement/From notifications non vérifié, APP_BASE_URL Render inconnue. Activation réelle/droits FFC/terrain/capacitéFree encore à qualifier ; aucun mail réel/DNS/service/remoteDB/deploy/collecte/tagfinal autorisé. Ne pas confondre merge et déploiement. Quotas non mesurables, aucune reprise automatique ni background promis.
