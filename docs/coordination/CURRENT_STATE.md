# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-12T17:33:01Z**. **Lots 0–6 intégrés**, rapport pré-déploiement après lot 6 en préparation. Aucun déploiement.

## État Git et tâche active

- Worktree isolé : C:/Users/theop/.codex/worktrees/add4/RaceAtlas. Checkout personnel main préservé.
- Branche active : **feature/predeployment-report**, créée depuis origin/main **7b733d86d99a354fdcfe2bf1ecbde519ef78a68f**, propre avant cadrage. Le commit contenant ce checkpoint porte le cadrage initial ; relever son SHA local/distant et ouvrir la Draft PR avant implémentation.
- Mission : docs/readiness/predeployment-mission.md. Aucun agent n'édite actuellement les sources ; les tests/revues du lot 6 sont terminés et les sources libérées.

| Tâche | État | Responsable |
|---|---|---|
| PRE-00 cadrage et Draft | IN_PROGRESS | Coordinator |
| PRE-01 rapport/configuration/attribution | TODO | Developer à attribuer |
| PRE-02 revue exacte et CI | TODO | Tester/Coordinator |
| PRE-03 intégration/main et rapport propriétaire | TODO | Coordinator |
| Lot 7 comptes/planning/ICS | TODO | après ce jalon indépendant |
| Expéditeur réel du lot 7 | BLOCKED | aucun domaine/expéditeur disponible |

**Prochaine action sûre :** publier ce cadrage sur la branche et ouvrir sa Draft PR, puis attribuer PRE-01 au seul Developer. Vérifier le SHA distant et surveiller sa CI. Ne pas déployer, créer un service ou rejouer migrations/collectes externes.

## Intégration acquise du lot 6

PR https://github.com/TheoxProject/RaceAtlas/pull/9, APPROVE complet exact **302462c006712ecd27f221f346d4f2e3d2c1d1ad**, merge confirmé **7b733d86d99a354fdcfe2bf1ecbde519ef78a68f**. Arbres identiques df012a878751c156cbc481209c43e5a59c5a8a28. CI PR43226499588 SUCCESS :389pytest174,15s/67frontend ; CI push main43227636726 SUCCESS :389pytest178,34s/67frontend et gardes source avant/après. Preuve durable : docs/lot-6/integration.md et rapport complet PR.

Calendrier et carte partagent mois/filtres/loader/détails, multijour et scopes ; candidates rayon séparées. MapLibre/caméra/Summit conservés, mobile et crédits vérifiés. F6-01 titres globaux et F6-02 attente de sélection clos au cycle1 ; caméra10s/60°/DEM>100 inchangée, disponibilité sélection15s sans SLA. Mesures Dev3,672s/Tester13,625s non assimilées à performance production. Ne pas rejouer les six A/B Clock ni les campagnes inchangées sans nouveau besoin. Les deux CIs vertes intègrent les régressions complètes.

Lots antérieurs : préparation PR8 merge8ce46a3fc1129a905d2e9f1fc8552e3cf4d0a56f ; lot5 PR7 merge5f8229245f31ff64f678cad9df331f7302bef76f ; preuves dans docs/readiness/integration.md et docs/lot-5/integration.md. Politique progressive et CI du SHA courant/main déjà intégrées.

## Décisions et limites

- Propriétaire : Altitude2,5D initial ; ouvrir Calendrier depuis Année/Semaine sélectionne le mois civil affiché, conservé au retour Carte.
- Réponse propriétaire du12novembre : comptes **email et mot de passe avec récupération par email** ; **aucun domaine ni expéditeur pour le moment**. Aucun achat/compte externe/envoi réel autorisé. Développement indépendant avec simulateur local possible ; ne pas prétendre le prérequis expéditeur/délivrabilité validé.
- FFC : qualification ciblée11novembre a reproduit layout_changed/debut et html_structure ; droits/identifiants durables de listes non établis. Pas de live activé ou republication autorisée. Voir docs/readiness/ffc-qualification.md et docs/lot-0/open-questions.md.
- Render/Neon : configurations et lanceur privé préparés, sans création/build Render/handshake Neon/backup-restore externe. Limites officielles revérifiées12novembre, comptes/plafonds réels inconnus. Mapterhorn attribution JSON403 surGETstandard12novembre, aucun contournement ; licences complètes restent à qualifier avant activation. Sources et limites à intégrer au rapport PRE-01.
- Déploiement, mutations distantes, dépense, email réel, collecte récurrente et tag/publication finale nécessitent toujours l'autorisation propriétaire. Aucun silence ne vaut approbation.

## Environnement et processus

Python3.12.14 : C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe ; venv sanspip, pip check via runtime avec --python. Node24.22.1 et pnpm10.20.0/cache prêts ; ne pas réinstaller ni utiliser wrapperpnpm11 incompatible. Chromium cache : C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers. Migration b7f4208ac112.

PostgreSQL17.11 existant loopback127.0.0.1:55434, cluster .local-tools/pgdata-lot2-native, userraceatlas_local. Developer raceatlas_lot2_test ; Tester raceatlas_lot2_review avec RACEATLAS_DISPOSABLE_DB=1. Preview raceatlas_map_demo séparée. Vérifier pg_ctl/processus avant tests ; aucun test/server Developer/Tester retenu après revue finale. Ne pas initdb/reseed, tuer touslesNode/PG ou utiliser une DB distante. Les fixtures réinitialisent leur propre base jetable.

Git natif/DB/browser demandent exécution native autorisée. Connecteur création PR403 historique ; fallback Git/GCM dans ses permissions réelles, sans secrets imprimés. Helpers PR7/8/9 ont numéros/bases statiques : ne pas lancer leurs opérations de fusion pour la nouvelle PR. Aucun reset/forcepush/main direct. Notes ignorées utiles : .local-tools/predeploy-after6-research.md et lot6-planning.md ; elles ne remplacent pas les preuves Git/CI.
