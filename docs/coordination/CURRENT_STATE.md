# Ouverture publique de RaceAtlas

Point du 2026-11-19 08:08:11 UTC. Base GitHub vérifiée `9f9096d04c21c488512969f173a5d81bfbe33bed` ([PR du filtre Discipline](https://github.com/TheoxProject/RaceAtlas/pull/20)). Worktree `C:/Users/theop/.codex/worktrees/d76c/RaceAtlas`, branche `feature/public-raceatlas`. Le propriétaire a demandé la suppression du mode preview, le contrôle des localisations du catalogue 2027 et des couleurs par type d’épreuve.

| Tâche | État | Critère observable |
|---|---|---|
| PUBLIC-01 · Développeur | DONE | Le lanceur public démarre sans identifiants partagés. L’authentification personnelle dépend des sessions. |
| PUBLIC-02 · Développeur | DONE | La carte, le calendrier et les résultats partagent les couleurs et les libellés. Un groupe mixte utilise une couleur neutre. |
| PUBLIC-03 · Coordinateur | DONE | Après accord explicite du propriétaire, trois centres officiels sont associés à neuf courses 2027 dans Neon. |
| PUBLIC-04 · Testeur et Coordinateur | IN_PROGRESS | Revue indépendante, CI intégrée sur le SHA figé, fusion et contrôle de main. Le propriétaire crée le nouveau service Render. |

**Existant.** Le service Render historique sert la base vérifiée, avec les déploiements automatiques désactivés. Le propriétaire créera lui-même le nouveau service public. Neon est à la révision `b806e44f7901`. Le premier contrôle a confirmé 94 courses FFC en 2027, zéro centre associé et zéro commune dans les observations d’import. L’import ponctuel est terminé. [Bilan du chargement](https://github.com/TheoxProject/RaceAtlas/pull/19#issuecomment-6987381129)

**Localisations vérifiées.** Une transaction Neon a associé Guilherand-Granges (une course), Montélimar (deux) et Saint-Marcellin (six) à neuf identités FFC exactes encore sans commune. La lecture post-transaction a confirmé neuf courses localisées, 85 non localisées et trois centres officiels en cache. La Faun Drôme Classic reste non localisée à cause d’un désaccord de département. [Faun Ardèche Classic](https://boucles-drome-ardeche.fr/faun-ardeche-classic/) · [Corima](https://www.corimadromeprovencale.com/) · [Saint-Marcellin et sources régionales](https://cyclo-cross.fr/courses/cyclo-cross-saint-marcellin-2027/) · [API officielle](https://geo.api.gouv.fr/decoupage-administratif/communes)

**Validation.** [Draft PR 21](https://github.com/TheoxProject/RaceAtlas/pull/21), checkpoint initial `d874327a5e877342d149dc7f44f02bb668f6c081`, [contrôle development réussi](https://github.com/TheoxProject/RaceAtlas/actions/runs/44483808354). Le Développeur a passé 141 tests frontend, le lint, le build et Ruff. PostgreSQL 17.11 jetable sur le port local 55463 avec les bases distinctes `raceatlas_public_test` et `raceatlas_public_review`. Les résultats du SHA figé seront consignés dans la PR.

**Prochaine action.** Publier le commit de livraison et lancer la revue indépendante et le contrôle `integrated` sur ce SHA. La géolocalisation ponctuelle est terminée. Vérifier les associations existantes avant toute opération complémentaire.
