# OPS-N1B-1 WIP — nominal intégré, preuves complémentaires TODO

16nov2026. feature/operations-readiness/DraftPR15/basec740 ; HEAD/origin avantcheckpointa76e35a5e11ad86362c4716e344c3f6c0037eabe. N1A APPROVE exact/CI43829642340developmentfull927/118 historiques, pas validation du nouveau SHA. Developer seulwriter, RootPR/notes, Tester au gel. Mission sync-notifications-mission.md du Coordinator préservée et incluse à ce checkpoint.

Source B1 raccordée : inventaire courant chaque fenêtre/guards avantflush+nested/RC+budgetlocal3s ; snapshot detachedfrozen parscope, révision/provenanceimmuables, vraie restaurationpresent distincte ; rollbacksource+record dansmêmeSAVEPOINT. Aucun modèle/migration/planning/notifications/auth/API/UI/CI/deps modifié. N1B2 finalto_verify/auditpur/capacité NONattribué.

Résultats nominaux : initial4PASS/5FAIL5,79s (fixtures comparaisonmêmeinstanttimezone+JOINaudit) ; puis8PASS/1FAIL6,20s (importImportWindowoublié) ; derniercasrollbackreciblé1PASS7,16s. Donc9cas nominaux réellement exercés verts via8+1, pas faux9PASSunique. Règles scoped/reorder/report/4statuts/ABAderuns/création2fenêtres/restaurationpresent/rollbackevent prouvés ; aucun verdictcopié. RuffcibléPASS. Pas de testpending ; _testb806/PG9780, _review réservé.

Prochaineaction sûre : publier ceWIP cohérent pourCI, puis compléterbarrières saveavant/aprèscommit, vraiecontentiongarde3s/audit, alias/cancelled/cache et couturesSync ciblées ; pasfull927local. Aucun gel final B1 ni notificationabsencefinale revendiqués, aucunlive/mail/DNS/remoteDB/deploy.

## Cadrage et historique conservés
# RaceAtlas — lot8 OPS-N1B-1 en cadrage

16nov2026 08:47UTC. Branche isolée feature/operations-readiness, DraftPR15 https://github.com/TheoxProject/RaceAtlas/pull/15. HEAD/origin a76e35a5e11ad86362c4716e344c3f6c0037eabe avant nouveau travail ; base/main c74086365df62bf1c71623e080bb1f649c9981f5. Root vient de rédiger mission N1B, pas encore code source B. Après transfert Developer seul writer suivi, Root PR/notes et Tester au gel.

## Acquis exacts

N1A APPROVE ciblé renouvelé exacta76, [rapport](https://github.com/TheoxProject/RaceAtlas/pull/15#issuecomment-6911659509). P2 ancien5d8 deadlock40P01 fermé par sonde indépendante (ChangeError immédiat/session utilisable, caller rollback libère autre transaction, pas sauvegarde partielle). Ancien REQUESTCHANGES et preuves préservés. CI43829642340 development/full SUCCESS927backend346,25s/118frontend/guards/statiques, Ubuntu24.04. DEV ne vaut pas gate integrated final. Reviewer30PGPASS, durée suite1256,85s anormale après interruption outil sans cause/SLA ;114 anciens explicitement réutilisés après diff nul. Source RELEASED, aucun test restant.

PR14/lot7 local intégré c740, mainCI43745685937SUCCESS891/118 ; [preuve durable](../lot-7/accounts-ui-integration.md). Aucune activation réelle des emails.

## Mission et statuts

[Mission générale](../lot-8/mission.md), [mission N1B](../lot-8/sync-notifications-mission.md), [handoff N1A](../lot-8/developer-handoff.md).

| Tâche | État |
|---|---|
| OPS-N0 cadrage/branche/Draft | DONE |
| OPS-N1A fondation/migration/locks/projection | DONE ciblé exacta76, pas fusion N1 |
| OPS-N1B-1 fenêtres/deltas business/restauration present | IN_PROGRESS interfaces fixées dans developer-handoff avant code, source encore TODO |
| OPS-N1B-2 finalisation présence/audit/capacité | TODO, non attribué |
| OPS-N1 final PR15 | TODO acceptation complète/integrated/fusion/main |
| OPS-N2 API/UI Changements récents | TODO |
| OPS-E/B/V erreurs/backup-restore/candidat V1 | TODO |

Décisions propriétaire : Changements récents dans Ma saison, compteur et Marquer comme lues ; retirer une sauvegarde retire SES messages, autres scopes/comptes préservés, réajout baseline fraîche. Pas question produit en attente. Pas source live/scheduler/email course. Conserver _apply/audit/idempotence/commits fenêtre et préflight identités.

## Environnement et prochain geste

PG17 existant add4/.local-tools/pgdata-lot2-native, dernierPID9780, écoute127.0.0.1:55434 ; bin/venv Python et caches Node/browsers worktree1a1e. _test Developer et _review Tester tous deuxb806e44f7901 ; pas ancien checkout contre ce schéma. Aucun Python/Chrome/worker actif au transfert, runtimes fermés avant Engines ; vérifier avant reprise, pas initdb/reseed/piddelete. Copie personnelle main et autres worktrees intacts.

Prochaine action sûre : transférer N1B-1 borné au Developer, consigner interfaces/source-snapshot avant code puis raccord fenêtre/_apply et ciblésPG. Mission+checkpoint Root seront inclus au prochain commit cohérent Developer, aucun verdict N1A copié au prochain SHA. Push/jalons et CI inspectés, gel/revue ciblée B1 avant B2 ; final N1 complet avec integrated/main avant N2. Ne pas relancer927 tests locaux par routine.

Resend Free/domainemailraceatlas.ucthonon.fr non activé, APP_BASE_URL Render inconnue, droits source/terrain et capacité réelle Free encore à qualifier. Aucun email réel/DNS/service/remoteDB/deploy/collecte/tagfinal autorisé. Quotas non mesurables, pas de reprise automatique promise.
N1B1 premier groupe :4PASS/5FAIL5,79s (.local-tools/ops-n1b1-initial.xml), migration b806 inchangée. Quatreasserts comparaient UTC normalisé à affichage PGEurope/Paris même instant ; cinquième requêtefixture utilisait ImportItem.run_id inexistant, JOINImportWindow corrigé. Aucun changement produit pour ces échecs. Prochaineaction : recible9nominales puis checkpointWIP/push, preuvesbarrières/timeout/alias/cache/scopedcancelled encoreTODO. Pasfull927local ni repriseautrecommandeactive.
