# Point de reprise RaceAtlas

**Checkpoint UTC 2026-11-13T21:53Z — candidat backend auth complet C2 prêt pour gel, NON APPROUVÉ.** PR12 reste Draft. Une acceptation COMPLETE backend et une CI exacte restent requises ; lot7, UI et V1 ne sont pas terminés.

## Git et prochaine action sûre

Branche **feature/account-authentication**, worktree isolé add4, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12). Parent local/origin **c06b2dc52cc832dee0e5a5548a6c40dbde5deea3**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Le commit contenant ce checkpoint sera le candidat C2 ; transmettre son SHA exact après push. Developer seul writer ; Root PR/notes ignorées, Tester indépendant read-only.

**Prochaine action sûre :** commit/push cohérent, communiquer le SHA puis STOP éditions. Demander une revue d'acceptation **COMPLETE A+B1+B2+C0+C1+C2 du backend PR12**, pas une simple APPROVE C2. Exiger la CI du même SHA et une base à jour avant intégration. [Mission C2](../lot-7/auth-http-email-mission.md), [handoff C2](../lot-7/auth-http-email-handoff.md), [mission globale](../lot-7/auth-http-mission.md). Planning HTTP/ICS/UI attendent intégration auth + mainCI et nouvelle attribution.

| Tâche | État |
|---|---|
| ACC-01 identité/sauvegardes | DONE intégré PR11/mainCI |
| Auth A/B1/B2/C0/C1 | Jalons APPROVE antérieurs ; verdict non transférable |
| C2 routes email/dispatcher/probes | Implémenté,225 ciblés PASS ; acceptation complète/CI TODO |
| Backend PR12 intégré | TODO, PR Draft non fusionnée |
| Planning API / ICS / UI / lot7 complet | TODO, exclus C2 |
| DNS/envoi réel/service/déploiement | BLOCKED autorisation/préconditions, aucun effectué |

## Comportement et limites C2

C1 est conservé : droits COOKIE uniquement, Basic preview permis mais pas identité compte, CSRF/Origin/admission C0 avant KDF.401 passive sans Set-Cookie pour éviter une réponse ancienne effaçant loginB ; réauth403 sans mint. Cookies site host-only/Secure HTTPS/HttpOnly/Lax/Path=/,7jours absolus/24h idle serveur. Corpus appliqué seulement aux nouveaux secrets, Unicode/espaces/NUL exacts.

C2 register/resend/forgot :202 constant pour résultats métier connus/inconnus/limités, file pleine/fermée et panne provider. Aucune promesse envoyé/reçu. Périmètre HTTP400/403/413/429/503 avant lookup, indépendant de l'existence. Confirmation/reset POST avec X-Account-Proof +CSRF, jamais query/JSONtoken ou auto-login. ResetB garde cookieA. IntentNone normal commité ; registration1hash si intent, sinon1dummy après commit/close sous slot.0KDF formes invalides/admission refusée/resend/resetrequest. Pas de temps constant revendiqué.

EmailIntent.account_id privé OPTIONNEL KEYWORD-ONLY, copié depuis Account déjà verrouillé ; operation_id reste quatrième position. Pas de lookup Account après Budget. Legacy sans ID peut dispatcher B2 directement mais pas entrer dans la queue HTTP. Probe worker PG non consommateur : hash/purpose/account/recipient/version/expiry/date de vérification, puis transaction et Session FERMÉES avant provider. DB en panne/preuve obsolète : abandon sans retry.

Dispatcher partagé : **16 pending +1 actif /16 channels /1 worker par processus**. Services B1 isolés par channel, Condition libérée avant probe et provider. Cadence conservatrice0,2s après fin de tentative, donc ≥0,2s entre débuts ; pas garantie quota équipe. Lazy channel : aucun worker pour auth désactivée/incomplète, C0/C1 ou demande sans intent. Close annule pending du channel, conserve les autres, signale un actif bloqué sans hard-cancel ou deuxième worker. Fixtures C0/C1/conftest/C2 ferment runtime avant Engine. Dernier job libéré avant idle/drain ; aucune Session/Connection/Flask app/context dans un job. Development garde ses20messages locaux B1, sans promesse d'effacement physique des strings.

Delete hook après commit/close : cancel_pending(channel,AccountID), jamais email, nouveau compte même email préservé. Autre channel peut garder un job mais son probe le rejette après CASCADE. Delete après probe/provider peut laisser finir un envoi in-flight, dont la preuve est invalide. Pas de tombstone illimité, outbox durable, scheduler ou effacement distant promis. Crash après commit : intent perdu possible, renvoi comme récupération et réservation conservée.

## Preuves exécutées

- C2 premiers11PASS5,79s, étendu31PASS9,18s, complet37PASS11,07s, tous exit0 ; JUnit ignorés `.local-tools/c2-first.xml`, `c2-expanded.xml`, `c2-complete.xml`.
- Final `pytest tests/backend/test_auth_http_email.py tests/backend/test_account_flows.py tests/backend/test_auth_http_sessions.py tests/backend/test_auth_http_foundation.py tests/backend/test_foundation.py tests/backend/test_catalog_options.py -q --tb=short --junitxml=.local-tools/c2-final-seams.xml` : **225PASS44,09s exit0** =37C2+89B2+29C1+47C0+23public. Fixture migration upgrade/check/base/upgrade/check sur `_test` ; migration source inchangée.
- Parcours Development complet, hash-only24h/30min/replay/renvoi/nonoverwrite, cookieA/proofB et révocation deux devices, commitfailure aucune queue ; pending/in-flight/delete/nouvel Account/autre channel ; full/slow/probe/stop/deux apps/cadence/GCrefs/PGidle avant provider/429 sans retry/DBdrop ;1 ou0KDF natif selon périmètre et compatibilité legacy UUID.
- Profils `.local-tools/c2-registration-profiles.jsonl` sans PII :7branches1KDF, premier profil89,26–200,95ms Windows (bootstrap/DB/KDF inclus, hors drain). Un échantillon par branche/run : nonconstant, pas SLA ou capacité Render mesurée.
- Ruff check PASS ; format **70 fichiers conformes** ; contrats **26PASS** ; pipcheck/diff PASS. A/B1/modèles/migrations/pins/source/frontend/serve/ops/CI inchangés vérifiés. Interfaces B2/C1 et nettoyages fixtures seulement. Pas de fullbackend/browser local répété ; vraie pile SDK B1 fake-wire réutilisable après diff.
- Toutes commandes terminées ; dernier inventaire natif aucun Python/Chrome actif, workers de tests fermés. PostgreSQL38028 conservé.

## Gates précédents et historique

C1 exactc06b2dc52cc832dee0e5a5548a6c40dbde5deea3 APPROVE68+9PASS ; CI43508577610 SUCCESS754backend233,70s/67frontend, gardes exactes. C0a2bf APPROVE15PASS11,12s et CI43465480107 SUCCESS725/67. Historique35f : CI43462508000 FAILED710PASS/7FAIL180,30s, str(URL) cachait password malgré62localtrustPASS + cache>8KiB ; corrigés sans assouplir PG/CI, C0CIa2bf a réellement validé password-auth.

B2b12d APPROVE107PASS18,07s/CI678/67 ; B1c79c APPROVE68+10/CI589/67 ; A9dfd APPROVE/CI521/67 restent antérieurs. C1 ancien138PASS65,01s et incident de capacité automatic-review résolu sont conservés dans son handoff. Aucun verdict ne vaut approbation du nouveau SHA ; revue backend COMPLETE obligatoire.

## Environnement et opérations interdites

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, pip via runtime `-m pip --python <venv>`, dépendances déjà installées. PostgreSQL17.11 PID38028 loopback55434, cluster `.local-tools/pgdata-lot2-native`. DeveloperDB `raceatlas_lot2_test` avec opt-in, Tester_review distincte. Pas initdb/reseed/killglobal. Caches Node/Chromium préservés, aucun navigateur requis C2.

AUTH_ENABLED=false par défaut, ENVIRONMENT app effectif, clés CSRF/Rate distinctes vides dans l'exemple, production mock refusée. Resend Free choisi ; `raceatlas.ucthonon.fr` email seul et From futur `RaceAtlas <notifications@raceatlas.ucthonon.fr>` non vérifiés ; URL Render réelle indépendante inconnue. Aucun compte externe/DNS/clé réelle/email/service/coût/remoteDB/deploy/collecte. Premier déploiement après lot8 sous autorisation distincte ; aucune délivrabilité/quotas réels/capacité production établis. Après publication : gel et arrêt, attendre revue complète/CI ; pas de main/merge/UI anticipé.
