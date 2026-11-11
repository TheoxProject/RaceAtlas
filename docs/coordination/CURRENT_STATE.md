# Point de reprise RaceAtlas

Lot 5 carte interactive, branche `feature/map-experience`, worktree `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`. Base locale/distante vérifiée **3bd018bff1b60f3831606348831fd72375f557dd**. Mission `docs/lot-5/mission.md`. Cadrage initial à publier et Draft PR à créer ; aucun candidat lot 5 validé.

## Intégration confirmée

Lot 4 DONE : https://github.com/TheoxProject/RaceAtlas/pull/6. Tester **APPROVE** SHA **7cab9a3a3390e01b09f925fe6e9e6321997bc74a** ; CI https://github.com/TheoxProject/RaceAtlas/actions/runs/42981366838 **success**, tous checks verts au même SHA. Merge GitHub confirmé **3bd018bff1b60f3831606348831fd72375f557dd** ; `git diff --exit-code` confirme l'arbre identique au SHA revu. Workflow sur PR, pas de CI main distincte attendue.

Preuves indépendantes : 304 pytest (99 catalogue + 205 antérieurs dont 3 Chromium), 119 assertions supplémentaires, 26 contrats, 3 tests frontend, Ruff 35, ESLint/build/pip/diff réussis. Corpus de 417 courses synthétiques, pagination à deux flux, rollback/invalidation et instantané concurrent vérifiés. Rapport complet dans PR #6 et `.local-tools/tester-report-lot4.md`. Aucun défaut relevé. Lots 0–3 et politique agents précédemment intégrés.

Migration courante **b7f4208ac112**, après 8a95eb41f220 : singleton/epoch catalogue, dix triggers statement sous privilèges invoquant, normalisation SQL, ordre DB des audits. Contrats publics catalogue 1.0.0 préservés. Rayon : deux flux de même offset/limite ; continuer sur next_cursor même si items vide. Une Feature par course ; regroupement des communes au lot 5 UI. GET catalogue/map read-only REPEATABLE READ ; version cohérente, changement => curseur 409.

| Tâche | Responsable | État |
|---|---|---|
| L5-01 cadrage/checkpoint/Draft PR | Coordinator | IN_PROGRESS |
| L5-02 carte/données/filtres/périodes | Developer | TODO |
| L5-03 détails/mobile/erreurs/preuves | Developer | TODO |
| L5-04 revue indépendante SHA figé | Tester | TODO |
| L5-05 CI/fusion/bilan | Coordinator | TODO |

## Décisions propriétaire et restrictions

**Altitude 2,5D initial, Summit 3D à la demande.** Ouvrir le calendrier sélectionnera le mois affiché et le conservera au retour carte ; autres filtres et caméra préservés. Aucun arbitrage en attente. Mineur conforme aux contrats, technique autonome/documenté ; produit majeur consulté avec 2–3 options/recommandation. Silence jamais accord. Pas de collecte FFC live/régionale/récurrente, achat, mutation distante/production, déploiement ou publication finale. Données/HTML synthétiques ; droits et qualification FFC live ouverts. Carte providers fixés dans mission, aucun service payant ni téléchargement régional.

## Environnement et processus

Python 3.12.14 et paquets réutilisables : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Node cache Codex ; frontend/node_modules local. Binaires locaux frontend eslint/bin/eslint.js, vitest/vitest.mjs, vite/bin/vite.js évitent résolution pnpm réseau ; dernier Vitest threads maxWorkers1 : 3 tests réellement PASS. Toute nouvelle dépendance doit être épinglée/verrouillée.

PostgreSQL 17.11 actif uniquement **127.0.0.1:55434**, cluster `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`, redémarré sans initdb lors de la reprise du 11 novembre. Bases jetables distinctes `raceatlas_lot2_test` (Developer) / `raceatlas_lot2_review` (Tester), utilisateur `raceatlas_local`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Reviewer DB laissé avec 417 courses/audit synthétiques après probes, singleton restauré ; ne pas supposer seed vide. Tester a terminé tous tests/lectures. Aucun autre écrivain actif. Si preview durable nécessaire, utiliser une autre base locale pour ne pas concurrencer les tests.

Chromium `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Native DB/browser et Git métadonnées partagées requièrent exécution autorisée hors sandbox. Aucun rejet auto-review. Ne pas initdb/reseed aveuglément, ni arrêter les processus Node étrangers. Ancien pgdata-lot2 incomplet et copie deps partielle ignorés dans .local-tools.

Connecteur création PR 403, accès Git local autorisé a servi sans secrets exposés ni contournement. Scripts ignorés lot2/3/4-pr.py limités à leurs anciennes PR et bases ; adapter et vérifier avant usage pour lot 5. Ne jamais lancer un merge à l'aveugle.

## Prochaine action sûre

Publier cadrage/checkpoint, ouvrir Draft PR lot 5 et déléguer une tâche bornée au Developer, seul éditeur suivi. Proposer toute extension de métadonnées nécessaire avant de modifier les contrats. Aucun test lot 5 encore exécuté ; prochain gel seulement après code/tests/handoff/checkpoint, puis Tester et CI du même SHA.

Dernier checkpoint UTC : 2026-11-11T07:55:11Z

## Jalon WIP L5-A (2026-11-11T08:10Z)

L5-01 DONE : branche initiale563b49e publiée, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/7. L5-02/L5-03 IN_PROGRESS : modules temporels/API, filtres et détails React, regroupement communes/clusters MapLibre réel implémentés ; rendu navigateur pas encore validé. MapLibre5.11.0 installé via binaire pnpm10.20.0 en cache (wrapper système11 incompatible avec store10), cache MapLibre absent donc téléchargement borné autorisé. Aucun script de build de dépendance activé.

Extension technique approuvée par Coordinator : GET `/api/v1/catalog/options` indépendant des courses filtrées, catégories dynamiques triées ; schéma séparé1.0.0, collection OpenAPI1.1.0 additive, réponses catalogue/map/detail1.0.0 inchangées.3tests API PostgreSQL PASS en5,40s,20tests frontend temporels/cycleAPI/UI PASS en11,21s,26contratsPASS. ESLint et build passent (bundle MapLibre important signalé par Vite, à documenter). Pas de gel ni avis Tester.

Preview locale distincte créée vide par Coordinator : `raceatlas_map_demo` sur même serveur local. Migration head puis seed synthétique12courses réussis ; première tentative seed bloquée avant écriture par RACEATLAS_ENV=development invalide, corrigé en local. Pas de serveur preview durable actif à ce jalon. Ne pas réinitialiser les bases Reviewer/Developer pour preview. Seuls données et fournisseurs synthétiques dans les tests.

Prochaine action sûre actualisée : remplacer les assertions Chromium de démonstration par les interactions carte réelles avec style/DEM déterministes interceptés, puis inspecter captures desktop/mobile/échecs et corriger les défauts avant régression globale/handoff. Ancienne prochaine action cadrage est accomplie ; les paragraphes ci-dessus constituent l'état courant WIP.
