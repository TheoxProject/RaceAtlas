# Prépublication V1 — filtre Discipline

Point du **18 novembre 2026 à 20:29 UTC**. Le filtre Discipline demandé par le propriétaire reprend les lots 4–6 sur la base distante vérifiée `b9a0c4313c5b93ca014b945bb0c1447ab8cfb9e6`. Le [correctif de rendu desktop](https://github.com/TheoxProject/RaceAtlas/pull/18) avait passé la [CI main](https://github.com/TheoxProject/RaceAtlas/actions/runs/44346863088) au `7f7cd9c`.

| Tâche | État | Preuve ou condition restante |
|---|---|---|
| DISC-01 · Développeur | DONE | Un seul bouton Discipline, cinq disciplines sélectionnables et types Route Course en ligne, CLM et Grimpée. Le parcours Chromium 390 px vérifie le filtre commun carte/calendrier et le retour du focus avec Échap. |
| DISC-02 · Développeur | DONE | Migration `4fc0cc210b83`, 26 tests de contrats et trois cas API sur PostgreSQL pour Piste et Grimpée. Le filtre de type conserve son intersection avec les disciplines. |
| DISC-03 · Développeur | DONE | `85ae591c67dd033202d0c75bad70a3abe8544ac9` aligne le test de notifications sur le mode `cors` déjà présent sur main. Treize tests ciblés passent. La [CI de la base](https://github.com/TheoxProject/RaceAtlas/actions/runs/44382718254) avait isolé cette assertion. |
| DISC-04 · Testeur et Coordinateur | IN_PROGRESS | Revue indépendante du SHA figé, contrôle GitHub `integrated`, fusion et contrôle main. |

**Travail et validation.** Worktree `C:/Users/theop/.codex/worktrees/161d/RaceAtlas`, branche `feature/discipline-picker`, [PR 20](https://github.com/TheoxProject/RaceAtlas/pull/20) en Draft. Handoff développeur au `d08921c554a3cd56ba7204dcf5564689f842eb90` avant ce checkpoint, build et lint réussis. Quatre tests PostgreSQL/Chromium réussis en 35,42 s avec le cycle Alembic de la suite. Le [premier contrôle development](https://github.com/TheoxProject/RaceAtlas/actions/runs/44391007743) porte sur le commit `85ae591`. Aucun SHA approuvé par le testeur à ce stade.

**Environnement.** Node 24.22.1, Python 3.12.14, Chromium 1194 et PostgreSQL 17.11 jetable sur `127.0.0.1:55454` dans `.local-tools/discipline-pg/native-data`. `raceatlas_discipline_test` pour le développeur et `raceatlas_discipline_review` pour le testeur. Garder les bases distinctes. Le premier `initdb` dans le bac à sable a été interrompu. Éviter de le relancer sur le répertoire partiel `data` et de reseeder une base existante. Aucun déploiement ni collecte FFC dans ce chantier.

**Prochaine action.** Publier le SHA qui contient ce checkpoint, confirmer la tête de la PR 20 et lancer la revue indépendante et le contrôle `integrated` sur ce même SHA. Consigner les résultats dans la PR pendant le gel.
