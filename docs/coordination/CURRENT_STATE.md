# Ouverture publique de RaceAtlas

Point du 2026-11-19 07:57:40 UTC. Base GitHub vérifiée `9f9096d04c21c488512969f173a5d81bfbe33bed` ([PR du filtre Discipline](https://github.com/TheoxProject/RaceAtlas/pull/20)). Worktree `C:/Users/theop/.codex/worktrees/d76c/RaceAtlas`, branche `feature/public-raceatlas`. Le propriétaire a demandé la suppression du mode preview, le contrôle des localisations du catalogue 2027 et des couleurs par type d’épreuve.

| Tâche | État | Critère observable |
|---|---|---|
| PUBLIC-01 · Développeur | IN_PROGRESS | Démarrer sans identifiants partagés. Ouvrir carte, calendrier et catalogue anonymement, contrôler les API personnelles par session. |
| PUBLIC-02 · Développeur | IN_PROGRESS | Distinguer les types par des couleurs et des libellés cohérents sur la carte et le calendrier. |
| PUBLIC-03 · Coordinateur | IN_PROGRESS | Associer uniquement des centres établis à partir d’une commune attestée. Les autres courses restent accessibles parmi les non-localisées. |
| PUBLIC-04 · Testeur et Coordinateur | TODO | Revue indépendante, CI intégrée sur le SHA figé, fusion, contrôle de main puis déploiement manuel et vérification anonyme. |

**Existant.** Render sert la base vérifiée sur le service existant, avec les déploiements automatiques désactivés. Neon est à la révision `b806e44f7901`. La lecture SQL du catalogue 2027 a confirmé 94 courses FFC, zéro centre associé et zéro commune enregistrée dans les observations d’import. Aucune écriture. L’import ponctuel est terminé et ne doit pas être rejoué. [Bilan et observations du catalogue](https://github.com/TheoxProject/RaceAtlas/pull/19#issuecomment-6987381129)

**Validation à venir.** Le SHA de travail part de la base ci-dessus. Aucun SHA de cette branche n’a encore été revu. Utiliser des environnements Python/Node locaux et PostgreSQL jetable ou le service PostgreSQL de la CI pour les tests, en séparant les bases du Développeur et du Testeur.

**Prochaine action.** Publier ce checkpoint et ouvrir la Draft PR, puis examiner les premières modifications du Développeur.
