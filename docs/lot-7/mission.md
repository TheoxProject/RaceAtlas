# Lot 7 — comptes et planification par scope

Décision fournisseur13nov : **Resend Free**, SDK Python officiel et `EmailService` avec providers Resend/Development ; confirmation24h et reset30min. Domaine/From souhaités non acquis/vérifiés, aucun envoi réel. [Mission Resend et attribution B1](resend-mission.md) ; ACC-02A approuvé au jalon9dfd, PR12 reste Draft.

Base vérifiée : **51856c9940a2b0e16c9f05d61a9f1726ae8701d9**, après [PRE-01](../readiness/predeployment-integration.md), lots 0–6 intégrés et CI main verte. Branche isolée `feature/accounts-and-planning`. Les contrats publics existants restent stables ; tout nouveau contrat est additif et accompagné de son comportement réel.

## Décisions et limite d'activation

Le propriétaire a choisi **email et mot de passe, récupération par email**, et indique **aucun domaine ni expéditeur disponible**. Premier déploiement privé prévu **après le lot 8 / candidat V1** ; aucune création/service/DNS/dépense/mutation distante/envoi réel autorisé. Développer et tester avec transport local simulé est indépendant. Ne pas présenter cette simulation comme délivrabilité réelle ou prérequis expéditeur validé ; la clôture complète du lot et l'activation des emails devront exposer cette dépendance.

Décisions complémentaires explicites : **email+mot de passe puis confirmation par email avant connexion** ; export ICS par défaut **Prévues et Inscrit**. ACC-01 intégré : [preuves](foundation-integration.md). Suite depuis main5e2c84a : [mission auth](auth-mission.md). Aucun choix sur ces points ne reste en attente.

## Découpage progressif

| ID | Fonction et périmètre | Gate |
|---|---|---|
| ACC-00 | Mission, dépendances, Draft et choix propriétaire | Base/main et checkpoint vérifiés |
| ACC-01 | Identité de compte et sauvegardes privées par scope, migration et service interne | Deux utilisateurs isolés, contraintes PG, idempotence/concurrence et favoris conservés pendant sync |
| ACC-02 | Identifiants email/mot de passe, sessions serveur, CSRF, récupération/révocation/suppression, transport local | Tests de sécurité négatifs réels, aucun contournement de production ou email réel implicite |
| PLAN-01 | API privée, statuts, export ICS stable | Autorisation issue de session validée, scopes cohérents, dates civiles/fin exclusive et UID stable |
| ACC-UI | Parcours comptes/planning intégrés à carte/calendrier/détails | React compilé→Flask→PG, mobile/clavier, aucune fausse action ou page liste de découverte |
| ACC-FINAL | Acceptation complète exacte, CI, expéditeur et intégration | Toute dépendance non validée déclarée ; pas de lot terminé par simulation seule |

ACC-01 est la première tâche bornée et la première PR est limitée à cette fondation indépendante. Une éventuelle intégration de cette fonctionnalité ne termine pas le lot 7 : authentification, UI, ICS, expéditeur et acceptation globale restent requis. Les autres tâches recevront une attribution précise après ce jalon, sans lancer tout le lot à la fois. Revues ciblées aux fonctionnalités importantes, puis acceptation complète au SHA final du lot. CI après chaque push et avant fusion ; pas de répétition de la suite backend complète locale inchangée à chaque commit.

## ACC-01 — modèle et service interne, sans parcours d'authentification factice

1. Identité de compte opaque et adresse email normalisée/unique, privée. Ce jalon ne rend pas un utilisateur authentifié et n'expose aucun login/register/reset temporaire. Aucun mot de passe ou token en clair/log ; les credentials et leurs primitives sécurisées seront implémentés dans ACC-02. Ne pas créer de bypass HTTP `user_id`, header utilisateur ou faux compte connecté pour tester.
2. `saved_entry` unique pour **utilisateur + entry_scope**, statut strict `interested`, `planned`, `registered`, `completed`, dates UTC de création/modification. `registered` reste une déclaration utilisateur, jamais une preuve FFC. Aucune éligibilité personnelle calculée ou restriction source modifiée.
3. Stocker le FK scope et dériver la course par sa relation ; éviter un `race_id` redondant incohérent. La suppression d'un scope ne doit ni supprimer silencieusement le favori ni le rendre sans cible : FK restrictif. La future suppression volontaire d'un compte peut effacer ses données privées, sans toucher les courses/scopes.
4. Service interne CRUD/liste scoppé par acteur serveur ; aucun acteur issu d'un paramètre utilisateur public. Interface ACC-01 : **Account persistant attaché à la même Session ORM**, que le futur Auth devra charger après validation serveur ; pas d'instance détachée ou de simple ID acteur reçu d'une requête. Ce contrat interne n'est pas une authentification en lui-même. Tests directs du service autorisés tant que les routes d'authentification ne sont pas livrées. Changement/lecture/suppression d'une sauvegarde d'autrui : réponse domaine générique introuvable, aucune fuite d'existence. Statuts indépendants pour deux utilisateurs ou deux scopes d'une même course.
5. Création répétée/upsert ne duplique pas ; un vrai changement de statut conserve ID/cible, un no-op conserve horodatage. Révision privée positive initiale **1**, incrémentée uniquement sur vrai changement de statut ; no-op conserve aussi cette révision. Ce compteur prépare la distinction de modification pour la suite, sans commencer ICS. Concurrence arbitrée par les contraintes PG. Les écritures privées n'invalident pas la version publique du catalogue.
6. Migrations Alembic upgrade/check/downgrade/upgrade/check uniquement en DB jetable locale, modèles et contraintes concordants. Public catalogue/API/fixtures et ancien historique restent compatibles. Pas de dépendance ou refonte backend sans nécessité démontrée.

## Intégration source et identité à protéger

Lecture indépendante acquise sur main7b733d86 : `sync/service.py` conserve les faits identiques, sinon exige attestation puis `project_race` et `session.merge`. Les bindings couvrent exactement les anciens IDs et ne déplacent pas les règles entre scopes : ajout/retrait/split/fusion sont actuellement refusés. Une ambiguïté produit l'audit `review/needs_review` et conserve le graphe ; elle ne change pas automatiquement `EntryScope.identity_status`. L'absence contrôlée ne supprime pas la course et peut seulement donner `to_verify` sur un run réussi. Ne pas réinventer cette politique ni réaffecter un favori par rang/libellé.

ACC-01 doit réellement vérifier sur PostgreSQL : renommage/report et réorganisation attestée avec replay gardent favori/ID/statut ; suppression/split/ambiguïté refusés sans perte ou transfert, audit conservé ; absence→`to_verify` garde la cible ; suppression effective d'un scope protégé est refusée ; suppression d'un compte n'affecte pas l'autre. Réutiliser les fixtures/protocoles de sync existants, données synthétiques uniquement.

## Ownership et suite

Coordinator possède mission, tâches, PR, interface entre auth/service/planning et gates. Developer sera seul writer sur les fichiers explicitement attribués ; Tester ne modifie pas le code qu'il vérifie. Caches Python/Node/PG du checkpoint, bases `_test` et `_review` distinctes. Pas d'initdb/reseed aveugle ou processus concurrent.

ACC-02 précisera hash de mot de passe et limites RAM, tokens aléatoires/vérificateurs hashés, cookies sûrs/CSRF, origine canonique des liens, anti-énumération/abus et cycle de révocation/suppression. Les sources primaires seront datées ; aucun « conforme » général sans preuve. PLAN-01 conservera dates civiles et portée de liste ; le choix fonctionnel des statuts exportés devra être clarifié avant le code dépendant s'il reste ambigu. Les notifications internes et sauvegardes complètes restent au lot 8 ; aucune activation distante ou finale anticipée.
