# Lot 1 — Core Foundation

Mission autorisée le 10 novembre 2026. Base vérifiée après `git fetch origin main` : `ae423f520c420bbdaebbaf5e515ce54ea50b4518` (fusion du lot 0). Worktree Codex isolé : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas`, branche `feature/core-foundation`. Aucun changement à `main`, aucune fusion ni mise en production.

## Périmètre et responsabilités

Le coordinateur définit ce cadrage, prépare les moyens de vérification, fige le SHA puis confie sa revue indépendante au testeur. Developer possède exclusivement l'implémentation : backend, frontend, migrations, scripts, dépendances verrouillées, tests, CI et documentation locale. Il peut modifier le README et le gitignore. `AGENTS.md`, `.codex/`, `docs/lot-0/`, `contracts/`, `fixtures/` et les tests du lot 0 sont préservés. Toute modification de sémantique des contrats exige signalement au coordinateur avant exécution.

## Interfaces et limites

- Flask en application factory, SQLAlchemy 2 et Alembic ; PostgreSQL uniquement pour les preuves d'intégration. Configuration explicite local/test/production, secrets via environnement. Aucune migration automatique au démarrage ni connexion à Neon.
- Flask sert le frontend React/Vite compilé depuis la même origine en mode monolithe ; Vite relaie `/api` vers Flask en développement. Serveur WSGI documenté pour Windows et production, sans déploiement.
- Premiers modèles relationnels : manifestation, commune et centre/provenance nullable, épreuve, référence source (saison distincte), liste d'engagement, règle et catégories associées. Identités opaques stables, dates civiles, catégories/restrictions corrélées, contraintes et clés étrangères PostgreSQL réelles. Les tables des fonctionnalités futures ne sont pas nécessaires.
- Minimum API : santé/disponibilité explicite et lecture `/api/v1/races/{race_id}` conforme au contrat `Race`. Les routes de sélection `/api/v1/races` et `/api/v1/map` restent au lot 4 : ne pas publier une approximation de leurs filtres. Une petite route de découverte de la démonstration est permise sous un espace distinct, documentée comme interface du socle.
- Chargement explicite et reproductible de données exclusivement synthétiques ; pas de seed au démarrage en production. Réutiliser le catalogue validé sans modifier ses fichiers ni inventer de données FFC. Démonstration technique sur la page d'accueil, pas de nouvelle page de listing produit.
- React affiche une donnée réellement lue via Flask depuis PostgreSQL, ainsi que chargement/échec/absence et nature synthétique. Identité navy/orange, interface simple et responsive ; aucune carte, aucun calendrier, aucun compte ni importeur.

## Critères d'acceptation

1. Installation et commandes PowerShell Windows documentées, versions/prérequis explicites, dépendances reproductibles et fichiers sensibles ignorés.
2. Migration Alembic `upgrade head`, contrôle de dérive (`alembic check`) et aller-retour downgrade/upgrade sur base PostgreSQL locale jetable, sans base distante ni donnée utilisateur.
3. Contraintes PostgreSQL testées : dates ordonnées, intégrité relationnelle, unicité des références sources et catégories, valeurs métiers principales, CLM comme type Route. Les identités ne dérivent pas du nom/date/parent.
4. Seed synthétique rejouable sans doublons ; réponse de détail vérifiée contre le contrat du lot 0, restrictions conservées et coordonnées nulles préservées.
5. Tests backend et frontend, lint et build réellement exécutés. Les tests contrats du lot 0 passent sans modification.
6. Test bout en bout automatisé avec navigateur exécutant le React compilé servi par Flask et une vraie PostgreSQL jetable : rendu d'une donnée persistée, appel API réel ; preuve qu'un changement en base est reflété par le parcours. Tester également l'indisponibilité/absence de données sans fuite de trace ou secret.
7. CI GitHub Actions sur Pull Requests : contrats, lint/tests frontend et backend, migrations/contraintes PostgreSQL, build et parcours intégré avec PostgreSQL de service. Permissions minimales, aucune collecte planifiée ni déploiement.
8. Developer livre fichiers, commandes et résultats effectifs, limites et SHA stable puis cesse ses éditions. Tester vérifie indépendamment ce SHA exact, avec verdict par critère et constats reproductibles. Il est expressément autorisé à exécuter les migrations uniquement sur sa base locale jetable.

## Livraison et contrôle

Une PR vers `main` est préparée et poussée, sans fusion. Le coordinateur attend la CI du SHA livré et indique les blocages éventuels. Merge commit privilégié lors d'une future intégration autorisée par le propriétaire. Aucun service payant, changement de production, migration Neon, déploiement Render, extraction FFC ou développement des lots 2–8.
