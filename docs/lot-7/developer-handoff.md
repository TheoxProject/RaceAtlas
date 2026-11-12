# Handoff ACC-01 — identité privée et sauvegardes par scope

Branche `feature/accounts-and-planning`, PR https://github.com/TheoxProject/RaceAtlas/pull/11, base **51856c9940a2b0e16c9f05d61a9f1726ae8701d9**. Parent local/distant avant ce jalon **c9696821e7f01afc72ed30837ee5388fd71e5c48**. Relever le SHA publié pour revue ciblée ACC-01 et CI. Une éventuelle intégration de cette fondation ne termine pas le lot 7.

## Interface à conserver pour ACC-02

`raceatlas/planning.py` est uniquement un service interne ; le caller possède commit/rollback. Aucun endpoint, cookie, session authentifiée, header utilisateur ou bypass créé. Le compte est une identité privée, **pas un compte connecté** : aucun faux hash ou mot de passe vide ajouté.

Toutes les opérations privées reçoivent un **Account persistant attaché à la même Session ORM**. ACC-02 devra le charger depuis son authentification serveur validée ; ne pas accepter un acteur issu d'un paramètre de requête, d'un ID utilisateur public ou d'une instance détachée. Ce contrôle de type/session ne constitue pas lui-même une authentification : les callers internes sont fiables, une future route doit établir ce lien de confiance avant l'appel.

- `create_account(session, email)` crée une identité opaque et retourne l'Account persistant ; doublon → domaine `account_unavailable`, sans refléter l'adresse. Ce résultat ne devra pas devenir une réponse HTTP d'énumération dans ACC-02.
- `normalize_email` applique `strip().lower()`, garde points et plus-tags, refuse espace/contrôle interne, forme vide ou plusieurs `@`, longueur >254. Politique de compte volontaire, pas validation RFC complète, Unicode/IDNA canonique, preuve de propriété ou délivrabilité. Le champ `email_normalized` est privé et unique, avec gardes PG trim/lower/forme minimale. Aucun email original supplémentaire conservé.
- `put_saved_entry(session, actor, scope_id, status='interested')` utilise `INSERT ... ON CONFLICT` PostgreSQL. Cible stockée : scope seul, course dérivée par `entry.scope.race_id`, aucun `race_id` redondant. Identité de la sauvegarde conservée lors des changements ; retour ORM rafraîchi même si déjà chargé.
- `get_saved_entry`, `list_saved_entries`, `update_saved_entry`, `delete_saved_entry` filtrent toujours sur le compte serveur. Lecture/modification/suppression d'une entrée d'autrui et d'une entrée inexistante renvoient le même `not_found` générique ; validation du statut après ownership en update. Cibles malformées/non trouvées n'exposent pas d'erreur FK brute du service.
- Statuts stricts `interested`, `planned`, `registered`, `completed`. `registered` reste déclaratif et ne prouve aucune inscription ou éligibilité FFC.
- `SavedEntry.revision` privée initiale **1**, +1 uniquement sur vrai changement de statut. No-op conserve ID, created_at, updated_at et revision. Le compteur public du catalogue n'est pas utilisé ou invalidé par les écritures privées. Ne pas commencer ICS sur cette fondation seule.
- FK scope **RESTRICT**, compte **CASCADE** sur ses données privées. `delete_account` n'efface ni source/scopes/courses ni favoris d'un autre compte ; révocation de sessions/credentials et parcours de suppression appartiennent à ACC-02.

Les trois nouveaux timestamps privés restent SQL `timestamptz`. Leur type ORM dédié rend toujours des datetime aware UTC et refuse une valeur naïve en binding, sans modifier les timestamps existants du catalogue. Pourquoi : le premier run a révélé le cluster en Europe/Paris ; [PostgreSQL](https://www.postgresql.org/docs/17/datatype-datetime.html) stocke l'instant mais l'affiche selon TimeZone de session. Le [TypeDecorator SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/custom_types.html) normalise ici seulement les nouveaux champs privés ; sources primaires consultées le 12 novembre 2026. Tests sous UTC, Europe/Paris et Pacific/Honolulu, sans changer le fuseau global de l'application.

## Migration et preuves

Migration **c40a7162b901** après **b7f4208ac112** : tables account/saved_entry, contraintes uniques/statuts/révision/ordre temps, FK ciblées et index scope. Aucun trigger du catalogue ajouté aux tables privées. `conftest.py` tronque aussi account afin d'isoler les tests ; la réinitialisation reste limitée à `_test`/`_review` et à leur opt-in existant.

PostgreSQL existant vérifié avant run : `pg_ctl status`, PID 38028, loopback port 55434 ; aucun pytest/Vitest/A-B concurrent. Python 3.12.14 et caches réutilisés ; DB **raceatlas_lot2_test** uniquement. Commande native après variables du checkpoint :

```powershell
python -m pytest tests/backend/test_planning.py -q --tb=short
python -m pytest tests/backend/test_foundation.py tests/backend/test_catalog.py tests/backend/test_catalog_sync.py -q --tb=short
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
git diff --check
```

Premier run : **36 PASS / 4 FAIL, 16,06 s**, migration upgrade/check/downgrade base/upgrade/check PASS. Deux erreurs UTC de retour ORM corrigées comme ci-dessus ; deux erreurs de tests corrigées (filtre obligatoire absent dans l'appel API de preuve, diagnostic exact `scope_identity_needs_review` pour ambiguïté sans attestation). Run final ACC-01 : **43 PASS, 24,49 s**, code 0. Régression publique fondation/catalogue/snapshot : **88 PASS, 52,38 s**, code 0, incluant à nouveau le cycle de migration et les checks concordance modèle/schéma. Ruff check et format --check complets PASS (**43 fichiers**), **26 contrats et diff PASS**. Aucun processus Developer conservé, aucun backend complet 389 répété. Frontend/build inchangés, non réexécutés localement ; CI complète actuelle requise.

Preuves ACC-01 : deux utilisateurs sur une même liste et deux listes d'une même course ; isolation CRUD/acteurs invalides ; UTC ; quatre statuts, idempotence et révision ; deux connexions PG réelles concurrentes (même statut → une entrée/révision1 ; statuts distincts → même ID/révisions2–3) ; contraintes directes PG et refus de suppression du scope sans autre dépendance que la sauvegarde ; compte supprimé sans toucher l'autre ni le catalogue ; version publique et JSON privés inchangés.

Imports réels du service sync avec observations synthétiques : renommage/report, réorganisation explicitement attestée et replay conservent IDs/statuts/timestamps/révisions privés ; ambiguïté sans preuve, retrait/split et déplacement de règle entre scopes refusés avec audit review et graphe intact ; absence contrôlée réussie → source `to_verify`, cible/favori conservés. Pas de réaffectation par rang/libellé, pas de nouvelle politique source. Aucune page ou collecte FFC réelle utilisée.

## Limites et revue attendue

Tester doit vérifier le SHA gelé : contraintes et aller/retour migration, isolation et objet ORM déjà chargé, no-ops/révisions, deux vraies sessions et graphe sync conservé. CI complète du candidat obligatoire. Les suites frontend/carte et autres sources sont inchangées ; aucune campagne backend 389 complète locale répétée ni preuve ancienne copiée au nouveau SHA.

ACC-02 auth/credentials/CSRF/récupération, API privée/ICS, UI et acceptation complète restent à faire. Email/mot de passe confirmé, sans domaine/expéditeur ; simulateur local futur ne valide pas délivrabilité/envoi réel. Premier déploiement après lot 8, sans opération distante/email/service/paiement/DNS/collecte dans ce jalon. Après publication : arrêt des éditions jusqu'à libération explicite.
