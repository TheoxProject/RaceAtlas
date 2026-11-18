# Initialisation du catalogue FFC 2027

Point du 18 novembre 2026 à 16:58 UTC. Base GitHub vérifiée `7f7cd9cd887c87fccfbe8f1537bd981c5eb778b1`. La CI `integrated` de cette base est [verte](https://github.com/TheoxProject/RaceAtlas/actions/runs/44346863088). Le propriétaire demande un chargement ponctuel et a confirmé les droits de réutilisation. Le périmètre est l’année civile 2027, les douze départements d’Auvergne-Rhône-Alpes et les quatre disciplines V1.

| Tâche | État | Preuve ou condition restante |
|---|---|---|
| FFC27-01 Vérifier Neon et préparer le schéma | IN_PROGRESS | Projet Free `raceatlas`, branche `production`, base `neondb` vide au contrôle préalable. Sur une branche temporaire PostgreSQL 18, la connexion TLS directe, la migration `b806e44f7901` et `alembic check` passent. Appliquer puis vérifier la même chaîne sur la cible. |
| FFC27-02 Qualifier le lecteur public | IN_PROGRESS | Fenêtres civiles effectives confirmées en Isère sur un intervalle de 14 jours. Le lecteur synthétique ne reconnaît ni le calendrier ni la fiche réelle. Le développeur travaille sur `feature/ffc-2027-reader` dans le worktree `.local-tools/ffc-reader`. |
| FFC27-03 Préparer le chargement et les contrôles | TODO | L’import existant est local. Préparer un lancement opérateur, sans ordonnanceur, qui utilise les observations positives et conserve les anomalies de couverture. Vérifier idempotence, provenance, fenêtres, admissibilité et décompte. |
| FFC27-04 Revoir et charger le catalogue | TODO | CI intégrée et revue indépendante du SHA final. Répéter sur un environnement jetable puis vérifier la cible et les parcours API après chargement. |

Branche d’intégration `feature/ffc-2027-initial-catalog`, worktree `078f`. Aucune revue du nouveau code ni CI de la branche à ce point. La CI du SHA final et les verdicts seront consignés dans la PR. Les dépendances Python 3.12.14 sont isolées sous `.local-tools/neon-runtime`. La branche Neon `raceatlas-initial-schema-check` expire le 18 novembre à 19:57 UTC. Les identifiants de maintenance restent dans l’environnement du processus.

**Prochaine action.** Après confirmation de la réussite d’Alembic sur la branche temporaire, appliquer la chaîne au schéma vide de `neondb` sur `production` et confirmer la révision et l’état du catalogue. Vérifier la cible et les tables avant toute reprise. Le premier chargement restera ponctuel et la synchronisation récurrente requiert une autorisation distincte.
