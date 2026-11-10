# Point de reprise RaceAtlas

- Horodatage : **2026-11-10T14:48:15Z**.
- Lot actif : 2, adaptateur FFC isolé. Mission `docs/lot-2/mission.md` ; handoff `docs/lot-2/developer-handoff.md`.
- Worktree `C:/Users/theop/.codex/worktrees/add4/RaceAtlas` ; branche `feature/ffc-adapter`.
- Base `origin/main` vérifiée : `2e03cd83931d2297df0b3be830c35974f588fbb8`.
- Parent local/distant avant livraison développeur : `844168ae6564b8255208aca2acd5571eb87c0dc6` ; le commit contenant ce checkpoint produit le candidat. Exécuter `git rev-parse HEAD` et comparer au head distant/PR pour obtenir le SHA final. Ne plus éditer pendant revue.
- PR https://github.com/TheoxProject/RaceAtlas/pull/4, **Draft**, CI finale à observer après push ; aucun SHA lot 2 approuvé par Tester.
- Lots 0 et 1 DONE, PR #1/#2 fusionnées ; politique agents PR #3 fusionnée. Aucun audit complet à rejouer.

| Tâche | Responsable | État |
|---|---|---|
| L2-01 mission/checkpoint/Draft PR/environnement | Coordinator | DONE |
| L2-02 adaptateur et projection | Developer | DONE |
| L2-03 tests et handoff | Developer | DONE |
| L2-04 revue exacte et régression | Tester | TODO |
| L2-05 CI/fusion/bilan | Coordinator | TODO |

## Livré / validation

Parseur hors réseau strict/borné, observations typées, fenêtres effectives et diagnostics ; règles/restrictions par scope ; aucun fait dérivé du slug ni ID source de liste inventé. Projection ORM détachée, nouvelles identités opaques, révisions sous attestation complète et sans effacement de faits connus. HTML complet/participants exclus. Dialecte synthétique et absence de qualification live explicités dans `fixtures/ffc/README.md`.

Développeur : **76 pytest PASS en 31,99 s** au passage final (53 adaptateur, 23 socle dont 3 Chromium), migrations PostgreSQL aller-retour et API JSON Schema compris. Ruff lint/format PASS, 26 contrats Node PASS, `git diff --check` PASS. Coordinator : frontend ESLint PASS, Vitest 3/3 PASS, build PASS et pip check PASS (préliminaires). Aucun verdict Tester ni CI finale déclaré. Aucun défaut fonctionnel non résolu ; limites live/FFC non levées.

## Décisions et contraintes

Politique propriétaire : autonomie technique ; fonctionnel mineur conforme aux contrats ; consultation pour choix produit majeurs/alternatives visibles (2–3 options, recommandation). Le silence ne vaut jamais accord. Seules les tâches indépendantes d'une décision en attente continuent. Aucun arbitrage majeur identifié au lot 2.

Fixtures synthétiques uniquement. Pas de collecte FFC, déploiement, Neon, achat ou mutation production. Contrats lot 0 conservés. Phrase historique d'approbation du merge dans `docs/lot-0/delivery.md` alignée sur `AGENTS.md` dans commit initial. Droits FFC et futures opérations source soumis aux gates existants.

## Environnement / processus / précautions

Python 3.12.14 et paquets : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Python système est un alias Windows, ne pas l'utiliser aveuglément. Node/pnpm : cache Codex ; dépendances frontend installées offline dans ce worktree.

PostgreSQL 17.11 préparé par Coordinator : `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`, écoute **127.0.0.1:55434**. Bases locales jetables : `raceatlas_lot2_test` (Developer) et `raceatlas_lot2_review` (Tester), utilisateur local `raceatlas_local`. URL développeur `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test` ; remplacer uniquement nom de base par `_review` pour Tester. `RACEATLAS_DISPOSABLE_DB=1` obligatoire ; les tests réinitialisent cette base. Chromium `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`.

**Ne pas réinitialiser** le cluster actif ni tester simultanément sur même base. Premier initdb sandbox `.local-tools/pgdata-lot2` **incomplet**, processus arrêtés : ne pas utiliser. Copie frontend partielle parquée `.local-tools/frontend-deps-partial`, à ignorer. Aucun test développeur actif à la livraison ; PostgreSQL reste actif pour Tester.

Fetch/branche/commit/push nécessitent autorisation sandbox pour métadonnées Git partagées hors worktree. Création PR connecteur : **403 Resource not accessible by integration** ; fallback local Git credential autorisé réussi, script ignoré `.local-tools/lot2-pr.py`, aucune exposition d'identifiant ni contournement de protection. Processus natifs PostgreSQL/Chromium hors sandbox nécessaires (enfants natifs pouvant bloquer sous sandbox).

## Prochaine action sûre

Après commit/push développeur : **figer `git rev-parse HEAD`, vérifier head PR #4 et demander la revue indépendante Tester de ce SHA exact**, sur `raceatlas_lot2_review`. Suivre CI du même SHA. Ne pas modifier ce checkpoint pendant revue ; utiliser description PR pour preuves finales. Sans Tester et CI verts au même SHA, garder Draft et ne pas commencer lot 3.
