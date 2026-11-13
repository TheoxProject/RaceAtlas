# ACC-02C1 — sessions HTTP, réauthentification et suppression

Branche `feature/account-authentication`, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12), parent **a2bf1d64cca54a2c0ae957b6bec62057e3299d47**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Le candidat est le commit contenant ce handoff, SHA exact communiqué après push. C1 reste un jalon : C2 email/queue puis acceptation backend complète sont nécessaires ; ni PR12 ni lot7 terminés.

## Livré

`raceatlas/auth/sessions_http.py`, raccord minimal dans `http.py`, petite primitive dans `auth/__init__.py` et sous-type dans `errors.py` ; tests HTTP et contrat auth additif. Aucun changement de modèle, migration, pins, B1/B2, catalogue, frontend, serve/ops/CI ou planning API.

| Route | Corps JSON exact | Résultat |
|---|---|---|
| POST /api/v1/auth/login | email, password |200 profil propre +preuve CSRF, bearer en cookie seulement |
| GET /api/v1/me | aucun |200 profil propre ou401 passif |
| POST /api/v1/auth/logout | objet vide |204, seule session courante révoquée |
| POST /api/v1/auth/logout-all | current_password |204, toutes sessions révoquées |
| POST /api/v1/auth/password/change | current_password, new_password |204, secret changé et toutes sessions révoquées |
| DELETE /api/v1/me | current_password |204, données privées propres supprimées |

Identité issue uniquement du cookie opaque et `resolve_session` dans la même `AccountFlowSession` ; aucun actor/user_id ou Authorization alternatif. Le header Basic du middleware de preview reste permis mais n'accorde aucun droit compte. Deux comptes/deux appareils isolés ; pas de session supplémentaire pour réauth. Profil minimal id opaque/email du compte courant, pas token en JSON/query/log ou stockage JS.

## Pipeline et cookies

Configuration/fermeture C0 conservées. Mutation : Origin exact+CSRF avant JSON strict8KiB, slot2/process, admission courte persistante indépendante commitée/fermée, puis AccountFlowSession avec statement3s/lock1s locaux. Account lock/fraîcheur Auth A, commit puis fermeture Session avant publication de cookies/réponse. Admission reste comptée sur échec métier. Pas d'I/O provider ou queue.

`reauthenticate(session, token, current_password)` retourne le compte persistant verrouillé sans mint. `ReauthenticationFailed` hérite AuthenticationFailed et conserve son message exact pour compatibilité des callers A ; HTTP403 spécifique seulement après session valide et mauvais current_password. Session absente/périmée/révoquée/malformée401. `change_password` réutilise le helper, un seul verifyKDF. HTTP vérifie d'abord la session puis blocklist du nouveau secret avant écriture ; login existant conserve strictement la politique A, même pour mot du corpus. Unicode/espaces/NUL restent exacts.

Login réussit indépendamment d'un ancien cookie périmé après GETcsrf valide : nouveau bearer cookie puis nonce/CSRF tournés après commit. Cookie __Host-raceatlas-session HTTPS/Secure/HttpOnly/Lax/Path=/ sans Domain ; nom raceatlas_session_dev seulement HTTP loopback local/test. Expires/MaxAge≤7jours absolus serveur, idle24h reste contrôlé DB ; GETme ne renouvelle pas l'expiration client. Cookie site, jamais domaine email. Succès explicites logout/global/change/delete effacent session+nonce aux mêmes attributs après commit, aucun auto-login.

**Révision technique du plan initial : toute401 passive ne modifie AUCUN cookie/nonce.** Une réponse GETme ancienne peut arriver après loginB dans un autre onglet ; un Set-Cookie expirant aurait effacé B. Les cookies résiduels restent remplaçables par GETcsrf→login ; C0 lie correctement les proofs à une valeur43 périmée ou à la liaison vide d'une valeur malformée. Mauvaise réauth403 ne vide rien non plus. Test401 retardée pendant loginBob : aucun Set-Cookie tardif et profil Bob conservé. Cela ne garantit pas l'ordre de deux actions explicites login/logout volontairement concurrentes.

Suppression : réauth/Account d'abord, capturer adresse, Budget singleton, supprimer les seuls HMAC EmailAddressQuota de cette adresse, deleteAccountCASCADE credentials/sessions/challenges/SavedEntry ; aucun nouvel Account verrouillé après Budget. UTF8 de l'adresse pour legacyUnicode (ASCII B2 inchangé). Compteurs globaux d'envoi, autre compte/source/epoch et admission HTTP conservés. Admission a TTL logique1h, purge opportuniste32, pas effacement physique instantané promis. C2 ajoutera annulation queued/inflight invalide ; aucune queue présente à C1.

## Preuves exécutées

Python3.12.14 cache `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, PG17.11 PID38028/55434 confirmé, aucun Python/Chrome concurrent avant premier run. Uniquement DB `raceatlas_lot2_test` avec opt-in ; Reviewer_review/distantes inchangées. Réseau HTTP email interdit en fixture.

- Premier bloc `pytest tests/backend/test_auth_http_sessions.py -q --tb=short --maxfail=3 --junitxml=.local-tools/c1-first.xml` : **22PASS15,99s exit0**, avant révision de la401 passive.
- Bloc révisé `.local-tools/c1-expanded.xml` : **27PASS18,12s exit0**, cookies résiduels/récupération et401 retardée, purge, vraie course HTTP et NOWAIT avant cookie.
- Final `pytest tests/backend/test_auth_http_sessions.py tests/backend/test_auth_sessions.py tests/backend/test_auth_http_foundation.py tests/backend/test_foundation.py tests/backend/test_catalog_options.py -q --tb=short --junitxml=.local-tools/c1-final.xml` : **138PASS65,01s exit0 (29C1+39A sessions+47C0+23public)**. Migration fixture upgrade/check/base/upgrade/check sur `_test`, migration source inchangée.
- `python -m ruff check raceatlas migrations tests/backend` PASS ; `python -m ruff format --check raceatlas migrations tests/backend` **67 fichiers conformes** ; `node --test tests/contracts/contracts.test.mjs` **26PASS** ; runtime pip `--python <venv> check` PASS ; `git diff --check` PASS.

Cas significatifs : cookiejars réels deux utilisateurs/deux appareils, Secure production/loopback/host-only/expiration, CSRF préauth/auth/rotation et Origin/Basic/Bearer, JSON/injection actor/cache oversize avant KDF, admission durable avant coûteux, legacycommon/newcommon et UnicodeNUL exact,401/403/no mint, rollback/commitfailure sans cookie prématuré, logout seul/global/change, scopepurge/epoch/budgets/admission, cookies observés après release Account NOWAIT. Course HTTP réelle changePassword sous Accountlock, secondGETme bloqué PG observé puis refusé (401 ou503 de timeout borné admis en contention, contrôle final401 obligatoire). Session clôturée avant réponse, pas de raw ORM détaché.

`contracts/auth.openapi.json` étendu C1, réponses réelles validées. Un seul ajustement C0 nécessaire : remplacer l'assertion 'un seul path' par présence du path CSRF, puisqu'une extension additive C1 est désormais attendue ; aucun attendu de sécurité C0 relâché. Catalogue OpenAPI1.0.0 intact. Nouvelle CI/revue SHA exacte requises ; aucune campagne backend/browser complète locale répétée.

## Historique et suite

C0 initial35f : CI43462508000 FAILED710PASS/7FAIL180,30s, fixture str(URL) masquait password malgré62localtrustPASS ; corps cache8KiB également corrigé. C0 correctif exacta2bf : Tester APPROVE15PASS11,12s, [CI43465480107](https://github.com/TheoxProject/RaceAtlas/actions/runs/43465480107) SUCCESS725backend225,68s/67frontend avec vrais identifiants PG CI, gardes exactes. Ce gate ne vaut pas verdict C1. B1/B2 chemins inchangés réutilisés après diff ; A sessions rejoués car minihelper modifié.

Après publication STOP pour revue C1 et CI du SHA exact avant C2. C2 reste plan ignoré : register/resend/confirm/reset, proofheader, worker/queue et équilibrageKDF non implémentés. Pas de provisionnement UI/CLI contournant vérification : credentials vérifiées créées uniquement dans fixtures de tests. Pas savedAPI/ICS/UI, aucun domaine vérifié, URL réelle Render encore inconnue, ni compte externe/DNS/clé réelle/email/service/coût/déploiement/collecte.

Interruption avant publication : contrôle pipcheck/processus non exécuté une première fois car automatic approval review indisponible pour limite d’utilisation, pas décision de sécurité. Après reprise explicite du propriétaire, même Developer/WIP conservé, nouveau contrôle natif approuvé exit0 : pipcheck PASS, aucun Python/Chrome actif, HEADa2bf/WIP confirmés. Aucun retry en boucle, aucun changement d’agent/modèle ni relance des138tests verts.
