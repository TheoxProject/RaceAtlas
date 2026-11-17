# Lot8 — préparation opérationnelle finale, cadrage

17nov2026 18:55UTC. Branche feature/operations-final-readiness, worktree isolé add4. HEAD/base avant cadrage **1f1d50b1395eaf271d1a22e255555cc027f34bf1**, origin/main identique après fetch et mainCI44150897395 SUCCESS1019backend467,95s/138frontend. N2 PR16 intégré, arbre0ea469ff584d9b3cfa90a16c5e5a8e3e8212142f et [preuves durables](../lot-8/n2-integration.md). Nouvelle Draft PR à ouvrir après commit de cadrage ; aucun code E/B/V implémenté.

| Tâche | État |
|---|---|
| OPS-N1 journal/sync/baselines | DONE intégré PR15/main vert |
| OPS-N2 backend/UI notifications | DONE intégré PR16/main vert |
| OPS-E erreurs/couverture/quotas | TODO, premier jalon borné à attribuer |
| OPS-B preuve dump/restauration locale | TODO, après revue ciblée E |
| OPS-V matrice/candidat V1 | TODO, consolidation E/B et preuves existantes |

[Mission finale](../lot-8/operations-final-mission.md). E/B/V regroupés en PR opérationnelle cohérente ; gels/revues ciblées E/B, acceptation complète finale +ci:full/integrated/Ready/main. Root seul writer du cadrage, transfert Developer seul writer après Draft. Tester STOP jusqu'au gel E. Aucun précédent verdict transféré à un futur SHA.

Prochain geste sûr : commit/push cadrage, ouvrir Draft et inspecter sa CI, puis attribuer E (au plus1couture importincomplet→pasfaussealerte→reprise/replay). Réutiliser les preuves d'erreurs existantes après diff vérifié. Ne pas inventer transport HTTPFFC429 ni modifier runtime/politiques/UI pour ce test.

Environnement à vérifier avant tests : PG17 localadd4/.local-tools/pgdata-lot2-native, dernierPID9780/127.0.0.1:55434, _test Developer/_review Tester b806, preview ancienne intacte. Python/Node24/pnpm10/browsers1a1e réutilisables. Aucun test/serveur de cadrage ; vérifier natif avant réemploi, pas initdb/reseed/piddelete/anciencheckout ; runtime.close avant engines. B n'utilisera que deux bases locales NEUVES synthétiques. Aucun dump privé/token dans Git/artefacts publics.

N2 rapports/CI/échecs conservés. Main/Ready/app external restent distincts : aucun achat, DNS, email réel, service, DB distante, déploiement, collecte live ou tag final autorisé. ResendFree/raceatlas.ucthonon.fr préparés nonactivés, APP_BASE_URL Render réelle inconnue, qualifications fournisseurs/GPU/capacité/backup externe à faire avant activation. Quota nonmesurable, pas de reprise automatique promise.
