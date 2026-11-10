# Handoff développeur — lot 2

Date : 2026-11-10T14:48:15Z. Branche `feature/ffc-adapter`, base `2e03cd83931d2297df0b3be830c35974f588fbb8`, PR Draft https://github.com/TheoxProject/RaceAtlas/pull/4. Parent avant livraison : `844168ae6564b8255208aca2acd5571eb87c0dc6`. Le SHA candidat exact est le résultat de `git rev-parse HEAD` après le commit contenant ce handoff ; aucun verdict Tester acquis.

## Livré

- `raceatlas/ffc/` : observations immuables, diagnostics structurés, lecture HTML bornée, parseurs calendrier/fiche et projection SQLAlchemy détachée. Aucun client réseau ni session de persistance.
- `fixtures/ffc/` : deux HTML entièrement synthétiques, documentation du dialecte supporté et limites.
- `tests/backend/test_ffc_adapter.py` : 53 tests nouveaux, dont fixture → adaptateur → PostgreSQL jetable → API détail → validation JSON Schema.
- Checkpoint actualisé ; modèles, migrations, contrats, fixtures historiques et frontend inchangés.

Identité source par saison/numéro, indépendante de la date civile/slug ; compteur et filtres effectifs vérifiés, incohérences `incomplete`, jamais couverture `complete`. CLM appartient à Route. Catégories et restrictions corrélées par règle/scope. Libellés génériques ou inconnus sans expansion implicite. Faits sélectionnés bruts conservés, jamais page complète ou zones participants.

Nouveaux IDs opaques. Révisions sous attestation complète et bijective, aucun rapprochement par rang/nom ni transfert de règles entre scopes. Graphe existant intact en cas de refus. Alias, imports transactionnels, changements de couverture et registre durable des preuves d'identité au lot 3. Une attestation ne permet pas l'effacement de faits connus par observation partielle. Aucune identité source durable de liste inventée ; un ID historiquement attesté reste conservé.

## Vérifications exécutées

Python 3.12.14 et paquets épinglés réutilisés : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. PostgreSQL 17.11 local, 127.0.0.1:55434, base réservée développeur `raceatlas_lot2_test`. Opt-in `RACEATLAS_DISPOSABLE_DB=1`. Chromium via `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`.

Commandes à la racine (`PYTHON` désigne le chemin ci-dessus) :

```powershell
PYTHON -m ruff check raceatlas migrations tests/backend
PYTHON -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
$env:TEST_DATABASE_URL='postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB='1'
$env:PLAYWRIGHT_BROWSERS_PATH='C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers'
PYTHON -m pytest -q
git diff --check
```

Résultats : lint PASS ; format 16 fichiers PASS ; contrats 26/26 PASS ; **76 pytest PASS en 31,99 s** au passage final, sans skip (53 adaptateur, 23 socle dont 3 Chromium). Upgrade/check/downgrade/upgrade/check, contraintes PostgreSQL et parcours intégrés exécutés. Passage précédent 67/67 PASS suivi de neuf cas supplémentaires (toutes disciplines/types explicites, URL mal formée et transfert de règles interdit), puis passage final complet. Aucun échec fonctionnel. Ruff a initialement signalé des lignes longues, corrigées avant validation.

Frontend préliminaire exécuté séparément par Coordinator : ESLint PASS, Vitest 3/3 PASS, build Vite PASS ; aucun fichier frontend modifié. Ne remplace pas revue indépendante/CI au SHA final.

## Revue demandée et limites

Tester : confirmer SHA exact et worktree propre ; lire diff/limites ; refaire tests sur **sa base locale jetable `raceatlas_lot2_review`**. Migrations/réinitialisations des tests réservées à cette base explicitement autorisée. Aucun accès distant ni test simultané sur base développeur. Cluster déjà préparé par Coordinator ; ne pas relancer initdb.

Le dialecte de fiche est synthétique : sélecteurs live complets non établis au lot 0. Aucune réussite live revendiquée. Avant branchement source autorisé, qualifier les champs réels et leurs droits de façon bornée. Structures inconnues en échec explicite. Synchronisation large/récurrente désactivée ; ni ordonnanceur, géocodage ou filtre catalogue applicatif dans ce lot.

Opérations natives PostgreSQL/Chromium exécutées hors sandbox autorisées ; aucun achat, déploiement, scraping ou mutation production. Connecteur création PR 403, fallback Git local autorisé réussi par Coordinator, sans contournement de protection.
