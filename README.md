# RaceAtlas

Découvrir et organiser les compétitions cyclistes d'Auvergne-Rhône-Alpes, avec carte Altitude/Summit, calendrier et filtres d'admissibilité.

## État du projet

Lot 0 : qualification des sources et contrats de conception. Aucune application ni collecte planifiée n'est implémentée. Les inconnues de complétude et les droits FFC restent des conditions distinctes de l'utilisation des fixtures synthétiques.

- [Dossier versionné du lot 0](docs/lot-0/README.md)
- [Contrat JSON Schema](contracts/catalog.schema.json)
- [Contrat API OpenAPI 3.1](contracts/openapi.json)
- [Fixtures synthétiques](fixtures/catalog.v1.json)
- [Orchestration developer → tester](docs/AGENT_WORKFLOW.md)

Qualification locale hors réseau : `node --test tests/contracts/contracts.test.mjs` (Node.js 22 ou plus récent). Aucun paquet à installer. Ces tests vérifient contrats et fixtures ; ils ne remplacent pas les futurs tests de l'application et des flux React → Flask → PostgreSQL.
