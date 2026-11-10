# Lot 1 — Handoff développeur

Branche `feature/core-foundation`, base `ae423f520c420bbdaebbaf5e515ce54ea50b4518`. Le SHA de livraison est le commit contenant ce rapport ; le coordinateur le relève et fige la revue indépendante sur ce SHA. Aucun merge, push ou déploiement effectué par Developer.

## Réalisation

Application factory Flask, moteur/session SQLAlchemy 2, sérialiseur du détail `Race` v1, modèles relationnels et migration Alembic initiale indépendante du modèle courant. PostgreSQL impose notamment dates ordonnées, départements AURA, clés étrangères, source candidate unique, catégories par règle uniques, règles/restrictions corrélées et compatibilité discipline/type (CLM Route), y compris lors d'une modification de discipline. Coordonnées communales nullables et provenance préservées ; aucune géolocalisation inventée.

Le seed explicite charge les 12 épreuves du catalogue synthétique sans modifier le lot 0 et sans écraser une édition locale lors d'une réexécution. IDs synthétiques conservés ; UUID opaques par défaut pour les nouvelles entités. La position d'une liste n'est jamais utilisée pour son rapprochement.

React/Vite lit `/api/foundation/demo`, puis le détail réel PostgreSQL via `/api/v1/races/{race_id}`. Flask sert le build depuis la même origine ; Vite possède un proxy local. Chargement, base vide, service indisponible et actualisation sont visibles. Aucun catalogue filtrable, carte, calendrier, compte ou importeur anticipé. Documentation PowerShell/Waitress et Docker PostgreSQL facultatif, configuration production préparée sans accès distant. CI PR avec PostgreSQL de service et navigateur.

## Preuves exécutées le 10 novembre 2026

Windows, Python 3.12.14, Node 24.22.1, pnpm 10.20.0, PostgreSQL 17.11 jetable loopback, Chromium 141 Playwright 1.56.0. Le runtime Python et pnpm ont été appelés par chemins absolus fournis par Codex ; les commandes ci-dessous emploient les exécutables équivalents documentés pour une installation standard.

| Commande | Résultat observé |
|---|---|
| `python -m pip install -r requirements-dev.txt` (runtime pip `--python .venv` localement) | Installation réussie ; versions transitives enregistrées dans `constraints.txt` |
| `python -m pip check` (runtime pip `--python .venv`) | `No broken requirements found` |
| `pnpm --dir frontend install` | Succès, lockfile généré avec pnpm 10.20.0 |
| `node --test tests/contracts/contracts.test.mjs` | 26/26 PASS, fichiers lot 0 inchangés |
| `python -m ruff check raceatlas migrations tests/backend` | All checks passed |
| `python -m ruff format --check raceatlas migrations tests/backend` | 10 fichiers déjà formatés |
| `pnpm --dir frontend lint` | PASS, zéro avertissement lint |
| `pnpm --dir frontend test` | 3/3 PASS |
| `pnpm --dir frontend build` | PASS, 29 modules, bundle JS 196.22 kB (61.85 kB gzip) |
| `python -m pytest -v` | 23/23 PASS en 21.22 s, dont 3 tests navigateur |
| `git diff --check` | PASS |

Le run pytest a utilisé `TEST_DATABASE_URL=postgresql+psycopg://raceatlas_local@127.0.0.1:55432/raceatlas_test`, `RACEATLAS_DISPOSABLE_DB=1` et le navigateur téléchargé dans `.local-tools/browsers`. Le fixture de session a réellement exécuté `upgrade head`, `check`, `downgrade base`, `upgrade head`, `check` ; les deux contrôles indiquent `No new upgrade operations detected`. Tests : toutes les réponses de détail comparées au catalogue et validées JSON Schema, seed rejoué, contraintes PostgreSQL négatives, absence de fallback SPA sur API, erreurs sans fuite, seed refusé en production.

Le navigateur exécute le React compilé servi par Flask, affiche l'épreuve persistée, puis une modification SQL du nom devient visible après actualisation et nouvelle réponse API 200. Vérification d'absence de débordement à 390 px, aucune erreur JavaScript. Parcours base vide et PostgreSQL indisponible également exécutés dans Chromium.

Un premier run backend avait détecté une différence de format du timestamp PostgreSQL (`+01:00` au lieu de `Z`) ; sérialisation UTC explicite corrigée, puis totalité des tests repassée. Les accès réseau/processus Chromium et PostgreSQL ont nécessité l'exécution autorisée hors sandbox Windows ; aucune base distante utilisée.

## À vérifier indépendamment

Tester le SHA figé, lire le diff complet, rejouer les commandes sur `raceatlas_review` (base locale jetable réservée), contrôler le lancement exact Waitress documenté. `PLAYWRIGHT_BROWSERS_PATH=.local-tools/browsers` pour réutiliser le navigateur local installé. Les fichiers générés, binaires PostgreSQL et données sont ignorés. La CI distante ne pourra être déclarée réussie qu'après push/PR et observation du résultat par le coordinateur.

## Limites

Ce lot n'est pas une livraison V1 complète. Les contrats catalogue/map restent réservés au lot 4 ; l'OpenAPI lot 0 ne prétend pas que ses routes soient toutes déjà implémentées. Pas de données réelles, collecte FFC, Neon, Render, sessions ou déploiement. Les composants Docker natifs et le démarrage Waitress exact restent à confirmer indépendamment ; la preuve intégrée locale utilise le serveur HTTP Werkzeug dans les tests. Les dépendances sont volontairement épinglées et devront être entretenues ; l'installation signale ESLint 9 en fin de support et une sous-dépendance `whatwg-encoding` dépréciée, sans échec de lint/test/build.
