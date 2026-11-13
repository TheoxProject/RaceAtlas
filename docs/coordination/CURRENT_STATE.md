# Point de reprise RaceAtlas

**UTC2026-11-13T22:12Z — lot7, PLAN-01 cadrage, auth backend intégré/mainCI verte.** Aucun service/DNS/email réel/déploiement. Les reprises explicites ont conservé WIP/caches et les mêmes agents, sans changement de modèle pour contourner quota.

## Branche, responsabilités et prochaine action

Branche **feature/private-planning**, checkout isolé **C:/Users/theop/.codex/worktrees/add4/RaceAtlas** réutilisé propre après merge, aucun autre writer. Base locale/distante vérifiée **87d7dd53efcdb144c38e2d3ef1f83c89e63654fc**, mainCI43515934267 SUCCESS791backend138,79s/67frontend. Ce commit de cadrage sera publié puis Draft PR créée ; SHA/URL/CI relevés Root, pas de code PLAN ou verdict encore.

**Prochaine action sûre :** publier PLAN-00/Draft et suivre CI, puis attribuer PLAN-A API/snapshot au Developer selon [mission](../lot-7/planning-mission.md). Root possède ces trois docs jusqu'au transfert, ensuite PR/notes seulement ; Tester read-only. Aucun test/commande/worker précédent pendant, aucune UI/lot8/main direct.

| Tâche | État |
|---|---|
|Lots0–6/PRE-01|DONE intégrés, preuves docs lots/readiness|
|ACC-01 identité/sauvegardes internes|DONE PR11/main5e2c84, CI457/67|
|ACC-02 backend A+B1+B2+C0+C1+C2|DONE PR12/merge87d7/APPROVE exactda5743/PRetmainCI791/67|
|PLAN-00 mission/Draft/integrationauth|IN_PROGRESS publication/CI TODO|
|PLAN-A API privée+snapshot|TODO|
|PLAN-B ICS/cachemétadonnées|TODO|
|PLAN-FINAL|TODO SHAfinal/revue/CI/merge/mainCI|
|ACC-UI/acceptation complète lot7|TODO après intégrations, expéditeur réel non qualifié|
|Lot8/candidatV1/activation|TODO dépendances/owner gates, aucun deploy autorisé|

## Intégration et choix acquis

[PR12](https://github.com/TheoxProject/RaceAtlas/pull/12) : reviewed **da5743c500603a11366080e97cd2e76db7cbcb33**, merge/main **87d7dd53efcdb144c38e2d3ef1f83c89e63654fc**, arbres identiques **dafa5967ca7f9726729e9a94cefae5f3a102deba**. Tester239PASS locaux (22545,70s+14sondes6,98s), APPROVE complet ; CI PR43514658079 SUCCESS791backend161,56s/67frontend et main43515934267 SUCCESS791backend138,79s/67frontend, sources exactes avant/après. [Intégration auth](../lot-7/auth-integration.md), rapport final intégral PR. UI/ICS/lot7 entière non couverts.

B2-F1 transactionexterne corrigé par AccountFlowSession ; C0-F1 fixtureURLstr masquée etC0-F2 bodycache8KiB corrigés. CI35f710PASS/7FAIL reste échec historique.401passive sansSet-Cookie, récupérationGETcsrf→login. C2 queue16+1/worker paresseux/channels16/probePGclos avantprovider, pertecrash/inflight/stop incomplet honnêtes,1KDF registration, pas garantie temporelle/capacité. Tous mails simulés, SDKfakewire avec sockets/DNS interdits.

Altitude2,5D initial/Summit3D à la demande ; carte/calendrier gardent période/filtres/caméra. Email+PW puis confirmation avantconnexion ; ICS planned+registered, statuts parscope et Inscrit déclaratif. AND même scope, centrescommune seulement, absence→to_verify jamais annulation inventée.

Resend Free définitif ; club déclaré propriétaire **ucthonon.fr/Webador**, sousdomaine **raceatlas.ucthonon.fr emailseulement**, From futur **RaceAtlas <notifications@raceatlas.ucthonon.fr>** non vérifiés. APP_BASE_URL réelleRender inconnue/indépendanteHost-email. Defaultsauthfermée/Developmentlocal, clés/From/URLvides/gardesfalse. Aucun DNS club modifié ou compte/clé/email/service/coût/remoteDB/deploy/collecte. Premier deployprivé aprèslot8/candidatV1 sousautorisationdistincte ; droits/compatibilitéréelleFFC/terrain/délivrabilité/capacité physique nonacquis.

PLAN : mission fige READCOMMITTEDauth puis SELECTgrapheunique/scoped, caps1000saved/1000events/2MiB/16KiBchamp/10000paires, UIDUUIDv5fixe account+scope, cachefingerprint/DTSTAMPDB/SEQUENCE retenujusqu'àcompte/scopepurge. Aucun feed/optionproduitnouvelle. Parser indépendanticalendar7.3.0 dev-only autorisé, vérifiervenv/transitifs puis pinsréels sansruntime/Django.

## Environnement à réutiliser

Python3.12.14 **C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe**, pip via runtimePython `-m pip --python <venv>` (venv sanspipmodule). Argon2/Resend+transitifs installés proprement ; pas réinstallaveugle. Node24.22.1/pnpm10.20.0/node_modules/browsers existants. Pas wrapperpnpm11 ni fauxClockPlaywrightglobal (carteDateProxyseulement).

PG17.11 existant127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, user **raceatlas_local**, dernierPID38028. Vérifierpg_ctlstatus, jamaisinitdb/reseed/killglobal. DeveloperDB **raceatlas_lot2_test**, TesterDB **raceatlas_lot2_review** distinctes, **RACEATLAS_DISPOSABLE_DB=1**, preview **raceatlas_map_demo** préservée. Schéma main **f61d338ab204**, futuremigrationPLANaprès ; nepaslancerancienworktreecontreDBdéjàmigréePLAN. Dernierscontrôles aucunPython/Chrome/workertest, sourceReviewerlibérée.

Copie personnelle main2e03cd8 et autresworktreesintacts ; feature/account-authentication conservéeauSHArevu, pasreset/forcepush. Helpers/rapports/profils/probes ignorés `.local-tools`, jamaisgitaddglobal/.env/secrets. Canoniqueauth `.local-tools/tester-report-auth.md` publiéintégralPR12. Ne pasrejouer138/225testsverts pouruneinterruption sansnouveaurisque/source. Le dépôt et Git/CI font foi sur ce checkpoint de cadrage.
