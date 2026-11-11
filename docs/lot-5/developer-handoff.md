# Handoff Developer — lot5, correction cycle1 finale

Branche `feature/map-experience`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/7, base intégrée `3bd018bff1b60f3831606348831fd72375f557dd`. **Premier correctif publié :00986e59d8ce882b7353d573cfa71f1f15e7116d.** Le commit contenant ce handoff et le dernier ajustement MapView/test est le candidat final ; relever HEAD local/distant/PR avant revue. Après ce push, toutes éditions suivies cessent. **Aucun APPROVE ni merge lot5 acquis.**

Ancien candidat4ce971f6a96d7d0ccbec75553db07f1f3389c388 : Tester REQUEST CHANGES, rapport `.local-tools/tester-report-lot5.md`, CI42996366566 failure307PASS/6FAIL. CI du code00986 :43024003147 FAILURE313PASS/1FAIL, test Summit lisant pitch35 avant fin de transition500ms. Le candidat remplaçant attend réellement la caméra pitch60 (10s maximum) puis conserve assertion exacte, DEM>100 et modepressed. Sa propre CI complète et revue restent obligatoires.

## Livraison et corrections

Carte React/MapLibre5.11.0 réelle : Altitude initial ombrage/pitch35°, Summit à la demande terrain1,3/pitch60°, commune-center markers regroupés puis clusters de courses distinctes, filtres partagés et chargement couplé/versionné de toutes les pages, détails/scopes/règles/incertitudes, candidates non localisées séparées du total rayon, responsive390px et erreurs/reprises. Périodes/filtres/réactualisation ne réinitialisent pas la caméra. Options dynamiques GET `/api/v1/catalog/options` additives, réponse séparée1.0 ; OpenAPI collection1.1, anciennes réponses catalogue/carte/fiche1.0 inchangées. Migration toujoursb7f4208ac112.

Le cycle1 modifie douze fichiers déjà livrés : `frontend/src/{catalog.js,catalog.test.js,Filters.jsx,App.test.jsx,style.css,MapView.jsx}`, `tests/backend/{test_e2e.py,map_support.py}`, `contracts/openapi.json`, les deux documents usage/handoff du lot et le checkpoint.

- **F1** : création des parents de captures, cas sansWebGL autonome ; dixième E2E détourne SHOTS vers `tmp_path/absent-parent/screenshots` et prouve sa création sans cache préalable.
- **F2** : bande d'attribution auto dimensionnée distincte de la rangée carte, sheet mobile limité à cette dernière ; hit-test de chacun des quatre liens avant ouverture, dans l'explorateur et dans les détails, y compris candidate rayon. Captures mobile et mobile-details vues : crédits visibles, scroll interne conservé.
- **F3/F4** : date d'ancrage civile et année ISO distinctes. Au2027-01-01 initialcivil2027, premier ISO2026-W53 (2026-12-28..2027-01-03), course multijour visible. Champ Année ISO en semaine, Année civile sinon ; années/semaines entières validées au blur/Entrée. Décimales/vides/0/-1 rejetés sans sélection invalide, semaines54/53 inexistantes bornées selon l'année ISO. Modifier mois/année civile recalcule ISO en bornant les jours bissextiles ; modifier la semaine ancre son lundi puis synchronise les modes civils. Simple bascule de mode conserve la date ciblée.
- **F5** : sept textes français UTF8 OpenAPI restaurés, aucun schéma/version/route changé dans ce correctif.

Les premiers attendus du nouveau test ont été corrigés contre la fixture effective (course multijour débordant sur2027, nom `race-mtb-multiday`). La baseline caméra est prise après marqueur+700ms pour laisser finir la transition initiale500ms du moteur ; assertion exacte conservée, aucune tolérance ajoutée aux anciennes assertions. Pas de changement produit pour faire passer un attendu erroné.

Initialisation MapLibre complétée : `once(style.load)` avec garde active, au lieu de dépendre de `load` qui attend les tuiles visibles selon la source moteur épinglée. Ceci autorise marqueurs/DEM même si le fond reste en attente. Nouveau scénario garde les routes raster suspendues, vérifie ready/API12/marker11 puis les abandonne en cleanup. Un timeout natif de démarrage20s suivi d'un rerun unique PASS16,24s ne prouve pas à lui seul une causalité GPU ; cette amélioration est fondée sur les événements moteur et la preuve avec fond retenu.

## Commandes et résultats réels

Python3.12.14, Node24.22.1, PostgreSQL17.11 et Chromium caches réutilisés ; aucun reinstall/initdb. Depuis racine :

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
node node_modules/vitest/vitest.mjs run --pool=threads --maxWorkers=1
node node_modules/vite/bin/vite.js build
Pop-Location
& 'C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m pip --python $python check
git diff --check
```

**314pytest PASS198,74s sur code00986**, aucun skip, dont10Chromium/WebGL réels et migrations upgrade/check/downgrade/upgrade/check. Cette campagne complète précède les derniers ajustements MapView/attente du test ; elle valide F1–F5 : API/DB réelle, centre corrigé et caméra, périodes/ISO/multijour, catégories/scopes/ambiguïtés, mobile/rayon/nonlocalisées, DEM décodé>100, panneDEM et fond, clusters/clavier,409borné/retry, WebGL absent, base vide/panne. Styles/DEM synthétiques interceptés, pas d'appel fournisseur pendant les tests.

**23tests frontend groupés PASS11,57s**, code0 sans erreur de runner (18catalogue +5App). Ancien problème de worker groupé non reproduit sur ce correctif ; aucun run échoué compté PASS. **26contrats PASS**, Ruff37 lint/format PASS, ESLint PASS, build Vite PASS, pip sans paquet cassé, diff-check PASS. Dernier build MapView JS1183,71kB/330,81kB gzip etCSS81,76kB/13,15kB gzip ; avertissement moteur>500kB conservé, aucun seuil masqué.

Ciblés préalables : mobile+WebGL2PASS, nouveau NouvelAn1PASS12,65s après corrections d'attendus et stabilisation initiale. Après changement MapView, campagne11E2E :10PASS/1FAIL115,46s ; unique échec du nouveau harness pending avant chargement (Playwright ne peut wrapper directement builtin list.append), corrigé en lambda. Puis **pending+base_warning2PASS19,33s**, code0 ; requêtes raster réellement retenues avant ready/API12/marker11 puis abortcleanup. Aucun315global local revendiqué, CI complète du SHA final obligatoire. Aucun test Python/preview Developer restant ; PostgreSQL local conservé actif.

## Revue indépendante et restrictions

Tester vérifie SHA final/propreté/base, lit le diff depuis4ce et les critères complets de mission, utilise seulement `raceatlas_lot2_review` avec opt-in jetable (jamais `_test` ni `_map_demo` en parallèle). Ne pas initdb/reseed aveuglément. La baseReviewer peut contenir417synthétiques après anciennes sondes ; fixtures réinitialisent leur seule base. Rejouer notamment crédits hit-test, dates de part et d'autre du NouvelAn, saisies invalides et transitions, caméra, parentcaptures absent, puis contrôler les régressions nécessaires. Aucun source modifié pendant revue. CI verte et APPROVE doivent viser le même SHA final, pas seulement00986.

Préflight fournisseur historique limité : métadonnées Liberty/Mapterhorn200, Terrarium512 confirmé, capture liveAltitude vue ; liveSummit expiré10s sousSwiftShader, pas de qualification réussie ni bilan réseau final revendiqué. Ne pas relancer ce smoke aveuglément. Audit complet licences terrain, performance matériel mobile/corpus régional et compatibilité FFC réelle restent ouverts avant release. Aucun défaut produit connu restant après correction locale ; avis indépendant à obtenir.

Suite après intégration5 : workflow durable validation progressive, README/CI main et head courant, configs Render Free monolithe/Neon TLS sans déploiement ; lot6 calendrier puis rapport pré-déploiement propriétaire, lots7/8 et RC. Qualification FFC limitée Coordinator séparée, droits/incertitudes préservés. Aucun compte payant, déploiement, mutation distante, collecte live massive/récurrente ou tag/publication finale autorisé par ce handoff. Choix propriétaire Altitude initial et mois calendrier conservé au retour carte inchangés.
