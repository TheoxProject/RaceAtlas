# Livraison intégrée RaceAtlas V1.0

Les lots 0–8 livrent une seule application progressivement utilisable. Un lot n'est pas terminé au seul passage de ses tests unitaires. Chaque lot fournit contrats, critères observables, tests d'intégration avec les lots précédents et preuves sur le SHA exact. Une limite non testée est indiquée, jamais déclarée PASS.

| Lot / branche proposée | Objectif, dépendances, composants | Gate d'intégration et risques prioritaires |
|---|---|---|
| 0 `feature/source-contracts` | Audit, identité, contrats/fixtures/tests ; pas d'application | Cohérence des contrats et scénarios négatifs ; inconnues FFC explicites |
| 1 `feature/core-foundation` | React/Vite + Flask/SQLAlchemy, migrations, CI ; dépend 0 | Flux minimal React→Flask→PostgreSQL jetable ; contraintes réelles PostgreSQL, lint/build ; pas Neon live |
| 2 `feature/ffc-adapter` | Adaptateur isolé ; dépend 0–1 | Fixtures vers modèle, types/catégories/restrictions ; aucune déduction du slug ; échecs HTML explicites |
| 3 `feature/auditable-sync` | Import idempotent et communes ; dépend 2 | Deux imports identiques sans doublons ; reprise, fenêtres effectives, erreur partielle et cache ; pas collecte large sans droits |
| 4 `feature/catalog-filters` | API et service partagé carte/calendrier ; dépend 1–3 | Scénarios de ce lot exécutés via Flask+PostgreSQL ; ET/OU exact, rayon et pagination ; zéro faux positif de listes séparées |
| 5 `feature/map-experience` | Carte Altitude/Summit, caméra, détails ; dépend 4 | Fixtures puis API réelle ; clustering, non-localisées, semaines ISO, mobile, DEM en échec ; attributions |
| 6 `feature/monthly-calendar` | Calendrier mensuel unique ; dépend 4–5 | Parité carte/calendrier, multijour/année, mêmes filtres ; pas de page de liste indépendante |
| 7 `feature/accounts-and-planning` | Comptes, sessions, favoris par scope, ICS ; dépend 1/4/6, expéditeur validé | Deux utilisateurs isolés, reset/révocation/suppression, multiappareil, statuts ; Inscrit déclaratif ; ICS stable |
| 8 `feature/operations-readiness` | Notifications internes, erreurs, couverture, exploitation ; dépend 3/7 | Changement réel → notification unique ; pas d'email course ; quotas simulés, sauvegarde/restauration ; workflows désactivés avant autorisation |

Protocole : coordinateur définit périmètre, fichiers, contrats, critères, risques et tests ; developer livre commits cohérents et cesse les éditions ; tester lit et teste le SHA figé ; corrections puis nouvelle revue (trois cycles max) ; coordinateur prépare PR ; propriétaire décide merge. Merge commit privilégié pour les lots importants, squash possible pour documentation/correctifs mineurs. Un changement du SHA invalide la précédente approbation technique. Tester également le résultat d'intégration si la base a changé.

## Phase finale V1 après lot 8

- Matrice de toutes les exigences du cahier des charges, avec PASS/FAIL/BLOCKED et preuve.
- Tests automatisés, bout en bout et responsive ordinateur/mobile ; navigation publique et compte.
- Flux complets React→Flask→PostgreSQL, cohérence carte/calendrier, multijour et semaines ISO.
- Sécurité : autorisations interutilisateurs, CSRF, sessions, reset, secrets, suppression, données/logs.
- Performances mesurées sur corpus identifié ; rendu terrain et mémoire mobile ; pagination et reprise après veille.
- Import/synchronisation : idempotence, dates effectives, alias d'identité, changements, pertes temporaires et notification unique.
- Déploiement de test sur Render Free/Neon Free uniquement après approbation du propriétaire ; accès de staging réellement protégé ; pas simple URL non indexée.
- Vérification des droits FFC, fournisseurs de carte, email, quotas et zéro facturation ; tout blocage à l'exploitation publique explicitement listé.

Préparer ensuite `v1.0.0-rc.1` avec rapport complet : SHA, environnement, commandes, résultats, captures nécessaires, risques, conditions de reprise et blocages. Corriger les régressions et refaire les parcours affectés. Soumettre la version finale au propriétaire. Le tag `v1.0.0`, la mise en production, les migrations distantes et l'activation de collecte exigent son autorisation explicite. L'acceptation du lot 0 n'autorise aucune de ces opérations.
