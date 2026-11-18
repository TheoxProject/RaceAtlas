# Lot 8 — sauvegarde approuvée, candidat local en validation

Point du **18 novembre 2026 à 08:07 UTC**. Worktree `add4`, branche `feature/operations-final-readiness`, [PR 17 Draft](https://github.com/TheoxProject/RaceAtlas/pull/17). Base `main` vérifiée `1f1d50b1395eaf271d1a22e255555cc027f34bf1`. Avant ce changement documentaire, HEAD local était au `e09a5ed` et la PR au `f77aa3d`. GitHub et Git donnent les références courantes.

| Tâche | État | Preuve ou condition restante |
|---|---|---|
| OPS-E erreurs et couverture | DONE | Revue ciblée `b338c87` et CI 44154102929. |
| OPS-B restauration synthétique | DONE au jalon `958cc3c` | Deux preuves natives distinctes passent. [Contre-revue](https://github.com/TheoxProject/RaceAtlas/pull/17#issuecomment-6972369820), 59 unités et 30 tables, 144 structures de contraintes, 4 séquences, 336 évaluations PostgreSQL, 7 scénarios DML et 21 contrôles API. [Validation B](../lot-8/backup-validation.md). |
| OPS-GUI diagnostic navigateur | IN_PROGRESS | Quatre scénarios passent sur le diagnostic isolé `933e8f0`. La sonde reproduit un déplacement pendant une animation sans changement de pitch. Correctif repris au `e09a5ed`, avec nouvelle régression et repli DEM réussis en 32,18 s. Les délais desktop restent à évaluer. |
| OPS-V candidat et validation finale | IN_PROGRESS | [Matrice et recette](../readiness/release-candidate.md) préparées. Reporter les résultats navigateur et figer le SHA avant revue complète et CI `integrated`. |

**CI.** Exécution 44262461031 sur le diagnostic publié `f77aa3d` avec 1 079 tests backend réussis en 359,20 s, dont les quatre scénarios navigateur, sur l’image Ubuntu `20261111.127.1`. Exécution précédente 44260218340 au `958cc3c` avec 1 076 tests backend réussis et 3 échecs navigateur en 450,25 s. Échecs sur le témoin janvier et la bascule Summit avant le scénario notifications desktop, ainsi que le même écart de centre mobile qu’en 44160225621. Les trois campagnes en échec utilisent l’image Ubuntu `20261111.370.1`, également verte sur `main` N2. Le résultat seul n’attribue pas la cause. Les tests de la sauvegarde passent.

**Environnement.** Python et Chromium existants réutilisés. PostgreSQL 17.11 PID 9780 sur `127.0.0.1:55434`. Les deux preuves ont terminé et leurs bases neuves et fichiers privés sont préservés. Le développeur navigateur a libéré `_test` et son worktree isolé. La base `_review` reste réservée au testeur. Le build issu du correctif est dans le `frontend/dist` ignoré du worktree isolé. Le build racine préexistant doit être vérifié avant une nouvelle preuve applicative. Le testeur a libéré le SHA `958cc3c` après contrôle natif de ses processus.

**Prochaine action.** Publier le correctif caméra testé et contrôler le nouvel SHA. Obtenir le verdict ciblé du testeur sur le correctif isolé et figer le candidat pour la revue finale et CI `integrated`. Les traces locales et la CI instrumentée ne reproduisent pas les délais desktop. Garder les seuils et assertions des tests, et traiter toute réapparition sur le candidat. Les passages Ready et `main` nécessitent leurs propres contrôles.

**Périmètre d'exploitation.** Recette privée, création Render/Neon, migrations distantes, DNS, Resend réel, collecte FFC et publication finale nécessitent les accords prévus. Le lecteur FFC réel, les droits et capacités des fournisseurs et l’organisation des sauvegardes réelles restent à qualifier. Une CI verte en local ou sur GitHub ne valide pas ces conditions.
