# ACC-UI — handoff en cours

Branche feature/accounts-ui, [Draft PR14](https://github.com/TheoxProject/RaceAtlas/pull/14), base b55f4c66e579046c09ee5cd8745fbeed4f566848. UI-1 en développement, UI-2 non attribué. Aucun verdict UI présumé.

## Checkpoint backend initial

`auth/csrf.py` ajoute `verify_request(..., *, mutation=True)` avec défaut historique inchangé. GET saved-entries/GET-HEAD calendar.ics appellent modeFalse lorsque X-CSRF-Token est présent ; header vide/malformed n'active pas fallback. Sans header, ancien client GET inchangé ; Origin absent lecture permis, présent doit être canonique. Cookie reste seul bearer. Contrat planning documente ce header optionnel. Besoin nouveau de liaison à l'intention UI, pas faille historique revendiquée.

Shell HTML seulement : X-Frame-Options DENY, CSP frame-ancestors 'none', Referrer-Policy no-referrer ; pas default-src/ressources MapLibre bloquées. JSON public inchangé.

Commande native PG_test opt-in, même cluster38028/55434 : `python -m pytest tests/backend/test_account_read_context.py -q --tb=short --maxfail=2 --junitxml=.local-tools/ui1-read-context.xml` =>9 PASS24,72s. Fixtures upgrade/check/base/upgrade/check au schéma a74, aucun ancien checkout. CookieB avec proofA/même nonce refuse avant SQL, retourA ne change pas le refus ; droits/sansheader/GETHEAD/expiry/proof nonbearer/Origin mutations/headers shell exercés. Ruff lint/format79 et Node26 contrats publics PASS. Pas de full853 local, email réel, fournisseur réseau, UI/code navigateur acquis à ce checkpoint. Tests/browser arrêtés, runtimes fermés avant dispose.

CI cadrage43577679731 SUCCESS853/67 au5643 est preuve antérieure, pas CI de ce nouveau code. Root suit chaque push exact. Bootstrap/controller/dialog et preuves React compilé restant UI-1 ; Ma Saison/scopes/export/opérations sensibles sont UI-2 et attendront gate.
