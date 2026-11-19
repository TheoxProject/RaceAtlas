# OPS-E — erreurs, couverture et quotas

Base intégrée `1f1d50b1395eaf271d1a22e255555cc027f34bf1`, main CI44150897395 SUCCESS1019backend/138frontend. Comparaison réelle avec cette base : diff nul sur `raceatlas/`, `frontend/`, `contracts/`, `migrations/`, requirements/constraints, ops/render.yaml/build.sh, workflows CI et les tests existants cités. Les preuves intégrées restent applicables à ces chemins ; elles ne constituent pas un nouveau verdict du candidat OPS-E.

| Critère | Preuve existante réutilisée | Vérification E |
|---|---|---|
| Import incomplet, dernier succès conservé, reprise honnête | `test_catalog_sync.py::test_coverage_uses_execution_order_retains_success_after_failure_then_recovers` | Réexécuté ; nouvelle couture `test_ops_errors.py` relie couverture publique et compteur privé exact |
| Source partielle/stale : pas de fausse absence/annulation/alerte | `test_sync_finalization.py::test_non_admissible_windows_do_not_infer_missing_and_coverage_is_incomplete` ; `test_sync_notifications.py::test_restoring_presence_records_even_when_business_unchanged` | Deux paramètres et restauration réexécutés ; journal vide après échec dans nouvelle couture |
| Commit incertain et audit vrai | `test_sync_commit_outcome.py` : vrai terminal puis accusé perdu, partial/failed compris ; précommit rollback ; confirmation inconnue et unlock défaillant | Réutilisé après diff nul, pas de nouvelle campagne. Une confirmation impossible reste outcome_unknown, jamais faux missing0 |
| Quotas/admission et fournisseur email simulé | `test_auth_http_email.py::test_provider_quota_failure_is_one_attempt_not_retry_and_probe_db_error_drops` ; `test_accounts_ui_e2e.py::test_browser_admission_clock_preserves_read_limit_and_recovers` ; `test_auth_http_foundation.py` sliding/capacity/rollback | Deux premiers réexécutés. Refus429 honnête/récupération après61s virtuelles limitées à admission, politiques20/60 inchangées ; aucun retry provider |
| Terrain/DB indisponibles, exploitation fermée | `test_e2e.py` DEM/base/WebGL/database_unavailable ; `test_foundation.py` erreur DB sûre ; `test_hosting.py` TLS/Basic/ready/startup sans migration | Réutilisés après diff nul et main CI ; pas de nouveaux browsers. Workflow CI relu : aucun schedule, collecte ou déploiement activé |

## Nouvelle couture unique

`tests/backend/test_ops_errors.py::test_incomplete_detail_preserves_saved_scope_then_real_recovery_notifies_once` utilise PostgreSQL et le vrai `synchronize`. Race retrouvée par SourceRecord provider/saison/clé, scope A par raw_label exact de l’observation connue ; scope frère distinct. Import valide puis sauvegarde planned, calendrier annonce la clé mais détail absent : coverage incomplete et ancien last_success conservé, course present/scheduled, zéro RaceChange et compteur privé0. Vrai changement de nom à la reprise : consistent_sample, une notification virtuelle sur LE scope suivi, cible frère exclue du DTO privé, PN toujours non matérialisées ; replay conserve événement/item/compteur.

Aucun faux HTTPFFC429 : la source est un contrat WindowBatch offline sans transport. Aucun changement runtime, politique, permission, migration, UI ou dépendance. Les sept tests ciblés ont passé en10,20s, JUnit ignoré `.local-tools/ops-e-targeted.xml`. Aucun échec lors de ce groupe. Détails des commandes dans le [compte rendu archivé](https://github.com/TheoxProject/RaceAtlas/blob/v1.0.0/docs/lot-8/errors-handoff.md).

## Limites

Aucun SLA ni quota réel fournisseur/team/IP/Render déduit de fixtures. Pas de qualification Render/Neon/TLS distante, ResendDNS/délivrabilité, droits de republication FFC, GPU physique ou sauvegarde externe. Pas de service/email/DNS/collecte/deploy activé. OPS-B et OPS-V restent séparés et TODO ; E exige sa revue ciblée exacte, puis l’ensemble final demandera integrated/Ready/main.
