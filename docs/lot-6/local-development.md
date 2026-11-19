# Lot 6 — calendrier mensuel et validation locale

La vue mensuelle partage la sélection de la carte. Entrer depuis Année/Semaine sélectionne le mois civil affiché, revenir Carte conserve mois/filtres/caméra. Les contrôles du calendrier restent mensuels et bornés à 1900–2200. Le bouton de chaque jour donne accès à toutes ses courses, même si seules une ou deux chips sont visibles. Les dernières semaines restent accessibles par le scroll du calendrier. Les détails et filtres sont partagés, sans recalcul des catégories côté calendrier. En rayon, les localisations à confirmer restent consultables à part, exclues des jours/totaux confirmés.

La carte reste montée lorsqu'elle est masquée ; le retour conserve zoom et Summit. Pour changer le centre depuis le calendrier, choisir l'option ouvre la carte visible ; les coordonnées peuvent aussi être saisies dans le formulaire.

## Contrat interne

`selectCalendarMonth` transforme la période partagée vers `mode: 'month'`, à partir de son année/mois civils, en réutilisant `changePeriod`. Ainsi une ancre2027-01-01 portant ISO2026W53 sélectionne bien janvier2027. Une sélection mensuelle inchangée conserve l'objet et la date d'ancrage ; les demandes invalides ou hors1900–2200 ne modifient pas l'état. `moveCalendarMonth` applique les mois entiers et conserve les règles de clamp du jour déjà utilisées par la carte.

`monthGrid` calcule uniquement avec dates UTC et getters UTC, sans heure locale implicite. Les cellules hors mois portent `inMonth: false`. `projectCalendar` utilise les items du loader existant et l'intervalle mensuel de `periodRange`, sans nouveau filtrage de catégories ni appel réseau. Une course apparaît chaque jour inclus dans le mois, mais une seule fois dans `total` ; les marges ne présentent aucune donnée prétendument complète. Les objets API et témoins de scopes restent les mêmes références. En rayon, passer `{radius: true}` pour séparer les IDs de `selection.unlocatedIds` dans `candidates` ; ils ne figurent ni dans les cellules ni dans le total confirmé. Hors rayon, les non-localisées restent visibles normalement.

## Vérification locale

Préparer la base PostgreSQL jetable, le build React et Chromium selon le README. [Installation et tests](../../README.md#vérification-complète)

```powershell
pnpm --dir frontend test src/calendar.test.js src/Calendar.test.jsx src/App.test.jsx
.\.venv\Scripts\python.exe -m pytest tests/backend/test_calendar_e2e.py -q
```

Le helper `set_civil_date` fige uniquement la date civile avant les imports. Les animations, timers et horloges de performance restent natifs. Les parcours utilisent MapLibre avec des styles et un relief synthétiques interceptés. [Preuves d’intégration](integration.md)
