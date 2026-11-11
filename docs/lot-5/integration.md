# Lot 5 intégré

- PR : https://github.com/TheoxProject/RaceAtlas/pull/7.
- SHA final approuvé : **95bf1deabec10492100c0d6210dd3f30ccf57c3f**.
- Merge GitHub confirmé : **5f8229245f31ff64f678cad9df331f7302bef76f**.
- CI : https://github.com/TheoxProject/RaceAtlas/actions/runs/43029965848, success ; 315 pytest en156,61s, 28 frontend, 26 contrats, lint/build/dépendances réussis.
- Tester : **APPROVE** exact ; F1–F7 clos. Trois E2E concernés PASS42,78s, cinq contrôles indépendants de caméra réussis ; réutilisation explicite des preuves backend315/11Chromium de fc8f540 et frontend28 de5cd0c58, dont le produit est identique au candidat.
- `git diff --exit-code 95bf1de… origin/main` a confirmé l'arbre identique après fetch. Aucun test ou preview laissé actif. L'ancien workflow ne déclenche pas de CI sur `main` ; cette amélioration appartient au chantier suivant, aucune CI main n'est prétendue.

Fonctionnalités exercées : carte réelle, terrain décodé, clustering, filtres API et pagination, scopes/restrictions, détails et crédits mobiles, non-localisées, erreurs/reprise, frontière civile/ISO et saisies inchangées, caméra conservée depuis un zoom non initial. La tolérance du centre est limitée à1e-9degré pour l'arrondi numérique ; zoom/orientation/inclinaison restent stricts. Les attentes Summit portent sur la caméra réelle, pas un délai arbitraire.

Limites conservées : données synthétiques, qualification live Summit non réussie, droits et compatibilité FFC non établis, performance matérielle mobile/régionale à qualifier avant release. Aucun déploiement, compte payant, mutation distante, collecte récurrente ou tag final effectué.
