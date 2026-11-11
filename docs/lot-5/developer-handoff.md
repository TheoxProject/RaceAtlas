# Handoff Developer — lot5, correction cycle2 F6

Branche `feature/map-experience`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/7, base intégrée **3bd018bff1b60f3831606348831fd72375f557dd**. Dernier candidat revu **fc8f540c4263c9b70de1b8a291ff98806b37299f** : CI43025992904 SUCCESS315PASS133,58s, revue indépendante315PASS252,70s mais **REQUEST CHANGES F6**. F1–F5 fermés par Tester. Le commit contenant ce handoff est le candidat C2 ; relever HEAD local/distant/PR. Après push, source et documents figés. **Aucun APPROVE ni merge lot5 acquis.**

## Correctif minimal et périmètre

F6 : simple Tab/Entrée sur année ISO2026 ou semaine53 inchangée déplaçait l'ancre du2027-01-01 au lundi2026-12-28 ; le retour civil affichait2026 ouDécembre2026 sans nouvelle sélection réelle. `changePeriod` conserve désormais strictement l'objet et la date d'ancrage quand année/mois/semaine normalisés ne changent pas. Une vraie bascule de mode conserve cette date ; un mode déjà actif est aussi un no-op. Une année/mois/semaine réellement modifiée continue de recalculer l'ancre, avec bornage des semaines et jours bissextiles existant. Aucun changement Filters/validation numérique/MapView/API/backend/migration/contrat.

Fichiers C2 : `frontend/src/catalog.js` (quatre lignes ajoutées, un retour ajusté), `catalog.test.js`, `App.test.jsx`, scénario NouvelAn existant dans `tests/backend/test_e2e.py`, présent handoff, checkpoint et mise à jour bornée des comptes de tests dans usage local. Aucune nouvelle dépendance ni fixture.

Régressions : identité stricte aux dates2027-01-01/2025-12-31/2024-02-29, clamp54→semaine53 déjà sélectionnée sans réancrage, vraie semaine52/année/mois toujours changés. Dans App, détails ouverts, blur/Entrée ISO et bouton du mode courant ne relancent pas le loader et ne ferment pas les détails. Navigateur réel : matrice quatre cas ISOyear/week×Tab/Enter, requêtes catalogue/carte stables après debounce180ms, détails conservés, retourAnnée2027 ouMoisJanvier2027. Les anciens tests décimales, valeurs vides/négatives, semaines52/53/54, course multijour, caméra exacte et parentcaptures absent restent en place.

## Commandes et résultats C2 réels

Dépendances/cache Python3.12.14, Node24.22.1, PostgreSQL17.11 et Chromium réutilisés, aucune réinstallation. Depuis frontend :

```powershell
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vitest/vitest.mjs run --pool=threads --maxWorkers=1
node node_modules/vite/bin/vite.js build
```

**28tests frontend PASS9,87s**, code0 sans erreur de runner :22catalogue +6App. ESLint PASS ; build37modules PASS3,99s, JS1183,90kB/330,87kB gzip etCSS81,76kB/13,15kB gzip. Avertissement moteur>500kB conservé, aucun seuil masqué.

Depuis racine :

```powershell
$python = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
$env:PLAYWRIGHT_BROWSERS_PATH = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
& $python -m pytest tests/backend/test_e2e.py -k new_year -q --tb=short
& $python -m ruff check raceatlas migrations tests/backend
& $python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
git diff --check
```

**E2E NouvelAn1PASS34,00s**,10désélectionnés, code0 ; Chromium/WebGL réel et React compilé→Flask→PostgreSQL, style/DEM synthétiques interceptés, aucun fournisseur contacté. Migrations upgrade/check/downgrade/upgrade/check de la fixture incluses.26contrats PASS ; lint/format Python et diff PASS. Pas de campagne backend complète redondante : catalogue/DB/loader/MapView inchangés dans C2. Les315PASS indépendants et la CI verte de fc8 sont des preuves historiques ; **une nouvelle CI complète315 et revue du SHA C2 sont obligatoires**, sans prétendre avoir exécuté315localement sur ce correctif.

## Revue indépendante et suite

Tester relève le SHA final/propreté/base, lit le petit diff depuisfc8 et vérifie notamment les quatre interactions sans changement, retours civils et absence de requête/réinitialisation des détails. Les preuves315backend/11WebGL surfc8 et les critères complets restent à évaluer avec les régressions ciblées appropriées au nouveau SHA. Utiliser uniquement `raceatlas_lot2_review`, opt-in jetable, jamais `_test` ni `_map_demo` en parallèle. Ne pas initdb/reseed aveuglément ; reviewer12fixtures après anciennes sondes. Aucun writer pendant revue et aucun APPROVE valable pour un SHA différent.

Tous tests Developer terminés code0, aucun processus Python/preview restant ; PostgreSQL local conservé actif. Cache Chromium et commandes dans CURRENT_STATE. Aucun défaut connu restant après C2, avis indépendant à obtenir. Aucun benchmark matériel mobile/régional exhaustif, audit complet des licences terrain, compatibilité FFC réelle ou liveSummit/SLA revendiqué. Seul smokeAltitude historique limité vu ; ne pas relancer les appels externes aveuglément.

Après intégration5 : validation progressive durable AGENTS/workflow, README/CI main/contrôle SHA, configs Render Free monolitheFlask/Waitress et NeonTLS sans service distant, lot6 calendrier puis rapport pré-déploiement propriétaire, lots7/8 et RC. Qualification FFC limitée Coordinator séparée, droits/incertitudes préservés. Aucun déploiement, dépense, mutation distante, collecte massive/récurrente ou tag/publication finale. Décisions propriétaire Altitude initial et mois calendrier conservé au retour carte inchangées.
