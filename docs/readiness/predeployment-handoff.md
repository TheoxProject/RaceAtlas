# Handoff PRE-01 — rapport après lot 6

Branche isolée `feature/predeployment-report`, PR https://github.com/TheoxProject/RaceAtlas/pull/10. Base intégrée **7b733d86d99a354fdcfe2bf1ecbde519ef78a68f** ; cadrage local/distant avant ce jalon **b762a55798e2747ed115a0301f8cba26910c5f6a**. Relever le SHA de ce commit après publication et le geler pour Tester/CI. Aucun verdict ancien transféré au nouveau candidat.

## Livraison et choix

- `ops/render.yaml` : seule valeur nouvelle `region: frankfurt`, conforme à la référence officielle ; service Free unique, main, déploiements automatiques et previews toujours désactivés, pas de base Render ni migration au build/start.
- `frontend/src/MapView.jsx` : seul href Mapterhorn remplacé par `https://mapterhorn.com/attribution`, comme la homepage/README fournisseur et le TileJSON observé le 11 novembre. Quatre crédits et tout le moteur/caméra inchangés. Aucun test ajouté pour recopier une simple valeur.
- `predeployment-report.md` : architecture/secrets/TLS/Basic/santé, séquence d'activation future conditionnelle, migrations manuelles, fixture distante non préparée, sauvegarde/restauration, scénarios chiffrés, preuves/non-preuves, droits fournisseurs/FFC et expéditeur absent. Trois moments de premier déploiement ; attendre le candidat après lot 8 recommandé. Ce rapport ne déclenche pas la consultation ni l'exécution.
- `hosting.md`, README et checkpoint : cohérence avec lots 0–6 intégrés, région et rapport actuel. Aucun autre code, API, modèle, migration, dépendance, auth ou configuration CI modifié.

Le choix propriétaire email/mot de passe avec récupération par email est enregistré, sans domaine ni expéditeur disponible. Développement futur sur simulateur local possible, aucune délivrabilité/envoi réel validé. Création de compte/service, import Blueprint, déploiement, DB distante, paiement, email et collecte : **zéro** dans ce jalon.

## Sources et limites

Relecture primaire le **12 novembre 2026** : Render Free/Blueprint/régions/compute/pipeline/native runtime/web services ; Neon plans/régions/TLS ; PostgreSQL pg_dump ; OpenFreeMap quick start/conditions/licences ; Mapterhorn homepage/data-access/README public. Liens directs dans le rapport. Comptes/quotas restants/facturation privée non inspectés. Aucun volume annuel FFC ou performance Render extrapolé ; les scénarios sont des hypothèses explicitement nommées et calculées, pas des mesures distantes.

Le JSON d'attribution Mapterhorn avait répondu 403 au GET standard du 12 novembre : **aucune nouvelle tentative**, changement d'User-Agent, miroir, tuile ou archive demandé ici. L'adresse de la page d'attribution est confirmée par les documents publics et la preuve TileJSON antérieure ; sa conformité détaillée n'est pas validée par le href. Pas de nouveau GET FFC ; qualification limitée antérieure réutilisée avec ses échecs et droits non établis.

Les preuves hosting PR8, lot6 et CI main sont réutilisées pour les sources inchangées ; aucune connexion Neon, build Render, exercice complet de restauration, navigateur GPU physique ou transport email réel prétendu. Les tests offline de crédits ne qualifient ni droits ni disponibilité réseau.

## Commandes et observations de ce jalon

```powershell
node .local-tools/readiness-yaml-check.cjs
node -e "const fs=require('fs');const yaml=require('./frontend/node_modules/.pnpm/js-yaml@4.3.2/node_modules/js-yaml');const r=yaml.load(fs.readFileSync('ops/render.yaml','utf8'));if(r.services[0].region!=='frankfurt')throw Error('region');console.log('frankfurt PASS')"
python .local-tools/check-predeployment-docs.py
# Depuis frontend
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vite/bin/vite.js build
# Depuis racine avec DB _test + opt-in et Chromium du checkpoint
python -m pytest tests/backend/test_e2e.py tests/backend/test_calendar_e2e.py -k 'compiled_mobile_filters or calendar_new_year' -q --tb=short
git diff --check
```

Parse YAML avec le parser déjà en cache et gardes d'inactivité PASS ; région `frankfurt` PASS. Aucun appel de validation/import sur Render et aucune dépendance installée. ESLint PASS, build réel PASS **6,50 s**, 40 modules, avertissement de taille du bundle existant. Script ignoré : **31 liens locaux résolus, arithmétique des sept scénarios et href PASS**. Premier passage avant création de ce handoff échouait sur ce lien encore absent, puis contrôle final PASS. Les liens primaires ont été lus via outils web, sans affirmer que les ressources protégées ont répondu 200.

Avant tests natifs : `pg_ctl status` confirme le cluster existant PID 38028 / port 55434 ; aucun processus pytest/Vitest/A-B concurrent. Python 3.12.14, PostgreSQL 17.11, Chromium/cache réutilisés, uniquement `raceatlas_lot2_test` et opt-in. Pas d'initdb ou mutation distante. **Deux parcours crédits desktop/mobile PASS, 13 désélectionnés, 45,80 s, code 0** ; hits sur quatre crédits avec panneaux mobiles et retour calendrier→carte Summit. Aucun backend 389 complet local ni campagne 15 E2E inchangée. Diff PASS, sources backend/migrations/contrats/catalogue/calculs/tests inchangées (`git diff --quiet HEAD -- raceatlas migrations contracts frontend/src/catalog.js frontend/src/calendar.js tests`, code 0 avant commit). Aucun processus Developer conservé.

Après publication : arbre propre et arrêt des éditions jusqu'à revue indépendante du SHA exact. CI actuelle, APPROVE exact, merge et main verte restent des gates du Coordinator. Aucun déploiement ni décision propriétaire supposé.
