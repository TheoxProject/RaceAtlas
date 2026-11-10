# Point de reprise RaceAtlas

- Horodatage : **2026-11-10T15:31:28Z** — livraison développeur lot3, revue indépendante requise.
- Branche `feature/auditable-sync`, worktree `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`.
- Base `origin/main` vérifiée `f33d837844abdc51ebcafc066da3c16cb4982f34`. Parent avant livraison finale : `7a52a826416d225ada98e58719250aa933288e96`. Le commit contenant ce checkpoint est le candidat ; relever `git rev-parse HEAD` après commit/push et comparer au head PR.
- Draft PR https://github.com/TheoxProject/RaceAtlas/pull/5 ; CI finale à observer sur le nouveau SHA. Aucun verdict Tester lot3 acquis.
- Mission `docs/lot-3/mission.md`, handoff `docs/lot-3/developer-handoff.md`, usage `docs/lot-3/local-development.md`.

## Intégration précédente confirmée

Lot2 DONE : PR https://github.com/TheoxProject/RaceAtlas/pull/4, Tester APPROVE `511208b7d5142f708106a3d4a8f51d170fb3e148`, CI success https://github.com/TheoxProject/RaceAtlas/actions/runs/42839321426, merge confirmé `f33d837844abdc51ebcafc066da3c16cb4982f34`, arbre identique au SHA testé. Lots0/1 et politique PR#3 déjà fusionnés. Dialecte HTML synthétique et droits FFC encore ouverts avant exploitation.

| Tâche | Responsable | État |
|---|---|---|
| L3-01 cadrage/checkpoint/Draft PR | Coordinator | DONE |
| L3-02 import/audit/identité | Developer | DONE |
| L3-03 communes/cache/intégration/handoff | Developer | DONE |
| L3-04 revue indépendante SHA figé | Tester | TODO |
| L3-05 CI/fusion/bilan | Coordinator | TODO |

## Livré et validation développeur

Six tables/migration statique audit/cache/révisions/alias ; empreintes métier stables sans tokens/checkdates ; importeur local possédant transactions/verrou PostgreSQL ; savepoints item et audit sûr, alias/groupe explicitement prouvés. Pas de rapprochement de scopes par rang/nom. Réorganisation ambiguë `needs_review` dans audit, graphe historique préservé. LocationFact explicite et fournisseur injecté sans transport ; cache positif7j/négatif1j/erreur5min par version/département. Centres connus préservés ; coordonnées non finies/inversées/provenance invalide rejetées. Rectangle numérique large n'est pas une preuve polygonale/GIS.

**160pytest PASS en44,71s**, aucun skip (65lot3+95précédents dont3Chromium), migrations aller-retour/drift/contraintes SQL et API JSON Schema comprises. Ruff lint/format25fichiers PASS,26contrats PASS, pipcheck PASS. Frontend inchangé : ESLint PASS, Vitest3/3PASS, build29modulesPASS par binaires locaux après échec de résolution pnpm en réseau restreint. Diff-check PASS. Premier fullrun119PASS/41FAIL : chaîne française du helper de test réencodée cp1252/UTF8, réparée ; passage final160PASS. Lectures/écritures UTF8 explicites, scan UTF8/mojibake PASS. Preuves LocationFact et fournisseur/version auditées durablement ; suite finale rejouée après ce dernier ajout.

WIP publiés/CI vertes : ff351d9 https://github.com/TheoxProject/RaceAtlas/actions/runs/42841269435 ; 7a52a826 https://github.com/TheoxProject/RaceAtlas/actions/runs/42842980835. Ces CI ne valent pas validation du futur SHA final. Aucun risque fonctionnel non résolu confirmé à la livraison développeur ; revue indépendante et CI finale requises.

## Décisions et restrictions

Absence différée jusqu'à réussite de **tout le périmètre du run** ; présence globale dédupliquée protège chevauchements ; fenêtre vide périmée ne remplace pas des faits plus récents. Absence contrôlée uniquement `to_verify`, jamais annulation. Erreur fournisseur/identité/détail/fenêtre empêche conclusions d'absence. Provenance minimale sans HTML/participants. Audit impossible si stockage PostgreSQL lui-même indisponible : exception propagée sans réussite annoncée.

Autonomie technique documentée ; choix produit majeurs consultés, silence jamais accord. **Choix propriétaire futur lot5 résolu explicitement : Altitude2.5D initial par défaut, Summit3D à la demande.** Aucun arbitrage en attente. Aucun déploiement, achat, collecte FFC live/régionale, mutation distante/production, fournisseur live ou publication finale autorisé. Contrats/fixtures historiques/frontend préservés, aucun ordonnanceur activé.

## Environnement et processus

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. Pip via runtime Python cache Codex `-m pip --python <venvpython> check`. Node cache Codex ; dépendances frontend locales installées. Pour éviter résolution pnpm réseau, binaires locaux `frontend/node_modules/eslint/bin/eslint.js`, `vitest/vitest.mjs`, `vite/bin/vite.js` (voir handoff).

PostgreSQL17.11 actif **127.0.0.1:55434**, cluster `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`. Bases jetables `raceatlas_lot2_test` (Developer), `raceatlas_lot2_review` (Tester), utilisateur `raceatlas_local`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Tests réinitialisent tables métier/audit/cache ; ne jamais partager une base de test simultanément. Browser `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Aucun test développeur actif, cluster laissé actif pour Tester.

Ne pas relancer initdb ; ancien `.local-tools/pgdata-lot2` incomplet à ignorer, copie deps partielle `.local-tools/frontend-deps-partial` à ignorer. Processus natifs DB/Chromium hors sandbox ; Git demande autorisation métadonnées partagées. Aucun rejet auto-review. Connecteur création PR403 ; fallback accès Git local autorisé sans secret exposé. Script ignoré `.local-tools/lot2-pr.py` limité ancienne PR4/base : ne pas lancer aveuglément pour lot3.

## Prochaine action sûre

Après commit/push final : **figer le résultat de `git rev-parse HEAD`, confirmer le head PR#5 et demander Tester sur ce SHA exact et sa base locale isolée raceatlas_lot2_review**. Suivre CI du même SHA ; publier preuves finales dans PR sans modifier le candidat. Ne pas fusionner ni commencer lot4 avant gates intégration, TesterAPPROVE et CI verte du même SHA.
