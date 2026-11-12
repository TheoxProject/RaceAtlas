# Lot 6 — calendrier mensuel et validation locale

CAL-02 ajoute la vue mensuelle en cours de revue. Entrer depuis Année/Semaine sélectionne le mois civil affiché, revenir Carte conserve mois/filtres/caméra. Les contrôles du calendrier restent mensuels et bornés à 1900–2200. Le bouton de chaque jour donne accès à toutes ses courses, même si seules une ou deux chips sont visibles. Les dernières semaines restent accessibles par le scroll du calendrier. Les détails et filtres sont partagés, sans recalcul des catégories côté calendrier. En rayon, les localisations à confirmer restent consultables à part, exclues des jours/totaux confirmés.

La carte reste montée lorsqu'elle est masquée ; le retour conserve zoom et Summit. Pour changer le centre depuis le calendrier, choisir l'option ouvre la carte visible ; les coordonnées peuvent aussi être saisies dans le formulaire. Aucun compte, page liste séparée, export ICS ou déploiement ajouté.

Tests ciblés supplémentaires depuis `frontend` :

```powershell
node node_modules/vitest/vitest.mjs run src/App.test.jsx --pool=threads --maxWorkers=1
node node_modules/vitest/vitest.mjs run src/Calendar.test.jsx --pool=threads --maxWorkers=1
```

Après build et configuration de la base PostgreSQL jetable `_test`/`_review` et de Chromium selon le [guide carte](../lot-5/local-development.md), depuis racine :

```powershell
python -m pytest tests/backend/test_calendar_e2e.py tests/backend/test_e2e.py -q --tb=short
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
```

Le helper `set_civil_date` fige uniquement Date avant les imports ; performance, timers et RAF restent natifs. Ne pas réintroduire `page.clock.set_fixed_time` avec Playwright 1.56 : reculs de performance reproduits, correctif validé sur bbd7625897040519a5e11ba9dd495c9cda605387. Styles/DEM synthétiques interceptés et MapLibre réel ; captures bornées `.local-tools/lot6-screenshots/{desktop,mobile,day-details,candidates}.png`. Ces tests ne qualifient pas les fournisseurs, FFC ou un environnement distant. Résultats et SHA courant au [handoff](developer-handoff.md).

La synchronisation de sélection du calendrier possède un budget de test explicite de 15 s ; ce n'est pas un SLA produit et cela ne change pas l'attente caméra 60° limitée à 10 s. Le parcours Summit→ISO→Calendrier mesure les phases API/ready sur l'horloge monotone hôte. Résumé synthétique local `selection-timing.json` dans le même dossier ignoré, trace limitée à 24 événements classés, sans URL/query/headers/body/env ; cette mesure inclut le transport et l'observateur, pas uniquement le rendu. Seuls les quatre PNG connus sont copiés par la CI ; un échec de disponibilité joint aussi un résumé borné à l'erreur.

## Calculs CAL-01 inchangés

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

Aucune base ni ressource externe n'est nécessaire aux tests des fonctions pures. Les E2E ci-dessus utilisent les bases jetables distinctes et les styles/DEM interceptés décrits au checkpoint ; vérifier l'état des processus et PostgreSQL avant leur setup. Aucun smoke fournisseur, import FFC, service distant ou déploiement autorisé par ces commandes.
