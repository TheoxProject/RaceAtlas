# Point de reprise RaceAtlas

Dernier checkpoint UTC **2026-11-13T07:54:45Z**. Lots 0–6, PRE-01 et fondation ACC-01 intégrés ; **ACC-02A testé, à publier/geler pour revue ciblée et CI**, lot 7 non terminé. Aucun déploiement.

## Travail actuel et prochaine action

Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche **feature/account-authentication** depuis `origin/main` **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Parent local/distant **37ca92a842cc5ba0413245120e029ebd3f28eab8**, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/12. CI cadrage `43385747578` SUCCESS (457 backend / 67 frontend), pas une preuve du WIP auth. Developer seul writer ; Root PR/notes ignorées, Tester sans processus actif.

**Prochaine action sûre :** publier le jalon cohérent et transmettre son SHA gelé au Tester/Coordinator pour CI, puis arrêter les éditions. Handoff `docs/lot-7/auth-handoff.md`, guide `auth-local-development.md`, deux tests `test_auth_passwords.py` et `test_auth_sessions.py`. B/C non attribués, aucun HTTP/frontend/email/activation. Nouveau SHA exige preuve et CI propres.

| Tâche | État |
|---|---|
| ACC-01 identité/sauvegardes privées par scope | DONE, PR11 et mainCI vérifiées |
| ACC-02A hash/credentials/sessions internes | Testé, à publier/geler pour revue ciblée |
| ACC-02B inscription/confirmation/reset simulés | TODO |
| ACC-02C HTTP/cookies/CSRF/abus/suppression | TODO |
| PLAN-01 API privée/statuts/ICS | TODO |
| ACC-UI comptes/planning intégrés | TODO |

ACC-02A : Argon2id 19456 KiB/t2/p1/sel16/tag32, argon2-cffi25.1.0 et transitives épinglées/installées dans la venv projet via runtime pip ; pip check PASS, dossier de recherche ignoré non utilisé comme runtime. Mots de passe exacts 15–128 codepoints / 512 octets UTF-8, espaces conservés ; KDF deux travaux simultanés/processus, attente maximale une seconde, coût local non assimilé à Render/RSS. Credentials vérifiés requis ; Account seul ne connecte pas. Tokens 32 octets CSPRNG, SHA-256 uniquement en DB, 7 jours absolus / 24 h idle ; version privée et suppression des sessions à révocation.

Sérialisation : Account FOR UPDATE d'abord, relecture credentials/session populate_existing, vérification/émission ou révocation sous verrou jusqu'au commit caller. Un résultat de vérification ancien ne survit pas à une révocation ultérieure ; une connexion fraîche après logout-all reste permise si le mot de passe est inchangé. Future B doit conserver cet ordre ; token retourné avant commit n'est pas une émission persistée, futur HTTP publiera le cookie seulement après commit. Chaîne FK Account→PasswordCredential→AuthSession CASCADE, évitant résurrection après suppression/recréation de credentials.

Migration `d82b9147a120` après `c40a7162b901`, sources/app/routes/serve/CI/contrats/frontend inchangés. PG existant PID38028/55434 vérifié, aucun Python/Chrome de test concurrent, `_test` et caches seulement. Premier ciblé : **54 PASS / 7 FAIL + 7 erreurs teardown en33,43 s** ; les 39 cas sessions PG étaient verts, 7 sondes KDF tentaient de remplacer des méthodes read-only. Proxy de sonde déléguant au vrai Argon2 : **22 primitives PASS5,02 s** après une unique relance autorisée (premier appel natif rejeté pour timeout de revue automatique, pas un refus de sûreté). Ajout ciblé ASCII PHC/NUL ; **132 auth + planning PASS63,10 s**, code0 (25 primitives/39 sessions/68planning), puis **10 publics PASS12,44 s**, 72 désélectionnés. Cycles migration/check effectivement réussis. Ruff lint/format **49 fichiers**, pip check final, **26 contrats/diff PASS**. Aucun processus Developer retenu ; aucune primitive faible substituée, aucun full457/browser répété. Mesure locale hash41,36/35,78/47,58ms et verify48,98/40,59/42,56ms, sans PHC/secret/RSS/Render archivé. Autres preuves ACC-01/publiques/UI/hosting réutilisées après diff, pas un verdict nouveau. Linux/dépendances et CI complète du candidat restent à confirmer.
| Expéditeur réel | BLOCKED, aucun domaine/expéditeur validé |
| ACC-FINAL / lot8 / candidat V1 | TODO, pas de clôture lot7 par simulation |

## Preuves intégrées

- ACC-01 [PR11](https://github.com/TheoxProject/RaceAtlas/pull/11), APPROVE exact **d264ae0ac7c5586e65966922caadbfe91abd811d**, merge **5e2c84a99f7795da9cc2e14118549873bf4a42be**, arbres identiques **58f7a7e23ed3d0626735e2f762066de1ab55a8da**. CI PR43281879288 SUCCESS457backend209,86s/67frontend ; CI main43282947407 SUCCESS457backend212,75s/67frontend, gardes exactes avant/après. F1/F2 clos cycle1, Tester80PASS28,54s et réutilisation compatible explicite. Rapport PR et docs/lot-7/foundation-integration.md. Aucun login/UI/ICS livré.
- PRE-01 PR10 APPROVE0eab2819, merge51856c9940a2b0e16c9f05d61a9f1726ae8701d9, CI PR43272958804/main43273970329 vertes389/67. Rapport concret de pré-déploiement et régionFrankfurt/attributionhref prêts sans activation ; docs/readiness/predeployment-integration.md.
- Lot6 PR9 APPROVE302462c, merge7b733d86d99a354fdcfe2bf1ecbde519ef78a68f ; CI PR43226499588/main43227636726 vertes389/67. Caméra10s/60°/DEM>100 inchangée, horloge navigateur Date-only. docs/lot-6/integration.md. Antérieurs : docs/readiness/integration.md, docs/lot-5/integration.md.

## Décisions acquises et contraintes

Altitude2,5D initial, Summit3D à la demande ; ouverture calendrier depuis Année/Semaine sélectionne le mois civil affiché, conservé au retour Carte. Comptes **email+mot de passe saisis, confirmation email obligatoire avant connexion**, récupération par email. ICS par défaut **Prévues et Inscrit**. Premier déploiement privé **après lot8/candidatV1**. Aucun domaine/expéditeur disponible ; aucune question produit pendante sur ces points.

Transport local simulé seulement : ne prouve pas délivrabilité et ne remplace pas le prérequis expéditeur. Aucun service/compte externe choisi/créé, DNS/achat/email réel. Déploiement, DB distante, paiement, email réel, collecte récurrente et tag/publication finale demandent autorisation explicite ; aucun silence comme accord.

FFC : deux GET limités11nov échouent layout_changed/debut et html_structure ; droits et IDs de listes non établis, aucune collecte live activée. Mapterhorn attributionJSON403 noncontourné12nov, licences terrain détaillées non auditées ; voir qualificationFFC/rapportreadiness. Aucun test GPU physique/liveSummit acquis.

ACC-01 acteur interne Account persistant de même Session ORM, pas preuve auth. SavedEntry scopeFKRESTRICT/compteCASCADE, révision1/+1sur vrai changement, no-opstable, privé UTC ; migration actuelle **c40a7162b901**. Futur auth charge acteur validé serveur. Argon2id choisi et comparaison locale documentée dans docs/lot-7/auth-security-decisions.md ; pas implémentation/RSSRender déjà validée.

## Environnement et processus

Python3.12.14 cache `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe` (pas pipmodule ; pip via runtime --python). Node24.22.1/pnpm10.20.0/cache prêts, wrapper11 incompatible à éviter. Chromium PLAYWRIGHT_BROWSERS_PATH=`C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`.

PostgreSQL17.11 existant127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, userraceatlas_local, PID38028 confirmé13nov07:21UTC. DeveloperDBraceatlas_lot2_test / TesterDBraceatlas_lot2_review, RACEATLAS_DISPOSABLE_DB=1 ; previewraceatlas_map_demo distincte. Inventaire natif sans Python/Chrome/Chromium ; anciens Node non revendiqués laissés intacts, pas de writer/test assigné actif. Vérifier ownership avant toute interruption de processus ; ne pas initdb/reseed/tuer tousNode/PG.

Dossier ignoré `.local-tools/auth-research-deps` contient Argon2 isolé pour comparaison, n'est pas le venv projet : Developer doit pin/installer proprement sa dépendance bornée pour ACC-02A. Pas réinstallation/retests complets inchangés à chaque commit.

Git natif/DB/browser nécessitent exécution native autorisée. Connecteur créationPR403 historique : fallback Git/GCM dans permissions existantes sans secrets ; helpersPR7–11 ont numéros/bases statiques, ne pas fusionner une nouvelle PR avec eux. Pas reset/forcepush/main direct. Pendant gel, Root tient état dans PR/surfaces ignorées, pas commitcheckpoint qui invalide le SHA. Ne jamais archiver globalement `.local-tools` (caches/DB/éventuels secrets).
