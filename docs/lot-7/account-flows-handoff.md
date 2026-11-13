# ACC-02B2 — confirmation et récupération internes

Branche `feature/account-authentication`, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12), parent de correction B2 **aac7b40bc284a127295dfb574691297f3268226b** (B1 exactc79c approuvé), base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Le candidat est le commit contenant ce handoff, dont le SHA exact sera transmis après push. B2 doit obtenir une nouvelle revue et CI ; ni auth/PR12 ni lot7 ne sont terminés.

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

Le caller possède commit/rollback. **`AccountFlowSession(engine)` dédiée est obligatoire**, importée depuis `raceatlas.auth.flows`. Une Session SQLAlchemy brute est refusée avant toute mutation, même si son bind déclaré est un Engine. La Session dédiée hérite de Session et reste compatible avec A/planning ; aucun changement de ces services n'est nécessaire. Un seul Engine transactionnel, aucun bind Connection/multi-bind/déroutage ou DBAPI AUTOCOMMIT.

```python
from raceatlas.auth.flows import AccountFlowSession, request_registration

with AccountFlowSession(engine) as session:
    result = request_registration(session, email, password, policy=policy)
    session.commit()  # normal refusals also commit their counters
if result.intent is not None:
    result.intent.dispatch_after_commit(email_service)
```

La Session dédiée refuse Connection/Engine différent via constructeur, `connection(bind_arguments=...)`, `execute/scalar/scalars(...bind_arguments...)` par `get_bind`, `SessionTransaction.connection`, `bind_mapper` et `bind_table`. Une affectation de bind dérouté est rejetée par le garde avant mutation. Ces fences utilisent les APIs publiques, sans examiner `_connections`/should_commit internes. Le contrat couvre l'emploi normal de cette classe ; il ne protège pas contre du code serveur arbitraire contournant ses méthodes ou sabotant les internals/le driver. Les SAVEPOINT ORM de cette Session restent pris en charge. Aucun commit implicite, aucun envoi dans le service ou callback.

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

## Correction B2-F1 cycle1 — nouveau gel

Tester a rendu **REQUEST CHANGES** pour exact **aac7b40bc284a127295dfb574691297f3268226b** : une Session déclarée Engine pouvait enrôler une Connection externe par `connection(bind_arguments={"bind": connection})`. Son commit logique armait l'intent sans commit PostgreSQL externe. P2 interne, aucune route/envoi réel exposé revendiqué. L'ancienne [CI43408753657](https://github.com/TheoxProject/RaceAtlas/actions/runs/43408753657) SUCCESS **650backend225,08s /67frontend** reste historique et ne vaut pas approbation.

Restriction AccountFlowSession autorisée par le Coordinator, pas contournement d'un défaut par inspection fragile des internals. Les callers B2 et fixtures de tests emploient cette classe ; les tests négatifs continuent à utiliser une Session brute pour reproduire l'ancien enrôlement et prouver refus sans mutation/intent. Aucun changement de modèle, migration e95c, A, B1, dépendances, contrat HTTP ou source publique.

Reprise du même Developer après demande explicite propriétaire, le13novembre vers15:54UTC : Git exactaac7 propre, PG38028/55434 confirmé, aucun Python/Chrome concurrent ; aucune limite de capacité bloquante observée dans les commandes exécutées. Pas de réinitialisation/reseed ou processus d'autrui arrêté.

- `pytest tests/backend/test_account_flows.py -q -k 'enlisted or raw_engine or public_bind or bind_assignment or savepoints or external or autocommit' --tb=short --maxfail=3 --junitxml=.local-tools/b2-f1-targeted.xml` : **33PASS5,38s exit0**.
- `pytest tests/backend/test_account_flows.py -q --tb=short --junitxml=.local-tools/b2-f1-final.xml` : **89PASS9,93s exit0**, dont61régressions +28nouveaux. Fixture migration upgrade/check/base/upgrade/check exécutée sur `_test` uniquement, migration source inchangée.
- Nouveaux cas : Session Engine brute pré-enrôlée externe, create_savepoint/rollback_only ×5services ; Session brute normale ; Connection/autre Engine via8APIs publiques ; affectation bind. Refus avant données privées/intent, transaction externe laissée active par le garde ; Session dédiée reste utilisable après refus, vrai commit/close puis dispatch simulé visible depuis autre connexion.
- Ruff check PASS, Ruff format --check **58fichiers conformes**, diff PASS. Contrats : **26PASS**. A64 tests et B1 preuves ci-dessus réutilisés après diff inchangé, pas de campagne complète backend/browser locale refaite.

Nouveau SHA requis pour CI et revue indépendante ciblée ; après publication STOP éditions. Le changement de contrat Session est à conserver dans le futur wrapper C, qui reste non attribué ; aucun HTTP/UI/planning endpoints nouveau, email réel, DNS ou déploiement anticipé.
