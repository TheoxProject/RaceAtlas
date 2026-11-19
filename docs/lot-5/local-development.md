# Carte Altitude / Summit — usage et validation locale

La carte React consomme les GET catalogue/carte du lot4. Les filtres et la caméra restent en mémoire de session UI uniquement. Ouverture sur l'année civile courante Europe/Paris ; Année/Mois/Semaine ISO utilisent des bornes inclusives et une date d'ancrage partagée. Le champ est nommé Année civile en Année/Mois et Année ISO en Semaine : au2027-01-01, l'année civile initiale2027 devient2026-W53 en mode semaine, sans perdre la date courante. Saisir une année ou semaine entière puis Entrée ou quitter le champ ; décimales/valeurs vides ou invalides restaurent la sélection précédente, semaines au-delà du maximum bornées selon l'année ISO. Un changement explicite de semaine recale l'ancrage sur son lundi ; les modes civils utilisent alors le mois et l'année de cette date. Changer la période ou les filtres conserve centre, zoom, orientation et inclinaison. Le calendrier mensuel utilise la même sélection. [Calendrier](../lot-6/local-development.md)

## Données et interactions

Toutes les pages catalogue et carte sont chargées ensemble. Le curseur peut continuer avec `items=[]` en rayon : les candidates non localisées constituent un second flux. Les deux endpoints et chaque page doivent garder la même version ; une vérification finale empêche une modification pendant le chargement des fiches candidates de produire une sélection mélangée. Au maximum trois tentatives complètes sur409, puis état clair et reprise manuelle. Annulation et garde de résultat ignorent les requêtes anciennes ; recherche débouncée180ms. Chargement de fiches candidates par groupes de huit maximum.

Les catégories viennent du **référentiel**, pas des courses de la sélection : GET `/api/v1/catalog/options`, réponse indépendante `catalog-options.schema.json`1.0.0. OpenAPI de collection passe à1.1.0 pour cette route additive ; réponses catalogue/carte/fiche et leur version1.0.0 inchangées. Aucun changement de migration. Une panne de métadonnées offre une reprise propre sans empêcher les autres filtres.

Les Features de courses sont dédupliquées puis regroupées par `commune_id`, avant clustering spatial MapLibre. Chaque marqueur indique le nombre distinct de courses, jamais le nombre de scopes. Activer un cluster agrandit la carte ; un marqueur communal ouvre les courses correspondantes. Boutons de marqueur nommés, utilisables au clavier. La signature de synchronisation inclut les identifiants, les quantités, la commune, les coordonnées et le style du marqueur ; un centre corrigé déplace le marqueur après actualisation, et des images identiques conservent le même bouton/focus. Synchronisation au rendu, sans dépendre d'un état idle qu'une source en échec peut empêcher.

« Explorer les communes » ouvre un panneau lié à la carte, transformé en bottom sheet mobile. Les non-localisées restent distinctes ; en rayon, elles ne sont pas ajoutées au total confirmé. Rayon : choisir explicitement un point sur la carte ou saisir ses coordonnées WGS84, jamais de géolocalisation implicite ni de départ de course inventé. Fiche : scopes et règles séparés, restrictions corrélées, incertitudes, annulation distincte d'une fiche à vérifier, fraîcheur et saison source. Aucune éligibilité personnelle ou inscription vérifiée revendiquée.

## Fond, relief et repli

MapLibre GL JS épinglé **5.11.0**, Liberty OpenFreeMap et Mapterhorn Terrarium512. Altitude initial : ombrage et inclinaison35°. Summit à la demande : source DEM terrain séparée, exagération1,3 et inclinaison60°. Retour explicite Altitude à35° ; une modification temporelle ne touche pas cette caméra. Une erreur DEM désactive Summit et laisse données, filtres et détails accessibles en Altitude sans relief. Un avertissement du fond ne désactive pas silencieusement un terrain disponible. Absence WebGL : panneau de courses/détails accessible et message explicite.

Attributions visibles OpenStreetMap/OpenMapTiles/OpenFreeMap/Mapterhorn. Références primaires : [exemple terrain MapLibre](https://maplibre.org/maplibre-gl-js/docs/examples/3d-terrain/), [OpenFreeMap](https://openfreemap.org/quick_start/), [accès Mapterhorn](https://mapterhorn.com/data-access/), [attributions Mapterhorn](https://mapterhorn.com/attribution/). Les conditions des fournisseurs et leurs limites figurent dans le guide d’exploitation. [Crédits et sources](../readiness/hosting.md#quotas-et-sources)

## Vérification locale

Préparer Chromium, le build React et une base PostgreSQL jetable selon le README. [Installation et tests](../../README.md#vérification-complète)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend/test_e2e.py -q
```

Les tests navigateur exercent MapLibre avec des styles et un relief synthétiques interceptés. Ils attendent la caméra enregistrée au `moveend` pour valider le passage à 60° et le relief décodé. Les comparaisons du zoom, de l’orientation et de l’inclinaison sont strictes. Le centre tolère seulement l’arrondi numérique. [Preuves de la carte](integration.md)
