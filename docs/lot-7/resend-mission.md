# ACC-02B — décision Resend et attribution progressive

Décision explicite du propriétaire reçue le **13 novembre 2026** : **Resend Free définitivement retenu**, SDK Python officiel, `EmailService` central avec `ResendEmailProvider` et `DevelopmentEmailProvider`. Cette mission complète [auth-mission.md](auth-mission.md), sans recommencer ACC-01 ni ACC-02A.

ACC-02A approuvé au SHA **9dfd8087820608f613e5915a1839800357e1ffb9** ; [CI43389431747](https://github.com/TheoxProject/RaceAtlas/actions/runs/43389431747) SUCCESS **521 backend220,54s / 67 frontend**, source vérifiée avant/après. Tester ciblé : 132 PASS60,64s +16 contrôles PASS18,10s, Ruff49/contrats26/pipcheck ; rapport indépendant publié dans PR12. Cela ne termine pas la PR ou le lot7. Les preuves de A peuvent être réutilisées pour ses chemins inchangés, avec nouvelle revue du candidat final.

## Configuration et limites autorisées

```dotenv
APP_BASE_URL=
EMAIL_PROVIDER=development
RESEND_API_KEY=
EMAIL_FROM=
```

Dernière précision propriétaire : le club possède `ucthonon.fr`, géré via Webador. Sous-domaine cible **raceatlas.ucthonon.fr**, réservé aux emails, From cible **RaceAtlas <notifications@raceatlas.ucthonon.fr>**. Rien n'est encore vérifié dans Resend ; ces valeurs ne constituent pas une activation. APP_BASE_URL reste l'URL réelle du service Render à renseigner, indépendante du domaine email. Clé/From/garde vérifié restent vides dans la configuration locale effective ; la configuration production cible sera documentée uniquement pour activation ultérieure autorisée. Ne modifier ni supprimer les DNS existants du domaine principal ou des emails du club. Le guide Webador doit vérifier le nom complet résultant et éviter un suffixe `ucthonon.fr` dupliqué, avec les seules valeurs réellement fournies par Resend.

Tous les tests automatisés restent simulés, y compris le transport du SDK. Aucune création de compte externe, achat de domaine, DNS, envoi réel, requête API avec clé, déploiement ou mutation distante autorisé. Les essais `resend.dev` ne sont pas un moyen d'envoyer aux utilisateurs ; les documenter seulement dans leurs limites officielles, sans les exécuter. Pas de clé dans Git/frontend/logs ; pas de fallback silencieux du réseau vers le simulateur en production.

## B1 — première attribution : service, providers et modèles, sans parcours métier

Developer seul writer après attribution explicite ; autres agents read-only. Fichiers autorisés : nouveau module `raceatlas/email/` (ou équivalent unique clairement nommé), tests backend correspondants, `requirements.txt`/`constraints.txt` pour le SDK et ses dépendances nécessaires, `.env.example`, README, docs lot7/guide Resend/checkpoint. Pas de modèle/migration, route/App/serve, frontend, sync/FFC/catalogue, CI ou ops à ce premier sous-jalon. Aucun flux B2/C anticipé. Proposer au coordinateur un élargissement nécessaire avant modification.

1. `EmailService` possède génération des liens et rendu français, puis délègue au provider. Aucun import/appel Resend futur dans les routes métier. Les messages en mémoire peuvent être inspectés par les tests, jamais par un endpoint ou un log. Types/repr/erreurs ne doivent pas réfléchir email, clé, token, HTML ou corps SDK.
2. `DevelopmentEmailProvider` explicite pour local/test, sans socket ou credential requis, stockage de messages borné. Aucune prétention de délivrance. Si un contexte production tente d'activer des comptes avec un provider simulé, échouer fermé ; ne pas casser la découverte publique qui ne l'instancie pas à ce jalon.
3. `ResendEmailProvider` utilise réellement **`resend.Emails.send` du SDK officiel épinglé**, pas un appel HTTP direct métier. Tester la pile SDK réelle avec transport injecté entièrement simulé. SDK2.53.2/Python>=3.10 qualifié en recherche ; pin et pipcheck projet/Linux à exécuter, sans installer extra async inutile à Flask sync.
4. Le SDK possède des globals APIkey/URL/client. Prévenir mélange entre instances/apps et restauration incomplète sur exception ; sérialisation bornée et tests concurrents. Ne pas hériter d'un `RESEND_API_URL` permettant de transmettre une clé ailleurs. Via l'interface HTTPClient supportée, imposer HTTPS vers `api.resend.com/emails`, TLS vérifié, pas de redirection, temps connect/read et taille réponse bornés. Ne pas présenter les timeouts connect/read comme un SLA de durée totale.
5. Absence/mauvaise configuration Resend doit être refusée, jamais remplacée par `resend.dev` ou un From supposé. Un garde explicite de domaine vérifié peut compléter les quatre variables (par exemple `EMAIL_VERIFIED_DOMAIN`, vide par défaut), sans faire passer cette attestation opérateur pour une vérification DNS/API réellement exécutée. Documenter la preuve à fournir avant activation et la restriction du domaine de la clé `sending_access`. Aucun accès réseau pour vérifier un domaine dans les tests ou le preflight.
6. Masquer exceptions réseau/SDK, y compris messages natifs contenant des secrets ; succès API signifie acceptation, pas réception. Tester timeout, erreur réseau,429/quota,403/domain/key,5xx, réponse invalide et trop grande, absence de retry incontrôlé ; utiliser un identifiant d'idempotence opaque si retry d'une même opération. Aucun changement de plan, dépense ou appel de quota réel.
7. Confirmation : objet **« Confirmez votre adresse e-mail — RaceAtlas »**, bienvenue brève, bouton **« Confirmer mon adresse e-mail »**, expiration **24 heures**, ignorer une demande non initiée. Reset : objet **« Réinitialisez votre mot de passe — RaceAtlas »**, bouton **« Réinitialiser mon mot de passe »**, expiration **30 minutes**, ignorer si inconnue. Chaque message fournit HTML et texte brut, navy#111F37/orange#F97316, sans ressource distante/tracking. Ne jamais transmettre un mot de passe.
8. Construire liens depuis **APP_BASE_URL exclusivement**, pas Host/Forwarded ou domaine de l'expéditeur. Canonicaliser/valider schéma/origine sans userinfo/query/fragment, HTTPS en production, HTTP loopback local/test seulement. Utiliser un fragment de l'URL racine pour le token afin que Flask et Referer ne le reçoivent pas ; figer les deux formats pour la future UI, pas une page qui n'existe pas côté serveur. Escape HTML et borner entrées ; aucun GET qui consomme un token.
9. Guide propriétaire concret : compte Resend Free, clé envoi uniquement et domaine restreint, propriété de domaine, valeurs SPF/DKIM fournies par Resend, DMARC recommandé, statut vérifié avant From, tracking désactivé pour tokens, secrets dans Render, URL du site indépendante, test futur d'envoi/réception/liens/quota/erreurs. Les valeurs DNS ne sont pas inventées ; aucune action de ce guide exécutée. Présenter Free100/jourUTC et3000/mois comme limites vérifiées dans les docs actuelles, pas quota d'un compte inspecté.

Gate B1 : tests ciblés significatifs des deux modèles/providers/config/URL/secrets/SDK réel hors réseau/concurrence et non-régression auth pertinente ; pipcheck/lint/format/contrats/build si concerné. Vérification visuelle locale des deux HTML avec données synthétiques, sans publier de contenu sensible. Pas de campagne backend/browser complète locale inchangée. Commit/push cohérent, handoff exact avec commandes/résultats/limites ; gel et revue indépendante ciblée avant B2.

## B2 — exigé ensuite, non attribué par B1

Compte initialement non vérifié, mot de passe déjà choisi, hash Argon2 seulement ; challenge de confirmation aléatoire, hash seul en PostgreSQL, usage unique **24h**, renvoi et limites persistantes. Confirmation liée au mot de passe de sa demande, sans écraser un compte vérifié ; interdiction des fonctions personnelles et login avant vérification. Préserver l'ordre Accountlock d'A, relecture fraîche et transactions du caller ; pas d'I/O email sous verrou, pas de lien/cookie publié avant commit.

Reset distinct, hash seul, **30min**, consommation atomique, aucun password par email, révocation de toutes sessions précédentes et pas d'auto-login. Réponses génériques non-énumérantes même si le fournisseur échoue, pas d'activation ou de changement de secret à la seule demande. Exercer rejeu/expiry/renvoi/concurrence/isolation/erreurs/rate limits. La couche HTTP/CSRF et UI restent aux jalons correspondants ; un service non exposé n'est pas une inscription utilisable.

## Sources primaires lues le13novembre2026

- [SDK Python officiel](https://resend.com/docs/send-with-python), [code SDK](https://github.com/resend/resend-python), [PyPI](https://pypi.org/project/resend/).
- [Clés API et permissions](https://resend.com/docs/api-reference/api-keys/create-api-key), [gestion des clés](https://resend.com/docs/dashboard/api-keys/introduction).
- [Domaines vérifiés](https://resend.com/docs/dashboard/domains/introduction), [SPF/DKIM](https://resend.com/docs/add-a-domain), [DMARC](https://resend.com/docs/dashboard/domains/dmarc).
- [Free et quotas](https://resend.com/docs/knowledge-base/account-quotas-and-limits), [prix](https://resend.com/pricing), [limites resend.dev](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain).

L'activation/délivrance réelle et les droits/prérequis de domaine restent **BLOCKED** jusqu'aux actions et autorisations du propriétaire. Les tests simulés valident l'intégration de code demandée, pas cette exploitation. Premier déploiement privé après lot8/candidatV1 inchangé.

## Reprise B1 et preuves

WIP sauvegardé au SHA **1464dfa2db250e1816e2f7120fde371479575338**, CI43402452005 SUCCESS589backend227,04s/67frontend ; preuve distincte du premier run tronqué dont le résultat reste inconnu. Reprise du même Developer le13novembre : objet reset corrigé et testé par attendu littéral, email **68PASS2,02s**, auth pertinente **64PASS20,66s**, quatre rendus HTML desktop/mobile synthétiques inspectés. [Handoff B1](email-handoff.md), [guide Resend/Webador](resend-guide.md) et checkpoint détaillent les commandes et limites. Nouvelle CI/revue du SHA publié requises ; aucune approbation transférée du WIP ou de A.
