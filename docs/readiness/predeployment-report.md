# Rapport de pré-déploiement après le lot 6

Établi le **12 novembre 2026**, pour décision après revue du présent jalon. **Aucune activation autorisée ou effectuée par ce rapport.** Compteurs de cette préparation : service créé 0, déploiement 0, base distante touchée 0, paiement 0, email envoyé 0, collecte FFC 0.

La base intégrée est **7b733d86d99a354fdcfe2bf1ecbde519ef78a68f** ([lot 6](../lot-6/integration.md)) : carte Altitude/Summit, calendrier et filtres partagés, détails et candidates non localisées. CI main [43227636726](https://github.com/TheoxProject/RaceAtlas/actions/runs/43227636726) verte : 389 pytest, 67 frontend et gardes de source. Cela prouve des parcours locaux/CI synthétiques, pas le fonctionnement chez Render/Neon.

## Décision proposée

**Recommandation : attendre le candidat de livraison après le lot 8**, tout en développant le lot 7 localement avec transport email simulé. Cela permet de valider comptes/récupération, sauvegarde/restauration et exploitation avant d'héberger des données à conserver. L'attente ne règle pas à elle seule les droits fournisseur/FFC : ces conditions restent explicites.

| Moment possible | Ce que cela permet | Préconditions supplémentaires |
|---|---|---|
| Après le lot 8 / candidat de livraison — recommandé | Une seule qualification externe complète, encore privée avant toute publication V1 | Gates des lots 7–8, sauvegarde/restauration exercée, expéditeur validé pour email réel, conditions fournisseurs clarifiées ; accord d'activation distinct |
| Après le lot 6 | Preview privée technique, uniquement synthétique/jetable, sans comptes utilisateurs ni email | Droits/attributions cartographiques à finir, comptes et plafonds gratuits vérifiés, procédure de fixtures distantes revue si des courses doivent être présentes ; accepter explicitement que ce n'est pas une validation V1 |
| Après le lot 7 | Tester les comptes en preview privée après validation locale | Même qualification hébergement et fournisseurs ; expéditeur et autorisation d'envoi réel si ce chemin est testé ; sauvegarde/restauration à terminer avant données importantes |

**Aucune option n'est sélectionnée par défaut. Le silence n'autorise rien.** La future autorisation doit nommer le SHA revu, la création d'un service Render Free et d'un projet Neon Free, le premier déploiement privé et son jeu de données. Migrations/insertion sur la nouvelle DB distante doivent être couvertes explicitement ; aucune collecte FFC, diffusion publique, carte bancaire, upgrade, achat de domaine ou email réel n'est inclus implicitement. Le périmètre et les comptes doivent être revérifiés au moment de cette décision.

## Services préparés et secrets

Un Web Service Render Python sert Flask/Waitress et le React compilé ; PostgreSQL est prévu chez Neon, sans base Render, worker, cron, stockage objet ou service Node permanent. [`ops/render.yaml`](../../ops/render.yaml) prépare `plan: free`, `region: frankfurt`, branche `main`, `autoDeployTrigger: "off"` et previews désactivées. L'import d'un Blueprint peut créer et déployer le service initial : ne pas l'importer « pour voir ».

La [référence Blueprint](https://render.com/docs/blueprint-spec) reconnaît `frankfurt`. Les [régions Render](https://render.com/docs/regions) et [Neon](https://neon.com/docs/introduction/regions) conduisent à préparer la paire Frankfurt / `aws-eu-central-1`, sous réserve de disponibilité effective Free dans le compte. Les régions sont fixées à la création. Cette proximité n'établit ni réseau privé entre fournisseurs ni conformité juridique.

| Paramètre | Préparation et vérification avant activation |
|---|---|
| Runtime/build | Python 3.12.14, Node 24.22.1 ; `bash ops/build.sh`, dépendances production et pnpm 10.20.0/lockfile gelé, build React. Aucun build Render réel exécuté |
| Start | `python -m raceatlas.serve`, Waitress 3.0.2, un processus, quatre threads, `0.0.0.0:$PORT` ; PORT fourni par Render, normalement 10000 |
| `RACEATLAS_ENV` | `production` pour le launcher privé obligatoire |
| `DATABASE_URL` | Secret complet `postgresql+psycopg`, credentials encodés et hôte/base exacts ; `sslmode=verify-full` et `sslrootcert` absolu lisible, par exemple `/etc/ssl/certs/ca-certificates.crt` |
| `PREVIEW_USERNAME`, `PREVIEW_PASSWORD` | Saisie privée via champs `sync: false`, mot de passe aléatoire d'au moins 32 caractères. Aucun secret dans Git, URL d'accès, commande, capture ou rapport |
| `MIGRATION_DATABASE_URL` | URL Neon directe dans une session de maintenance distincte ; jamais injectée dans le Web Service |
| Domaine/email | Le sous-domaine HTTPS Render n'exige pas un domaine acheté. Aucun domaine ni expéditeur email n'est disponible actuellement ; ce prérequis du lot 7 est distinct |

Préflight fermé avant factory si configuration/TLS/CA/secrets invalides. La CA locale lisible n'est pas une preuve de handshake Neon ; la vérification de chaîne et du nom se fait à la connexion ([TLS Neon](https://neon.com/docs/connect/connect-securely)). HTTPS est terminé au bord Render puis HTTP interne vers Waitress ([port/TLS](https://render.com/docs/web-services#port-binding)). Aucun `ProxyFix` universel ou endpoint de contournement ajouté.

La garde Basic obligatoire protège pages, assets, API et `/api/health/ready` ; seules les méthodes GET/HEAD du chemin exact `/api/health/live`, sans query, sont publiques. Les refus sont génériques 401, les réponses privées `no-store`. Basic reste une protection partagée de preview, distincte des futurs comptes email/mot de passe. Le [guide hosting](hosting.md) détaille formats, rotation et commandes ; aucune ouverture publique préparée.

## Limites gratuites vérifiées et risques

Sources primaires consultées le **12 novembre 2026** ; comptes privés, autres services, moyens de paiement et consommation restante **inconnus**. Les chiffres publiés ne garantissent pas la gratuité de ce workspace précis.

| Ressource | Référence publique et conséquence |
|---|---|
| Render service | [Compute](https://render.com/docs/compute-plans) : Free 0,1 CPU / 512 MB. [Free](https://render.com/docs/free) : 750 h mensuelles partagées par workspace, veille après 15 min, réveil annoncé autour d'une minute, filesystem éphémère. Pas de keepalive artificiel |
| Render builds/transfert | [Pipeline](https://render.com/docs/build-pipeline) : Hobby inclut 500 minutes Starter/mois, partagées. [Free](https://render.com/docs/free) : bande passante/builds peuvent déclencher des suppléments avec paiement ; sans paiement, suspension des services ou arrêt des nouveaux builds selon quota. Le montant de bande passante inclus du compte reste à vérifier |
| Neon | [Plans](https://neon.com/docs/introduction/plans) : Free 100 CU-h/projet/mois, 1 GB PostgreSQL/projet et 20 GB total compte, 5 GB de transfert public/projet/mois ; scale-to-zero après 5 min, autoscaling jusqu'à 2 CU. Historique 6 h et 1 GB de changements, un snapshot manuel. Pas de SLA Free |
| Dépassement Neon | Même [référence](https://neon.com/docs/introduction/plans) : compute suspendu à épuisement CU-h/transfert ; opérations augmentant le stockage refusées au plafond. Une DB suspendue ne permet pas `pg_dump` avant reprise. Ne pas attendre le quota épuisé pour sauvegarder |

Ne pas ajouter de moyen de paiement, activer un plan supérieur ou changer une limite de dépense pour résoudre un blocage. Préférer arrêt explicite et décision propriétaire. Le choix de région n'écarte pas les risques financiers, de données ou de sous-traitance.

## Estimations sous hypothèses, pas mesures de production

Calculs décimaux : kB = 1 000 octets, MB = 1 000 000, GB = 1 000 000 000. Scénarios de dimensionnement fictifs, **aucune estimation du nombre réel d'épreuves FFC**. Les tailles de lignes, profils d'usage, latences et mémoire devront être mesurés après une éventuelle autorisation.

| Scénario | Calcul et résultat | Lecture prudente |
|---|---|---|
| DB, enveloppe de 10 000 épreuves | 10 000 × 20 kB (épreuve et relations) × facteur 2 (index/marge) + 50 MB fixes = **450 MB**, 45 % de 1 GB | Hypothèse non mesurée ; à 20 000 épreuves : **850 MB**, 85 %. Comptes, historique de changements et sauvegardes peuvent nécessiter davantage ; pas de capacité garantie |
| Neon usage regroupé | 30 jours × (2 h de travail + 4 réveils × 5 min) = **70 h actives** ; à 0,25 CU moyen : **17,5 CU-h** | Hypothèse de sessions regroupées, sans compute secondaire. À 2 CU moyens : **140 CU-h**, au-delà du quota. Toujours actif à 0,25 CU sur 30 jours : **180 CU-h** ; 100 CU-h ne financent que 400 h à 0,25 CU |
| Render heures | 30 × (2 h + 4 réveils × 15 min) = **90 h** ; toujours actif sur 31 jours = **744 h** | Les 750 h sont partagées : un autre service peut épuiser la marge. Pas de promesse que les health checks ou le trafic suivent ce scénario |
| Neon transfert | 100 sessions/j × 30 × 10 sélections × 0,1 MB de sortie DB totale/sélection = **3 GB/mois** | Inclut hypothétiquement toutes les requêtes/pagination de chaque sélection. À 0,2 MB : **6 GB**, dépassement. Ce n'est pas la taille JSON navigateur ni une mesure SQL réelle |
| Sortie Render | 3 000 sessions × (2 MB assets/rechargement + 10 × 0,2 MB API) = **12 GB/mois** | Enveloppe sans bénéfice de cache ; quota restant du workspace inconnu. Les tuiles/styles/DEM sont demandés directement par le navigateur aux fournisseurs, pas relayés par Flask ; leur trafic et leurs droits restent distincts |
| Mémoire runtime | 80 MB de base + 4 requêtes simultanées × 25 MB + 50 MB de marge = **230 MB**, environ 45 % de 512 MB | Budget fictif, pas un profil RSS mesuré. CPU 0,1 et pagination/scopes peuvent limiter avant la RAM. Aucun débit ou temps de réponse garanti |
| Builds | 4 builds autorisés/mois × 5 min supposées = **20 min** | Hypothèse à confronter au vrai build distant et aux autres builds du workspace ; les secondes Vite locales ne représentent pas pip/pnpm/Render |

Ces scénarios sont indépendants : ne pas additionner RAM, stockage, transfert et CU-h. Une première preview synthétique de quelques utilisateurs ne valide pas 10 000 épreuves ou 100 sessions/jour. Définir des seuils opérationnels avant usage réel et examiner la consommation avant chaque session de qualification ; aucune surveillance distante automatique activée ici.

## Séquence future, uniquement après autorisation explicite

1. Revalider SHA intégré/CI, comptes Free et disponibilités régionales, absence de paiement/ressource facturable, quotas restants et conditions fournisseurs. Si une condition diffère, arrêter et présenter le nouveau choix ; ne pas créer pour tester.
2. Avec accord couvrant la nouvelle DB jetable, créer le seul projet Neon prévu, noter version serveur/région et fournir les secrets par canal privé. Vérifier TLS/identité et rôle/cible avant toute mutation. L'application ne crée ni schéma ni données au démarrage.
3. Dans la session de maintenance autorisée : `python -m alembic current`, `python -m alembic heads`, puis `python -m alembic upgrade head` et `python -m alembic check` avec `DATABASE_URL` fourni par `MIGRATION_DATABASE_URL`. Révision intégrée actuelle `b7f4208ac112`, à reconfirmer au SHA déployé. Jamais ces commandes au build/start ; pas de downgrade automatique. Sauvegarder avant modification d'une DB contenant des données à conserver.
4. Définir le jeu de données : DB vide suffit à la santé/au parcours vide ; des courses synthétiques distantes exigent une procédure de maintenance revue et une autorisation d'insertion. Le CLI `seed-synthetic` refuse le mode production : **aucun contournement prévu**. Ni import FFC ni participants réels.
5. Après accord de création/déploiement Render, renseigner les secrets privés, créer depuis le Blueprint revu et confirmer manuellement Free/région/branche/auto-deploy off/previews off avant lancement. Vérifier versions, build et start effectifs ; aucun pre-deploy/cron/keepalive. Ne jamais recopier DSN/Authorization dans les logs ou captures.
6. Tester HTTPS/redirection, anonyme et mauvais Basic →401 pour page/asset/API/ready ; live minimal GET/HEAD →200, chemins voisins non exemptés. Avec credentials valides, ready doit joindre PostgreSQL ; 503 garde un diagnostic générique et se traite sans retry agressif.
7. Vérifier carte/terrain/replis et quatre crédits, calendrier multijour/no-ops/filtres/scopes/rayon, caméra après bascule, mobile physique/GPU et réseau réel. Les tests locaux interceptés ne prouvent pas ces étapes externes. Sans clarification des attributions/droits, ne pas lancer la qualification live correspondante.
8. Mesurer premier démarrage puis reprise après veille, latences API/ready, mémoire, transferts/CU-h/builds. Redémarrer et confirmer persistance PostgreSQL ; les fichiers et la mémoire Render sont jetables. Ne pas simuler une charge volumique sans budget et accord précis.
9. En cas de secret compromis, suspendre l'accès et préparer rotation privée/redémarrage ; pour panne applicative, retour au SHA connu compatible avec le schéma. Aucune restauration/downgrade destructif automatique. Arrêt distant ou suppression de ressources à exécuter seulement dans le périmètre autorisé, en préservant les données importantes.

## Sauvegarde, email et sources : conditions encore ouvertes

La procédure du [guide hosting](hosting.md#sauvegarde-et-restauration-préparées) emploie un client PostgreSQL 17 ou supérieur compatible avec le serveur, URL directe/TLS via `PGHOST`, `PGDATABASE`, `PGUSER`, `PGSSLMODE=verify-full`, `PGSSLROOTCERT` et `PGPASSFILE` privé ; aucun secret dans argv. `pg_dump --format=custom --no-owner --no-privileges` vers stockage privé chiffré hors Render/GitHub ; checksum/manifeste/version. Restauration d'abord dans une **nouvelle DB locale jetable**, jamais `--clean` d'une base importante, puis contraintes/migrations/identités/API. [Documentation pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html). **Exercice complet et automatisation restent au lot 8** ; une procédure écrite ou six heures d'historique Neon ne constituent pas cette preuve.

Le propriétaire choisit **email + mot de passe avec récupération par email**, sans domaine ni expéditeur actuel. Développer avec simulateur local ne nécessite pas de compte email externe ; cela ne valide ni délivrabilité, identité d'expéditeur, DNS, origine canonique des liens, stockage des secrets ou autorisation d'envoi réel. Ces éléments seront préparés et revus au lot 7 ; Basic preview ne les remplace pas. Aucun service email choisi/créé, domaine acheté ou message envoyé.

Les [conditions OpenFreeMap](https://openfreemap.org/tos/) (mise à jour affichée du 14 octobre 2026), son [quick start](https://openfreemap.org/quick_start/) et les [licences des styles](https://github.com/hyperknot/openfreemap-styles/blob/main/LICENSE.md) doivent être considérés ensemble : repo MIT, Liberty code BSD-3/design CC BY 4.0, données OSM et licences de polices distinctes. Ce relevé n'est pas une validation juridique de redistribution.

Pour Mapterhorn, [homepage](https://mapterhorn.com/), [accès aux données](https://mapterhorn.com/data-access/) et [README public](https://github.com/mapterhorn/mapterhorn) séparent code BSD-3 et sources terrain multiples. Le lien UI est aligné sur [la page d'attribution officielle](https://mapterhorn.com/attribution), également indiquée par le TileJSON observé le 11 novembre. Le JSON d'attributions distinct a répondu **403 au GET standard du 12 novembre** ; aucune nouvelle tentative, changement d'User-Agent, miroir ou téléchargement de tuiles/archives n'a été entrepris pour le contourner. **Sources terrain détaillées/licences encore à qualifier** ; corriger un href ne vaut pas audit complet.

Enfin, [qualification FFC](ffc-qualification.md) : deux exemples limités ont échoué explicitement, droits de collecte/réutilisation non établis. Aucun calendrier réel complet, synchronisation récurrente ou republication autorisé. La preview synthétique n'autorise pas de contourner ce blocage ou d'adapter le produit pour masquer l'absence de qualification.

## Matrice de preuve et suite

| Élément | État réel |
|---|---|
| Lots 0–6, CI main et parcours synthétiques | Intégrés ; références exactes en tête, preuves [lot 6](../lot-6/integration.md) |
| Launcher privé, TLS préflight, Basic et santé locaux | Testés dans [préparation V1](integration.md), réutilisation de code inchangé ; pas de handshake distant |
| Région Blueprint et href crédit | Préparés dans ce jalon ; contrôles/résultats courants au [handoff](predeployment-handoff.md), CI et revue exacte requises |
| Comptes/plafonds disponibles, vrai build/start Render, CA/Neon | Non inspectés ou non exécutés ; autorisation et qualification nécessaires |
| Budget de ressources | Hypothèses chiffrées ci-dessus, à mesurer ; aucune garantie de gratuité/performance |
| Backup/restore complet, comptes/email réels | Non validés ; lots 7–8 et expéditeur manquant |
| GPU/tuiles live, licences cartographiques et droits FFC | Qualification partielle ou bloquée, aucune conclusion globale |

Après intégration/revue/CI de PRE-01, le Coordinator présentera les trois moments de déploiement avec ces conditions. Les travaux indépendants du lot 7 peuvent continuer localement ; **aucune opération distante n'est engagée par la préparation, la fusion ou le choix d'un moment**.
