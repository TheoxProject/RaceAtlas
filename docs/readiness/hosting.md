# Héberger RaceAtlas sur Render et Neon

Le [Blueprint](../../ops/render.yaml) décrit un Web Service Render Free nommé `raceatlas`, en région Frankfurt, relié à PostgreSQL sur Neon. Les déploiements automatiques et les previews de PR sont désactivés. Créer, déployer ou modifier les services distants exige l’autorisation du propriétaire. La carte, le calendrier et le catalogue sont accessibles sans mot de passe partagé. Les API personnelles exigent une session.

## Commandes du service

- **Build** · `bash ops/build.sh` installe les dépendances Python et compile le frontend avec le lockfile pnpm. Les versions de Python et de Node sont fixées dans le Blueprint.
- **Démarrage** · `python -m raceatlas.serve` lance Waitress sur `0.0.0.0:$PORT` avec quatre threads et sert le React compilé et les API sur la même origine.
- **Sonde** · `/api/health/live` vérifie le processus sans requête PostgreSQL. `/api/health/ready` vérifie l’accès à PostgreSQL et renvoie un état générique. Réserver cette dernière à un diagnostic ponctuel pour laisser Neon se mettre en veille.

Le build et le démarrage n’exécutent ni migration, ni seed, ni synchronisation. Render assure la terminaison TLS et la redirection vers HTTPS. [Runtimes Render](https://render.com/docs/native-runtimes) · [Web Services Render](https://render.com/docs/web-services#port-binding)

## Variables et TLS

| Variable | Exigence |
|---|---|
| `RACEATLAS_ENV` | `production` |
| `DATABASE_URL` | URL complète `postgresql+psycopg` avec hôte, base et identifiants, fournie à Render comme secret |
| Paramètres TLS de l’URL | `sslmode=verify-full&sslrootcert=/etc/ssl/certs/ca-certificates.crt`. Le fichier de CA doit être absolu, lisible et non vide. |
| `PORT` | Fourni par Render. Le lanceur exige une valeur valide et écarte les ports réservés. |
| `MIGRATION_DATABASE_URL` | URL Neon directe réservée à une session de maintenance autorisée, avec les mêmes exigences TLS. |

Le lanceur vérifie ces réglages avant de créer l’application. La vérification du certificat et du nom du serveur PostgreSQL a lieu lors de la connexion. Une erreur de configuration ne doit afficher ni URL ni identifiants. [Exemple d’environnement](../../.env.example) · [Connexion Neon sécurisée](https://neon.com/docs/connect/connect-securely)

L’activation des comptes exige aussi leur configuration serveur et une `APP_BASE_URL` égale à l’origine HTTPS du site. Cette origine sert aux liens de confirmation et de réinitialisation. [Configuration des comptes](../lot-7/resend-guide.md)

## Migrations et contrôle du service

Dans une session de maintenance autorisée, installer les dépendances Python de la version à déployer. Vérifier la cible et la sauvegarde avant toute mutation. Fournir le secret via l’environnement privé.

```powershell
$env:DATABASE_URL = $env:MIGRATION_DATABASE_URL
python -m alembic current
python -m alembic upgrade head
python -m alembic check
```

Le Web Service utilise son propre secret de connexion. Le CLI `seed-synthetic` refuse le mode production.

Après déploiement, vérifier l’accueil, les assets, le catalogue, la carte et la readiness en HTTPS. Tester le catalogue dans une session anonyme et le refus d’une route personnelle sans session. Si les comptes sont actifs, tester les liens e-mail avec un compte autorisé. Avant de rétablir un déploiement précédent, vérifier sa compatibilité avec les variables et le schéma actuels. [Retour arrière Render](https://render.com/docs/rollbacks)

## Sauvegarde et restauration

L’exercice V1 a été effectué sur des bases PostgreSQL locales avec des données synthétiques. Avant usage sur des données réelles, convenir du stockage chiffré, de la rétention et des accès. [Preuves de restauration V1](../lot-8/backup-validation.md)

1. Depuis un environnement privé, utiliser un client PostgreSQL compatible avec le serveur. Préparer `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSSLMODE=verify-full` et `PGSSLROOTCERT`. Fournir les identifiants via un `PGPASSFILE` privé, hors arguments et journaux.
2. Créer l’archive avec `pg_dump --format=custom --no-owner --no-privileges --file <archive-privee>`. Garder l’archive hors Render et GitHub. Consigner le checksum, la date, les versions et la révision Alembic.
3. Ouvrir une session distincte pour la restauration avec les seuls réglages PostgreSQL locaux. Vérifier l’adresse `127.0.0.1`, le port, le rôle et le nom inédit de la base jetable. Examiner l’archive et restaurer avec `pg_restore --host 127.0.0.1 --port <port-local> --username <rôle-local> --exit-on-error --single-transaction --no-owner --no-privileges --dbname <base-jetable> <archive-privee>`. Vérifier les migrations, contraintes, identités attendues et API.

Références des commandes. [pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html) · [pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html)

## Quotas et sources

Vérifier les quotas des comptes et la consommation partagée avant de publier. Les offres gratuites ont des seuils de veille et de ressources. Tout changement potentiellement facturable exige l’autorisation du propriétaire. Les hypothèses chiffrées du premier hébergement sont archivées. [Render Free](https://render.com/docs/free) · [Plans Neon](https://neon.com/docs/introduction/plans) · [Rapport historique](https://github.com/TheoxProject/RaceAtlas/blob/v1.0.0/docs/readiness/predeployment-report.md)

Les crédits de l’interface distinguent les fournisseurs de cartes et de relief. Vérifier les conditions du fond, du style et de leurs données avant toute réutilisation. Le rapport historique conserve aussi la réponse 403 à la consultation du JSON d’attributions du relief. La collecte FFC récurrente et tout élargissement du corpus demandent une qualification et des droits établis. [OpenFreeMap](https://openfreemap.org/tos/) · [Licences des styles](https://github.com/hyperknot/openfreemap-styles/blob/main/LICENSE.md) · [Attribution Mapterhorn](https://mapterhorn.com/attribution) · [Qualification FFC](ffc-qualification.md)

## Vérification locale

Préparer le build React et une base PostgreSQL jetable comme dans le guide de développement. Le groupe ciblé vérifie la validation TLS, le démarrage sans connexion, les accès anonymes et la protection des API de compte. [Développement local](../../README.md#vérification-complète)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend/test_hosting.py -q --tb=short
```
