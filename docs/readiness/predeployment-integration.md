# PRE-01 — intégration confirmée

Le rapport demandé après le lot 6 est intégré. [PR10](https://github.com/TheoxProject/RaceAtlas/pull/10), **APPROVE exact 0eab28197d8ea6443fa1f16e702e0b1a94585b3b**, merge GitHub confirmé **51856c9940a2b0e16c9f05d61a9f1726ae8701d9** le 12 novembre 2026 à 17:52:23 UTC. Arbre approuvé/main identique **1af4c9ffc3d753df22c160670fa9d1a3b1c87885**.

- CI PR [43272958804](https://github.com/TheoxProject/RaceAtlas/actions/runs/43272958804) SUCCESS : 389 pytest en 202,50 s, 67 frontend, lint/format/contrats/build/dépendances verts et source vérifiée avant/après.
- CI push main [43273970329](https://github.com/TheoxProject/RaceAtlas/actions/runs/43273970329) SUCCESS : 389 pytest en 167,19 s, 67 frontend et contrôles verts, source 51856c9 vérifiée avant/après.
- Revue indépendante exacte : YAML/gardes, 31 liens locaux, sept scénarios chiffrés, sources primaires, lint/build et deux parcours d'attribution passent. Sources backend, migrations, tests, dépendances et autres comportements inchangés explicitement vérifiés ; rapport complet dans la PR.

Région Frankfurt préparée et lien Mapterhorn aligné ; aucune activation. [Rapport](predeployment-report.md) et [handoff](predeployment-handoff.md) distinguent hypothèses, tests locaux et validations externes absentes. Domaines, services, paiements, email réel, base distante et collecte : aucun créé ou activé.

**Décision explicite du propriétaire du 12 novembre : premier déploiement privé après le lot 8, au stade candidat V1.** Ce choix fixe le jalon ; création de services, déploiement, migrations/fixtures distantes et envois réels restent soumis aux préconditions et à une autorisation explicite. Aucun silence ou merge ne la remplace. Le lot 7 peut progresser localement : email/mot de passe retenus, expéditeur encore absent.
