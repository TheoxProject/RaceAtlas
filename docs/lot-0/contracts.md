# Contrats pour la première interface sur fixtures

Version `1.0.0` des contrats, distincte de la version produit V1. Les fichiers `contracts/catalog.schema.json` et `contracts/openapi.json` décrivent le modèle et les échanges. Aucune route n'est implémentée. Ajout compatible de champs optionnels : version mineure ; changement de sens, champs requis ou retrait : version majeure.

`fixtures/catalog.v1.json` contient un catalogue synthétique et le référentiel de catégories utilisé. `fixtures/scenarios.v1.json` définit les filtres canoniques et IDs attendus. `fixtures/identity-revisions.v1.json` représente deux versions d'une même épreuve dont titre, date et parent changent : les IDs restent égaux. Les fixtures ne prétendent pas traduire le règlement FFC réel.

## Filtres et réponse

Les IDs API sont opaques : UUID sérialisés acceptés, IDs lisibles uniquement pour les exemples synthétiques. Les codes de catégories sont extensibles (U15/U13/etc. possibles), avec intégrité vérifiée contre le référentiel livré ; celui des fixtures n'est qu'un sous-ensemble. `types: []` signifie type inconnu et `organizer: null` organisateur inconnu : aucun libellé sportif ou organisateur ne doit être inventé. `matching_scope_ids` indique les seules listes témoins du filtre ; la fiche conserve les autres listes distinctes sans les confondre avec les résultats.

Les routes GET futures `/api/v1/races` et `/api/v1/map` partagent un paramètre `filter` JSON encodé dans l'URL, conforme à `Filter`. Ce choix rend explicites dates, catégories, opérateur et géographie sans convention implicite pour tableaux imbriqués. `limit` (1–200) et `cursor` sont distincts. Même filtre et même version de catalogue => même sélection d'épreuves avant pagination. Les noms de catégories sont des codes stables du référentiel, pas des UUID FFC supposés.

Le filtre représente une période `[from,to]` inclusive, une intersection de dimensions et un seul mode géographique : `all`, `departments` (OU entre départements), `radius` (centre choisi et kilomètres). Les résultats restent côté serveur dans les douze départements AURA ; une sélection extérieure est invalide. Recherche normalisée par nom, commune ou organisateur ; types multiples compatibles avec la discipline. Catégories AND/OR selon `data-decisions.md`. Sans catégories : filtre neutre.

Une course multijour correspond si `start_date <= to` et `end_date >= from`. Les semaines ISO se calculent du lundi au dimanche avant appel. L'ouverture utilise l'année civile actuelle dans Europe/Paris, indépendamment de la saison source. Le filtre est en mémoire de session UI seulement ; aucune persistance entre sessions.

`RacePage` renvoie la sélection paginée, le total distinct avant pagination, un curseur nullable et la fraîcheur/couverture. `MapPage` projette les mêmes IDs en GeoJSON (WGS84 longitude,latitude) et expose séparément les IDs non localisés. Le compteur de courses ne compte ni scopes ni marqueurs. Un résultat contient toujours ses scopes et restrictions ; aucune promesse d'éligibilité personnelle.

Pour une recherche par rayon, une course sans centre n'est pas un résultat géographique confirmé : `unlocated_count` et `unlocated_ids` signalent les candidates répondant aux autres filtres. Elles restent consultables via la fiche, le panneau non localisé et le calendrier hors contrainte de rayon. Ne pas mélanger ces candidates dans `total` des correspondances confirmées au rayon.

Le curseur doit être lié au filtre et à la version du catalogue, pour éviter trous/doublons lors d'une synchronisation. Une révision différente invalide le curseur avec erreur explicite. Tri stable date puis ID. Les erreurs comportent code, message public, champs invalides et identifiant technique, jamais trace serveur ou secret. Codes : 400 filtre invalide, 404 fiche inconnue, 409 curseur périmé, 429 limite, 503 service indisponible.

## Carte

Moteur confirmé par le propriétaire : MapLibre GL JS 5.11.0 ; fond commun `https://tiles.openfreemap.org/styles/liberty` ; DEM `https://tiles.mapterhorn.com/tilejson.json` encodé Terrarium, 512 px. Altitude : ombrage/relief 2.5D ; Summit : terrain 3D incliné. Aucun PMTiles ni téléchargement régional. Les tests du lot 0 n'appellent aucun fournisseur ; les GET de métadonnées ont été vérifiés lors de la conception, pas un rendu WebGL.

La carte utilise exclusivement le centre de commune sourcé. Pas de coordonnées de départ inventées. Les communes partagent un marqueur regroupant les épreuves ; clustering supplémentaire entre communes proches. La caméra (centre, zoom, orientation) est indépendante du filtre temporel et conservée lors de ses changements. Le panneau desktop/bottom sheet mobile et un panneau non-localisé restent disponibles. Les attributions OpenStreetMap/OpenMapTiles et Mapterhorn sont visibles ; en cas d'échec du DEM, garder Altitude et les courses accessibles. Les plafonds, conditions et disponibilité des fournisseurs sont à revérifier avant ouverture publique.

## Validation locale

`fixtures/map.v1.json` est une réponse GeoJSON figée directement chargeable pour une première carte : onze points pour douze épreuves, avec une épreuve non localisée séparée. Elle est liée au premier scénario synthétique et comparée à l'oracle. Les scénarios contiennent des résultats attendus explicites, vérifiés indépendamment de cet exemple projeté. Les compteurs sont globaux avant pagination ; les marqueurs d'une page restent une projection des épreuves de cette page, et les consommateurs dédupliquent les IDs lors du chargement des pages.

Le validateur `tests/contracts/schema-validator.mjs` contrôle le sous-ensemble JSON Schema 2020-12 effectivement employé, rejette les mots-clés inconnus et ne se présente pas comme une implémentation générale ou certifiée. Les tests contrôlent aussi les références OpenAPI, liens entre entités, coordonnées, catégories et cas métier. Le modèle de sélection dans `tests/contracts/reference-model.mjs` est un oracle de test pour les fixtures, jamais un module applicatif ou importeur. Il ne certifie pas un futur backend : les lots applicatifs devront exécuter les mêmes scénarios sur PostgreSQL et l'API réelle.
