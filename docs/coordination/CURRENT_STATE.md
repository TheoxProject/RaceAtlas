# Ouverture publique de RaceAtlas

Point du 2026-11-19 09:25:20 UTC. Base GitHub vérifiée `37085644e9fc03e954b8105679ff3ed45011c6d6`. Worktree `C:/Users/theop/.codex/worktrees/d76c/RaceAtlas`, branche `fix/signup-browser-framebuffer`. Le propriétaire a demandé la suppression du mode preview, le contrôle des localisations du catalogue 2027 et des couleurs par type d’épreuve.

| Tâche | État | Critère observable |
|---|---|---|
| PUBLIC-01 · Développeur | DONE | Le lanceur public démarre sans identifiants partagés. L’authentification personnelle dépend des sessions. |
| PUBLIC-02 · Développeur | DONE | La carte, le calendrier et les résultats partagent les couleurs et les libellés. Un groupe mixte utilise une couleur neutre. |
| PUBLIC-03 · Coordinateur | DONE | Après accord explicite du propriétaire, trois centres officiels sont associés à neuf courses 2027 dans Neon. |
| PUBLIC-04 · Testeur et Coordinateur | IN_PROGRESS | PR 21 fusionnée. Un test Chromium intermittent échoue après la fusion. Correctif de test en validation. |

**Render et Neon.** Render a créé le service Free `raceatlas` lors d’une synchronisation Blueprint après la fusion. Le build a réussi, puis le lanceur a rejeté la configuration `DATABASE_URL`. Le propriétaire configure le nouveau service. L’ancien service sert son déploiement précédent. Neon est à la révision `b806e44f7901`. L’import ponctuel FFC est terminé. [Bilan du chargement](https://github.com/TheoxProject/RaceAtlas/pull/19#issuecomment-6987381129)

**Localisations vérifiées.** Une transaction Neon a associé Guilherand-Granges (une course), Montélimar (deux) et Saint-Marcellin (six) à neuf identités FFC exactes encore sans commune. La lecture post-transaction a confirmé neuf courses localisées, 85 non localisées et trois centres officiels en cache. La Faun Drôme Classic reste non localisée à cause d’un désaccord de département. [Faun Ardèche Classic](https://boucles-drome-ardeche.fr/faun-ardeche-classic/) · [Corima](https://www.corimadromeprovencale.com/) · [Saint-Marcellin et sources régionales](https://cyclo-cross.fr/courses/cyclo-cross-saint-marcellin-2027/) · [API officielle](https://geo.api.gouv.fr/decoupage-administratif/communes)

**Validation de la V1 publique.** [PR 21](https://github.com/TheoxProject/RaceAtlas/pull/21). Le Testeur a approuvé `d400bf471700ca28064228d2b81800b75a3a455a`, avec deux contrôles intégrés réussis et un arbre identique à celui du merge. Sur `main`, les tentatives 1 et 3 ont passé 1 051 tests et échoué sur le délai Summit dans le scénario d’inscription desktop. Les diagnostics montraient l’inclinaison à 60°. La tentative 2 a passé le scénario puis atteint la limite globale du job après dix minutes d’installation Chromium. Le Testeur a passé le scénario seul sur le code fusionné. [CI main](https://github.com/TheoxProject/RaceAtlas/actions/runs/44488466296)

**Correctif.** La [Draft PR 22](https://github.com/TheoxProject/RaceAtlas/pull/22) réutilise la limite de framebuffer logiciel dans le scénario d’inscription. Le Développeur et le Testeur ont passé ce scénario. [La CI de `efd6ba9`](https://github.com/TheoxProject/RaceAtlas/actions/runs/44494648566) a passé l’inscription et 1 050 autres tests. Le test voisin de saison a mesuré un passage de 667 à 672 px de hauteur CSS lorsque le moteur a recalculé le canevas, avec la même caméra. Le helper synchronise maintenant le canevas avec son conteneur avant de mesurer le framebuffer, en conservant les assertions strictes. Ruff et `git diff --check` passent. PostgreSQL 17.11 jetable sur le port local 55463 avec les bases distinctes `raceatlas_public_test` et `raceatlas_public_review`.

**Prochaine action.** Publier le helper corrigé et obtenir de nouveaux contrôles indépendants et GitHub sur ce SHA. La géolocalisation ponctuelle est terminée. Vérifier les associations existantes avant toute opération complémentaire.
