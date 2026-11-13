# ACC-02B1 — service email, SDK et modèles français

Jalon préparé sur `feature/account-authentication`, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12), parent de reprise **1464dfa2db250e1816e2f7120fde371479575338**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Le SHA de livraison est le commit qui contient ce handoff (`git rev-parse HEAD` après publication), transmis au Coordinator pour gel et revue indépendante ; aucune approbation B1 revendiquée ici.

## Interfaces et fichiers

- `raceatlas/email/__init__.py` : `EmailService.from_environment(mapping)`, `render(purpose, recipient, token)`, `send_confirmation(...)`, `send_password_reset(...)`. Ces deux derniers prennent un `operation_id` UUID optionnel, opaque et réutilisable pour une même opération. Aucun appel par une route ou un launcher à ce jalon.
- `config.py` : configuration immuable et erreurs génériques ; origine explicite canonicalisée, HTTPS production, HTTP loopback local/test seulement. From ASCII ou nom canonique avec adresse ASCII, domaine exact, attestations opérateur. Validation de forme bornée, pas validateur RFC exhaustif, vérification DNS ou délivrabilité.
- `templates.py` : sujets/boutons français exacts, confirmation annoncée 24 h et reset 30 min, HTML+texte. Liens racine `/#confirm-email=<token>` et `/#reset-password=<token>`, jeton URL-safe 43 caractères fourni par le caller. B1 n'en garantit pas encore l'usage unique ou l'expiration : services B2 non attribués.
- `providers.py` : Development explicite local/test (20 messages maximum par défaut, configurable 1–100, pas de log/fichier/réseau), Resend via vrai `resend.Emails.send`. Transport supporté injectable pour tests, endpoint HTTPS exact, TLS vérifié, proxy/netrc hérités désactivés, aucune redirection/retry, connect/read 3,05/5 s, corps décompressé maximum 65 536 octets. Pas d'échéance totale garantie.
- SDK globals protégés par verrou process (attente 1 s) puis restaurés même sur exception. Les deux apps concurrentes gardent leur clé/From/client. Tout futur code doit employer ce service, pas les globals SDK directement. Erreurs natives masquées sans contexte secret ; erreurs stables `busy`, `quota`, `rejected`, `delivery_failed`, jamais destinataire/token/corps/clé. Un succès est `accepted`, pas livré.
- `requirements.txt` / `constraints.txt` : Resend 2.53.2, requests 2.34.2, urllib3 2.8.0, charset-normalizer 3.5.2, idna 3.20, certifi 2026.10.23 ; typing_extensions 4.16.0 existant. Installation via pip runtime `--python` dans la venv projet ; pas de runtime depuis le dossier de recherche.
- `tests/backend/test_email.py`, `.env.example`, README, mission, [guide Resend/Webador](resend-guide.md), checkpoint. Aucun changement d'auth A, modèle, migration, route, UI, hosting ou CI.

## Vérifications exécutées à la reprise du 13 novembre 2026

Python utilisé : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe` (3.12.14, pas de module pip). Les commandes abrégées `python` ci-dessous désignent cet interpréteur.

| Commande / preuve | Résultat réel |
|---|---|
| `python -m pytest tests/backend/test_email.py -q --tb=short --junitxml=.local-tools/email-b1-final.xml` | **68 PASS, 2,02 s, exit 0** |
| `pg_ctl status -D .local-tools/pgdata-lot2-native` et inventaire natif Python/Chrome | PG PID 38028 actif, port 55434 ; aucun Python/Chrome concurrent avant régression |
| `python -m pytest tests/backend/test_auth_passwords.py tests/backend/test_auth_sessions.py -q --tb=short --junitxml=.local-tools/email-b1-auth-regression.xml` | **64 PASS, 20,66 s, exit 0**, uniquement DB `raceatlas_lot2_test` avec opt-in |
| `python -m ruff check raceatlas migrations tests/backend` | PASS |
| `python -m ruff format --check raceatlas migrations tests/backend` | **54 fichiers conformes** |
| Runtime Python `-m pip --python <venv> check` | PASS, aucune dépendance cassée |
| `node --test tests/contracts/contracts.test.mjs` | **26 PASS** |
| `git diff --check` | PASS |

Les 68 cas emploient le vrai SDK avec Session HTTP simulée ; les requêtes réseau requests sont interdites par fixture. Couverture : configuration/origine/production fermée, modèles et sujets littéraux indépendants du dictionnaire d'implémentation, injections/bornes, appel SDK réussi/idempotence, HTTP 403/429/500/503, timeout/connexion/redirection/corps invalide ou trop grand, endpoints refusés, restauration des globals, concurrence entre apps et attente du verrou bornée. Les secrets et destinataires des tests sont synthétiques.

Premier run avant interruption : sortie tronquée, résultat non réconcilié, **ne pas le relabeller PASS**. Le nouveau run ci-dessus possède son propre JUnit/code de sortie. Preuve distincte de sauvegarde parent1464 : [CI43402452005](https://github.com/TheoxProject/RaceAtlas/actions/runs/43402452005) SUCCESS **589 backend / 67 frontend**, 227,04 s backend ; elle précède la correction du sujet et ne remplace pas la CI/revue du nouveau head. Auth A exact9dfd APPROVE et CI43389431747 521/67 réutilisées pour les chemins inchangés ; régression locale A ci-dessus ajoutée après les dépendances. Pas de nouvelle campagne backend complète ou carte/frontend inchangés.

## Contrôle visuel local

Script ignoré `.local-tools/email-b1-preview.py`, Chromium du cache, `set_content` et toutes routes réseau bloquées. Deux HTML synthétiques rendus chacun en 680 et 390 px, contrôle d'absence de débordement horizontal et bouton visible ; **quatre PNG inspectés visuellement** :

- `.local-tools/email-b1-preview/confirmation-680.png`
- `.local-tools/email-b1-preview/confirmation-390.png`
- `.local-tools/email-b1-preview/reset-680.png`
- `.local-tools/email-b1-preview/reset-390.png`

Texte, bouton, durée, lien de secours et pied de page lisibles, navy/orange corrects. HTML ignorés dans le même dossier. Ces captures de navigateur ne valident pas tous les clients mail réels. Aucun serveur ou navigateur retenu après le contrôle.

## Limites et revue à renouveler

Sous-domaine email choisi `raceatlas.ucthonon.fr`, From futur `RaceAtlas <notifications@raceatlas.ucthonon.fr>`, propriété du club déclarée par le propriétaire ; **aucune vérification Resend/DNS, clé réelle ou autorisation d'envoi acquise**. `.env.example` garde From/domaine/clé vides, gardes `false`, provider Development ; APP_BASE_URL vide, URL réelle Render encore à renseigner. Guide Webador sans valeurs DNS inventées ni modification des services du club. Irlande recommandée pour routage, stockage US/limites documentés, aucune conformité juridique revendiquée.

Tester : vérifier ce commit exact, les deux rendus/sujets, refus de production simulée, secrets/globals/SDK réel sans réseau, erreurs et dépendances. [Mission B1](resend-mission.md) fait autorité ; le plan ignoré `.local-tools/tester-email-probe-plan.md` doit tenir compte du domaine désormais choisi mais non vérifié. La revue B1 n'approuve pas toute la PR12 : inscription/confirmation/reset métier, tokens persistants, renvois, limites anti-abus, HTTP/CSRF/UI, livraison réelle et acceptation finale restent à faire. Aucun compte externe, DNS, email réel, coût, collecte ou déploiement exécuté. Après publication : gel du SHA et arrêt des éditions jusqu'au retour du Coordinator.
