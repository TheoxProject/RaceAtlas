# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-11T12:51:00Z**. Lot5 correction cycle1 en validation ; **aucun APPROVE ni merge lot5**.

## État réel et prochaine action

- Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche `feature/map-experience`, propre avant correction ; aucun autre writer.
- Base `origin/main` vérifiée : **3bd018bff1b60f3831606348831fd72375f557dd**, lots0–4 intégrés. PR https://github.com/TheoxProject/RaceAtlas/pull/7 encore Draft.
- Ancien candidat local/distant/revu : **4ce971f6a96d7d0ccbec75553db07f1f3389c388**. Tester **REQUEST CHANGES**, rapport `.local-tools/tester-report-lot5.md`. CI42996366566 :307PASS/6FAIL, parent ignoré de captures absent. Aucun résultat ancien n'approuve le remplaçant.
- Le commit contenant ce checkpoint publie les corrections ; relever son SHA local/distant/PR. CI du nouveau SHA à surveiller dès le push. Ne pas lancer les scripts PR des anciens lots.

| Tâche | État / preuve |
|---|---|
| L5-01/02/03 carte/API/détails | Livrés, puis défauts indépendants confirmés sur4ce |
| L5-C1 F1 dossier captures | Corrigé parents=True, cas sansWebGL autonome ; régression tmp_path à parent absent PASS |
| L5-C1 F2 crédits mobiles | Bande auto dimensionnée distincte du sheet, quatre liens hit-testés avant/exploration/détails PASS |
| L5-C1 F3/F4 périodes | Ancrage civil/ISO distinct, annéeISO explicite, saisies entières blur/Entrée ; NouvelAn2027→2026W53 et course multijour PASS |
| L5-C1 F5 OpenAPI | Sept textes UTF8 restaurés, aucun schéma/version changé ;26contrats PASS |
| L5-04 revue finale | TODO sur nouveau SHA figé après validations/documentation finales |
| L5-05 CI/fusion | TODO, gates exacts obligatoires |

**Prochaine action sûre unique :** après push du correctif, contrôler sa CI puis terminer la campagne locale complète sur `_test`, finaliser handoff/checkpoint et geler le SHA final pour Tester sur `_review`. Aucun merge sans APPROVE et CI verte au même SHA.

## Preuves du correctif et limites

Frontend23tests PASS11,57s après bornage final, lint/build PASS. E2E mobile et WebGL PASS ; nouveau parcours NouvelAn PASS12,65s avec parentcaptures absent, année civile2027, semaine2026W53, fixture multijour visible, décimales/vides/0/-1 rejetées, semaines inexistantes bornées et caméra exactement conservée. Baseline caméra après initialisation500ms du moteur ; attente marqueur+700ms avant snapshot, aucune tolérance ajoutée aux assertions existantes. Premiers attendus de test corrigés contre fixture réelle (une course multijour en2027, nom race-mtb-multiday), pas de comportement produit supprimé. Captures mobile et détails inspectées : crédits visibles au-dessous du panneau, scroll interne conservé.

Ancienne revue4ce :313pytest PASS189,57s dont9Chromium réel et migrations,26contrats,20frontend, Ruff37/ESLint/build/pip/diff PASS ; ces succès locaux ne masquent ni les défauts ni la CI propre en échec. Le correctif ajoute un dixième E2E ; campagne globale encore à exécuter, aucun314PASS revendiqué.

MapLibre5.11.0, Altitude initial/Summit à la demande, fournisseur Liberty/Mapterhorn ; catalogue/options additif1.0, collectionOpenAPI1.1, anciennes réponses1.0 inchangées. Migration couranteb7f4208ac112. Tests styles/DEM synthétiques interceptés, moteur WebGL réel. Qualification fournisseur historique limitée : Altitude réelle vue, Summit live expiré et non qualifié ; ne pas relancer aveuglément. Bundle environ1,18MB brut/331KB gzip, aucun benchmark matériel mobile exhaustif.

## Suite autorisée après intégration lot5

TODO : AGENTS/workflow validation progressive, surveillance CI après push et contrôle du SHA courant, tests main après merge ; README actualisé ; configuration Render Free monolithe Flask/Waitress + Neon TLS sans création/déploiement/mutation distante. Lot6 calendrier mensuel puis rapport pré-déploiement propriétaire ; lots7 comptes/planning/ICS puis8 exploitation/notifications/RC. Qualification FFC réelle limitée commencée par Coordinator, incompatibilités HTML/droits à documenter séparément ; aucun import live/récurrent/bulk autorisé.

Décisions propriétaire acquises : Altitude2,5D initial, Summit3D à la demande ; ouvrir le calendrier sélectionne le mois affiché et le conserve au retour carte, autres filtres/caméra préservés. Aucun arbitrage produit en attente.

## Environnement et restrictions

Python3.12.14 : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Node24.22.1 et frontend/node_modules réutilisés ; pnpm10.20 compatible en cache, ne pas utiliser wrapper11 contre store10. Chromium : `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`.

PostgreSQL17.11 actif uniquement `127.0.0.1:55434`, cluster `.local-tools/pgdata-lot2-native`, utilisateur `raceatlas_local`. Developer `raceatlas_lot2_test`, Tester `raceatlas_lot2_review`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Ne pas initdb/réinstaller/reseed aveuglément. Preview `_map_demo` séparée,12fixtures, pas de serveur persistant ; ancienne baseReviewer417synthétiques non pristine, fixtures de tests réinitialisent uniquement leur DB jetable. Aucun test Python actif lors de reprise ; nouvelles sessions Developer suivies et attendues avant handoff. Ne jamais arrêter tous les Node/Postgres.

Aucun reset/forcepush/main direct, déploiement, dépense, collecte FFC massive/récurrente, mutation distante ou tag/publication finale. Git natif/réseau et DB/browser nécessitent exécution native autorisée ; connecteur créationPR403 historique, fallback Git autorisé sans secret. Les scripts/rapports/captures ignorés ne sont pas des preuves de merge. Tester doit réapprouver le SHA final exact, même après simple commit documentaire.
