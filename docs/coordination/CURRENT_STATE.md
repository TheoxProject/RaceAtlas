# OPS-N1-F1 — candidat corrigé cycle1, GEL après publication

**16 novembre 2026, 18:05 UTC.** Checkout isolé `add4/feature/operations-readiness`, [Draft PR15](https://github.com/TheoxProject/RaceAtlas/pull/15), base `c74086365df62bf1c71623e080bb1f649c9981f5`. HEAD/origin avant publication : `b9f07e9640287aa791ad868a7ccdcb2d28704f77`. Tester b9f REQUEST CHANGES P2 (audit faux après commit durable) ; integrated43877837658 historique SUCCESS958/118 ne vaut ni verdict ni CI du nouveau candidat. Developer seul writer, Tester STOP, `_review` réservée.

Correction limitée service : flush terminal explicite avant COMMIT ; erreur commit => rollback local puis confirmation `ImportRun FOR UPDATE` via connexion fraîche READ COMMITTED et budgets locaux3s. Le verrou résout le backend précédent avant de conclure non-commit. Terminal success/partial/failed confirmé => bilan durable intact ; running/finishedNULL confirmé => audit de refus seulement. Confirmation indisponible/ambiguë => `FinalizationOutcomeUnknown` (`code=outcome_unknown`, run_id), aucun faux missing0/rollback ni audit réécrit. Invalidation de la connexion bindée si rollback défaillant ; cleanup global n’écrase pas l’issue inconnue. Aucun replay d’import ni Account côté source.

## Résultats correction réels

- `pytest tests/backend/test_sync_commit_outcome.py -q --tb=short --junitxml=.local-tools/ops-n1-f1-commit.xml` : **8 PASS, 6,84 s**. Commit PG réel puis erreur unique success/partial/failed, primaire invalidée ; préflush/précommit ; confirmation indisponible avant/après durabilité et unlock défaillant.
- `pytest tests/backend/test_sync_finalization_edges.py -k "capacity or second_final or final_commit" -q --tb=short --junitxml=.local-tools/ops-n1-f1-seams.xml` : **5 PASS, 5,59 s**. Cap1000/1001, rollback2e record et deux barrières save/finalcommit.
- `pytest tests/backend/test_sync_commit_outcome.py -k failed_local_rollback -q --tb=short --junitxml=.local-tools/ops-n1-f1-rollback-unavailable.xml` : **1 PASS, 3,45 s**, seule branche nouvelle : rollback local impossible puis invalidation/confirmation saine. Les8 verts n’ont pas été relancés.
- Ruff lint/format **93 fichiers PASS**, contrats **26 PASS**, range diffcheck base avant/après commit à vérifier avant gel.

Toutes commandes terminées exit0 ; aucun test/session/worker pending, listeners/threads/engines fermés. `_test` b806 uniquement, PG9780/127.0.0.1:55434 vérifié nativement avant tests ; aucun reset/reseed/migration nouvelle. Préparation N2 ignorée reste lecture seule.

**Prochain geste sûr : commit/push cohérent, communiquer SHA gelé puis STOP éditions.** Coordinator renouvelle acceptation COMPLÈTE N1A+B1+B2 et CI integrated exacte (`ci:full` déjà posé), merge/main CI avant N2. Runtime hors chemin final inchangé, preuves44 reviewer/958CI antérieures réutilisées explicitement après diff ; aucune ancienne approbation copiée. Si la confirmation est indisponible, issue inconnue exige inspection opérateur du run, pas retry automatique. Aucun email/live/DNS/service/DB distante/deploy/achat/tag.

## Historique candidat b9f (avant finding F1)

# OPS-N1 — candidat final A + B1 + B2, GEL après publication

**16 novembre 2026, 13:32 UTC.** Checkout isolé `add4/feature/operations-readiness`, [Draft PR15](https://github.com/TheoxProject/RaceAtlas/pull/15), base/main `c74086365df62bf1c71623e080bb1f649c9981f5`. HEAD/origin WIP `dbe9c07eeb49c1a586e6fd27934057421c5391cd` ; compléments tests/docs locaux non publiés. CI [43875151220](https://github.com/TheoxProject/RaceAtlas/actions/runs/43875151220) **FAIL : 949 PASS / 1 FAIL, 283,71 s ; 118 frontend PASS**, mode development/fullfallback. Unique échec : ancien attendu B1 restauration `RaceChange1 == 0`, corrigé et reciblé localement ci-dessous ; aucune autre failure. Ne vaut pas preuve verte du candidat final. Developer seul writer ; Tester STOP, `_review` réservé. Aucun processus de test en attente.

| Tâche | État |
|---|---|
| N1A modèles, guards globaux, baselines et projection | Preuves a76 réutilisées après diff nul, pas verdict final copié |
| N1B-1 imports/deltas/restauration | Gate ciblé 3ed + CI development 942/118 ; runtime B1 inchangé hors couture finale explicite |
| N1B-2 plan pur, absence atomique/provenance/capacité | Implémenté et ciblés acquis ; revue finale TODO |
| N1 complet | TODO acceptation indépendante A+B1+B2 + integrated au SHA final, puis merge/main CI |
| N2 API/UI, exploitation/backup/candidat V1 | TODO, non attribués |

Livré B2 : plan frozen sans ORM/SQL, promotions audit historiques et anciennes métriques conservées (`missing_marked` = races réellement passées à `to_verify`). Snapshot chargé sous `no_autoflush`, revalidé après guards numériques N1A avant DML ; seul l'ensemble des scopes des vraies transitions consomme la borne1000. Métadonnées seules et catalogue>1000 sans grands deltas ne sont pas refusés. Événements/stamps/audit dans un commit final ; refus cap/guard/snapshot/record/commit : rollback final puis audit incomplete/partial/failed et missing0. Fenêtres business déjà committées conservées.

Provenance absence = URL/checked_at du calendrier ImportWindow réellement contrôlé, version Run validée, evidence `window:UUID`, témoin maxchecked/tieID. Payload présence seul ; aucune annulation ni révision business inventée. Aucun Account côté source. [Handoff](../lot-8/developer-handoff.md) : commandes, fichiers, interfaces et limites.

## Résultats B2 réels

- `ops-n1b2-initial.xml` : **8 PASS, 10,815 s** (session74560 réconciliée, aucun rerun).
- `ops-n1b2-edges.xml` : **6 PASS / 1 FAIL, 25,35 s**. Six nouvelles preuves cap1000/1001, catalogue volumineux/1delta, rollback2e record et deux barrières passent. Ancien attendu B1 de restauration comptait encore une seule transition ; corrigé explicitement pour absence puis retour, cibles/provenances exactes et business inchangé.
- `ops-n1b2-final-seams.xml` : **28 PASS, 59,83 s**, source historique/alias/fraîcheur/absence/coverage et cas restauration corrigé.
- `ops-n1b2-revalidation.xml` : **2 PASS, 12,25 s**, vraie attente PG puis revalidation du snapshot et cas restauration renforcé.
- `ops-n1b2-unsave.xml` : **1 PASS, 9,38 s**, import→notification→retrait exact/réajout frais/autrui préservé.
- Ruff lint et format **92 fichiers PASS** ; contrats **26 PASS** ; `git diff --check c740...` PASS avant commit, range final à revérifier après commit.

Tests uniquement `_test` b806, PG9780 loopback55434/cluster add4 existant ; fixtures migrations upgrade/check/downgrade/upgrade/check, aucune nouvelle migration. Sessions74560/31793/46187/86427/61400 terminées ; barrières libérées, engines/threads fermés. Pas de campagne942 locale ; modèles/migration/N1A/planning/auth/ICS/frontend/API/CI/deps inchangés dans B2.

**Prochain geste sûr : publier tests/docs cohérents, vérifier range final puis GEL exact communiqué au Coordinator. STOP sources ensuite pour acceptation COMPLÈTE N1 et integrated courant.** Limite technique1000 vraie union sans chunks/drop/retry ; pas SLA de latence ni rétention produit ajoutée. Aucune action réelle live/email/DNS/service/DB distante/deploy/achat/tag final.

## Historique B1 conservé
# OPS-N1B-1 — candidat à figer

**16nov2026 12:49UTC.** Checkout isolé add4/feature/operations-readiness, DraftPR15 https://github.com/TheoxProject/RaceAtlas/pull/15. Base/mainc74086365df62bf1c71623e080bb1f649c9981f5 ; local/origin avant publication98147ac78cf6d1051a21f5e9ae97a64122a5eead. Source B1 du checkpoint981 inchangée, nouveau test edge+docs seulement. CI43836355310 development/fullfallback SUCCESS936backend272,01s/118frontend, sourceguards avant/après ; pas verdict ni gate integrated du prochain SHA.

| Tâche | État |
|---|---|
| OPS-N1A fondation/ordre global | APPROVE ciblé exacta76, P2CLOSED ; pas fusion N1 |
| OPS-N1B-1 import/deltas/restauration present | Implémenté, ciblés acquis ; revue ciblée TODO |
| OPS-N1B-2 absencefinale/auditpur/capacité1000/1001 | TODO, non attribué |
| OPS-N2 API/UI Changements récents | TODO |
| OPS-E/B/V exploitation/backup/V1 | TODO |

[Mission B](../lot-8/sync-notifications-mission.md) du Coordinator préservée/incluse981 ; [handoff](../lot-8/developer-handoff.md) décrit signatures/transactions/limites et toutes commandes. Developer STOP après push/GEL exact, Root PR/CI et Tester au SHA courant. Aucun verdict précédent copié, B1 n'est ni N1 complet ni lot8 terminé.

## Livré

Inventaire frais chaque fenêtre, guards N1A numériques/rootDB avant premierflush/nested de fenêtre, reload sousgarde. Snapshot immutable parscopeID, wide vs règles/labels scoped, pas effet ordre/cache/centre seul. Evénements business parSourceRevision.id/provenanceimmuable ; replay/fraîcheur/reorder/création initiale sans alerte, reprise present distincte mêmeunchanged. Source/révision/event/cibles rollback jointdansSAVEPOINT. Budget source lock_timeout local3s, RCeffective ; timeout garde rollbackAVANTauditfailed et fenêtrescommittées préservées. Pas Account/fanout/mail source. Modèles/migrationb806/N1A/auth/ICS/frontend/API/CI/deps immuablesa76.

## Preuves et incidents conservés

Nominal initial4PASS/5FAIL5,79s (fixtures UTCsameinstant/JOINDiagnostic), puis8PASS/1FAIL6,20s (importfixtureoublié) et derniercasrollback1PASS7,16s ;9cas acquis via8+1 et tousverts dansCI981936backend. Compléments **6PASS12,874s**, JUnitops-n1b1-edges.xml : alias/cancelled/cache+gardePG3s/audit+2barrières saveavant/aprèscommit. Source/helper/testedge inchangés depuis ces preuves, réutilisation explicite.

Dernièrecommande12coutures avait été REJETÉEquota avantCreateProcess (aucuneexécution/session/JUnit), puis reprise explicite et ONErun réel session3636 terminéexit0 : **12PASS9,41s**,74deselected, .local-tools/ops-n1b1-sync-seams.xml. Aucun rerun6/8+1/927local. Ruff89 lint/format et contrats26 PASS ; range c740..HEAD àrevérifier aprèscommit également.

## Environnement et prochain geste sûr

Rootconciliation12:45UTC : aucunPython/Chrome/testPID, seulPG9780 clusterabsoluadd4/127.0.0.1:55434 ; `_test` et `_review` b806. Tous tests Developer sur_test uniquement, pas reset/reseed/oldcheckout/_review ni runtime retenu. Aucunecommandepending, barrières/workers fermés.

**Prochaineaction sûre : publier/GEL exact B1, Coordinator suitCI et renouvelle revue ciblée ; STOPsource ensuite.** Ne pas lancer B2 avant attribution, ni afficher notification absence comme livrée. N1final exigera B2+acceptation COMPLÈTE/integrated/mainCI avant N2. Aucun action réelle email/DNS/Resend/service/DBremote/deploy/collecte/payant/tagfinal.
