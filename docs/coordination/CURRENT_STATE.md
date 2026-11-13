# Point de reprise RaceAtlas

**Checkpoint UTC2026-11-13T10:23Z — B1 approuvé au jalon, B2 préparé pour revue, non approuvé.** Même Developer repris après reset explicite, aucune limite active constatée à cette reprise. PR12 reste Draft, non fusionnée ; aucun HTTP/email réel livré par le jalon B1.

## Git, responsabilités et prochaine action

Branche **feature/account-authentication**, worktree isolé add4, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12). Parent local/distant **c79c557e32fed3fd56c85ed1ce786f0bd46fde04**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Developer a intégré les trois fichiers de cadrage préparés par Root avec le code B2. Le commit contenant ce checkpoint est le prochain candidat ; relever son SHA exact après push pour gel et contrôle CI. Root PR/notes ignorées uniquement, Tester indépendant read-only ; aucun autre writer.

**Prochaine action sûre :** publier le jalon B2 cohérent, communiquer le SHA exact au Coordinator, puis STOP éditions pendant revue B2 et CI de ce SHA. Voir [mission](../lot-7/account-flows-mission.md) et [handoff B2](../lot-7/account-flows-handoff.md). Aucun verdict B1/A transféré au nouveau head. Pas de C/HTTP/UI anticipé ni fullbackend/browser local inchangé répété.

B1 **APPROVE ciblé exactc79c**, Tester68emailPASS1,96s+10sondesindépendantesPASS1,52s, Ruff54/contrats26/pipcheck/diff et quatre PNG vus. [CI43404533408](https://github.com/TheoxProject/RaceAtlas/actions/runs/43404533408) SUCCESS **589backend176,18s/67frontend**, source exacte avant/après. Root a vu reset390 et confirmation680 ; rapport complet publié dans PR12. Rien de ceci n'approuve B2 ou un nouveau head. Developer B1 :68emailPASS2,02s+64authPASS20,66s ; handoff email-handoff.md, guide resend-guide.md. Premier run tronqué demeure historique inconnu, preuves acquises distinctes ensuite.

| Tâche | État |
|---|---|
| ACC-01 identité et sauvegardes | DONE intégré PR11/mainCI |
| ACC-02A primitives/sessions | DONE jalon APPROVE9dfd ; PR12 incomplète |
| ACC-02B1 service/SDK/templates | DONE jalon APPROVEc79c et CI589/67 |
| Sujet reset/guide Webador/rendus synthétiques | DONE préparation, aucun essai externe |
| ACC-02B2 confirmation/reset/renvois/limites PG | Implémenté, final61B2 PASS + régression64A PASS ; revue/CI du nouveau head TODO |
| ACC-02C HTTP/cookies/CSRF/abus/suppression | TODO |
| PLAN-01 / UI / acceptation lot7 | TODO |
| Domaine vérifié, clé, envoi réel, déploiement | BLOCKED autorisation/préconditions ; aucun effectué |

## Décisions et limites

Resend Free et SDK officiel retenus. Club propriétaire de `ucthonon.fr` selon instruction propriétaire, gestion DNS Webador ; cible **raceatlas.ucthonon.fr**, **email seulement**, From futur **RaceAtlas <notifications@raceatlas.ucthonon.fr>**. Aucune vérification Resend/DNS ou clé réelle acquise. Aucun domaine de remplacement à rechercher/acheter. Ne modifier ni supprimer les enregistrements existants du club, notamment A/CNAME/MX racine ; guide avec noms de format, valeurs réelles console uniquement et prévention du suffixe doublé. Irlande recommandée pour routage si disponible, pas résidence EU : stockage US/rétention Free30j documentés avant activation.

APP_BASE_URL doit être l’URL **réelle** Render à renseigner, non encore connue/confirmée, indépendante du domaine email. `.env.example` : provider Development, URL/clé/From/domaine vérifié vides, attestations d’autorisation/tracking false. Aucun compte externe, achat, DNS, API avec clé, email réel, service ou déploiement autorisé/exécuté. Premier déploiement privé après lot8/candidatV1 sous autorisation distincte.

Objets exacts : « Confirmez votre adresse e-mail — RaceAtlas » / « Réinitialisez votre mot de passe — RaceAtlas ». Confirmation annoncée24h et reset30min ; B2 implémente jetons hashés/usage unique/renvoi/révocation sans route ; B1 rend les messages. Liens depuis APP_BASE_URL uniquement : `/#confirm-email=<token>` / `/#reset-password=<token>`. Aucun Host/Forwarded ou token query. Pas d’I/O email sous verrou Account/transaction métier ni lien publié avant commit lors de B2.

## Preuves réconciliées

- Premier run pré-interruption tronqué : résultat inconnu, ne pas le relabeller PASS. Cache sans échec non probant.
- Sauvegarde1464 : [CI43402452005](https://github.com/TheoxProject/RaceAtlas/actions/runs/43402452005) SUCCESS **589 backend227,04s / 67 frontend**, gardes exactes ; antérieure au sujet corrigé, ne valide pas le nouveau head.
- Reprise : `pytest tests/backend/test_email.py -q --tb=short --junitxml=.local-tools/email-b1-final.xml` **68 PASS2,02s exit0**, vrai SDK/HTTP entièrement simulé et réseau requests interdit.
- Régression A après dépendances : `pytest tests/backend/test_auth_passwords.py tests/backend/test_auth_sessions.py -q --tb=short --junitxml=.local-tools/email-b1-auth-regression.xml` **64 PASS20,66s exit0**, uniquement `_test` avec opt-in.
- Preuve B1 : Ruff check PASS ; Ruff format --check **54 fichiers conformes** ; pipcheck PASS ; contrats **26PASS** ; diffcheck PASS. Aucun frontend/source/API/modèle/migration/CI/hosting modifié ; pas full589 ou carte/browser inchangés répétés.
- Chromium local : deux modèles x680/390px, routes réseau bloquées, pas de débordement/boutons visibles, quatre PNG inspectés sous `.local-tools/email-b1-preview/` (noms dans handoff), aucune vraie donnée ou email émis. Pas de navigateur/serveur retenu.
- A exact **9dfd8087820608f613e5915a1839800357e1ffb9** : APPROVE ciblé, CI43389431747 SUCCESS521/67 ; code A inchangé, preuves réutilisables explicitement. B1 est désormais approuvé au jalon c79c ; B2 et PR complète restent à revoir.

## Environnement et processus

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, pip via runtime `-m pip --python <venv>`. Resend2.53.2 et transitifs épinglés déjà installés ; ne pas réinstaller ou utiliser les dossiers research comme runtime. Argon2 25.1.0 inchangé.

PostgreSQL17.11 existant127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, userraceatlas_local/PID38028 confirmé avant régression. DeveloperDBraceatlas_lot2_test, TesterDBraceatlas_lot2_review distincte, `RACEATLAS_DISPOSABLE_DB=1`. Aucun Python/Chrome actif avant les tests ; commandes ciblées et Chromium terminés exit0. Pas initdb/reseed/killglobal. Node24.22.1/pnpm10.20.0 et caches Chromium worktree1a1e préservés.

Root possède PR et notes ignorées uniquement ; Developer stop après gel, Tester futur read-only. Plan `.local-tools/tester-email-probe-plan.md` à contextualiser : domaine choisi mais non vérifié. ACC-01 intégration et lots antérieurs liés depuis README ; FFC droits/compatibilité, délivrabilité, clients mail réels et acceptation auth complète restent limites. Pas de reset/forcepush/main direct, pas collecte live, aucun secret dans les preuves.

## Preuves B2 et contrat de reprise

- Code : `auth/flows.py`, `flow_limits.py`, trois tables privées et migration **e95c0278b431** après d82b9147a120, tests `test_account_flows.py`, .env avec AUTH_RATE_KEY vide. A/B1/pins/source/frontend/CI/hosting inchangés (diff vérifié).
- Premier bloc **33PASS9,91s**, étendu **59PASS25,84s** ; précision de la fenêtre glissante puis final B2+A **124PASS60,51s exit0 (60B2+64A)**, JUnit ignoré `.local-tools/b2-final-auth.xml`. Migration finale upgrade/check/base/upgrade/check incluse sur `_test` uniquement ; ancienne révision locale inédite redescendue à d82 avant réapplication de son schéma final. Pas de migration distante.
- Ruff check PASS ; Ruff format --check **58 fichiers conformes** ; contrats **26PASS** ; pipcheck/diff PASS. Deux connexions PG avec blocage réellement observé avant premier commit : inscriptions, double consommation, budget nouveau compte refusé, reset contre login/change/revoke/delete dans les deux ordres. Bornes24h/30min, rollback/ORM déjà chargé, HMAC/TTL/cap/purge/budgets UTC et heure glissante éprouvés.
- Account→Budget singleton→quota, aucun retour Budget→Account. Refus budget normal retire seulement Account newly-created ; préexistants/preuve active préservés et compteurs commités normalement. Caller possède commit/rollback, C devra commit les résultats sans intent.
- Session Engine transactionnel unique ; bind Connection externe ou DBAPI AUTOCOMMIT refusé avant mutation. Intents privés en mémoire armés seulement par commit racine réussi ; RELEASE SAVEPOINT seul, rollback/close de l’origine, commit échoué, Session.close/réemploi ne publient rien. Pas d’I/O dans callbacks. Dispatch une fois après commit via EmailService, crash peut perdre intent ; renvoi comme récupération, pas queue ou retry automatique.
- AUTH_RATE_KEY dédié ≥32octets, HMAC pseudonyme ; défaut60s/3 admissions heure glissante/80jourUTC/2400mois/TTL2h/cap4096, purge32 et timestamps≤100 par quota. Propositions techniques configurables, pas quota Resend réel prouvé. Limites IP/admission/timing restent à C.
- Aucun test/processus Python/Chrome retenu après contrôles ; PostgreSQL38028 préservé. Aucun email réel/API Resend/DNS/service/coût/deploy effectué. Après push STOP, Tester/CI renouvelés pour SHA exact ; lot7/PR12 pas terminés.

Dernière vérification pré-gel : garde DBAPI AUTOCOMMIT ajoutée pour rendre explicite Engine transactionnel uniquement. Ciblé commit/rollback initial **7PASS/3FAIL3,78s** (.local-tools/b2-transaction-guard.xml) : les trois tests Connection externe n’utilisaient pas la fixture session nettoyant Account, assertion table vide dépendait de l’ordre ; refus du service déjà effectif. Isolation du fichier corrigée pour supprimer Account privé avant chaque cas, sans source publique touchée. Relance des10cas concernés **10PASS3,37s exit0** (.local-tools/b2-transaction-guard-fixed.xml). Fichier B2 complet final après garde/isolation : **61PASS19,51s exit0**, JUnit `.local-tools/b2-final-flows.xml`. Régression A64 du run124 déjà verte et inchangée. Contrôles Ruff58 et diff revérifiés après ces derniers changements, PASS. Aucun test Python/Chrome retenu.
