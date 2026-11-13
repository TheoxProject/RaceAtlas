# Point de reprise RaceAtlas

**Checkpoint UTC 2026-11-13T09:49Z — ACC-02B1 prêt pour gel/revue, non approuvé.** Reprise explicite du même Developer après interruption de capacité ; aucune implémentation parallèle ou action distante. Voir [handoff B1](../lot-7/email-handoff.md) et [mission](../lot-7/resend-mission.md).

## Git et prochaine action sûre

Branche **feature/account-authentication**, worktree isolé add4, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12). Parent local/origin de reprise **1464dfa2db250e1816e2f7120fde371479575338**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Le commit qui contient ce checkpoint est le prochain candidat B1 ; relever `git rev-parse HEAD` après push pour le gel. Coordinator seul gère PR/CI/merge ; aucun merge ou changement main effectué ici.

**Prochaine action sûre :** publier code/tests/docs cohérents, communiquer le SHA exact au Coordinator, puis STOP éditions pendant la revue indépendante B1 et la CI de ce SHA. Ne pas lancer B2/C ou une campagne complète locale inchangée. Aucun verdict B1 actuel ; A APPROVE ne vaut pas approbation B1/PR12.

| Tâche | État |
|---|---|
| ACC-01 identité et sauvegardes | DONE intégré PR11/mainCI |
| ACC-02A primitives/sessions | DONE jalon APPROVE9dfd ; PR12 reste incomplète |
| ACC-02B1 service/SDK/templates | Implémenté, 68 tests locaux PASS ; revue/CI nouveau head TODO |
| Sujet reset exact et assertions indépendantes | DONE |
| Guide Resend/Webador, quatre rendus synthétiques | DONE préparation, pas validation externe |
| ACC-02B2 confirmation/reset/renvois/limites PG | TODO, non attribué |
| ACC-02C HTTP/cookies/CSRF/abus/suppression | TODO, non attribué |
| PLAN-01 / UI / acceptation lot7 | TODO |
| Domaine vérifié, clé, envoi réel, déploiement | BLOCKED autorisation/préconditions ; aucun effectué |

## Décisions et limites

Resend Free et SDK officiel retenus. Club propriétaire de `ucthonon.fr` selon instruction propriétaire, gestion DNS Webador ; cible **raceatlas.ucthonon.fr**, **email seulement**, From futur **RaceAtlas <notifications@raceatlas.ucthonon.fr>**. Aucune vérification Resend/DNS ou clé réelle acquise. Aucun domaine de remplacement à rechercher/acheter. Ne modifier ni supprimer les enregistrements existants du club, notamment A/CNAME/MX racine ; guide avec noms de format, valeurs réelles console uniquement et prévention du suffixe doublé. Irlande recommandée pour routage si disponible, pas résidence EU : stockage US/rétention Free30j documentés avant activation.

APP_BASE_URL doit être l’URL **réelle** Render à renseigner, non encore connue/confirmée, indépendante du domaine email. `.env.example` : provider Development, URL/clé/From/domaine vérifié vides, attestations d’autorisation/tracking false. Aucun compte externe, achat, DNS, API avec clé, email réel, service ou déploiement autorisé/exécuté. Premier déploiement privé après lot8/candidatV1 sous autorisation distincte.

Objets exacts : « Confirmez votre adresse e-mail — RaceAtlas » / « Réinitialisez votre mot de passe — RaceAtlas ». Confirmation annoncée24h et reset30min ; B2 garantira jetons hashés/usage unique/renvoi/révocation, B1 ne rend que les messages. Liens depuis APP_BASE_URL uniquement : `/#confirm-email=<token>` / `/#reset-password=<token>`. Aucun Host/Forwarded ou token query. Pas d’I/O email sous verrou Account/transaction métier ni lien publié avant commit lors de B2.

## Preuves réconciliées

- Premier run pré-interruption tronqué : résultat inconnu, ne pas le relabeller PASS. Cache sans échec non probant.
- Sauvegarde1464 : [CI43402452005](https://github.com/TheoxProject/RaceAtlas/actions/runs/43402452005) SUCCESS **589 backend227,04s / 67 frontend**, gardes exactes ; antérieure au sujet corrigé, ne valide pas le nouveau head.
- Reprise : `pytest tests/backend/test_email.py -q --tb=short --junitxml=.local-tools/email-b1-final.xml` **68 PASS2,02s exit0**, vrai SDK/HTTP entièrement simulé et réseau requests interdit.
- Régression A après dépendances : `pytest tests/backend/test_auth_passwords.py tests/backend/test_auth_sessions.py -q --tb=short --junitxml=.local-tools/email-b1-auth-regression.xml` **64 PASS20,66s exit0**, uniquement `_test` avec opt-in.
- Ruff check PASS ; Ruff format --check **54 fichiers conformes** ; pipcheck PASS ; contrats **26PASS** ; diffcheck PASS. Aucun frontend/source/API/modèle/migration/CI/hosting modifié ; pas full589 ou carte/browser inchangés répétés.
- Chromium local : deux modèles x680/390px, routes réseau bloquées, pas de débordement/boutons visibles, quatre PNG inspectés sous `.local-tools/email-b1-preview/` (noms dans handoff), aucune vraie donnée ou email émis. Pas de navigateur/serveur retenu.
- A exact **9dfd8087820608f613e5915a1839800357e1ffb9** : APPROVE ciblé, CI43389431747 SUCCESS521/67 ; code A inchangé, preuves réutilisables explicitement. B1 et PR complète restent à revoir.

## Environnement et processus

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, pip via runtime `-m pip --python <venv>`. Resend2.53.2 et transitifs épinglés déjà installés ; ne pas réinstaller ou utiliser les dossiers research comme runtime. Argon2 25.1.0 inchangé.

PostgreSQL17.11 existant127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, userraceatlas_local/PID38028 confirmé avant régression. DeveloperDBraceatlas_lot2_test, TesterDBraceatlas_lot2_review distincte, `RACEATLAS_DISPOSABLE_DB=1`. Aucun Python/Chrome actif avant les tests ; commandes ciblées et Chromium terminés exit0. Pas initdb/reseed/killglobal. Node24.22.1/pnpm10.20.0 et caches Chromium worktree1a1e préservés.

Root possède PR et notes ignorées uniquement ; Developer stop après gel, Tester futur read-only. Plan `.local-tools/tester-email-probe-plan.md` à contextualiser : domaine choisi mais non vérifié. ACC-01 intégration et lots antérieurs liés depuis README ; FFC droits/compatibilité, délivrabilité, clients mail réels et acceptation auth complète restent limites. Pas de reset/forcepush/main direct, pas collecte live, aucun secret dans les preuves.
