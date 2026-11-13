# Point de reprise RaceAtlas

**Checkpoint UTC2026-11-13T16:42Z — B2 APPROVE exactb12d/CI678, C0 prêt pour revue intermédiaire, non approuvé.** PR12 reste Draft et non fusionnée, main/base5e2c84 inchangé. C1/C2 et authHTTP complète restent à livrer.

## Git, responsabilités et prochaine action

Branche **feature/account-authentication**, worktree isolé add4, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12). Parent local/distant correction C0 **35f123db2ec1741e1509630a2803d29d6b873251**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Developer a intégré les trois fichiers de cadrage préparés par Root avec le code B2. Le commit contenant ce checkpoint est le prochain candidat ; relever son SHA exact après push pour gel et contrôle CI. Root PR/notes ignorées uniquement, Tester indépendant read-only ; aucun autre writer.

**Prochaine action sûre :** publier la correction C0 cycle1 F1/F2 cohérente, donner SHA exact au Coordinator puis STOP éditions pour revue ciblée/CI de ce SHA. [Mission C](../lot-7/auth-http-mission.md), [handoff C0](../lot-7/auth-http-handoff.md). C1sessions/reauth et C2parcours email/queue pas commencés ; ne pas commencer tant que ce jalon est gelé. A/B1/B2 preuves inchangées réutilisées explicitement, pas transfert de verdict au nouveau head.

B1 **APPROVE ciblé exactc79c**, Tester68emailPASS1,96s+10sondesindépendantesPASS1,52s, Ruff54/contrats26/pipcheck/diff et quatre PNG vus. [CI43404533408](https://github.com/TheoxProject/RaceAtlas/actions/runs/43404533408) SUCCESS **589backend176,18s/67frontend**, source exacte avant/après. Root a vu reset390 et confirmation680 ; rapport complet publié dans PR12. Rien de ceci n'approuve B2 ou un nouveau head. Developer B1 :68emailPASS2,02s+64authPASS20,66s ; handoff email-handoff.md, guide resend-guide.md. Premier run tronqué demeure historique inconnu, preuves acquises distinctes ensuite.

| Tâche | État |
|---|---|
| ACC-01 identité et sauvegardes | DONE intégré PR11/mainCI |
| ACC-02A primitives/sessions | DONE jalon APPROVE9dfd ; PR12 incomplète |
| ACC-02B1 service/SDK/templates | DONE jalon APPROVEc79c et CI589/67 |
| Sujet reset/guide Webador/rendus synthétiques | DONE préparation, aucun essai externe |
| ACC-02B2 confirmation/reset/renvois/limites PG | DONE jalon APPROVE exactb12d Tester107PASS et CI678/67 |
| ACC-02C0 configuration/CSRF/admission/corpus | Correction F1/F2 : final70C0/publicPASS ; revue/CI password-auth nouveau head TODO |
| ACC-02C1 sessions/réauth et C2parcours email/queue | TODO, auth backend complète pas livrée |
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
- Depuis correction F1 : AccountFlowSession dédiée obligatoire ; Session brute refusée même bind Engine, routages externes/multi-bind et DBAPI AUTOCOMMIT refusés avant mutation. Intents privés en mémoire armés seulement par commit racine réussi ; RELEASE SAVEPOINT seul, rollback/close de l’origine, commit échoué, Session.close/réemploi ne publient rien. Pas d’I/O dans callbacks. Dispatch une fois après commit via EmailService, crash peut perdre intent ; renvoi comme récupération, pas queue ou retry automatique.
- AUTH_RATE_KEY dédié ≥32octets, HMAC pseudonyme ; défaut60s/3 admissions heure glissante/80jourUTC/2400mois/TTL2h/cap4096, purge32 et timestamps≤100 par quota. Propositions techniques configurables, pas quota Resend réel prouvé. Limites IP/admission/timing restent à C.
- Aucun test/processus Python/Chrome retenu après contrôles ; PostgreSQL38028 préservé. Aucun email réel/API Resend/DNS/service/coût/deploy effectué. Après push STOP, Tester/CI renouvelés pour SHA exact ; lot7/PR12 pas terminés.

Dernière vérification pré-gel : garde DBAPI AUTOCOMMIT ajoutée pour rendre explicite Engine transactionnel uniquement. Ciblé commit/rollback initial **7PASS/3FAIL3,78s** (.local-tools/b2-transaction-guard.xml) : les trois tests Connection externe n’utilisaient pas la fixture session nettoyant Account, assertion table vide dépendait de l’ordre ; refus du service déjà effectif. Isolation du fichier corrigée pour supprimer Account privé avant chaque cas, sans source publique touchée. Relance des10cas concernés **10PASS3,37s exit0** (.local-tools/b2-transaction-guard-fixed.xml). Fichier B2 complet final après garde/isolation : **61PASS19,51s exit0**, JUnit `.local-tools/b2-final-flows.xml`. Régression A64 du run124 déjà verte et inchangée. Contrôles Ruff58 et diff revérifiés après ces derniers changements, PASS. Aucun test Python/Chrome retenu.

## Correction B2-F1 cycle1 — prête pour publication/gel

Tester REQUEST CHANGES exactaac7 : Session bind Engine pouvait enrôler une Connection externe via bind_arguments et armer intent au simple commit logique. Ancienne CI43408753657 SUCCESS650backend225,08s/67frontend demeure historique non approbation. Source libérée, seul Developer writer ; reprise effective du même agent après demande propriétaire vers15:54UTC, aucune capacité bloquante observée dans les commandes. Git propre avant correction, PG38028 confirmé et aucun Python/Chrome concurrent.

Restriction technique attribuée : **AccountFlowSession(Engine) dédiée obligatoire**, Session brute refusée avant mutation même bind Engine. Fences publics constructor/get_bind/connection/bind_mapper/bind_table couvrent aussi execute/scalar/scalars et SessionTransaction.connection ; aucune inspection `_connections`/should_commit. Le contrat ne prétend pas protéger contre code serveur arbitraire contournant la classe/driver. Fixture B2 adaptée, A/planning non modifiés ; futur wrapper C devra utiliser la Session dédiée.

Premier ciblé F1/routages **33PASS5,38s exit0**, JUnit `.local-tools/b2-f1-targeted.xml`. Final fichier B2 **89PASS9,93s exit0** (61régressions+28nouveaux), `.local-tools/b2-f1-final.xml`. F1 raw pré-enrôlé create_savepoint/rollback_only ×5fonctions, APIconnection/execute/scalar/scalars/transaction/mapper/table/constructor ×Connection/autreEngine, Session brute et bindassignment ; refus sans mutation ni intent et normalcommit/close/dispatch préservé. Migration locale fixture upgrade/check/base/upgrade/check PASS, source e95c inchangée. Ruff check/format58/diff PASS ; contrats26PASS. A64/B1 preuves réutilisées après diff ; aucun full650/browser répété.

Handoff corrigé [account-flows-handoff.md](../lot-7/account-flows-handoff.md), mission alignée. Gate F1 désormais passée exactb12d : Tester APPROVE107PASS18,07s et CI43458142079 SUCCESS678/67 ; preuve non transférable à C0. Aucun C commencé (son futur scope n'inclut pas les saved endpoints), aucune modification migration/modèle/EmailService/dépendance/route/hosting/source. Aucun email réel/DNS/service/coût/déploiement.

## Attribution C après gate B2

B2 exactb12d APPROVE Tester107PASS18,07s et CI43458142079 SUCCESS678backend197,29s/67frontend, source libérée. Nouvelle mission versionnée docs/lot-7/auth-http-mission.md ; Developer seul writer, pas C implicite avant cette attribution. C0 configuration/CSRF/admission/corpus puis jalons C1sessions et C2parcours email/queue, sans savedAPI/UI/ICS/serve/ops/CI/pins. Prochaine action : premier C0 cohérent testé puis publication/gel pour revue indépendante ; aucun réseau email/service/DNS/déploiement.

## C0 — premier jalon HTTP prêt pour publication/gel

Config finale app/activationfermée, CSRF réel GET, helpers stricts de mutations, admissionPG indépendante/slots2 et corpusDjango6.0 local+notice écrits. Handoff docs/lot-7/auth-http-handoff.md, contrat auth additif C0 seul, migration f61d338ab204 après e95c. Aucun endpoint session/email C1/C2 prétendu livré. Ciblé34PASS5,49s puis finalC0+public61PASS29,88s, JUnit .local-tools/c0-final-public.xml. Migrationupgrade/check/base/upgrade/check incluse sur _test seulement ; aucun réseau email autorisé, aucun worker créé. Ruff check/format65, contrats26, pipcheck/diff PASS. A/B1/B2/pins inchangés vérifiés par diff. Aucun Python/Chrome actif après contrôles, PG38028 conservé. Prochaine action : commit/push C0 puis STOP pour revue ciblée, sans débuter C1/C2 pendant review.

Précision finale C0 : nonce conservé interonglets sans renouvellement, expires_in annonce le TTL réellement restant. Final **62PASS29,61s exit0 (39C0+23public)**, `.local-tools/c0-final-public-ttl.xml`. Retrait d’un import devenu inutilisé, contrôles Ruffcheck/format65 et diff finaux PASS avant publication ; aucun test fonctionnel échoué. Corpus/helper uniquement, setter endpointsC1/C2 encore TODO.

## C0 correction cycle1 — constats groupés

SOURCE RELEASED après REQUEST CHANGES exact35f. F1 fixtureDATABASE_URL=str(URL) masquait password ; CI43462508000 FAILED710PASS/7FAIL180,30s (503PGpasswordauth), malgré62localtrustPASS. F2 corpsWerkzeugdéjàcache>8192 contournaitlimite. Correction minimale : objet database.url conservé en mémoire et contrôle explicite len(raw)>8192→413 avantJSON après get_data toujours borné sur flux neuf. Aucun changement PG/roles/trust/CI/modèle/migration/pins/A/B1/B2. Ciblé8PASS2,91s JUnit .local-tools/c0-cycle1-targeted.xml ; nouvelleCI passwordauth encore requise. Final C0/public **70PASS26,14s exit0 (47C0+23public)**, JUnit `.local-tools/c0-cycle1-final.xml` ; Ruff65/contrats26/diff PASS, source A/B1/B2/modèles/migration/pins inchangée. Aucun Python/Chrome retenu après tests. Prochaine action : commit/push/gel correction4fichiers, puis revue et nouvelleCI password-auth ; pas C1/C2 avant gate renouvelée.
