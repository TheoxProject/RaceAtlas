# Mission approuvée et limites

Le propriétaire valide l'architecture générale et autorise le lot 0 le 10 novembre 2026 : qualification de la complétude FFC, identités des listes, ambiguïtés d'admissibilité, spécifications versionnées et contrats permettant une première carte sur fixtures. Travail sur `feature/source-contracts`, base `ff16c6366333fcabcfea206e05d0efbc1cce5ff1`, worktree isolé. Aucun merge sur `main`.

Le coordinateur établit les preuves réseau ; developer rédige les spécifications et outils locaux ; tester examine indépendamment le SHA figé. Les corrections donnent lieu à un nouveau SHA et une nouvelle revue (maximum trois cycles avant arbitrage). L'autorisation de développement n'accorde aucun droit détenu par la FFC et ne permet pas de collecte massive, déploiement ou dépense.

## Acceptation du lot 0

| Critère | Preuve attendue |
|---|---|
| Complétude qualifiée sans conclusion globale abusive | Requêtes bornées datées, fenêtre effective, compte affiché, nombre de clés, limites et contre-exemple |
| Identité indépendante du nom/date/parent | Contrat stable et scénario de révision conservant les identifiants |
| Listes non rapprochées par position | État d'identité incertain, gel du rapprochement ambigu, besoin de confirmation explicite |
| Admissibilité ET exacte | Une même liste ; restrictions conservées dans chaque règle ; cas négatifs entre listes et entre épreuves |
| Première carte possible hors réseau | Catalogue synthétique, réponse carte, règles temporelles, coordonnées nullables et styles décrits |
| Contrats contrôlables | Schéma JSON, OpenAPI 3.1, références résolues et tests locaux positifs/négatifs |
| Exploitation séparée de la conception | Gates juridiques, imports, hébergement et RC identifiés |
| Intégration progressive | Chaque prochain lot vérifie ses parcours avec les lots précédents ; validation V1 globale prévue |

La qualification partielle d'une source n'empêche pas d'accepter les contrats pour les fixtures. Elle interdit de déclarer une ingestion annuelle exhaustive prête à exploiter.
