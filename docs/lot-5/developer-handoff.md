# Handoff Developer — lot5

Branche `feature/map-experience`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/7, base intégrée `3bd018bff1b60f3831606348831fd72375f557dd`. Dernier jalon **code testé** publié : **7f85cf4df97adf110e1fe10f9e75606cfa777583**. Le commit contenant ce handoff et le checkpoint final constitue le candidat ; relever HEAD et le comparer au distant/PR avant revue. Aucun APPROVE lot5 ni merge acquis. Après publication finale, éditions suivies arrêtées.

## Livré et fichiers

- `frontend/src/catalog.js` : état initial Paris, bornes Année/Mois/ISO, domaines validés, regroupement communes, chargement paginé couplé/versionné et annulation. `catalog.test.js` :16cas temporels et cycle de données.
- `App.jsx`, `Filters.jsx`, `MapView.jsx`, `RaceDetails.jsx`, `style.css` : carte dominante responsive, filtres stricts, terrain et replis, markers/clusters accessibles, panneau desktop/bottom sheet mobile et détails par scope. `App.test.jsx` :4cas UI, y compris métadonnées/retry et ancienne réponse non annulable ignorée.
- `frontend/package.json` et `pnpm-lock.yaml` : MapLibre GL JS **5.11.0** exact. Installation depuis pnpm10.20.0 compatible en cache ; MapLibre absent du cache téléchargé avec ses dépendances gratuites, aucun script de dépendance activé. Aucun changement Python de dépendances.
- `raceatlas/__init__.py`, `contracts/catalog-options.schema.json`, `contracts/openapi.json`, `tests/backend/test_catalog_options.py`, mise à jour limitée du résolveur `tests/contracts/contracts.test.mjs` : route options additive approuvée par Coordinator, référentiel de catégories indépendant des résultats. Collection OpenAPI1.1.0, nouvelle réponse options1.0.0 ; formes/versions catalogue/carte/fiche1.0.0 inchangées.3tests options (u15 sans course, vide, panne).
- `tests/backend/test_e2e.py`, `map_support.py` :9parcours React compilé→Flask→PostgreSQL, moteur MapLibre/Chromium réel, styles et Terrarium512 synthétiques interceptés. Anciennes assertions de démonstration remplacées en conservant garanties DB/réactualisation/vide/indisponibilité.
- Mission, présent handoff, usage local et checkpoint. Aucune migration ni fixture historique modifiée. Captures/scripts de smoke ignorés, aucun asset construit ni tuile brute commis.

## Choix et comportements

Filtres en mémoire UI seulement, initialisation à l'année civile actuelle Europe/Paris, distincte de la saison FFC. Frontières ISO/leap-year testées ; saisie d'année validée sur blur/Entrée. Période et autres filtres ne réinitialisent pas la caméra. Décisions propriétaire futures préservées : Altitude initial, Summit à la demande ; ouverture future du calendrier sélectionnera le mois affiché et le gardera au retour carte, autres filtres/caméra préservés. Aucun faux calendrier/compte/inscription.

Loader : toutes les pages des deux flux, y compris pages rayon sans confirmées, versions cohérentes entre routes/pages puis vérification finale ; trois tentatives maximum sur409, échec clair/retry, requêtes périmées annulées ou ignorées. Candidates non localisées via fiches, par groupes de huit ; jamais ajoutées au total du rayon. Point de rayon explicitement choisi par l'utilisateur, sans localisation de départ inventée.

Courses distinctes→communes→clusters spatiaux, comptes distincts indépendants des scopes. Signature incluant coordonnées/IDs/membres/nom ; boutons inchangés conservés pour le focus, centres corrigés mis à jour. Synchronisation sur render : DEM en échec n'empêche plus le compte du marqueur. Une source DEM pour hillshade, seconde créée seulement pour Summit, selon recommandation du moteur ; Altitude35°, Summit terrain1,3/pitch60°. Panne DEM→Altitude et Summit désactivé ; avertissement générique du fond conserve un terrain utilisable. Aucune modification des politiques du navigateur utilisateur.

Scopes/règles/restrictions corrélées, incertitudes et fraîcheur affichés. Source absente/à vérifier distincte d'une annulation explicite ; admissibilité personnelle non évaluée. IDs utilisés comme clés internes et pas comme contrôles produit ; libellés et noms de fixtures historiques restent les données de source synthétique. Attributions permanentes OpenStreetMap/OpenMapTiles/OpenFreeMap/Mapterhorn.

## Commandes exactes et preuves

Environnement Python3.12.14, Node24.22.1, PostgreSQL17.11 local, Chromium en cache. Depuis racine :

```powershell
$python = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
$env:PLAYWRIGHT_BROWSERS_PATH = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
& $python -m pytest -q --tb=short
& $python -m ruff check raceatlas migrations tests/backend
& $python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
Push-Location frontend
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vitest/vitest.mjs run src/catalog.test.js --pool=threads --maxWorkers=1
node node_modules/vitest/vitest.mjs run src/App.test.jsx --pool=threads --maxWorkers=1
node node_modules/vite/bin/vite.js build
Pop-Location
& 'C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m pip --python $python check
git diff --check
```

**313/313pytest PASS en295,09s**, aucun skip, dont9Chromium : DB réelle et modification source/centre, caméra inchangée, période/mois, scopes ambigus, mobile390px ET/rayon/non-localisées, terrain DEM décodé (`queryTerrainElevation>100`), DEM en échec, avertissement fond sans désactivation Summit, communes puis clustering distinct/activation clavier,409borné/reprise, WebGL indisponible avec détails, vide, panneDB. Migrations upgrade/check/downgrade/upgrade/check incluses, version toujoursb7f4208ac112.

Ruff lint/format37fichiers PASS ;26contrats Node PASS ; ESLint PASS ; build Vite PASS ; pip check PASS ; diff-check PASS. **16tests catalogue frontend PASS en5,26s et4tests UI PASS en4,28s**, chacun avec code0, aucune erreur de runner. Le premier run groupé20tests avait passé11,21s ; dernier run groupé a rencontré un timeout de démarrage de worker (4tests UI exécutés, code1), **pas compté PASS**. Reprises isolées natives ci-dessus propres ; aucune configuration produit modifiée pour masquer l'erreur. Un runner sandbox sans tests avait été arrêté après vérification exacte de son PID/commande/parent, aucun Node étranger arrêté.

Développement navigateur : premiers attendus Mois/casse de labels corrigés contre fixtures, aria-labels explicites ajoutés ;8tests ont ensuite passé56,79s. Inspection visuelle a révélé marqueurs idle/DEM ; assertions renforcées ont révélé le couplage avertissement/mode, corrigé. Le global313PASS ci-dessus inclut toutes corrections et le neuvième scénario. Aucun défaut local connu restant ; ces preuves ne remplacent pas la revue indépendante.

## Captures et qualification limitée

Captures ignorées `.local-tools/lot5-screenshots/` inspectées : `desktop.png`, `mobile.png`, `mobile-details.png`, `summit.png`, `cluster-details.png`, `dem-failure.png`, `webgl-failure.png`. Lisibilité desktop1440/mobile390, bottom sheet, comptes11/10+1, messages et attributions vérifiés. Les sept captures déterministes utilisent contours/DEM synthétiques, pas un fournisseur réel.

Préflight primaire limité 2026-11-11 : Liberty/TileJSON Mapterhorn/planet200, Terrarium512 et attributions confirmés ; résumé `.local-tools/lot5-provider-preflight.md`. Un seul smoke viewport local `_map_demo`, sans pan/zoom, deux hôtes autorisés, plafond80requêtes externes et temps bornés : `provider-altitude.png` montre fond/labels/ombrage réels, inspecté par Developer/Coordinator. **Capture Summit réelle expirée10s sous SwiftShader, script terminé en échec avant bilan réseau JSON** ; aucun nombre précis de succès HTTP, qualification live Summit, SLA ou compatibilité GPU générale revendiqué. Aucun autre smoke externe à relancer aveuglément. Aucun compte, achat, FFC ou téléchargement régional ; serveur arrêté dans finally. Sources terrain/licences complètes restent à qualifier avant ouverture publique.

## Revue indépendante et limites

Tester : relever le SHA final exact/propreté/base et utiliser uniquement sa base `raceatlas_lot2_review` avec opt-in jetable, pas `_test` ni `_map_demo`. PostgreSQL existant sain ; ne pas initdb. Réexécuter commandes, vérifier critères de mission et captures récentes, notamment centre corrigé/caméra, marqueurs en panne DEM, vraie élévation Summit et absence de mélange de versions. Ne pas modifier le source. CI et APPROVE doivent viser le même SHA final ; le code7f85cf4 et ses anciennes CI ne suffisent pas à approuver le commit documentaire final.

Bundle moteur environ1,18MB brut/330KB gzip, CSS82KB ; avertissement Vite de taille documenté sans seuil masqué. Pas de benchmark exhaustif sur mobile matériel ou corpus régional réel. Render Free/Neon, release, dépenses, collecte/récurrence et mutations distantes non activés. Preview locale distincte `_map_demo` migrée/seedée12fixtures, pas de serveur persistant. Tous les tests Developer terminés, PostgreSQL laissé actif ; reprise sûre détaillée dans CURRENT_STATE.
