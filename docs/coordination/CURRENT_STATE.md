# Point de reprise RaceAtlas

Dernier checkpoint UTC **2026-11-13T07:24Z**. Lots0–6, PRE-01 et **fondation ACC-01 intégrés** ; lot7 en cours, aucun déploiement. La reprise réconcilie Git/CI après interruption, sans supposer du travail de fond.

## Travail actuel et prochaine action

Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche **feature/account-authentication** depuis `origin/main` **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Au cadrage local/main égal, Draft à publier ; aucun code ACC-02 écrit ni verdict présumé. Checkout personnel main et autres worktrees préservés. Coordinator seul writer du cadrage, Developer/Tester précédents terminés et source libérée.

**Prochaine action sûre :** publier ce cadrage et la Draft auth, contrôler sa CI, attribuer ACC-02A borné au Developer dans docs/lot-7/auth-mission.md. Pas de tâches B/C ni source parallèle avant son gel/revue. Nouveau SHA exige nouvelle preuve/CI ; pas de copie d'ancien APPROVE.

| Tâche | État |
|---|---|
| ACC-01 identité/sauvegardes privées par scope | DONE, PR11 et mainCI vérifiées |
| ACC-02A hash/credentials/sessions internes | TODO, première attribution bornée |
| ACC-02B inscription/confirmation/reset simulés | TODO |
| ACC-02C HTTP/cookies/CSRF/abus/suppression | TODO |
| PLAN-01 API privée/statuts/ICS | TODO |
| ACC-UI comptes/planning intégrés | TODO |
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
