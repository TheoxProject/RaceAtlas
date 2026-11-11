# Carte Altitude / Summit — usage et validation locale

La carte React consomme les GET catalogue/carte du lot4. Les filtres et la caméra restent en mémoire de session UI uniquement. Ouverture sur l'année civile courante Europe/Paris ; Année/Mois/Semaine ISO utilisent des bornes inclusives et une date d'ancrage partagée. Le champ est nommé Année civile en Année/Mois et Année ISO en Semaine : au2027-01-01, l'année civile initiale2027 devient2026-W53 en mode semaine, sans perdre la date courante. Saisir une année ou semaine entière puis Entrée ou quitter le champ ; décimales/valeurs vides ou invalides restaurent la sélection précédente, semaines au-delà du maximum bornées selon l'année ISO. Un changement explicite de semaine recale l'ancrage sur son lundi ; les modes civils utilisent alors le mois et l'année de cette date. Changer la période ou les filtres conserve centre, zoom, orientation et inclinaison. Aucun calendrier factice : le calendrier partagé arrivera au lot6, selon la décision propriétaire déjà consignée.

## Données et interactions

Toutes les pages catalogue et carte sont chargées ensemble. Le curseur peut continuer avec `items=[]` en rayon : les candidates non localisées constituent un second flux. Les deux endpoints et chaque page doivent garder la même version ; une vérification finale empêche une modification pendant le chargement des fiches candidates de produire une sélection mélangée. Au maximum trois tentatives complètes sur409, puis état clair et reprise manuelle. Annulation et garde de résultat ignorent les requêtes anciennes ; recherche débouncée180ms. Chargement de fiches candidates par groupes de huit maximum.

Les catégories viennent du **référentiel**, pas des courses de la sélection : GET `/api/v1/catalog/options`, réponse indépendante `catalog-options.schema.json`1.0.0. OpenAPI de collection passe à1.1.0 pour cette route additive ; réponses catalogue/carte/fiche et leur version1.0.0 inchangées. Aucun changement de migration. Une panne de métadonnées offre une reprise propre sans empêcher les autres filtres.

Les Features de courses sont dédupliquées puis regroupées par `commune_id`, avant clustering spatial MapLibre. Chaque marqueur indique le nombre distinct de courses, jamais le nombre de scopes. Activer un cluster agrandit la carte ; un marqueur communal ouvre les courses correspondantes. Boutons de marqueur nommés, utilisables au clavier. La signature de synchronisation inclut IDs, comptes, commune et coordonnées ; un centre corrigé déplace le marqueur après actualisation, et des images identiques conservent le même bouton/focus. Synchronisation au rendu, sans dépendre d'un état idle qu'une source en échec peut empêcher.

« Explorer les communes » ouvre un panneau lié à la carte, transformé en bottom sheet mobile. Les non-localisées restent distinctes ; en rayon, elles ne sont pas ajoutées au total confirmé. Rayon : choisir explicitement un point sur la carte ou saisir ses coordonnées WGS84, jamais de géolocalisation implicite ni de départ de course inventé. Fiche : scopes et règles séparés, restrictions corrélées, incertitudes, annulation distincte d'une fiche à vérifier, fraîcheur et saison source. Aucune éligibilité personnelle ou inscription vérifiée revendiquée.

## Fond, relief et repli

MapLibre GL JS épinglé **5.11.0**, Liberty OpenFreeMap et Mapterhorn Terrarium512. Altitude initial : ombrage et inclinaison35°. Summit à la demande : source DEM terrain séparée, exagération1,3 et inclinaison60°. Retour explicite Altitude à35° ; une modification temporelle ne touche pas cette caméra. Une erreur DEM désactive Summit et laisse données, filtres et détails accessibles en Altitude sans relief. Un avertissement du fond ne désactive pas silencieusement un terrain disponible. Absence WebGL : panneau de courses/détails accessible et message explicite.

Attributions visibles OpenStreetMap/OpenMapTiles/OpenFreeMap/Mapterhorn. Références primaires : [exemple terrain MapLibre](https://maplibre.org/maplibre-gl-js/docs/examples/3d-terrain/), [OpenFreeMap](https://openfreemap.org/quick_start/), [accès Mapterhorn](https://mapterhorn.com/data-access/), [attributions Mapterhorn](https://mapterhorn.com/attribution/). Préflight borné de métadonnées conservé localement dans `.local-tools/lot5-provider-preflight.md`. Disponibilité/SLA et audit complet des licences des sources terrain ne sont pas établis ; aucune autorisation d'ouverture publique n'en découle.

## Commandes PowerShell

Utiliser les dépendances Python et Chromium existantes selon le checkpoint. Node≥22.12 ; package manager épinglé pnpm10.20.0. Le wrapper système peut pointer vers pnpm11 incompatible avec le store local10 : réutiliser le binaire pnpm10 en cache plutôt que réinstaller toutes les dépendances. Dépendance MapLibre absente du cache lors du développement : téléchargement borné autorisé, verrou mis à jour, aucun script de dépendance activé.

```powershell
pnpm --dir frontend install --frozen-lockfile
Push-Location frontend
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vitest/vitest.mjs run --pool=threads --maxWorkers=1
node node_modules/vite/bin/vite.js build
Pop-Location
node --test tests/contracts/contracts.test.mjs
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
# Pointer PLAYWRIGHT_BROWSERS_PATH vers le cache local si nécessaire.
python -m pytest -q --tb=short
```

Les tests réinitialisent seulement leur base jetable ; Developer `_test`, Tester `_review`, jamais les partager simultanément. Les tests navigateur utilisent le **moteur réel** avec styles et PNG DEM512 synthétiques interceptés, aucun fournisseur appelé. SwiftShader est limité aux arguments du processus Chromium de test ; aucun changement de navigateur utilisateur, politique de sécurité ou désactivation web-security. Tests unitaires React isolent uniquement le rendu moteur ; les preuves WebGL viennent des tests backend compilés.

Caméra en E2E : attendre la valeur réellement enregistrée au `moveend` (maximum10s pour Summit), puis vérifier le pitch60 strict et le DEM décodé>100. Seules les coordonnées du centre tolèrent un arrondi absolu1e-9degré, relatif0 (environ0,1mm) ; zoom, orientation et inclinaison restent stricts. Le parcours chronologique zoome réellement avant sa baseline et prouve que le comparateur rejette un retour à la caméra initiale. Les attentes fixes700ms ne garantissent pas la fin d'une animation sous rendu logiciel.

Sur cette machine, une ancienne commande Vitest groupée a rencontré un timeout de démarrage du second worker ; ce run n'est pas compté PASS. Le correctif actuel a passé28tests groupés en9,87s sans erreur de runner. Reprise isolée possible sans modifier la configuration produit : `node node_modules/vitest/vitest.mjs run src/catalog.test.js --pool=threads --maxWorkers=1` (22tests), puis `node node_modules/vitest/vitest.mjs run src/App.test.jsx --pool=threads --maxWorkers=1` (6tests). Exiger un code0 et aucune erreur de runner ; la CI du SHA exact reste obligatoire.

Preview distincte déjà créée/migrée/seedée : `raceatlas_map_demo` sur le même PostgreSQL local,12courses synthétiques. Ne pas reseed/réinitialiser une base inconnue. Pour un serveur local manuel :

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_map_demo'
$env:RACEATLAS_ENV = 'local'
python -m flask --app raceatlas run --host 127.0.0.1 --port 5000
```

Build Vite observé : JS environ1,18MB brut/330KB gzip, CSS82KB brut ; avertissement de taille attendu pour le moteur complet, sans seuil masqué. Terrain optionnel et replis disponibles ; aucun benchmark mobile réel/régional exhaustif revendiqué. Aucun compte, collecte FFC, téléchargement régional, migration distante, dépense ou déploiement activé.
