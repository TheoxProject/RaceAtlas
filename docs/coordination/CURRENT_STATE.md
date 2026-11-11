# Point de reprise RaceAtlas

Dernier checkpoint UTC : **2026-11-11T07:38:37Z**. Lot4 API catalogue/filtres prêt pour gel/revue, **pas encore intégré ni approuvé**.

## Git et tâches

- Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche `feature/catalog-filters`.
- Base vérifiée `origin/main` : `48a2c3766276c92b2074139847c95e8d6a7b3916`.
- Dernier jalon code local/distant : `9364442f4c6034b389dcac80cd46105d045b687e`. Le commit contenant ce checkpoint et le handoff final est le candidat à relever avec `git rev-parse HEAD`, puis comparer au distant et à la PR.
- Draft PR https://github.com/TheoxProject/RaceAtlas/pull/6. CI jalon code `9364442` verte https://github.com/TheoxProject/RaceAtlas/actions/runs/42980914993 ; **CI du candidat final à vérifier**, aucune preuve ancienne ne vaut pour le nouveau SHA.
- Mission `docs/lot-4/mission.md`, handoff `docs/lot-4/developer-handoff.md`, usage `docs/lot-4/local-development.md`.

| Tâche | Responsable | État |
|---|---|---|
| L4-01 mission/checkpoint/Draft PR | Coordinator | DONE |
| L4-02 validation/sélection/filtres | Developer | DONE, validations locales réussies |
| L4-03 pagination/carte/couverture/intégration | Developer | DONE, handoff livré |
| L4-04 revue indépendante SHA figé | Tester | TODO, aucun SHA lot4 approuvé |
| L4-05 CI/fusion/bilan | Coordinator | TODO, aucun merge lot4 |

## Livraison et preuves actuelles

GET catalogue/carte via un sélecteur SQL partagé, catégories dynamiques, ET dans un seul scope confirmé, règles/restrictions intactes, dates civiles inclusives et saison source indépendante. Recherche nom/commune/organisateur normalisée NFD et espaces Unicode ; JSON/paramètres/types stricts, erreurs publiques structurées sans détails SQL. Jsonschema4.25.1 promu en dépendance runtime épinglée.

Pagination triée date/ID, curseur lié au filtre et à la version, invalidation409. Rayon à deux flux indépendants partageant offset/limite : confirmées dans `total`, candidates non localisées à part ; des pages vides avec continuation sont attendues, parcourir jusqu'à `next_cursor=null`. Une Feature par course au centre communal ; regroupement visuel au lot5. Graphes chargés uniquement pour la page<=200, compteurs SQL.

Nouvelle migration **b7f4208ac112** après **8a95eb41f220** : singleton epoch/révision et triggers statement sur dix tables métier/audits, normalisation SQL sans extension, ordre monotone `ImportRun.catalog_order`. Anciennes migrations inchangées, aucun GRANT/SECURITY DEFINER. Audits historiques préordre conservativement incomplets ; dernière tentative sélectionnée par ordre de création DB, jamais UUID/horloge source. Dernier succès conservé après échec ; exhaustivité intrinsèque toujours inconnue. Une requête lit version/compteurs/items/couverture dans un snapshot PostgreSQL read-only REPEATABLE READ, puis restaure le pool.

**Résultats Developer sur code9364442 :304/304pytest PASS en90,46s**, aucun skip, dont99tests catalogue et3Chromium antérieurs. Migration upgrade/check/downgrade/upgrade/check exécutée. Les neuf scénarios contractuels passent par Flask/PostgreSQL, puis parcours limite1 ; tests rayon sans confirmées et avec continuation, catégories u15/recherche Unicode, triggers/rollback/seed/import, commit concurrent réel entre compteurs et graphes, fixture→adaptateur→sync→catalogue/carte, centres communs, couverture échec/reprise/historique et erreurs malformées.26contrats Node PASS ; Ruff lint/format35fichiers PASS ; frontend ESLint PASS, Vitest3/3PASS (threads1), build Vite PASS ; pip check PASS ; diff-check PASS.

Première expansion ciblée :15échecs/58succès ; défaut réel NBSP corrigé dans normalisation SQL, chaînes NUL/surrogates isolés rejetées avant DB. Les autres échecs provenaient d'attendus nouveaux incorrects (Error plat et suppression raw SQL contraire aux FK), corrigés. Puis98tests ciblés PASS, extension finale incluse dans304tests globaux. Aucun défaut local restant connu, aucune revue indépendante acquise.

## Intégration antérieure confirmée

Lot3 DONE : https://github.com/TheoxProject/RaceAtlas/pull/5. Tester **APPROVE** SHA **54a14472222c0278017074a82ab097f3de8b50ac**, CI https://github.com/TheoxProject/RaceAtlas/actions/runs/42899767502 **success**, check integrated vert au même SHA, aucun autre statut requis en attente. Merge GitHub confirmé **48a2c3766276c92b2074139847c95e8d6a7b3916**, arbre identique au SHA approuvé (`git diff --exit-code` réussi). Workflow PR, pas de CI push main distincte attendue.205tests backend,26contrats et22assertions indépendantes PASS ; rapport PR#5 et `.local-tools/tester-report-lot3.md`. Lots0/1/2 et politique agents également intégrés (lot2PR#4, SHA revu511208b, mergef33d837).

## Environnement et restrictions

Python3.12.14 réutilisé : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Pip check via runtime `C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -m pip --python <venvpython> check`. Node cache Codex ; `frontend/node_modules` local, build prêt. Binaires locaux eslint/bin/eslint.js, vitest/vitest.mjs, vite/bin/vite.js ; Vitest `--pool=threads --maxWorkers=1` fonctionne ici (3tests exécutés), aucun changement produit pour le runner.

PostgreSQL17.11 actif seulement `127.0.0.1:55434`, cluster existant `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`. Redémarré à la reprise sans réinitialisation. Bases jetables séparées `raceatlas_lot2_test` Developer et `raceatlas_lot2_review` Tester ; utilisateur `raceatlas_local`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Browser `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Tous les tests Developer terminés, aucun test actif ; cluster conservé. Ne pas initdb/reseed aveuglément ni partager les bases pendant tests. Ancien cluster incomplet `.local-tools/pgdata-lot2` et deps partielles à ignorer.

Exécution native DB/Chromium et Git métadonnées partagées requiert hors sandbox autorisé. Aucun rejet auto-review. Connecteur création PR403 historique, fallback Git autorisé ; ne pas relancer les scripts ignorés lot2/lot3 de merge ciblant anciennes PR/bases. Ne pas stopper de processus Node sans propriété prouvée.

Choix propriétaire explicites futurs lots5/6 : **Altitude2.5D initial, Summit3D à la demande ; ouvrir le calendrier passe la période partagée au mois affiché, conservé au retour carte, autres filtres et caméra préservés.** Aucun arbitrage en attente. Aucune collecte FFC live/régionale, synchronisation récurrente, dépense, mutation distante/production, déploiement ou publication finale autorisé. Données synthétiques et géocodeur injecté hors réseau ; droits/qualification FFC live ouverts. Rectangle de géocodage : plausibilité, pas preuve GIS. Pas de benchmark sur corpus FFC régional réel.

## Prochaine action sûre

Coordinator : relever et confirmer le **SHA final du commit de handoff** local/distant/PR, puis demander au Tester la revue indépendante de ce SHA avec sa seule base `_review` et contrôler la CI de ce même SHA. Aucune édition suivie après gel ; preuves de revue/CI dans la PR. Le lot n'est DONE qu'après tous les gates et merge GitHub confirmé. Ne pas fusionner sur la seule preuve304pytest locale.
