# Héberger RaceAtlas sur Render Free et Neon Free

Cette configuration prépare un nouveau service Render relié à Neon. Le lanceur ouvre la carte, le calendrier et le catalogue aux visiteurs. Les API personnelles conservent leurs contrôles de session. Le [rapport de pré-déploiement après le lot 6](predeployment-report.md) décrit la préparation historique de l’ancienne preview.

## Architecture et commandes préparées

Un seul Web Service Python sert Flask, les API et `frontend/dist`. Waitress 3.0.2 est déjà épinglé dans les dépendances ; aucun service Node permanent ni base Render n'est ajouté. Le catalogue utilise PostgreSQL standard et les migrations existantes, sans extension PostGIS ou SDK Neon.

- Blueprint [`ops/render.yaml`](../../ops/render.yaml). Le nouveau service `raceatlas` suit la branche `main` sur le plan Free, en région Frankfurt, avec des déploiements manuels. Les previews de PR Render sont désactivées. Importer le Blueprint ou reprendre ses réglages en créant le service sur le tableau de bord. [Référence Blueprint](https://render.com/docs/blueprint-spec)
- Build : `bash ops/build.sh`. Dépendances Python de production, pnpm 10.20.0 et lockfile gelé, outils frontend de build inclus via `--prod=false`, compilation React. Python 3.12.14 et Node 24.22.1 sont explicites ; les scripts Bash restent en LF grâce à `ops/.gitattributes`.
- Start : `python -m raceatlas.serve`, Waitress sur `0.0.0.0:$PORT`, quatre threads. **Ni le build ni le démarrage n'exécutent Alembic, seed ou synchronisation.** Le launcher n'ouvre pas de connexion DB à sa création ; les requêtes DB autorisées et la readiness le font ensuite.

Le runtime Python Render inclut Node, npm et pnpm. La CI compile le frontend en utilisant le lockfile. [Runtimes Render](https://render.com/docs/native-runtimes)

## Variables et TLS

Les champs `sync: false` du Blueprint attendent une saisie privée par l'opérateur autorisé ; aucune valeur secrète n'est fournie. [`.env.example`](../../.env.example) reste un exemple local non chargé automatiquement, avec les nouveaux secrets laissés vides.

| Variable | Exigence du lanceur |
|---|---|
| `RACEATLAS_ENV` | `production`, obligatoire avant la factory Flask |
| `DATABASE_URL` | URL complète `postgresql+psycopg`, hôte, base et credentials ; ne jamais la publier |
| Paramètres TLS de cette URL | `sslmode=verify-full` et `sslrootcert` vers une CA absolue, lisible et non vide ; par exemple `/etc/ssl/certs/ca-certificates.crt` sur Render |
| `PORT` | Fourni par Render, défaut `10000` ; ne pas personnaliser. Les ports réservés `18012`, `18013`, `19099` sont rejetés |
| `PYTHON_VERSION`, `NODE_VERSION` | Versions épinglées dans le Blueprint |
| `MIGRATION_DATABASE_URL` | Session de maintenance distincte seulement, jamais injectée dans le Web Service |

Une configuration incomplète ou TLS affaibli arrête le launcher avant `create_app`. Ses erreurs ne contiennent pas les valeurs de variables. La prévalidation de CA prouve sa présence et sa lecture ; **libpq vérifie la chaîne et le nom du serveur lors de la connexion**, ce qui n'a pas été exercé contre Neon ici. Référence : [connexion Neon sécurisée](https://neon.com/docs/connect/connect-securely).

Le pool catalogue et son `pool_pre_ping`/`connect_timeout=3` restent inchangés. Un seul processus Waitress à quatre threads borne les requêtes simultanées du service ; ce n'est pas une promesse de disponibilité ou de délai maximal après veille.

## Accès public et santé

Le lanceur sert directement Flask. Vérifier dans une session anonyme la page d’accueil et ses assets, le catalogue et la carte pour 2027, puis contrôler qu’une route personnelle refuse la requête sans session. Render termine TLS au load balancer et redirige HTTP vers HTTPS. [Web Services Render](https://render.com/docs/web-services#port-binding)

Si les comptes sont activés sur le nouveau service, recopier leur configuration depuis la source de secrets et définir `APP_BASE_URL` sur le nouveau site HTTPS. Cette URL sert aux liens envoyés par e-mail. [Configuration des comptes](../lot-7/resend-guide.md)

`/api/health/live` teste le processus sans requête PostgreSQL. Render utilise cette route comme sonde. `/api/health/ready` vérifie PostgreSQL et renvoie un état générique. Utiliser la readiness pour un diagnostic ponctuel afin de laisser Neon se mettre en veille. En cas de régression du déploiement, rétablir le déploiement Render précédent après avoir vérifié sa compatibilité avec la configuration du service. [Retour arrière Render](https://render.com/docs/rollbacks)

## Migrations et validation après une future autorisation

Préparer une URL Neon **directe** de maintenance distincte, avec les mêmes exigences TLS, dans une session privée de l'opérateur. Les migrations ne passent ni dans le build, ni dans le start, ni dans un `preDeployCommand` payant. Les commandes suivantes ne sont un mode opératoire qu'après autorisation explicite ; aucune n'a été exécutée contre une DB distante :

```powershell
# Les deux secrets proviennent de la session privée, jamais d'un fichier versionné.
$env:DATABASE_URL = $env:MIGRATION_DATABASE_URL
python -m alembic current
python -m alembic upgrade head
python -m alembic check
```

Vérifier cible, sauvegarde et version attendue avant mutation ; ne pas faire de downgrade automatique de données importantes. Reprendre ensuite une session Web avec son URL d'application, pas avec le secret de maintenance.

Les tests locaux et la CI utilisent un PostgreSQL jetable et des fixtures synthétiques. Le CLI `seed-synthetic` bloque les bases de production.

## Sauvegarde et restauration préparées

Le lot8 fournit désormais un [CLI local borné et une preuve Developer synthétique complète](../lot-8/backup-validation.md) sur deux bases neuves PostgreSQL17. La revue indépendante B et les gates finaux restent requis. Aucun dump de données réelles ni restauration distante n’a été effectué ; la procédure opérationnelle réelle (chiffrement, rétention, stockage externe) n’est pas qualifiée par cette preuve locale.

1. Opérateur autorisé, client PostgreSQL **17 ou plus récent compatible** avec la version serveur, depuis un environnement privé hors filesystem Render. Ne pas supposer que le `postgresql-client` de Render est en version 17.
2. URL directe et TLS vérifié. Fournir `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSSLMODE=verify-full`, `PGSSLROOTCERT` et un `PGPASSFILE` privé fourni par le gestionnaire de secrets. Aucun mot de passe/DSN en argv ou logs.
3. `pg_dump --format=custom --no-owner --no-privileges --file <archive-privee>` vers un stockage chiffré privé hors dépôt et Render. Contrôler exit code, checksum et manifeste : date, version client/serveur, migration, identité du jeu synthétique. Ne jamais mettre une archive réelle dans les artefacts GitHub.
4. La première preuve de restauration doit viser **une nouvelle DB locale jetable**, après vérification explicite de `PGHOST=127.0.0.1` et de son nom inédit. Examiner l'archive et appliquer `pg_restore --exit-on-error --single-transaction --no-owner --no-privileges --dbname <nom-de-cette-base> <archive-privee>`. Pas de `--clean`, pas de base importante réutilisée.
5. Vérifier migrations, contraintes, nombres/identités des fixtures et API. Consigner le résultat réel ; n'autoriser aucune restauration distante sur la seule existence de ce document.

Référence des outils : [PostgreSQL 17, pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html) et [pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html). La rétention/chiffrement des archives et la restauration opérationnelle seront validés au lot 8 avant usage de données réelles.

## Limites gratuites à revérifier avant activation

Constat documentaire revérifié le **12 novembre 2026**, pas une inspection de comptes ou une garantie de facturation :

| Fournisseur | Limites pertinentes et conduite prévue |
|---|---|
| Render Free | 750 heures par workspace/mois, partagées ; veille après 15 minutes sans trafic, réveil annoncé autour d'une minute. Filesystem éphémère ; pas de disque persistant, SSH ou one-off job gratuit. Bande passante/builds peuvent entraîner des suppléments si une méthode de paiement existe ; sans paiement, suspension/désactivation selon le quota. Aucun paiement ou upgrade automatique préparé. |
| Neon Free | 100 CU-heures/projet/mois, 1 GB PostgreSQL/projet et 5 GB de transfert public/projet/mois ; veille après 5 minutes. 100 CU-heures correspondent à 400 heures à 0,25 CU, pas un mois constamment actif. Limites compute/transfert : suspension ; stockage saturé : écritures refusées. Historique de restauration gratuit borné, insuffisant pour remplacer une sauvegarde indépendante. |

Sources : [Render Free](https://render.com/docs/free), [plans Neon](https://neon.com/docs/introduction/plans). Ne pas ajouter de carte, souscrire, créer de service ou modifier une limite de dépense sans autorisation. L'usage des comptes et l'épuisement réel des quotas ne sont pas connus ; préférer l'indisponibilité explicite à un coût inattendu. Aucun SLA, performance régionale, qualification GPU physique ou droit FFC/fournisseur de cartes n'est établi par cette préparation.

Le plan service Free est publié à 0,1 CPU / 512 MB ([compute Render](https://render.com/docs/compute-plans)) ; le workspace Hobby inclut 500 minutes Starter/mois ([pipeline](https://render.com/docs/build-pipeline)). Quotas effectifs et consommation partagée doivent être contrôlés avant toute activation. Les [scénarios de ressources](predeployment-report.md#estimations-sous-hypothèses-pas-mesures-de-production) sont des hypothèses, pas des mesures distantes.

Les cartes ont des obligations propres : le href Mapterhorn pointe désormais vers la page d'attribution officielle, mais son JSON distinct a répondu 403 au GET standard du 12 novembre, sans nouvelle tentative ou contournement. Cette correction n'est pas un audit de licences. FFC reste bloquée selon sa [qualification limitée](ffc-qualification.md). Comptes email/mot de passe et récupération sont le choix du propriétaire pour le lot 7 ; aucun domaine/expéditeur disponible, aucun email réel envoyé. Développement local simulé possible ; qualification de délivrabilité toujours ouverte.

## Vérification locale de cette préparation

Utiliser une DB PostgreSQL jetable suffixée `_test` ou `_review`, l'opt-in `RACEATLAS_DISPOSABLE_DB=1` et le build frontend existant. Exemple PowerShell, à adapter depuis le setup du [README](../../README.md) :

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
python -m pytest tests/backend/test_hosting.py -q --tb=short
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
```

Les tests couvrent la validation TLS et CA, le démarrage sans connexion, migration ou seed, la configuration Waitress et les accès anonymes et personnels. Les tests intégrés exercent Flask, le React compilé et PostgreSQL local. Suivre la validation en cours dans le [checkpoint](../coordination/CURRENT_STATE.md).
