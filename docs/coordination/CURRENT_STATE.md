# Point de reprise RaceAtlas

Dernier checkpoint UTC : 2026-11-11T13:31:36Z. **Lot5 correction cycle3 F7 tests/documentation validée localement ; aucun APPROVE ni merge lot5.**

## État Git et prochaine action

- Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche `feature/map-experience`, Developer seul writer pendant correction ; aucun fichier préexistant révoqué.
- Base `origin/main` **3bd018bff1b60f3831606348831fd72375f557dd**, lots0–4 intégrés. Draft PR https://github.com/TheoxProject/RaceAtlas/pull/7.
- Dernier candidat revu/local/distant **5cd0c5839ce596d0e0426613659422b8dbb416cd** : Tester **REQUEST CHANGES F7**, F1–F6 CLOSED. CI43028158824 FAILURE314PASS/1FAIL (mainE2E Summit pitch35 lu avant fin de mouvement). Rapport `.local-tools/tester-report-lot5.md` ; C2 sondes no-op/détails/requêtes ont PASS, chronologie locale échoue uniquement centre arrondi≈2e-12degrés, zoom/bearing/pitch identiques.
- Le commit contenant ce checkpoint publie C3 ; relever son SHA local/distant/PR et sa propre CI. **C3 modifie seulement test_e2e.py et trois documents, aucun produit JS/Python/contrat.** Après push, éditions suivies arrêtées.

| Tâche | État / preuve |
|---|---|
| L5-01/02/03 carte/API/détails | Livrés, comportement et contrats validés progressivement |
| L5-C1 F1–F5 et fond pending | CLOSED indépendant surfc8 ;315tests/11Chromium PASS252,70s et CI315PASS133,58s |
| L5-C2 F6 no-op période | CLOSED indépendant sur5cd : quatre combinaisons ISOyear/week×Tab/Enter, détails/pasrefetch/retours2027Janvier PASS |
| L5-C3 F7 harness caméra | DONE local : attente réelle pitch, centre abs1e-9deg rel0, autres champs stricts, baseline zoomée et contrôle négatif reset |
| L5-04 revue finale C3 | TODO exact nouveau SHA, troisième et dernier cycle ; aucune approbation par épuisement |
| L5-05 CI/fusion | TODO, nouvelle CI complète315 et APPROVE exact obligatoires |

**Prochaine action sûre unique :** Coordinator confirme le SHA final local/distant/PR, surveille sa CI complète et demande la revue indépendante ciblée C3 avec évaluation finale du lot. Aucun writer pendant revue. Si défaut persiste, le rapporter sans contourner la limite des cycles ; aucun merge avant tous les gates.

## Preuves C3 et exigences conservées

**3E2E PASS36,87s**,8désélectionnés, première campagne C3 code0 : main React→Flask→PostgreSQL/SQL actualisé/Summit, NouvelAn/ISO/matriceF6/invalides, fond503 avec Summit. Les deux tests Summit attendent réellement le pitch60 enregistré au moveend (maximum10s), puis assertion60 stricte ; élévationDEM réelle>100 et mode conservés. Les700ms fixes pour caméra sont supprimés, pas remplacés par un délai plus long.

Comparateur partagé : seules les deux coordonnées du centre admettent **abs1e-9degré, rel0** (≈0,1mm maximum, contre≈2e-12 observés). Tous les autres champs, clés et zoom/bearing/pitch restent stricts. Trois anciennes égalités dictionnaires utilisent ce même comparateur. La chronologie effectue un vrai clic navigationZoomin, attend le zoom final initial+1 enregistré par moteur, puis prend la baseline ; contrôle négatif prouve que le comparateur rejette la caméra initiale. Invariance vérifiée après no-ops et retoursAnnée/Mois, puis changements réels, sans réinitialiser ce zoom non initial.

Aucun source produit modifié.28tests frontend C2 PASS9,87s (22catalogue+6App),26contrats/build/lint frontend de5cd réutilisés explicitement ; pas de nouvelles campagnes redondantes. Ruff37 lint/format et diff PASS C3. Migrations roundtrip de la fixture E2E jetable incluses.315tests indépendants surfc8 restent historiques ; **nouvelleCI complète sur C3 obligatoire**, aucun315local C3 revendiqué.

C2 produit : ancre conservée pour année/mois/semaine normalisés inchangés, même objet/no-refetch/détails maintenus ; vrais changements et bornages conservés. SourceJS depuis5cd inchangé. MapLibre5.11.0 ; réponses catalogue1.0/options1.0/OpenAPIcollection1.1, migrationb7f4208ac112 inchangés. Bundle historique5cd1183,90kB/330,87gzip ; avertissement taille moteur conservé.

## Suite après intégration5 et limites

TODO : AGENTS/workflow validation progressive, surveillance CI après push/contrôle SHA/tests main après merge ; README ; configs Render Free monolitheFlask/Waitress et NeonTLS sans création/déploiement/mutation distante. Lot6 calendrier mensuel puis rapport pré-déploiement propriétaire ; lots7 comptes/planning/ICS,8 exploitation/notifications/RC. Qualification FFC limitée Coordinator, incompatibilités HTML/droits à documenter séparément ; aucun importlive/récurrent/bulk autorisé.

Choix propriétaire acquis : Altitude2,5D initial, Summit3D à la demande ; calendrier sélectionne le mois affiché et le conserve au retour carte, autres filtres/caméra préservés. Aucun arbitrage en attente. Seul smokeAltitude historique limité vu ; Summitlive expiré/non qualifié, ne pas relancer aveuglément. Droits FFC/terrain, performances matérielles mobiles/régionales restent gates avant release. Aucun déploiement, dépense, mutation distante ou tag/publication finale autorisé.

## Environnement et processus

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, Node24.22.1, frontend/node_modules et build5cd réutilisés. pnpm10.20 compatible en cache, ne pas employer wrapper11 contre store10. Chromium : `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`.

PostgreSQL17.11 actif uniquement127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, utilisateur `raceatlas_local`. Developer `raceatlas_lot2_test`, Tester `raceatlas_lot2_review`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Bases distinctes, fixtures synthétiques ; preview `_map_demo` séparée. Session Developer95430 terminée code0, aucun test/preview Developer restant ; PostgreSQL conservé actif. Ne pas initdb/reseed/réinstaller aveuglément ni arrêter tous les Node/Postgres.

Git/DB/browser natifs autorisés nécessaires ; connecteur créationPR403 historique, fallback Git autorisé sans secret. Aucun reset/forcepush/main direct ; scripts ignorés anciens lots à ne pas relancer. Rapports/scripts/captures ignorés ne prouvent jamais une fusion. Tester/CI doivent viser le SHA final, même pour changement uniquement documentaire.
