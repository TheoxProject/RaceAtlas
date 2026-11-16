# Lot8 — notifications internes et préparation V1

Branche `feature/operations-readiness`, checkout isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, base main vérifiée `c74086365df62bf1c71623e080bb1f649c9981f5`. [Intégration lot7](../lot-7/accounts-ui-integration.md) et CI main43745685937 vertes. Sources : AGENTS.md, AGENT_WORKFLOW.md, lot-0/delivery.md, data-decisions.md et contrats existants.

## Décisions et découpage

Décisions propriétaire : **Changements récents dans Ma saison**, compteur nouveautés et **Marquer comme lues**. Retirer une sauvegarde supprime les notifications de CE scope ; les autres scopes et comptes restent intacts. Réajout : nouvel abonnement, sans anciens messages. Les quatre statuts sauvegardés sont suivis ; Inscrit reste déclaratif. Pas email de changement de course ni nouvelle page de découverte. Absence source = to_verify, jamais annulation inventée.

| Tâche | Périmètre |
|---|---|
| OPS-N1 | Journal durable des changements scopés, abonnements/baselines, contraintes et projection privée ; mission bornée ci-dessous |
| OPS-N2 | Contrat/API privés, section Ma saison, compteur/lecture et concurrence UI ; cadrage après gate N1 |
| OPS-E | Erreurs, couverture et quotas simulés, workflows live désactivés |
| OPS-B | Sauvegarde/restauration synthétique sur NOUVELLE DB locale jetable |
| OPS-V | Matrice V1 complète et candidat avec limites externes ; pas publication finale |

Chaque feature cohérente passe revue indépendante du SHA final, CI integrated complète et main avant suite dépendante. N1 seul ne termine pas le lot8. Développement : ciblés et rapports courts, sans campagnes locales complètes répétées sur code inchangé.

## OPS-N1 — ownership et interfaces

Coordinator cadre/publie/gère les gates. Après transfert explicite, Developer est SEUL writer suivi : modèles/migration après a74, nouveaux modules de changements/notifications, raccords minimaux sync/planning et services internes nécessaires au verrou Account, tests PG/fixtures synthétiques, docs et checkpoint. Tester lit/teste le SHA figé sans modifier les sources. Pas UI/routes N2, refonte auth/ICS/catalogue, dépendance supplémentaire, ordonnanceur, fournisseur ou action réelle externe.

Créer RaceChange et cibles ScopeChange durables, baseline SavedEntry et PersonalNotification unique par compte/changement/scope. Conserver provenance et faits minimaux ; ignorer fraîcheur, replay et ordre sans delta. Les deltas de règles/labels/restrictions d'un scope concernent CE scope ; date/titre/commune/statut de race concernent ses scopes. Import initial sans ancien abonnement : pas d'alertes historiques. Transitions de présence réelles distinctes des changements attestés, fenêtres partielles sans faux manque. Événements/cibles atomiques avec leurs mutations/savepoints et finalisation de présence.

Projection privée batch bornée après commit source, sans fanout ni verrou Account dans sync. Pas suppression silencieuse à une limite technique : signaler s'il reste du travail. Index/contrat de batch et champs exacts sont des décisions techniques à documenter avant code. Lecture/accusé privés ne changent pas CatalogState/epoch. Aucun choix de rétention production ajouté.

## Intégrité et concurrence à prouver

- Ordre proposé : sync verrou import global puis guards scopes triés AVANT sourceDML/flush ; privé Account puis guard scope et baseline/save. Inspecter auto-flush et graphes effectifs avant adoption. Aucun chemin sync vers Account/SavedEntry ; pas de cycle inverse. Documenter point de linéarisation et délais bornés.
- FK composée Notification(account_id,scope_id) vers UQ SavedEntry existante (`uq_saved_entry_account_id`), ON DELETE CASCADE ; autre FK composée (change_id,scope_id) vers ScopeChange UQ correspondante. Deux FK simples ne garantissent pas ces couples. Accountcascade transitif, Scope/Saved RESTRICT conservé, ledger ICS INCHANGÉ et survivant à unsave.
- Accountfirst doit être respecté aussi par les services internes, pas supposé depuis HTTP. Projection SELECT sur abonnement/id/baseline COURANTS, jamais ancien candidat RAM rejoué après remove/readd (ABA). Une mise à jour de statut ou un no-op conserve baseline et incarnation ; réajout initialise baseline fraîche.
- Migration journal neuf vide : backfill0 des abonnements existants puis aucun default0 durable pour les nouveaux saves. Chaque création fournit maxsequence courant sous garde. Préserver données et contraintes existantes ; upgrade/downgrade uniquement sur DB locale jetable autorisée.

## Acceptation et tests ciblés N1

Imports identiques, replay, reorder et fraîcheur : aucun doublon/alerte parasite. Vrai report/règles/annulation sourcée : une cible exacte ; manque complet to_verify, partiel sans faux delta. Deux comptes/deux scopes, quatre statuts, changement/no-op/retrait/réajout ; suppression compte purge ses messages sans autrui. Rollback/savepoint ne laisse aucune donnée partielle. Mauvais couples FK refusés ; suppression parent ORM chargé/nonchargé et SQL bulk cohérente ; rollback retrait restaure abonnement et notifications.

Vrais commits/deux connexions avec barrières et délais bornés : save avant/après sync noncommittée, retrait/réajout/projection et suppression compte ; unicité/idempotence/absence de cycle réellement exercées. Vérifier source/epoch, SavedEntry et ledger ICS d'autrui intacts. Ne pas déclarer ces propriétés prouvées par une simple lecture du code.

Python/Node/PG/browsers existants ; _test Developer, _review Tester, schéma initial a74 à vérifier. Runtime.close avant Engines. Pas initdb/reseed aveugle ni modification copie personnelle main. Ciblés pendant développement ; gel SHA, revue N1 complète et integrated avant fusion. Handoff court : fichiers/SHA/commandes/comptes/temps/échecs/risques et choix de concurrence. Preuves antérieures réutilisées explicitement après diff nul, jamais ancien verdict copié.

Aucun achat, DNS, email réel, création service, DB distante, déploiement, collecte FFC live ou tag final sans autorisation distincte. Fixtures synthétiques seulement. Le premier déploiement privé reste prévu après lot8/candidat et soumis à autorisation.
