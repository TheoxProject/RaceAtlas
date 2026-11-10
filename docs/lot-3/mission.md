# Lot 3 — Synchronisation auditable et communes

Base : `f33d837844abdc51ebcafc066da3c16cb4982f34`, merge confirmé du lot 2 (PR #4), arbre identique au SHA approuvé `511208b7d5142f708106a3d4a8f51d170fb3e148`. Branche `feature/auditable-sync`, worktree `add4/RaceAtlas`.

## Périmètre

Persister les observations du lot 2 par une synchronisation locale explicite, idempotente, transactionnelle et auditable ; résoudre les communes avec un fournisseur injecté et un cache persistant. Fixtures synthétiques par défaut. Aucun client FFC live, ordonnanceur actif, géocodage réseau implicite, migration distante ou déploiement.

Un rang, libellé ou slug ne prouve jamais un rapprochement de liste. Une modification ambiguë est enregistrée pour revue sans écraser les scopes/règles/favoris. Une répétition strictement identique ne crée ni nouvelle course ni révision métier. Les alias source demandent une preuve explicite ; aucun rapprochement par similarité.

## Tâches

- L3-01 Coordinator : bilan lot 2, mission, checkpoint et Draft PR.
- L3-02 Developer : modèle/migration audit, service d'import, révisions/empreintes métier, alias explicites et erreurs partielles.
- L3-03 Developer : résolution/cache communes, intégration hors réseau, fixtures et preuves.
- L3-04 Tester : SHA figé, PostgreSQL réel, migrations et régression.
- L3-05 Coordinator : CI et Tester au même SHA, fusion et bilan.

## Acceptation observable

1. Deux imports identiques ne dupliquent aucune identité ou révision métier. Chaque exécution conserve son audit (version parseur, horodatages, fenêtres demandées/effectives, compteurs, erreurs et verdict).
2. Les empreintes excluent tokens aléatoires d'observation, date de contrôle, bruit de présentation et participants ; elles conservent les faits métier et restrictions corrélées. Provenance minimale/version vérifiable sans archive de page brute.
3. Modification attestée du titre/date/groupement conserve les IDs internes. Alias saison/numéro explicitement attesté conserve la cible ; conflit/ambiguïté refuse le rapprochement et laisse l'existant intact. Aucune identité source de liste fabriquée ; réorganisation ambiguë en revue.
4. Fenêtre incohérente, détail manquant/invalide, erreur fournisseur ou import partiel n'efface aucune ancienne donnée et ne permet aucune conclusion d'absence. Absence dans une fenêtre entièrement contrôlée : `source_presence=to_verify`, jamais annulation. Une annulation sourcée reste conservée si la fiche disparaît.
5. Reprise après échec : transactions/savepoints et audit explicites, aucun état à moitié remplacé ; nouvel essai cohérent sans doublons. Les fenêtres indépendantes restent exploitables sans masquer les échecs.
6. Géocodage au centre de commune exclusivement : cache persistant positif et négatif/version/provenance ; résultat hors département ou ambigu rejeté, erreur sans faux centre. Deuxième résolution identique via cache ; course non localisée consultable dans l'API détail.
7. Flux fixtures → adaptateur → synchronisation → PostgreSQL → API/schema testé, révisions/identités/communes contrôlées. Migrations upgrade/check/downgrade/upgrade/check, contraintes et régressions lots 0–2. Commandes Windows et handoff.
8. Aucun workflow planifié/live ni service externe activé. La couverture technique ne prétend pas prouver l'exhaustivité intrinsèque FFC ; les données synthétiques restent identifiées.

Décisions techniques documentées en autonomie ; pas de fonctionnalité utilisateur hors roadmap. Politique de consultation du propriétaire conservée au checkpoint. Les droits et qualifications live du lot 0/2 restent ouverts et n'empêchent pas ces tests hors réseau.
