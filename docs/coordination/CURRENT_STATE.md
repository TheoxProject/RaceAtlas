# Point de reprise RaceAtlas

- Horodatage : 2026-11-10T15:03:30Z (initialisation lot 3).
- Lot 3 : synchronisation auditable et communes ; mission `docs/lot-3/mission.md`.
- Worktree `C:/Users/theop/.codex/worktrees/add4/RaceAtlas` ; branche `feature/auditable-sync`.
- Base locale/distante après fetch : `f33d837844abdc51ebcafc066da3c16cb4982f34` (`origin/main`). Branche publiée, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/5 ; checkpoint initial `d4f55af6740a52964eb8e68df4273af6346294be`. Aucun candidat lot 3 validé.

## Intégration précédente confirmée

Lot 2 DONE : https://github.com/TheoxProject/RaceAtlas/pull/4. Tester **APPROVE** au SHA **511208b7d5142f708106a3d4a8f51d170fb3e148** ; CI https://github.com/TheoxProject/RaceAtlas/actions/runs/42839321426 **success**. Merge GitHub **f33d837844abdc51ebcafc066da3c16cb4982f34** confirmé, arbre identique au SHA testé (`git diff --exit-code` réussi). Workflow sur PR, pas de CI push main distincte attendue.

Preuves : 95 pytest (72 adaptateur, 23 socle dont 3 Chromium), 26 contrats, 3 React, lint/format/build/pip et 18 probes indépendantes PASS. Deux défauts de la première revue corrigés en un cycle. Rapport final dans PR #4 et `.local-tools/tester-report-lot2.md`. Lots 0/1 et politique PR #3 déjà fusionnés. Limite : dialecte HTML synthétique, qualification live et droits FFC encore ouverts avant exploitation.

| Tâche | Responsable | État |
|---|---|---|
| L3-01 cadrage/checkpoint/Draft PR | Coordinator | DONE |
| L3-02 import/audit/identité | Developer | IN_PROGRESS |
| L3-03 communes/cache/intégration/handoff | Developer | TODO |
| L3-04 revue indépendante SHA figé | Tester | TODO |
| L3-05 CI/fusion/bilan | Coordinator | TODO |

## Politique et restrictions

Autonomie technique documentée ; fonctionnel mineur conforme aux contrats ; consultation pour choix produit majeurs/alternatives visibles, question précise avec 2–3 options et recommandation. Silence jamais considéré comme accord ; seules tâches indépendantes d'une décision en attente continuent. Aucun arbitrage majeur en attente. Aucun déploiement, achat, collecte FFC live/régionale, mutation distante/production ni publication finale autorisé.

## Environnement et processus

Python 3.12.14/paquets : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Pip via runtime Python `C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -m pip --python <venvpython> check`. Node/pnpm cache Codex ; frontend installé offline/build prêt. pnpm CLI `C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.cjs`.

PostgreSQL 17.11 actif uniquement `127.0.0.1:55434`, cluster `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`. Bases jetables distinctes `raceatlas_lot2_test` (Developer) / `raceatlas_lot2_review` (Tester), utilisateur `raceatlas_local`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Réutilisables après migrations ; jamais tests concurrents sur même base. Browser `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Aucun test/agent écrivain actif après lot 2.

Ne pas relancer initdb du cluster actif ; `.local-tools/pgdata-lot2` est un ancien initdb sandbox incomplet à ignorer. Copie deps partielle `.local-tools/frontend-deps-partial` à ignorer. Processus natifs DB/Chromium hors sandbox ; Git nécessite autorisation pour métadonnées partagées hors worktree. Aucun rejet auto-review.

Connecteur création PR : 403 Resource not accessible by integration ; fallback accès Git local configuré réussi, sans secrets affichés ni contournement. `.local-tools/lot2-pr.py` est limité à PR 4 et ancienne base : **ne pas lancer pour lot 3 sans adaptation et contrôle des SHA**.

## Prochaine action sûre

Commit/push du cadrage et ouverture Draft PR lot 3, puis délégation bornée au Developer. Confirmer URL PR, SHA distant et absence d'autre écrivain. Aucun test lot 3 exécuté ni verdict acquis. Preuves finales dans la description PR sans altérer le SHA en revue.



## Étape développeur L3-A — WIP publiable

Modèles/migration statique ajoutés : import_run/window/item, source_alias, source_revision, geocode_cache. Types de batches explicites et empreinte métier indépendante des tokens/IDs/contrôles et espaces de présentation ; restrictions corrélées et ordre des scopes conservés pour déceler les réorganisations ambiguës. Deux tests d'empreinte réussis. Migration autogénérée en comparant uniquement la base PostgreSQL locale développeur puis relue ; aucune table historique altérée. Service, géocodage et tests d'intégration restent à réaliser ; aucune validation finale revendiquée.

Décision technique : importer les faits positifs des fenêtres indépendantes mais **différer toute inférence d'absence jusqu'à réussite du périmètre complet du run**. Dédupliquer les clés globalement ; présence dans une fenêtre empêche une fausse absence dans une autre. Cache géocode positif/négatif/versionné ; erreur/ambiguïté/mismatch bloque l'inférence d'absence. LocationFact explicite liée à une SourceKey et preuve ; aucune déduction du titre/slug.

Prochaine action sûre : implémenter le service transactionnel et le résolveur injecté, puis tester migration et imports réels sur PostgreSQL local jetable développeur. Ne pas lancer d'import source ou de synchronisation active.
