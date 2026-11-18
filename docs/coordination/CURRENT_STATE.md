# Lot 8 — sauvegarde approuvée, candidat local en validation

Point du **18 novembre 2026 à 07:46 UTC**. Worktree `add4`, branche `feature/operations-final-readiness`, [PR 17 Draft](https://github.com/TheoxProject/RaceAtlas/pull/17). Base `main` vérifiée `1f1d50b1395eaf271d1a22e255555cc027f34bf1`. Avant ce changement documentaire, HEAD et PR étaient au `958cc3c7fcea5d78b1575c838a9f44dd27ab3c30`. GitHub et Git donnent les références courantes.

| Tâche | État | Preuve ou condition restante |
|---|---|---|
| OPS-E erreurs et couverture | DONE | Revue ciblée `b338c87` et CI 44154102929. |
| OPS-B restauration synthétique | DONE au jalon `958cc3c` | Deux preuves natives distinctes passent. [Contre-revue](https://github.com/TheoxProject/RaceAtlas/pull/17#issuecomment-6972369820), 59 unités et 30 tables, 144 structures de contraintes, 4 séquences, 336 évaluations PostgreSQL, 7 scénarios DML et 21 contrôles API. [Validation B](../lot-8/backup-validation.md). |
| OPS-GUI diagnostic navigateur | IN_PROGRESS | Trois campagnes en échec. Les quatre scénarios passent en local au `933e8f0` sur `fix/browser-validation-diagnostics`. Une sonde isolée vérifie le chevauchement animation et redimensionnement. |
| OPS-V candidat et validation finale | IN_PROGRESS | [Matrice et recette](../readiness/release-candidate.md) préparées. Reporter les résultats navigateur et figer le SHA avant revue complète et CI `integrated`. |

**CI courante.** Run 44260218340 au `958cc3c` avec 1 076 tests backend réussis et 3 échecs navigateur en 450,25 s. Échecs sur le témoin janvier et la bascule Summit avant le scénario notifications desktop, ainsi que le même écart de centre mobile qu’en 44160225621. Les trois campagnes en échec utilisent l’image Ubuntu `20261111.370.1`, également verte sur `main` N2. Le résultat seul n’attribue pas la cause. Les tests de la sauvegarde passent.

**Environnement.** Python et Chromium existants réutilisés. PostgreSQL 17.11 PID 9780 sur `127.0.0.1:55434`. Les deux preuves ont terminé et leurs bases neuves et fichiers privés sont préservés. Les tests navigateur disposent de la base `_test` jetable et du build local compilé. La base `_review` reste réservée au testeur. Les archives ou manifestes de sauvegarde et secrets restent dans le dossier ignoré. Le testeur a libéré le SHA `958cc3c` après contrôle natif de ses processus.

**Prochaine action.** Lire la sonde de redimensionnement du worktree navigateur et décider d’un correctif ciblé si elle reproduit l’écart. Garder les seuils et assertions des tests. Les traces locales des trois autres parcours ne reproduisent pas leurs échecs CI. Publier le diagnostic retenu, puis figer le candidat pour revue finale et CI `integrated` une fois les régressions traitées. Les passages Ready et `main` nécessitent leurs propres contrôles.

**Périmètre d'exploitation.** Recette privée, création Render/Neon, migrations distantes, DNS, Resend réel, collecte FFC et publication finale nécessitent les accords prévus. Le lecteur FFC réel, les droits et capacités des fournisseurs et l’organisation des sauvegardes réelles restent à qualifier. Une CI verte en local ou sur GitHub ne valide pas ces conditions.
