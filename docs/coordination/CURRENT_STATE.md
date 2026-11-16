# RaceAtlas — OPS-N1A candidat à figer

**16nov2026 07:46UTC.** Branche isolée add4/feature/operations-readiness, [DraftPR15](https://github.com/TheoxProject/RaceAtlas/pull/15). Base `c74086365df62bf1c71623e080bb1f649c9981f5`, mainCI43745685937SUCCESS891/118 ; local/origin avant publication `fb86117fc5408fc22ed5b5fce3ced8af2d6fce03`. CadrageCI43746572542 developmentSUCCESS118frontend/statiques/backendnone docs-only, pas validation du nouveau produit. SHA final communiqué au push puis aucune édition pendant revue.

| Tâche | État |
|---|---|
| OPS-N0 branche/Draft/cadrage | DONE |
| OPS-N1A modèles/migration/helpers/planning/baseline/projection | Implémenté, ciblés acquis ; revue ciblée TODO |
| OPS-N1B raccord sync/deltas/presence réels | TODO, non attribué |
| OPS-N2 API/UI Changements récents | TODO |
| OPS-E/B/V exploitation/backup-restauration/candidat V1 | TODO |

[Mission](../lot-8/mission.md), [handoff/interfaces/limites](../lot-8/developer-handoff.md), [commandes Windows](../lot-8/local-development.md). Developer seul writer jusqu'au push/GEL, Root PR/notes, Tester au SHA exact ensuite. Aucun APPROVE N1A, aucune fin N1/lot8 déclarée.

## Livré et décisions

RaceChange/ScopeChange/PersonalNotification + migration b806e44f7901 aprèsa74 ; FKcomposées exactes et cascade de SES notifications lors unsave/Accountdelete, ScopeRESTRICT et ICSledger préservés. Baseline anciennes0 sans default durable ; nouveau save prend maxsequence sous garde, statut/no-op préservent incarnation. Guards triés transactionnels avant DML, suivent Session ET Connection effective root/nested, hors contexte/rollback invalides ; multibind/AUTOCOMMIT/RR refusés. Privé Accountfirst aussi horsHTTP, validations pures avant SQL. Record idempotent par clé de mutation réelle, projection batch courante inserted/pending bornée sans drop/N+1/fanout Account. Aucun raccord sync, API, UI, auth sémantique, CI, dépendance ou collecte.

## Résultats réconciliés

- Initial12PASS14,053s, migration roundtrip fixture compris.
- Étendu97PASS/10FAIL73,175s conservé : lock trop tôt pour9IDs invalides ; fixture duplicate sans baseline pour1test. Corrigés sans assouplir assertions. Les97 verts couvrent backfill réel, ABA/deuxconnexions/barrières, cascades/FK/scopes/4statuts/epoch/ICS.
- Corrections23PASS17,186s :10défauts + nouveaux batch210/limites/séquence et modes effectifs Connection/RC/AUTOCOMMIT/RR. Aucun replay97 à reprise ; fichiers source/tests antérieurs au JUnit23, preuve explicitement réutilisée pour chemins inchangés.
-16nov Ruff lint/format86 et contrats26PASS ; diffcheck complet base..HEAD à vérifier après commit également. Nouvelle CI et verdict exact restent requis, jamais ancien verdict copié.

## Environnement et prochain geste sûr

Aucune commande/test pending, runtimes/browsers fermés. PG17 existant redémarré après interruption : incident port défaut corrigé par stop/start du SEUL serveur lancé, chemin absolu vérifié, options explicites -h127.0.0.1 -p55434. PID courant9780 ; lectures schéma `_test`=b806e44f7901 et `_review`=a74d915e3c02 (Reviewer aucune mutation). Pas initdb/reseed/réinstallation/ancienne copie utilisée.

**Prochaine action sûre : publier ce jalon, geler SHA et STOP ; Coordinator suit CI et demande revue indépendante ciblée N1A.** Ne pas reprendre N1B avant attribution/gate, ne pas relancer aveuglément les ciblés verts/full891. L'intégration N1 complète demandera N1B+acceptation finale/integrated/mainCI.

Décisions owner : Changements récents dans Ma saison/compteur/Marquer lues ; retrait scope retire ses messages sans toucher autres listes/comptes, re-add sans historique. Aucun choix produit restant ici. Aucun email réel/DNS/Resend/service/remoteDB/déploiement/collecte/tag final autorisé.
