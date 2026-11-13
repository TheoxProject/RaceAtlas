# ACC-02 — authentification email/mot de passe

Base vérifiée **5e2c84a99f7795da9cc2e14118549873bf4a42be**, après [ACC-01 intégré](foundation-integration.md) et CI main verte. Branche isolée `feature/account-authentication`, nouvelle Draft PR. Le coordinateur attribue un seul jalon borné à la fois ; le Developer est seul writer, puis gèle le SHA pour Tester indépendant.

## Décisions produit et activation

Le propriétaire choisit **email et mot de passe saisis à l'inscription, confirmation par email obligatoire avant connexion** ; récupération par email. Export ICS par défaut **Prévues et Inscrit**, à implémenter dans PLAN-01. Aucun domaine/expéditeur validé ; premier déploiement privé après lot8/candidat V1. Aucun service, DNS, compte externe, email réel, dépense ou mutation distante autorisé par cette mission.

Les tests locaux utilisent un transport explicitement simulé. Il ne devient jamais un fallback en production et ne prouve ni délivrabilité ni prérequis expéditeur. Toute activation doit échouer fermée si ses préconditions manquent. Ne pas inventer une route/header/user_id ou un mode de production contournant confirmation/authentification. Les comptes sont optionnels et la découverte publique reste disponible.

## Jalons de la PR

| ID | Périmètre | Gate observable |
|---|---|---|
| ACC-02A | Hash, credentials vérifiés et sessions serveur internes, migration | Multiappareil, expiry/révocation, deux connexions concurrentes, acteur fiable pour planning |
| ACC-02B | Inscription/confirmation et récupération à usage unique, transport local | Pas de connexion avant preuve email ; rejeu/expiration/concurrence ; aucun secret exposé |
| ACC-02C | Flask login/logout/contexte, cookies/CSRF/limites d'abus, suppression | Vrais appels HTTP→PG, négatifs interutilisateurs, fixation/CSRF/reset/révocation/suppression |
| ACC-02-FINAL | Acceptation complète du périmètre auth local au SHA final | Tester exact et CI ; dépendance expéditeur déclarée, pas lot7 terminé |

Les API planning/ICS et composants React comptes arrivent ensuite. Une approbation intermédiaire ne vaut pas approbation d'un autre SHA ou de cette PR complète. Après chaque push : CI du head courant ; revue ciblée aux jalons importants, pas suite backend/browser complète locale après chaque petit changement.

## Première attribution ACC-02A

Fichiers autorisés : nouveaux modules `raceatlas/auth/`, ajouts strictement privés dans `raceatlas/models.py`, nouvelle migration Alembic après c40a7162b901, tests backend auth nouveaux et ajustement minimal de nettoyage jetable si requis, `requirements.txt`/`constraints.txt` pour Argon2 seulement, docs de ce jalon et checkpoint. Ne pas modifier App/serve/public API, catalogue/sync/FFC, frontend, fixtures/contrats publics, CI ou configuration distante. Proposer au coordinateur tout élargissement nécessaire avant édition.

1. Argon2id maintenu et paramètres explicites selon [décision technique](auth-security-decisions.md). Stocker PHC salé uniquement, jamais password/token en clair dans DB/log/exception/repr. Aucun hash faible pour « accélérer » les tests d'acceptation. Mots de passe distincts du traitement de l'email : pas strip/lower/troncature. Validation cohérente pour création/changement ; 15–128 caractères Unicode valides, espaces autorisés, limite UTF-8 documentée et erreurs génériques. Pas prétention de conformité générale.
2. Credentials privés uniques FK Account/CASCADE, avec preuve email vérifiée requise. Un Account ACC-01 seul ne doit pas pouvoir se connecter. Le futur flux de confirmation crée les credentials ; pour ce jalon interne, les fixtures de tests peuvent préparer cette donnée directement. Ne pas ajouter de commande de provisioning, formulaire ou route publique temporaire.
3. Sessions opaques générées par CSPRNG256bits, vérificateurs hashés en DB, sessions distinctes pour appareils distincts ; aucun bearer JWT ou ID acteur choisi par client. Le contexte validé charge un Account de la même Session ORM pour planning. Bornes sur tokens soumis et dates serveur UTC ; données ORM préchargées ne doivent pas contourner une révocation récente.
4. Définir et documenter expiration absolue et idle côté serveur : valeur initiale technique 7jours absolus/24heures d'inactivité, sans extension au-delà de l'absolue. La future couche HTTP contrôlera cookies et CSRF, pas ce premier module interne.
5. Connexion par email/password, validation de session, déconnexion une session/toutes, changement du mot de passe avec preuve actuelle et révocation de toutes sessions. Sérialiser émission et révocation/changement/suppression : une vérification d'ancien secret ne peut pas créer une nouvelle session après révocation/reset. Utiliser contraintes/verrous/versions explicites, prouver avec deux vraies connexions PG et barrières/délais bornés. Aucun compteur catalogue modifié.
6. Préserver deux utilisateurs et leurs SavedEntry ; suppression Account cascade uniquement ses données privées. Erreurs de domaine génériques, pas broad catch cachant une panne SQL. Contrat transactionnel caller-owned explicite et test rollback. KDF borné en concurrence ; mesurer localement sans prétendre budget Render mesuré.

Acceptance ciblée : vrai hash salé/nonplaintext et vérification positive/négative/Unicode/bornes ; refus credentials absents/nonvérifiés ; tokens indépendants, stockage hashé, expiry/idle/no-resurrection ; révocation isolée/globale/changement et courses concurrentes ; reprise en nouvelle Session, acteur validé réellement utilisé dans planning et isolation ; contraintes/FK/migration réelle et régression publique pertinente. Caches existants et `_test` Developer / `_review` Tester distincts avec opt-in ; vérifier processus/PG, pas initdb/reseed aveugle. L'environnement de recherche ignoré n'est pas un environnement de production ou de tests du projet.

Handoff : fichiers/interfaces, exact SHA, commandes/résultats, tests non exécutés et preuves inchangées réutilisées, risques. Mettre à jour checkpoint cohérent avant commit/push, puis arrêter toute édition au gel. Pas de fusion de ce seul jalon en affirmant ACC-02 ou lot7 complet.

## Attentes déjà fixées pour les jalons suivants

Confirmation liée à la demande d'inscription et au hash de son mot de passe, pas au dernier hash arbitrairement remplacé ; ne jamais écraser les credentials d'un compte confirmé par réinscription. Possession mailbox prouvée avant usage. Tokens email CSPRNG, vérificateur hashé, expiration/usage unique et consommation atomique ; confirmation/reset n'ouvrent pas implicitement une session. GET et scanners de liens ne consomment rien.

Origine canonique configurée pour liens, indépendante Host/Forwarded ; tokens hors query serveur, logs, referer, erreurs et réponses API. Réponses externes uniformes et limites d'abus bornées persistantes, pas seulement RAM ou IP fournie par header client. Les garanties temporelles/transport doivent être mesurées avec limites déclarées, jamais affirmées sur un mock seul.

HTTP : cookies Secure/HttpOnly/SameSite/host-only, protection CSRF préauth et auth, pas CORS permissif, mutations JSON bornées/méthodes strictes, no-store privé, logout/reset/delete révoquent réellement. Réauthentification avant opérations sensibles et suppression complète sans toucher source/autrui. Préserver la protection Basic de preview et le preflight existants. Les missions précises B/C seront attribuées après revue A, sans engager automatiquement tous les fichiers maintenant.
