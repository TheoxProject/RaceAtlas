# N2A-F1 — candidat corrigé cycle1, GEL après publication

**17 novembre 2026, 08:20 UTC.** Checkout add4/feature/notifications-interface / [DraftPR16](https://github.com/TheoxProject/RaceAtlas/pull/16), base014bda3480d0f8c0233f8e6f68d0ae82886b83db. HEAD/origin avant publication07f22acc4f755d1911fd4def001ca9220947777d. Verdict07f REQUEST CHANGES P2 curseur >1024 pour IDs valides ; rapport archivé ignoré initial-07f. CI44042648284 development SUCCESS998backend288,93s/118front historique seulement, aucun verdict du nouveauSHA.

Correction : corps v2 version+dateUTC+deuxIDs UTF8 séparés NUL (déjà interdit dans IDs). Brut≤543octets, base64url≤724 +point/HMAC43 => **768≤1024** pour TOUS IDs1..64 valides, même contrôles/4octets. Pas troncature/refus artificiel/hausse de borne. HMAC domaine/acteur inchangé, v1 JSON encore lu si valide≤1024 ; validation version/UTF8/séparateurs/date/IDs avant SQL. Extension MINIMALE autorisée Coordinateur : planning.schema $defs.Scope.properties.id→$ref #/$defs/Id, ancien patternASCII contradictoire ; public/catalogue/DB/runtime planning inchangés.

## Résultats réels

- Groupe correction `test_notifications_cursor.py test_notifications_api.py test_notifications_validation.py` : **14PASS/3FAIL9,515s**, ops-n2a-f1-cursor.xml. Deux FAIL de schéma privé contradictoire ; un FAIL503 fixture qui gardait Account lock après service avant HTTP autreSession. Corrigés explicitement, aucune passe relabellisée.
- `test_notifications_cursor.py -k legacy_json` : **1PASS3,52s**, ops-n2a-f1-legacy.xml (commit de lecture libère lock, pas hausse timeout).
- `test_notifications_cursor.py -k both_maximum` : **4PASS5,15s**, ops-n2a-f1-maxima.xml (2 bornes pures +2 roundtrips maxima service/HTTP page2/schema/count/scope ET GETplanning privé).
- `test_private_planning.py -k private_planning_contract_matches` : **1PASS3,25s**, ops-n2a-f1-planning-contract.xml.
- Ruff lint/format100 et26contrats publics PASS ; range base..HEAD à confirmer après commit. Codec négatifs/signature/acteur dans14verts conservés, pas rerun49 reviewer/fullN1.

Developer seul writer, Root PR/CI, Tester STOP/_review réservée. PG9780/55434 existant vérifié natif ; tests `_test` b806 exclusivement. Toutes commandes terminées exit0 ou échec initial documenté, aucune session/test/worker pending, listeners/runtimes/engines fermés. [Handoff](../lot-8/notifications-handoff.md) commandes/borne/couture exactes.

**Prochain geste sûr : commit/push cohérent, SHA exact puis STOP pour renouvellement ciblé N2A et CI courante.** N2B UI non attribué avant APPROVE. Snapshot/ACK/projection N1A/HTTP/auth/source/ICS/frontend/CI/deps inchangés ; seul codec et champ privé de schéma autorisé changés. Pagination live, pas rétention/TTL produit. Aucun email/live/DNS/service/remoteDB/deploy/achat/tag final.