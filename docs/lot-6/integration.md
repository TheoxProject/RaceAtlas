# Lot 6 — intégration confirmée

Le calendrier mensuel est intégré dans `main` depuis le 12 novembre 2026.

- PR : https://github.com/TheoxProject/RaceAtlas/pull/9.
- SHA complet approuvé : **302462c006712ecd27f221f346d4f2e3d2c1d1ad**.
- Merge confirmé par GitHub : **7b733d86d99a354fdcfe2bf1ecbde519ef78a68f**, 2026-11-12T13:28:31Z.
- Arbre approuvé et `origin/main` identiques : **df012a878751c156cbc481209c43e5a59c5a8a28**.
- CI PR [43226499588](https://github.com/TheoxProject/RaceAtlas/actions/runs/43226499588) SUCCESS : **389 pytest en 174,15 s**, **67 tests frontend**, lint, format, contrats, build et dépendances verts. Source vérifiée avant et après sur le SHA approuvé.
- CI push main [43227636726](https://github.com/TheoxProject/RaceAtlas/actions/runs/43227636726) SUCCESS : **389 pytest en 178,34 s**, **67 tests frontend**, autres contrôles verts ; source vérifiée avant et après sur le merge SHA.

Le Tester a donné **APPROVE complet au SHA exact**, avec réutilisation explicitement vérifiée des preuves inchangées. Les constats F6-01 (titres de panneaux globaux) et F6-02 (synchronisation du test calendrier) sont clos. Le rapport indépendant complet et la confirmation ultérieure de la CI sont dans la description de la PR. Les rapports locaux ignorés ne sont pas la seule preuve d'intégration.

Fonctionnalités exercées : sélection civile partagée, ouverture depuis année/semaine ISO, retour carte conservant le mois, multijour du 31 décembre aux 1er/2 janvier avec total distinct, mêmes filtres et témoins de scope, candidates rayon séparées, journées denses et détails, mobile 390 px, défilement des dernières semaines, erreurs/retry et réponses périmées. MapLibre reste monté ; caméra non initiale à zoom 7.5, Summit réel 60° et crédits conservés. Quinze parcours intégrés ont été exécutés sur le jalon initial ; le correctif final a été revérifié par quatre parcours ciblés, une sonde indépendante contexte/détails/no-op et les tests App, puis par la CI complète.

Le budget de disponibilité de sélection de 15 s est une synchronisation de test, pas un SLA produit. Les mesures locales diffèrent : Developer 3,672 s, Tester 13,625 s depuis le début de l'action, avec transport/ordonnancement et rendu logiciel. Les assertions caméra de 10 s, pitch exact 60° et DEM >100 restent inchangées. Aucune qualification générale du matériel mobile ou du Summit live n'en découle.

Les tests utilisent les fixtures synthétiques et le vrai moteur WebGL avec style/DEM interceptés. Aucun service Render/Neon, migration distante, paiement, email réel, collecte FFC ou publication finale effectué. Le rapport de pré-déploiement et les travaux indépendants du lot 7 viennent ensuite ; l'activation et les validations externes restent des décisions distinctes du propriétaire.
