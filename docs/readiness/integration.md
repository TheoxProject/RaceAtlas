# Préparation V1 intégrée

- PR : https://github.com/TheoxProject/RaceAtlas/pull/8.
- SHA final approuvé : **dd80392605cb41ea995a0226eb89486cf1f00918**.
- Merge GitHub confirmé : **8ce46a3fc1129a905d2e9f1fc8552e3cf4d0a56f** ; fetch/diff ont confirmé l'arbre identique au candidat.
- CI PR : https://github.com/TheoxProject/RaceAtlas/actions/runs/43091426728, success ;385pytest125,09s et28frontend,26contrats/lint/build/dépendances verts, source contrôlée avant/après.
- **CI push sur main** : https://github.com/TheoxProject/RaceAtlas/actions/runs/43092874749, success ;385pytest154,02s et28frontend, source8ce46a3 contrôlée avant/après.
- Tester final : **APPROVE** exact ;70hosting PASS7,06s,349 sondes indépendantes TLS/auth/paths/headers/cache, YAML et scripts de build,24liens locaux, Ruff39/26contrats/pip/diff. Réutilisation explicitée des jalons documentaires/CI inchangés, aucun avis intermédiaire traité comme verdict final.

Livré : workflow progressif et README actuels ; CI du SHA courant et après merge, diagnostics bornés ; configuration monolithique Render Free/Neon TLS et lanceur de preview obligatoirement privé ; procédures opérateur et70tests. La fusion n'a créé aucun service, payé, déployé ou muté une base distante. Build Render complet, handshake Neon, restauration opérationnelle et autorisations source restent des validations distinctes ; sauvegarde/restauration complète prévue au lot8. Rapport propriétaire de pré-déploiement après lot6.

Les agents/tests ont terminé et le PostgreSQL local est conservé. Le lot6 démarre uniquement après le succès du gate main ci-dessus, depuis8ce46a3.
