# Catalogue et filtres — développement local

Les GET `/api/v1/races` et `/api/v1/map` acceptent exactement `filter`, `limit` et `cursor`. `filter` est le JSON complet défini par `contracts/catalog.schema.json#/$defs/Filter` ; les paramètres dupliqués ou inconnus sont rejetés. `limit` vaut100 par défaut, entre1 et200. Les erreurs sont les objets `Error` plats du contrat, avec `fields`, `request_id` et en-tête `X-Request-ID`.

## Sélection et pagination

Le même service SQL sélectionne les courses pour les deux routes. Intersection inclusive des dates civiles ; saison source indépendante. Catégories OU ou ET par scope confirmé, sans mélanger scopes/courses ; les règles et restrictions corrélées restent intactes. Les catégories sont vérifiées contre la table `category`, sans liste de codes figée. Recherche par sous-chaîne littérale sur nom/commune/organisateur, après décomposition NFD, retrait des accents combinés, minuscules et espaces Unicode condensés. `%` et `_` sont des caractères littéraux.

Tri croissant `(start_date, id COLLATE "C")`. Un curseur opaque contient le prochain offset, le hash du filtre canonique et la version du catalogue. Il est commun aux routes ; les limites peuvent changer entre pages. Modifier le filtre impose un nouveau parcours (400), modifier le catalogue périme le curseur (409). Jeton corrompu, vide ou hors plage :400. Ce jeton public ne porte aucune autorisation ; sa somme SHA256 détecte la corruption et ne constitue pas une signature secrète.

Hors rayon, `total` inclut les courses non localisées et `unlocated_count` les compte avant pagination ; chaque page carte projette les courses de la même page catalogue. Une course localisée produit une Feature à son centre de commune sourcé. Deux courses dans la même commune produisent deux Features avec le même `commune_id` ; le regroupement visuel appartient au lot5.

En mode rayon, deux flux triés partagent **le même offset et la même limite** : les courses confirmées dans le rayon et les candidates non localisées. `total` compte seulement les confirmées ; `unlocated_count` compte toutes les candidates séparément ; la carte retourne les IDs de la page du second flux. Le curseur continue tant que l'un des flux a une page suivante. Ainsi une page `items=[]` ou `features=[]` peut avoir un `next_cursor` non nul : continuer jusqu'à `null`, sans s'arrêter au seul total confirmé. Une candidate non localisée ne reçoit aucune coordonnée ni confirmation d'appartenance au rayon.

## Version, transactions et audits

Migration `b7f4208ac112` après `8a95eb41f220` : singleton `catalog_state`, epoch propre à la migration, compteur transactionnel et triggers par statement INSERT/UPDATE/DELETE/TRUNCATE sur les dix tables qui influencent les réponses/audits. Les corrections manuelles, seeds et imports invalident aussi les curseurs. Un rollback n'invalide rien ; même un UPDATE sans changement peut invalider conservativement. Aucune extension PostgreSQL, aucun GRANT ni SECURITY DEFINER. Ne pas modifier manuellement `catalog_state` ni désactiver les triggers.

Chaque requête lit version, compteurs, IDs, graphes et couverture dans une seule transaction **REPEATABLE READ READ ONLY**. Le pool retrouve son isolation et son mode par défaut ensuite. Les compteurs restent SQL ; seuls les graphes des courses de la page (au plus200) sont chargés. La pagination OFFSET privilégie ici simplicité et cohérence ; aucune mesure de performance sur une collecte FFC régionale réelle n'est revendiquée.

`ImportRun.catalog_order` ordonne les tentatives par création en base, indépendamment des UUID et des horloges du fournisseur. La couverture utilise les fenêtres de la dernière tentative ; une tentative échouée/partielle/en cours reste incomplète et conserve la dernière synchronisation réussie. `audit_floor` distingue les audits antérieurs à la migration, dont l'ordre réel ne peut être reconstruit : incomplets jusqu'à un nouveau contrôle. Une enveloppe de dates ne prouve pas la continuité. Même un échantillon synthétique cohérent garde `intrinsic_exhaustiveness=unknown` et une note explicite ; aucune complétude FFC réelle n'en découle.

## Vérification reproductible PowerShell

Préparer les dépendances de `requirements-dev.txt`, Node et `frontend/node_modules` conformément au lot1. Réutiliser l'environnement compatible existant si présent. La base doit être PostgreSQL jetable, suffixée `_test` ou `_review` ; les tests détruisent **leur schéma** et parcourent upgrade/check/downgrade/upgrade/check. Ne jamais utiliser une base distante ou métier.

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
# Pointer PLAYWRIGHT_BROWSERS_PATH vers les navigateurs locaux déjà installés si nécessaire.
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
Push-Location frontend
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vitest/vitest.mjs run --pool=threads --maxWorkers=1
node node_modules/vite/bin/vite.js build
Pop-Location
python -m pytest -q --tb=short
```

Tests ciblés : `python -m pytest tests/backend/test_catalog.py tests/backend/test_catalog_sync.py tests/backend/test_catalog_validation.py -q --tb=short`. `test_catalog_sync.py` réutilise uniquement les constructeurs de fixtures synthétiques des tests lot3 ; aucun oracle de sélection n'est importé en production. Aucun client réseau, scheduler, migration distante ou déploiement n'est activé par ce lot.
