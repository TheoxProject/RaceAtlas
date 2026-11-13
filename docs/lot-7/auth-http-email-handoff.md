# ACC-02C2 — candidat backend auth complet, soumis à acceptation

Branche `feature/account-authentication`, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12), parent **c06b2dc52cc832dee0e5a5548a6c40dbde5deea3**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Le candidat est le commit contenant ce handoff, dont le SHA exact sera communiqué après push. Revue d'acceptation **COMPLETE du backend PR12 A+B1+B2+C0+C1+C2** et CI exactes requises ; C1 APPROVE ne se transfère pas. Planning HTTP/ICS/UI restent ultérieurs, lot7 pas terminé.

## Interfaces et fichiers

`auth/email_http.py` expose les cinq POST réels register, confirmation/resend, confirmation/complete, password-reset/request et password-reset/complete sous /api/v1/auth. CSRF+Origin exact, JSON strict8KiB et admission indépendante avant lookup/KDF. Preuve uniquement header **X-Account-Proof**, pas query/JSON ; GET/HEAD ne consomment rien. Les trois demandes mail renvoient exactement **202 {status:accepted}**, sans promesse envoyé/reçu, pour résultat métier connu/inconnu/pending/vérifié/limité, queue pleine/fermée et panne provider. Rejets de périmètre restent400/403/413/429/503 avant lookup, indépendants de l'existence. RequestResult.intentNone normal est commité, pas rollback des limites.

Confirmation/reset réussis204, jamais auto-login ou mutation de cookies. Preuve B vise uniquement B, même si cookie A présent ; test resetB garde A et révoque B. Cookie401 passive et contrôles réauth C1 inchangés. New-secret policy seulement inscription/reset, login existant inchangé. Adresses ASCII expédiables validées avant mutation, password Unicode/espaces/NUL exacts A.

B2 `EmailIntent.account_id` **privé optionnel keyword-only**, copié depuis Account déjà verrouillé. operation_id reste quatrième argument positionnel compatible. Aucun nouveau lookup Account après Budget ou identity_map privée. Un legacy sans account_id garde son dispatch B2 direct après commit mais est refusé comme job HTTP. Aucune migration/modèle/pin changé.

`flows.email_intent_is_active(session,intent)` : lecture non consommatrice du digest domaine-séparé partagé B2, purpose/account/recipient/version/expiry/date vérification ; AccountFlowSession Engine propriétaire, temps DB. Le worker configure timeouts statement3s/lock1s, effectue ce probe PG éphémère puis **ferme sa transaction et Session avant provider**. Erreur DB/preuve obsolète →abandon best-effort sans retry, aucune activation. Pas de FOR UPDATE ou mise à jour dans le probe, pas d'Account lookup du caller sous Budget.

C1 seul changement : après delete commit ET fermeture, `runtime.cancel_pending(account_id)` avec ID copié avant Budget, puis clear des cookies déjà prévu. Pas de cancellation par email : nouveau compte même adresse préservé. Les jobs d'un autre channel peuvent rester en mémoire, mais leur probe rejette aprèsCASCADE. Si delete arrive après probe/début d'appel, envoi in-flight peut finir ; sa preuve demeure invalide. Ce n'est pas une garantie « aucun email après suppression » ou effacement fournisseur.

## Dispatcher et lifecycle

`auth/dispatch.py` : **un worker daemon partagé par processus**, deque16 pending +1 actif, au plus16 channels avec services/Engine propres, aucun Session/Connection/Flask app/requestcontext dans les jobs. Enqueue non bloquant après vrai commit+fermeture. Locks registry/Condition brefs, relâchés avant probe PG ET provider ; un probe lent ne bloque pas enqueue/cancel HTTP.

Cadence monotone conservatrice : au moins0,2s **après fin d'une tentative** avant la suivante, donc au moins0,2s entre débuts, y compris429/erreurs. Attente Condition interrompable par close, aucun retry ou queue externe/outbox secrets. Marge ≤5/s/process, pas garantie quota équipe Resend ou SLA de durée totale B1.

`AuthRuntime.email_service()` construit le service central B1 depuis settings app finaux, sans lecture env contradictoire ou fallback production. Service validé avant lookup. Channel/worker **paresseux au premier intent à enqueue**, pas pour authdisabled/configfermée, C0/C1 ou demande sansintent. Runtime `drain(timeout)`, `close(timeout)` et cancellation explicites ; fermeture avant Engine.dispose dans fixtures C0/C1/conftest et C2. Aucun global callback ne capture l'app Flask. Un worker idle libère son dernier job avant notification du drain ; faibles références intent/channel testées. Development conserve ses20messages locaux B1 intentionnellement, pas de promesse d'effacement physique des strings Python.

Close annule pending du channel, conserve autres channels, dernier channel demande arrêt global. Join borné retourne False si provider actif encore bloqué ; pas hard-cancel. Aucun second worker pendant arrêt incomplet, tests libèrent ensuite la barrière et ferment réellement. Cap channels fermé au17e, sans worker supplémentaire. Un hook atexit tente arrêt borné, pas garantie de livraison/durabilité. Crash après commit peut perdre intent ; renvoi comme récupération, budget réservé conservé.

## KDF et délais

B2 fait un hash natif siintent ; sinon HTTP appelle **dummy_verify seulement intentNone après commit/close**, slotHTTP conservé. Aucun doubleKDF : sept branches new/pending/confirmed/future/limited/budget/capacity testées chacune exactement1KDF natif, vrai hash ou verify dummy. Forme invalide/admissionHTTP refusée0, resend/resetrequest0. Commit/KDF/stockage inattendu ne devient pas faux202. Pas changement du corpus/hash de password existant.

Métadonnées locales `.local-tools/c2-registration-profiles.jsonl` : un échantillon par branche/run, aucune adresse/clé/token/DSN. Premier profil normal (requête inclut bootstrap/DB/KDF, hors drain)89,26–200,95ms sur ce poste Windows ; nonconstant et insuffisant pour garantie statistique/Render. Barrières provider/probe démontrent que HTTP ne les attend pas, pas un seuil de performance inventé. Aucun RSS/capacité Free/délivrabilité mesuré.

## Vérifications exécutées

Python3.12.14 cache `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, PG17.11 PID38028/55434 confirmé et aucun Python/Chrome concurrent au départ. Seulement `raceatlas_lot2_test` avec RACEATLAS_DISPOSABLE_DB=1 ; reviewer/DBdistantes intactes. Tous appels réseau email interdits, SDK B1 source inchangée. Tests simulent provider sans socket.

- Premier `pytest tests/backend/test_auth_http_email.py -q --tb=short --maxfail=3 --junitxml=.local-tools/c2-first.xml` : **11PASS5,79s exit0**.
- Étendu `.local-tools/c2-expanded.xml` : **31PASS9,18s exit0**.
- C2 complet `.local-tools/c2-complete.xml` : **37PASS11,07s exit0**.
- Final `pytest tests/backend/test_auth_http_email.py tests/backend/test_account_flows.py tests/backend/test_auth_http_sessions.py tests/backend/test_auth_http_foundation.py tests/backend/test_foundation.py tests/backend/test_catalog_options.py -q --tb=short --junitxml=.local-tools/c2-final-seams.xml` : **225PASS44,09s exit0 (37C2+89B2+29C1+47C0+23public)**. Fixture migration upgrade/check/base/upgrade/check sur `_test`, source migration inchangée.
- `python -m ruff check raceatlas migrations tests/backend` PASS ; `python -m ruff format --check raceatlas migrations tests/backend` **70 fichiers conformes** ; `node --test tests/contracts/contracts.test.mjs` **26PASS** ; runtime pip `--python <venv> check` PASS ; `git diff --check` PASS. Dernier inventaire natif aucun Python/Chrome actif, tous workers de tests fermés avant Engine.dispose.

Preuves : parcoursHTTP réel register→Development→proof→login→forgot/reset→revoke2devices ; hashonly24h/30min/replay/renvoi/confirmednonoverwrite ; cookieA/proofB ; framebody/header/methodes ; commitfailure aucunequeue ; defaultcooldown et budget conservés ; legacy4eposition UUID. Worker16+1/16channels/2apps/cadence/closeone/stopincomplet, zero retry429, DBpannedrop, invaliditépurpose/recipient/account/version/expiry/consommation/remplacement, commit→delete→enqueue, pendingdelete/nouvelAccountmêmeemail/inflight/authpurge, autrechannelstaledrop, Condition relâchée au probe et transaction PG idle avantprovider, references libérées, KDF natif et profils.

Contrat `contracts/auth.openapi.json` additif C2, catalogue1.0.0 inchangé. Modèles/migrations/pins/source/frontend/serve/ops/CI inchangés. A primitives et B1 vraisSDKfake-wire réutilisables après diff ; B2/C1/C0 seams rejoués à cause petits changements. Pas de fullbackend/browser local à chaque détail ; CI et Tester doivent encore fournir acceptation complète exacte.

## Historique et gates

C1 exactc06b APPROVE68+9PASS, CI43508577610 SUCCESS754backend233,70s/67frontend avec gardes. C0a2bf APPROVE15 et CI43465480107 SUCCESS725/67 ; historique35f FAILED710/7 (URLstr masquait password) conservé, objetURL et bodycache8KiB corrigés sans assouplir PG. B2b12d APPROVE107 et CI678/67, B1c79c APPROVE68+10 et CI589/67, A9dfd APPROVE/CI521/67 restent preuves antérieures, pas verdict du nouveau SHA.

Au gel : STOP éditions et demander revue COMPLETE backend PR12, pas simple APPROVE C2. Aucun vrai email/ResendAPI/DNS/clé/compte/service/coût/remoteDB/deploy/collecte. Sous-domaine futur raceatlas.ucthonon.fr/From non vérifiés, URL Render réelle inconnue, premier déploiement après lot8 sous autorisation distincte. PlanningAPI/ICS/UI suivent seulement intégration auth + mainCI ; lot7/V1 pas déclarés terminés.
