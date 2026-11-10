# Point de reprise RaceAtlas

- Horodatage : 2026-11-10, UTC (initialisation ; horodatage précis au prochain checkpoint).
- Lot actif : 2, adaptateur FFC isolé. Mission : `docs/lot-2/mission.md`.
- Worktree : `C:/Users/theop/.codex/worktrees/add4/RaceAtlas` ; branche `feature/ffc-adapter`.
- Base locale et `origin/main` vérifiés après fetch : `2e03cd83931d2297df0b3be830c35974f588fbb8`.
- Branche distante lot 2 / PR / CI : à créer après ce checkpoint initial ; aucun SHA lot 2 approuvé.
- Lots 0 et 1 : DONE, PR #1 et #2 fusionnées ; politique agents PR #3 fusionnée. Aucun audit complet à rejouer.

| Tâche | Responsable | État |
|---|---|---|
| L2-01 mission/checkpoint/Draft PR/environnement | Coordinator | IN_PROGRESS |
| L2-02 adaptateur et projection | Developer | TODO |
| L2-03 tests et handoff | Developer | TODO |
| L2-04 revue exacte et régression | Tester | TODO |
| L2-05 CI/fusion/bilan | Coordinator | TODO |

## Décisions et contraintes

Politique propriétaire : autonomie technique ; choix fonctionnels mineurs conformes aux contrats ; consultation pour choix produit majeurs ou alternatives visibles (2–3 options, recommandation). Le silence ne vaut jamais accord. Poursuivre seulement les tâches indépendantes d'une décision en attente. Aucun arbitrage majeur identifié au lot 2.

Fixtures synthétiques uniquement. Pas de collecte FFC, déploiement, Neon, achat ou mutation production. Contrats lot 0 conservés. `docs/AGENT_WORKFLOW.md` est déjà aligné ; la phrase historique de validation propriétaire dans `docs/lot-0/delivery.md` doit être alignée dans ce lot.

## Environnement / processus

Worktree propre avant initialisation, checkout initial détaché, désormais branche dédiée. Aucun Python/Node/PostgreSQL actif observé. Caches existants dans `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas` : `.venv`, `frontend/node_modules`, `.local-tools/pgsql`, `.local-tools/browsers`, anciens clusters jetables. Vérifier compatibilité avant réutilisation ; ne pas redémarrer/réinitialiser aveuglément un ancien cluster. Python de commande système est un alias Windows ; runtime réel disponible dans le cache Codex.

Fetch/création de branche ont nécessité l'autorisation sandbox pour les métadonnées Git partagées hors worktree ; opérations réussies. Aucun échec d'approbation automatique. Aucun processus long lancé et aucune migration exécutée.

## Validation et prochaine action

Aucun nouveau test exécuté ; aucune approbation Tester du lot 2. Prochaine action sûre : committer/pousser ce cadrage et ouvrir la Draft PR, puis déléguer L2-02/L2-03 au Developer dans ce worktree sans autre éditeur concurrent. Confirmer SHA distant et URL PR. Ne pas déclarer ce checkpoint fusionnable.
