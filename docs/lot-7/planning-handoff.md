# PLAN-A — Handoff Developer

Document historique du jalon A approuvé au SHA ae446a5. Pour le candidat final API+ICS, voir [handoff PLAN-A+B](planning-ics-handoff.md). Les mentions ICS absent décrivent uniquement ce jalon antérieur.

Jalon API privée CRUD/liste et snapshot, branche `feature/private-planning`, [Draft PR13](https://github.com/TheoxProject/RaceAtlas/pull/13), base **87d7dd53efcdb144c38e2d3ef1f83c89e63654fc**. Ce document accompagne le commit candidat ; le SHA exact publié est communiqué au Coordinator au gel. Aucun verdict indépendant PLAN-A ou résultat CI du candidat n'est présumé. Auth backend intégré et approuvé au SHA da5743c500603a11366080e97cd2e76db7cbcb33, merge PR12 87d7dd53efcdb144c38e2d3ef1f83c89e63654fc et mainCI43515934267 SUCCESS791/67 : preuves réutilisées pour les modules auth inchangés, pas approbation de ce jalon.

## Livraison et interfaces

- `raceatlas/planning_http.py` : GET `/api/v1/me/saved-entries`, PUT `/by-scope/<scope_id>` avec `{status}`, PATCH `/<entry_id>` avec `{status}`, DELETE `/<entry_id>` avec `{}`. Préfixe complet identique sur les quatre routes. Réponses GET `{items}`, PUT/PATCH `{item}`, DELETE204. Aucun acteur, filtre public ou borne temporelle fourni par le client.
- `raceatlas/planning_snapshot.py` : `snapshot_documents(session, actor, entry_id=None, limits=None)` produit des dictionnaires ordinaires ; `encode_personal(document, limits)` produit les octets JSON UTF8 exacts avant commit. DTO : saved ID/scope/status/revision/dates, race/provenance/localisation et LE scope avec ses règles/catégories/restrictions/normalization_version. Aucun autre scope, compte/email, mot de passe ou bearer. `personal_eligibility=not_evaluated` n'invente aucune admissibilité personnelle.
- Raccord minimal dans `auth/http.py` et action `planning` dans `auth/admission.py`. Réutilisation des frontières/config/slot/admission/CSRF/Origin/strictJSON8KiB C0 et du cookie/acteur persistant même Session C1. Authorization Basic preview reste permis, sans droits compte. 401 passive sans Set-Cookie. Commit et fermeture avant Response ; échec commit503 générique et rollback.
- Contrats additifs `contracts/planning.schema.json` et `planning.openapi.json`. Codes planning400 invalid_status,404 not_found,413 selection_limit ; codes du périmètre auth conservés. PATCH d'une entrée étrangère/inexistante donne404 avant validation métier du statut. DELETE ne demande pas de statut.

## Cohérence et limites

Auth conserve READ COMMITTED et le verrou Account, puis le snapshot utilise **un SELECT** avec JOIN explicite Scope→Race et joinedload des relations nécessaires. `raiseload("*")`, `populate_existing` et DTO immédiats empêchent SQL lazy ou réutilisation d'un graphe ORM ancien. Aucun `race_document` parcourant les scopes voisins. Le test d'import réel synthétique modifie titre/dates/labels sur une autre connexion pendant le SELECT : première réponse entièrement ancienne, suivante entièrement nouvelle, sauvegardes stables.

`PlanningLimits` impose 1000 sauvegardes/account,2MiB de réponse exacte et16KiB UTF8 par valeur texte. Seul le serveur peut réduire ces limites dans `app.extensions["planning_limits"]`. Créations sérialisées sous Accountlock ; mise à jour/upsert existant et retrait restent possibles au cap. Liste cap+1 détecte le dépassement, aucune liste valide tronquée. Tri created_at/id, tous les quatre statuts et toutes les années,201 entrées exercées. Si la représentation dépasse les bornes, refus413 et aucune création privée partiellement validée. Les règles du scope restent séparées, Registered demeure déclaratif, source absente reste to_verify sans annulation inventée.

## Preuves exécutées et incidents conservés

Commandes reproductibles et environnement : [développement local](planning-local-development.md).

- Premier ciblé10 PASS19,271s, `.local-tools/plan-a-first.xml`.
- Étendu19 :18 PASS/1 FAIL36,392s, `.local-tools/plan-a-complete.xml` : référence `$defs/Id` manquante dans le nouveau contrat. Ajout de la définition ; pas défaut produit masqué.
- Une invocation contenant les chemins inexistants `test_api.py`/`test_health.py` a terminé sans tests (exit1), puis la commande réelle ci-dessous a été exécutée.
- Final acquis avant interruption, réconcilié le14nov sans relance : **139 PASS118,877s**,0 erreur/skipped, `.local-tools/plan-a-final.xml` :19 PLAN-A,68 ACC01,29 auth HTTP sessions,20 fondation publique,3 options catalogue. Aucun changement source depuis cette exécution, hors documentation. La reprise a vérifié le rapport complet et l'absence de Python actif ; le résultat n'est pas déduit du cache pytest.
- Ruff check PASS ; Ruff format --check **73 fichiers** conformes, vérifié après reprise. Contrats publics Node **26 PASS** ; schéma planning Draft202012 et17 cibles de références locales résolues, réponses réelles GET/PUT/erreur validées dans les19 tests. Pip check PASS, dépendances inchangées. Diff check PASS avant commit.
- Pas de full backend791 ni navigateur/build frontend local : aucun code frontend, moteur carte, dépendance, modèle ou migration modifié. La fixture PostgreSQL réexerce upgrade/check/downgrade/upgrade/check au schéma existant f61d338ab204.

Les19 nouveaux tests couvrent deux comptes/deux appareils, propriété404, CSRF/Origin/session non vérifiée/révocation, no-op/revision, cap concurrent,201 sauvegardes, UTF8 exact16KiB et dépassement/rollback, commit failure, verrou Account libéré avant Response, compteur SQL=1 puis zéro au rendu, relecture ORM, vrai import concurrent et reorder/replay/refus ambigu/absence sans transfert de favoris. Les gardes d'IDs NUL/surrogate/longueur/type refusent avant SQL et la Session reste utilisable.

## Revue et limites restantes

Tester : vérifier le SHA gelé annoncé, les quatre routes avec comptes réels sur `_review`, les contrats/scopes et les barrières de cohérence/concurrence ; constater l'absence de route ICS factice. La CI du cadrage cb02b99dcbdc41af8cb3487465c07385221de3fe (43518396894 SUCCESS791backend191,73s/67frontend) ne valide pas ce nouveau code. Nouvelle CI et revue exactes requises avant libération.

PLAN-B ICS/codec/cache/UID/SEQUENCE, migration et parseur indépendant ne sont pas commencés. UI, lot7 complet et lot8 restent à faire. Pas de benchmark Free, fournisseur réel, email/DNS/compte externe, collecte, base distante ou déploiement effectué. Tous imports sont synthétiques/offline ; aucun dataset FFC brut conservé. Aucun worker/test/serveur de test retenu après le ciblé ; PostgreSQL local38028 reste disponible et les Node d'autres tâches ne sont pas touchés.
