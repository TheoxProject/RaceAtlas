# Point de reprise RaceAtlas

- Horodatage : **2026-11-10T15:16:44Z**, lot 3 WIP après service/cache.
- Branche `feature/auditable-sync`, worktree `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`.
- Base `origin/main` : `f33d837844abdc51ebcafc066da3c16cb4982f34`. Parent avant ce checkpoint : `ff351d9c762ea9075efa8f8683ab098777246c5d` ; relever HEAD après commit/push.
- Draft PR https://github.com/TheoxProject/RaceAtlas/pull/5 ; CI intermédiaire ff351d9 SUCCESS https://github.com/TheoxProject/RaceAtlas/actions/runs/42841269435. Aucun candidat lot 3 figé ni approuvé.
- Mission `docs/lot-3/mission.md`.

## Intégration précédente confirmée

Lot 2 DONE : PR https://github.com/TheoxProject/RaceAtlas/pull/4, Tester APPROVE `511208b7d5142f708106a3d4a8f51d170fb3e148`, CI success https://github.com/TheoxProject/RaceAtlas/actions/runs/42839321426, merge confirmé `f33d837844abdc51ebcafc066da3c16cb4982f34`, arbre identique au SHA testé. Lots 0/1 et politique PR #3 déjà fusionnés. Dialecte HTML synthétique et droits FFC encore ouverts avant exploitation.

| Tâche | Responsable | État |
|---|---|---|
| L3-01 cadrage/checkpoint/Draft PR | Coordinator | DONE |
| L3-02 import/audit/identité | Developer | IN_PROGRESS, service et35 tests ciblés PASS |
| L3-03 communes/cache/intégration/handoff | Developer | IN_PROGRESS, cache testé, docs/finalisation restantes |
| L3-04 revue indépendante SHA figé | Tester | TODO |
| L3-05 CI/fusion/bilan | Coordinator | TODO |

## Livré et vérifications actuelles

Six tables/migration audit/cache/révisions/alias ; empreintes métier stables sans tokens/checkdates ; service local possédant ses transactions et verrou PostgreSQL ; savepoints par item, audit durable des erreurs, alias explicitement prouvés, graphes non rapprochés par rang/nom. LocationFact explicite, fournisseur injecté sans client réseau, cache positif7j/négatif1j/erreur5min séparé par version/département. Faits connus et centres existants préservés ; conflit/ambiguïté mis en revue/erreur.

**35 tests ciblés PASS en7,02s** sur PostgreSQL17.11 réel, migration upgrade/check/downgrade/upgrade/check compris. Ruff PASS. Pas encore de suite globale lot3 ni revue/CI du prochain SHA ; ce checkpoint WIP n'est pas fusionnable.

Décisions techniques : faits positifs de fenêtres indépendantes autorisés, mais **toute absence différée jusqu'à réussite de tout le périmètre du run** ; présence globale dédupliquée protège les chevauchements. Textes source normalisés des listes conservés comme signaux d'ambiguïté, jamais comme preuve positive d'identité. Une réorganisation ambiguë conserve intégralement le graphe existant. Groupe/alias sous preuve référencée et révision attendue ; preuves d'identité enregistrées dans audit item. Révisions métier minimales sans archive HTML/participants. Aucune garantie d'audit si PostgreSQL lui-même est indisponible.

## Politique et restrictions

Autonomie technique documentée ; fonctionnel mineur conforme aux contrats ; consultation pour choix produit majeurs/alternatives visibles (2–3 options, recommandation). Silence jamais accord ; seules tâches indépendantes d'une décision en attente continuent. Aucun arbitrage majeur en attente. Aucun déploiement, achat, collecte FFC live/régionale, mutation distante/production ou publication finale autorisé. Aucune voie réseau/schedule ajoutée.

## Environnement et processus

Python3.12.14 : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Pip via runtime Python cache Codex `-m pip --python <venvpython> check`. Node/pnpm cache Codex, frontend installé offline/build prêt ; pnpm CLI `C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.cjs`.

PostgreSQL17.11 actif **127.0.0.1:55434**, cluster `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`. Bases jetables `raceatlas_lot2_test` (Developer), `raceatlas_lot2_review` (Tester), utilisateur `raceatlas_local`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, `RACEATLAS_DISPOSABLE_DB=1`. Tests réinitialisent leurs tables, dont audits/cache. Ne pas tester simultanément sur même base. Browser `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Aucun test actif après ce checkpoint ; cluster laissé actif.

Ne pas relancer initdb ; ancien `.local-tools/pgdata-lot2` incomplet à ignorer, copie deps partielle `.local-tools/frontend-deps-partial` à ignorer. Processus natifs DB/Chromium hors sandbox ; Git demande autorisation métadonnées partagées. Aucun rejet auto-review. Connecteur création PR 403 ; fallback accès Git local autorisé réussi sans secret exposé. `.local-tools/lot2-pr.py` limité ancienne PR4/base : ne pas lancer aveuglément pour lot3.

## Prochaine action sûre

Terminer cas négatifs d'intégration/contraintes et documentation Windows/handoff, puis exécuter suite globale (backend+Chromium, contrats, frontend/build pertinents) sur base développeur isolée. Mettre à jour ce checkpoint avant candidat final, committer/pousser, figer HEAD et demander Tester. Ne pas fusionner ni commencer lot4 avant gates lot3.
