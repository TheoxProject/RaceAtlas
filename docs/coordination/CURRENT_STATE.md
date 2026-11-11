# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-11T19:53:35Z**. Lots0–5 intégrés ; préparation V1 en cours, **aucun déploiement**.

## Git et tâche active

- Worktree isolé réutilisé après propreté/arrêt des tests : `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche **feature/v1-readiness**. Le checkout personnel main est préservé.
- Base locale/distante vérifiée : **5f8229245f31ff64f678cad9df331f7302bef76f** (`origin/main`). Dernier jalon local/distant RDY-01 : **136768cd6499f18858e27834926bd3bf216150f7**, CI43031656451 success, Tester APPROVE ciblé documentation/workflow ; ce verdict ne vaut pas approbation finale de la PR.
- Draft PR https://github.com/TheoxProject/RaceAtlas/pull/8. Dernier jalon local/distant RDY-02 : **1d33dc480b1cdc3f9de4a9c959788f6ad982d24b**, revue ciblée **APPROVE** (`.local-tools/tester-report-readiness-rdy02.md`) et CI43086393213 success,315pytest en128,50s et28frontend. Gardes de tête initiale/finale réellement exercées. Verdict intermédiaire, aucune approbation finale de la PR.
- Le commit contenant ce checkpoint publie le launcher et les configurations testées RDY-03/04. Relever son SHA local/distant/PR ; sa CI complète et une revue finale indépendante sont encore requises. Après ce push, éditions suivies arrêtées ; aucun résultat du jalon précédent approuve ce nouveau SHA.
- Mission/critères : `docs/readiness/mission.md`. Notes techniques de préparation ignorées : `.local-tools/next-readiness-notes.md` ; ne pas les présenter comme configurations testées.

| Tâche | Responsable | État |
|---|---|---|
| RDY-01 politique progressive, README, intégration5, qualification FFC | Coordinator | DONE, APPROVE ciblé136768cd, CI verte ; pas de verdict final |
| RDY-02 CI SHA courant/échecs/main | Developer | DONE, APPROVE ciblé1d33dc4 et CI verte ; aucun verdict final |
| RDY-03 Render/Neon/TLS/build/start sans activation | Developer | DONE local, launcher/config et preuves livrés ; revue/CI finales requises |
| RDY-04 preview privée/health/redémarrage/backup et tests locaux | Developer | DONE préparation : guard testé et procédures documentées ; aucun déploiement, handshake ou restore réel prétendu |
| RDY-05 revue finale/CI/fusion/main | Coordinator/Tester | TODO |
| Lot6 calendrier puis rapport pré-déploiement | Équipe | TODO après intégration/CI main ; décision de mois déjà acquise |

**Prochaine action sûre unique :** Coordinator confirme le SHA final local/distant/PR, surveille sa CI complète, puis demande la revue indépendante de tous les critères RDY-01–05 sur ce SHA. Aucun writer pendant revue, aucun merge sur un avis intermédiaire. Après merge éventuel, attendre les nouveaux contrôles `main` avant le lot6.

RDY-02 : checkout sur le head source exact d'une PR ou le SHA du `push`, sans credentials persistés ; garde de HEAD et de la ref PR publique au début/fin ; annulation des anciens runs et `push` sur `main` ajouté. Tous contrôles et le job `integrated` conservés, permissions `contents: read`. Échec : annotation/résumé du SHA, JUnit et copies de sept PNG synthétiques connus vers `RUNNER_TEMP`, rétention1jour ; pas de capture fournisseur, console/env ou dossier `.local-tools` entier. Aucune permission write, bot, schedule ou déploiement ajouté. Pipeline série fail-fast conservé.

RDY-03/04 : `raceatlas/serve.py` valide production, URL PostgreSQL complète avec `sslmode=verify-full`, CA absolue lisible, port et credentials preview avant `create_app`. Garde Basic obligatoire, aucun flag public ; seuls GET/HEAD exacts sans query sur `/api/health/live` sont exemptés. Comparaisons sur octets UTF-8, refus générique401 et réponses privées `no-store`. Waitress quatre threads ; application et pool catalogue inchangés. `ops/render.yaml` et `ops/build.sh` préparatoires, previews et auto-déploiement désactivés ; aucune migration ou seed au build/start. Guide `docs/readiness/hosting.md`, secrets vides dans `.env.example`, procédures migrations et sauvegardes séparées ; restauration complète encore à démontrer au lot8.

**70 tests hosting PASS en6,07s**, avec vraie intégration Flask/React compilé/PostgreSQL `_test`, migrations roundtrip, refus TLS/env/CA/ports réservés, préflight avant factory, startup sans connexion/migration/seed, Basic malformé/UTF-8, routes/assets et panne DB sans secrets. Ruff39 lint/format,26contrats, pip check et diff PASS. Build Vite réel PASS8,94s, mêmes assets frontend inchangés. Script Render : LF/syntaxe et trois commandes testées par stubs, fail-fast prouvé, aucune installation effectuée ; pas de build Render prétendu. Première tentative Bash sandbox refusée par MSYS, reprise native réussie. Parser `js-yaml` transitive déjà en cache retrouvé : CI et Blueprint parsés et contraintes critiques vérifiées, aucune dépendance ajoutée.17liens relatifs README/guide vérifiés sans cible absente. Aucun service créé, TLS Neon, déploiement, paiement ou mutation distante.

Sondes natives RDY-02 : scripts Bash PASS ; checkout136/refPR8 acceptés sans credentials ; mauvais SHA et refPR7 différente refusés code1 attendu ; chemin sansPR accepté. Staging : sept PNG seulement,683478octets, aucun provider/env. Scripts ignorés dans `.local-tools`, ainsi que `hosting-build-probe.py` et `readiness-yaml-check.cjs` pour le nouveau jalon. PyYAML était absent lors du premier jalon ; la validation YAML locale actuelle utilise le cache Node existant. Aucune campagne backend complète locale redondante, nouvelle CI complète obligatoire. Nit SHA intégration5 corrigé sur autorisation Coordinator.

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
