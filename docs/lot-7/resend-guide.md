# Email RaceAtlas — préparation Resend Free et Webador

Guide préparatoire B1, sources primaires consultées le **13 novembre 2026**. Aucune des actions de console, DNS, envoi ou déploiement ci-dessous n'a été exécutée. Elles requièrent l'autorisation du propriétaire. Le module n'est pas encore appelé par l'application publique ; inscription, consommation des liens et interface restent aux jalons B2/C.

## Domaine email et adresse du site

Le club possède `ucthonon.fr`, géré via Webador. La cible retenue est **`raceatlas.ucthonon.fr` uniquement pour les emails**, avec **`RaceAtlas <notifications@raceatlas.ucthonon.fr>`** comme From futur. Le sous-domaine n'est pas encore vérifié dans Resend. Il n'héberge aucun site et ne nécessite pas de déplacer le site ou les emails existants du club.

`APP_BASE_URL` sera l'URL **réelle** du service Render, à renseigner après autorisation et création du service. Aucune adresse Render effective n'est présumée. Cette URL est indépendante du domaine d'envoi ; les liens ne sont jamais construits depuis `EMAIL_FROM`, Host ou Forwarded.

## Procédure future, sans toucher aux services du club

1. Après accord, ouvrir un compte **Resend Free** détenu par le club/propriétaire, sécuriser ses accès et confirmer les limites affichées. Ne pas activer de plan payant ou de dépassement facturable.
2. Ajouter uniquement le domaine d'envoi `raceatlas.ucthonon.fr`. Choisir **Ireland (`eu-west-1`)** si toujours disponible dans le compte Free. Les régions d'envoi sont proposées sur Free ; la région détermine le routage/envoi, **pas une résidence européenne des données** : Resend indique stockage des contenus/logs/métadonnées aux États-Unis, rétention Free de 30 jours. Examiner les engagements contractuels/DPA et la confidentialité avant toute donnée réelle ; ce guide ne conclut pas à une conformité juridique.
3. Relever dans la console les enregistrements **réellement fournis** pour SPF et DKIM, leurs types, hôtes, valeurs et priorités. Aucun enregistrement de ce guide n'est une valeur à appliquer. Garder le receiving désactivé : usage strictement expédition.
4. Dans Webador : **Mon abonnement → Gérer domaines → Modifier DNS → Ajouter enregistrement**. Avant toute modification, inventorier les enregistrements existants. **Ne modifier ni supprimer aucun DNS existant du club, aucun A/CNAME/MX racine ; ne pas restaurer les paramètres DNS par défaut.** Si une entrée requise entre en conflit, arrêter et consulter le propriétaire.
5. Si Resend affiche un nom court relatif à `raceatlas.ucthonon.fr`, reconstituer d’abord son FQDN complet, sans perdre le segment `raceatlas`. Vérifier si le champ Hôte Webador ajoute automatiquement `.ucthonon.fr`. Dans ce cas retirer **une seule occurrence finale** de `.ucthonon.fr` du nom complet fourni par Resend. Exemple de format seulement : `nom.raceatlas.ucthonon.fr` devient `nom.raceatlas`. Vérifier le FQDN résultant complet et le comparer exactement à la console avant de sauvegarder : jamais `…ucthonon.fr.ucthonon.fr`. Ne pas appliquer les étapes `www`/site d'autres guides Webador.
6. Attendre les vérifications SPF/DKIM et le statut vérifié du sous-domaine dans Resend. DMARC est recommandé : déterminer une politique adaptée avec le responsable du domaine sans écraser celle du club. Ne pas inventer une adresse de rapports ou une politique sans accord.
7. Désactiver **open tracking et click tracking** du domaine avant toute utilisation de liens sensibles. Vérifier ce réglage dans la console. Les modèles ne contiennent aucun pixel ou ressource distante ; cela ne suffit pas à empêcher une réécriture opérée par le fournisseur.
8. Créer une clé **`sending_access` restreinte à ce domaine** ; aucun accès global de gestion n'est requis. La conserver dans le gestionnaire de secrets puis dans les variables serveur autorisées, jamais Git, frontend, log, capture ou ticket. L'application ne sonde pas l'API de gestion des domaines et ne possède aucune preuve DNS automatique.

Références : [domaines et SPF/DKIM](https://resend.com/docs/add-a-domain), [configuration des domaines et tracking](https://resend.com/docs/dashboard/domains/introduction), [DMARC](https://resend.com/docs/dashboard/domains/dmarc), [permissions de clé](https://resend.com/docs/api-reference/api-keys/create-api-key), [régions](https://resend.com/docs/dashboard/domains/regions), [régions sur Free](https://resend.com/changelog/multi-region-for-everyone), [traitement des données](https://resend.com/security/gdpr), [DNS Webador](https://help.webador.com/hc/fr/articles/29426730759441-Puis-je-changer-les-DNS), [format relatif des hôtes Webador](https://help.webador.com/hc/fr/articles/45366721420817-Comment-connecter-un-domaine-Webador-%C3%A0-Systeme-io).

## Variables et garde d'activation

Dans `.env.example`, `EMAIL_PROVIDER=development`, les secrets/From/domaine vérifié restent vides et les deux attestations restent `false`. En local/test, renseigner explicitement une URL loopback, par exemple `http://127.0.0.1:5000`. Le simulateur conserve au plus 20 messages en mémoire, sans réseau, fichier ou log ; ils disparaissent avec le processus. Il est refusé en production.

Après vérification **et autorisation distincte**, configuration cible future :

| Variable | Valeur ou source future |
|---|---|
| `RACEATLAS_ENV` | `production` |
| `APP_BASE_URL` | URL HTTPS réelle du site Render, sans chemin, query, fragment ou identifiants |
| `EMAIL_PROVIDER` | `resend` |
| `RESEND_API_KEY` | Secret `sending_access` restreint, fourni par la console |
| `EMAIL_FROM` | `RaceAtlas <notifications@raceatlas.ucthonon.fr>` après vérification |
| `EMAIL_VERIFIED_DOMAIN` | `raceatlas.ucthonon.fr` après preuve opérateur |
| `EMAIL_SEND_AUTHORIZED` | `true` seulement après autorisation d'envoi |
| `EMAIL_TRACKING_DISABLED` | `true` seulement après contrôle des deux trackings désactivés |

Ces attestations sont déclaratives : ni propriété DNS, ni portée réelle de clé, ni autorisation externe ne peuvent être prouvées par leur simple présence. Une configuration Resend incomplète échoue fermé ; aucun fallback vers Development ou `resend.dev`. Le choix du provider seul ne déploie et n'active rien.

## Liens et comportement du service

Modèles français HTML et texte brut, sans mot de passe :

| Message | Objet exact | Bouton | Durée annoncée |
|---|---|---|---|
| Confirmation | Confirmez votre adresse e-mail — RaceAtlas | Confirmer mon adresse e-mail | 24 heures |
| Réinitialisation | Réinitialisez votre mot de passe — RaceAtlas | Réinitialiser mon mot de passe | 30 minutes |

Formats figés pour la future UI : `${APP_BASE_URL}/#confirm-email=<token>` et `${APP_BASE_URL}/#reset-password=<token>` (une seule barre racine après canonicalisation). Jeton URL-safe de 43 caractères, entrées bornées et échappement HTML. Le fragment n'est pas envoyé dans la requête HTTP ou le Referer ; il reste sensible côté navigateur et ne doit pas être journalisé. B1 ne génère/stocke/expire/consomme pas ces jetons : durées et usage unique seront garantis par B2, pas par le rendu email. Aucun GET ne consomme un jeton à ce jalon.

Le SDK officiel `resend.Emails.send` utilise le transport borné fourni : POST exact `https://api.resend.com/emails`, TLS vérifié, pas de proxy hérité, redirection ou retry ; connect 3,05 s/read 5 s et réponse décompressée limitée à 65 536 octets. Ce ne sont pas une échéance totale ni un SLA. Les globals du SDK sont sérialisés (attente maximale du verrou 1 s) et restaurés sur succès/erreur. Tout futur code doit passer par EmailService, sans écrire ces globals ni appeler le SDK directement.

Un résultat `accepted` signifie seulement acceptation API, jamais réception. Les erreurs restent génériques (`quota`, `rejected`, `busy`, `delivery_failed`), sans exception native, corps, destinataire, clé ou jeton. L'identifiant d'opération UUID est opaque ; conserver le même pour une éventuelle répétition explicitement décidée. B1 ne retente rien et n'offre pas de file persistante. Les futurs flux doivent effectuer l'I/O email hors verrou/transaction métier et ne publier un lien qu'après commit.

## Limites et essais ultérieurs

[Quotas documentés](https://resend.com/docs/knowledge-base/account-quotas-and-limits) et [offre](https://resend.com/pricing), consultés le 13 novembre 2026 : Free **100 emails/jour UTC**, **3 000/mois**, **3 domaines**, **10 requêtes/s par équipe**. Le comptage concerne notamment les destinataires ; vérifier les règles et quotas réels du compte lors de son ouverture. Aucun quota de compte n'a été interrogé. Sur 429/quota, arrêter et signaler, sans boucle, file de retry ou passage payant. Les limites peuvent changer.

Après autorisation, puis après implémentation B2/C : vérifier une réception contrôlée HTML/texte, From, SPF/DKIM/DMARC, absence de tracking, URL réelle, confirmation/renvoi/expiration/rejeu, reset distinct et révocation des sessions, erreurs 403/429/5xx sans fuite ni énumération. Vérifier dans le compte les limites avant/après, sans provoquer un dépassement. À ce jour tous ces essais externes restent **non réalisés** ; les tests B1 injectent un HTTP simulé dans le vrai SDK et ne qualifient ni délivrabilité ni réputation du domaine.
