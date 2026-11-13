# Point de reprise RaceAtlas

**Checkpoint d'interruption UTC2026-11-13T09:34Z — ACC-02B1 WIP, non revu.** Le Developer a atteint la limite d'utilisation de la plateforme, avec reprise indiquée le18novembre2026. Aucun autre agent n'a reçu son implémentation pour contourner cette limite ; aucune reprise automatique promise. Coordinator sauvegarde les fichiers existants et les décisions, sans terminer ou approuver B1.

## État réel et prochaine action sûre

Branche **feature/account-authentication**, worktree isolé add4, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12). Parent local/distant avant sauvegarde **32a4b5aa30a918b376ceec1d6c0f951666114fa5**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Relever le SHA de sauvegarde sur Git/PR après publication. PR non fusionnée ; aucun verdict transféré de A au WIP.

Fichiers B1 présents : `raceatlas/email/{__init__,config,providers,templates}.py`, `tests/backend/test_email.py`, pins SDK dans requirements/constraints, `.env.example` et mission. Le Developer a signalé un premier run natif dont la sortie a été tronquée : **nombre de tests/code de sortie non réconciliés, aucun PASS B1 revendiqué**. Cache pytest sans échec ne prouve pas réussite. Contrôle natif13nov09:29UTC : aucun Python/Chrome/Chromium actif, donc aucune session de test à attendre ou interrompre. Pas de JUnit B1 identifié au niveau racine des artefacts ; ne pas supposer rapport existant. Aucun B2/HTTP/frontend/activation commencé.

**Prochaine action sûre lorsque la capacité redevient disponible et qu'une session est effectivement reprise :** vérifier status/head/processus, reprendre le même Developer sur le WIP conservé, adapter la configuration/templates aux dernières décisions ci-dessous, puis lancer uniquement les tests email ciblés avec code de sortie et JUnit ignoré conservés. Le premier résultat tronqué ne doit pas être réétiqueté PASS. Ensuite contrôles pertinents/visuels, handoff/gel SHA exact, revue indépendante B1 et CI ; pas de merge avant toutes les gates finales.

| Tâche | État |
|---|---|
| ACC-01 identité et favoris | DONE intégré PR11/mainCI |
| ACC-02A primitives/sessions | DONE jalon APPROVE9dfd ; PR12 pas complète |
| ACC-02B1 EmailService/SDK/templates/docs | BLOCKED capacité Developer, code WIP sauvegardé, tests inconnus |
| Mise à jour sujet reset dans code/tests | TODO : « Réinitialisez votre mot de passe — RaceAtlas » |
| Guide Resend/Webador et preuve visuelle HTML | TODO, aucune validation complète revendiquée |
| ACC-02B2 confirmation24h/reset30min/renvois/limites PG | TODO |
| ACC-02C Flask/cookies/CSRF/abus/suppression | TODO |
| PLAN-01 / UI / acceptation lot7 | TODO |
| Domaine vérifié, clé, envoi réel, déploiement | BLOCKED autorisation/préconditions, aucun effectué |

## Dernière décision propriétaire faisant autorité

Le club possède **ucthonon.fr** et indique **Webador** comme gestionnaire DNS. Sous-domaine retenu **raceatlas.ucthonon.fr**, réservé à l'expédition email ; From cible **RaceAtlas <notifications@raceatlas.ucthonon.fr>**. **Aucune vérification Resend ou modification DNS acquise.** Ne pas toucher/supprimer les enregistrements existants du domaine principal ou les emails du club. Reprendre uniquement les valeurs DNS réellement fournies par Resend ; futur guide doit prévenir le suffixe ucthonon.fr ajouté deux fois par l'interface. Région européenne souhaitée si disponible, à vérifier sur sources primaires et console autorisée.

Resend Free et SDK Python officiel restent choisis. APP_BASE_URL doit contenir l'URL RÉELLE du service Render, non encore connue/confirmée, indépendante du sous-domaine d'envoi. Valeurs locales/test : EMAIL_PROVIDER=development, clé vide, From/domaine vérifié non activés ; exemple production cible seulement après DNS vérifié et autorisation. Aucun achat, création de compte externe, DNS, requête API avec clé, email réel ou déploiement autorisé par ces consignes.

Parcours confirmé : email+mot de passe, compte non vérifié, challenge24h hash seul/usageunique/renvoi avant connexion/personnel ; reset distinct30min/hash seul/usageunique/réponse générique/révocation. Objets HTML+texte : « Confirmez votre adresse e-mail — RaceAtlas » et **« Réinitialisez votre mot de passe — RaceAtlas »** (le WIP templates conserve encore l'ancien objet : à corriger). Liens depuis APP_BASE_URL exclusivement, formats B1 racine `/#confirm-email=<token>` / `/#reset-password=<token>` ; aucun Host/Forwarded ou token query serveur.

## Preuves acquises, sans transfert au WIP

A exact **9dfd8087820608f613e5915a1839800357e1ffb9** APPROVE ciblé : Tester132PASS60,64s +16PASS18,10s ; CI43389431747 SUCCESS521backend220,54s/67frontend, gardes exactes. Cadrage32a4 CI43391151742 SUCCESS521backend219,72s/67frontend, gardes exactes. Aucune de ces CI ne valide les nouveaux fichiers B1.

A : Argon2id19456KiB/t2/p1/sel16/tag32, password exact15–128codepoints/512UTF8, KDF2/process/attente1s ; sessions256bits/SHA256DB/7joursabs24hidle, Accountlock en premier et relecture fraîche jusqu'au commit caller. B doit conserver l'ordre, pas d'I/O email sous verrou ni cookie/lien publié avant commit. Planning/SavedEntry publics/source/frontend/hosting inchangés à ce checkpoint.

## Environnement préservé et preuves de sauvegarde

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, pip via runtime `--python`. Métadonnées vérifiées sans import SDK : resend2.53.2, requests2.34.2, urllib3 2.8.0, charset-normalizer3.5.2, idna3.20, certifi2026.10.23, Argon2 25.1.0 ; **pip check PASS**. Analyse AST sans exécution des4modules email+test_email :5fichiers syntaxiquement valides, `git diff --check` PASS. Ce ne sont pas tests fonctionnels ni revue B1. Ne pas réinstaller ces dépendances ou utiliser les dossiers de recherche comme runtime.

PostgreSQL17.11 existant127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, userraceatlas_local/PID38028. DeveloperDBraceatlas_lot2_test/TesterDBraceatlas_lot2_review avec RACEATLAS_DISPOSABLE_DB=1 ; previewmap_demo distincte. Vérifier statut avant reprise, pas initdb/reseed aveugle. Node24.22.1/pnpm10.20.0/cache, Chromium cacheworktree1a1e prêts ; pas killglobal, anciens Node non revendiqués préservés.

ACC-01 PR11 merge5e2c84a et CI main43282947407 SUCCESS457/67 : docs/lot-7/foundation-integration.md. PRE-01 et lots0–6 : docs/readiness/predeployment-integration.md, docs/lot-6/integration.md et preuves antérieures liées. Main reste5e2c84a tant que PR12 n'a pas passé ses gates complètes.

Derniers agents : Developer errored quota, Tester idle avec plan B1 .local-tools/tester-email-probe-plan.md. Rapports A et ACC01 ignorés complets publiés en PR ; notes .local-tools/resend-integration-notes.md et auth-b2-mission-draft.md préparatoires, pas code validé. Pas reprendre recherches Brevo/Mailjet supersédées. Aucun secret ou vraie donnée expédié ; ne jamais archiver globalement .local-tools (DB/caches/éventuels secrets).

FFC droits/compatibilité réels, licences terrain détaillées/GPU et expéditeur réel restent limitations déjà documentées ; aucune collecte/sync live ou service activé. Premier déploiement privé après lot8/candidatV1, autorisation distincte ; Altitude2,5D et mois partagé inchangés, ICS défautPrévues+Inscrit. Pas reset/forcepush/main direct. Helpers PR ont numéros/bases statiques, fallbackGit/GCM autorisé dans permissions existantes après403 historique du connecteur ; pas clé/token affiché.
