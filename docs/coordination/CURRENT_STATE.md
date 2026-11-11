# Point de reprise RaceAtlas

- Lot4 API catalogue/filtres ; branche `feature/catalog-filters`, worktree `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`.
- Base locale/distante vérifiée `48a2c3766276c92b2074139847c95e8d6a7b3916` (`origin/main`). Mission `docs/lot-4/mission.md`.
- Draft PR https://github.com/TheoxProject/RaceAtlas/pull/6 ; checkpoint initial d42032729b1b04cc62d5b9df0de00eecfed160d1 publié. Jalon courant WIP avant pagination/concurrence complètes, aucun candidat lot4 approuvé.

## Intégration confirmée

Lot3 DONE : https://github.com/TheoxProject/RaceAtlas/pull/5. Tester **APPROVE** SHA **54a14472222c0278017074a82ab097f3de8b50ac**, CI https://github.com/TheoxProject/RaceAtlas/actions/runs/42899767502 **success**, check integrated vert au même SHA, aucun autre statut requis en attente. Merge GitHub confirmé **48a2c3766276c92b2074139847c95e8d6a7b3916**, arbre identique au SHA approuvé (`git diff --exit-code` réussi). Workflow PR, pas de CI push main distincte attendue.

Preuves indépendantes :205pytest PASS (110lot3+95antérieurs dont3Chromium),26contrats,Ruff26,lint/build/pip et22assertions supplémentaires PASS. Deux cycles ont corrigé conflits d'alias puis preuves historiques effaçant une absence plus récente. Rapport final complet dans PR#5 et `.local-tools/tester-report-lot3.md`. Limitation locale : runner unitaire frontend timeout sans tests, pas de fauxPASS ; frontend/config inchangés,3Chromium locaux et3unitaires en CI exacte réussis. Lots0/1/2 et politique agents déjà fusionnés (lot2 PR#4, SHA revu511208b, mergef33d837).

Migration courante **8a95eb41f220**, après65107930ec01. Six tables audit/cache/révisions/alias et champ interne SourceRecord.presence_checked_at ; API publique inchangée. Baseline présence/absence immuable, historiques non autoritaires ; historical_duplicate sans mutation seulement après réussite effective d'un frais identique ; erreurs ne prêtent pas de fraîcheur. Backfill réel et égalité temporelle conservateurs.

| Tâche | Responsable | État |
|---|---|---|
| L4-01 mission/checkpoint/Draft PR | Coordinator | DONE |
| L4-02 validation/sélection/filtres | Developer | IN_PROGRESS,41tests ciblés PASS |
| L4-03 pagination/carte/couverture/intégration | Developer | IN_PROGRESS |
| L4-04 revue indépendante SHA figé | Tester | TODO |
| L4-05 CI/fusion/bilan | Coordinator | TODO |

## Politique et limites

Autonomie technique ; mineur conforme aux contrats ; produit majeur/alternatives visibles soumis au propriétaire (question précise,2–3options et recommandation). Silence jamais accord, seules tâches indépendantes d'une décision pendante continuent. **Choix propriétaire explicites futurs lots5/6 : Altitude2.5D initial, Summit3D à la demande ; ouvrir le calendrier passe la période partagée au mois affiché, conservé au retour carte, autres filtres et caméra préservés.** Aucun arbitrage en attente. Aucune collecte FFC live/régionale, synchronisation récurrente, dépense, mutation distante/production, déploiement ou publication finale autorisé. Dialecte/données synthétiques, droits/qualification FFC live ouverts ; géocodeur injecté hors réseau, rectangle uniquement de plausibilité, pas GIS polygonal.

## Environnement et processus

Python3.12.14 : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, paquets déjà disponibles. Pip via runtime `C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -m pip --python <venvpython> check`. Node cache Codex, frontend/node_modules local et build prêt. Éviter wrapper pnpm qui peut tenter registre : binaires locaux eslint/bin/eslint.js,vitest/vitest.mjs,vite/bin/vite.js depuis frontend ; Vitest --pool=threads --maxWorkers=1 si pool fork indisponible, aucun succès sans tests exécutés.

PostgreSQL17.11 actif uniquement127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`. Bases jetables distinctes `raceatlas_lot2_test` (Developer) et `raceatlas_lot2_review` (Tester), utilisateur `raceatlas_local`. URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>` ; opt-in `RACEATLAS_DISPOSABLE_DB=1`. Browser `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Aucun test ni écrivain actif après lot3 ; cluster conservé. Ne pas initdb/reseed aveuglément ; tests isolés réinitialisent leurs tables. Ancien `.local-tools/pgdata-lot2` incomplet et copie deps partielle `.local-tools/frontend-deps-partial` à ignorer.

Native DB/Chromium requiert exécution autorisée hors sandbox ; Git métadonnées partagées hors worktree. Aucun rejet auto-review. Connecteur création PR403, fallback Git local autorisé réussi sans secret ni contournement. Scripts ignorés lot2/lot3-pr.py sont limités aux anciennes PR/bases : adapter puis vérifier numéros/SHA avant usage pour lot4. Ne jamais lancer leur merge à l'aveugle.

## Jalon WIP L4-A

Validation JSON/schema stricte et paramètres, service SQL unique, endpoints réels, scope ET/OU exact, rayon/communes, projection une Feature par course, pagination partagée à deux flux pour rayon (confirmées et candidates non localisées). Chaque flux a le même offset et limite ; curseur commun race/map, aucun doublon entre pages, items vides avec continuation possibles quand seules candidates restent. Vérifications adversariales de pagination/concurrence/couverture encore à compléter.

Nouvelle migration statique **b7f4208ac112** : compteur catalogue singleton+epoch, triggers par statement sur tables influençant réponses et audits, normalisation SQL sans extension, ordre d'exécution monotone ImportRun.catalog_order. Anciennes migrations inchangées. Triggers sous privilèges invoquant par défaut, aucun GRANT/SECURITY DEFINER. Historique d'audits antérieur à l'ordre marqué conservativement incomplet jusqu'à nouveau contrôle ; aucune sélection aléatoire par UUID/horloge source. Read-only REPEATABLE READ pour version/compteurs/items/couverture cohérents ; graphes uniquement pour la page<=200.

jsonschema4.25.1 déjà disponible promu aux dépendances runtime épinglées (requirements/pyproject), pas de réinstallation. **41tests ciblés PASS en6,41s** :31validations +9scénarios contractuels viaFlask/PostgreSQL +témoins corrélés, migration aller-retour/check comprise. RuffPASS. Un attendu de nouveau test avait omis le préfixe réel d'un scope, corrigé contre fixture. Aucun test global lot4 ni Tester acquis.

## Jalon WIP L4-B

Reprise vérifiée le 2026-11-11 sur `c707d08f70470eabe90c27062a583daa6e53e8d5`, distant identique, CI WIP verte (run42905266499), base inchangée. Cluster existant redémarré sans initdb ni reseed ; seul Developer utilise `_test`.

**98 tests catalogue ciblés PASS en23,16s**, PostgreSQL réel et migration aller-retour/check inclus. Ajouts : parcours limite1 des neuf scénarios, parité carte/catalogue, invalidation des dix triggers, rollback, seed répété, catégorie u15 dynamique, recherche nom/commune/organisateur, bornes civiles multijours, commit concurrent réel entre compteurs et graphes, adaptateur→sync→API, dernier échec et reprise, audits historiques conservateurs, erreurs publiques malformées. Un défaut réel de normalisation d'espace Unicode NBSP corrigé dans la nouvelle migration ; validation rejette également NUL et surrogates isolés avant accès DB. Premiers échecs de tests corrigés : forme Error plate du contrat et suppression ORM requise par les FK. RuffPASS. Depuis ces98tests, extension des preuves de flux rayon vide avec continuation et de projection de deux imports au même centre ; nouveau run/global encore à exécuter. Aucun candidat figé ni avis Tester.

## Prochaine action sûre

Exécuter le backend global avec PostgreSQL `_test` et Chromium existants, puis contrats Node/lint/build/tests frontend et handoff avant gel SHA/Tester. Ne pas fusionner ce WIP.

Dernier checkpoint UTC : 2026-11-11T07:36:08Z
