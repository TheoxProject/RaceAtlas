# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-12T07:27:49Z**. Lots0–5 et préparation V1 intégrés ; **lot6 CAL-01 validé localement, prêt pour gel/revue ciblée**. Aucune UI calendrier ni déploiement encore livré.

## Git et tâche active

- Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, réutilisé propre après arrêt des agents/tests ; branche **feature/monthly-calendar**. Le checkout personnel main reste préservé.
- Base locale/distante vérifiée : **8ce46a3fc1129a905d2e9f1fc8552e3cf4d0a56f**, `origin/main`, CI main verte. Dernier cadrage local/distant : **3f454b0f98f19883c915b9bda28fadb39aca11fd**, CI43094428404 success ; cette preuve initiale ne valide pas le helper suivant.
- Draft PR https://github.com/TheoxProject/RaceAtlas/pull/9. Le commit contenant ce checkpoint publie CAL-01 : relever son SHA local/distant/PR et sa propre CI. Aucun SHA lot6 approuvé. Mission : `docs/lot-6/mission.md`, handoff et usage local ; planning indépendant ignoré `.local-tools/lot6-planning.md`.

| Tâche | Responsable | État |
|---|---|---|
| CAL-00 mission/checkpoint/Draft | Coordinator | DONE, PR9 et CI de cadrage vérifiées |
| CAL-01 dates/projection/état partagé | Developer | DONE local,32tests PASS ; revue ciblée du nouveau SHA TODO |
| CAL-02 calendrier responsive/détails/parité | Developer | TODO |
| CAL-03 intégration/captures/revue finale/CI | Developer/Tester | TODO |
| CAL-04 fusion/main et rapport pré-déploiement | Coordinator | TODO ; aucune activation autorisée |

**Prochaine action sûre unique :** Coordinator confirme le SHA CAL-01 publié et surveille sa CI, puis demande sa revue indépendante ciblée. Éditions suivies arrêtées après ce push. CAL-02/UI ne commence qu'après libération explicite ; le lot nécessitera encore un APPROVE complet du SHA final, aucune fusion sur ce jalon intermédiaire.

CAL-01 : uniquement `frontend/src/calendar.js`, ses tests et trois documents du lot. `catalog.js` et App/MapView/Filters/CSS inchangés. Fonctions pures réutilisant `changePeriod`/`periodRange` : mois civil partagé, navigation bornée1900–2200, grille UTC lundi–dimanche, hors mois distincts/sans épreuve, clipping multijour inclusif et déduplication par raceID. Les objets API et témoins de scope restent intacts. En rayon, candidates non localisées séparées des cellules/totaux confirmés ; hors rayon elles restent dans le calendrier. Aucun calcul d'admissibilité client ni appel API/DB.

**32 tests calendrier PASS3,27s, code0 le12novembre**, fichiers préservés après interruption ; couverture bissextiles/siècles, mois aux limites dimanche,2026-12-31..2027-01-02, frontière Paris/ISO, identité des no-ops, vrais changements/bornes, total distinct et scopes/candidates. ESLint/build PASS7,75s et26contrats/diff PASS acquis le11novembre sur les mêmes fichiers avant interruption ; aucune campagne385backend redondante. Run groupé calendar+catalog bloqué au démarrage du second worker :31tests calendrier avaient passé mais run **NON PASS**, arrêté seulement après vérification NodePID34828/parent38448/commande exacte, session25917 exit1. Reprise isolée32PASS3,62s puis confirmation12novembre3,27s ; aucun paramètre Vitest modifié. Dernier runner isolé terminé code0, aucun processus Developer laissé actif. Aucune UI, capture ou intégration calendrier prétendue avant CAL-02/03.

## Intégrations acquises

**Préparation V1 DONE** : https://github.com/TheoxProject/RaceAtlas/pull/8. SHA approuvé **dd80392605cb41ea995a0226eb89486cf1f00918**, merge confirmé **8ce46a3fc1129a905d2e9f1fc8552e3cf4d0a56f**, arbre identique vérifié. CI PR43091426728 success (385pytest125,09s,28frontend,26contrats/lint/build/dépendances). **CI push main43092874749 success**,385pytest154,02s/28frontend, gardes source8ce46a3 avant/après réellement exécutées. Tester APPROVE exact :70hosting,349 sondes indépendantes, scripts/YAML/liens, preuves RDY-01/02 explicitement réutilisées. Rapport dans PR et `.local-tools/tester-report-readiness.md` ; intégration `docs/readiness/integration.md`.

Livré : politique progressive, README actuel, CI du SHA courant et de main, diagnostics synthétiques bornés ; configuration Render Free/Neon TLS et lanceur privé obligatoire, guides opérateur. Ni build Render complet, handshake Neon, backup/restore exécuté ou compte/service distant créé. Restauration complète au lot8 ; rapport propriétaire après6 avant toute demande d'activation.

**Lot5 DONE** : https://github.com/TheoxProject/RaceAtlas/pull/7. APPROVE exact **95bf1deabec10492100c0d6210dd3f30ccf57c3f**, CI43029965848 success (315pytest/28frontend), merge **5f8229245f31ff64f678cad9df331f7302bef76f**, arbre identique vérifié. F1–F7 clos, caméra réelle/Summit/credits/ISO/no-op et 11 parcours WebGL exercés. Preuves `docs/lot-5/integration.md` et rapport PR. Lots0–4 déjà intégrés.

## Décisions et risques ouverts

Propriétaire : **Altitude2,5D initial**, Summit3D à la demande. Ouvrir le calendrier depuis Année/Semaine sélectionne le mois affiché ; revenir à la carte conserve ce mois, les autres filtres et la caméra. Aucun arbitrage produit en attente. Calendrier mensuel unique, pas page liste distincte. Multi-jour et catégories ET sur même scope restent invariants.

FFC : qualification ciblée du11novembre a reproduit `layout_changed/debut` calendrier et `html_structure/html` fiche ; dialecte synthétique non qualifié live. Aucun HTML brut/participant archivé. Droits de collecte/réutilisation incertains : activation bloquée, travaux indépendants sur fixtures autorisés. Voir `docs/readiness/ffc-qualification.md`. Qualification Summit live/matériel mobile et licences finales restent à compléter avant release.

Après6 : rapport pré-déploiement concret avec limites/risques/coûts/protection/tests, sans créer de service. Lot7 comptes/planning/ICS : expéditeur réel non validé ; conserver portée par scope et inscription déclarative. Lot8 notifications internes et exploitation/backup/restore puis RC. Publication/tag final, déploiement, dépense, mutations distantes et collecte récurrente nécessitent toujours l'autorisation explicite propriétaire ; son silence ne vaut pas accord.

## Environnement et processus

Python3.12.14 réutilisé : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Pip via runtime `-m pip --python <venv> check` (venv sans module pip). Node24.22.1, frontend/node_modules et pnpm10.20.0 en cache ; wrapper11 incompatible store10 à éviter. Chromium cache `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Migration actuelle **b7f4208ac112**.

PostgreSQL17.11 existant sur **127.0.0.1:55434**, cluster `.local-tools/pgdata-lot2-native`, utilisateur `raceatlas_local`. Developer `raceatlas_lot2_test`, Tester `raceatlas_lot2_review` ; URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, `RACEATLAS_DISPOSABLE_DB=1`. Seulement données synthétiques ; les fixtures réinitialisent leur propre base jetable. Preview `raceatlas_map_demo` séparée ; aucun serveur ni test Developer/Tester actif après handoffs. PostgreSQL conservé, ne pas initdb/reseed/réinstaller aveuglément ou arrêter tous les Node/Postgres.

Git natif et DB/browser demandent exécution native autorisée ; connecteur création PR403 historique, fallback Git/GCM dans ses permissions réelles sans secrets exposés. Les helpers PR anciens sont à numéros/bases statiques : ne pas lancer ceux des PR7/8 pour le lot6. Aucun reset/forcepush/main direct. Les notes/rapports ignorés ne remplacent pas GitHub et les preuves exécutées.
