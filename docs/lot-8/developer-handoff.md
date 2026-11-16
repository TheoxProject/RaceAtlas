# OPS-N1B-1 — checkpoint WIP nominal (pas gel final)

Nouveau raccord service.py + helperimmutable sync/change_facts.py et test_sync_notifications.py. Gardes avant fenêtre, reloadORM après attente, RC vérifiée mêmeunionvide, lock_timeout transactionnel3s ; erreurs acquisition ChangeError/OperationalError rollbackent AVANT audit fenêtrefailed, recordError rollback nesteditem seulement. Snapshot commune identité exclutcentre/cache, scopes/règles corrélées horsordre ; SourceRevision.id clé et provenance UTC immuable, présence restore distincte mêmeunchanged.

Commandes : `pytest tests/backend/test_sync_notifications.py -q --tb=short --junitxml=.local-tools/ops-n1b1-initial.xml`4PASS/5FAIL5,79s, fixturesUTCsameinstant+JOINaudit corrigées ; runnominal8PASS/1FAIL6,20s importImportWindowoublié ; `-k record_failure --junitxml=.local-tools/ops-n1b1-rollback-corrected.xml`1PASS7,16s après seulimport. Les8verts réutilisés explicitement source inchangée ;9cas nominaux acquis mais pas9PASSunique ni acceptance. Ruff cibléPASS, aucun testpending.

RESTE : barrières2connexions saveavant/aprèscommit, refusgarde3saudit réel, alias/cancelled/cache et testsSync coutures utiles. Publication WIP précoce pourCI, gel final plus tard ; N1B2/API/UI nonattribués. CadrageRoot mission/checkpoint inclus sansrévocation. Aucun modèle/migrationb806/N1A/auth/CI/deps modifié.

## Interfaces avant code et historique
# OPS-N1B-1 — interfaces avant code (WIP)

Base travail a76e35a5e11ad86362c4716e344c3f6c0037eabe, PR15. N1A APPROVE exact/CI43829642340developmentfull927/118 acquis ; pas verdict copié au prochain SHA. Mission nouvelle sync-notifications-mission.md et checkpoint non committés du Coordinator préservés/inclus au prochain jalon. N1B-2final absence reste hors périmètre.

Raccord proposé : `_window_scope_ids(session,batch,preflight)` fait inventaire COURANT no_autoflush par clés/alias attestés ; guards numériques N1A avant `_import_window`/son premier flush/nested géocodage. Recharger ensuite ORM sous garde (expire_all sans dirty antérieur). Union vide=newraces, nullcontext ; race existing sans guard refuse avant DML. Echec acquisition borne/contention : rollback unité fenêtre avant mutation, persister fenêtre audit failed/diagnostic borné, garder commits des fenêtres précédentes.

Petit helper sync/change_facts.py : snapshot frozen de tuples(scopeID,JSONcanoniquebytes) + présence, aucun objet ORM conservé. Snapshot race-wide name/dates/status/discipline/types/organizer/communeidentity/competition ; commune sans coordonnées/provenance/timestamp cache. Scope raw_label/eligibility/rules corrélées canonicalisées indépendamment de positions/IDs de règles/ensembles. Deltas par ID commun stable, pas union frères ; source/règles brutes restent dans graphe et provenance existants, notification ne fabrique aucune admissibilité.

`_apply(...,guard=None)` garde retour(race_id,action) ; capture avant mutation et après flush dans nested existant. SourceRevision créée gardée en variable : updated→record_change(event_key='revision:'+id, provenance immuablechecked_at/source_url/version, deltas). Created et revision technique sans delta→rien. Restauration missing/to_verify→present, même otherwiseunchanged, crée événement presence distinct ; clé stable bornée SHA du run/race/phase/avant/après, evidence_idrun ; pas nouvelle preuve d'annulation. Source/event/cibles rollbacks joints sirecordError, diagnostic change_record_error sans payload, pas fanout/Account côté source.

Tests prévus : imports synthétiques réels +projection privée, report/règles scoped/cancelled, replay/fraîcheur/reorder/alias/deuxfenêtres création-identique, runs A→B→A→B, restaurationpresent, rollbackinjectionrecord etbarrières saveavant-aprèscommit. Groupes ciblés uniquement_testb806 aprèsstatutPG ; aucun résultat B1 encore, pas full927local. Clés/provenance replay restent celles mutation, paschecked_at nouveau injecté dans ancienneclé. API/UI/absencefinale nonimplémentées ici.

## Handoff N1A historique
# OPS-N1A-F1 cycle1 + CI-R1 — candidat à figer

16nov2026, feature/operations-readiness/DraftPR15/basec740, head avant publication5d8bf28d80ba06eb00586a669fe97588b3b7001b. Tester REQUEST CHANGES P2 remplace son APPROVE initial :114PASS historiques mais sonde2connexions révèle40P01 en1,156s entre putB/batchA,B/putA. CI43826354099 a échoué AVANTbackend : ubuntu-latest devenu26.04 non supporté par l'installateur Chromium ;118frontend/statiques avaient passé. Aucun verdict réutilisé pour le futur SHA.

## Correction transactionnelle

`changes.py` garde maintenant watermark MAX des CLÉSadvisory numériques réelles (SHA64 signé, clés dédupliquées/triées), pas seulement ordre de chaque batch. `guard.scope_ids` reste lexical. Bookkeeping Connection.info privé lié à l'identité du ROOTDB effectif : partagé entre Sessions sur la même connexion, conservateur après rollbackchild, remplacé à nouveau root/rollback-autobegin/réutilisation pool. Pas de held-set présumant propriété après rollback. Nouvelle clé>MAX : acquisition bloquante ascendante ; clé≤MAX : pg_try_advisory_xact_lock immédiat, false→ChangeError générique avant attente/DML, aucun commit/rollback/retry/intent rejoué caché. Pré-acquérir l'union complète après Accountfirst reste recommandé pour plusieurs sauvegardes ; B→A libre et réentrance restent permis. Racine/nested effectifs et validité du jeton N1A sont conservés.

Preuve ciblée : paire synthétique scope-order-b/c dont ordre lexical ET numérique coïncident. Même intercalation de cycle que l'ancien code ; S1 reçoit ChangeError avec transaction utilisable (pas40P01), son rollback explicite libère S2 qui écrit/commit, autrui/projection préservés. Autres cas : B→A sans contention/union pré-gardée, rollbackchild puis contention sur clé égale ou descendante, Sessions Connection partagée3join modes, rootrollback/autobegin et poolreuse. Les12 validations IDs non représentables gardent zéroSQL. Pas de lock Account ajouté à la source/sync.

## CI-R1 et vérifications

Seule ligne YAML modifiée : runs-on ubuntu-24.04. Tous steps/modes development/integrated, fallbackfull, permissions, guards, artefacts et timeout restent identiques ; aucune dépendance ou version Playwright changée. [GuideCI](../readiness/ci-validation.md) explique le rollover. La CI réelle au nouveau SHA doit encore valider l'installation et le backend.

`pytest tests/backend/test_notifications.py tests/backend/test_planning.py -k 'global_order or guard_outer or effective_external or multi_bind or save_vs or nonrepresentable' -q --tb=short --junitxml=.local-tools/ops-n1a-f1-lock-order.xml` : **28PASS27,81s**,76deselected, aucun warning. Un groupe ciblé, pas replay114. Les preuves initiales97verts/23corrections et114Tester sont historiques/chemins inchangés explicitement réutilisables, pas nouvelle approbation. Ruff86 lint/format, contrats26 et diff complet base..HEAD PASS avant publication ; range revérifié après commit.

Modèles/migrationb806/planning/notifications/auth/ICS/sync/frontend/contrats/pins restent identiques5d8. Aucun test/processus restant ; PG9780/55434, _test et _review b806 selon état de transfert, tests Developer UNIQUEMENT_test. Prochaine action : push SHA exact/GEL et STOP pour revue N1A renouvelée/CI courante, pas N1B ni N1 complet/lot8 terminé. Aucun mail réel/DNS/service/remoteDB/deploy/collecte.

## Fondation N1A — interfaces et preuves antérieures (historiques)
# OPS-N1A — fondation interne, candidat à figer

16 novembre 2026. Branche `feature/operations-readiness`, [Draft PR15](https://github.com/TheoxProject/RaceAtlas/pull/15), base `c74086365df62bf1c71623e080bb1f649c9981f5`. HEAD/origin avant publication : `fb86117fc5408fc22ed5b5fce3ced8af2d6fce03`. Sa CI43746572542 development est verte (118 frontend/statiques, backend none explicite docs-only), pas une validation de N1A. SHA final communiqué au push puis STOP. N1B sync, N2 API/UI et fin du lot8 restent TODO.

## Interfaces et fichiers

- `models.py` + migration `b806e44f7901` après `a74d915e3c02` : RaceChange UQ(race,event_key), ScopeChange PK(change,scope)/UQ(scope,sequence), PersonalNotification PK(account,change,scope). FK composée account/scope vers SavedEntry UQ CASCADE et change/scope vers ScopeChange ; suppression d'un abonnement retire SES messages, Account cascade transitif, scope source RESTRICT. Ledger ICS inchangé/survivant à unsave. Baseline SavedEntry NOTNULL≥0 : backfill0 des anciennes lignes sur journal neuf, AUCUN default0 durable.
- `changes.py` : `scope_guards(session, scope_ids)` contextmanager → jeton interne ; `subscription_baseline(session, guard, scope_id)` ; `record_change(session, guard, *, race_id, event_key, kind, targets, provenance)` → ID ou None si aucun delta. `targets` = scope opaque → before/after dicts des seuls champs métier modifiés ; JSON canonique≤16Kio/cible, ≤1000 cibles, provenance minimale≤4Kio (source_url, checked_at UTC, normalization_version, evidence_id facultatif). Kind business/presence distinct, aucune annulation déduite. Event_key identifie UNE mutation réelle, jamais businesshash seul : A→B→A→B reste trois événements ; replay même clé/payload/provenance immuables idempotent, conflit refusé sans nouvelle ligne.
- `planning.py` : validation pure acteur/ID avant SQL, Account FOR UPDATE aussi hors HTTP puis scope guard/baseline avant création. Lecture de l'identité ORM sans SQL sur ID expiré ; aucun écrasement des attributs Account pending. Statut/no-op préservent ID/baseline ; re-add crée nouvelle incarnation/baseline fraîche. Deux fixtures directes SavedEntry et un INSERT UQ de tests existants renseignent désormais baseline0 explicitement, sans relâcher les assertions.
- `notifications.py` : `project_notifications(session, actor, *, batch_size=256)` → `ProjectionResult(inserted, pending)`, batch entier1..1000. INSERT…SELECT sur abonnements/baselines COURANTS sous Account lock, pas de candidat RAM ; UQ ON CONFLICT no-op. Cas210 événements :128 puis82, pending signalé, trois statements SQLAlchemy par batch (pas N+1). Aucun drop, worker ou fanout Account côté record.

## Transactions et concurrence

Toutes opérations caller-owned, aucun commit caché. Privé Account → scope guards triés ; futur sync import guard → scope guards AVANT source DML/SAVEPOINT, jamais Account. Le jeton suit Session et son ancestor transaction, MAIS AUSSI Connection effective et ses root/nested transactions publiques : rollback du SAVEPOINT effectif invalide le jeton même si Session paraît active. Guard outer reste valide dans un child rollback ; guard acquis dans child invalidé après rollback. RELEASE du nested d'acquisition est rejeté conservativement. Jeton hors contexte/rollback puis autobegin refusé. Bind Connection supporté et trois join modes testés ; multi-bind/routage rejeté. Pas promesse contre code serveur arbitraire manipulant internals/SQL transactionnel brut.

Guards/projection exigent connexion transactionnelle READ COMMITTED effective ; AUTOCOMMIT et REPEATABLE READ refusés (lock éphémère/baseline snapshot périmée). Aucune configuration ou sémantique auth globale changée. Des gardes internes n'autorisent aucune requête client, aucun nouvel endpoint. Le service n'applique pas encore de mutation source : fixtures directes seulement, aucun import notifiant revendiqué avant N1B.

## Preuves exécutées et réutilisation

[Commandes/environnement](local-development.md), DB `_test` opt-in uniquement :

- `pytest tests/backend/test_notifications.py -q --tb=short --junitxml=.local-tools/ops-n1a-initial.xml` : **12 PASS14,053s**, roundtrip upgrade/check/downgrade base/upgrade/check de fixture compris.
- `pytest tests/backend/test_notifications.py tests/backend/test_planning.py tests/backend/test_private_planning.py -q --tb=short --junitxml=.local-tools/ops-n1a-extended.xml` : **97 PASS/10 FAIL73,175s** conservés. Neuf échecs : nouveau lock précédait validation NUL/surrogates qui exige zéro SQL ; corrigé validation pure avant lock. Dixième : fixture duplicate omettait baseline, causait23502 avant attendu23505 ; fixture corrigée. Trois warnings précis du rollback Connection externe sont désormais assertés localement, pas filtrage global.
- `pytest tests/backend/test_planning.py tests/backend/test_notifications.py -k 'nonrepresentable or database_restricts or large_batch or transaction_modes or invalid_batch or invalid_or_oversized or effective_external' -q --tb=short --junitxml=.local-tools/ops-n1a-corrections.xml` : **23 PASS17,186s**, défauts reciblés + batch210/limites/dépassement séquence/3join modes/AUTOCOMMIT-RR.

Les97 verts incluent backfill sur sauvegardes existantes (downgrade a74/upgrade/check, ID préservé et absence de default), deux connexions/barrières save avant/après record non committé, ABA projection/remove/re-add, cascades ORM parent chargé et SQL bulk, mauvais couples FK, statuts/no-op/rollback et epoch/ICS/autrui préservés. Leur preuve est réutilisée explicitement pour chemins inchangés ; pas de verdict courant copié, pas de campagne complète locale. Source/tests inchangés depuis JUnit23 (mtime antérieurs confirmés à reprise). Ruff lint + format86 et contrats Node26 PASS le16nov ; range diffcheck base..HEAD vérifié avant/après commit.

## État local et suite

Reprise16nov : JUnit déjà terminés réconciliés, aucune relance. Cluster existant redémarré, premier lancement sans anciens arguments a utilisé port défaut ; arrêté uniquement ce serveur puis relancé avec chemin absolu/-h127.0.0.1/-p55434. PID courant9780 ; lectures Alembic `_test`=b806e44f7901, `_review`=a74d915e3c02 (lecture seule, pas de mutation Reviewer). Aucun initdb/reseed/réinstallation, runtime/browser/test restant.

Prochaine action : revue ciblée du SHA exact N1A + CI courante ; STOP source au gel. N1B doit raccorder deltas/presence réels, avec garanties de guards avant DML et clés de mutation stables ; API/UI notifications, exploitation, backup/restore et V1 restent à faire. Pas d'approbation N1 complète, de fusion ou de lot8 terminé à ce seul jalon. Aucun email réel/Resend/DNS/service/remoteDB/déploiement/collecte/tag final.
