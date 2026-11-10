# Développement local — Windows PowerShell

Prérequis : Python 3.12, Node.js 24 LTS (minimum 22.12), pnpm 10.20.0 et PostgreSQL 17.11 local. Installer pnpm avec `npm install --global pnpm@10.20.0` si nécessaire. PostgreSQL peut être installé nativement ou via Docker Desktop selon votre usage. Toutes les commandes partent de la racine du dépôt.

## Installation et démarrage

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
pnpm --dir frontend install --frozen-lockfile
```

`constraints.txt` verrouille aussi les dépendances Python transitives. Pour une installation sans outils de test, utiliser `requirements.txt`. Le lockfile pnpm est versionné.

Option Docker pour la base locale uniquement :

```powershell
docker compose up -d --wait postgres
docker compose exec postgres createdb -U raceatlas raceatlas_test
```

Avec PostgreSQL natif, créer un rôle local et les bases `raceatlas_dev` et `raceatlas_test` via `createdb`/pgAdmin, puis adapter les URLs ci-dessous. Ne jamais utiliser Neon ou une base contenant des données personnelles pour ces tests. Les identifiants `raceatlas` ci-dessous sont des valeurs de démonstration locales. `.env.example` est indicatif : il n'est pas chargé automatiquement.

```powershell
$env:RACEATLAS_ENV = 'local'
$env:DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_dev'
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m flask --app raceatlas:create_app seed-synthetic
pnpm --dir frontend build
.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 --call raceatlas:create_app
```

Ouvrir [RaceAtlas local](http://127.0.0.1:5000). Flask sert le React compilé et l'API sur la même origine. Le bouton « Actualiser la démonstration » relit PostgreSQL. Le seed est explicite, ajoute seulement les épreuves absentes et peut être rejoué sans doublons ; il ne remplace pas les éditions locales. Il ne constitue pas un importeur FFC.

Pour le rechargement à chaud, lancer Flask dans un terminal et Vite dans un second :

```powershell
.venv\Scripts\python.exe -m flask --app raceatlas:create_app run --host 127.0.0.1 --port 5000
# Deuxième terminal, même répertoire :
pnpm --dir frontend dev
```

Ouvrir [Vite local](http://127.0.0.1:5173). Son proxy `/api` cible Flask sur `127.0.0.1:5000` ; aucun CORS ouvert. `Ctrl+C` arrête les serveurs. `docker compose stop` arrête la base en conservant les données locales.

## Vérification complète

Les tests réinitialisent uniquement une base jetable dont le nom se termine par `_test` ou `_review`, après opt-in explicite. Ils vérifient les migrations aller-retour, l'absence de dérive du modèle, les contraintes PostgreSQL, la réponse API contractuelle et Chromium exécutant le React compilé servi par Flask. Ils ne contactent aucun fournisseur.

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
.venv\Scripts\python.exe -m playwright install chromium
node --test tests/contracts/contracts.test.mjs
.venv\Scripts\python.exe -m ruff check raceatlas migrations tests/backend
.venv\Scripts\python.exe -m ruff format --check raceatlas migrations tests/backend
pnpm --dir frontend lint
pnpm --dir frontend test
pnpm --dir frontend build
.venv\Scripts\python.exe -m pytest -v
```

Backend seul : `.venv\Scripts\python.exe -m pytest -m 'not e2e'`. Navigateur seul : `.venv\Scripts\python.exe -m pytest -m e2e` après build et installation Chromium. Sous Linux, remplacer `.venv\Scripts\python.exe` par `.venv/bin/python` et installer les dépendances système du navigateur avec `python -m playwright install --with-deps chromium`. La CI GitHub Actions exécute ces contrôles sur PR avec un PostgreSQL de service jetable.

Créer une migration : `.venv\Scripts\python.exe -m alembic revision --autogenerate -m 'description'`, relire le fichier généré avant commit ; puis `upgrade head` et `check` avec le même préfixe. Un `downgrade base` supprime les tables : réservé à une base jetable, jamais des données à conserver.

## Configuration production préparée

Aucun déploiement n'est effectué. Fournir `RACEATLAS_ENV=production` et `DATABASE_URL` via environnement, puis compiler le frontend. Les migrations s'exécutent séparément, après autorisation du propriétaire pour toute base distante. Lancer `python -m waitress --listen=127.0.0.1:5000 --call raceatlas:create_app` derrière un reverse proxy HTTPS ; ne pas activer le debug Flask. Le démarrage ne crée aucune table et ne charge aucune donnée ; le seed refuse le mode production. Le lot ne comprend ni session ni authentification : aucun secret applicatif n'est nécessaire. Les erreurs publiques ne contiennent ni SQL, ni URL de connexion, ni trace serveur.

API livrée : `/api/health/live` (processus), `/api/health/ready` (DB et schéma accessibles), `/api/v1/races/{race_id}` (contrat `Race` v1), `/api/foundation/demo` (découverte bornée de démonstration, `{synthetic:true,race_id:string|null}`). Les sélections `/api/v1/races` et `/api/v1/map` restent au lot 4 et renvoient 404 JSON. L'OpenAPI lot 0 reste un contrat de conception, pas une déclaration que toutes ses routes sont opérationnelles.

IDs nouvelles entités : UUID opaques par défaut ; les IDs lisibles du catalogue synthétique sont conservés conformément aux exemples du lot 0. La position d'une liste sert uniquement à l'affichage, jamais à son identité. Les règles/restrictions restent associées à leur liste ; aucune éligibilité personnelle n'est déduite. Les premières tables n'anticipent ni comptes ni import/synchronisation. L'intégration future privilégie un Merge commit, après accord du propriétaire.
