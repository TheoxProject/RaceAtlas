# Lot6 — calculs mensuels et validation locale

Le jalon CAL-01 apporte seulement les fonctions pures de `frontend/src/calendar.js`. La carte existante reste affichée : le calendrier visuel, ses détails et sa conservation de caméra viendront à CAL-02/03 après revue du jalon.

## Contrat interne

`selectCalendarMonth` transforme la période partagée vers `mode: 'month'`, à partir de son année/mois civils, en réutilisant `changePeriod`. Ainsi une ancre2027-01-01 portant ISO2026W53 sélectionne bien janvier2027. Une sélection mensuelle inchangée conserve l'objet et la date d'ancrage ; les demandes invalides ou hors1900–2200 ne modifient pas l'état. `moveCalendarMonth` applique les mois entiers et conserve les règles de clamp du jour déjà utilisées par la carte.

`monthGrid` calcule uniquement avec dates UTC et getters UTC, sans heure locale implicite. Les cellules hors mois portent `inMonth: false`. `projectCalendar` utilise les items du loader existant et l'intervalle mensuel de `periodRange`, sans nouveau filtrage de catégories ni appel réseau. Une course apparaît chaque jour inclus dans le mois, mais une seule fois dans `total` ; les marges ne présentent aucune donnée prétendument complète. Les objets API et témoins de scopes restent les mêmes références. En rayon, passer `{radius: true}` pour séparer les IDs de `selection.unlocatedIds` dans `candidates` ; ils ne figurent ni dans les cellules ni dans le total confirmé. Hors rayon, les non-localisées restent visibles normalement.

## Commandes PowerShell

Utiliser le cache Node/pnpm existant si compatible, sans réinstallation. Depuis racine :

```powershell
Push-Location frontend
node node_modules/vitest/vitest.mjs run src/calendar.test.js --pool=threads --maxWorkers=1
node node_modules/eslint/bin/eslint.js . --max-warnings 0
node node_modules/vite/bin/vite.js build
Pop-Location
node --test tests/contracts/contracts.test.mjs
git diff --check
```

Le fichier calendrier contient32cas ciblés. Sur ce poste Windows, un run groupé avec le catalogue inchangé a bloqué au démarrage d'un worker ; il a été arrêté après identification exacte du PID et n'est pas une réussite. Un run calendrier seul terminé avec code0 est disponible ; ne pas modifier Vitest pour masquer l'incident, ne pas arrêter tous les Node et ne pas relancer le backend385 inchangé pour ce helper isolé. La CI du SHA courant reste obligatoire.

Aucune base ni ressource externe n'est nécessaire à ces tests. Les futurs E2E du lot utiliseront les bases jetables distinctes et les styles/DEM interceptés décrits au checkpoint ; ne pas lancer leur setup/reseed avant l'attribution CAL-03. Aucun smoke fournisseur, import FFC, service distant ou déploiement autorisé par ces commandes.
