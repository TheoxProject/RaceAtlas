# Handoff Developer — lot6, jalon CAL-01

Branche `feature/monthly-calendar`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/9, base **8ce46a3fc1129a905d2e9f1fc8552e3cf4d0a56f**. CAL-01 **eba50f3735c6d19344ca9221da5f5adecf55a77d** a reçu APPROVE ciblé, mais CI43175452166 échoue sur un ancien scénario Summit (384PASS/1FAIL). Le commit contenant ce handoff ajoute seulement le diagnostic de cet échec ; relever son SHA local/distant/PR. **Pas de correction déclarée ou verdict final, aucun merge lot6.**

## Diagnostic CI prioritaire, produit inchangé

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
