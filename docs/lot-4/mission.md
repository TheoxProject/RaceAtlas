# Lot 4 — API catalogue et sélection partagée

Base vérifiée : `48a2c3766276c92b2074139847c95e8d6a7b3916`, lot 3 fusionné (PR #5), arbre identique au SHA approuvé `54a14472222c0278017074a82ab097f3de8b50ac`. Branche `feature/catalog-filters`, worktree Codex `add4/RaceAtlas`.

## Périmètre et tâches

Implémenter les GET `/api/v1/races` et `/api/v1/map` selon `contracts/openapi.json` et `catalog.schema.json`, avec un service de sélection unique et PostgreSQL réel. Le détail existant et les restrictions par scope restent intacts. Aucune page liste distincte, carte/calendrier UI prématurés, collecte réseau, synchronisation active, migration distante ou déploiement.

- L4-01 Coordinator : bilan lot 3, mission, checkpoint et Draft PR.
- L4-02 Developer : validation, sélection PostgreSQL et filtres partagés.
- L4-03 Developer : pagination/version, projection carte, couverture, intégration et handoff.
- L4-04 Tester : revue du SHA figé, scénarios contractuels réels et régression.
- L4-05 Coordinator : CI et Tester au même SHA, fusion confirmée et bilan.

## Acceptation observable

1. Paramètre `filter` JSON conforme au contrat : dates civiles valides/ordonnées, dimensions et types compatibles, catégories référencées, géographie exclusive, rayon borné, valeurs non finies et formes invalides refusées. Erreurs JSON publiques structurées, champs et request_id ; aucune trace SQL ou secret. Limite 1–200, curseurs invalides explicitement rejetés.
2. OU catégorie : au moins une sélection acceptée explicitement. ET : toutes les sélections acceptées dans **un même scope** ; jamais union entre scopes, races ou manifestation. Admissibilité ambiguë/inconnue sans affirmation de correspondance. `matching_scope_ids` contient les seuls témoins ; fiche, règles corrélées, restrictions, labels bruts et `personal_eligibility=not_evaluated` conservés.
3. Intersection inclusive des dates multijours, frontières d'année, saison source indépendante. Disciplines/types exacts, CLM Route uniquement, départements OU dans AURA. Recherche normalisée par nom/commune/organisateur. Rayon sur centres sourcés uniquement : candidates non localisées séparées du total confirmé, jamais coordonnées inventées.
4. Tri stable date puis ID, pagination sans trous/doublons. Curseur lié au filtre canonique et à une version cohérente du catalogue ; changement invalidant =>409. Lecture cohérente d'une requête face à l'import concurrent ; aucun mélange de versions entre compteurs et éléments. Même sélection avant pagination sur carte et catalogue.
5. GeoJSON WGS84 longitude/latitude, regroupement par commune, projection des courses de la page, IDs non localisés distincts. Compteurs globaux avant pagination. Documenter les détails de pagination des candidates non localisées conformément au contrat, et vérifier parité après parcours complet des pages.
6. Couverture/fraîcheur fondée sur les audits du lot 3 ; reprise d'erreurs partielles visible et dernière synchronisation réussie conservée. `intrinsic_exhaustiveness=unknown`. Aucun import synthétique présenté comme une preuve de complétude FFC réelle ; états incohérents restent incomplets.
7. Tous les scénarios de `fixtures/scenarios.v1.json` exécutés via Flask + PostgreSQL et comparés aux IDs attendus ; oracle de test jamais importé en production. JSON Schema des deux réponses, cas négatifs entre scopes/races, curseur périmé, rayon/non localisé, recherche et multiannée. Parcours fixture → adaptateur → sync → API catalogue/carte réel et régressions précédentes.
8. Tests/lint/build/migrations pertinents, handoff et commandes Windows reproductibles ; aucune activation live/source externe ou dépense.

Contrats et fixtures historiques restent la référence. Une dépendance existante utilisée en production doit figurer dans les dépendances runtime épinglées. Les anciens tests de routes réservées peuvent évoluer pour les routes désormais implémentées ; les API inconnues restent 404 JSON.

Autonomie technique documentée et politique de consultation maintenue. Choix propriétaire futur lot 5 déjà confirmé : **Altitude initial, Summit à la demande**. Aucun choix produit majeur en attente pour ce lot backend.
