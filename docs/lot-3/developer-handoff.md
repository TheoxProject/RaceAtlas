# Handoff développeur — lot 3

Branche `feature/auditable-sync`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/5. Base intégrée `f33d837844abdc51ebcafc066da3c16cb4982f34`. Parent avant candidat final : `7a52a826416d225ada98e58719250aa933288e96`. Le commit contenant ce handoff et le checkpoint final est le candidat : relever son SHA avec `git rev-parse HEAD`, puis comparer au distant/PR. Aucun verdict Tester acquis pour le lot 3.

## Implémentation

- `raceatlas/models.py` + migration statique `65107930ec01` : `import_run`, `import_window`, `import_item`, `source_revision`, `source_alias`, `geocode_cache`. Tables métier historiques et contrats inchangés.
- `raceatlas/sync/` : types d'entrée hors réseau, normalisation/empreinte métier, import avec transactions possédées et savepoints, audit, alias/groupe attestés, résolution/cache centre de commune injecté. Aucun transport ou ordonnanceur.
- `tests/backend/test_sync.py`, `test_sync_fingerprint.py`, `test_geocoding.py` : 65 tests nouveaux. `conftest.py` réinitialise aussi audits/cache pour isolation.
- `docs/lot-3/local-development.md` : usage Windows/Python, transactions/provenance/limites ; checkpoint consolidé.

Décisions : conserver scopes/règles inchangés sans rapprochement ; toute réorganisation non attestée reste `needs_review` dans l'audit sans réaffectation du graphe historique. Labels source normalisés servent seulement à détecter l'ambiguïté, y compris listes aux mêmes règles. Les preuves explicites permettent les corrections d'identité/groupement ; les anciennes clés restent des alias. Replay d'une preuve déjà enregistrée idempotent. Empreinte sans tokens/checkdates/slug/HTML/participants ; restrictions corrélées et faits métier retenus.

Les fenêtres indépendantes peuvent conserver leurs faits positifs, mais toute inférence d'absence est différée jusqu'à succès du périmètre complet du run. Déduplication globale et contrôle de fraîcheur des fenêtres ; aucune fausse absence sur chevauchement ou ancienne fenêtre vide. Une absence contrôlée produit `to_verify`, jamais annulation ; annulation historique conservée. Échec item sous savepoint, nouvel essai sans doublon. Audit d'exécution distinct des révisions métier ; indisponibilité PostgreSQL peut empêcher l'audit, aucune garantie mensongère.

Communes via `LocationFact` source explicite et fournisseur injecté ; aucune déduction depuis titre/slug. Cache positif 7j, négatif 1j, erreur 5min, isolé par fournisseur/version/commune/département. Coordonnées finies non booléennes, précision centre, INSEE/département/nom cohérents ; ambiguïté/erreur/conflit sans faux centre. Centre connu conservé si source incomplète/fournisseur défaillant. Rectangle numérique large lon1–8/lat43–48 pour écarter axes inversés et lieux manifestement distants : **pas une preuve polygonale d'appartenance administrative**. Qualité du centre reposant toujours sur la provenance explicitement injectée, aucune qualification GIS/live revendiquée.

## Preuves exécutées

Environnement réutilisé : Python3.12.14, PostgreSQL17.11 local `127.0.0.1:55434/raceatlas_lot2_test`, Chromium cache existant. Aucune base distante, collecte source ou installation payante. Commandes backend depuis racine :

```powershell
$python='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL='postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB='1'
$env:PLAYWRIGHT_BROWSERS_PATH='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
& $python -m pytest -q --tb=short
& $python -m ruff check raceatlas migrations tests/backend
& $python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
git diff --check
```

Résultats finaux : **160 pytest PASS en44,71s**, aucun skip (65 lot3 et95 précédents dont3Chromium). Migrations upgrade/check/downgrade/upgrade/check, contraintes SQL positives/négatives, fixture→adaptateur→sync→PostgreSQL→Flask/schema, identité/révisions/cache/reprise réellement exercés. Ruff lint et format25fichiers PASS ; contrats26/26 PASS ; pip check `No broken requirements found` ; diff-check PASS.

Frontend inchangé, contrôles exécutés après fin des tests navigateur : depuis `frontend`, `node node_modules/eslint/bin/eslint.js . --max-warnings 0`, `node node_modules/vitest/vitest.mjs run`, `node node_modules/vite/bin/vite.js build` : lint PASS,3/3 tests PASS, build29modules PASS (196,22kB JS /61,85kB gzip). La première tentative via pnpm a essayé sa résolution de version sur registre npm et échoué en réseau restreint ; processus arrêté puis utilisation des binaires locaux sans téléchargement, réussite. Aucune dépendance/lockfile modifiée.

Historique d'échec transparent : le premier passage global a donné119PASS/41FAIL, tous causés par la chaîne française `épreuves` d'un helper de test réencodée cp1252/UTF-8 lors d'une lecture Windows implicite. Réparée, lectures/écritures UTF-8 explicites ; passage final160/160ci-dessus. Les passages ciblés antérieurs35puis57PASS et CI WIP vertes ne sont pas présentés comme validation du SHA final.

Checkpoints publiés : `ff351d9c762ea9075efa8f8683ab098777246c5d` (schéma/empreintes), CI success https://github.com/TheoxProject/RaceAtlas/actions/runs/42841269435 ; `7a52a826416d225ada98e58719250aa933288e96` (service/cache), CI success https://github.com/TheoxProject/RaceAtlas/actions/runs/42842980835. CI du candidat final encore à observer.

## Revue et limites

Tester doit relever le SHA exact, confirmer worktree propre, relire diff/critères et exécuter les tests sur sa base locale jetable **raceatlas_lot2_review** uniquement, sans autre écrivain. Migrations/réinitialisations expressément limitées à cette base ; aucune base production. Ne pas relancer initdb. Aucun test développeur actif à la livraison ; cluster PostgreSQL laissé actif. Les prochaines preuves doivent être publiées sur PR sans modifier le SHA en revue.

Le dialecte HTML et les données restent synthétiques, droits et compatibilité FFC live ouverts. Pas de workflow récurrent, collecte, géocodeur live, achat, migration distante, déploiement ou notification utilisateur. Traitement opérationnel/rétention à valider au lot8 avant activation récurrente. Un conflit d'identité non attesté est conservateur et nécessite une décision documentée, jamais une fusion par similarité.

Décision propriétaire résolue pour futur lot5 : **Altitude2.5D initial par défaut ; Summit3D à la demande**. Aucun choix produit en attente pour ce lot. Autonomie technique maintenue, silence jamais accord.

Contrôle final de provenance : preuves LocationFact et nom/version du fournisseur persistés dans audit item, avec assertion dédiée. Après cet ajout final, suite globale rejouée :160/160PASS en44,71s. Scan UTF8/mojibake de tous fichiers modifiés/nouveaux PASS.
