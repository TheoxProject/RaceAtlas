# Point de reprise RaceAtlas

Dernier checkpoint UTC : 2026-11-11T13:19:26Z. **Lot5 correction cycle2 F6 validée localement, prête au gel/revue ; aucun APPROVE ni merge lot5.**

## État Git et prochaine action

- Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche `feature/map-experience`, Developer seul writer pendant correction, fichiers préexistants préservés.
- Base `origin/main` : **3bd018bff1b60f3831606348831fd72375f557dd**, lots0–4 intégrés. Draft PR https://github.com/TheoxProject/RaceAtlas/pull/7.
- Dernier candidat local/distant/revu : **fc8f540c4263c9b70de1b8a291ff98806b37299f**. CI43025992904 SUCCESS315tests133,58s, mais Tester **REQUEST CHANGES F6** après315tests indépendants PASS252,70s. Les gates restent fermés malgré la CI verte. Rapport `.local-tools/tester-report-lot5.md`, observations `.local-tools/lot5-retest-screenshots/observations.json`.
- Le commit contenant ce checkpoint publie le correctif C2 et ses preuves ; relever son SHA local/distant/PR et contrôler sa propre CI. Après push, toutes éditions suivies cessent. Un ancien SHA approuvé/vert ne valide jamais le remplaçant.

| Tâche | État / preuve |
|---|---|
| L5-01/02/03 carte/API/détails | Livrés, corrections indépendantes intégrées dans les candidats successifs |
| L5-C1 F1–F5 | CLOSED par Tester surfc8 : captures propres, crédits mobiles, nombres entiers, frontière ISO initiale, UTF8 |
| L5-C1 fond pending/terrain | PASS indépendant surfc8 : init once(style.load), marqueurs11/API12 avant réponse raster, terrain>100/pitch60 |
| L5-C2 F6 no-op période | DONE local : objet/ancre préservés si valeur normalisée inchangée, détails/requêtes conservés |
| L5-04 revue finale C2 | TODO sur nouveau SHA figé, réutiliser preuves backend inchangé et contrôler C2 |
| L5-05 CI/fusion | TODO, CI315 et APPROVE au SHA final obligatoires |

**Prochaine action sûre unique :** Coordinator confirme le SHA final local/distant/PR, surveille sa CI complète, puis demande le retest indépendant F6 et l'évaluation finale du lot sur ce SHA. Aucun writer pendant revue et aucun merge sans tous les gates.

## Correction C2 et preuves

F6 confirmé par Tester : au2027-01-01, initialcivil2027→ISO2026W53 correct ; simple Tab/Entrée sur année ISO2026 ou semaine53 inchangée réancrait au lundi2026-12-28, puis retourAnnée2026/MoisDécembre2026. Correction minimale `changePeriod` : comparer les valeurs effectives après bornage, renvoyer le même objet pour un vrai no-op, changer seulement le mode si demandé, réancrer uniquement une année/mois/semaine réellement modifiée. Numbervalidation et clamps existants conservés ; aucun MapView/backend/contrat modifié dans C2.

**28frontend PASS9,87s** (22catalogue +6App), ESLint/build PASS3,99s. Unités : identité stricte Jan1/Dec31/jourbissextile, semaine bornée sans changement effectif, vrais changements conservés. UI : détails ouverts, champs ISO inchangés et bouton du mode actif ne relancent pas le loader, retourMoisJanvier2027 et Année2027.

**E2E ciblé NouvelAn1PASS34,00s**,10désélectionnés : quatre cas ISOyear/week×Tab/Enter réels, détails maintenus, nombre de requêtes stable après debounce, retoursAnnée2027/MoisJanvier2027 ; anciens cas décimales/vides/0/-1, bornage52/53/54, course multijour, caméra exacte et parentcaptures absent conservés. Migrations roundtrip de la fixture jetable incluses.26contrats PASS ; lint/format Python et diff PASS. Backend catalogue inchangé : pas de nouvelle campagne complète locale redondante ;315PASS indépendant et CI surfc8 restent des preuves historiques, nouvelleCI complète nécessaire sur C2.

Build JS1183,90kB/330,87kB gzip, CSS81,76kB/13,15kB ; avertissement moteur>500kB conservé. Pas de qualification exhaustive GPU mobile/régionale. MapLibre5.11.0, anciennes réponses catalogue1.0, options additif1.0/OpenAPIcollection1.1, migrationb7f4208ac112 inchangés.

## Suite après intégration lot5 et restrictions

TODO : AGENTS/workflow validation progressive, surveillance CI après chaque push/contrôle SHA courant/tests main après merge ; README ; configs Render Free monolithe Flask/Waitress + Neon TLS sans création/déploiement/mutation distante. Lot6 calendrier mensuel puis rapport pré-déploiement propriétaire ; lots7 comptes/planning/ICS,8 exploitation/notifications/RC. Qualification FFC limitée commencée par Coordinator, incompatibilités HTML et droits à documenter séparément ; aucun importlive/récurrent/bulk autorisé.

Choix propriétaire acquis : Altitude2,5D initial, Summit3D à la demande ; calendrier sélectionne le mois affiché et le conserve au retour carte, filtres/caméra préservés. Aucun arbitrage en attente. Fournisseurs : seul smokeAltitude historique vu, Summit live expiré/non qualifié ; ne pas relancer aveuglément. Droits FFC/terrain et performances matérielles restent gates avant release. Aucun déploiement, dépense, mutation distante ou tag/publication finale autorisé.

## Environnement et processus

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, Node24.22.1, frontend/node_modules existants. pnpm10.20 compatible en cache, ne pas employer wrapper11 contre store10. Chromium : `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`.

PostgreSQL17.11 actif uniquement127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, utilisateur `raceatlas_local`. Developer `raceatlas_lot2_test`, Tester `raceatlas_lot2_review`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. `_review`12fixtures après sondes indépendantes, preview `_map_demo` séparée12fixtures. Aucun test/preview Developer restant après C2, session60751 terminée code0. Ne pas initdb/reseed/réinstaller aveuglément, ni arrêter tous les Node/Postgres. Ne pas partager les DBs simultanément.

Git/DB/browser natifs autorisés nécessaires ; connecteur créationPR403 historique, fallback Git autorisé sans secret. Aucun reset/forcepush/main direct ; scripts ignorés anciens lots à ne pas relancer. Les scripts/captures/rapports ignorés ne prouvent jamais une fusion. Tester et CI doivent viser le nouveau SHA final, même si seul un document change.
