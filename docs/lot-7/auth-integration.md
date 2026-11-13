# ACC-02 — backend comptes intégré

[PR12](https://github.com/TheoxProject/RaceAtlas/pull/12) fusionnée13nov2026 après acceptation indépendante complète A+B1+B2+C0+C1+C2.

| Preuve | Résultat |
|---|---|
|Head final revu|`da5743c500603a11366080e97cd2e76db7cbcb33`|
|Base avant fusion|`5e2c84a99f7795da9cc2e14118549873bf4a42be`|
|Merge/main confirmé|`87d7dd53efcdb144c38e2d3ef1f83c89e63654fc`|
|Arbre identique revu/fusionné|`dafa5967ca7f9726729e9a94cefae5f3a102deba`|
|Tester final|APPROVE complet,239PASS locaux (22545,70s+14sondes6,98s), Ruff70/contrats26/pipcheck/diffPASS ; rapport intégral en descriptionPR|
|CI PR|[43514658079](https://github.com/TheoxProject/RaceAtlas/actions/runs/43514658079) SUCCESS791backend161,56s/67frontend, source exacte avant/après|
|CI main|[43515934267](https://github.com/TheoxProject/RaceAtlas/actions/runs/43515934267) SUCCESS791backend138,79s/67frontend, merge exact avant/après|

GitHub a confirmé merged=true ; fetch origin/main et diff complet confirment l'identité des arbres. Sous PowerShell citer les révisions `^{tree}`. Copie personnelle main et autres worktrees intacts. Aucun verdict copié à un nouveau SHA : réutilisation des preuves immuables explicitée par Tester.

Livré : inscription non vérifiée, confirmation24h, renvoi, reset30min/usageunique/révocation, cookies opaques/CSRF/Origin/admission, réauth et suppression. EmailService central Resend/Development, dispatcher borné après commit/close, probe encore valide et saturation/arrêt incomplet. Vrais appels WSGIFlask→PG et SDK officiel→fakewire avec sockets/DNS interdits. Hash seuls DB,1KDF registration vérifié, aucune garantie de temps constant ou capacité Free issue des profils locaux.

Historique : B2-F1 transaction externe, C0-F1 URL masquée et C0-F2 bodycache corrigés ; CI35f710PASS/7FAIL reste un échec historique. C1 ne pose jamais Set-Cookie sur401 passive. [Handoff final](auth-http-email-handoff.md), missions et anciens handoffs conservent interfaces/preuves.

**ACC-02 backend terminé, lot7 incomplet** : planningAPI/ICS et UI React restent requis. Domaine futur `raceatlas.ucthonon.fr`, From `RaceAtlas <notifications@raceatlas.ucthonon.fr>` non vérifiés, URL réelle Render inconnue. Aucun compte/service externe, clé réelle, DNS, email réel, achat, remoteDB, déploiement ou collecte. Defaults fermés/Development local ; premier déploiement privé après lot8/candidatV1 sous autorisation distincte. Droits/délivrabilité/capacité physique restent à qualifier.
