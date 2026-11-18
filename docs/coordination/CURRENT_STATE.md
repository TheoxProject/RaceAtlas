# Initialisation du catalogue FFC 2027

Point du 18 novembre 2026 à 17:49 UTC. Base GitHub vérifiée `7f7cd9cd887c87fccfbe8f1537bd981c5eb778b1`. La CI `integrated` de cette base est [verte](https://github.com/TheoxProject/RaceAtlas/actions/runs/44346863088). Le propriétaire demande un chargement ponctuel depuis le HTML et a confirmé les droits de réutilisation. Le périmètre est l’année civile 2027, les douze départements d’Auvergne-Rhône-Alpes et les quatre disciplines V1.

| Tâche | État | Preuve ou condition restante |
|---|---|---|
| FFC27-01 Vérifier Neon et préparer le schéma | DONE | Connexion TLS directe à PostgreSQL 18 vérifiée sur la branche temporaire, puis sur `production/neondb`, initialement vide. Révision `b806e44f7901` confirmée sur les deux cibles. `alembic check` ne détecte aucun écart. |
| FFC27-02 Qualifier le lecteur public | DONE | Le développeur a livré `e0f195a65026bcb296f634eba16b41f5c186d70a`, repris au `30710f8`. Un calendrier et des fiches Route, Gravel et Cyclo-cross ont été vérifiés sur le site. Le VTT est couvert dans les tests synthétiques. |
| FFC27-03 Préparer le chargement et les contrôles | DONE | Six courses réelles ont été chargées sur la branche Neon temporaire. Le premier rejeu refusait cinq observations incomplètes. Après correction, deux rejeux ont retrouvé les six courses inchangées, sans doublon. Les deux réponses de catalogue étaient HTTP 200 avec six courses. |
| FFC27-04 Revoir et charger le catalogue | IN_PROGRESS | La revue de `75d6ef9` a relevé la perte possible du diagnostic de couverture. Le correctif passe 9 contrôles ciblés. La revue de `8956ca1` a passé 196 tests et demandé une correction de la lecture des restrictions et badges. Le développeur a livré cette correction au `d57b551`, repris au `f38860d`, avec 18 tests lecteur réussis. Renouveler la revue et la CI sur le nouveau SHA. |

Branche d’intégration `feature/ffc-2027-initial-catalog`, worktree `078f`, [PR 19 Draft](https://github.com/TheoxProject/RaceAtlas/pull/19). Aucun verdict indépendant sur le nouveau code. Les preuves exactes seront consignées dans la PR. Les dépendances Python 3.12.14 sont isolées sous `.local-tools/neon-runtime`. La branche Neon `raceatlas-initial-schema-check` expire le 18 novembre à 19:57 UTC. Les identifiants de maintenance restent dans l’environnement du processus.

Un chargement extérieur à cette PR a ajouté 42 courses à la base cible avant la reprise, dont trois de l’année civile 2027. Le contrôle n’a relevé aucun import audité ni connexion concurrente active à cet instant. Les lignes existantes seront conservées.

**Prochaine action.** Publier le correctif et relancer la revue sur ce SHA. Lire le catalogue public et garder les observations en mémoire jusqu’à validation du commit. Vérifier à nouveau la cible, puis exclure les identités déjà présentes avant l’écriture. Le déclenchement récurrent requiert une autorisation distincte.
