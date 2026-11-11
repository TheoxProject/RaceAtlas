# Handoff Developer — préparation V1, candidat final RDY-01–05

Branche `feature/v1-readiness`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/8, base **5f8229245f31ff64f678cad9df331f7302bef76f**. Jalons intermédiaires approuvés : RDY-01 documentaire **136768cd6499f18858e27834926bd3bf216150f7**, RDY-02 CI **1d33dc480b1cdc3f9de4a9c959788f6ad982d24b** ; ce dernier a CI43086393213 success (315 tests en128,50s,28 frontend, gardes début/fin réellement exercées). **Aucun avis intermédiaire n'approuve le candidat final.** Le commit contenant ce handoff publie RDY-03/04 ; relever son SHA local/distant/PR, puis aucune édition suivie pendant revue complète. Aucun merge, service ou déploiement effectué.

## Livré

- CI du jalon précédent conservée : job `integrated`, `contents: read`, checkout source exact sans credentials persistés, contrôle HEAD/ref PR publique avant/après, concurrence, `push` sur `main`, annotations/résumé et preuves synthétiques limitées à un jour. Tous contrôles existants préservés, aucun bot/write/schedule/déploiement.
- Nouveau `raceatlas/serve.py` : préflight avant `create_app`, environnement production, URL complète `postgresql+psycopg`, `sslmode=verify-full`, CA absolue lisible/non vide, port valide non réservé et credentials sans défaut. Garde Basic WSGI obligatoire, comparaison UTF-8 avec `compare_digest`, toutes routes/assets/ready protégés ; seuls GET/HEAD exacts sans query sur `/api/health/live` publics. Refus401 générique, aucune réflexion des headers, réponses privées `no-store`. Main Waitress sur `0.0.0.0:$PORT`, quatre threads ; aucun startup migration/seed/connexion DB.
- `ops/render.yaml` : un Web Service Python plan `free`, branche `main`, auto-déploiement et previews Blueprint désactivés, aucune DB Render ou `preDeployCommand`. Secrets `sync: false`, versions Python3.12.14/Node24.22.1. `ops/build.sh` installe les dépendances Python de production et compile React avec pnpm10.20 gelé, outils de build explicitement inclus ; `ops/.gitattributes` force LF. Aucun build/start ne migre ou seed.
- `.env.example` : nouveaux secrets vides et URL de maintenance distincte, jamais intégrée au service Web. Nouveau `tests/backend/test_hosting.py` :70 cas ciblés. Guide `docs/readiness/hosting.md`, lien README et checkpoint actualisés. Les sources catalogue, modèles, migrations, frontend et configuration `create_app` restent inchangées.

## Vérifications réelles

Python3.12.14, Node24.22.1 et caches existants réutilisés. PostgreSQL17.11 déjà actif sur127.0.0.1:55434 vérifié avant tests, aucune réinitialisation du cluster. Seulement la base jetable Developer `_test` utilisée ; `_review` et `_map_demo` préservées.

```powershell
$python = 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe'
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas_local@127.0.0.1:55434/raceatlas_lot2_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
& $python -m pytest tests/backend/test_hosting.py -q --tb=short
& $python -m ruff check raceatlas migrations tests/backend
& $python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
Push-Location frontend
node node_modules/vite/bin/vite.js build
Pop-Location
& 'C:/Users/theop/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m pip --python $python check
git diff --check
```

**70 tests hosting PASS6,07s**, sans skip : TLS plus faible/manquant, CA absente/relative/vide/illisible/dupliquée, variables invalides et ports réservés, préflight avant factory, startup sans connexion/migration/seed, appel Waitress simulé borné, Basic malformé/UTF-8, mauvaise authentification et protection des pages/assets/API/ready ; vraie intégration Flask/React compilé/PostgreSQL et panne locale sans DSN/Authorization dans réponse/logs. Les identifiants des tests paramétrés ne contiennent pas les headers Basic. Migrations upgrade/check/downgrade/upgrade/check de la fixture incluses. Premières campagnes65 puis69 cas également vertes ; la dernière70 les remplace sans transformer un échec en succès.

Ruff lint/format **39 fichiers PASS**,26 contrats PASS, pip sans paquet cassé, diff PASS. Build frontend réel **PASS8,94s**,37 modules, JS1183,90kB/330,87kB gzip etCSS81,76kB/13,15kB gzip ; avertissement du moteur conservé. Frontend source/28 tests inchangés depuis CI1d33, explicitement réutilisés plutôt que rejoués localement ; nouvelle CI complète obligatoire.

Build Render préparatoire : `bash -n`, LF et exécution des trois commandes avec stubs, arrêt code9 attendu sur échec de la première commande, PASS via `.local-tools/hosting-build-probe.py`. **Aucun pip global, téléchargement pnpm ou build Render complet exécuté.** Premier Bash sandbox refusé par MSYS ; reprise native autorisée réussie, pas de modification pour masquer ce refus. `js-yaml`4.3.2 transitive déjà en cache : parsing CI/Blueprint et vérification des champs critiques PASS via `.local-tools/readiness-yaml-check.cjs`, aucune dépendance ajoutée.17 liens relatifs README/guide vérifiés sans cible absente.

## Limites et revue finale

Préflight CA local : lecture d'un fichier, pas validation d'une chaîne Neon ; les tests utilisent un placeholder synthétique et aucune connexion distante. Waitress main vérifié par interception, aucune ouverture de service externe. Le guard a été exercé localement avec la vraie app et PostgreSQL. Basic est uniquement la preview privée, pas les comptes du lot7 ; aucun flag ne permet de la rendre publique. Render terminera HTTPS selon sa documentation, pas TLS dans Waitress ni confiance globale dans un proxy.

Le guide décrit migrations manuelles seulement après autorisation et une procédure de sauvegarde chiffrée hors Render, avec client PostgreSQL17 compatible, secrets via environnement/fichier privé et restauration d'abord en nouvelle DB locale jetable. **Aucun dump/restore réalisé ; preuve opérationnelle complète au lot8.** Aucun service, compte payant, handshake Neon, mutation distante, FFC ou déploiement. Limites gratuites vérifiées dans les sources officielles datées11novembre, à revérifier avant activation ; usage de compte non inspecté et aucune garantie de coût/SLA.

Tester : confirmer le SHA final/propreté/base ; évaluer tous critères RDY-01–05, inspecter le delta depuis les jalons et réutiliser explicitement leurs preuves seulement sur les chemins inchangés. Rejouer les70 cas sur `_review` et les sondes indépendantes utiles, vérifier les configurations/build/guards/limites, puis contrôler la CI du nouveau SHA. Aucun writer pendant revue. Les avis RDY-01/02 restent intermédiaires ; nouveau APPROVE exact et CI verte nécessaires. Après merge éventuel, vérifier arbre/SHA et attendre la nouvelle CI `main` avant lot6.

Rapport propriétaire de pré-déploiement après lot6, puis lots7/8 et RC ; publication finale/tag, déploiement, mutations distantes et collecte FFC récurrente restent soumis à autorisation. Les blocages de compatibilité/droits FFC et de qualification matérielle/provider antérieurs sont préservés. Tous processus Developer terminés, PostgreSQL existant conservé actif ; ne pas initdb/reseed/réinstaller aveuglément.
