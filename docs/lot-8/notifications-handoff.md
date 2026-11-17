# N2 final — handoff N2B2 navigateur

17 novembre 2026, 13:50 UTC. PR16, `feature/notifications-interface`, base014bda ; avant publication e5ecbb127ff30f90d61f176f94fce4a2304eea41. SHA final envoyé au Coordinateur après push, puis STOP éditions. Demander acceptation COMPLÈTE N2A+N2B et integrated exacte ; aucun ancien APPROVE n’est transféré au candidat.

## Changements et preuves

`tests/backend/test_notifications_ui_e2e.py` : deux scénarios React compilé→Flask→PG_test. Vrais synchronize synthétiques, SourceRecord retrouvé par provider/key exact ; scopes liés aux labels et règles de l’observation connue, jamais à l’ordre SQL/DOM. Alice sauvegarde deux scopes planned/registered, Bob le scopeB interested ; mobile utilise interested/completed.26imports réels créent52notificationsAlice/26Bob,50affichées ; ACK sans charger suite enregistre52read_at, Bob reste26. NouveauSync : Alice2/Bob27 ; retrait seulscopeA, réajout nouvelle incarnation/baseline27, puis nouveauSync Alice3 dont une seule scopeA. Aucune insertion PN de préparation. Mobile : calendrier décembre horsfiltre, vrai import absent→to_verify (pas cancelled), ACK clavier puis restauration réelle→deux nouvelles non lues ; retrait exact/autrui préservé. Carte/Summit60°10s/DEM>100, caméra/Mapnode/filtres/périodes et focus conservés.

`.github/workflows/ci.yml` : uniquement deux PNG connus ajoutés à la copie failure avec contrôle fichier régulier/non-symlink, préfixe notifications-, rétention1jour conservée. Captures vues réellement : `.local-tools/notifications-ui-screenshots/desktop.png` (52nouveautés, avant/après nom/dates/deuxscopes) et `mobile.png` (390px, présence à vérifier/source/ACK, sans overflow visible). Le test vérifie aussi dernier item accessible par scroll et Tab dans dialog.

## Commandes observées

Venv `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Variables : TEST_DATABASE_URL=`postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test`, RACEATLAS_DISPOSABLE_DB=1, PLAYWRIGHT_BROWSERS_PATH=`C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`.

- `python -m pytest tests/backend/test_notifications_ui_e2e.py -q --tb=short --junitxml=.local-tools/ops-n2b2-browser-initial.xml` :2FAIL8,382s avant navigateur, fixture supposait le titre seul au lieu du raw_label parsé comprenant les conditions. Correspondance corrigée sans ordre SQL/DOM.
- Même commande, JUnit `ops-n2b2-browser-labels.xml` :2FAIL37,99s. Explorer ouvert interceptait Summit ; attente «0 nouveauté» erronée, composant affiche «0 nouveautés». Mobile avait déjà fait Sync/ACK204/GET200. Parcours corrigé par fermeture/réouverture normale, pluriel attendu corrigé ; aucun produit modifié.
- Même commande, JUnit `ops-n2b2-browser-controls.xml` : **2PASS96,13s**, session9397 exit0. Pas retry aveugle : chaque reprise suit le défaut de harnais identifié et conservé ci-dessus.
- `python -m ruff check raceatlas migrations tests/backend ops/ci_selection.py` PASS ; `python -m ruff format --check raceatlas migrations tests/backend ops/ci_selection.py` PASS101fichiers. `git diff --check 014bda3480d0f8c0233f8e6f68d0ae82886b83db` PASS, contrôle range renouvelé après commit.

Production frontend/API/source/auth/DB/ICS/pins et sélectionCI inchangées par rapport à e5 : preuves ciblées N2A et N2B1 réutilisées explicitement, pas full1017 local ni rebuild du dist d9/e5 byte-identique. Test admission_clock qualifié e5 conservé : pauses61s explicites entre phases humaines, limites20/60 et protocoles CSRF→GETme mêmeproof→opération intacts, clocks session/CSRF/DB/RAF indépendantes. PG9780b806, `_review` non utilisée ; tous runtimes fermés avantEngine.dispose, aucun Python/Chrome/commande pending au gel.

Limites : tests offline/synthétiques, pas performanceSLA ni délivrabilité, aucun email/DNS/service/déploiement/DB distante/liveFFC. CI e5 development1017/138 et APPROVE ciblé sont historiques ; Root doit inspecter le nouveau head et demander Tester N2complet+integrated avant fusion.

---

# N2B1 — handoff correction CI admission cycle1

17 Nov 2026 13:24:18 UTC. PR16/feature/notifications-interface/base014bda ; HEAD/origin avant publicationd9d182dc2fa4e87e0bfcca80bd26b72c4ecc84e4, SHA corrigé communiqué au gel. APPROVE ciblé unit d9 historique archivé `.local-tools/tester-report-notifications-n2b1-initial-d9.md`. Gate CI44088350671 FAIL1/1015PASS355,66s +138frontendPASS conservé : vieuxbrowser saison Alice/Bob finit en GETme429, bouton Scope2 absent, pas panneGPU démontrée.

Logs job134056681973 lus par connecteur GitHub et décolorisés ANSI pour compter :51requêtes privées,21GETme13:01:48→13:02:38UTC =17×200+3×401 admis puis429. Admission read est AVANT auth ;20admissions/50s atteignent limite peer20/min, global60 non atteint. Pas doublon auto démontré, aucune suppression d’attestation ni optimisation/réglage runtime.

## Changement borné

Seulement `tests/backend/test_accounts_ui_e2e.py` : fixture admission_clock non autouse (patch scoped de raceatlas.auth.admission._now, thread-safe), assertion identité auth._now globale intacte. Test HTTP garde policy20/60 et prouve refus/récupération de fenêtre glissante, sans prolonger le refus. Ancien browser attend pipeline fini aprèsAlice, puis pause61svirtuelles avant phaseBob. Aucun sleep réel, clocks session/CSRF/DB/DateProxy/RAF ou timeout/pitch/caméra/identité/filtres changé ; aucune purgequota entre phases.

Métadonnées statut/count seulement par phase et assertions ≤20/zéro429 ; aucun header/body/query/proof/token/accountID enregistré. Pause modélise deux parcours humains séparés ; elle n’efface pas le besoin d’UI honnête429 en production. Helper réutilisable N2B2 après nouvelle attribution, aucun vraiSync nouveau ici.

## Commandes et résultats

Venv/caches existants, TEST_DATABASE_URL=postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test ; RACEATLAS_DISPOSABLE_DB=1 ; PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers. Compilé frontend d9 courant réutilisé après diff nul, pas rebuild/réinstall :

1. `pytest tests/backend/test_accounts_ui_e2e.py -k browser_admission_clock -q --tb=short --junitxml=.local-tools/ops-n2b1-ci-admission.xml` : **1PASS9,85s**.20×401(admis),429, encore429à59s/bucket20stampsinchangés, puis401admisà61s ; mêmes limites.
2. `pytest tests/backend/test_accounts_ui_e2e.py -k test_season_scope_actions_map_two_accounts_outside_public_filters -q --tb=short --junitxml=.local-tools/ops-n2b1-ci-browser.xml` : **1PASS55,97s**, UNrun. Sorties phases :Alice14×200+3×401, Bob5×200, pausevirtuelle61s/zéro429. Anciennes assertions caméra60°/10s/DEM>100 et sourceprivée/acteurs/scopes/périodes conservées. Aucun rerun jusqu’auvert.
3. Ruff check et format --check raceatlas migrations tests/backend ops/ci_selection.py : **PASS100** ; range git diff --check base014..HEAD avant/aprèscommit. Pas full1016local, unit frontend71+2sondes/lint/build d9 réutilisés après code byte-identique.

Artefacts ignorés :ops-n2b1-ci-admission.xml,ops-n2b1-ci-browser.xml,ops-n2b1-ci-browser-phases.json,ops-n2b1-ci-failure-analysis.json ; capture synthétique season-desktop existante, aucune QA N2B2 prétendue. PG9780/55434b806 confirmé natif ; _review réservée, tous tests/serveur/browser/runtime/listeners fermés avantEngine.dispose, aucune commande pending. Frontend/production/API/authpolicies/source/DB/ICS/schema/CI/deps IMMUTABLES.

Au push : GEL/STOP pour revue renouvelée exacte+CI. Pas d’APPROVE copié, N2B2/Sync/390 restent TODO après gate. Aucun email réel/liveFFC/DNS/service/remoteDB/deploy/achat/tag.

## Historique premier jalon d9

# OPS-N2B1 — handoff WIP contrôleur/rendu

17 novembre 2026, 12:56 UTC. PR16 / feature/notifications-interface / base014bda, HEAD/origin avant publication8581b5b23b52d5c884583eff2e8d84aebea06a35. SHA intermédiaire communiqué au gel. N2A APPROVE6943153896/CI44048466660development1016/118 historique, aucune approbation UI copiée.

Fichiers frontend seulement : privateAccount.js, SeasonPanel.jsx/test, nouveaux notifications.js/test, NotificationsPanel.jsx/test, notificationsController.test.js, account.css. Backend/API/source/auth/planning/ICS/DB/deps/CI inchangés ; ni captures ni navigateur encore.

Contrôleur : état notifications/reset avec contexte, allowlist query limit50/cursor normalisés RAM, validation réponse2MiB/texte16KiB/count sûr/composites. loadSeason coalesce un listTask ScopeSaveActions actif puis lit entries→notifications sous opération/proof commune ; acteur/epoch d’appel et ticket avant await initial, assertCurrent avant fetch et after await, publication/catch/finally gardés. ACK EXACT204 puis GET fresh, compteur jamais déduit de page ni forcé0 ; si ACK confirmé maisGET échoue message confirmé/counter inconnu distinct du POST inconnu, pas retry. Retrait204 enlève ses seuls messages et invalide count/cursor horspage avant relecture ; statut seul ne supprime pas suivi.

SectionFR accessible : compteur global, lues/nonlues, vide/chargement/erreur, Actualiser/Charger suite/Marquer toutes. Source payload contient déjà les seules clés changed via record_change ; comparaison structurelle défensive fonctionne aussi pour full snapshots. Faits lisibles, groupes de conditions/rawlabels corrélés, pas admissibilité personnelle/annulation depuis manque/JSON brut/IDs compétition DOM. Liens http(s) sûrs/noreferrer, instants de constat vs dates civiles distingués. Carte et ICS conservés.

## Exécution avant interruption, sorties réconciliées17nov12:54

Depuis frontend, Node24/caches existants, commandes NATIVES :

- `node node_modules/vitest/vitest.mjs run src/notificationsController.test.js src/privateAccount.test.js src/season.test.js src/accountSensitive.test.js` : **47PASS3,32s** (dernier contrôleur après garde avantHTTP).
- `node node_modules/vitest/vitest.mjs run src/SeasonPanel.test.jsx src/NotificationsPanel.test.jsx src/AccountPanel.test.jsx src/App.test.jsx` : **20PASS11,09s**. Vrai montage React ScopeSaveActions derrière dialog+SeasonPanel coalesce sans boucle ; erreurs/états/provenance/rendu et coutures publiquesApp.
- Préliminaire `node node_modules/vitest/vitest.mjs run src/notifications.test.js src/NotificationsPanel.test.jsx` : **7PASS3,56s**, dont4utilitaires (allowlist/limites/diff/conditions) ;3composants recoupés avec20, pas somme de tests uniques.
- `node node_modules/eslint/bin/eslint.js . --max-warnings 0` : PASS ; `node node_modules/vite/bin/vite.js build` : PASS4,44s, avertissement chunk>500KiB connu conservé, aucun changement de seuil/timeout/bundler.

Première tentative sandbox sur4fichiers : **0test/4fork-start errors**, NONPASS. Passage natif a exécuté les tests sans changer Vitest ; tentative CSS mauvais cwd échouée sans écrire puis chemin corrigé. Préliminaires3/13/34PASS existent mais recoupés avec derniers groupes, pas additionnés. Pas de JUnit Vitest configuré : preuve = sorties exec conservées/relevées dans `.local-tools/ops-n2b1-observed-checks.md`, sessions68967/98162 terminées exit0. Source WIP inchangée entre ces résultats et reprise, aucune passe relabellisée/cache.

Au17nov12:54 : aucun Python/Chrome/test concurrent, Nodes externes identiques intacts. Aucun PG/test/browser exécuté à reprise, _review réservée ; vérifier PG9780/55434b806 avant futur _test. Pas1016backendlocal/reinstall ni changement source/DB.

## Limites et prochain gate

GEL COURT N2B1 : revue ciblée indépendante lease/store/orchestration/rendu puis release. Ce n’est ni acceptation finaleN2 ni preuve visuelle/navigateur ; N2B2 reste TODO avec vrai synchronize fixture→UI/count/ACK/newchangeunread, deux acteurs/scopes/retrait/réajout/offpage/mobile390/contexte public et captures inspectées. CI courante du WIP à suivre ; finalN2 nécessitera acceptation complète/integrated/main. STOP éditions après push, aucun acte externe réel.

## Historique N2A

# N2A-F2 — handoff correction cycle2

17 Nov 2026 08:37:57 UTC. PR16 / feature/notifications-interface / base014bda ; HEAD/origin avant publicationa4fce6bdadcd9f25a060c395c0f214bb5cb09884, SHA exact communiqué au gel. F1 CLOSED, a4f REQUEST CHANGES F2P2 (dates offset extrêmes v1/v2 lèvent OverflowError, GET500sansSQL). Rapport archivé `.local-tools/tester-report-notifications-n2a-initial-a4f.md`, CI44046262877development1004/118 historique ne valide pas le futurSHA.

Seul changement runtime : ajouter `OverflowError` à l’exception du bloc validation PURE de `parse_query`, sans modifier timestamp global ni capturer des erreurs SQL/opérationnelles. Les débordements UTC deviennent NotificationQueryError/HTTP400 générique avant touteSQL ; Date UTC canonique valide reste acceptée. Codec v2≤768/v1compat/HMAC acteur/champs/limites et schéma privé F1 inchangés.

## Exécuté

- `pytest tests/backend/test_notifications_cursor.py -k "date_boundary or canonical_utc_extremes" -q --tb=short --junitxml=.local-tools/ops-n2a-f2-dates.xml` : **12PASS9,02s**,6deselected, exit0. V1/v2×haute/basse overflow, noncanonicalité/+00:00 et timezone absente : parse refuse, GETanonyme400/no-store/aucuneSQL. V1/v2×UTCannée0001/9999.microsecondes : authentification/sig acteur réelles, service+HTTP200, counts/page/schéma cohérents. Aucune erreur initiale dans ce groupe correctif.
- `python .local-tools/tester-n2a-cursor-date-boundary.py` : quatre cas deviennent NotificationQueryError, pure/sansSQL ; le script HTTP reviewer n’a PAS été exécuté contre `_review`, ses cas sont couverts sur `_test` par le groupe ci-dessus.
- Ruff check et format --check raceatlas migrations tests/backend ops/ci_selection.py : **PASS100**. node --test tests/contracts/contracts.test.mjs :26contrats publics. `git diff --check 014bda3480d0f8c0233f8e6f68d0ae82886b83db..HEAD` avant/après commit.

Les14passes reviewer a4f (F1maxima/contrat/tamper/legacy) et49PG07f (snapshot/ACK/isolation/HTTP) sont explicitement réutilisées après diff nul de leurs branches, pas relabellisées ni rejouées. Scope.id privé a changé dans F1, mais PAS ce cycle ; contrats/runtimeplanning inchangés vs a4f. Aucun fullN1 local/browser/build inchangé.

PG9780/127.0.0.1:55434 confirmé natif, `_test` b806 uniquement, `_review` réservée. Session10919 terminée/listeners/runtimes/engines fermés, aucun pending. Au push/GEL STOP éditions pour revue ciblée N2A renouvelée+CI ; N2B non attribué. Aucun acte externe autorisé.

## Historique F1, avant finding F2

# N2A-F1 — handoff correction cycle1

17 novembre 2026, 08:20 UTC. PR16 / feature/notifications-interface / base014bda. HEAD/origin avant publication07f22acc4f755d1911fd4def001ca9220947777d, SHA exact communiqué au gel. Reviewer07f REQUEST CHANGES P2, rapport initial archivé `.local-tools/tester-report-notifications-n2a-initial-07f.md`. CI44042648284 development998/118 historique n’approuve pas le correctif.

## Représentation bornée et couture autorisée

`notifications_api.py` codec seulement : v2 b'2\0' + date UTC canonique ASCII + NUL + changeID UTF8 + NUL + scopeID UTF8. Date≤27octets, IDs≤64codepoints/256octets chacun (NUL déjà interdit) ; brut≤543, base64url≤724, point+HMAC43 => **≤768**, contrat1024 préservé pour emoji ET contrôles. Signature HMAC/domaine/acteur inchangés, version incluse dans corps signé ; anciens v1 JSON encore acceptés sous borne existante. UTF8/séparateurs/date/version/IDs invalides refusés avant SQL, pas troncature/ASCII imposé.

Extension de périmètre justifiée et autorisée par Coordinator après preuve : seul `contracts/planning.schema.json:$defs.Scope.properties.id` aligné sur `$defs.Id` privé1..64 ; ancienne regexASCII contredisait scope_id/runtime. Aucun schéma public/catalogue ou runtime planning/modèle changé. Notifications et GETplanning privés testés avec IDs64emoji/64contrôles. Tests nouveaux `test_notifications_cursor.py`, mission/checkpoint actualisés.

## Commandes (_test opt-in, venv/PG existants)

Avec `-q --tb=short` :

1. `pytest tests/backend/test_notifications_cursor.py tests/backend/test_notifications_api.py tests/backend/test_notifications_validation.py --junitxml=.local-tools/ops-n2a-f1-cursor.xml` : **14PASS/3FAIL9,515s**. Codec bornes/négatifs/signature/acteur passent. Deux schémas Scope.id privés incohérents, et un503 fixture (service gardait Account lock) ; incidents conservés.
2. `pytest tests/backend/test_notifications_cursor.py -k legacy_json --junitxml=.local-tools/ops-n2a-f1-legacy.xml` : **1PASS3,52s** après commit caller de la lecture avant HTTP, sans changer timeout. Lecture v1 réelle service+HTTP.
3. `pytest tests/backend/test_notifications_cursor.py -k both_maximum --junitxml=.local-tools/ops-n2a-f1-maxima.xml` : **4PASS5,15s** (deux bornes pures dont768exact avec deuxIDs64U+10FFFF/dateMax, et deux roundtrips service/HTTP/schema notifications+planning, compteur2/scopes exacts/nextpage200).
4. `pytest tests/backend/test_private_planning.py -k private_planning_contract_matches --junitxml=.local-tools/ops-n2a-f1-planning-contract.xml` : **1PASS3,25s**, contrat privé existant après alignement.
5. Ruff check et format --check raceatlas migrations tests/backend ops/ci_selection.py : **PASS100** ; node --test tests/contracts/contracts.test.mjs : **26PASS** publics inchangés. Range base..HEAD contrôlé avant/après commit.

Aucun replay des49passes reviewer/fullN1 ; preuves07f explicitement réutilisées pour SQL E/count/page/DTO, ACK MVCC/read_at/rollback/barrières, HTTP/auth/admission/source/ICS inchangés, pas pour le codec modifié. Le schéma planning privé change : sa couture doit être revue au nouveauSHA, pas déclarée immuable. Nouveau test couvre aussi malformations v2 correctement signées avant TOUT SQL et ancien test tamper/autrui/ABA rejoué dans14verts.

PG9780/127.0.0.1:55434 vérifié nativement, `_test` b806 seulement, `_review` réservée. Toutes commandes/listeners/runtimes/engines terminés, aucun processus pending. Gel et STOP après push pour renouvellement N2A/CI ; N2B non attribué, zéro opération externe réelle. Handoff précédent ci-dessous historique, aucun ancien verdict copié.

## Historique candidat07f avant finding F1

# OPS-N2A — handoff candidat

17 novembre 2026, 07:55 UTC. feature/notifications-interface / [Draft PR16](https://github.com/TheoxProject/RaceAtlas/pull/16), base014bda3480d0f8c0233f8e6f68d0ae82886b83db. HEAD/origin avant publication finale d3544eb70caa2903e8dcb4cc2abcec7cd8b1a0ce, SHA exact communiqué au gel. CI WIP43932247137 development SUCCESS979backend290,58s/118frontend/statiques/build/guards ; pas verdict du futur SHA ni mergegate.

## Fichiers et interfaces

`notifications_api.py` : `parse_query`, `read_notifications`, `mark_all_notifications_read`. E = SavedEntry courant JOIN ScopeChange>baseline JOIN RaceChange LEFT PN ; non matérialisé non lu. Count global/page et DTO complet du SEUL scope joints dans le même SELECT ; page limit+1 AVANT multiplication règles/catégories, raiseload/populate_existing et dédup identité change/scope sans hacher JSON ni fusionner frères. Keyset live `(created_at,change_id,scope_id)` descendant, aucune promesse de snapshot durable entre requêtes. Cursor≤1024, limit50/max100 ; HMAC-SHA256 AUTH_CSRF_KEY/domaine notifications-cursor:v1/acteur serveur, pas bearer/nouveau secret. Syntaxe/taille validées avant SQL ; signature après résolution acteur avant lecture source.

ACK : un INSERTSELECT de toutes E + ONCONFLICT UPDATE seulement read_at NULL, sans RETURNING massif/boucle256/Python non borné. Account lock puis snapshot de CETTE instruction ; source committée après reste non lue même created_at antérieur. Read_at antérieur conservé, retrait exact/réajout baseline par jointure courante, zéro Account côté source. Caller commit/rollback ; aucun retry d’intention ni faux204.

`notifications_http.py` : GET /api/v1/me/notifications ; POST /read-all JSON{}→204 après commit+close. Availability boundary dédié car auth/planning interdit toute querystring ; whitelist limit/cursor stricte, Origin/CSRF/runtime réutilisés et admission notifications ajoutée sans changement global. Cookie seul acteur, preuve de lecture optionnelle liée si présente, 401 passive/no-store, SQL3s/lock1s et PlanningLimits JSON2MiB/texte16KiB. Dépassement413 explicite. Raccord minimal auth.http/admission. Contrats notifications.schema.json/openapi.json additifs référencent le DTO planning.

Tests API/HTTP/snapshot/validation nouveaux. Modèles/migrationb806, source/N1A projection, planning/ICS/auth sémantique, frontend, CI et dépendances inchangés.

## Commandes et résultats réels

Venv existante, TEST_DATABASE_URL=postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test et RACEATLAS_DISPOSABLE_DB=1 ; toutes commandes pytest avec `-q --tb=short` :

1. `pytest tests/backend/test_notifications_api.py --junitxml=.local-tools/ops-n2a-initial.xml` : **4FAIL5,48s**, JSON non hashable par unique. Clé composite corrigée, même groupe `ops-n2a-initial-corrected.xml` : **4PASS4,50s**, quatre statuts/deux acteurs/scopes/count/page/ACK/idempotence.
2. `pytest tests/backend/test_notifications_http.py --junitxml=.local-tools/ops-n2a-http-initial.xml` : **8PASS6,24s** ; Ruff import/F811fixture corrigé, seul `-k http_contract --junitxml=.local-tools/ops-n2a-http-fixture.xml` : **1PASS3,60s** vérifie délégation fixture.
3. `pytest tests/backend/test_notifications_snapshot.py --junitxml=.local-tools/ops-n2a-snapshot.xml` : **7PASS6,765s**. 1005 éligibles/256 matérialisées, count exact/page complète sans doublons/ACK tout ; barrières PG réelles dans ONCONFLICT via PN row-lock (pg_blocking_pids observé, pas avant-callback pris comme snapshot), source avant/après avec timestamp plus ancien ; timeout rollback intégral, retrait/réajout/Accountdelete/autrui et bornes.
4. `pytest tests/backend/test_notifications_validation.py tests/backend/test_notifications_http.py -k "pure_notification or cursor_wrong or session_closed or wrong_origin or openapi_refs" --junitxml=.local-tools/ops-n2a-validation.xml` : **10PASS1FAIL5,902s**. Curseurs/tampering/acteurs/ABA avant données privées, commitclose/503 sans fauxACK, Origin/CSRF/413. Seul FAIL walker imposait ./ à la référence locale auth.openapi.json ; test corrigé pour chemin local canonique, produit inchangé.
5. `pytest tests/backend/test_notifications_http.py tests/backend/test_auth_http_foundation.py tests/backend/test_account_read_context.py -k "openapi_refs or native_basic or disabled_incomplete or bad_activation or admission_sliding or admission_is_own or admission_requires or read_intent_cookie or preflight_b_a_b" --junitxml=.local-tools/ops-n2a-seams.xml` : **19PASS7,578s**, 52désélectionnés. Contrat corrigé/Basic natif/nonvérifié et coutures auth/admission. Session68566 terminée exit0, XML19/0/0/0 réconcilié17nov ; aucun replay des passes après interruption.
6. `python -m ruff check raceatlas migrations tests/backend ops/ci_selection.py` et `python -m ruff format --check raceatlas migrations tests/backend ops/ci_selection.py` : **PASS99**. `node --test tests/contracts/contracts.test.mjs` : **26PASS** publics ; notifications JSON/refs OpenAPI validés dans HTTP via jsonschema+registry locale sans réseau. `git diff --check 014bda3480d0f8c0233f8e6f68d0ae82886b83db..HEAD` à vérifier après commit également.

PG9780/55434 vérifié natif à reprise, `_test` b806 seulement, `_review` réservée. Aucun test/session pending ; listeners/threads/runtimes/engines fermés, Nodes externes intacts. Aucun reset/reseed/nouveau schéma, pas967local/browser/build inchangé répété.

## Revue et limites

Tester cible N2A complet au SHA gelé : E virtuelle/count/page/DTO même snapshot, ACK de toutes non matérialisées, cutoff MVCC réel, champs/scopes/provenance/incertitudes et guards/cookies/curseurs, rollback/timeout/fermeture, retrait/réajout/isolation/epoch. Les groupes verts non modifiés sont explicitement réutilisés, aucun ancien verdict copié. N2B UI reste non attribué avant cette gate ; N2 complet exige acceptation complète + integrated/main avant suite lot8. Pagination vivante et budgets SQL, pas TTL/rétention produit inventés. Aucune action externe réelle autorisée. Au gel : STOP éditions.