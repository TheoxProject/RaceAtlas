# ACC-02B2 — confirmation et récupération internes

Branche `feature/account-authentication`, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12), parent B1 **c79c557e32fed3fd56c85ed1ce786f0bd46fde04**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Le candidat est le commit contenant ce handoff, dont le SHA exact sera transmis après push. B2 doit obtenir une nouvelle revue et CI ; ni auth/PR12 ni lot7 ne sont terminés.

## Interfaces et transactions

Nouveau `raceatlas/auth/flows.py` :

```python
request_registration(session, email, password, *, policy=None)
resend_confirmation(session, email, *, policy=None)
confirm_email(session, token)
request_password_reset(session, email, *, policy=None)
complete_password_reset(session, token, new_password)
```

Les trois requests retournent toujours `RequestResult(status="accepted", intent=...)` ; l'intent optionnel est **interne**, masqué dans repr et jamais un résultat HTTP. Confirmation/reset renvoient `None` ou `InvalidProof("Invalid account proof.")`. La forme du mot de passe reste le contrat exact d'A ; forme email B2 normalisée ACC01 puis sous-ensemble ASCII expédiable B1, avant mutation. Aucun changement du contrat Unicode interne ACC01/A.

Le caller possède commit/rollback. Session **liée à un Engine unique** pour tous les modèles concernés : les Sessions liées à une Connection externe, ainsi que DBAPI AUTOCOMMIT, notamment `join_transaction_mode=create_savepoint`, sont refusées avant mutation. Un RELEASE SAVEPOINT n'est pas une preuve de commit PostgreSQL externe. Aucun commit implicite, aucun envoi dans le service ou callback.

Après un commit racine réussi uniquement : `result.intent.dispatch_after_commit(email_service)` s'il existe. UUID d'opération opaque stable, dispatch une seule fois, pas de retry automatique. Intents uniquement en mémoire, raw token/représentation masqués ; callbacks suivent leur transaction d'origine. Commit imbriqué seul ne les arme pas ; rollback/close du niveau d'origine les invalide, rollback d'un niveau enfant n'invalide pas un intent parent. Session.close puis réutilisation ne ressuscite rien. Commit échoué/rollback ne publie rien.

Crash après commit avant envoi : intent perdu, renvoi comme récupération. Pas de durabilité email ou atomicité DB→fournisseur revendiquée. Panne du provider après commit laisse réservation/preuve et état pending inchangés, ne vérifie pas le compte. Ce dispatcher synchrone interne ne prouve pas non-énumération temporelle HTTP : C doit traiter réponse générique, admission, timing et cookies/CSRF. Ne pas sérialiser intent, compte, token ou motif interne.

## Persistance et verrouillage

- `models.py` : `AuthChallenge` (FK Account CASCADE, unique compte+purpose, SHA256 domaine-séparé confirmation/reset, version credential, timestamps UTC). CSPRNG256 bits/43 caractères, hash seul DB ; confirmation24h/reset30min, `now >= expires_at` refusé. Raw token/URL/HTML/password absents des tables de challenge et quotas.
- Nullable `PasswordCredential` d'A réutilisé pour pending : nouvelle inscription crée hash Argon2, réinscription pending remplace hash/version/preuve ensemble, jamais un credential avec date vérifiée non NULL, même future. Renvoi conserve hash/version et ne remplace la preuve que s'il est admis. Confirmation consomme la preuve sans auto-login ; Auth A n'émet pas de session pour pending.
- Reset demandé ne touche ni hash ni sessions. Reset valide change hash et réutilise `_revoke_all` d'A (version + suppression toutes sessions), consomme la preuve atomiquement. Les anciens resets deviennent périmés après change_password/logout_all via session_version.
- Ordre **Account → Budget singleton → quota adresse/purpose** ; les mutations de preuves verrouillent Account puis relisent avec `populate_existing`. Un lookup initial de digest identifie seulement le compte. Aucun retour Budget→Account, aucun flux multi-comptes. Adresse inconnue : Budget/quota sans verrou Account ultérieur.
- Inscription : INSERT ON CONFLICT puis verrou Account. Refus normal de budget/capacité retire uniquement l'Account nouvellement créé de cette demande ; aucun pending préexistant supprimé, aucun rollback global. Le futur HTTP doit commit les résultats normaux sans intent. Rollback volontaire du caller restaure normalement toutes les mutations/compteurs.
- Migration **e95c0278b431**, parent **d82b9147a120** : trois tables privées challenge/budget/quota, contraintes, index d'expiration. Ni catalogue public ni CatalogState modifié par ces écritures.

## Limites techniques

`raceatlas/auth/flow_limits.py`, `FlowPolicy` explicite ou construit via `AUTH_RATE_KEY` : clé serveur dédiée stable de 32–1024 octets UTF-8, vide dans `.env.example`, jamais fallback vers une autre clé. HMAC-SHA256 d'adresse normalisée, pseudonyme et non anonyme ; ne pas le publier. Rotation de clé remettrait les quotas adresse à zéro : décider la procédure opératoire avant exploitation, aucune clé réelle générée ici.

Valeurs initiales configurables par l'interface interne : cooldown60s, **3 admissions sur heure glissante**, budget global80 intentions/jour UTC et2400/mois UTC, capacité4096. Les valeurs peuvent être abaissées (cooldown jusqu'à0, capacité jusqu'à1 pour tests), bornes maximales globales80/2400/cap4096 et100 admissions/heure ; pas interface HTTP de configuration. Ce ne sont pas choix produit propriétaires ni quota du compte Resend prouvé.

Tableau de timestamps serveur admis borné à100 par quota ; aucune création par token invalide. TTL2h après dernière admission, purge indexée de32 lignes au plus par demande ; sous Budgetlock, capacité vérifiée avant nouvelle clé, saturation refuse conservativement. Refus ne prolonge pas cooldown/TTL et ne remplace pas de preuve active. Adresse absente limitée aussi, sans consommer le budget d'envois lorsqu'aucun intent n'existe. Singleton réutilisé, jour/mois remis à zéro sous verrou et heure relue après attente du verrou. Réservation comptée même si transport échoue après commit ; pas de file de retry/paywall/dépense.

Risques restant à C : saturation des budgets par abus, demandes valides coûtant KDF, limites IP/admission et traitement uniforme des échecs. Ces quotas internes ne sont pas une défense DDoS ou un SLA. Une perte de clé de limitation modifie l'historique pseudonyme ; garder cette clé secrète et stable.

## Preuves locales

Python : `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, PG17.11 PID38028/127.0.0.1:55434, DB **raceatlas_lot2_test** exclusivement avec `RACEATLAS_DISPOSABLE_DB=1`. Statut PG et absence Python/Chrome concurrent vérifiés avant premier run. Pas de processus Tester concurrent.

- Premier bloc : `pytest tests/backend/test_account_flows.py -q --tb=short --maxfail=3 --junitxml=.local-tools/b2-first.xml` : **33 PASS9,91s**.
- Bloc étendu : même fichier, `.local-tools/b2-expanded.xml` : **59 PASS25,84s**. Puis précision de l'heure glissante et preuve supplémentaire de frontière ; la migration locale inédite a été redescendue à d82 sur `_test` avant le cycle final pour appliquer son schéma final.
- B2 + régression A avant dernier garde transactionnel : `pytest tests/backend/test_account_flows.py tests/backend/test_auth_passwords.py tests/backend/test_auth_sessions.py -q --tb=short --maxfail=3 --junitxml=.local-tools/b2-final-auth.xml` : **124 PASS60,51s exit0 (60 B2 +64 A)**.
- Dernier garde DBAPI AUTOCOMMIT : ciblé transactionnel initial **7PASS/3FAIL3,78s** (.local-tools/b2-transaction-guard.xml). Les trois assertions de table vide des cas Connection externe dépendaient de l’ordre car elles ne demandaient pas la fixture session nettoyant Account. Le refus du service était effectif. Fixture privée du fichier corrigée pour nettoyer aussi Account ; relance **10PASS3,37s** (.local-tools/b2-transaction-guard-fixed.xml), sans changement des attendus.
- Fichier B2 final après garde/isolation : `pytest tests/backend/test_account_flows.py -q --tb=short --junitxml=.local-tools/b2-final-flows.xml` : **61PASS19,51s exit0**. A inchangé depuis les64PASS ci-dessus.
- Fixture database exécute upgrade head/check/downgrade base/upgrade head/check ; le nouveau schéma doit y passer. Pas de DB distante ou importante touchée.
- `python -m ruff check raceatlas migrations tests/backend` PASS ; `python -m ruff format --check raceatlas migrations tests/backend` **58 fichiers conformes** ; `node --test tests/contracts/contracts.test.mjs` **26PASS** ; runtime pip `--python <venv> check` PASS ; `git diff --check` PASS.

Les tests B2 couvrent : hash-only/pending/confirmation, réinscription et renvoi, 24h/30min juste avant/à/après, mauvais purpose/version/rejeu, reset multi-appareils/isolement, mots de passe invalides non consommateurs, rollback/commit échoué/savepoints/Connection externe, erreur email simulée, ASCII/configuration, quotas persistants/jour/mois/glissant/TTL/capacité/purge/refus, contraintes et transaction utilisable, SavedEntry/autre compte/epoch préservés. Concurrence réelle à deux connexions : état de blocage PostgreSQL observé avant libération du premier commit ; même email, double consommation, nouveau compte refusé au budget, reset contre login/change/revoke/delete dans les deux ordres légaux, ORM déjà chargé revalidé.

B1 code/templates/providers/tests inchangés, preuve ciblée exactc79c APPROVE68+10 et CI43404533408 SUCCESS589/67 réutilisée explicitement ; aucune campagne locale complète ou browser inchangée refaite. Le domaine cible et l'URL réelle future sont inchangés : [guide Resend/Webador](resend-guide.md). Aucun réseau Resend, DNS, compte externe, mail réel, service, coût ou déploiement. Corpus de passwords communs, HTTP/C, UI/planning/ICS et acceptation intégrée restent ultérieurs. Après push : SHA exact au Coordinator, gel et STOP éditions pour revue indépendante B2/CI.
