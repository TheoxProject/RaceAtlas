# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-12T18:21:37Z**. Lots 0–6 et PRE-01 intégrés, **ACC-01 modèle/service/migration testés, à publier/geler pour revue ciblée et CI**. Lot 7 non terminé. Aucun déploiement.

## Git et prochaine action

Worktree isolé C:/Users/theop/.codex/worktrees/add4/RaceAtlas ; checkout personnel main préservé. Branche **feature/accounts-and-planning**, depuis origin/main **51856c9940a2b0e16c9f05d61a9f1726ae8701d9** après CI main verte. Parent local/distant **c9696821e7f01afc72ed30837ee5388fd71e5c48**, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/11. Developer seul writer, aucune commande Tester active ; changements WIP conservés avant tests, pas de verdict ou CI présumés.

**Prochaine action sûre :** publier ce jalon cohérent, transmettre son SHA gelé pour Tester/CI et arrêter les éditions. Aucun ancien verdict transféré ; aucune clôture globale lot 7. Aucun login/compte connecté temporaire, email réel, service/domaine/DNS ou DB distante.

| Tâche | État |
|---|---|
| ACC-00 mission/Draft | DONE, PR11 |
| ACC-01 identité et sauvegardes par scope | Testé, à publier/geler pour revue ciblée |
| ACC-02 credentials/sessions/CSRF/récupération | TODO, périmètre ultérieur |
| PLAN-01 API privée/statuts/ICS | TODO |
| ACC-UI parcours intégré | TODO |
| Expéditeur réel | BLOCKED, aucun domaine/expéditeur ; simulation locale non équivalente |
| ACC-FINAL | TODO, aucune clôture lot7 par simulation seule |

Mission : docs/lot-7/mission.md. Le service ACC-01 doit être privé/scoppé par acteur fiable, sans route auth factice ni header de bypass ; FKscope restrictif et preuve réelle de conservation favoris pendant sync. IDs source/listes non durables restent inconnus. Les phases suivantes sont détaillées après ce premier jalon.

Interface : `Account` opaque/email privé trim+lower unique, sans suppression de points/plus-tags, validation minimale non RFC/délivrabilité. L'acteur du service est obligatoirement un **Account persistant attaché à la même Session ORM** ; ACC-02 devra charger ce compte depuis l'auth serveur, jamais prendre un ID acteur de requête ou passer une instance détachée. `SavedEntry` stocke scope seul, FK RESTRICT, compte CASCADE privé, quatre statuts déclaratifs. Révision privée positive initiale 1, +1 uniquement sur vrai statut ; no-op garde ID/created/updated/revision. Upsert PostgreSQL atomique et rafraîchissement ORM déjà chargé ; aucun compteur public modifié. Migration `c40a7162b901` après `b7f4208ac112`. Fixtures test réinitialisent aussi account, sans changer les données source. Interface et commandes détaillées dans docs/lot-7/developer-handoff.md et local-development.md.

Avant tests : `pg_ctl status` a confirmé PostgreSQL existant PID 38028, port 55434 ; aucun pytest/Vitest/A-B concurrent. Caches réutilisés, `_test` uniquement, pas initdb ou campagne 389 complète. Premier run **36 PASS / 4 FAIL en 16,06 s** : timestamps PG retournés en fuseau Paris (deux cas), filtre API obligatoire manquant dans un test et diagnostic ambigu attendu incorrect. Conversion ORM UTC limitée aux nouveaux champs privés, gardant SQL timestamptz ; tests explicites UTC/Paris/Honolulu. Appel API/diagnostic de preuve corrigés. **43 ACC-01 PASS en 24,49 s**, **88 fondation/catalogue/snapshot PASS en 52,38 s**, code 0 ; cycles upgrade/check/downgrade base/upgrade/check réussis. Ruff lint/format **43 fichiers**, **26 contrats/diff PASS**. Aucun test actif. Isolation, contraintes, no-ops/révision, deux connexions concurrentes et vrais imports synthétiques (nom/report/réorganisation attestée/replay/refus/absence) exercés. Frontend et sources publiques inchangés, pas de build/rerun frontend local ; CI complète et revue exacte du nouveau SHA restent nécessaires.

## Intégrations vérifiées

- PRE-01 : PR10, APPROVE exact **0eab28197d8ea6443fa1f16e702e0b1a94585b3b**, merge **51856c9940a2b0e16c9f05d61a9f1726ae8701d9**, arbre égal **1af4c9ffc3d753df22c160670fa9d1a3b1c87885**. CI PR43272958804 SUCCESS389pytest202,50s/67frontend ; CI push main43273970329 SUCCESS389pytest167,19s/67frontend et gardes exactes avant/après. Preuves docs/readiness/predeployment-integration.md et PR. Rapport et régionFrankfurt/hrefattribution prêts, aucune activation.
- Lot6 : PR9, APPROVE **302462c006712ecd27f221f346d4f2e3d2c1d1ad**, merge **7b733d86d99a354fdcfe2bf1ecbde519ef78a68f**, CI PR43226499588 et main43227636726 vertes389/67. F6-01/02 clos cycle1, caméra10s/60°/DEM>100 inchangée. Docs/lot-6/integration.md. Budgets/tests ne sont pas SLA.
- Antérieurs : préparation PR8 et lot5 PR7 intégrés ; preuves docs/readiness/integration.md et docs/lot-5/integration.md. Ne pas rejouer anciens A/B Clock ni campagnes complètes inchangées sans raison.

## Décisions explicites et limites

Propriétaire : Altitude2,5D initial, calendrier ouvre le mois civil affiché et le conserve au retour Carte. Réponses12novembre : **email et mot de passe, récupération par email** ; **aucun domaine ni expéditeur** ; **premier déploiement privé après le lot8/candidat V1**. Cette planification n'autorise pas création de service, migration, envoi ou dépense. Aucun silence comme approbation.

Le développement local avec mailer simulé peut avancer indépendamment, sans prétendre expéditeur/délivrabilité validés. Aucun service email choisi/créé ou achat/DNS/envoi réel. Politique ICS et activation réelle à préciser au jalon concerné. FFC : deux pages limitées11nov échouent layout_changed/debut et html_structure ; droits et IDs de listes non établis, aucune collecte live activée. Mapterhorn attributionJSON403 noncontourné12nov, licences terrain détaillées non auditées ; href corrigé seul. Références dans rapport de pré-déploiement et qualificationFFC.

Déploiement, DB distante, paiement, email réel, collecte récurrente et tag/publication finale exigent toujours autorisation explicite. Lots7–8/RC non livrés par les préparations déjà fusionnées.

## Environnement et processus

Python3.12.14 : C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe (pas de pip module ; pipcheck via runtime --python). Node24.22.1/pnpm10.20.0/cache prêts ; wrapper11 incompatible à éviter. Chromium : C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers. Migration actuelle **b7f4208ac112**.

PostgreSQL17.11 existant127.0.0.1:55434, cluster .local-tools/pgdata-lot2-native, user raceatlas_local ; Developer raceatlas_lot2_test, Tester raceatlas_lot2_review avec RACEATLAS_DISPOSABLE_DB=1. Preview raceatlas_map_demo distincte. Vérifier statut/processus avant tests ; ne pas initdb/reseed aveuglément ou tuer tous les Node/PG. Dernier handoff PRE-01 : aucun test/server retenu, cluster conservé.

Git natif/DB/browser passent en exécution native autorisée. Création PR connecteur403 historique : fallback Git/GCM sans secrets et dans ses permissions. Helpers PR7/8/9/10 ont numéros/bases statiques, ne pas les utiliser pour fusionner une nouvelle PR. Pas de reset/forcepush/main direct. Notes ignorées lot7-architecture-notes.md (audit borné sync et sources primaires) utiles mais à convertir en preuves versionnées ; la mission contient déjà les invariants nécessaires.
