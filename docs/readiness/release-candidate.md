# RaceAtlas V1 — dossier du candidat local

Le candidat couvre la feuille de route V1 sur des données synthétiques. La [PR 17](https://github.com/TheoxProject/RaceAtlas/pull/17) porte les derniers contrôles opérationnels. La validation du SHA final, la CI `integrated`, les contrôles après passage en Ready et ceux de `main` figurent dans la PR à mesure qu'ils sont confirmés.

## Matrice des exigences

Les références aux lots intégrés décrivent les preuves déjà exécutées. Leur réutilisation suppose une comparaison Git des chemins concernés. Au jalon sauvegarde `958cc3c7fcea5d78b1575c838a9f44dd27ab3c30`, le produit, les contrats, les fixtures et les migrations sont identiques à `1f1d50b1395eaf271d1a22e255555cc027f34bf1`, la base intégrée du lot 8.

| Exigence | État local et preuve | Qualification restante |
|---|---|---|
| Catalogue AURA, quatre disciplines et CLM sur route | Contrats et fixtures vérifiés. `test_catalog.py` exerce carte et résultats API sur Flask et PostgreSQL, y compris pagination et positions absentes. | Compatibilité et droits pour le catalogue réel. |
| Filtres corrélés et provenance | `test_catalog.py` vérifie OU et ET dans le même périmètre d’engagement, sans combinaison entre listes. Les conditions et libellés bruts restent consultables. | Établir l’identité durable des listes réelles avant import. |
| Carte Altitude et Summit | [Lot 5](../lot-5/integration.md) avec carte rendue, points au centre des communes, regroupement et replis en cas d’erreur du fond de carte, du relief ou du WebGL. | Données et crédits des fournisseurs, rendu sur appareils physiques. |
| Périodes civiles et calendrier mensuel | [Lot 6](../lot-6/integration.md) avec semaines ISO, Europe/Paris, courses multijours et bascule qui conserve le mois. Les contrôles navigateur de la PR finale restent à conclure. | Vérifier caméra et sélection pendant la recette privée. |
| Inscription, confirmation et récupération | [Comptes](../lot-7/auth-integration.md) et [parcours complets](../lot-7/accounts-ui-integration.md). Confirmation requise avant connexion, jetons hachés à usage unique de 24 h et 30 min, récupération générique, révocation et suppression. SDK Resend testé avec transport simulé. | Vérifier le domaine d’envoi, puis l’adresse des liens et la réception. |
| Ma saison et export ICS | [Planning et export](../lot-7/planning-integration.md). Quatre statuts par périmètre, isolement de deux comptes, inscription déclarative, export Prévue et Inscrit avec UID et séquences stables. | Recette sur la base de preview autorisée. |
| Synchronisation et notifications | [Journal et import](../lot-8/n1-integration.md), [API et interface](../lot-8/n2-integration.md). Réimport idempotent, données manquantes à vérifier, compteurs propres à chaque compte, lecture hors page et retrait par liste. Le test navigateur a marqué les 52 notifications disponibles dont 50 étaient affichées. | Sources réelles et activation récurrente soumises à une qualification et une autorisation distinctes. |
| Reprise après erreurs et admission | [Contrôles du lot 8](../lot-8/errors-validation.md). La nouvelle couture relie import incomplet, ancienne couverture conservée, reprise avec notification et répétition stable. Les quotas et erreurs des fournisseurs sont simulés. | Capacité et quotas effectifs à vérifier au moment de la recette. |
| Sauvegarde et restauration | [Validation locale](../lot-8/backup-validation.md), [approbation indépendante](https://github.com/TheoxProject/RaceAtlas/pull/17#issuecomment-6972369820). Deux exercices complets distincts au code `958cc3c`, sur des bases neuves et PostgreSQL 17.11. | Définir le stockage, le chiffrement et la rétention des sauvegardes réelles. |
| Accès, vie privée et exploitation | [Guide d’hébergement](hosting.md). Accès Basic de preview, readiness avec PostgreSQL, liveness minimale, préflight des paramètres TLS, démarrage sans migration et auto-déploiement désactivé. Les preuves de sécurité des comptes et du planning sont dans les rapports des lots 7 et 8. | Tester TLS, secrets, sauvegarde et seuils d’exploitation sur les services autorisés. |

## Navigateurs et mesures

Les parcours intégrés utilisent React compilé, Chromium et le vrai moteur cartographique avec ressources synthétiques. Les preuves des lots 6 et 8 couvrent le format mobile 390 px, le clavier et le retour sur la carte. Le lot 6 a mesuré de 3,672 à 13,625 secondes entre l’action de sélection et son résultat dans les essais concernés. Le rapport du lot 8 indique le nombre de notifications et les interactions exercées. La latence au réveil, la mémoire sur mobile physique et la capacité distante restent à mesurer pendant la recette.

La CI de la PR a observé des délais dépassés après sélection d’une période, recherche et bascule Summit. Les runs `44160225621` et `44260218340` ont relevé le même changement de centre sur mobile. Les campagnes de la PR utilisant l’image Ubuntu `20261111.370.1` ont été plus lentes et ont rencontré ces échecs. Cette image a également passé la suite de `main` après le lot 8. Son rôle reste à déterminer.

Le diagnostic local sur le SHA isolé `933e8f011c55f0cb4c75999453c38aa06515d173` a passé les quatre scénarios en 204,21 s avec PostgreSQL 17.11 et Chromium. Les cinq sélections mensuelles et les deux recherches suivies terminent côté navigateur et Playwright. Les centres enregistrés pendant le scénario mobile concordent à la tolérance du test. Cette campagne apporte une trace de fonctionnement sur l’environnement local. Les journaux CI et l’évaluation des échecs restent suivis dans la PR 17.

## Recette privée et livraison

1. Obtenir l’acceptation indépendante et les contrôles GitHub du SHA final, puis vérifier le merge et les contrôles de `main`.
2. Revalider les conditions des fournisseurs et les quotas disponibles. La [qualification FFC](ffc-qualification.md) a relevé deux structures réelles que le lecteur actuel ne traite pas. Un échantillon autorisé est nécessaire pour adapter et valider le lecteur avant un usage réel.
3. Soumettre au propriétaire le candidat, le SHA, les services gratuits à créer, les migrations de la nouvelle base et le jeu de données de la preview protégée. Le [rapport de pré-déploiement](predeployment-report.md) fixe le premier essai privé au stade du candidat V1.
4. Après autorisation, vérifier TLS et l’accès à la preview sur Render et Neon, mesurer démarrage et réveil, tester la persistance et les parcours sur appareils physiques. Confirmer la procédure de restauration et le budget de ressources sur le corpus approuvé.
5. Pour activer les inscriptions réelles, suivre le [guide Resend et Webador](../lot-7/resend-guide.md) après accord. Le domaine `raceatlas.ucthonon.fr` sert à l’expédition. Les liens utilisent l’URL Render réelle configurée par `APP_BASE_URL`. Vérifier le DNS fourni par Resend, la clé d’envoi limitée au domaine, la désactivation du suivi et les deux parcours de réception.
6. Documenter les résultats et soumettre la publication et le tag final au propriétaire.
