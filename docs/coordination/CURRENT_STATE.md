# Point de reprise RaceAtlas

**UTC2026-11-14T08:15Z — lot7, PLAN-A+B candidat final implémenté/testé, publication et gel pour acceptation complète.** Aucun réseau fournisseur, email réel, DNS, coût, service, DB distante ou déploiement. Même Developer, WIP/caches préservés à la reprise.

## Branche et prochaine action

Branche **feature/private-planning**, checkout isolé **C:/Users/theop/.codex/worktrees/add4/RaceAtlas**, Developer seul writer suivi ; Root PR/notes ignorées, Tester read-only au gel. [Draft PR13](https://github.com/TheoxProject/RaceAtlas/pull/13), base **87d7dd53efcdb144c38e2d3ef1f83c89e63654fc** inchangée. HEAD=origin avant publication finale **ae446a5f1ff266a1f4590930485469ce973dff5e** ; le commit contenant ce checkpoint est le candidat final A+B, son SHA exact est communiqué après push puis vérifié par Git.

**Prochaine action sûre :** commit/push cohérent B, communiquer SHA exact et STOP éditions. Root suit nouvelle CI et demande acceptation indépendante **COMPLÈTE PR13 PLAN-A+B** ; pas une approbation B seule ni lot7 terminé. Aucun prochain push avant conclusion CI précédente, aucune UI/lot8/main direct. [Mission](../lot-7/planning-mission.md), [handoff final](../lot-7/planning-ics-handoff.md), [commandes](../lot-7/planning-local-development.md).

| Tâche | État |
|---|---|
| Lots0–6/PRE-01 | DONE intégrés |
| ACC-01 identité/sauvegardes internes | DONE PR11/main5e2c84, CI457/67 |
| ACC-02 backend A+B1+B2+C0+C1+C2 | DONE PR12/merge87d7, APPROVE exactda5743, PR/mainCI791/67 |
| PLAN-00 mission/Draft | DONE cb02/CI43518396894 SUCCESS791backend191,73s/67frontend |
| PLAN-A API privée+snapshot | DONE ciblé ae446/APPROVE/CI810+67 ; preuves réutilisées après diff |
| PLAN-B ICS/cache/codec/migration | IN_PROGRESS livraison et ciblés acquis, CI/revue candidat final TODO |
| PLAN-FINAL | TODO SHA final/revue complète/CI/merge/mainCI |
| ACC-UI/acceptation complète lot7 | TODO après intégrations |
| Lot8/candidatV1/activation | TODO dépendances/owner gates ; aucun deploy autorisé |

## Gate A et candidat B

Gate PLAN-A exacte **ae446a5f1ff266a1f4590930485469ce973dff5e** : Tester APPROVE ciblé139PASS126,22s+8sondes26,12s, `.local-tools/tester-report-planA.md` ; CI **43572962256 SUCCESS810backend162,74s/67frontend**, Ruff73/contrats/build/pip et gardes ae446 avant/après. Source explicitement libérée. Cette preuve ne vaut pas approbation finale A+B.

B livré : codec runtime stdlib pur DTO, GET/HEAD `/api/v1/me/calendar.ics`, serveur sélectionne strictement planned+registered sans filtre public. Snapshot source unique scoped/raiseload sous auth READ COMMITTED et Accountlock, ledger batch3 requêtes pour201événements, rien par événement. Nouveau PersonalCalendarEventStore/migration **a74d915e3c02** après f61, PK account+scope, CASCADE account/scope sans affaiblir SavedEntryRESTRICT. Fingerprint métier+incarnation, stampDB/SEQUENCE0..2147483647, UID namespace/tuple exacts, rétention même unsave jusqu'à purge account/scope sans TTL/LRU.

Caps1000saved/1000events/2MiB exact/16KiB texte émis composé/10000paires, refus explicite sans tronquer ; cap retenu permet update existant mais refuse nouvelle paire. Date all-day fin exclusive, UTF8/CRLF/fold75octets codepoints intacts, pas METHOD/invites/GEO/heure inventée. STATUS:CANCELLED seulement fait source. Rendu avant DML et commit/close avant Response ; rollback complet cap/codec/DML/commit. Fichier statique, aucune synchronisation automatique des imports précédents garantie. Aucun favori/statut/source/publicepoch changé par export.

Dev-only **icalendar7.3.0/python-dateutil4.0.0** résolus/dry-run/metadata puis installés via runtimepip --python venv. tzdata2026.6/typing_extensions4.16 existants réutilisés, pipcheckPASS. Runtime requirements inchangés, pas Django. Provenance/licences dans [notice](../third-party/planning-parser.md).

## Résultats réels et incidents

Final ciblé **113 PASS97,59s**, exit0, `.local-tools/plan-b-final.xml` :21 codec/parser+21 PG/HTTP+19 API-A+29 authC1+20 fondation publique+3 options. Ajout ensuite d'une preuve processus/restart/APP_BASE_URL/TZ/PYTHONHASHSEED : **1 PASS3,47s**, `.local-tools/plan-b-process-formatted.xml`, produit inchangé. Donc114 cas exécutés sans échec au candidat final, pas une prétendue unique campagne114. Migration native `_test` upgrade/check/base/upgrade/check incluse au run113. Ruff lint/format78 PASS,26 contrats publics Node PASS, schéma planning/17refs locales PASS, pipcheck/diff PASS avant commit.

Développement B conservé : codec19PASS/2FAIL (encodage littéraux à la création), corrigé21PASS0,97s ; PG11PASS/3FAIL16,32s maxfail3 (hooks nouveaux mauvais Engine, fixture201 sans position, suppression brute bloquée par règles), tests corrigés17PASS21,27s puis113 final. Gardes produit/assertions métier préservés. A historique :10PASS19,271s,18PASS/1FAIL36,392s contratId manquant corrigé ; invocation deux chemins inexistants sans tests, puis139PASS118,877s avant interruption, réconcilié sans relance. JUnit ignorés conservés, pas cache pytest assimilé à un résultat.

Seams API-A et authC1 réexercés ; ACC01core68 inchangé et preuves auth intégrées réutilisées après diff. Aucun run810/backend complet ou navigateur/buildfrontend local redondant : frontend, moteur carte, source/sync, auth core et hosting inchangés. CI complète du nouveau candidat et revue exactes restent exigées.

## Intégrations et limites conservées

Auth PR12 merge **87d7dd53efcdb144c38e2d3ef1f83c89e63654fc**, arbre da5743 revu ; [intégration auth](../lot-7/auth-integration.md). Tester APPROVE complet239PASS et CI PR43514658079 SUCCESS791/67 ; mainCI **43515934267 SUCCESS791backend138,79s/67frontend**. Historique C0 CI35f710PASS/7FAIL fixtureURL masquée corrigée,401 passive sansSet-Cookie conservée. Queue auth16+1/channels16/probePGclos avant fournisseur ; limites crash/inflight/stop documentées, mails simulés seulement.

Altitude2,5D initial/Summit3D à la demande ; carte/calendrier gardent période/filtres/caméra. Email+PW et confirmation avant connexion ; ICS planned+registered, statuts par scope et Inscrit déclaratif. AND même scope ; centres commune seulement ; absence→to_verify sans annulation inventée. Aucun nouveau profil produit/feed/UI.

Resend Free choisi ; club déclaré propriétaire **ucthonon.fr/Webador**, **raceatlas.ucthonon.fr email seulement**, From futur **RaceAtlas <notifications@raceatlas.ucthonon.fr>** non vérifiés. APP_BASE_URL réelle Render inconnue, indépendante du domaine email. Auth production fermée par défaut, Development local, clés/From/URL vides et gardes false. Premier deploy privé après lot8/candidatV1 avec autorisation distincte ; droits FFC/terrain/délivrabilité/capacité non acquis.

## Environnement à réutiliser

Python3.12.14 **C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe**, pip via runtimePython `-m pip --python <venv>` (venv sanspipmodule). Argon2/Resend+transitifs installés proprement ; pas réinstallaveugle. Node24.22.1/pnpm10.20.0/node_modules/browsers existants. Pas wrapperpnpm11 ni fauxClockPlaywrightglobal (carteDateProxyseulement).

PG17.11 existant127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, user **raceatlas_local**, dernierPID38028. Vérifierpg_ctlstatus, jamaisinitdb/reseed/killglobal. DeveloperDB **raceatlas_lot2_test**, TesterDB **raceatlas_lot2_review** distinctes, **RACEATLAS_DISPOSABLE_DB=1**, preview **raceatlas_map_demo** préservée. Schéma base auth **f61d338ab204**, schéma Developer `_test` désormais **a74d915e3c02** ; nepaslancerancienworktreecontreDBdéjàmigréePLAN. Source Reviewer libérée avant B ; runtime/fixtures fermés après les ciblés.

Copie personnelle main2e03cd8 et autresworktreesintacts ; feature/account-authentication conservéeauSHArevu, pasreset/forcepush. Helpers/rapports/profils/probes ignorés `.local-tools`, jamaisgitaddglobal/.env/secrets. Canoniqueauth `.local-tools/tester-report-auth.md` publiéintégralPR12. Ne pasrejouer138/225testsverts pouruneinterruption sansnouveaurisque/source. Le dépôt et Git/CI font foi sur ce checkpoint.



Pas de processus test/serveur retenu après113+1 ; PG38028/55434 conservé, `_review` réservé Tester. Node externes non revendiqués intacts. Ne pas exécuter ancien worktree contre `_test` migrée a74. Aucune réexécution113/139 pour checkpoint documentaire. Après gel, toute modification suivie impose renouvellement revue/CI.
