# Point de reprise RaceAtlas

**UTC 2026-11-14T18:13Z — UI1-F1 cycle1 corrigé, publication/gel pour renouvellement revue ciblée.**

## État et prochaine action

Branche **feature/accounts-ui**, checkout isolé add4, [Draft PR14](https://github.com/TheoxProject/RaceAtlas/pull/14), base **b55f4c66e579046c09ee5cd8745fbeed4f566848**. HEAD/origin avant correctif **8f3aaf88cceb9f33cfda28d56a4413f8c86cb8f4**, CI43578191784 SUCCESS862backend174,30s/67frontend/gardes exactes. Cadrage5643CI43577679731 SUCCESS853/67. Ces CI ne valident pas le nouveau frontend ; SHA candidat communiqué après commit/push.

Developer seul writer suivi ; Root PR/notes, Tester readonly au gel. **Prochaine action sûre :** publier incrément UI-1+CI avec preuves et donner SHA exact ; STOP edits pour revue ciblée UI-1/CI courante. Aucun UI-2 avant libération, aucun merge avant acceptation finale du périmètre et integratedsuccess exact puis mainCI complète. [Mission](../lot-7/accounts-ui-mission.md), [handoff](../lot-7/accounts-ui-handoff.md), [commandes](../lot-7/accounts-ui-local-development.md).

| Tâche | État |
|---|---|
| Lots0–6/PRE-01, ACC-01/ACC-02 backend, PLAN | DONE intégrés ; preuves ci-dessous |
| UI-00 cadrage/Draft | DONE5643/PR14 |
| UI-1 fondations/parcours compte | IN_PROGRESS livraison/ciblés acquis, revue/CI nouveauSHA TODO |
| UI-2 saison/export/opérations sensibles | TODO après gate UI-1 |
| ACC-UI FINAL/lot7 local | TODO acceptation complète/fusion/mainCI |
| Lot8/candidatV1/activation | TODO dépendances/owner gates |

## Correction UI1-F1 cycle1

CI baseline8f3 **43623571912 development SUCCESS288backend167,17s/85frontend**, source exacte avant/après. Tester ciblé REQUEST CHANGES F1seul (copie202 promesse d’envoi malgré providerfail), rapport initial `.local-tools/tester-report-ui1-initial-8f3.md` conservé/publié ; SOURCE RELEASED. Developer seul writer, UI2planvalidé mais non attribué.

Seule constante produit changée vers texte exact propriétaire « Demande prise en compte. Vérifiez votre boîte de réception et vos courriers indésirables ; si un message vous parvient, suivez ses instructions. » Identique connu/inconnu/limité/providerfail.13testsclientPASS1,82s ; lint/build8,16s PASS ; browser ciblé2PASS16,04s (2deselected) sur_test, providerquota réellement déclenché1fois/cooldown/unknown/mise enpage390. Captures dialog-desktop/account-mobile vues, runtimes fermés. Premier run1PASS/1FAIL26,51s =fixtureadresse commune/cooldown conservé, corrigé par adresse synthétique par port, pas assouplissement produit. Ruff82/diff PASS.

Diff nul autresproduits/backend/migrations/pins/CI/dialog/CSS ; preuves104backend/18frontend/App9/flows/sondes indépendantes réutilisées après diff, pas verdictcopié, pas replay104/full881. Prochaine action : commit/push test+copie+docs, annoncerexactSHA et STOP pour revue ciblée UI1 complète/CIdevelopmentnouvelle. UI-2/mergegateintegrated restent àfaire.

## UI-1 livré et preuves

Bootstrap avantReact/scrub/preuveRAM enveloppe effaçable commune main/props (fermeture/succès/invalidité définitive), pas POST au montage/StrictMode ni token stockage/JSON/URLfinal/log. Dialog FR login/signup/renvoi/oubli/confirmation/reset ; Unicodeexact15–128points/512UTF8, emailASCII expliqué,202 uniforme et pas autologin. Contrôleur générations/abort/identité, login401 conserveA, late401 ignoréeaprèsB, resetB gardeA, feedback ancien nettoyé sur switch ; carte publique montée/conservée.

Préflight corrigé **CSRF→GETme portant CEproof→op mêmeproof**, pas coalescence avec mepassif. Headeroptionnel GETme/liste/ICS vérifié avantSQL ; vide/invalide403, sansheadercompatible, Origin absent GET accepté ; cookie seulbearer. Repro B→A→B1FAIL5,90s avant correction conservée. Headers HTML XFO/CSPframe-ancestors/no-referrer ciblés, OPS02Resendchoisi/nonvérifié aligné sans rapport historique modifié.

Preuves acquises :87PG/HTTP PASS40,02s (11readguard+29C1+47C0),18frontendisolés(13client+5dialog), App9 PASS12,02s initial ;17tests sélectionCI PASS0,10s ; browser Reactcompilé→Flask→PG2PASS26,09s desktop/mobile390. Desktop supplémentaire mois/filtre/recherche/détail noninitiaux1PASS31,27s (ui1-browser-context-fixed.xml), setup détails/caméra corrigé sans produit changé. Ruff82/lintfrontend/build3,50s/Node26contrats/diff PASS ; YAML existant js-yaml et4blocsBash syntaxe PASS. Captures dialog-desktop/reset-form-mobile/account-reset synthétiques vues, URLscrub ; provider Development RAM seulement. Pas full862local.

Focus : premierbrowser1PASS/1FAIL après changementidentitéremontantinput ; diagnostic simple1PASS timingvariable, puis barrièreinitialenondéclenchée1timeout. Maintenant meB retenu puis libéré sur inputA, focus recentré uniquement horsdialog,2PASS. Vitestgroupé2timeoutsrunner sans tests puisfichiersisolésverts, configinchangée. Erreurcallbacklocale captée4FAIL/lint puis corrigée5PASS. Rapports/JUnit ignorés conservés ; ne pas relabeller incidents ou cache enPASS.

## Politique CI propriétaire14nov

Draft sansci:full : job APIdevelopment, touslint/format/pip/contrats/frontend/build et backendciblé conservateur. Inconnu runtime/deps/migration/conftest=>fallbackfull, docs-only backendabsent explicitement. NonDraft/ci:full/main : job APIintegrated complet, seul nom accepté gatefusion. Unjob YAML IDintegrated avecnomdynamique, guardssourceavant/après/contentsread/persistcredentialsfalse/artefactsPNGwhitelist+JUnit1jour conservés. Rootposeci:full auheadfinal, vérifieintegratedsuccess exact puismainCIcomplète. Tests sélection17PASS ; vraieCI nouvelleàexercer. AGENTS/workflow alignés, rapports courts commandes/comptes/échecs/risques, pas skipci.

## Intégration acquise, pas à rejouer

[PR13](https://github.com/TheoxProject/RaceAtlas/pull/13) confirmée merged, head revu **679ec3e0dd53669d445a254f2b840c503a087bbb**, merge **b55f4c66e579046c09ee5cd8745fbeed4f566848**, arbre identique **dbda4b2fc2a1a7e75939e4cec74b29f8531c78c3** (fetch/diff vérifiés). Tester APPROVE complet A+B : 27 PASS courants6,27s + preuves produit113PASS/16sondes réutilisées après diff nul. CI PR43576022192 SUCCESS853backend238,36s/67frontend ; main43576573783 SUCCESS853backend156,11s/67frontend, gardes source avant/après. [Intégration durable](../lot-7/planning-integration.md). PLAN-F1 initialaa077 113PASS/1FAIL Windows CP1252 corrigé test-only, jamais relabellisé PASS. Rapports complets publiés PR13, canonical ignoré .local-tools/tester-report-planning.md.

[PR12](https://github.com/TheoxProject/RaceAtlas/pull/12) backend auth intégré87d7, head da5743, APPROVE complet239PASS, CI791/67 ; [preuve](../lot-7/auth-integration.md). Cookies opaques, email/hashonly/confirmation24h/reset30m, CSRF/Origin/admission/dispatcher borné déjà livrés. Defaults fermés, Development local/tests. Ne pas confondre backend terminé et lot7 complet.

## Environnement et interdictions de reprise aveugle

Python3.12.14 : C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe. Venv sans pip module ; runtimePython -m pip --python si besoin prouvé, pas réinstallation. Node24.22.1/pnpm10.20.0/node_modules et browsers existants (pas pnpm11). Playwright DateProxy seulement pour date fixe, pas page.clock.set_fixed_time qui casse RAF/Summit.

PG17.11 loopback127.0.0.1:55434, cluster .local-tools/pgdata-lot2-native, user raceatlas_local, dernierPID38028 ; vérifier statut avant réutilisation, jamais initdb/reseed/killglobal. DeveloperDB raceatlas_lot2_test, TesterDB raceatlas_lot2_review, preview raceatlas_map_demo préservée ; RACEATLAS_DISPOSABLE_DB=1. Les DB test/review sont à **a74d915e3c02**, ne pas utiliser un ancien checkout contre ce schéma. Aucun test/serveur/browser conservé après acceptation PLAN ; processus Node externes non revendiqués intacts. Fermer runtime/workers avant dispose Engine. Aucun autre writer actif attribué.

Copie personnelle main2e03cd8 et autres worktrees intacts. Branches historiques conservées, pas reset/clean/forcepush. .local-tools ignoré jamais gitaddglobal. Git/CI priment les notes ; source figée pendant revue, changements suivis imposent nouveau verdict/CI.

## Limites externes

Resend Free retenu ; club déclare posséder ucthonon.fr/Webador, raceatlas.ucthonon.fr email seulement, futur From RaceAtlas <notifications@raceatlas.ucthonon.fr> non vérifié. APP_BASE_URL Render réelle inconnue. Aucun compte/service/DNS/email réel/achat/remoteDB/déploiement/collecte autorisé. Premier déploiement privé après lot8/candidatV1 et autorisation distincte. Droits FFC/terrain, délivrabilité, capacité Free/physicalGPU restent à qualifier ; aucune activation automatisée. Owner silence jamais approbation. Quotas non mesurables, pas de promesse de reprise automatique.


Pas de test/serveur/browser retenu au gel ; fermer runtimes avant Engines, PG38028 conservé. Reprise explicite après quota a conservé le même WIP/agent ; anciennecommande rejetée n'avait rien exécuté. Node externes non revendiqués laissés intacts. Pas réexécution87/18/2 pour statut documentaire, pas UI-2 ni activation externe.
