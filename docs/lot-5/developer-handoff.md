# Handoff Developer — lot5, correction cycle3 F7 tests seulement

Branche `feature/map-experience`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/7, base intégrée **3bd018bff1b60f3831606348831fd72375f557dd**. Dernier candidat revu **5cd0c5839ce596d0e0426613659422b8dbb416cd** : Tester REQUEST CHANGES F7, F1–F6 CLOSED ; CI43028158824 FAILURE314PASS/1FAIL, attente Summit fragile. Le commit contenant ce handoff constitue le candidat C3 ; relever HEAD local/distant/PR, puis aucun writer pendant revue. **Aucun APPROVE ni merge acquis ; dernier cycle borné, pas d'approbation par épuisement.**

## Correction et garanties

Scope C3 : seulement `tests/backend/test_e2e.py`, présent handoff, checkpoint et instructions locales. Aucun produit JS/Python, MapView, contrat, dépendance ou fixture modifié. F7 ne démontrait pas un défaut produit : localement centre≈2e-12degrés différent avec zoom/bearing/pitch strictement identiques ; en CI pitch35 lu après700ms alors que l'animation n'avait pas fini.

Les deux parcours Summit partagent désormais une attente bornée10s sur le pitch60 réellement enregistré par moteur au moveend, puis conservent assertion60 stricte et preuve DEM décodé>100/mode. Les700ms fixes de caméra disparaissent. Le comparateur commun autorise uniquement **centre abs1e-9degré, rel0** (≈0,1mm), toutes les clés et autres valeurs zoom/bearing/pitch strictes. Les trois anciennes égalités de dictionnaires passent par ce même contrôle.

La chronologie utilise maintenant une caméra effectivement non initiale : clic du vrai contrôle MapLibreZoomin, attente zoom final initial+1 dans datasetcamera (mis à jour au moveend), puis baseline. Un contrôle négatif avec pytest.raises prouve que le comparateur refuse la caméra initiale enregistrée. Comparaisons répétées après no-ops et retoursAnnée/Mois, puis après changements réels ; un reset de zoom ne peut satisfaire la baseline. Aucun attendu métier supprimé, aucun timeout accru aveuglément.

## Tests C3 réellement exécutés

Python3.12.14, PostgreSQL17.11 et Chromium caches réutilisés ; build frontend5cd inchangé, aucun reinstall/initdb ni source produit édité.

```powershell
$python = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
$env:PLAYWRIGHT_BROWSERS_PATH = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
& $python -m pytest tests/backend/test_e2e.py -k 'compiled_react_flask_postgresql or new_year or base_map_warning' -q --tb=short
& $python -m ruff check raceatlas migrations tests/backend
& $python -m ruff format --check raceatlas migrations tests/backend
git diff --check
```

**3passed,8deselected in36,87s**, code0 dès première campagne C3 : principal React→Flask→PostgreSQL/mise à jour source et centre/Summit, chronologie NouvelAn avec zoom7,5 non initial et matriceF6, fond503 avec Summit. Migrations upgrade/check/downgrade/upgrade/check de la fixture incluses. Ruff37 lint/format et diff PASS. Moteur WebGL réel, style et DEM synthétiques interceptés, aucun fournisseur contacté.

Réutilisation explicite des preuves **5cd** inchangé pour produit :28frontend Developer PASS9,87s (22catalogue+6App),26contrats, ESLint/build PASS ; TesterC2 a aussi passé22+6 isolés après timeout initial workerApp non compté PASS, build/pip/statique/contrats. Sonde indépendante F6 : quatre cas ISOyear/week×Tab/Enter, détails/pasrefetch/retours2027Janvier et trois no-ops civils PASS ; crédits mobiles/WebGL autonome PASS. Ces succès ne transformaient pas son E2E caméra en PASS et ne masquaient pas la CI314/1.

Backend/MapView/loader/catalogue inchangés depuis validation indépendante **fc8**315tests dont11Chromium PASS252,70s et CI315PASS133,58s. Aucune nouvelle campagne complète backend/frontend redondante C3. **Nouvelle CI complète315 et revue du SHA C3 obligatoires** ; aucun315local C3 revendiqué. Bundle historique5cd1183,90kB/330,87kB gzip, avertissement moteur conservé.

## Revue et exploitation

Tester confirme SHA final/propreté/base et scope test-only, contrôle tolérance absolue stricte/attentes effectives/baseline zoomée/contrôle négatif puis rejoue les trois parcours et les sondes utiles ; évalue les critères complets avec preuves réutilisées clairement rattachées aux SHA historiques. Si échec persiste, remonter le blocage sans étendre arbitrairement la limite des cycles. Aucune auto-approbation Developer. Utiliser uniquement `raceatlas_lot2_review`, opt-in jetable ; jamais `_test` ni `_map_demo` simultanément. Ne pas initdb/reseed aveuglément.

Session95430 terminée code0 ; aucun Python/preview Developer restant, PostgreSQL local conservé actif. Aucune performance mobile physique/régionale exhaustive, liveSummit/SLA ou audit complet de droits revendiqué. Ancien smokeAltitude limité vu, ne pas relancer les fournisseurs aveuglément. Aucun déploiement, dépense, mutation distante, collecte massive/récurrente ou tag/publication finale.

Après intégration5 : workflow validation progressive, README/CI main/contrôle SHA, configs Render Free monolitheFlask/Waitress et NeonTLS sans service distant ; lot6 calendrier puis rapport pré-déploiement propriétaire, lots7/8 et RC. Qualification FFC limitée Coordinator séparée avec droits/incertitudes préservés. Décisions propriétaire Altitude initial et mois calendrier conservé au retour carte inchangées.
