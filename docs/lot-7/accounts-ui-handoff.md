# PR14 — CI-F3 cycle3, DIAGNOSTIC à publier puis figer

Branche feature/accounts-ui/DraftPR14/baseb55f4c66e579046c09ee5cd8745fbeed4f566848 ; head avant commit4ec711c7132015ebfdbedde22f30f345c365cba0. **Full43742604527/job132898842854 FAIL890PASS/1FAIL404,09s** : saisonJanvierphasepublic-selection/events[]/strong_nodes0/elapsed16858ms, puis screenshot5s masque initial. events[] n'établissait pas zéro événement : collecte ancienne après sortie3contextes seulement. Anciennes full891/118 et APPROVE sont historiques, jamais verdict du prochainSHA. AuthSummitPASS n'est pas preuve de résolution causale.

## Modification strictement diagnostique

Un seul fichier test_accounts_ui_e2e.py : callbacks request/response/requestfinished/requestfailed installés avant select, filtrés aux3requêtes publiques du mois/date/query/limit attendus ; anneau48événements/12requêtes max, petits IDs locaux, kind/phase/status/tempshôte relatif uniquement. Callbacks sans corps/header/URL/token/PII ni appelrenderer/JSON. Validation métier publique/versions et budgets15s inchangés. Callbacks retirés enfin.

Observateurcaméra existant installé danssaison AVANTSummit, snapshotinitial reçu ; cachehôte avant sélection et au failure, aucun count/evaluate/screenshot additionnel requis pour produire l'erreur. Captureouter5s protégée puis bare raise pour conserver exceptioninitiale. Phase/typeerreur/cache figés avant capture. HorlogeDateProxy/timersnatifs, caméra10s/pitch60°/DEM>100/acteurs/scopes/règles/horsfiltres strictement conservés.

## Preuve et limite

UNIQUE run Developer `_test` offline : `pytest tests/backend/test_accounts_ui_e2e.py -k season_scope_actions_map_two_accounts_outside_public_filters -q --tb=short --junitxml=.local-tools/pr14-ci-f3-diagnostic.xml -rP` : **1PASS64,57s**. Janvier requêtes3438ms, races/map finis3860ms, témoinfini7266ms, validation10156ms/UI10203ms ; Novembre races/mapfinis7875ms, témoin7922ms, validation11562ms/UI11594ms. Ce sont observations hôte, pas chronométrage réseau physique ni SLA. Snapshotinitial/assertionsstrictes et callbacks actifs pendant ce run.

**Métadonnées seules ajoutées après import du run : numéros locaux request_id, select-start/return et copie cacheavantselection. Chaînage failure public conservé via from error, sur demande Coordinator, après ce run également.** Pas de nouveau wait/asserteffet ; preuve de flow réutilisée explicitement, ces métadonnées attendent vérification Reader/CI exacte. Aucun second run local, aucun retry jusqu'auvert. Ruff check/format82 et rangediffcheckbase..HEAD à confirmer aprèscommit. Produit/frontend/backend/CI/contrats/pins/migrations strictement identiques4ec ; aucun changement map_support/test_e2e partagé, pasbuild/install/fullbackendlocal.

**Pas de cause unique établie ni de correctif produit déclaré.** L'instrumentation peut modifier charge/ordonnancement SwiftShader ; vieuxcache/absenceframes peuvent être idle/JS/GPU/protocole, pas preuve isolée de gel. Les traces futures différencieront émission/réponse/fin/témoin/validation/présentation, et moteur/dataset/âgecache/stops/contexte sans dépendre d'un renderer déjàbloqué.

Prochaine action : push/GEL exact, revue finalecomplète renouvelée et CI intégrée au SHA. **Si nouveléchec CI nonrésolu, cycle3 STOP/rapportblocage et options ; aucun quatrième patch/rerun jusqu'auvert.** Aucune approbation par épuisement ni fusion/lot8 avant gate. Commande63168terminée, serveurs/runtimes/browsers fermés, PG38028conservé/_reviewintact ; aucun emailréel/DNS/remoteDB/deploy/collecte. Les précédents échecs CI-F1/F2 demeurent en Git/rapports.
