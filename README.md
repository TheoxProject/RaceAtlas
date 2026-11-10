# RaceAtlas

Découvrir et organiser les compétitions cyclistes d'Auvergne-Rhône-Alpes, avec carte Altitude/Summit, calendrier et filtres d'admissibilité.

## Démarrage du lot 1

Le socle React/Vite → Flask/SQLAlchemy → PostgreSQL est lançable sur des données synthétiques. L'accueil est une démonstration technique ; carte, calendrier, filtres, comptes et import FFC restent réservés aux lots suivants. Aucune collecte ni aucun déploiement n'est activé.

Les [instructions Windows et de validation](docs/lot-1/local-development.md) décrivent l'installation, les migrations, le seed et le serveur Waitress. [Cadrage et critères lot 1](docs/lot-1/mission.md).

- [Dossier versionné du lot 0](docs/lot-0/README.md)
- [Contrat JSON Schema](contracts/catalog.schema.json)
- [Contrat API OpenAPI 3.1](contracts/openapi.json)
- [Fixtures synthétiques](fixtures/catalog.v1.json)
- [Orchestration developer → tester](docs/AGENT_WORKFLOW.md)

Qualification locale hors réseau : `node --test tests/contracts/contracts.test.mjs` (Node.js 22 ou plus récent). Aucun paquet à installer. Ces tests vérifient contrats et fixtures ; ils ne remplacent pas les futurs tests de l'application et des flux React → Flask → PostgreSQL.
