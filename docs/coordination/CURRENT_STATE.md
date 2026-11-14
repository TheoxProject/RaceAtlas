# Point de reprise RaceAtlas

**UTC2026-11-14T07:50Z — lot7, PLAN-A implémenté, publication/gel pour revue en cours.** Aucun service/DNS/email réel/déploiement. Reprise explicite après interruption : WIP conservé, même Developer, résultats terminés réconciliés, aucun contournement de quota.

## Branche, responsabilités et prochaine action

Branche **feature/private-planning**, checkout isolé **C:/Users/theop/.codex/worktrees/add4/RaceAtlas**, Developer seul writer suivi ; Root PR/notes ignorées, Tester read-only au gel. [Draft PR13](https://github.com/TheoxProject/RaceAtlas/pull/13), base **87d7dd53efcdb144c38e2d3ef1f83c89e63654fc**. HEAD local/origin avant publication **cb02b99dcbdc41af8cb3487465c07385221de3fe** ; le commit contenant ce checkpoint est le candidat PLAN-A, son SHA exact sera communiqué au gel et vérifié par Git. CI du cadrage **43518396894 SUCCESS791backend191,73s/67frontend**, gardes cb02 avant/après ; aucune CI/verdict PLAN-A présumé.

**Prochaine action sûre :** commit/push cohérent API+contrats+tests+docs, communiquer le SHA exact puis STOP éditions ; Root suit la nouvelle CI et demande revue ciblée de ce SHA. Aucun PLAN-B avant libération explicite. [Mission](../lot-7/planning-mission.md), [handoff](../lot-7/planning-handoff.md), [commandes locales](../lot-7/planning-local-development.md).

| Tâche | État |
|---|---|
| Lots0–6/PRE-01 | DONE intégrés |
| ACC-01 identité/sauvegardes internes | DONE PR11/main5e2c84, CI457/67 |
| ACC-02 backend A+B1+B2+C0+C1+C2 | DONE PR12/merge87d7, APPROVE exactda5743, PR et mainCI791/67 |
| PLAN-00 mission/Draft | DONE cb02/PR13/CIverte |
| PLAN-A API privée+snapshot | IN_PROGRESS implémentation et ciblés acquis, revue/CI candidat TODO |
| PLAN-B ICS/cache/codec/migration | TODO non commencé |
| PLAN-FINAL | TODO SHA final/revue complète/CI/merge/mainCI |
| ACC-UI/acceptation complète lot7 | TODO après intégrations |
| Lot8/candidatV1/activation | TODO dépendances/owner gates ; aucun deploy autorisé |

## PLAN-A acquis et vérifications

Quatre routes cookie-auth GET/PUT/PATCH/DELETE saved-entries, acteur persistant même Session, frontières Origin/CSRF/JSON/admission/401 passive réutilisées. DTO scope exact, jamais scopes voisins ni filtre public caché ;1000 sauvegardes,2MiB JSON,16KiB UTF8/texte. Auth READ COMMITTED puis SELECT graphe unique/raiseload/relecture fraîche, DTO et encodage avant commit/close, Response après libération. Aucune source catalogue/modèle/migration/pin/frontend/CI modifiée ; ICS reste404.

Historique honnête :10 PASS19,271s initial ; étendu18 PASS/1 FAIL36,392s ($defs/Id manquant dans nouveau contrat, corrigé). Une invocation avec deux chemins tests inexistants a terminé sans tests ; elle ne constitue aucune preuve. Puis **139 PASS118,877s**,0failure/error/skipped dans `.local-tools/plan-a-final.xml`, terminé avant interruption :19 PLAN-A+68 ACC01+29 authC1+20 fondation publique+3 options. Source inchangée depuis ce run hors docs, rapport complet réconcilié le14nov sans relance. Ruff check PASS ; format --check73 fichiers PASS ; Node26 contrats publics PASS ; pip check PASS ; schéma planning et17 références locales PASS ; diff check avant commit. Imports concurrent/reorder/replay/refus/absence uniquement synthétiques/offline, SQL1/0 et locks libérés prouvés. Pas de run791/browser/build frontend local redondant.

## Intégrations et décisions conservées

Auth PR12 merge **87d7dd53efcdb144c38e2d3ef1f83c89e63654fc**, arbre égal da5743 revu ; [intégration auth](../lot-7/auth-integration.md). Tester APPROVE complet239PASS et CI PR43514658079 SUCCESS791/67 ; mainCI **43515934267 SUCCESS791backend138,79s/67frontend**. Ces preuves concernent les chemins auth inchangés, pas une approbation PLAN-A. C1 seams29 réexercés ici. Historique C0 CI35f710PASS/7FAIL fixture URL masquée, corrigée par objet URL ;401 passive sans Set-Cookie conservée. Queue auth16+1/canaux16, probe PG clos avant fournisseur, limites crash/inflight/stop documentées ; mails simulés seulement.

Altitude2,5D initial/Summit3D à la demande ; carte/calendrier gardent période/filtres/caméra. Email+PW et confirmation avant connexion ; ICS futur planned+registered, statuts par scope et Inscrit déclaratif. AND même scope ; centres commune seulement ; absence→to_verify sans annulation inventée. PLAN-B garde mission UID UUIDv5 fixe/cachefingerprint/stampDB/SEQUENCE/caps, mais rien implémenté en A.

Resend Free choisi ; club déclaré propriétaire **ucthonon.fr/Webador**, **raceatlas.ucthonon.fr email seulement**, From futur **RaceAtlas <notifications@raceatlas.ucthonon.fr>** non vérifiés. APP_BASE_URL réelle Render inconnue et indépendante du domaine email. Auth production fermée par défaut, Development local, clés/From/URL vides et gardes false. Aucun DNS, compte externe, clé réelle, email, collecte, base distante, coût ou déploiement. Premier deploy privé après lot8/candidatV1 avec autorisation distincte ; droits FFC/terrain/délivrabilité/capacité non acquis.

## Environnement à réutiliser

Python3.12.14 **C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe**, pip via runtimePython `-m pip --python <venv>` (venv sanspipmodule). Argon2/Resend+transitifs installés proprement ; pas réinstallaveugle. Node24.22.1/pnpm10.20.0/node_modules/browsers existants. Pas wrapperpnpm11 ni fauxClockPlaywrightglobal (carteDateProxyseulement).

PG17.11 existant127.0.0.1:55434, cluster `.local-tools/pgdata-lot2-native`, user **raceatlas_local**, dernierPID38028. Vérifierpg_ctlstatus, jamaisinitdb/reseed/killglobal. DeveloperDB **raceatlas_lot2_test**, TesterDB **raceatlas_lot2_review** distinctes, **RACEATLAS_DISPOSABLE_DB=1**, preview **raceatlas_map_demo** préservée. Schéma main **f61d338ab204**, futuremigrationPLANaprès ; nepaslancerancienworktreecontreDBdéjàmigréePLAN. Dernierscontrôles aucunPython/Chrome/workertest, sourceReviewerlibérée.

Copie personnelle main2e03cd8 et autresworktreesintacts ; feature/account-authentication conservéeauSHArevu, pasreset/forcepush. Helpers/rapports/profils/probes ignorés `.local-tools`, jamaisgitaddglobal/.env/secrets. Canoniqueauth `.local-tools/tester-report-auth.md` publiéintégralPR12. Ne pasrejouer138/225testsverts pouruneinterruption sansnouveaurisque/source. Le dépôt et Git/CI font foi sur ce checkpoint.


Reprise14nov : aucun Python/Chrome actif, aucun test pendant ; Node externes non revendiqués laissés intacts. PG38028 confirmé. Ne pas relancer139 tests pour la seule reprise ; pas de schéma PLAN-B ou parser installé avant attribution. Après publication, toute modification suivie périme le gel et impose nouvelle revue/CI.
