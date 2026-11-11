# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-11T09:34:00Z**. Lot5 carte interactive prêt pour gel/revue ; **pas encore approuvé ni intégré**.

## Git, tâches et action suivante

- Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche `feature/map-experience`.
- Base locale/distante vérifiée `origin/main` : **3bd018bff1b60f3831606348831fd72375f557dd**.
- Dernier jalon code local/distant testé : **7f85cf4df97adf110e1fe10f9e75606cfa777583**. Le commit contenant ce checkpoint et le handoff final est le candidat ; relever `git rev-parse HEAD` et comparer distant/PR avant revue.
- Draft PR https://github.com/TheoxProject/RaceAtlas/pull/7. Ancienne CI34a21db en échec42984715747 sur WIP ; aucune ancienne CI n'est une validation du candidat final. **CI du SHA final à contrôler.**
- Références : `docs/lot-5/mission.md`, `developer-handoff.md`, `local-development.md` ; contrats publics conservés.

| Tâche | Responsable | État |
|---|---|---|
| L5-01 cadrage/checkpoint/Draft PR | Coordinator | DONE |
| L5-02 carte/données/filtres/périodes | Developer | DONE, validations locales réussies |
| L5-03 détails/mobile/erreurs/preuves | Developer | DONE, handoff et captures livrés |
| L5-04 revue indépendante SHA figé | Tester | TODO, aucun SHA lot5 approuvé |
| L5-05 CI/fusion/bilan | Coordinator | TODO, aucun merge lot5 |

**Prochaine action sûre unique :** Coordinator confirme le SHA final local/distant/PR, puis demande revue indépendante de ce SHA au Tester sur sa seule base `_review` et contrôle CI/base/mergeabilité exactes. Aucune édition suivie après gel ; résultats de revue/CI dans la PR. Ne pas fusionner sur les seuls tests Developer.

## Livraison et preuves actuelles

MapLibre **5.11.0** épinglé/verrouillé, Liberty OpenFreeMap, Mapterhorn Terrarium512. Altitude initial ombrage/pitch35°, Summit à la demande terrain1,3/pitch60°, source DEM terrain séparée. Repli DEM→Altitude sans perte de données/filtres/détails, WebGL indisponible→panneau accessible ; avertissement fond distinct du mode effectif. Attributions permanentes OpenStreetMap/OpenMapTiles/OpenFreeMap/Mapterhorn. Desktop/mobile390px, scopes/règles/restrictions séparés, incertitudes/fraîcheur, non-localisées distinctes des confirmées au rayon. Pas de calendrier/compte/inscription factice.

Loader commun parcourt tous curseurs, y compris pages rayon vides ; versions des deux endpoints/pages cohérentes puis recontrôle final. Trois tentatives sur409, reprise claire ; anciennes requêtes annulées/ignorées. Points regroupés en communes puis clusters, comptes de courses distinctes. Marqueurs synchronisés sur render avec signature incluant géométrie/IDs/membres/nom pour préserver focus et corriger les centres sans déplacer la caméra. État temporel/session UI en mémoire, année civile Europe/Paris initiale, semaines ISO et années bissextiles, saison source séparée ; filtre temporel ne touche pas caméra.

Extension de métadonnées **approuvée par Coordinator** : GET `/api/v1/catalog/options`, catégories du registre triées indépendamment des courses. Schéma réponse séparé1.0.0 ; OpenAPI collection1.1.0 additive. Réponses catalogue/carte/fiche et leurs versions1.0.0 inchangées. Aucune nouvelle migration, modèle ou fixture historique modifiés. Migration courante **b7f4208ac112**.

**Code7f85cf4 :313/313pytest PASS en295,09s**, aucun skip, dont9Chromium réels et3tests options. Migrations upgrade/check/downgrade/upgrade/check incluses. Intégration réelle React compilé→Flask→PostgreSQL, centre corrigé/refresh/caméra stable, périodes, scopes ambigus, mobile ET/rayon/non-localisées, DEM décodé queryTerrainElevation>100, panne DEM, avertissement fond/Summit, commune→cluster/clavier,409borné/reprise, absenceWebGL/détails, vide et panneDB.26contrats Node, Ruff lint/format37fichiers, ESLint, build Vite, pip check, diff-check PASS.

Frontend :16tests catalogue PASS5,26s +4tests UI PASS4,28s, chaque invocation isolée native code0/sans erreur. Dernier run groupé a eu un timeout de démarrage du second worker (4tests exécutés puis code1) : **pas compté PASS**. Un runner sandbox sans tests a été arrêté seulement après vérification exacte du PID11800/commande/parent37320 ; aucun autre Node arrêté. Le premier run20tests avait passé11,21s. Commandes individuelles et résultats précis dans handoff ; configuration produit inchangée.

Développement : premiers échecs d'attendus Mois/casse corrigés et aria-labels explicites ;8cas WebGL PASS56,79s. Inspection a révélé attente idle empêchant compte du marqueur après panne DEM, corrigée ; assertions renforcées ont révélé couplage avertissement/mode, corrigé. Deux ciblés PASS20,31s puis global313PASS incluant neuvième scénario et toutes corrections. Aucun défaut local restant connu ; aucun avis indépendant acquis.

## Captures et fournisseurs

Captures ignorées `.local-tools/lot5-screenshots/{desktop,mobile,mobile-details,summit,cluster-details,dem-failure,webgl-failure}.png` inspectées visuellement, marqueur11 mobile/DEM stabilisé, bottom sheet et attributions lisibles. Ces sept captures utilisent **fond/DEM synthétiques interceptés et moteur réel**, sans appels fournisseurs dans les tests.

Préflight limité `.local-tools/lot5-provider-preflight.md` : métadonnées Liberty/Mapterhorn/planet HTTP200, Terrarium512 et attributions confirmés. Un smoke local `_map_demo` plafonné80requêtes externes/temps bornés, sans pan/zoom : `provider-altitude.png` montre Liberty/ombrage réels, inspecté Developer/Coordinator. **Capture Summit réelle expirée10s sous SwiftShader, script terminé en échec avant bilan réseau JSON.** Aucun compte précis de réponses, qualification live Summit, SLA ou audit complet des licences terrain revendiqué. Ne pas relancer le smoke aveuglément ; aucune exploration fournisseur supplémentaire nécessaire. Pas de collecte FFC, archive de tuiles, régional download, achat ou déploiement.

## Intégration antérieure confirmée

Lot4 DONE : https://github.com/TheoxProject/RaceAtlas/pull/6. Tester **APPROVE** SHA **7cab9a3a3390e01b09f925fe6e9e6321997bc74a**, CI https://github.com/TheoxProject/RaceAtlas/actions/runs/42981366838 **success**, checks verts au même SHA. Merge GitHub confirmé **3bd018bff1b60f3831606348831fd72375f557dd**, arbre identique au SHA revu (`git diff --exit-code`). Workflow PR, pas de CI main séparée attendue.304pytest dont3Chromium,119assertions indépendantes,26contrats,3tests frontend et contrôles statiques/build/pip réussis. Corpus417courses synthétiques vérifié ; rapport PR#6 et `.local-tools/tester-report-lot4.md`. Lots0–3 et politique agents intégrés.

## Environnement, processus et restrictions

Python3.12.14 : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Pip check via `C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -m pip --python <venvpython> check`. Node24.22.1 ; frontend/node_modules et build prêts. Wrapper pnpm système11 incompatible avec store10 : binaire compatible `C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.cjs` version10.20.0 réutilisé. MapLibre absent du cache téléchargé avec dépendances gratuites, aucun script de dépendance activé. BundleJS environ1,18MB brut/330KB gzip etCSS82KB ; avertissement Vite documenté, aucun benchmark régional/matériel mobile exhaustif.

PostgreSQL17.11 sain/actif seulement `127.0.0.1:55434`, cluster `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`. Bases distinctes `raceatlas_lot2_test` Developer / `raceatlas_lot2_review` Tester ; utilisateur `raceatlas_local`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Pas de partage simultané de DB ; ne pas initdb/reseed aveuglément. Ancien cluster incomplet et deps partielles ignorés.

Preview supplémentaire **locale** `raceatlas_map_demo` : créée vide par Coordinator, migrée au head et seedée12fixtures synthétiques par Developer. Première tentative seed avec envdevelopment invalide empêchée avant écriture, corrigée en local. Ne pas utiliser `_test`/`_review` pour preview durable. Aucun serveur preview ni test Developer actif après validation, smoke fermé dans finally. Chromium cache `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Arguments de rendu SwiftShader/WebGL-failure limités aux navigateurs jetables de test, aucune politique utilisateur/web-security modifiée.

Native DB/browser et Git métadonnées partagées nécessitent hors sandbox autorisé ; aucun rejet auto-review. Connecteur création PR403 historique, fallback Git autorisé sans secret ; scripts ignorés anciennes PR à ne pas lancer aveuglément. Aucun main/reset/forcepush/merge par Developer.

**Décisions propriétaire : Altitude2,5D initial, Summit3D à la demande ; ouvrir le calendrier sélectionnera le mois affiché, conservé au retour carte, autres filtres et caméra préservés.** Aucun arbitrage en attente. Pas de collecte FFC live/régionale/récurrente, dépense, mutation distante/production, déploiement, tag/publication finale. Droits/qualification FFC live, exploitation et audit complet de fournisseurs restent ouverts avant release.
