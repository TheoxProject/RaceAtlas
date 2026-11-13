# PLAN-01 — API privée et export ICS statique

Base vérifiée **87d7dd53efcdb144c38e2d3ef1f83c89e63654fc**, après [auth intégré](auth-integration.md) et mainCI791/67 verte. Branche `feature/private-planning`, checkout isolé add4 réutilisé propre après intégration, sans writer concurrent ; copie personnelle main préservée. Nouvelle Draft PR. Root possède cadrage/checkpoint jusqu'à attribution, puis Developer seul writer et Tester read-only au gel.

Produit acquis : sauvegardes par **entry_scope**, statuts interested/planned/registered/completed, Inscrit déclaratif nonFFC, export personnel **statique planned+registered**. Pas feed, email course, options supplémentaires d'export ou troisième page de découverte. UI ensuite, sans reset carte/calendrier/caméra/filtres. Les plans ignorés sont préparatoires ; cette mission fige les choix techniques.

## Jalons et fichiers

PLAN-00 : cadrage/Draft/mainCI ; PLAN-A : API CRUD/liste+snapshot, revue ciblée ; PLAN-B : codec ICS/cache/endpoint, puis acceptation COMPLETE feature au SHA final, CI/gates/merge/mainCI. Ne pas confondre jalon et lot7 terminé.

Ownership Developer : nouveaux modules planning_http/snapshot/ics/calendar_store et tests, ajouts privés models et migration après **f61d338ab204**, raccord minimal factory/auth et adaptateur HTTP privé commun si nécessaire, contrat planning additif/docs/checkpoint. Réutiliser ACC01CRUD/auth sans refonte. Petite extension action admission planning et extraction scope serializer compatibles autorisées ; cleanup tests utile seulement. Exclusions frontend/sync/FFC/filtres/serve/ops/CI/données réelles/provider. Runtime dependencies inchangées ; parseur indépendant **icalendar7.3.0 dev-only** autorisé avec transitifs réellement résolus/épinglés et provenance BSD2 (PyPI officiel vérifié13nov2026, Python>=3.10). Pas de Django ou service nouveau.

## Routes et droits

- GET `/api/v1/me/saved-entries` : toutes sauvegardes propres, DTO scoped, tri created_at/id, aucun filtre public implicite.
- PUT `/api/v1/me/saved-entries/by-scope/<scope_id>` `{status}` : upsert ACC01, course dérivée du scope.
- PATCH `/api/v1/me/saved-entries/<entry_id>` `{status}` et DELETE même route `{}` : ownership avant enum comme ACC01, étranger/inexistant404 générique ; forme/types restent validés avant métier.
- GET/HEAD `/api/v1/me/calendar.ics` : toute sélection planned+registered, filename fixe `raceatlas-planning.ics`, text/calendar UTF8, attachment/no-store. Aucun bearerURL/publictoken.

Pas actor/user_id/filter/range/statuses supplémentaires. Statuts4, no-op ID/revision/timestamps stables, vrai changement+1. Acteur cookieC validé et Account persistant dans LA MÊME Session que planning. Origin/CSRF/JSON8KiB/admission C0/C1 sur mutations, metadata/Origin si fourni sur GET ; pas CORS permissif. Basic preview permis sans droits compte ;401 passive sans Set-Cookie. Commit/fermeture avant réponse, aucun ORM/cursor tardif.

## Snapshot et limites

Auth reste **READ COMMITTED**, Accountlock/relectures fraîches ; pas RR global pouvant relire un credential révoqué pendant attente. Après auth, **un SELECT du graphe** SavedEntry/Scope ciblé/Race/commune/types/source/règles/categories porte le snapshot cohérent. EntryScope n'a pas de relationship race : joindre Race explicitement. `raiseload`/DTOs et compteurSQL prouvent zéro lazy/selectin au rendu. Ne pas utiliser race_document parcourant toutes listes. Source peut changer entre auth et SELECT, pas produire un graphe mélangeant snapshots.

Défauts techniques : **1000 sauvegardes/account**, **1000 événements/export**, **2MiB réponse personnelle/ICS**, **16KiB UTF8/champtexte**, **10000 paires cache/account**. Sous Accountlock refuser créations dépassant cap, upsert existant/retrait possibles. Détection cap+1 préserve collections. Erreur explicite contractuelle, pas liste/calendrier valide tronqué ; rollback complet du cache si limite/rendu échoue. Tests peuvent abaisser limites internes, pas paramètres HTTP. Timeouts privés existants, pools/catalogue inchangés ; aucune capacité Free revendiquée.

## ICS et identité

Un VEVENT par scope, même Race commune. SUMMARY race+raw_label ; DESCRIPTION statut personnel/règles/restrictions/incertitudes, sans fusionner listes/éligibilité. Registered jamais assimilé à FFC CONFIRMED ; missing/to_verify jamais annulé. Source réellement cancelled peut émettre STATUS:CANCELLED. Pas METHOD/ATTENDEE/ORGANIZER/VALARM/ATTACH/URL/GEO ; provenance en texte sûr. LOCATION commune connue seulement avec caveat centre/départ inconnu, nonlocalisé explicite sans coordonnées inventées.

All-day VALUE=DATE : DTSTART=start_date, DTEND=end_date inclusive+1jour civil ; pas heure/TZID supposés. VCALENDAR2.0/PRODID, UTF8/CRLF, TEXTescape et folding≤75**octets** continuation comprise, codepoints intacts. Tri déterministe dates/scopeID, ordre règles stable. HTML/newlines ne peuvent injecter propriété/composant ; date non représentable et overflow refusés, pas wrap. Codec pur DTO, parseur indépendant en tests.

Namespace UID fixe une fois : `uuid5(NAMESPACE_URL, 'https://github.com/TheoxProject/RaceAtlas/private-calendar/v1')`, puis UUIDv5 de JSONcompact UTF8 non normalisé `["v1",accountOpaqueID,scopeOpaqueID]`. Aucun host/domaine/email/clé de config ou SavedEntry.id dans UID. UUID opaque seul stable rename/report/reorder/restart/host/unsave-readd, distinct user/scope. Golden indépendant ; pseudonyme, jamais autorisation.

## Cache de métadonnées retenu

Table privée **PersonalCalendarEventStore**, unique account+scope, FK AccountCASCADE et ScopeCASCADE ; fingerprintSHA256, stampUTCDB, SEQUENCE nonnégative≤2147483647. Pas FK SavedEntry, payload/email/token/historique humain ou nouvelle UI. Fingerprint du VEVENT métier réellement émis ET SavedEntry.id comme incarnation ; exclure DTSTAMP/SEQUENCE/requestclock/freshness/source.checked_at. Identique garde stamp/seq, contenu/incarnation changé +1 et dateDB. DTSTAMP est la matérialisation réelle de cette représentation, pas une date inventée d'application source ; LAST-MODIFIED omis. Même seconde possible pour deux séquences, overflow refuse.

Créer seulement à l'export, conserver pendantviecompte même après unsave, cap10000 transparent sans TTL/LRU faisant régresser sous mêmeUID. Compte ou scope définitivement purgé supprime ces métadonnées pseudonymes ; ScopeCASCADE n'affaiblit pas SavedEntryFKRESTRICT. IDs retirés définitivement non recyclés par le métier actuel, sync refuse retrait/split sans preuve. A→B→A jamais exporté B peut rester identique : pas historique des états non matérialisés. GET/HEAD peut actualiser ce cache et idle auth, JAMAIS favoris/statuts/source/publicepoch. Fichier statique déjà importé ne se retire/synchronise pas automatiquement et comportement universel client non promis.

## Acceptation et workflow

Vrai Flask→PG, deux users/devices, cookies/Origin/CSRF/revoke/unverified/IDOR/IDs malformés ; upsert/no-op/concurrence, >200 sans pagination publique cachée, scopes distincts, refus caps/retrait. Source synthétique rename/report/reorder/replay/ambiguïté/absence ne transfère jamais un favori ; snapshot durant vraie mutation autreconnexion, zéro lazySQL, locks relâchés avant Response. Preuves auth réutilisées explicitement après diff, pas verdict copié.

ICS parser indépendant : vide/201+/multijour/Dec31-Jan2/leap/DST/processTZ/unlocated/cancel/to_verify, accents/emoji/CRLF/backslash/virgule/semicolon/injection75octets, UIDgolden/stabilité/readd/twoUsers, bytes stables/fraîcheur seule, contenu réel et même-seconde/sequence/rollback/cap/overflow. Auth accountdelete purge cache propre/autrui/epoch préservés. Migration upgrade/check/base/upgrade/check seulement `_test`/`_review` opt-in.

Checkpoint/handoff/commits/push cohérents et CI après chaque push ; STOP au gel important et final, Tester SHA exact/cycles ciblés≤3. MainCI avant suite ; pas fullbackend/browser local inchangé répété. Aucun DNS/email réel/clé/dépense/service/remoteDB/deploy/FFCcollecte/tagV1 autorisé. Domaine/expéditeur/UI et acceptation lot7 restent à qualifier ensuite.
