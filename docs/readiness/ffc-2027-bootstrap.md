# Chargement initial des courses FFC 2027

Le chargement couvre les courses dont le départ est en 2027 dans les douze départements d’Auvergne-Rhône-Alpes, pour la route, le gravel, le VTT et le cyclo-cross. La paire saison FFC et numéro de course identifie la source. L’année civile vient des dates affichées.

L’opérateur lit le calendrier et les fiches HTML publiques. Le calendrier est parcouru par fenêtres de quatorze jours au plus, avec un délai entre les requêtes. L’outil exige les dates, le département et le nombre de fiches affichés avant d’accepter une fenêtre comme échantillon cohérent. Il journalise les échecs et les exclusions en codes. Les pièces d’engagement et les données de participants restent hors périmètre.

Le traitement applique les fiches positives et journalise les fenêtres cohérentes comme partielles. Une course absente ne change pas d’état. Les catégories ou l’identité d’une liste restent incertaines si la fiche ne fournit pas de preuve. Les courses sans centre de commune confirmé restent accessibles dans le catalogue et le calendrier.

## Exécution sur une cible autorisée

1. Vérifier le SHA approuvé, l’autorisation du chargement et la révision Alembic. Préparer dans la session de maintenance une URL Neon directe pour la cible et les paramètres TLS `sslmode=verify-full` et `sslrootcert`. Conserver le secret dans l’environnement du processus.
2. Lancer la commande suivante avec le nom exact de l’hôte Neon et de la base attendue. Sans `--apply`, elle lit le site et retourne un bilan de collecte sans écrire dans PostgreSQL.

   ```powershell
   python -m raceatlas.ffc.bootstrap_2027 --apply --expect-host $targetHost --expect-database $targetDatabase
   ```

3. Vérifier le bilan de collecte, l’identifiant d’exécution, le nombre de courses acceptées et l’absence de changements d’état déduits d’une absence. Conserver les compteurs et traiter les diagnostics source avant de conclure à la couverture du catalogue.

Après une interruption pendant l’écriture, vérifier la dernière exécution enregistrée avant de relancer. La commande traite les fenêtres par transactions séparées. Les identités déjà observées restent stables lors d’un rejeu. L’exécution est manuelle et ponctuelle.
