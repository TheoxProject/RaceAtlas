# RaceAtlas après le gel de la V1

Point du 19 novembre 2026 à 12:11 UTC. Le tag `v1.0.0` identifie `3967729a21ee8ab8086180e27f1fa24841c54020`. La CI `integrated` de ce commit a réussi. Les PR 21 et 22 et leurs preuves sont référencées dans le dossier de validation. [Validation V1](../readiness/validation-v1.md)

| Tâche | État | Résultat attendu |
|---|---|---|
| DOC-01 · Développeur | DONE | README V1 et commandes Windows à jour. Les documents de travail remplacés restent accessibles via le tag figé. Les guides actifs, preuves d’intégration et contrats sont conservés. |
| DOC-02 · Coordinateur et Testeur | IN_PROGRESS | Publier la branche documentaire, vérifier son SHA figé et appliquer les contrôles de fusion. |
| Suite après V1 | TODO | Cadrer l’ajout d’épreuves, la gestion des catégories, la simplification et l’éventuelle transition vers Neon Auth. |

**Branche.** `feature/v1-documentation-cleanup` dans le worktree `d76c`, depuis le commit tagué. L’état du SHA final, du Testeur et de la CI est consigné dans la PR dès l’ouverture et le gel. Le nettoyage documentaire ne nécessite ni démarrage de PostgreSQL ni opération sur les ressources distantes.

**Prochaine action.** Publier le commit documentaire et ouvrir la PR en Draft. Vérifier les liens locaux et la portée du diff, puis engager la revue et les contrôles GitHub du SHA. Ne pas rejouer le chargement ponctuel des courses ni la géolocalisation validée lors de la V1.
