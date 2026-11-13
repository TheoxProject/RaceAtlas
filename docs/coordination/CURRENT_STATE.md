# Point de reprise RaceAtlas

**Checkpoint UTC 2026-11-13T21:10Z — C1 prêt pour publication et revue intermédiaire, non approuvé.** PR12 reste Draft ; C2 et acceptation complète auth restent à faire. Aucun déploiement ou email réel.

## Git et prochaine action sûre

Branche **feature/account-authentication**, worktree isolé add4, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12). Parent local/origin **a2bf1d64cca54a2c0ae957b6bec62057e3299d47**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Le commit contenant ce checkpoint est le nouveau candidat C1 ; son SHA exact est transmis après push. Developer seul writer suivi ; Root PR/notes ignorées, Tester futur read-only.

**Prochaine action sûre :** commit/push du C1 cohérent, communiquer SHA exact puis STOP éditions pour revue C1 et CI de ce SHA. Ne pas commencer C2 ou créer un nouveau head pendant ces contrôles. [Mission HTTP](../lot-7/auth-http-mission.md), [handoff C1](../lot-7/auth-http-sessions-handoff.md), [handoff C0](../lot-7/auth-http-handoff.md).

| Tâche | État |
|---|---|
| ACC-01 identité/sauvegardes | DONE intégré PR11/mainCI |
| Auth A primitives/sessions | Jalon APPROVE9dfd ; minihelper réauth C1 à revoir |
| Email B1 | Jalon APPROVEc79c, inchangé C1 |
| Preuves/limites B2 | Jalon APPROVEb12d, inchangé C1 |
| HTTP C0 config/CSRF/admission/corpus | Jalon APPROVEa2bf +CI725/67 |
| HTTP C1 sessions/réauth/change/delete | Implémenté,138ciblésPASS ; revue/CI nouveau head TODO |
| HTTP C2 register/confirmation/reset/queue | TODO, plan uniquement, non attribué |
| UI/planning HTTP/ICS/acceptation lot7 | TODO, exclus du C1 |
| DNS/envoi réel/service/déploiement | BLOCKED autorisation/préconditions, aucun effectué |

## Comportement C1 et interfaces

Login/me/logout courant/logout-all/passwordchange/delete sont réels Flask→PG, droits COOKIE uniquement ; Basic de preview conservé mais ne donne aucun droit compte, Bearer/actor/user_id non acceptés. CSRF/Origin exact/JSON8KiB/slots2/admission persistante C0 réellement branchés avant KDF. AccountFlowSession dédiée, Account lock et état frais, commit/fermeture avant réponse/cookies. A nouvelle primitive reauthenticate sans mint ; ReauthenticationFailed hérite AuthenticationFailed en conservant le message interne. Session invalide401 ; currentpassword faux après session valide403 sans révoquer.

**401 passive ne modifie aucun cookie/nonce**, révision du plan initial pour éviter qu’une réponse ancienne efface loginB récent. GETcsrf→login remplace cookie résiduel malformé/périmé ; login ne requiert pas que l’ancien bearer soit valide. Clear seulement sur succès explicites logout/global/change/delete après commit ; pas d’auto-login. Deux actions explicites login/logout simultanées ne sont pas ordonnées magiquement.

Cookie site host-only/Secure HTTPS/HttpOnly/Lax/Path=/, __Host-raceatlas-session ou raceatlas_session_dev uniquement loopback HTTP local/test. MaxAge/Expires≤7jours absolus, idle24h serveur, GETme n’étend pas le cookie. Corpus nouveaux secrets seulement ; legacylogin inchangé, Unicode/espaces/NUL exacts. Profile propre id/email, aucune session/emailproof JSON/query/log/localStorage.

Delete réauth Account→Budget→quota, own Account CASCADE credential/sessions/challenges/SavedEntry, purge seuls HMAC B2 de l’adresse ; budget global/autrui/source/epoch préservés, admission conservée TTL logique1h/purge opportuniste. Pas de garantie effacement physique exact à TTL ni données fournisseur. C2 ajoutera queue/annulation/validation inflight, rien de cela implémenté ici.

## Preuves actuelles

- Premier C1 **22PASS15,99s**, JUnit `.local-tools/c1-first.xml`, avant révision401 passive ; historique, pas verdict final.
- C1 révisé **27PASS18,12s**, `.local-tools/c1-expanded.xml`, purge/NOWAIT/concurrence/401retardée.
- Final `pytest tests/backend/test_auth_http_sessions.py tests/backend/test_auth_sessions.py tests/backend/test_auth_http_foundation.py tests/backend/test_foundation.py tests/backend/test_catalog_options.py -q --tb=short --junitxml=.local-tools/c1-final.xml` : **138PASS65,01s exit0**,29C1+39A sessions+47C0+23public. Fixture migrations upgrade/check/base/upgrade/check sur `_test` ; migration source inchangée.
- Cookiejars deux users/devices,401/403 et récupération, rotationCSRF/Origin/Basic/Bearer, cachedbody413 avantKDF, legacycommon/newcommon/UnicodeNUL, commitfailure pas de cookie prématuré, purge/budgets/admission/epoch, Account NOWAIT au moment cookie et vraie course HTTP change/read PG bloqué observé. En contention le read peut refuser401/503 ; contrôle final401 obligatoire, pas relâchement de permission.
- Ruff check PASS ; format **67fichiers conformes** ; contrats **26PASS** ; pipcheck/diff PASS. Contrat auth C1 additif valide réponses réelles, catalogue1.0.0 intact. Test C0 adapté seulement pour retirer assertion 'un seul path' devenue incompatible avec extension additive.
- Aucun fullbackend/browser local répété. A sessions rejouées car helper modifié ; modèles/migrations/pins/B1/B2 inchangés par diff vérifié. No worker, routes email ou savedAPI ajoutés.

## Gates précédents et historique conservé

A exact9dfd8087820608f613e5915a1839800357e1ffb9 APPROVE ciblé, CI43389431747 SUCCESS521/67 ; B1 c79c557e32fed3fd56c85ed1ce786f0bd46fde04 APPROVE68+10 et CI43404533408 SUCCESS589/67. B2 corrigé b12d2c37405ac754ee2331b95c696b3bf71c5c47 APPROVE107PASS18,07s, CI43458142079 SUCCESS678/67. Ces verdicts ne se transfèrent pas au nouveau C1.

C0 initial35f123db2ec1741e1509630a2803d29d6b873251 : CI43462508000 **FAILED710PASS/7FAIL180,30s**, fixture str(URL) cachait password malgré62localtrustPASS ; autre finding cacheWerkzeug>8KiB. Corrigés sans changer PGtrust/permissions/CI : URLobject conservé en mémoire et borne explicite rawlen. C0 corrigé exacta2bf1d64cca54a2c0ae957b6bec62057e3299d47 APPROVE15PASS11,12s, CI43465480107 **SUCCESS725backend225,68s/67frontend** avec passwordauth réelle et gardes exactes. Preuve locale trust n’est pas relabellée passwordauth.

Dernière interruption C1 : une commande pipcheck/processus NON exécutée car automatic approval review indisponible pour limite d’utilisation, pas rejet sécurité. Reprise explicitement demandée, même agent/WIP ; contrôle natif ensuite approuvé exit0, pipcheckPASS/aucun PythonChrome actif. Aucun changement d’agent/modèle ou retry en boucle,138tests verts non relancés.

## Environnement et limites

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, pip via runtime `-m pip --python <venv>`, dépendances déjà installées et inchangées. PostgreSQL17.11 PID38028 loopback55434, cluster `.local-tools/pgdata-lot2-native` préservé. DeveloperDB `raceatlas_lot2_test` avec opt-in ; Tester_review distincte. Dernières commandes toutes terminées, aucun Python/Chrome actif au contrôle natif. Pas initdb/reseed/killglobal.

AppConfig final ENVIRONMENT fait autorité ; AUTH_ENABLED=false par défaut, clés CSRF/Rate fortes distinctes vides dans exemple, aucune activation production mock. Resend Free choisi ; `raceatlas.ucthonon.fr` email seul, From futur `RaceAtlas <notifications@raceatlas.ucthonon.fr>` non vérifié, URL réelle Render indépendante inconnue. Aucun DNS/compte externe/clé réelle/email/service/coût/remoteDB/deploy/collecte ; premier déploiement après lot8/candidatV1 sous autorisation distincte.

Plans ignorés C1/C2 préparatoires seulement. C2 prévu plus tard : preuveheader, routesregister/resend/confirm/reset,1KDFregistration équilibré, dispatcher partagé Queue16/worker1 cadence0,2s/channels, champprivéaccountid B2 et contrôle PG éphémère avantprovider autorisés seulement lors attribution C2. Aucun code C2 présent. Après publication C1 : gel et attente de review/CI puis libération formelle.
