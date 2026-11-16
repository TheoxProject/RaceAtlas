# OPS-N1B — raccord de la synchronisation aux changements

16 novembre2026. Même branche isolée `feature/operations-readiness`, DraftPR15, base main `c74086365df62bf1c71623e080bb1f649c9981f5`. Fondation N1A approuvée au SHA exact `a76e35a5e11ad86362c4716e344c3f6c0037eabe` : [rapport](https://github.com/TheoxProject/RaceAtlas/pull/15#issuecomment-6911659509), CI43829642340 development/full SUCCESS927backend346,25s/118frontend. Ce contrôle n'est pas le gate integrated final. P2 ordre global fermé par sonde indépendante ; ancienne preuve40P01 et durée anormale du groupe Reviewer conservées dans les rapports.

## Ownership et jalons

Coordinator cadre puis transfère explicitement. Developer devient seul writer suivi : `raceatlas/sync/service.py`, petits helpers de projection de faits nécessaires, tests sync/notifications et fixtures synthétiques, documentation/checkpoint. Modèles/migrationb806, auth, planning/ICS, frontend, API et dépendances inchangés sauf manque réel d'interface démontré au Coordinateur. Tester lit/teste le SHA figé sans édition.

- **N1B-1** : gardes par fenêtre avant mutations, vrais deltas `_apply`, événements business et restauration de présence `present`. Premier jalon attribué, gel/revue ciblée avant la suite.
- **N1B-2** : finalisation de présence `to_verify`, plan d'audit pur, capacité et régressions ; attribué après APPROVE exact3ed et CI43870248750development942/118 ; interfaces ci-dessous.

N1B-1 seul ne termine pas N1B. PR15 ne fusionne qu'après acceptation indépendante COMPLÈTE du N1 final, CI nommée integrated complète, base actuelle puis mainCI. API/UI Changements récents restent N2. Aucun scheduler/live/email course nouveau.

## N1B-1 — comportement et transactions

Conserver verrou global d'import, contrat `_apply`/audit, commits par fenêtre, SAVEPOINT de géocodage/application, idempotence et réconciliation d'identités existants. Résoudre l'inventaire courant de races/scopes sous no_autoflush à CHAQUE fenêtre ; le préflight immutable seul ne voit pas les créations d'une fenêtre antérieure. Prendre l'union des gardes avant le premier flush/DML métier/nested de `_import_window`, pas après mutations dans `_apply`. Connexion RC transactionnelle effective, aucune acquisition Account côté sync. Le helper N1A ordonne les clés advisory numériques sur tout le ROOT DB ; ne pas recréer un ordre lexical local incohérent. Token non réutilisé après commit.

Nouvelle race : aucune ancienne sauvegarde valide/visible, pas alerte de création historique. Fenêtre ultérieure identique retrouve UUID/scopes existants sans double événement. Ne pas relâcher le préflight qui refuse des observations contradictoires dans un même run pour inventer une séquence A→B dans ce run ; tester les vrais changements sur runs successifs.

Sous garde, capturer avant/après des faits immuables par scopeID stable ; recharger sous verrou les objets éventuellement lus avant l'attente. Comparer uniquement faits métier, pas checked_at, contrôles, rang d'affichage, ordre des ensembles ou cache de géocodage. Tri des règles/catégories sans casser leur corrélation ; raw labels/restrictions/provenance/incertitude préservés. Date/titre/statut/discipline/types/organisateur/commune/groupement race visent ses scopes ; éligibilité/règles/label changés visent CE scope. Aucun mélange avec un scope frère, admissibilité ou coordonnées de départ inventées. Un rafraîchissement des centres/cache seul ne change pas une course.

Action updated : clé `revision:` + ID de la SourceRevision réellement créée, provenance IMMUTABLE de cette révision ; pas businesshash seul, run_id seul ou nouveau checked_at rejoué sous ancienne clé. Une révision technique/reorder sans delta ne crée pas d'événement. Création, relecture/fraîcheur/replay sans delta : zéro notification parasite. Restaurer une vraie présence to_verify→present même sur action autrement unchanged génère un événement presence distinct ; présence déjà present n'en génère aucun. Kind presence n'est jamais cancelled.

Mutation, révision, changement et cibles dans le même SAVEPOINT/commit : erreur record annule aussi la mutation correspondante et reste auditable avec diagnostic borné, sans payload/secret. Projection privée N1A après commit source, jamais fanout/lock Account ni envoi dans sync. Les abonnements antérieurs reçoivent le futur delta, ceux créés après commit prennent la nouvelle baseline sans rétroactivité ; retrait/réajout et autres comptes/scopes restent isolés.

## N1B-2 — contrat attribué, implémentation en cours

Prévoir sans affectation ORM/autoflush les promotions historical_duplicate, conditions success/couverture/stale et vraies transitions de présence. `_finalize_historical_duplicates` ne modifie que l'audit mais ses promotions peuvent autoriser l'inférence d'absence ; conserver cet effet. Seules les races qui changeront réellement de présence consomment des gardes/cibles, TOUS leurs scopes même sans abonné. Fraîcheur presence_checked_at, audit et catalogue volumineux sans delta ne deviennent pas un plafond produit.

Union réelle≤1000 : gardes puis appliquer audit/métadonnées/présence/événements dans le commit final atomique existant. Union>1000 : refus AVANT changements finaux, aucun timestamp/presence/event partiel, audit incomplet explicite borné et missing_marked=0 ; fenêtres déjà committées conservées selon contrat. Aucun drop/tri1000premiers/filtre aux abonnés, annulation fabriquée ou commits par item pour contourner la limite. Si un usage valide nécessite d'élargir cette borne technique, cadrer et mesurer l'extension séparément.

## Preuves attendues

N1B-1 : vrais imports synthétiques → changement scoped → projection privée unique ; deux scopes/deux comptes, quatre statuts, report/date/règles/annulation attestée ; idempotence/relecture/reorder/fraîcheur, A→B→A→B sur runs successifs, création fenêtre1/relecture fenêtre2, alias attestés. Vrais commits/barrières save avant/après import noncommitté ; source ne prend aucun Account, baseline/suppression/autrui/ICS cohérents. Erreur événement et rollback/savepoint ne laissent pas mutation source sans changement, ni révision/event/cible partiels. Contrats SourceRevision/Run/ImportItem/coverage existants préservés.

N1B-2 : présence complète→to_verify→present et cancelled attesté conservé ; fenêtres partielles/stale/erreur sans faux manque ; catalogue>1000scopes mais une vraie transition réussit, borne1000/1001 vrais scopes atomique avec un seul abonnement qui ne réduit pas l'union. Les preuves finales exercent B1+B2, pas seulement des appels directs record_change.

Ciblés sync/notifications/coutures utiles, pas replay local des927 tests inchangés. Checkpoint avant groupes longs/après échecs, commits/push WIP cohérents, exact SHA au gel et résultats réels. Réutilisation explicite des preuves immuables, jamais ancien verdict copié. _test Developer/_review Tester tous deuxb806 au départ, PG9780/55434 existant à vérifier ; aucun reset/reseed aveugle, runtime.close avant Engines. Rapport court et limites honnêtes.

Aucune collecte FFC live/bulk, service, email réel, DNS, DB distante, déploiement, achat ou publication finale autorisé. Fixtures synthétiques seulement ; les gates externes restent distincts.

## Interfaces B2 retenues avant implémentation (16nov2026)

Nouveau module pur final_plan : dataclasses frozen de primitifs/tuples/bytes (windows/items/races et plan), builder sans Session/ORM ni SQL. Prévoir promotions historical_duplicate et statuts logiques, success/stale/coverages, stamps metadata séparés des vraies transitions ; missing_marked compte les races. Charger snapshots sous no_autoflush ; apply après gardes numériques N1A de TOUTES les scopes des transitions réelles, pas metadata/touscandidats. Revalider snapshot avantDML sous garde, refuser plan changé sans retry silencieux.

Provenance absence : ImportWindow.source_url/checked_at réellement contrôlés, version Run.parser_version validée par pipeline Calendar.normalization_version, evidence_id=window:UUID ; witness maxchecked admissible/tiebreakID. Jamais URL/horodatage fiche Race non consultée ni now inventé. Clé presence:+SHA256 tuple(run,race,absence,before,to_verify,witness). Payload source_presence seul, Race.status/revision et SourceRevision inchangés.

Application dans unique commit final existant ; erreur scope/cap1001/record/commit rollback TOUTES mutations finales puis audit de refus seulement, runpartial/failed/missing0 et fenêtres affectées incomplete/diagnosticborné. Fenêtres B1 committées conservées. CoverageAPI ne peut être consistent_sample sur dernierRun refusé ; last_success antérieur reste honnête. Pas de nouveau modèle/migration/API/deps/CI.
