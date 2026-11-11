# Lot 6 — calendrier mensuel partagé

Base vérifiée : **8ce46a3fc1129a905d2e9f1fc8552e3cf4d0a56f**, après intégration PR8 et CI pushmain43092874749 verte. Branche `feature/monthly-calendar`, worktree isolé réutilisé après propreté et arrêt des agents/tests. Roadmap : `docs/lot-0/delivery.md` ; contrats catalogue/API existants inchangés par défaut.

## Décision propriétaire acquise

Ouvrir le calendrier depuis une carte Année ou Semaine sélectionne **le mois affiché**, issu de l'ancre civile partagée. Le retour Carte conserve **ce mois**, les autres filtres et la caméra. Altitude reste le mode initial ; un passage calendrier ne change pas le mode de terrain choisi. Ne pas reconsulter ces choix.

## Fonctions et acceptation

1. **CAL-01 sélection et dates** : un seul état de filtres/période et le même loader/API que la carte. Calendrier toujours mensuel, navigation précédente/suivante et année/mois réels, bornes1900–2200, passage décembre/janvier. Les contrôles n'affichent pas une grille mensuelle avec une requête annuelle/hebdomadaire. Les saisies inchangées préservent ancre/détails/requêtes ; vraies modifications appliquées sans état périmé.
2. Grille lundi–dimanche avec mois civils et années bissextiles corrects, indépendante du fuseau de l'appareil. Jours hors mois distincts et sans prétention de données complètes. Une course multijour apparaît chaque jour inclus dans le mois (`start_date <= day <= end_date`) mais une seule fois dans le total mensuel. Fixture2026-12-31..2027-01-02 visible31décembre puis1et2janvier, jamais perdue par son année de départ.
3. **CAL-02 interface** : vraie vue mensuelle responsive, bascule Carte/Calendrier fonctionnelle, pas page liste distincte ou bouton factice. Densité maîtrisée sans course inaccessible : chips/compteurs puis panneau des courses du jour et détails existants. Full labels accessibles même si tronqués. Clavier et contrôles nommés ; si ARIA grid utilisé, comportement clavier cohérent. Navy/orange,390px sans débordement.
4. Filtres communs recherche/départements/rayon/disciplines/types/catégoriesET/OU : mêmes IDs et témoins de scope pour une même sélection. Hors rayon les non-localisées apparaissent ; en rayon elles restent candidates à part, consultables mais exclues des cellules/totaux confirmés. Statuts/source/fraîcheur/règles/restrictions et incertitudes préservés, aucune éligibilité personnelle ou inscription FFC inventée. Choisir un centre depuis le calendrier doit réellement fonctionner via l'accès carte/formulaire, pas une carte invisible.
5. Garder la caméra et l'instance MapLibre à travers les changements de vue/mois/filtres. Tester depuis un zoom non initial et Summit : centre borné uniquement pour l'arrondi1e-9degré, autres champs conservés. Attributions visibles chaque fois que la carte est visible. Aucun déplacement de caméra pour une sélection temporelle ; ni remontage silencieux ni retour aux valeurs initiales.
6. Loading/vide/erreur/retry, métadonnées, pages multiples et reprise409 gardent le comportement partagé ; une ancienne réponse ne remplace pas la sélection actuelle. Détails et fermeture/retour utilisables dans les deux vues. Aucun compte/planning/ICS anticipé ou parcours technique affiché aux utilisateurs.
7. **CAL-03 preuves intégrées** : tests ciblés des calculs/date/clipping/IDs et App parité/bascule ; vrais parcours React compilé→Flask→PostgreSQL pour multi-jour/frontièreannée, mêmes filtresET/OU et rayon/non-localisées, caméra/terrain, erreurs et mobile. Captures desktop/mobile examinées ; moteur réel avec style/DEM interceptés, aucun nouveau smoke réseau FFC/fournisseurs.
8. **CAL-04 livraison** : commits/pushs cohérents, Draft tôt, surveillance CI après chaque push ; revues ciblées aux jalons importants puis revue complète du SHA final. Lint/contrats/build/régressions appropriés et CI finale verte, APPROVE indépendant exact, merge confirmé et CI main verte. Ensuite rapport de pré-déploiement concret pour décision propriétaire, fondé sur la préparation PR8, avec limites gratuites revérifiées et tests encore requis. Ne rien activer.

## Ownership et limites

Coordinator possède mission/checkpoint/intégration et rapport pré-déploiement. Developer recevra explicitement les fichiers frontend, tests et docs du lot ; un seul writer dans ce worktree. Tester ne modifie pas les sources. Aucun changement API/modèle/migration/import/sécurité/hosting sans nécessité signalée et scope explicite.

Réutiliser caches/venv/PG du checkpoint ; bases `_test` et `_review` distinctes. Tests natifs ciblés, pas nouvelle campagne complète inchangée après chaque petit commit. La CI complète et le verdict final restent obligatoires. Aucun déploiement, service, dépense, remoteDB, email réel, collecte FFC ou tag final autorisé.
