# OPS-B — candidat documentaire figé pour revue

2026-11-18 07:24 UTC. Worktree isolé add4, branche `feature/operations-final-readiness`, PR17 : https://github.com/TheoxProject/RaceAtlas/pull/17. Base/main `1f1d50b1395eaf271d1a22e255555cc027f34bf1`. HEAD/origin avant cette publication documentaire : `0f9af1b3a68601b7248d4e4ef2a1c4da9e760886`. SHA final exact communiqué au Coordinateur après commit/push ; Git et le head PR font autorité.

| Tâche | État |
|---|---|
| OPS-E erreurs/couverture/quotas | APPROVE ciblé6958216564 et CI44154102929 acquis |
| OPS-B sauvegarde/restauration synthétique | Preuve Developer PASS ; revue indépendante au nouveau SHA TODO |
| OPS-V matrice/candidat V1 | TODO, non attribué |

Preuve native5 au SHA propre0f9 ci-dessus, nonce20261117b0000005, session17219 exit0 :30tables/hashs/4séquences/144structures contraintes égales ;25CHECKtextuels différents déclarés (24casts+1AND),336domaines PG/7scénarios DML avec rollback/21contrôles API restaurées PASS. Empreinte des trois outils `e0317993d87cb8d63e85f28c123e506fdf5b118214cc924c934acaa7ffc9ca25`, revérifiée identique le18novembre. Diff nul code/outils/tests/CI depuis0f9 : six documents seulement finalisés, aucune nouvelle preuve ni test DB/GUI relancé.

Rapport public borné ignoré `.local-tools/ops-b-native5-public-result.json` ; rapport complet noms/hashesCHECK `.local-tools/backup-proof/20261117b0000005/report.json`. Archives/manifeste/passfile privés ne doivent pas être publiés. Quatre échecs natifs précédents conservés ; commandes et limites : [handoff B](../lot-8/backup-handoff.md), [validation](../lot-8/backup-validation.md). Ne pas réutiliser les DB/noms des anciennes preuves.

Contrôles locaux acquis :39unitPASS1,29s +3factoryPASS1,56s +10worker/envPASS1,09s (chevauche1 ; fichier51cas, pas52passes uniques), Ruff106/formatPASS, contrats26E réutilisés à diff nul. CI du code0f9, run44164167525/job134325641968 : SUCCESS1071backend374,56s/138frontend, gardes avant/après exactes. CI771 également verte ; les trois échecs GUI historiques de CIa750 restent inexpliqués et demandent une évaluation ciblée distincte. Aucun correctif GUI effectué dans B ; aucune suite actuelle présentée rouge ni cause déclarée résolue par un PASS ultérieur.

Environnement reconfirmé sans SQL : pg_ctl status18novembre, serveur EXISTANT PID9780, clusteradd4/127.0.0.1:55434. Aucun démarrage/réensemencement, aucun Python/Chrome actif ou commande de preuve pendante à la reprise. Tous runtimes et moteurs de la preuve avaient été fermés. _test/_review/preview non mutés pourB, seulement deux nouvelles bases par essai autorisé.

Prochain geste sûr : commit/push de ces seuls documents, vérifier range diff et nouvelle CI, communiquer SHA exact puis STOP éditions/libérer le worktree pour Reviewer B (autre nonce neuf, SHA figé). Ne pas relancer la preuve Developer pour la documentation, ne pas toucher aux scénarios GUI. Le verdict B et la CI du nouveau SHA ne sont pas présumés ; B ne termine pas V/PR17. Acceptation finale et integrated/Ready/main restent obligatoires.

Aucun email/DNS/achat/service/DB distante/liveFFC/déploiement/tag. La preuve locale ne résout pas l’incompatibilité FFC réelle déjà documentée, les droits/capacités fournisseurs ni la sauvegarde opérationnelle externe (chiffrement/rétention/stockage non qualifiés).
