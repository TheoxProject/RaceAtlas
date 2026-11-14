# Point de reprise RaceAtlas

**UTC 2026-11-14T08:52Z — lot 7, ACC-UI UI-1 IN_PROGRESS après transfert Developer.**

## État et prochaine action

Branche **feature/accounts-ui**, checkout isolé **C:/Users/theop/.codex/worktrees/add4/RaceAtlas** réutilisé proprement après PR13. Base HEAD=origin/main **b55f4c66e579046c09ee5cd8745fbeed4f566848** avant ce commit de cadrage ; futur SHA local/remote obtenu après commit, pas deviné ici. Draft PR à ouvrir immédiatement après push ; pas de code UI livré/revu. Root seul writer du cadrage, Developer en attente ; après transfert Developer seul writer suivi, Root PR/notes ignorées, Tester read-only au gel.

**Prochaine action sûre :** implémenter et vérifier UI-1 selon [mission](../lot-7/accounts-ui-mission.md). Pas d'édition produit avant transfert ; pas de merge avant acceptation finale et CI exacte.

| Tâche | État |
|---|---|
| Lots0–6/PRE-01 | DONE intégrés |
| ACC-01 identité/sauvegardes internes | DONE PR11/main5e2c84 |
| ACC-02 backend compte/email | DONE PR12/merge87d7, APPROVE exactda5743, PR/mainCI791/67 |
| PLAN API privée/ICS | DONE PR13/mergeb55, APPROVE exact679ec3, PR/mainCI853/67 |
| UI-00 cadrage/Draft | DONE 5643a8d/PR14, CI suivie Root |
| UI-1 fondations/parcours compte | IN_PROGRESS Developer seul writer, puis revue ciblée |
| UI-2 saison/export/opérations sensibles | TODO après UI-1 |
| ACC-UI FINAL/lot7 local | TODO acceptation complète finale/CI/merge/mainCI |
| Lot8/candidatV1/activation | TODO dépendances et owner gates |

## Intégration acquise, pas à rejouer

[PR13](https://github.com/TheoxProject/RaceAtlas/pull/13) confirmée merged, head revu **679ec3e0dd53669d445a254f2b840c503a087bbb**, merge **b55f4c66e579046c09ee5cd8745fbeed4f566848**, arbre identique **dbda4b2fc2a1a7e75939e4cec74b29f8531c78c3** (fetch/diff vérifiés). Tester APPROVE complet A+B : 27 PASS courants6,27s + preuves produit113PASS/16sondes réutilisées après diff nul. CI PR43576022192 SUCCESS853backend238,36s/67frontend ; main43576573783 SUCCESS853backend156,11s/67frontend, gardes source avant/après. [Intégration durable](../lot-7/planning-integration.md). PLAN-F1 initialaa077 113PASS/1FAIL Windows CP1252 corrigé test-only, jamais relabellisé PASS. Rapports complets publiés PR13, canonical ignoré .local-tools/tester-report-planning.md.

[PR12](https://github.com/TheoxProject/RaceAtlas/pull/12) backend auth intégré87d7, head da5743, APPROVE complet239PASS, CI791/67 ; [preuve](../lot-7/auth-integration.md). Cookies opaques, email/hashonly/confirmation24h/reset30m, CSRF/Origin/admission/dispatcher borné déjà livrés. Defaults fermés, Development local/tests. Ne pas confondre backend terminé et lot7 complet.

## Décisions UI documentées

Compte en dialog accessible ; carte/calendrier restent montés et conservent caméra/période/filtres/selection. Email+PW puis confirmation avant login, pas auto-login après confirmation/reset. Bootstrap pré-React capture fragment en RAM puis scrub, POST explicite uniquement. Contrôleur privé génération/abort/identité, pas retry silencieux. CSRF→GETme attendu→opération avec même proof ; pour lectures privées header optionnel vérifié côté serveur avant données, clients sans header compatibles. Voir mission pour bornes/critères et tests interleavings. Ma saison tous scopes propres, ICS Prévues+Inscrit statique, Inscrit déclaratif.

Préparations lecture seule ignorées : developer-accounts-ui-design.md, accounts-ui-integration-notes.md, ui-read-context-design.md. Aucun code/test/DB/install UI exécuté pendant ces préparations. Aucun verdict UI existant.

## Environnement et interdictions de reprise aveugle

Python3.12.14 : C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe. Venv sans pip module ; runtimePython -m pip --python si besoin prouvé, pas réinstallation. Node24.22.1/pnpm10.20.0/node_modules et browsers existants (pas pnpm11). Playwright DateProxy seulement pour date fixe, pas page.clock.set_fixed_time qui casse RAF/Summit.

PG17.11 loopback127.0.0.1:55434, cluster .local-tools/pgdata-lot2-native, user raceatlas_local, dernierPID38028 ; vérifier statut avant réutilisation, jamais initdb/reseed/killglobal. DeveloperDB raceatlas_lot2_test, TesterDB raceatlas_lot2_review, preview raceatlas_map_demo préservée ; RACEATLAS_DISPOSABLE_DB=1. Les DB test/review sont à **a74d915e3c02**, ne pas utiliser un ancien checkout contre ce schéma. Aucun test/serveur/browser conservé après acceptation PLAN ; processus Node externes non revendiqués intacts. Fermer runtime/workers avant dispose Engine. Aucun autre writer actif attribué.

Copie personnelle main2e03cd8 et autres worktrees intacts. Branches historiques conservées, pas reset/clean/forcepush. .local-tools ignoré jamais gitaddglobal. Git/CI priment les notes ; source figée pendant revue, changements suivis imposent nouveau verdict/CI.

## Limites externes

Resend Free retenu ; club déclare posséder ucthonon.fr/Webador, raceatlas.ucthonon.fr email seulement, futur From RaceAtlas <notifications@raceatlas.ucthonon.fr> non vérifié. APP_BASE_URL Render réelle inconnue. Aucun compte/service/DNS/email réel/achat/remoteDB/déploiement/collecte autorisé. Premier déploiement privé après lot8/candidatV1 et autorisation distincte. Droits FFC/terrain, délivrabilité, capacité Free/physicalGPU restent à qualifier ; aucune activation automatisée. Owner silence jamais approbation. Quotas non mesurables, pas de promesse de reprise automatique.

Transfert réel UI-1 : HEAD=origin feature/accounts-ui **5643a8d0dd2590df69cc71a1dfda4fa089994b9b**, [Draft PR14](https://github.com/TheoxProject/RaceAtlas/pull/14). Checkout/processus vérifiés propres et aucun Python/Chrome actif. Developer seul writer suivi, Root PR/notes ; pas UI-2. Première étape raccord read-proof compatible et headers HTML ciblés, puis bootstrap/client/dialog et preuves réelles compilées. Ne pas lancer de campagne853 backend locale redondante.

UI-1 checkpoint intermédiaire : raccord lecture X-CSRF-Token optionnel et verify_request mutation keyword-only, headers HTML frame-ancestors/XFO/referrer ciblés implémentés.9 tests PG/HTTP PASS24,72s (.local-tools/ui1-read-context.xml) : cookie A/proof A puis cookie B même nonce/retour A refus avant tout SQL privé, GET/HEAD/sans-header compatibles, invalid/expiry/no_nonce, preuve seule nonbearer et Origin mutation requis. Ruff format79/lint et contrats publics26 PASS. Pas de migration/deps ; frontend bootstrap/controller en cours non livrés dans ce checkpoint, pas APPROVE UI. CI cadrage43577679731 SUCCESS853backend171,84s/67frontend au5643, ne valide pas ce nouveau raccord. Prochaine action : publier cet incrément backend testé pour CI, puis poursuivre uniquement UI-1 ; aucun UI-2.
