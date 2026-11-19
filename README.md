# RaceAtlas

RaceAtlas aide à trouver les épreuves cyclistes dans les douze départements d’Auvergne-Rhône-Alpes et à organiser sa saison. La référence de la V1 est le [tag v1.0.0](https://github.com/TheoxProject/RaceAtlas/tree/v1.0.0). Les résultats de recette et les PR de livraison figurent dans la [validation V1](docs/readiness/validation-v1.md).

## Fonctionnalités V1

- **Carte et calendrier mensuel** avec filtres partagés par période, discipline, type, catégorie, recherche, département ou rayon. Altitude affiche le relief en 2,5D et Summit en 3D. Les marqueurs indiquent les centres de communes. Les épreuves non localisées restent consultables dans les résultats et le calendrier. Une légende identifie les types d’épreuve.
- **Conditions d’engagement** consultables par liste, avec les libellés et la provenance de la source. Un filtre de catégories en mode ET exige que la même liste accepte toutes les catégories sélectionnées.
- **Compte personnel et Ma saison** avec confirmation de l’adresse e-mail, récupération du mot de passe, favoris par liste d’engagement et quatre statuts. Le statut « Inscrit » est déclaré par l’utilisateur. Les épreuves prévues ou inscrites peuvent être exportées au format ICS.
- **Suivi du catalogue** avec import auditable et notifications internes sur les épreuves suivies. Une disparition à la source produit un état « à vérifier ». L’activation d’une collecte récurrente dépend de l’autorisation de la source et du propriétaire.

React et Vite composent l’interface, MapLibre GL JS affiche la carte et Flask sert l’application compilée et ses API. Le catalogue et les comptes reposent sur PostgreSQL, SQLAlchemy et Alembic.

## Développement local sous Windows

Prérequis pour PowerShell depuis la racine du dépôt. Installer Python 3.12, Node.js 24, pnpm 10.20.0 et PostgreSQL 17.11. Si nécessaire, installer la version de pnpm avec `npm install --global pnpm@10.20.0`.

Préparer un rôle PostgreSQL local et deux bases vides, `raceatlas_dev` et `raceatlas_test`, avec pgAdmin par exemple. Avec Docker Desktop, le fichier Compose crée la base de développement et la deuxième commande crée la base de test à la première installation.

```powershell
docker compose up -d --wait postgres
docker compose exec postgres createdb -U raceatlas raceatlas_test
```

Adapter les identifiants ci-dessous si le rôle ou le port local diffère. Les valeurs `raceatlas` sont des exemples locaux. Le fichier `.env.example` documente les variables et leur format. PowerShell ne le charge pas automatiquement.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
pnpm --dir frontend install --frozen-lockfile

$env:RACEATLAS_ENV = 'local'
$env:DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_dev'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m flask --app raceatlas:create_app seed-synthetic
pnpm --dir frontend build
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 --call raceatlas:create_app
```

Ouvrir [RaceAtlas local](http://127.0.0.1:5000). Choisir 2026 pour consulter la plupart des épreuves fictives. Le chargement synthétique peut être rejoué sans doublons et refuse le mode production. Flask sert l’interface et les API sur la même origine. Pour le rechargement à chaud, garder le backend sur le port 5000 et lancer `pnpm --dir frontend dev` dans un deuxième terminal. Ouvrir alors [Vite local](http://127.0.0.1:5173).

## Vérification complète

Les tests PostgreSQL réinitialisent une base locale jetable suffixée `_test` ou `_review`, avec accord explicite via `RACEATLAS_DISPOSABLE_DB=1`. Utiliser la base de test dédiée. Les parcours navigateur exécutent l’interface React compilée, Flask, PostgreSQL et MapLibre dans Chromium avec des ressources cartographiques et des services externes simulés.

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check raceatlas migrations tests/backend ops
.\.venv\Scripts\python.exe -m ruff format --check raceatlas migrations tests/backend ops
node --test tests/contracts/contracts.test.mjs
pnpm --dir frontend lint
pnpm --dir frontend test
pnpm --dir frontend build
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest -q
```

Pour cibler les parcours navigateur, utiliser `.\.venv\Scripts\python.exe -m pytest -m e2e`. Les règles de validation et d’intégration détaillent les contrôles requis sur GitHub. [Guide CI](docs/readiness/ci-validation.md)

## Documentation

- Hébergement public, configuration TLS, migrations et sauvegardes. [Render et Neon](docs/readiness/hosting.md)
- Configuration de l’envoi des e-mails de confirmation et de récupération. [Resend et Webador](docs/lot-7/resend-guide.md)
- Développement du catalogue, de l’import et des interfaces. [Catalogue](docs/lot-4/local-development.md) · [Import et communes](docs/lot-3/local-development.md) · [Carte](docs/lot-5/local-development.md) · [Calendrier](docs/lot-6/local-development.md)
- Contrats et données synthétiques. [Guide des contrats](docs/lot-0/contracts.md) · [OpenAPI](contracts/openapi.json) · [Catalogue synthétique](fixtures/catalog.v1.json)
- Règles de contribution et historique des lots. [Workflow de l’équipe](docs/AGENT_WORKFLOW.md) · [Archives documentaires v1.0.0](https://github.com/TheoxProject/RaceAtlas/tree/v1.0.0/docs)

## Après la V1

Les pistes à cadrer sont l’ajout d’épreuves, la refonte de la gestion des catégories, la simplification de l’application et l’évaluation d’une transition vers Neon Auth. La V1 utilise ses propres comptes et sessions.
