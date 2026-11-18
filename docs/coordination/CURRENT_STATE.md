# Initialisation du catalogue FFC 2027

Point du 18 novembre 2026 à 17:13 UTC. Base GitHub vérifiée `7f7cd9cd887c87fccfbe8f1537bd981c5eb778b1`. La CI `integrated` de cette base est [verte](https://github.com/TheoxProject/RaceAtlas/actions/runs/44346863088). Le propriétaire demande un chargement ponctuel depuis le HTML et a confirmé les droits de réutilisation. Le périmètre est l’année civile 2027, les douze départements d’Auvergne-Rhône-Alpes et les quatre disciplines V1.

| Tâche | État | Preuve ou condition restante |
|---|---|---|
| FFC27-01 Vérifier Neon et préparer le schéma | DONE | Connexion TLS directe à PostgreSQL 18 vérifiée sur la branche temporaire, puis sur `production/neondb`, initialement vide. Révision `b806e44f7901` confirmée sur les deux cibles. `alembic check` ne détecte aucun écart. |
| FFC27-02 Qualifier le lecteur public | DONE | Le développeur a livré `e0f195a65026bcb296f634eba16b41f5c186d70a`, repris au `30710f8`. Un calendrier et des fiches Route, Gravel et Cyclo-cross ont été vérifiés sur le site. Le VTT est couvert dans les tests synthétiques. |
| FFC27-03 Préparer le chargement et les contrôles | DONE | Six courses réelles ont été chargées sur la branche Neon temporaire. Le premier rejeu refusait cinq observations incomplètes. Après correction, deux rejeux ont retrouvé les six courses inchangées, sans doublon. Les deux réponses de catalogue étaient HTTP 200 avec six courses. |
| FFC27-04 Revoir et charger le catalogue | IN_PROGRESS | Revue indépendante et CI du SHA livré. Exécuter ensuite le chargement autorisé et vérifier le décompte, les exclusions et la réponse du catalogue de la base cible. |

Branche d’intégration `feature/ffc-2027-initial-catalog`, worktree `078f`, [PR 19 Draft](https://github.com/TheoxProject/RaceAtlas/pull/19). Aucun verdict indépendant sur le nouveau code. Les preuves exactes seront consignées dans la PR. Les dépendances Python 3.12.14 sont isolées sous `.local-tools/neon-runtime`. La branche Neon `raceatlas-initial-schema-check` expire le 18 novembre à 19:57 UTC. Les identifiants de maintenance restent dans l’environnement du processus.

**Prochaine action.** Publier le candidat puis vérifier la revue indépendante et la CI au SHA publié. Aucune course réelle n’a encore été chargée sur `production`. Vérifier le résultat du pilote avant tout rejeu. Le déclenchement récurrent requiert une autorisation distincte.
