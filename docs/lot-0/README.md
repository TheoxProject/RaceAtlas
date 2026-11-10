# Lot 0 — Qualification des sources et contrats

Spécification candidate du 10 novembre 2026. Ce lot ne contient ni application, ni importeur exploitable, ni planification de collecte, ni déploiement.

- [Mission et conditions d'acceptation](mission.md)
- [Audit FFC et preuves bornées](source-audit.md)
- [Identité, admissibilité et modèle](data-decisions.md)
- [Contrats carte et catalogue](contracts.md)
- [Livraison intégrée V1](delivery.md)
- [Incertitudes et gates](open-questions.md)

Les fichiers `fixtures/` sont exclusivement synthétiques : aucune course réelle, aucun participant, aucun document ou jeu de données FFC téléchargé. Le validateur et les oracles de test sont des outils de qualification des contrats, pas une implémentation de l'application.

Depuis la racine : `node --test tests/contracts/contracts.test.mjs`. Aucun accès réseau, service, installation ou secret nécessaire.
