# RaceAtlas

Découvrir et organiser les compétitions cyclistes d'Auvergne-Rhône-Alpes, avec carte Altitude/Summit, calendrier et filtres d'admissibilité.

## État du projet

Les lots 0–6 sont intégrés : modèle et migrations PostgreSQL, adaptateur HTML hors réseau, synchronisation auditable sur observations autorisées, API de catalogue, carte interactive et calendrier mensuel partagé. Altitude 2,5D s'ouvre par défaut ; Summit active le terrain 3D. Les filtres couvrent périodes civiles/ISO, disciplines/types, catégories OU/ET dans une même liste, recherche, départements et rayon. Les points représentent les centres de communes, jamais des départs inventés ; les courses non localisées restent consultables.

Entrer dans le calendrier depuis Année/Semaine sélectionne le mois civil affiché ; revenir sur la carte conserve ce mois, les filtres et la caméra. Les jours ouvrent toutes leurs courses et les détails communs ; une épreuve multijour ne compte qu'une fois dans le total. Voir les [preuves d'intégration](docs/lot-6/integration.md) et le [guide calendrier](docs/lot-6/local-development.md). Les comptes email/mot de passe, récupération par email et planification/ICS arrivent au lot 7 ; aucun domaine ni expéditeur email disponible pour le moment. Les notifications internes et l'exploitation arrivent au lot 8. Aucun déploiement ni collecte récurrente n'est activé. **La compatibilité de l'adaptateur avec les pages FFC réelles n'est pas acquise** : deux exemples ciblés échouent explicitement ; les droits de réutilisation restent à clarifier. Voir la [qualification limitée](docs/readiness/ffc-qualification.md).

[Rapport concret de pré-déploiement](docs/readiness/predeployment-report.md), [checkpoint opérationnel](docs/coordination/CURRENT_STATE.md), [préparation hébergement intégrée](docs/readiness/integration.md). Le rapport est préparatoire : comptes/plafonds réels, licences complètes, expéditeur et validations distantes restent ouverts ; aucune activation par fusion ou silence.

## Développement local

Prérequis : Python 3.12, Node.js 24, pnpm 10.20.0 et PostgreSQL 17.11 local. Les [instructions Windows d'installation](docs/lot-1/local-development.md) décrivent la création des bases et les dépendances. Les [commandes et scénarios actuels de carte](docs/lot-5/local-development.md) précisent les tests WebGL hors réseau et leurs limites.

Après création d'une base locale vide `raceatlas_dev`, depuis la racine, dans PowerShell :

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
pnpm --dir frontend install --frozen-lockfile
$env:RACEATLAS_ENV = 'local'
$env:DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_dev'
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m flask --app raceatlas:create_app seed-synthetic
pnpm --dir frontend build
.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 --call raceatlas:create_app
```

Les identifiants sont des exemples locaux, à adapter. Ouvrir [RaceAtlas local](http://127.0.0.1:5000). Flask sert le React compilé et l'API sur la même origine. Le seed explicite est idempotent et refuse le mode production ; aucune migration ni insertion ne se fait au démarrage. Ne pas utiliser ces commandes contre une base distante sans autorisation.

Routes disponibles : `/api/v1/races`, `/api/v1/map`, `/api/v1/races/{id}`, `/api/v1/catalog/options`, `/api/health/live` et `/api/health/ready`. Les sélections paginées partagent les filtres et la version du catalogue. Une fenêtre source manquante signifie « à vérifier », pas « annulée ». Les comptes arrivent au lot 7 ; le statut d'inscription restera déclaré par l'utilisateur.

## Validation et intégration

Les tests PostgreSQL réinitialisent uniquement une base jetable suffixée `_test` ou `_review`, avec `RACEATLAS_DISPOSABLE_DB=1`. Ne jamais fournir une base de développement à conserver ou une base distante. Après installation de Chromium et build :

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
.venv\Scripts\python.exe -m playwright install chromium
node --test tests/contracts/contracts.test.mjs
pnpm --dir frontend lint
pnpm --dir frontend test
pnpm --dir frontend build
.venv\Scripts\python.exe -m ruff check raceatlas migrations tests/backend
.venv\Scripts\python.exe -m ruff format --check raceatlas migrations tests/backend
.venv\Scripts\python.exe -m pytest -q
```

Les E2E exécutent réellement React → Flask → PostgreSQL et MapLibre/Chromium avec fond et DEM synthétiques interceptés. Ils ne qualifient pas les droits FFC, la disponibilité des fournisseurs ou tous les GPU mobiles. La CI contrôle le SHA courant et après fusion ; les résultats effectifs figurent dans le checkpoint et les PR.

La cible préparée est un monolithe Flask/Waitress sur Render Free Frankfurt avec Neon Free proche si disponible. La création des services, les mutations distantes, tout déploiement et la publication finale restent soumis à l'autorisation du propriétaire. Le [rapport après lot 6](docs/readiness/predeployment-report.md) expose les étapes, hypothèses de ressources, limites et trois moments possibles de premier déploiement ; attendre le candidat après lot 8 est recommandé, sans engager cette décision.

- [Dossier versionné du lot 0](docs/lot-0/README.md)
- [Contrat JSON Schema](contracts/catalog.schema.json)
- [Contrat API OpenAPI 3.1](contracts/openapi.json)
- [Fixtures synthétiques](fixtures/catalog.v1.json)
- [Orchestration developer → tester](docs/AGENT_WORKFLOW.md)
- [Préparation de la preview privée Render Free / Neon Free](docs/readiness/hosting.md)

Les contrats et fixtures sont synthétiques. Leur validation seule ne remplace pas les tests de l'application ni la revue indépendante du SHA final.
