# OPS-N2 — Changements récents dans Ma saison

Branche `feature/notifications-interface`, checkout isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, base main **014bda3480d0f8c0233f8e6f68d0ae82886b83db** après CI main43928375559 SUCCESS967/118. [Intégration N1](n1-integration.md), AGENTS/AGENT_WORKFLOW et contrats actuels font foi.

## Décisions et jalons

Propriétaire : section **Changements récents dans Ma saison**, compteur nouveautés, **Marquer comme lues** pour **TOUTES les notifications déjà disponibles, même non affichées**. Retrait d'une sauvegarde supprime SES messages ; autres scopes/comptes préservés, réajout avec baseline fraîche. Pas centre séparé, email course, troisième page de découverte ou source live. Les quatre statuts sont suivis, Inscrit reste déclaratif et admissibilité personnelle non évaluée.

- **N2A backend**, jalon attribué et implémenté, candidat à revue ciblée : services de lecture/acquittement, routes/contrats, tests PG/HTTP/snapshot. Gel/revue ciblée avant UI.
- **N2B UI (attribué, IN_PROGRESS)** : section/store/client dans Ma saison, compteur/lecture/pagination accessibles, vrais navigateurs ; mission détaillée après gate N2A.

Developer est seul writer après transfert explicite ; Root cadre/PR/gates et notes, Tester lit/teste le SHA figé sans édition. N2A : notifications.py ou petit module dédié, notifications_http.py, raccord factory/guards minimal, contrats notifications et tests/docs/checkpoint. Pas refonte auth/sync/planning/ICS, migration b806, frontend ou dépendance supplémentaire sans besoin démontré. API et UI seront acceptées COMPLÈTEMENT au SHA final avant integrated/fusion/mainCI ; N2A seul ne termine pas N2/lot8.

## N2A — service et snapshot

Relation éligible = SavedEntry COURANTE du compte serveur JOIN ScopeChange(sequence > baseline) JOIN RaceChange LEFT JOIN PersonalNotification par le triplet exact. Non matérialisée = non lue. Count et page au MÊME snapshot SELECT, jamais seulement COUNT(personal_notification), taille de page ou batch256. Count global non filtré par le curseur ; pas besoin de matérialiser pour rendre GET exact, pas de liste Python non bornée.

Ordre keyset total `(created_at,change_id,scope_id)` décroissant ; curseur opaque borné, validé/signé et lié à l'acteur, jamais bearer ni promesse de snapshot durable interrequêtes RC. Pagination vivante ; suppressions/réajouts reflétés, nouveaux événements récupérables en rafraîchissant la tête. DTO du scope EXACT avec faits minimaux/provenance/read_at ; raw labels/restrictions/incertitudes préservés, aucun scope frère, email/proof/session ou profil d'admissibilité inféré. Budget JSON privé existant, champs/taille bornés ; pas de troncature silencieuse.

ACK ALL : verrou Account puis UNE instruction INSERT…SELECT de toutes les éligibles actuellement visibles + ON CONFLICT UPDATE seulement read_at NULL, anciens read_at conservés. Le snapshot MVCC de CETTE instruction après lock est le cutoff, pas un timestamp client/MAXsequence global/UUID. Source committée APRÈS snapshot reste non lue même si created_at est antérieur ; AVANT snapshot incluse. Pas boucle LIMIT/batch256, drop ou watermark scalaire. Aucun Account lock côté sync ni scopeguard dans ACK. Commit/rollback caller-owned, délais bornés et échec atomique ; pas de retry d'intention ni faux succès.

## Routes et frontières

Proposition additive à finaliser techniquement : GET `/api/v1/me/notifications?limit=&cursor=` →200 `{items,unread_count,next_cursor,has_more}` ; POST `/api/v1/me/notifications/read-all` JSON{} →**204 exact après commit/close**. Défaut50/max100 pour la page, curseur/JSON/champs dans budgets privés. Décisions techniques documentées avant code, pas d'option produit inventée.

Réutiliser les coutures planning : cookie seul bearer, acteur exclusivement serveur, adresse vérifiée, Origin/CSRF obligatoires en mutation, lecture liée si X-CSRF-Token présent (vide/invalide refusé avant SQL privé), lecture native sans header compatible. No-store, aucune preuve/token en URL/body/stockage/log, aucune identité client faisant autorité. Validation pure des paramètres/tailles avant SQL selon admission existante ; 401 passive sans Set-Cookie, erreurs génériques/bornées, Session fermée avant Response. Pas de modification globale des permissions, de l'isolation auth ou des limites validées.

Frontend ultérieur : CSRF→GETme portant CE proof→op même proof, full lease/ticket/epoch après await/catch/finally ; ancien401 ne purge pas nouvelacteur. Échec réseau/commit inconnu ne devient pas succès/retry. Les mutations privées ne changent pas l'epoch public, ni les données d'autrui/ICS.

## Tests utiles N2A

Deux comptes/deux scopes/quatre statuts, lu/nonlu, baseline/replay/retrait/réajout/suppression compte et FK. Plus de1000 éligibles avec256 matérialisées/pending : page50 et count global exacts ; ACK tout et replay idempotent, read_at antérieur stable. Erreur/timeout avant commit : aucun acquittement partiel ni faux204. Contrastes d'acteur A→B/ABA, CSRF/Origin/header lecture optionnel et malformed/oversized avant SQL ; session fermée avant réponse.

Barrières réelles : source écrit avant ACK mais commit APRÈS le snapshot réel (timestamp antérieur) reste non lue ; commit AVANT snapshot inclus. Instrumenter le vrai point SQL, pas sleeps/horloge comme fausse preuve. Source ne prend aucun Account. Retrait/ACK sérialisés par compte, réajout baseline fraîche et aucun ancien candidat RAM rejoué. Vérifier absence de N+1, DTO borné, source/epoch et ICS d'autrui intacts. Contrats OpenAPI/schema et HTTP réel Flask→PG ; pas endpoints debug ou envoi réel.

## UI N2B prévue et suite

Section dans Ma saison, liste avec état lu, compteur exact, ACK toutes explicite, chargement/vide/erreur/refresh/pagination/clavier/focus/mobile390. Aucun reset caméra/période/filtres ni nouvelle page. Controller privé générations et réponses tardives, retrait scope nettoie SES messages ; changements source→section→ACK→nouveau changement encore non lu dans vrai React compilé→Flask→PG. Styles sport existants navy/orange, pas refonte.

Ciblés pendant développement et rapports courts ; CI integrated complète obligatoire au SHA final puis main. _test Developer/_review Tester b806, PG9780/55434 existant à vérifier, venv/Node/browsers réutilisés ; runtime.close avant Engines. Pas ancien checkout contre schéma nouveau, initdb/reseed aveugle, dump privé ou modification des autres worktrees.

Après N2 : erreurs/quotas simulés, sauvegarde/restauration sur NOUVELLE DB locale synthétique, matrice candidat V1. Aucun achat, DNS, email réel, service, DB distante, déploiement, collecte live ou tag final sans autorisation distincte.

## Interfaces N2A retenues avant code

`notifications_api.py` : validation pure limit1..100/défaut50 et curseur≤1024octets, lecture virtuelle par SELECT CTE éligible légère/count/page puis graphes joints bornés (raiseload/populate_existing comme planning), ACK INSERTSELECT/ONCONFLICT sans retour massif. Item : change_id/scope_id/kind/created_at/read_at/delta/provenance et entry DTO planning du SEUL scope. Count non filtré par curseur, aucune projection obligatoire. Signature HMAC-SHA256 liée acteur et domaine `notifications-cursor:v1` sur AUTH_CSRF_KEY existante ; pas bearer, nouveau secret ou snapshot durable. Budgets PlanningLimits2MiB/texte16KiB réutilisés.

`notifications_http.py` : boundary/Origin/CSRF/AccountFlowSession/resolve_session comme planning, admission action notifications (ajout whitelist minimal), commit+close avant Response. Raccord minimal auth.http, aucun changement sémantique auth/planning/ICS. N2A seul ne livre pas l’UI.
## Correction N2A-F1 — représentation interne v2 (17 novembre)

IDs contractuels1..64codepoints UTF8 valides, sauf NUL déjà interdit. Corps de curseur v2 = b'2\0' + date UTC canonique ASCII + NUL + changeID UTF8 + NUL + scopeID UTF8. Date≤27octets, IDs≤256chacun : brut≤543octets, base64url≤724 ; avec point+HMAC43, **≤768**, donc borne1024 inchangée. Signature domaine/acteur inchangée ; v1 JSON encore lu si valide et≤1024. Aucun refus artificiel des caractères de contrôle/emoji, troncature ou changement d’API. Version/UTF8/séparateurs/date/IDs stricts avant SQL, signature liée acteur avant source privée. Roundtrips maxima service et HTTP, schéma/page2/compteur/scopes requis.
## Attribution N2B (17 novembre)

Gate N2A exact8581 : APPROVE6943153896/F1F2CLOSED et CI44048466660 development1016/118. MêmePR16, Developer seul writer frontend contrôleur/SeasonPanel/composant/formatage/styles/tests + navigateur offline dédié ; pas refonteAPI/auth/source/DB/ICS. Pipeline loadSeason orchestre loadEntries/listTask et notifications sans lectures privées concurrentes s’annulant ; une preuve acteur par opération, leases après await/catch/finally. Compteur serveur horspage, ACK204→GET (pas faux0/retry), retraitscope/nettoyage+compteur inconnu puisrefresh. Étape contrôleur/UI ciblée puis navigateur réel synchronize fixture, desktop/mobile390 et contexte public conservé. Deux captures connues CI seulement autorisées. Acceptation finale N2COMPLÈTE et integrated/main avant suite.
## Jalon intermédiaire N2B1 (17 novembre)

Contrôleur/store/section et ciblés frontend livrés avant navigateur, GEL court pour revue indépendante lease/rendu. Source sync snapshot complet est réduit par record_change aux seules clés changed : renderer compatible delta différentiel/full snapshot, sans exigence de payload complet. N2B2 vrai navigateur/Sync/captures reste TODO après gate N2B1 ; aucune acceptation N2 finale implicite.
## N2B2 — preuves navigateur terminées, acceptation finale en attente

Deux browsers réels sur `_test` (17novembre) : 2PASS96,13s, vrais synchronize successifs→52Alice/26Bob/50visibles puis ACK horspage/nouveauSync/retrait/réajout ; mobile390 calendrier décembre→absence à vérifier/ACK/restauration, quatre statuts et identités exactes. Pas modification produit/limite20/60/protocole/caméra. Captures desktop/mobile vues réellement, whitelistfailure bornée2PNG. Voir handoff pour incidents de harnais conservés et commandes. N2A/N2B1 ciblés historiques ; N2 final demeure TODO jusqu’au verdict complet exactSHA+integrated/merge/mainCI.
