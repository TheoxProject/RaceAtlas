# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-11T13:05:15Z**. Lot5 correction cycle1 validée localement, prête au gel/revue ; **aucun APPROVE ni merge lot5**.

## État réel et prochaine action

- Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche `feature/map-experience`, propre avant correction ; aucun autre writer.
- Base `origin/main` vérifiée : **3bd018bff1b60f3831606348831fd72375f557dd**, lots0–4 intégrés. PR https://github.com/TheoxProject/RaceAtlas/pull/7 encore Draft.
- Ancien candidat local/distant/revu : **4ce971f6a96d7d0ccbec75553db07f1f3389c388**. Tester **REQUEST CHANGES**, rapport `.local-tools/tester-report-lot5.md`. CI42996366566 :307PASS/6FAIL, parent ignoré de captures absent. Aucun résultat ancien n'approuve le remplaçant.
- Premier correctif publié : **00986e59d8ce882b7353d573cfa71f1f15e7116d**. CI43024003147 FAILURE313PASS/1FAIL : le test Summit lisait pitch35 avant fin animation500ms malgré DEM chargé. Le candidat remplaçant contient une attente bornée10s sur la caméra réelle pitch60, assertion exacte/élévation>100/mode conservés, plus initialisation once(style.load) et preuve fond retenu. Le commit contenant ce checkpoint est le candidat final : relever son SHA local/distant/PR et contrôler sa propre CI. Ne pas lancer les scripts PR des anciens lots.

| Tâche | État / preuve |
|---|---|
| L5-01/02/03 carte/API/détails | Livrés, puis défauts indépendants confirmés sur4ce |
| L5-C1 F1 dossier captures | Corrigé parents=True, cas sansWebGL autonome ; régression tmp_path à parent absent PASS |
| L5-C1 F2 crédits mobiles | Bande auto dimensionnée distincte du sheet, quatre liens hit-testés avant/exploration/détails PASS |
| L5-C1 F3/F4 périodes | Ancrage civil/ISO distinct, annéeISO explicite, saisies entières blur/Entrée ; NouvelAn2027→2026W53 et course multijour PASS |
| L5-C1 F5 OpenAPI | Sept textes UTF8 restaurés, aucun schéma/version changé ;26contrats PASS |
| L5-04 revue finale | TODO sur nouveau SHA figé après validations/documentation finales |
| L5-05 CI/fusion | TODO, gates exacts obligatoires |

**Prochaine action sûre unique :** Coordinator confirme le SHA final local/distant/PR, puis demande la revue indépendante de ce SHA au Tester sur `_review` et contrôle sa CI/base/mergeabilité. Éditions suivies arrêtées après ce push ; aucun merge sans APPROVE et CI verte au même SHA.

## Preuves du correctif et limites

**314pytest PASS198,74s sur code00986**, aucun skip, dont10parcours Chromium réels et migrations upgrade/check/downgrade/upgrade/check. Frontend23tests groupés PASS11,57s ;26contrats, Ruff37 lint/format, ESLint/build, pip/diff PASS. Après cette campagne : attente réelle pitch60 dans le test, puis initialisation MapView once(style.load)+guardactif afin de ne pas attendre les tuiles du fond. Source moteur épinglée confirme que load dépend de ces tuiles ; aucune causalité GPU n'est déduite du timeout natif isolé (un démarrage20s expiré, rerun unique PASS16,24s). Les10anciens E2E ont ensuite PASS, nouveau pending échoué sur wrapper builtin list.append du harness avant chargement ; corrigé en lambda, **ciblés pending+base_warning2PASS19,33s**, routes réellement retenues avant ready/API12/marker11 et abortcleanup. Aucun315global local revendiqué, CI complète du SHA final obligatoire.

Crédits mobiles hit-testés sur chaque lien, NouvelAn2027→2026W53/course multijour, décimales/vides/0/-1 et bornes invalides, caméra exacte, parentcaptures absent et WebGL autonome réellement vérifiés. Baseline caméra après marqueur+700ms pour la transition initiale500ms, aucune assertion existante affaiblie. Premiers attendus de test corrigés contre fixture réelle (une course multijour en2027, nom race-mtb-multiday). Captures mobile et détails inspectées : crédits visibles au-dessous du panneau, scroll interne conservé.

Ancienne revue4ce :313pytest PASS189,57s dont9Chromium réel et migrations,26contrats,20frontend, Ruff37/ESLint/build/pip/diff PASS ; ces succès locaux ne masquent ni les défauts ni la CI propre en échec. Nouvelle campagne globale314PASS puis E2E complémentaires distingués ci-dessus. Aucune approbation indépendante ni CI finale présumée.

MapLibre5.11.0, Altitude initial/Summit à la demande, fournisseur Liberty/Mapterhorn ; catalogue/options additif1.0, collectionOpenAPI1.1, anciennes réponses1.0 inchangées. Migration couranteb7f4208ac112. Tests styles/DEM synthétiques interceptés, moteur WebGL réel. Qualification fournisseur historique limitée : Altitude réelle vue, Summit live expiré et non qualifié ; ne pas relancer aveuglément. Bundle environ1,18MB brut/331KB gzip, aucun benchmark matériel mobile exhaustif.

## Suite autorisée après intégration lot5

TODO : AGENTS/workflow validation progressive, surveillance CI après push et contrôle du SHA courant, tests main après merge ; README actualisé ; configuration Render Free monolithe Flask/Waitress + Neon TLS sans création/déploiement/mutation distante. Lot6 calendrier mensuel puis rapport pré-déploiement propriétaire ; lots7 comptes/planning/ICS puis8 exploitation/notifications/RC. Qualification FFC réelle limitée commencée par Coordinator, incompatibilités HTML/droits à documenter séparément ; aucun import live/récurrent/bulk autorisé.

Décisions propriétaire acquises : Altitude2,5D initial, Summit3D à la demande ; ouvrir le calendrier sélectionne le mois affiché et le conserve au retour carte, autres filtres/caméra préservés. Aucun arbitrage produit en attente.

## Environnement et restrictions

Python3.12.14 : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Node24.22.1 et frontend/node_modules réutilisés ; pnpm10.20 compatible en cache, ne pas utiliser wrapper11 contre store10. Chromium : `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`.

PostgreSQL17.11 actif uniquement `127.0.0.1:55434`, cluster `.local-tools/pgdata-lot2-native`, utilisateur `raceatlas_local`. Developer `raceatlas_lot2_test`, Tester `raceatlas_lot2_review`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Ne pas initdb/réinstaller/reseed aveuglément. Preview `_map_demo` séparée,12fixtures, pas de serveur persistant ; ancienne baseReviewer417synthétiques non pristine, fixtures de tests réinitialisent uniquement leur DB jetable. Aucun test Python actif lors de reprise ; sessions Developer terminées code0, aucun test/serveur preview Developer restant après campagne. Ne jamais arrêter tous les Node/Postgres.

Aucun reset/forcepush/main direct, déploiement, dépense, collecte FFC massive/récurrente, mutation distante ou tag/publication finale. Git natif/réseau et DB/browser nécessitent exécution native autorisée ; connecteur créationPR403 historique, fallback Git autorisé sans secret. Les scripts/rapports/captures ignorés ne sont pas des preuves de merge. Tester doit réapprouver le SHA final exact, même après simple commit documentaire.
