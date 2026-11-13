# Handoff ACC-02A — primitives et sessions internes

Branche `feature/account-authentication`, PR https://github.com/TheoxProject/RaceAtlas/pull/12. Base **5e2c84a99f7795da9cc2e14118549873bf4a42be**, parent local/distant **37ca92a842cc5ba0413245120e029ebd3f28eab8**. CI du cadrage `43385747578` SUCCESS 457 backend / 67 frontend, ne valide pas cette implémentation. Relever le SHA publié, geler pour Tester ciblé et CI ; ce jalon ne termine ni PR auth ni lot 7. B/C non attribués.

## Fichiers et interfaces

Nouveaux modules `raceatlas/auth/{__init__,passwords,errors}.py`, ajouts privés PasswordCredential/AuthSession dans models, migration **d82b9147a120** après **c40a7162b901**, deux fichiers tests `test_auth_passwords.py` et `test_auth_sessions.py`, Argon2 seulement dans requirements/constraints et documents du jalon. Aucun App/serve/route/HTTP/frontend/CI/public API/contrat/source/transport email modifié. La fixture de nettoyage existante TRUNCATE account CASCADE couvre les nouvelles tables ; aucun élargissement de nettoyage requis.

- `hash_password`/`verify_password` : Argon2id 19456 KiB, t2, p1, sel16, tag32, PHC version19. Paramètres explicites ; sel natif aléatoire, aucun hash faible en tests. PHC soumis borné ASCII/sans NUL et paramètres exacts vérifiés avant KDF, pour ne pas allouer un coût arbitraire. Erreurs natives de hash converties en indisponibilité générique ; échec de vérification générique sans mot de passe/PHC réfléchi.
- Politique : 15–128 **codepoints** Unicode valides, maximum **512 octets UTF-8 strict**. Aucune normalisation, strip/lower, troncature ou règle de composition. Espaces, accents, emoji et NUL de mot de passe sont traités comme octets exacts ; ne pas confondre avec les tokens/PHC qui sont ASCII. Corpus de mots courants et contrôles d'abus/timing restent des gates de l'auth complète, pas une conformité NIST/OWASP revendiquée.
- PasswordCredential unique par Account, PHC seulement, date de preuve email et version privée positive. Absent/non vérifié ou preuve future → refus. Aucun Account seul ne permet login ; aucune fonction de provisioning/route temporaire ajoutée. Seules les fixtures de tests préparent directement les credentials ; B créera la donnée vérifiée après le vrai protocole local de confirmation.
- `authenticate(session, email, password)` : normalisation email ACC-01, vérification fraîche puis session CSPRNG **32 octets / 256 bits**, token URL-safe43 caractères. DB contient uniquement SHA-256 du token. `IssuedSession.token` exclu du repr ; échéance aware UTC. Hash de travail factice aléatoire pour compte/credential absent, sans prétendre timing constant ou défense anti-abus complète.
- `resolve_session(session, token)` : refus borné/générique des tokens malformés, lookup SQL frais, contrôle credential/version/expirations ; retourne l'Account **persistant de la même Session ORM**, réellement utilisable par planning. Pas d'ID acteur choisi par client ou JWT. Validation met à jour last_seen uniquement si valide, sans prolonger l'absolue. Sessions indépendantes par appareil.
- Expiration serveur : **7 jours absolus / 24 h idle**, bornes exactes exclues. Horloge DB `clock_timestamp` convertie UTC ; aucune date fournie par un navigateur/paramètre public. Les tests injectent seulement le helper d'horloge de confiance, et vérifient aussi sessions PG UTC/Paris/Honolulu et relecture d'objets préchargés.
- `logout` invalide une session ; `logout_all` incrémente la version credential et supprime toutes ses sessions, sans toucher autrui. `change_password` exige token valide et preuve actuelle, hash nouveau puis révocation totale, sans ouverture implicite d'une session. Chaîne FK **Account→PasswordCredential→AuthSession CASCADE** : supprimer/recréer un credential ne ressuscite pas les anciens tokens. SavedEntry et source d'autrui conservés.

## Transactions et concurrence — contrat pour B/C

**Caller possède commit/rollback. Ne jamais publier token/cookie avant commit réussi.** Un IssuedSession retourné avant rollback n'est pas une émission persistée. Aucun commit implicite du module. Une exception laisse le caller responsable de terminer sa transaction et libérer les verrous ; ne pas faire d'I/O email sous verrou.

Ordre obligatoire de tous les écrivains auth : **Account FOR UPDATE d'abord**, puis relecture credential/session avec `populate_existing`, vérification, émission/révocation/modification et commit. Account est le point de sérialisation ; le résultat durable est décidé au commit. Un résultat KDF antérieur ne peut pas passer entre révocation et émission : la vérification se fait déjà sous ce verrou. Les phases B confirmation/reset devront respecter le même ordre, sans écrire autour du service. Une suppression Account concurrente attend son verrou puis cascade.

Les tests utilisent deux connexions PG véritables et phases bornées : la première vérification ou validation tient le verrou ; la seconde révocation/changement/suppression est observée bloquée via `pg_blocking_pids`, puis libération/commits et refus du token ancien. Aucun faux deadlock exigeant entrée de la deuxième opération dans le verrou déjà tenu. Ordre légal : émission avant révocation, ensuite invalidée ; **une connexion fraîche après logout-all reste permise** si le mot de passe n'a pas changé. Cache ORM préchargé n'est pas une preuve et n'évite pas les relectures après modification par une autre connexion.

KDF : deux opérations simultanées maximum **par processus**, attente de slot plafonnée à une seconde puis erreur générique ; tests de travail natif, contention et libération sur erreur. Cela borne le travail actif, pas le nombre global de clients ou un système multi-processus. Pas encore de rate limiter HTTP/persistant (C). 2×19 MiB est un paramètre de travail, **pas une mesure RSS** ; ne pas le convertir en capacité Render Free.

## Dépendances et commandes exécutées

`argon2-cffi==25.1.0`, bindings26.1.0, cffi2.1.1, pycparser3.12 épinglés. Installation dans **venv projet existante**, via runtime pip `--python <venv>` ; wheels/cache réutilisés, dossier `.local-tools/auth-research-deps` non utilisé comme runtime. `pip check` PASS ; Linux reste à qualifier par la CI du candidat. Sources primaires [Argon2 API](https://argon2-cffi.readthedocs.io/en/stable/api.html), [installation](https://argon2-cffi.readthedocs.io/en/stable/installation.html), [OWASP hash](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) et [sessions](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) relues le **13 novembre 2026**.

```powershell
# Runtime Python -m pip --python <venv> install -c constraints.txt argon2-cffi==25.1.0
# Runtime Python -m pip --python <venv> check
python -m pytest tests/backend/test_auth_passwords.py tests/backend/test_auth_sessions.py tests/backend/test_planning.py -q --tb=short
python -m pytest tests/backend/test_foundation.py tests/backend/test_catalog.py -k 'all_seeded_details_preserve_contract or every_contract_scenario' -q --tb=short
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
git diff --check
```

PG17 existant vérifié avant tests : PID38028/port55434 ; aucun Python/Chrome concurrent, anciens Node non revendiqués préservés. Seulement `raceatlas_lot2_test` avec opt-in, Python3.12.14/cache ; pas initdb, DB distante ou navigateur. Migration upgrade/check/downgrade base/upgrade/check effectivement exécutée par la fixture.

Premier ciblé : **54 PASS / 7 FAIL + 7 erreurs teardown, 33,43 s**. Les 39 scénarios sessions PG passaient ; sept sondes tentaient de remplacer des méthodes read-only de PasswordHasher. Correction du harness : proxy de test déléguant au vrai KDF, pas modification des paramètres/primitive. Une commande native a expiré au stade revue automatique de permission ; l'unique retry explicitement permis a réussi. **22 primitives PASS5,02 s**, puis ajout ciblé PHC ASCII/NUL et mot de passe NUL. **Ciblé final auth + planning : 132 PASS en63,10 s**, code0 (25 primitives,39 sessions,68 planning).

Mesure locale de ce dernier run, aucun secret archivé : hash **41,36 /35,78 /47,58 ms**, verify **48,98 /40,59 /42,56 ms** ; premières mesures22tests65–69ms/62–67ms, variation de poste normale, pas benchmark universel. Résumé ignoré `.local-tools/auth-kdf-cost.json`, sans PHC/password/token. Pas de mesure mémoire RSS/Render ou débit réseau.

Ruff lint/format PASS (**49 fichiers**), **26 contrats/diff PASS**, pip check final PASS. Courte régression publique détails/scénarios catalogue : **10 PASS, 72 désélectionnés, 12,44 s**, code0, incluant le cycle migration/check. ACC-01 reste réexécuté dans le ciblé ; autres preuves publiques/source/hosting/UI inchangées réutilisées après diff, pas de full457/backend/browser répété. Aucun processus Developer de test retenu après ces commandes.

## Risques et suite non livrée

Revue ciblée du nouveau SHA + CI complète requises. Pas d'inscription/confirmation/reset, transport local/email réel, HTTP/cookies/CSRF/abus, suppression réauthentifiée HTTP, UI ou ICS livré ici. Aucun compte/domaine/expéditeur validé, service/DNS/paiement ou déploiement ; premier déploiement après lot8. Les fixtures vérifiées ne prouvent pas une délivrabilité. Corpus mots communs et garanties de timing/limites externes restent à cadrer avant acceptation auth complète. Arrêt des éditions après publication jusqu'à libération.
