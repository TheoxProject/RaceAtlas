# Point de reprise RaceAtlas

Checkpoint UTC **2026-11-13T08:09Z**. Lots0–6, PRE-01 et ACC-01 intégrés. **ACC-02A approuvé au jalon**, PR12 toujours Draft/non fusionnée ; lot7 non terminé. Nouvelle décision Resend versionnée pour la prochaine tâche. Aucun déploiement ou envoi réel.

## Git, ownership et prochaine action

Worktree isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, branche **feature/account-authentication**, base/main **5e2c84a99f7795da9cc2e14118549873bf4a42be**. Parent local/distant du cadrage B : **9dfd8087820608f613e5915a1839800357e1ffb9**, [Draft PR12](https://github.com/TheoxProject/RaceAtlas/pull/12). Nouveau SHA à relever après publication de ce cadrage. Aucune ancienne approbation transférée à un nouveau head.

Developer et Tester ont libéré la source A, aucun test retenu. Coordinator seul writer de la mission B1 ; puis Developer sera seul writer, Root sur PR/notes ignorées, Tester read-only. **Prochaine action sûre :** publier le cadrage Resend, vérifier la CI de son SHA, attribuer uniquement B1 défini dans docs/lot-7/resend-mission.md. B2/HTTP/UI non attribués par ce cadrage.

| Tâche | État |
|---|---|
| ACC-01 compte et sauvegardes par scope | DONE intégré PR11/mainCI |
| ACC-02A Argon2/credentials/sessions internes | DONE jalon exact9dfd, pas PR entière intégrée |
| ACC-02B1 EmailService/ResendSDK simulé/templates/config/docs | TODO, mission bornée prête |
| ACC-02B2 compte non vérifié/confirmation24h/reset30min/renvoi | TODO |
| ACC-02C HTTP/cookies/CSRF/abus/suppression | TODO |
| PLAN-01 API privée/statuts/ICS | TODO |
| ACC-UI comptes/planning intégrés | TODO |
| Domaine/expéditeur/délivrance réels | BLOCKED, aucune propriété/vérification/autorisation acquise |
| ACC-FINAL / lot8 / candidat V1 | TODO, simulations ne prouvent pas exploitation |

## Preuves A et intégrations

- A exact **9dfd8087820608f613e5915a1839800357e1ffb9** : Tester ciblé APPROVE, **132 PASS60,64s +16 PASS18,10s**, Ruff49/contrats26/pipcheck/diff. Six sondes indépendantes de concurrence inverse/ORM préchargé/rollback/slotKDF plus dix scénarios publics. [CI43389431747](https://github.com/TheoxProject/RaceAtlas/actions/runs/43389431747) SUCCESS **521 backend220,54s /67 frontend**, gardes source9dfd avant/après. Pas d'APPROVE HTTP/email/PR12 entière. Rapport complet dans PR12 et .local-tools/tester-report-authA.md.
- Developer A :132PASS63,10s (25hash/39PGsessions/68planning),10publicsPASS12,44s, migrations/checks/pipcheck/Ruff49/contrats26. Premier54PASS/7FAIL+7teardown : instrumentation Argon2 read-only, corrigée par proxy déléguant au vrai KDF ;22PASS puis25finaux. Handoff auth-handoff.md/guide auth-local-development.md. Aucun paramètre faible substitué ou campagne complète locale répétée.
- ACC-01 PR11 APPROVE **d264ae0ac7c5586e65966922caadbfe91abd811d**, merge **5e2c84a99f7795da9cc2e14118549873bf4a42be**, arbre égal **58f7a7e23ed3d0626735e2f762066de1ab55a8da**. CI PR43281879288 SUCCESS457backend209,86s/67frontend ; main43282947407 SUCCESS457backend212,75s/67frontend. F1/F2 clos cycle1. docs/lot-7/foundation-integration.md.
- PRE-01 PR10 merge51856c9940a2b0e16c9f05d61a9f1726ae8701d9 et CI PR43272958804/main43273970329 vertes389/67 ; docs/readiness/predeployment-integration.md. Lot6 PR9 merge7b733d86d99a354fdcfe2bf1ecbde519ef78a68f et CI PR43226499588/main43227636726 vertes389/67 ; docs/lot-6/integration.md. Antérieurs : docs/readiness/integration.md, docs/lot-5/integration.md.

## Décisions propriétaire et limites

**Resend Free définitivement choisi13nov**, SDK Python officiel via EmailService central/ResendEmailProvider, DevelopmentEmailProvider pour développement et tous tests automatisés. EMAIL_PROVIDER=development par défaut, RESEND_API_KEY et EMAIL_FROM vides. APP_BASE_URL souhaitée **https://raceatlas.onrender.com**, à confirmer au déploiement ; domaine ultérieur souhaité **raceatlas.com**, From souhaité **RaceAtlas <no-reply@raceatlas.com>** : ni acquis ni vérifiés. Site et domaine email indépendants. Aucun domaine non vérifié utilisé et aucun fallback resend.dev pour utilisateurs.

Inscription **email+mot de passe avant confirmation**, compte non vérifié puis lien **24h usage unique/renvoi** avant login/personnel ; récupération distincte **30min usage unique**, sessions précédentes révoquées, réponse générique. Modèles français HTML+texte aux objets/boutons définis dans resend-mission.md, liens depuis APP_BASE_URL exclusivement. Documentation propriétaire compte Free/clé minimale/domain ownership/DNS/configRender/test futur à préparer ; aucune de ces actions autorisée par le choix fournisseur.

Altitude2,5D initial/Summit à la demande ; calendrier sélectionne et conserve le mois civil affiché. ICS défaut **Prévues et Inscrit**. Premier déploiement privé **après lot8/candidatV1**. Aucun silence comme accord. Pas d'achat, compte/service externe, DNS, clé réelle, envoi réel, DB distante, collecte récurrente, publication/tag final ou déploiement sans autorisation explicite. Tests simulés complets de l'intégration Resend autorisés, pas délivrabilité revendiquée.

FFC deux GET bornés11nov échouent layout_changed/debut et html_structure, droits/listIDs non qualifiés ; aucune collecte live. Mapterhorn attributionJSON403 noncontourné12nov, licences détaillées non auditées. Voir qualificationFFC/rapportreadiness. Pas GPU physique/liveSummit acquis.

## Contrats techniques à préserver

A : Argon2id19456KiB/t2/p1/sel16/tag32, password exact15–128codepoints/512UTF8 sans normalisation, deux KDF/process et attente1s. Credential absent/non vérifié/futur refuse. Session256bits CSPRNG/SHA256DB seulement,7jours absolus/24h idle serveurUTC, version et cascade Account→Credential→Session. **Accountlock d'abord**, relecture populate_existing, verify/issue/revoke jusqu'au commit caller ; B doit respecter cet ordre. Pas d'I/O email sous verrou ou publication token/cookie avant commit. Freshlogin après logoutall permis ; preuve ancienne ne survit pas à révocation. Aucun HTTP/email encore livré.

Planning : acteur Account persistant même Session, auth doit charger sa preuve ; saved scopeRESTRICT/compteCASCADE, révision1/+1 vrai changement/no-op stable, privéUTC. Migration actuelle **d82b9147a120** aprèsc40a7162b901. Catalogue public/source/hosting/frontend inchangés.

## Environnement et reprise sûre

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, pip via runtime `--python` (venv sans pipmodule). Argon2 déjà installé proprement avec pins25.1.0/bindings26.1.0/cffi2.1.1/pycparser3.12 ; ne pas utiliser research-deps comme runtime. Node24.22.1/pnpm10.20.0/cache prêts (wrapper11 incompatible), Chromium cache .local-tools/browsers du worktree1a1e.

PostgreSQL17.11 existant127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, userraceatlas_local, PID38028 ; Developer raceatlas_lot2_test/Tester raceatlas_lot2_review avec RACEATLAS_DISPOSABLE_DB=1 ; map_demo distincte. Dernier Tester : aucun Python/Chrome/Chromium, processus de tests terminés ; anciens Node non revendiqués préservés. Vérifier avant tests, pas initdb/reseed/killglobal.

SDK officiel Resend2.53.2 inspecté seulement en wheel isolé .local-tools/resend-research-wheels, **pas installé dans le venv pendant gel A** ; B1 doit pin/installer proprement ses dépendances nécessaires. Globals SDKkey/url/client, timeout30s/redirects par défaut : points à sécuriser/tester via HTTPClient supporté, notes ignorées resend-integration-notes.md.

Git/PG/browser natifs autorisés ; création PR connecteur403 historique, fallback Git/GCM dans ses permissions sans secrets. HelpersPR7–12 ont numéros/bases statiques, ne pas les réutiliser aveuglément. Pas reset/forcepush/main direct. Pendant gel, PR/notes ignorées pour progrès ; tout changement suivi invalide verdict du head. Ne jamais archiver tout .local-tools (DB/caches/éventuels secrets). Recherches Brevo/Mailjet antérieures supersédées, aucun compte ou envoi effectué.
