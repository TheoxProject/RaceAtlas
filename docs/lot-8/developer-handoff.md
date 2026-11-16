# OPS-N1-F1 — handoff correctif cycle1

16 novembre 2026, 18:05 UTC. PR15 / feature/operations-readiness / basec740 ; HEAD/origin avant publicationb9f07e9640287aa791ad868a7ccdcb2d28704f77, SHA final communiqué au gel. Verdict b9f REQUEST CHANGES P2 malgré integrated43877837658 SUCCESS958/118 historique : après commit réel, perte d’accusé réécrivait failed/missing0 alors que faits/événements/audit success étaient durables. Rapport `.local-tools/tester-report-operations-n1.md`, sonde indépendante conservés.

## Changement borné et garanties

`sync/service.py` : `_finish_run` flush le bilan terminal atomiquement avec les faits/événements avant tentative COMMIT. Erreur de flush = précommit connu, rollback puis audit refus. `_commit_finalization` distingue l’erreur de commit ; après rollback local (ou invalidation si ce rollback échoue), `_confirm_final_commit` lit sur connexion saine **READ COMMITTED**, budgets statement/lock locaux3s, `SELECT ImportRun FOR UPDATE`. Ce verrou attend résolution de l’écriture terminale du backend précédent ; pas de lecture d’un cache ORM ni d’un timestamp utilisé comme faux accusé.

`finished_at` non NULL + statut terminal success/partial/failed donne le vrai `RunResult` durable, sans nouvelle réécriture. Running/finishedNULL/missing0 après verrou prouve le non-commit et permet le seul audit de refus ; source jamais rejouée. Preuve indisponible/ambiguë, y compris erreur de commit de cet audit de refus : exception `FinalizationOutcomeUnknown(code=outcome_unknown, run_id)` sans bilan inventé. Le caller doit inspecter le run, pas relancer aveuglément. Un rollback local n’annule JAMAIS un commit déjà durable.

Cleanup du verrou import global : connexion invalidée ne se reconnecte pas pour unlock une autre session ; erreur unlock entraîne invalidation/fermeture physique sans remplacer l’issue inconnue. Aucun Account, modification de modèle/migrationb806, auth/planning/ICS, UI/API/contrat/dépendance/CI. Nouveau `test_sync_commit_outcome.py`, docs/checkpoint seulement. API interne privée `_finish_run(..., engine=engine)` limitée à synchronize ; exception non convertie en faux RunResult.

## Commandes / résultats

Même venv/DB `_test` opt-in b806, PG9780 loopback55434, `_review` non utilisée :

1. `pytest tests/backend/test_sync_commit_outcome.py -q --tb=short --junitxml=.local-tools/ops-n1-f1-commit.xml` : **8 PASS6,84s**. Vrai commit puis OperationalError unique sur success/partial/failed et primaire invalidée ; erreur avant flush/commit et rollback réel ; confirmation impossible + unlock défaillant, issue inconnue préservée, global lock vérifié libre.
2. `pytest tests/backend/test_sync_finalization_edges.py -k "capacity or second_final or final_commit" -q --tb=short --junitxml=.local-tools/ops-n1-f1-seams.xml` : **5 PASS5,59s**. Bornes et atomicité, ancien business-window commit conservé, deux barrières de sauvegarde.
3. `pytest tests/backend/test_sync_commit_outcome.py -k failed_local_rollback -q --tb=short --junitxml=.local-tools/ops-n1-f1-rollback-unavailable.xml` : **1 PASS3,45s**, seule addition après groupe8 : rollback local lui-même défaillant, connexion bindée invalidée puis confirmation saine.
4. `python -m ruff check raceatlas migrations tests/backend ops/ci_selection.py` et `python -m ruff format --check raceatlas migrations tests/backend ops/ci_selection.py` : **PASS93**. `node --test tests/contracts/contracts.test.mjs` : **26 PASS**. Range `git diff --check c74086365df62bf1c71623e080bb1f649c9981f5..HEAD` contrôlé après commit également.

Aucun échec dans les groupes de correction. Aucun rerun44 reviewer/958 backend ni browser/build inchangé. Les preuves N1A/B1/B2 précédentes sont historiques explicitement réutilisées pour code non modifié ; nouvelle acceptation COMPLÈTE et integrated au SHA corrigé nécessaires. Tous tests/listeners/engines terminés, aucune commande pending. Au gel STOP sources ; N2 non attribué, aucune action externe autorisée.

## Handoff historique b9f, avant finding F1

# OPS-N1 — handoff candidat final A + B1 + B2

16 novembre 2026, 13:32 UTC. Branche `feature/operations-readiness`, [Draft PR15](https://github.com/TheoxProject/RaceAtlas/pull/15), basec740. HEAD/origin avant publication finale : `dbe9c07eeb49c1a586e6fd27934057421c5391cd`. CI [43875151220](https://github.com/TheoxProject/RaceAtlas/actions/runs/43875151220) **FAIL949PASS/1FAIL283,71s +118frontendPASS** : unique ancien attendu B1 restauration (1==0), déjà corrigé et reciblé ci-dessous. Aucun autre échec. SHA exact final communiqué au gel ; nouvelle CI et acceptation complète nécessaires, aucun verdict final présumé.

## Interfaces et fichiers B2

`sync/final_plan.py` : `FinalInputs` et `FinalizationPlan` frozen, tuples/primitifs/bytes seulement. `plan_finalization(inputs)` sans ORM/Session/SQL ni effet de bord : promotions historiques audit, états fenêtres, stamps metadata, transitions et union de scopes, statut et compteur de races. `_load_final_inputs` du service charge sous `no_autoflush` ; `_finish_run` acquiert les guards N1A uniquement pour les vraies transitions, recharge/revalide avant DML puis applique dans le commit final existant. Ce helper possède exclusivement la transaction finale de `synchronize`, jamais un commit par race/chunk.

Absence : clés `presence:` + SHA256(run/race/absence/from/to/window), witness maxchecked puis ID, provenance IMMUTABLE ImportWindow calendrier URL/checkedUTC/versionRun/evidence `window:UUID`. Aucun prétendu contrôle fiche Race, statut cancelled et SourceRevision business inchangés. Répéter `to_verify` rafraîchit seulement sa preuve, compteur et événement zéro. Restauration B1 reste événement distinct présent.

Cap1001, garde, snapshot changé ou écriture refusée : rollback de toutes les mutations finales puis audit borné incomplete/partial/failed/missing0 ; commits business des fenêtres préservés. Dernier coverage incomplete, last_success précédent honnête. Pas de retry silencieux. Source jamais Account ; le save privé reste Account→guard→baseline. Barrières PG prouvent save avant/après finalcommit ; retrait scope cascade ses seules notifications et réajout reprend une baseline fraîche.

Tests nouveaux `test_sync_finalization.py`, `test_sync_finalization_edges.py` ; couture restauration B1 actualisée avec directions, cibles et provenance exactes (absence + retour). Pas modèle/migrationb806, N1A, planning/auth/ICS, frontend/API, CI ou dépendance changé dans B2.

## Commandes et résultats exécutés

Venv existante, `TEST_DATABASE_URL=postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test`, `RACEATLAS_DISPOSABLE_DB=1`. JUnit ignorés sous `.local-tools/`, `--tb=short` partout :

1. `pytest tests/backend/test_sync_finalization.py -q --junitxml=.local-tools/ops-n1b2-initial.xml` : **8 PASS, 10,815 s**.
2. `pytest tests/backend/test_sync_finalization_edges.py tests/backend/test_sync_notifications.py -k "capacity or large_catalogue or second_final or final_commit or restoring_presence" -q --junitxml=.local-tools/ops-n1b2-edges.xml` : **6 PASS / 1 FAIL, 25,35 s**. Ancien test B1 attendait une seule transition ; les six nouvelles preuves passent. Aucune passe relabellisée.
3. `pytest tests/backend/test_sync.py tests/backend/test_catalog_sync.py tests/backend/test_sync_notifications.py -k "restoring_presence or only_complete_run or partial_independent_window or global_presence or old_empty_window or no_windows or failed_fresh_member or prebaseline_duplicate or repeated_controlled_absence or historical_or_equal or genuinely_fresh_alias or coverage_uses_execution or incoherent_success_window" -q --junitxml=.local-tools/ops-n1b2-final-seams.xml` : **28 PASS, 59,83 s**.
4. `pytest tests/backend/test_sync_finalization_edges.py tests/backend/test_sync_notifications.py -k "revalidated or restoring_presence" -q --junitxml=.local-tools/ops-n1b2-revalidation.xml` : **2 PASS, 12,25 s**, après renforcement des directions/provenances de restauration.
5. `pytest tests/backend/test_sync_finalization.py -k unsave -q --junitxml=.local-tools/ops-n1b2-unsave.xml` : **1 PASS, 9,38 s**.
6. `python -m ruff check raceatlas migrations tests/backend ops/ci_selection.py` et `python -m ruff format --check raceatlas migrations tests/backend ops/ci_selection.py` : **PASS, 92 fichiers formatés**. `node --test tests/contracts/contracts.test.mjs` : **26 PASS**. Range `git diff --check c74086365df62bf1c71623e080bb1f649c9981f5..HEAD` à contrôler aussi après commit.

PG9780/55434, `_test` b806 uniquement ; `_review` réservée. Fixtures migrations et toutes connexions/threads fermés, aucune commande pending. Aucun nouveau schéma. Preuves B1 réutilisées : 9 nominaux, 6 edges, 12 coutures et CI3ed942/118 ; finalisation/restauration impactées revérifiées ci-dessus. N1A a76 APPROVE/CI927/118 est historique et code inchangé, pas approbation du futur SHA.

## Revue et limites

Tester doit accepter **N1A+B1+B2 ensemble** au SHA final : contraintes/baselines/ordre global numérique et rollback/savepoints, imports/deltas/scopes/provenance, finalisation pure et atomicité1000/1001, absence distincte d'annulation, projection/unsave/readd, coverage et zéro Account dans source. Integrated exacte demandée par Root puis merge/main CI obligatoires avant N2. Aucune suite942 locale répétée ni ancien verdict copié.

La borne technique1000 concerne tous les scopes réellement changés, pas les abonnés ni le catalogue entier ; refus explicite sans drop. Budget lock source3s local, pas objectif SLA. API/UI notifications, exploitation/backup et V1 restent TODO ; aucun mail réel, FFC live, DNS, service, DB distante, déploiement, achat ou tag final autorisé. Au gel : STOP éditions.

## Handoff B1 historique
# OPS-N1B-1 — candidat à figer

16 novembre2026 12:49UTC. Branche `feature/operations-readiness`, [Draft PR15](https://github.com/TheoxProject/RaceAtlas/pull/15), basec74086365df62bf1c71623e080bb1f649c9981f5. HEAD/origin avant publication98147ac78cf6d1051a21f5e9ae97a64122a5eead. N1A APPROVE exacta76e35a5e11ad86362c4716e344c3f6c0037eabe acquis ; aucune approbation B1 copiée. CI98143836355310 **development/fullfallback SUCCESS936backend272,01s/118frontend**, sourceguards avant/après ; ne valide pas les6tests edge locaux ajoutés ensuite et n'est pas gate integrated de fusion. SHA final communiqué au push, puis STOP pour revue ciblée B1.

## Livré et fichiers

- `sync/service.py` : inventaire COURANT à chaque fenêtre (clés/alias/races/scopes), guards N1A AVANT premier flush/nested de `_import_window`, reload ORM après attente ; nouveaux objets initialement sans abonnement ne créent pas d'alerte historique. Connexion réelle RC vérifiée, y compris unionvide ; `SET LOCAL lock_timeout=3000ms` source uniquement. Refus garde/OperationalError : rollback de transaction abortée AVANT audit fenêtrefailed ; commits de fenêtres précédentes conservés, pas de succès/inférence d'absence faux.
- `sync/change_facts.py` : snapshot frozen tuples(scopeID,JSONcanoniquebytes), aucun ORM capturé ; faits wide vers scopes exacts, règles/labels/éligibilité par ID stable/corrélations conservées. Positions/ordre d'ensembles, contrôles/timestamps/provenance cache et coordonnées de centre exclus du delta. Commune identité reste un fait, jamais départ inventé. Graphes sources bruts/provenance conservés ailleurs, aucune admissibilité personnelle inférée.
- `_apply` garde retour(race_id,action), capture avant/après sous garde dans nested existant. Business updated : clé `revision:`+SourceRevision.id réellement créée, provenance immuable sourceURL/checked_at UTC/version ; reorder technique sans delta, fraîcheur et replay ne créent pas d'événement. Source créée puis retrouvée en fenêtre2 conserve IDs et zéro événement initial ; préflight contradictoire inchangé. Vraie restauration to_verify→present, même otherwiseunchanged, enregistre kindpresence distinct avec clé stable run/race/transition ; jamais cancelled inventé.
- Mutation source/révision/event/cibles sont dans le même SAVEPOINT : une erreur record après écriture annule le tout et laisse diagnostic item borné. Pas de fanout/Account lookup ou email côté source. Projection privée N1A après commit : abonnements avant delta reçoivent l'événement, après commit baselinefraîche sans rétroactivité.
- Tests nouveaux `test_sync_notifications.py` et `test_sync_notification_edges.py`. Mission non committée du Coordinator préservée et incluse au checkpoint981. Aucun modèle/migrationb806, changes/planning/notifications N1A, auth/ICS, frontend/API, CI ou dépendance modifié depuis a76.

## Commandes et résultats réels

DB locale `_test` opt-in seulement, Python/PG existants :

1. `pytest tests/backend/test_sync_notifications.py -q --tb=short --junitxml=.local-tools/ops-n1b1-initial.xml` : **4PASS/5FAIL5,79s** conservés. Fixtures : comparaison du même instant UTC et PGEurope/Paris, puis requête erronée ImportItem.run_id corrigée en JOINImportWindow. Run nominal corrigé : **8PASS/1FAIL6,20s**, oubli importImportWindow ; dernier cas `-k record_failure --junitxml=.local-tools/ops-n1b1-rollback-corrected.xml` : **1PASS7,16s**. Les8verts sont explicitement réutilisés, pas faux9PASSunique ; CI981936backend a ensuite passé les9cas complets au code source inchangé.
2. `pytest tests/backend/test_sync_notification_edges.py -q --tb=short --junitxml=.local-tools/ops-n1b1-edges.xml` : **6PASS12,874s**. Annulation attestée/scopes exacts, alias idempotent, cache/centre non notifiables, garde réellement contendue3s puis audit cohérent transaction utilisable/priorwindow préservée, deux ordres save/source commit avec vraies connexions et barrières sans sleep. IDs/baselines et absence de rétroactivité vérifiés, pas simple appel record simulant un import.
3. `pytest tests/backend/test_sync.py -k 'fixture_sync_is_idempotent or title_date_and_grouping or unverified_reordered or attested_scope_change or partial_independent or global_presence_prevents or incoherent_window_and_conflicting or stale_and_partial_details or item_savepoint_rolls_back or advisory_lock_prevents or explicit_center_binding or geocoder_failure_defers' -q --tb=short --junitxml=.local-tools/ops-n1b1-sync-seams.xml` : **12PASS9,41s**,74deselected.

Reprise après quota : commande3 précédente avait été REJETÉE AVANT CreateProcess, sans session/JUnit ; reprise explicite16nov puis UNE exécution réelle après conciliation native. Aucun rerun6/8+1. Source service/helper et test edge mtime antérieurs au JUnit6 confirmés ; aucun correctif produit après checkpoint981. Ruff check/format **89 fichiers PASS**, contrats Node **26PASS** le16nov ; range diffcheckc740..HEAD vérifié avant/après publication. Pas campagne927locale/build/browser non affectés.

## Limites et revue

**N1B-2 finalisation to_verify/audit pur/capacité1000/1001 n'est PAS implémentée**, reste à attribuer après ce jalon. Le code de finalisation existant est préservé ; la restauration present est seule nouvelle couture de présence B1. API/UI Changements récents, exploitation/backup/V1 restent à faire. B1 seul ne termine ni N1 ni lot8 et ne permet pas fusion sans acceptation complète/integrated/mainCI futurs.

Aucune commande/runtime/thread conservé ; cleanup Session/Engine et barrières finally. PG9780 loopback55434, `_test` et `_review` b806 confirmés par Root12:45UTC, ReviewerDB jamais utilisée par les tests Developer. Prochaine action : push SHA gelé, revue ciblée B1 et CI courante ; STOP éditions ensuite, pas B2 sans transfert. Aucun email réel/collecte live/Resend/DNS/service/remoteDB/deploy/payant/tag final.
