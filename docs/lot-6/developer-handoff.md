# Handoff Developer — lot 6, jalon CAL-02

## Jalon courant à revoir

Branche `feature/monthly-calendar`, PR https://github.com/TheoxProject/RaceAtlas/pull/9, base **8ce46a3fc1129a905d2e9f1fc8552e3cf4d0a56f**. Parent avant publication : **bbd7625897040519a5e11ba9dd495c9cda605387**, CI `43219642754` SUCCESS : 386 pytest en 117,48 s, 60 frontend et tous contrôles. Tester APPROVE ciblé de ce parent : `.local-tools/tester-report-lot6-clock.md`, 4 PASS / 49,81 s et 165 sondes. Cela valide le correctif Clock inchangé, pas CAL-02. Relever le nouveau SHA publié, puis geler pour CI et revue ciblée. CAL-03 complète restera obligatoire.

Livraison : `Calendar.jsx`, `calendar.css` et tests du composant ; App et tests ; MapView visibilité/resize seulement ; trois nouveaux E2E ; whitelist CI bornée, README et documents du lot. CAL-01, catalog.js, API, modèles, migrations, dépendances, terrain et harness Clock inchangés.

La bascule sélectionne le mois civil partagé, retour Carte le conserve. Contrôles fonctionnels année/mois, navigation bornée, table lundi–dimanche avec boutons indépendants, marges désactivées. Deux chips maximum (une visible sur mobile), accès à toutes les courses par jour, détails RaceDetails communs et candidates rayon séparées. Les objets et témoins de scopes sélectionnés restent ceux du loader unique. Résultats liés au filtre/tentative pour cacher immédiatement les anciennes courses durant le debounce ; abort, 409 et retry conservés. Saisies inchangées gardent détail/ancre/requêtes. Choix de centre depuis calendrier ouvre la carte visible, avec formulaire existant.

MapView reste monté ; wrapper visible `display: contents` pour préserver la grille et la rangée crédits d'origine, masqué `display: none` avec tous ses contrôles/attributions. ResizeObserver ignore l'état masqué ; resize au retour, aucune reconstruction de caméra. Les tests partent de zoom 7.5 et Summit réel 60°, DEM >100, puis conservent centre/zoom/bearing/pitch et identité du nœud.

### Commandes et résultats CAL-02

Depuis `frontend`, Node 24/dépendances existants :

```powershell
node node_modules/vitest/vitest.mjs run src/App.test.jsx --pool=threads --maxWorkers=1
node node_modules/vitest/vitest.mjs run src/Calendar.test.jsx --pool=threads --maxWorkers=1
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vite/bin/vite.js build
```

**8 App PASS / 10,18 s ; 4 composant PASS / 3,39 s ; ESLint PASS ; dernier build PASS / 3,90 s.** Run groupé bloqué après App : NON PASS, Node 23324 identifié par commande exacte puis arrêté. Runs isolés terminés code 0, configuration Vitest inchangée. L'attendu initial « 0 course » corrigé en « 0 courses » ; contrôle d'absence immédiate des anciennes données PASS.

Depuis racine, Python 3.12.14/Chromium/cache et DB locale `raceatlas_lot2_test` avec opt-in :

```powershell
python -m pytest tests/backend/test_calendar_e2e.py tests/backend/test_e2e.py -q --tb=short
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
git diff --check
```

Premier E2E : 2 PASS / 1 FAIL en 51,60 s, sélecteur chip/ligne ambigu, corrigé en bornant au panneau. Inspection visuelle : fond vert/actions tassées par priorité CSS corrigés ; **3 E2E PASS / 63,36 s**. Ciblé suivant : **3 PASS / 1 FAIL en 55,15 s**, nouveaux accès réels aux 31 janvier / 30 novembre PASS mais ancien mobile a reproduit un recouvrement des crédits par le panneau. Wrapper corrigé en `display: contents`, sans toucher le test existant. **Dernier run carte + calendrier : 15 PASS en 170,41 s, code 0**, aucun processus restant. Il couvre aussi les 12 cas carte existants : données PG/refresh, credits mobile/détails, cluster, DEM/base failure, WebGL indisponible et erreurs/retry. Aucun backend complet local répété. Ruff check/format --check PASS (**40 fichiers**), **26 contrats et diff PASS**. Le build a d'abord été relancé avant application effective du script de correction (mauvais répertoire, pas une preuve du correctif) ; le script a ensuite été exécuté depuis racine, puis lint/build réels PASS 3,90 s avant ce dernier run.

Trois parcours nouveaux couvrent : ISO 2026 W53 / civil janvier 2027, course 31 décembre–2 janvier et compteur distinct ; caméra Summit non initiale conservée ; parité carte/calendrier catégories ET/OU et témoin de scope, non-localisée hors rayon et candidate exclue du rayon ; mobile 390 px, 11 courses accessibles, détails/retour, erreur/retry. Dernières semaines atteignables par scroll et clic (jour vide/panneau refermé), pas seulement visibles sur capture. Pas de scroll horizontal.

Captures synthétiques inspectées : `.local-tools/lot6-screenshots/{desktop,mobile,day-details,candidates}.png`. Les nouveaux tests capturent aussi au point d'échec avec timeout 5 s. CI copie uniquement ces quatre PNG réguliers non symlinks vers `calendar-<nom>.png`, sans écraser les preuves carte, rétention un jour inchangée. Aucun dump HTML/env/console ou données fournisseur. Pas de disponibilité GPU/fournisseurs/droits FFC, service distant ou déploiement qualifiés. Revue ciblée puis acceptation complète du SHA final requises ; arrêter les éditions après gel.

## Historique CAL-01 et correction d'horloge

Branche `feature/monthly-calendar`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/9, base **8ce46a3fc1129a905d2e9f1fc8552e3cf4d0a56f**. CAL-01 **eba50f3735c6d19344ca9221da5f5adecf55a77d** a reçu APPROVE ciblé. Parent du correctif actuel : **6982fddc5825e53f0e3eabd28dc0fdf27f9bd27a**, CI instrumentée `43179912170` : **383 PASS / 2 FAIL**. Ce commit corrige uniquement le harness de date ; relever son SHA publié pour CI et revue ciblée renouvelées. Aucun verdict final ou merge lot 6.

## Correctif Date seule — preuves actuelles

Suivi format uniquement : CI `43219175247` sur **9e3c3bc26b0840a6df7e0223655b092395ddeeef** arrêtée à `ruff format --check` (test_e2e.py à reformater), avant tout test backend/frontend. Après libération Tester, `python -m ruff format tests/backend/test_e2e.py` : un fichier reformaté, AST Python avant/après strictement identique. `python -m ruff check raceatlas migrations tests/backend` PASS ; `python -m ruff format --check raceatlas migrations tests/backend` PASS, 39 fichiers déjà formatés ; `git diff --check` PASS. Pas de rerun navigateur pour ce changement de présentation ; les 4 PASS ciblés ci-dessous restent une preuve de la logique inchangée, et non une CI verte du nouveau SHA. Nouvelle CI et revue runtime indépendantes encore requises.

Fichiers modifiés : `tests/backend/map_support.py`, `test_e2e.py`, ce handoff et le checkpoint. Aucun changement produit, calcul calendrier, dépendance, MapView ou animation. L'UI reste suspendue.

La CI a capturé une animation à 56,435° (dataset 35°), terrain réel 829,22, moving/easing vrais et contexte intact, avec reculs de performance. Le ClockController réellement embarqué par Playwright Python 1.56 (driver 1.56.1) a aussi été reproduit indépendamment : `[1000, 10, 1000]`, recul −990 ms. `set_fixed_time` installe implicitement les timers, RAF et performance ; MapLibre capture performance à l'import. [Issue primaire 37700](https://github.com/microsoft/playwright/issues/37700) et [correctif 37820](https://github.com/microsoft/playwright/pull/37820), consultés le 12 novembre 2026. Preuve minimale réutilisée du Tester : `.local-tools/tester-playwright-clock-minimal.cjs` ; rapport `.local-tools/tester-review-lot6-camera-diagnostic.md`.

Campagne A/B prédéfinie terminée, aucun retry conditionné au succès : deux mêmes cas par exécution (`compiled_react_flask_postgresql` et `base_map_warning`), pages neuves et assertions identiques. A1/A2/A3 Clock existant : chacun 2 PASS, 24,53 / 27,36 / 34,09 s, avec 6 / 10 / 7 reculs de performance. B1/B2/B3 Date seule : chacun 2 PASS, 19,33 / 25,08 / 24,17 s, aucun recul, date métier identique et fonctions natives inchangées. Les six résultats détaillés restent ignorés dans `.local-tools/clock-ab/<label>/result.json` ; commandes `python .local-tools/clock-ab-run.py playwright A1` ou `date-only B1`, labels jusqu'à 3. Ne pas les relancer aveuglément.

Cela prouve la contamination d'horloge et justifie son retrait ; aucun timeout complet n'a été reproduit dans ce bornage et la causalité du second échec CI (refresh PostgreSQL) n'est pas démontrée. L'observateur moteur/IPC, identique dans les deux variantes du cas base warning, influence potentiellement l'ordonnancement. Le scénario principal n'a pas cette instrumentation lourde. Aucune attribution démontrée à un défaut GPU/MapLibre.

`set_civil_date(page, iso)` ajoute un script avant navigation/imports : seule Date sans argument et `Date.now()` sont figées, les arguments explicites et statiques sont conservés par Proxy. Les trois usages de Clock sont remplacés. Le nouveau test navigateur contrôle appels/constructeur/sous-classe, arguments explicites dont undefined invalide, now/parse/UTC, Paris au 1er janvier 2027, identité des fonctions natives performance/timers/RAF, progression monotone et date toujours fixe. Le parcours Nouvel An exerce toujours ISO 2026 W53 / civil 2027 et caméra zoomée. Les vrais parcours MapLibre gardent animation, attente 10 s, pitch exact 60° et terrain > 100, sans jumpTo.

Commande native ciblée :

```powershell
python -m pytest tests/backend/test_e2e.py -k 'civil_date or compiled_react_flask_postgresql or base_map_warning or new_year_iso' -q --tb=short
python -m ruff check tests/backend/test_e2e.py tests/backend/map_support.py
git diff --check
```

Environnement : venv Python 3.12.14, Chromium/cache existants, DB locale `raceatlas_lot2_test` avec opt-in ; ressources carte/DEM synthétiques et aucune requête fournisseur. Aucun processus A/B ou pytest restant avant ce run, vérifié nativement. Résultat ciblé : **4 PASS, 8 désélectionnés, 64,05 s**, code 0 le 12 novembre 2026 ; Ruff et diff PASS. Pas de nouvelle campagne backend complète ou frontend inchangé ; CI complète et Tester sur le nouveau SHA restent requis. Après publication : arrêter les éditions jusqu'au verdict du Coordinator.

## Historique du diagnostic CI, produit inchangé

`tests/backend/map_support.py` et `test_e2e.py` ajoutent au scénario concerné un observateur du moteur existant via la fibre React19.2 épinglée, sans modifier MapView. Le binding transmet avant l'échec un cache borné au processus Python : caméra réelle et dataset séparés, moving/easing, terrain/élévation, mode/warning, contexte/erreurs agrégées, préférence reduced-motion, performance/Date/frames et temps monotone hôte. Trace60événements et12appelsstop/_stop maximum avec stacks courtes expurgées des URL. Aucun header/env/HTML/console brut enregistré.

Au timeout réel, lecture du cache hôte **sans réévaluation JS potentiellement bloquée**, puis capture `summit.png` avec plafond5s ; JSON réduit à12000caractères dans l'erreur/JUnit. Le nom PNG est déjà dans la whitelist synthétique de CI. Tous critères métier, clock, rendu et attente10s restent identiques, avec pitch60 strict et DEM>100. La réception d'un snapshot hôte est vérifiée dans le chemin local réussi.

Reproduction détaillée préalable :1PASS26,58s, fichier ignoré `.local-tools/diagnose-map-animation.py`. Elle a montré un moteur39,95° contre dataset35° lors de l'arrivée du DEM, puis les deux60° avec fin d'animation511ms, terrain présent et aucun pageerror. Cause du timeout CI non prouvée ; ni délai augmenté, ni workaround produit, ni attribution supposée à une issue upstream. Artefacts détaillés `.local-tools/map-animation-diagnostic/`.

Version finale du harness avec binding : **1PASS12,16s,10désélectionnés**, commande native `python -m pytest tests/backend/test_e2e.py -k base_map_warning -q --tb=short`, uniquement DB `_test` et ressources offline. Première version du collecteur avant demande de cache hôte :1PASS7,65s, pas une correction ou une clôture. Ruff/diff contrôlés après instrumentation. Un PASS du diagnostic ne ferme pas le défaut ; la prochaine CI instrumentée fournit une nouvelle observation, pas une relance jusqu'au vert. Aucun processus de test restant.

CAL-01 calculs et testsJS restent exactement ceux approuvés ci-dessous. Le composant calendrier isolé peut être préparé séparément sur autorisation, sans intégrer App/MapView/Filters ou pousser avant fin de cette CI. L'UI et la fusion restent suspendues à la décision Coordinator.

## Fichiers et interface livrés

`frontend/src/calendar.js`, `calendar.test.js`, présent handoff, usage local et checkpoint. Aucun changement `catalog.js`, App, MapView, Filters, CSS, API, modèle, migration, hosting ou source FFC. Aucun bouton calendrier factice ajouté ; le module n'est pas encore branché dans l'UI.

Quatre fonctions pures, sans dépendance ajoutée :

- `selectCalendarMonth(period, year = period.year, month = period.month)` réutilise `changePeriod` et conserve l'ancre civile en passant au mois. Un vrai no-op renvoie le même objet ; valeurs invalides également rejetées sans changement.
- `moveCalendarMonth(period, delta)` navigue en mois entiers, traverse décembre/janvier et respecte1900–2200. L'état d'origine est rendu si le mouvement est invalide ou hors limites. Exports `MIN_CALENDAR_YEAR`/`MAX_CALENDAR_YEAR` réutilisables par les futurs contrôles.
- `monthGrid(year, month)` retourne une grille plate en semaines complètes lundi–dimanche,28/35/42jours, dates civiles UTC. Cellules `{date, day, inMonth, items: []}` ; invalides→grille vide.
- `projectCalendar(period, selection, {radius = false})` retourne `{days, items, candidates, total}`. Intervalle mensuel issu de `periodRange`, projection inclusive start/end uniquement dans les cellules du mois. Les marges restent sans épreuves pour ne pas prétendre couvrir un autre mois. Déduplication stable par raceID, premier item source conservé tel quel, aucune fusion de scopes. `total` compte les IDs distincts, pas leurs occurrences journalières ou scopes.

En rayon, `selection.unlocatedIds` désigne les candidates : hors cellules/totaux confirmés, disponibles séparément par référence pour le futur panneau. Hors rayon les non-localisées restent des courses ordinaires de calendrier. Statuts, provenance, restrictions et `matching_scope_ids` ne sont ni réinterprétés ni copiés/fusionnés. Les entrées sont les objets contractuels du loader partagé ; aucune sélection catégorie concurrente n'est créée.

## Vérifications effectuées

Depuis `frontend`, runtime Node24 réutilisé :

```powershell
node node_modules/vitest/vitest.mjs run src/calendar.test.js --pool=threads --maxWorkers=1
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vite/bin/vite.js build
```

**32 tests calendrier PASS3,27s, code0 le12novembre2026**, après reprise explicite et confirmation Git ; mêmes fichiers préservés, aucune modification perdue. Avant interruption :32PASS3,62s, ESLint PASS, build PASS7,75s ;26contrats et diff PASS depuis racine. Pas de nouvelle campagne backend385 inchangée. La CI complète du SHA publié doit encore passer.

Cas :2024/2025 et siècles1900/2000/2100/2200, début/fin dimanche et mois de quatre semaines ; UTC sous trois valeurs TZ ; navigation réelle/clamps/bornes invalides ; Paris2027-01-01 et ISO2026W53→Janvier2027 ; no-ops avec identité stricte/ancre préservée ; fixture multijour31décembre puis1/2janvier avec total unique ; clipping de longs intervalles ; scopes multiples/manifestation commune sans mauvais comptage ; non-localisées hors rayon/candidates en rayon ; statuts cancelled/to_verify et objets source inchangés.

Incident runner initial : commande groupée `calendar.test.js catalog.test.js` bloquée au second worker après31cas calendrier PASS. Ce run n'est **pas compté PASS** : NodePID34828/parent38448 et commande exacte vérifiés avant arrêt du seul runner, session25917 exit1. Aucune configuration Vitest altérée. Le fichier catalogue existant n'est pas modifié ; calendrier seul ensuite terminé proprement deux fois. Aucun processus de test/preview Developer restant.

## Revue et phase suivante

Tester confirme SHA/propreté/base, inspecte ces fonctions et les critères CAL-01, exécute les32cas et les sondes indépendantes utiles. Reprendre explicitement les preuves des chemins inchangés ; l'ancienne CI de cadrage ne valide pas ce nouveau SHA. Garde des cellules hors mois, frontière civile/ISO, no-ops, déduplication et témoins/candidates sont prioritaires. Aucun writer pendant revue.

Après libération seulement, CAL-02 branchera une vraie UI mensuelle au loader/état partagé, avec détails et filtres communs, responsive390px, contrôle des mois et conservation effective de MapLibre/caméra/Summit. CAL-03 apportera les parcours réels React→Flask→PostgreSQL et captures ; ces comportements ne sont **pas encore livrés ou démontrés** par ce jalon pur. Une revue complète finale et la CI/main verte resteront obligatoires avant lot suivant.

Aucune DB ouverte pour CAL-01, aucune dépendance installée, aucun appel fournisseur/FFC, déploiement, paiement ou mutation distante. Rapport pré-déploiement propriétaire prévu après lot6 ; décisions de mois partagé et Altitude initial déjà acquises, aucune nouvelle consultation nécessaire.
