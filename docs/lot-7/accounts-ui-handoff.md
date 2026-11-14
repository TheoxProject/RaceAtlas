# UI-1 — Handoff ciblé PR14

## UI1-F1 cycle1 (14nov)

Baseline8f3aaf88cceb9f33cfda28d56a4413f8c86cb8f4 : CI43623571912 development288backend167,17s/85frontend verte, mais Tester REQUEST CHANGES ciblé (rapport initial `.local-tools/tester-report-ui1-initial-8f3.md`, publié PR14). Unique P2 : copie202 promettait conditionnellement un envoi malgré refus quota provider. SOURCE RELEASED, pas APPROVE du nouveauSHA.

Seul changement produit : ACCEPTED devient exactement « Demande prise en compte. Vérifiez votre boîte de réception et vos courriers indésirables ; si un message vous parvient, suivez ses instructions. » Même texte connu/inconnu/limité/providerfail, aucun état transport exposé. Contrôleur horsconstante, dialog/CSS/bootstrap/readguards/backend/migrations/deps/CI inchangés par diff.

Ciblés exécutés : privateAccount13PASS1,82s ; lintfrontend/build8,16s PASS ; navigateur Reactcompilé→Flask→PG **2PASS16,04s** (2anciensflows désélectionnés), `.local-tools/ui1-f1-copy-browser-final.xml`. Provider simulé refuse réellement1tentative, drain confirmé ; cooldown puis adresse inconnue donnent exactement la même copie. Desktop/mobile390 et scroll/captures vus : dialog-desktop.png/account-mobile.png. Premier run1PASS/1FAIL26,51s conservé : mêmeadresse entre paramètres maintenait correctement le cooldown, donc aucune tentative mobile ; adresses synthétiques isolées par port de fixture, aucune limite désactivée/timeout modifié. Ruff82/diff PASS.

Réutilisation explicite après diff nul des autres chemins :104backend/18frontend/App9 et parcours métier/4sondes indépendantes passés dans revue initiale (panne renderer initiale et reprise desktop conservées). Pas de replay104/full881 ni nouveau verdict copié. NouveauSHA communiqué après push puis STOP pour renouvellement revue UI-1 complète et CIdevelopment courante. UI-2 toujours TODO ; aucun emailréel/service/DNS/remoteDB.

## Livraison UI-1 initiale et preuves conservées


Branche `feature/accounts-ui`, [Draft PR14](https://github.com/TheoxProject/RaceAtlas/pull/14), base **b55f4c66e579046c09ee5cd8745fbeed4f566848**. Le SHA exact du candidat est communiqué après push, puis STOP pour revue ciblée. UI-2/Ma Saison/scopes/export/opérations sensibles non commencés ; UI-1 ne clôt pas lot7.

## Livré

- Bootstrap avant createRoot : fragments stricts capturés en RAM/scrub sans POST au montage. Enveloppe partagée main/props effaçable à fermeture/succès/invalidité définitive ; pas promesse de zeroisation JS. StrictMode ne consomme pas une seconde fois la preuve.
- Compte en dialog natif FR : inscription/connexion/renvoi/oubli/confirmation explicite/reset. Unicode15–128points/512UTF8 sans trim/maxLengthUTF16, login legacy inchangé, email ASCII expliqué pour nouvelles demandes.202 uniforme sans promesse d'envoi. Confirmation/reset ne connectent pas ; resetB conserveA.
- Contrôleur privé séparé : même origine/routes constantes/cookie-only, génération+abort même si abort ignoré, pas retry automatique ni clear global sur login401. Réponse passive ancienne ignorée aprèsB ; feedback ancien effacé si identité change. Focus recentré seulement si un remount a sorti le focus du dialog.
- Préflight **CSRF → GETme portant CEproof → opération mêmeproof**. Vérification serveur optionnelle GETme/liste/ICS si header présent,403 vide/invalide/autre cookie AVANT SQL privé ; sansheader compatible et Origin absent lecture accepté. Le conseil initial GETme non lié est invalidé par la trace B→A→B, reproduite puis corrigée. Aucun acteur client/nouveau bearer.
- Shell HTML seulement : XFO DENY, CSP frame-ancestors 'none', Referrer-Policy no-referrer. Carte/Summit/période/filtres/détails restent montés, aucun fetch public dû au compte. OPS02 aligné Resend choisi/non vérifié, pas rapport historique prédeploy réécrit.
- CI propriétaire : job YAML unique, nom API **development** draft sansci:full (sélection stdlib conservatrice) ou **integrated** main/nonDraft/ci:full (suite complète). Gardes/permissions/artifacts1jour conservés. Development vert ne vaut jamais fusion. [Guide](../readiness/ci-validation.md).

## Preuves

Commandes/cache : [local](accounts-ui-local-development.md).87 PG/HTTP PASS40,02s (11readguard+29C1+47C0),18 frontend ciblés (13client+5dialog), App9PASS avant derniers handlers d'UI,17 tests sélectionCI PASS0,10s ; Ruff82/lintfrontend/build3,50s/Node26contrats/diff PASS ; YAML parsé avec js-yaml existant et4 blocs Bash syntaxe PASS (pas nouvelle dépendance). Browser compilé→Flask→PG :2PASS26,09s, desktop+mobile390. Contraste desktop supplémentaire mois/filtre/recherche/détail noninitiaux :1PASS31,27s, `.local-tools/ui1-browser-context-fixed.xml` ; setup initial Summit intercepté par détails, corrigé en réglant caméra avant détails, sans source produit changée. Aucun full862 local rejoué. CI862/67 au6b91 est antérieure, pas validation du futur candidat UI.

Browser : DevelopmentEmailProvider lu RAM par fixture, zéro endpoint debug-mail ; preuve URL navigation neutralisée en cas d'erreur. Signup/renvoi202/confirmation explicite/login/wrong401/late401 ignorée aprèsB ; resetB/A et loginB explicite, clavier/focus/scroll et caméra zoom+Summit60/DEMréel>100. Réponse meB retenue puis libérée sur inputA pour exercer remount/focus/feedback. Captures synthétiques vues : `.local-tools/accounts-ui-screenshots/dialog-desktop.png`, `reset-form-mobile.png`, `account-reset.png`. `account-mobile.png` réservé échec ; PNGwhitelist réguliers/non symlinks seulement.

Incidents conservés : reproduction BAB1FAIL5,90s avant correctif ; browser initial1PASS/1FAIL focus, diagnostic timing1PASS puis barrière mal déclenchée1timeout, corrigée par événement explicite ; final2PASS. Vitest groupé n'avait démarré aucun worker (2timeouts), puis runs isolés verts sans changer config. Une erreur de callback local a été captée par4testsdialog/lint puis corrigée,5PASS. JUnit ignorés, pas assimilation pytestcache à résultat.

## Revue et limites

Tester : SHA gelé exact, revalider frontières/proofABA/fragmentpurge/générations et vrai browser, focus/accessibilité/mobile/découverte. CI réelle doit exercer nouveau mode et sélection ; avant fusion finale UI-2, Root exige integratedsuccess au mêmehead puis mainCI complète. Tous tests/serveurs/workers fermés ; PG local conservé, `_review` réservé. Aucun email réel/DNS/clé/Resend/service/remoteDB/achat/deploy/collecte ; délivrabilité réelle non validée. Prochain jalon UI-2 seulement après gate ciblé.
