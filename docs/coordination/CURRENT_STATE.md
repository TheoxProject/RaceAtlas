# Point de reprise RaceAtlas

- Lot4 API catalogue/filtres ; branche `feature/catalog-filters`, worktree `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`.
- Base locale/distante vérifiée `48a2c3766276c92b2074139847c95e8d6a7b3916` (`origin/main`). Mission `docs/lot-4/mission.md`.
- Checkpoint initial à committer/pousser, Draft PR à ouvrir. Aucun candidat lot4 approuvé.

## Intégration confirmée

Lot3 DONE : https://github.com/TheoxProject/RaceAtlas/pull/5. Tester **APPROVE** SHA **54a14472222c0278017074a82ab097f3de8b50ac**, CI https://github.com/TheoxProject/RaceAtlas/actions/runs/42899767502 **success**, check integrated vert au même SHA, aucun autre statut requis en attente. Merge GitHub confirmé **48a2c3766276c92b2074139847c95e8d6a7b3916**, arbre identique au SHA approuvé (`git diff --exit-code` réussi). Workflow PR, pas de CI push main distincte attendue.

Preuves indépendantes :205pytest PASS (110lot3+95antérieurs dont3Chromium),26contrats,Ruff26,lint/build/pip et22assertions supplémentaires PASS. Deux cycles ont corrigé conflits d'alias puis preuves historiques effaçant une absence plus récente. Rapport final complet dans PR#5 et `.local-tools/tester-report-lot3.md`. Limitation locale : runner unitaire frontend timeout sans tests, pas de fauxPASS ; frontend/config inchangés,3Chromium locaux et3unitaires en CI exacte réussis. Lots0/1/2 et politique agents déjà fusionnés (lot2 PR#4, SHA revu511208b, mergef33d837).

Migration courante **8a95eb41f220**, après65107930ec01. Six tables audit/cache/révisions/alias et champ interne SourceRecord.presence_checked_at ; API publique inchangée. Baseline présence/absence immuable, historiques non autoritaires ; historical_duplicate sans mutation seulement après réussite effective d'un frais identique ; erreurs ne prêtent pas de fraîcheur. Backfill réel et égalité temporelle conservateurs.

| Tâche | Responsable | État |
|---|---|---|
| L4-01 mission/checkpoint/Draft PR | Coordinator | IN_PROGRESS |
| L4-02 validation/sélection/filtres | Developer | TODO |
| L4-03 pagination/carte/couverture/intégration | Developer | TODO |
| L4-04 revue indépendante SHA figé | Tester | TODO |
| L4-05 CI/fusion/bilan | Coordinator | TODO |

## Politique et limites

Autonomie technique ; mineur conforme aux contrats ; produit majeur/alternatives visibles soumis au propriétaire (question précise,2–3options et recommandation). Silence jamais accord, seules tâches indépendantes d'une décision pendante continuent. **Choix propriétaire explicite futur lot5 : Altitude2.5D initial, Summit3D à la demande.** Aucun arbitrage en attente. Aucune collecte FFC live/régionale, synchronisation récurrente, dépense, mutation distante/production, déploiement ou publication finale autorisé. Dialecte/données synthétiques, droits/qualification FFC live ouverts ; géocodeur injecté hors réseau, rectangle uniquement de plausibilité, pas GIS polygonal.

## Environnement et processus

Python3.12.14 : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, paquets déjà disponibles. Pip via runtime `C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -m pip --python <venvpython> check`. Node cache Codex, frontend/node_modules local et build prêt. Éviter wrapper pnpm qui peut tenter registre : binaires locaux eslint/bin/eslint.js,vitest/vitest.mjs,vite/bin/vite.js depuis frontend ; Vitest --pool=threads --maxWorkers=1 si pool fork indisponible, aucun succès sans tests exécutés.

PostgreSQL17.11 actif uniquement127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`. Bases jetables distinctes `raceatlas_lot2_test` (Developer) et `raceatlas_lot2_review` (Tester), utilisateur `raceatlas_local`. URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>` ; opt-in `RACEATLAS_DISPOSABLE_DB=1`. Browser `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Aucun test ni écrivain actif après lot3 ; cluster conservé. Ne pas initdb/reseed aveuglément ; tests isolés réinitialisent leurs tables. Ancien `.local-tools/pgdata-lot2` incomplet et copie deps partielle `.local-tools/frontend-deps-partial` à ignorer.

Native DB/Chromium requiert exécution autorisée hors sandbox ; Git métadonnées partagées hors worktree. Aucun rejet auto-review. Connecteur création PR403, fallback Git local autorisé réussi sans secret ni contournement. Scripts ignorés lot2/lot3-pr.py sont limités aux anciennes PR/bases : adapter puis vérifier numéros/SHA avant usage pour lot4. Ne jamais lancer leur merge à l'aveugle.

## Prochaine action sûre

Commit/push du cadrage et ouverture Draft PR lot4, puis délégation bornée au Developer sans autre éditeur suivi. Confirmer URL PR, head distant/base et environnement ; aucun test lot4 encore exécuté. Avant futur gel : checkpoint/handoff consolidés, puis preuves finales dans PR sans changer le SHA en revue.

Dernier checkpoint UTC : 2026-11-10T21:09:37Z
