# PLAN — API privée et ICS intégrés

[PR13](https://github.com/TheoxProject/RaceAtlas/pull/13) fusionnée le 14 novembre 2026 après acceptation indépendante complète PLAN-A+B.

| Preuve | Résultat |
|---|---|
| Head final revu | `679ec3e0dd53669d445a254f2b840c503a087bbb` |
| Base | `87d7dd53efcdb144c38e2d3ef1f83c89e63654fc` |
| Merge/main confirmé | `b55f4c66e579046c09ee5cd8745fbeed4f566848` |
| Arbre identique revu/fusionné | `dbda4b2fc2a1a7e75939e4cec74b29f8531c78c3` |
| Tester final | APPROVE complet ; 27 PASS courants en 6,27s, preuves produit inchangées 113 PASS et 16 sondes indépendantes réutilisées après diff nul des chemins produit |
| CI PR | [43576022192](https://github.com/TheoxProject/RaceAtlas/actions/runs/43576022192), SUCCESS, 853 backend en 238,36s et 67 frontend ; gardes SHA avant/après |
| CI main | [43576573783](https://github.com/TheoxProject/RaceAtlas/actions/runs/43576573783), SUCCESS, 853 backend en 156,11s et 67 frontend ; gardes merge avant/après |

GitHub a confirmé la fusion ; fetch et diff ont confirmé l'identité des arbres. Le rapport indépendant intégral est en description PR et [commentaire final](https://github.com/TheoxProject/RaceAtlas/pull/13#issuecomment-6874589419).

Livré : CRUD privé par scope, snapshots bornés, export statique des courses planned+registered, UID stable et ledger personnel batch avec SEQUENCE/DTSTAMP. Migration `a74d915e3c02`, runtime ICS stdlib ; parseur indépendant réservé aux tests. Source et favoris inchangés par export, erreurs/caps atomiques, isolation et révocation exercées via Flask/PostgreSQL. Voir [mission](planning-mission.md) et [handoff ICS](planning-ics-handoff.md).

Historique conservé : candidat `aa07746` REQUEST CHANGES, 113 PASS/1 FAIL sur le décodage stdin du processus de test Windows CP1252, malgré CI Linux verte. PLAN-F1 a explicitement décodé les bytes UTF-8 et vérifié enfants CP1252/UTF-8 ; aucun changement produit. Le nouveau SHA a reçu sa propre CI et son verdict complet. Aucune preuve échouée n'est relabellisée PASS.

**Planning backend terminé ; lot 7 encore incomplet.** L'interface comptes/sauvegardes/export et son acceptation intégrée restent requises. Domaine et expéditeur futurs non vérifiés, aucun email réel/DNS/service/déploiement/DB distante/collecte autorisé par cette fusion. Les autorisations externes restent distinctes.
