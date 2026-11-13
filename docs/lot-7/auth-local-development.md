# ACC-02A — validation locale des primitives et sessions

Ce jalon est un module interne, sans route de connexion/inscription ou commande de provisioning. Pour tester, les fixtures créent directement un credential vérifié avec un **vrai** Argon2id ; cela n'existe pas comme bypass dans l'application. Account seul reste non connectable. B/C et interface seront attribués séparément.

Réutiliser Python3.12, les environnements et PostgreSQL du [guide ACC-01](local-development.md). La nouvelle dépendance et ses transitives sont épinglées dans requirements/constraints ; le dossier de recherche ignoré n'est pas une venv de projet. Si la venv n'a pas pip, employer le runtime pip `--python <chemin-venv>`, pas une installation globale ou des fichiers copiés depuis la recherche. `pip check` doit passer.

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
python -m pytest tests/backend/test_auth_passwords.py tests/backend/test_auth_sessions.py tests/backend/test_planning.py -q --tb=short
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
git diff --check
```

Vérifier cluster/processus avant run ; `_review` appartient au Tester, aucune DB distante/à conserver. La fixture éprouve migration **d82b9147a120** après c40a7162b901, aller/retour/check ; TRUNCATE account CASCADE existant suffit au nettoyage privé. Les tests de courses concurrentes utilisent plusieurs connexions et un observateur PG, deadlines/barrières bornées, aucun réseau fournisseur.

Mots de passe exacts, 15–128 codepoints et au plus512octets UTF-8, sans strip/lower/normalisation/troncature ; Argon2id19456KiB/t2/p1,sel16/tag32. Deux KDF actifs/processus maximum, attente bornée à1s ; pas de primitive moins coûteuse dans les tests. Le résumé local ignoré auth-kdf-cost.json contient seulement des temps et paramètres, pas les secrets/PHC ni une mesure RSS/Render.

Contrat transactionnel : verrou Account d'abord, relectures fraîches credential/session, opérations jusqu'au commit caller. Ne pas publier le token avant commit. `resolve_session` rend l'Account persistant de la même Session pour planning, pas un acteur choisi par client. Tout futur écrivain B/C doit conserver cet ordre ; pas d'email/I/O distant sous verrou. Expiry7jours/idle24h côté serveur ; logout-all n'interdit pas un nouveau login avec une preuve fraîche encore valide.

[Handoff et preuves exactes](auth-handoff.md), [mission bornée](auth-mission.md), [décisions de sécurité](auth-security-decisions.md). Transport email/HTTP/CSRF/abus/corpus mots courants et acceptation complète restent ouverts ; expéditeur absent, aucune action externe ou activation autorisée par ces commandes.
