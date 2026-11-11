# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-11T13:40:34Z**. Lots0–5 intégrés ; préparation V1 en cours, **aucun déploiement**.

## Git et tâche active

- Worktree isolé réutilisé après propreté/arrêt des tests : `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche **feature/v1-readiness**. Le checkout personnel main est préservé.
- Base locale/distante vérifiée : **5f8229245f31ff64f678cad9df331f7302bef76f** (`origin/main`). HEAD avant premier commit de préparation = cette base ; le commit contenant ce checkpoint sera le jalon RDY-01, à relever et publier avant revue.
- Nouvelle PR Draft à ouvrir après premier commit. Aucun SHA de préparation approuvé ; CI à contrôler après chaque push.
- Mission/critères : `docs/readiness/mission.md`. Notes techniques de préparation ignorées : `.local-tools/next-readiness-notes.md` ; ne pas les présenter comme configurations testées.

| Tâche | Responsable | État |
|---|---|---|
| RDY-01 politique progressive, README, intégration5, qualification FFC | Coordinator | IN_PROGRESS, documents préparés, revue ciblée à obtenir |
| RDY-02 CI SHA courant/échecs/main | Developer après libération | TODO |
| RDY-03 Render/Neon/TLS/build/start sans activation | Developer | TODO |
| RDY-04 preview privée/health/redémarrage/backup et tests locaux | Developer | TODO |
| RDY-05 revue finale/CI/fusion/main | Coordinator/Tester | TODO |
| Lot6 calendrier puis rapport pré-déploiement | Équipe | TODO après intégration/CI main ; décision de mois déjà acquise |

**Prochaine action sûre unique :** publier le premier commit documentaire et ouvrir sa Draft PR, surveiller sa CI puis demander une revue indépendante ciblée RDY-01 du SHA figé. Ne pas éditer les sources suivies pendant cette revue. Développer ensuite CI/configuration dans cette PR ; aucune fusion sur un seul avis intermédiaire.

## Lot5 réellement intégré

PR https://github.com/TheoxProject/RaceAtlas/pull/7, **APPROVE** indépendant exact **95bf1deabec10492100c0d6210dd3f30ccf57c3f**. CI https://github.com/TheoxProject/RaceAtlas/actions/runs/43029965848 **success** :315pytest156,61s,28frontend,26contrats/lint/build/dépendances verts. F1–F7 clos après trois cycles ; pas d'approbation par épuisement. Rapport final dans PR et `.local-tools/tester-report-lot5.md`, historiques initial/C1/C2 préservés.

Merge confirmé **5f8229245f31ff64f678cad9df331f7302bef76f** ; fetch et diff ont prouvé l'arbre identique au candidat approuvé. L'ancien workflow ne teste pas main après merge : aucune CI main prétendue, ajout demandé dans RDY-02. Preuves et limites dans `docs/lot-5/integration.md`. MapLibre5.11, caméra, scopes, pagination, crédits mobiles, nouveaux cas ISO/no-op et terrain réellement exercés. Dernière révision C3 seulement tests/docs ; centre toléré1e-9degré pour arrondi, autres champs stricts et reset réel rejeté.

## Décisions, qualification et suite

Propriétaire : **Altitude2,5D initial**, Summit3D à la demande ; ouvrir le calendrier sélectionnera le mois affiché et le conservera au retour carte, autres filtres/caméra préservés. Aucun arbitrage produit en attente.

Qualification FFC limitée du11novembre : robots et mentions consultés, deux exemples publics en mémoire seulement. Calendrier échoue `layout_changed/debut`, fiche `html_structure/html`, dialecte synthétique non qualifié live. Aucun HTML brut ou participant archivé ; aucune API/handler/login contacté. Voir `docs/readiness/ffc-qualification.md`. Droits de collecte récurrente/republication non établis : **blocage d'activation**, pas de contournement. Fixtures et travaux indépendants continuent.

Préparer Render Free monolithe Flask/Waitress + Neon TLS ; sources officielles consultées11novembre dans notes, limites à revérifier à l'utilisation. Aucun service créé ni distant connecté. Après lot6 : rapport propriétaire de pré-déploiement avant décision. Lots7 comptes/planning/ICS (expéditeur réel encore non validé),8 exploitation/notifications/backups puis RC. Publication/tag final, déploiement, dépense, mutation distante et collecte live récurrente restent non autorisés.

## Environnement et processus

Python3.12.14 : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Node24.22.1, frontend/node_modules réutilisés ; pnpm10.20.0 compatible en cache, wrapper11 incompatible avec store10 à éviter. Chromium cache `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Migration actuelle **b7f4208ac112**.

PostgreSQL17.11 existant seulement `127.0.0.1:55434`, cluster `.local-tools/pgdata-lot2-native`, utilisateur `raceatlas_local`. Developer `raceatlas_lot2_test`, Tester `raceatlas_lot2_review`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Les deux bases ont12fixtures après derniers tests ; elles sont jetables et distinctes. Preview `raceatlas_map_demo` séparée, aucun serveur actif. Aucun processus de test/preview Developer ou Tester laissé actif ; PostgreSQL conservé. Ne pas initdb/réinstaller/reseed aveuglément ni arrêter tous les Node/Postgres.

Git natif et DB/browser nécessitent exécution native autorisée. Connecteur création PR403 historique : fallback Git/GCM dans ses permissions réelles, sans secret affiché. Scripts PR anciens à base/numéro statiques : ne pas les réutiliser aveuglément pour la nouvelle PR. Aucun reset/forcepush/main direct.
