# Lot 8 — suivi de la CI navigateur desktop

Point du **18 novembre 2026 à 16:03 UTC**. La [PR 17](https://github.com/TheoxProject/RaceAtlas/pull/17) est fusionnée sur main au SHA `e766a70996e7ce375a7826da5d064a3caac91b61`. Le [contrôle intégré post-fusion](https://github.com/TheoxProject/RaceAtlas/actions/runs/44338906844/job/134923111166) a échoué avec 1 078 tests backend réussis et 2 échecs desktop en 460,07 s. Le cas mobile et la nouvelle régression terrain passent.

| Tâche | État | Preuve ou condition restante |
|---|---|---|
| OPS-GUI diagnostic post-fusion | DONE | Saison desktop bloquée sur le témoin de janvier après deux réponses HTTP 200. Notifications desktop bloquées sur l'attente du pitch alors que le diagnostic a observé 60° et quatre avertissements GPU. |
| OPS-GUI réduction du tampon SwiftShader | IN_PROGRESS | Développeur `2872bdf33425b0a162a0788e85824576dfc51172` sur `fix/desktop-map-ci`, worktree `.local-tools/worktrees/desktop-map-ci`. Deux parcours locaux réussis. Publication, PR, CI du correctif et verdict indépendant à consigner. |
| OPS-V validation finale | BLOCKED | Le contrôle intégré post-fusion requiert une correction et une validation GitHub avant la suite de la [recette V1](../readiness/release-candidate.md). |

Le harnais applique `Map.setPixelRatio(0.5)` avant Summit sur la page principale de ces deux tests. Dans une sonde A/B/B/A sous Chromium 1194 et SwiftShader, le tampon WebGL passe de 1 096 × 667 à 548 × 333 pixels. Le viewport reste à 1 440 × 960 CSS. Les quatre passages atteignent le pitch 60° et une élévation moteur de 829,26 m. La réduction des pixels est vérifiée, avec quatre avertissements GPU par passage et des délais hôte variables. Ces mesures locales ne déterminent pas la cause des délais Ubuntu.

**Validation locale.** Build du frontend vérifié contre main, Python 3.12.14 et PostgreSQL 17.11 sur `127.0.0.1:55434/raceatlas_lot2_test`. Aucune autre session sur cette base jetable avant le lancement. Deux tests en 129,04 s, Ruff `check` et `format --check` sur les trois fichiers modifiés, puis `git diff --check` réussis.

~~~text
python -m pytest -q --tb=short --junitxml=.local-tools/desktop-pixel-ratio.xml tests/backend/test_accounts_ui_e2e.py::test_season_scope_actions_map_two_accounts_outside_public_filters tests/backend/test_notifications_ui_e2e.py::test_notifications_real_sync_offpage_ack_two_actors_scope_readd_desktop
~~~

**Prochaine action.** Publier la branche en Draft et vérifier la CI du SHA publié. Le verdict indépendant et le contrôle `integrated` sont requis pour décider de la fusion. La base `_test` est libérée et `_review` demeure réservée au testeur. Les preuves locales sont sous `.local-tools/`. Éviter de relancer les mêmes tests sans changement ni question de validation identifiable. Toute opération externe de recette ou de publication relève des accords prévus.
