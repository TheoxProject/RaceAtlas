# Rapport de pré-déploiement après le lot 6

## Base et objectif

Base vérifiée : **7b733d86d99a354fdcfe2bf1ecbde519ef78a68f**, après [intégration du lot 6](../lot-6/integration.md) et CI main verte. Branche isolée `feature/predeployment-report`. Préparation explicitement demandée par le propriétaire ; aucun nouveau périmètre produit.

Livrer un rapport concret et vérifiable avant de demander une décision de premier déploiement. Ne créer aucun compte/service distant, ne pas importer le Blueprint, ne pas modifier une base distante, ne pas envoyer d'email réel et ne pas activer de collecte. Le rapport distingue ce qui est préparé, testé localement, estimé sous hypothèses et encore bloqué.

## PRE-01 — contenu et réglages préparatoires

1. `docs/readiness/predeployment-report.md` : services Render Free monolithique Flask/React et Neon Free ; étapes de configuration, variables privées/TLS/Waitress/health, migrations manuelles, sauvegarde/restauration, protection Basic, arrêt/reprise et tests après une éventuelle autorisation. Réutiliser `hosting.md`, sans revendiquer build Render ou connexion Neon déjà effectués.
2. Limites officielles datées, sources primaires et risques de facturation ; bornes réelles du compte encore inconnues. Estimations explicites avec hypothèses et formules ; aucun volume FFC annuel ou performance Render inventé. Pas de garantie de gratuité sans contrôle du compte et des plafonds.
3. Choix technique préparé : région Render `frankfurt`, cohérente avec un futur projet Neon AWS Frankfurt si disponible en Free. Aucun service créé, aucune conformité juridique déduite de la région. Vérifier la valeur selon la documentation officielle.
4. Attributions : aligner le lien Mapterhorn visible sur sa page d'attribution indiquée par les métadonnées fournisseur, sans changer le moteur, les quatre crédits ou le mode initial. Ne pas présenter cette correction comme audit complet des licences. Le JSON d'attributions a répondu 403 au GET standard du 12 novembre : aucun contournement ni nouvelle tentative sans raison ; documenter la limite et les sources publiques réellement accessibles.
5. Exposer les blocages réels : compatibilité/droits FFC non établis, qualifications GPU/live, sauvegarde/restauration complète encore au lot 8 et absence d'expéditeur. Le propriétaire a choisi **email et mot de passe avec récupération par email**, mais indique **aucun domaine ni expéditeur pour le moment**. Le transport local simulé permet le développement indépendant ; il ne valide pas la délivrabilité réelle ni le prérequis d'expéditeur du lot 7.
6. Mettre README, liens d'exploitation et checkpoint en cohérence. Présenter au propriétaire deux ou trois moments possibles de premier déploiement avec recommandation et préconditions précises, sans considérer son silence comme approbation et sans exécuter les opérations proposées.

## Ownership et validation

Coordinator possède mission, intégration du lot 6, PR, réconciliation et décision de gates. Developer recevra seul l'ownership de `ops/render.yaml`, lien Mapterhorn dans `frontend/src/MapView.jsx`, tests existants d'attribution strictement concernés si nécessaire, rapport/handoff/readiness/README/checkpoint. Pas d'autre source backend, modèle, migration, API, dépendance ou méthode d'authentification à implémenter dans ce jalon.

Contrôles ciblés : YAML et région, scripts/configuration toujours désactivés, liens locaux/primaires et arithmétique, lint/build et parcours crédits pertinents si href modifié. Pas de nouvelle campagne backend complète locale pour des documents/configurations/lien. CI surveillée après chaque push ; revue indépendante du SHA final, tous gates avant fusion puis CI main. Aucun test créé uniquement pour recopier une valeur de configuration réversible.

## Suite

PRE-00 cadrage/Draft ; PRE-01 rapport/configuration ; PRE-02 revue ; PRE-03 intégration/main et présentation au propriétaire. Ensuite lot 7 comptes/planning/ICS sur les parties indépendantes ; validation d'un expéditeur et tout envoi réel restent des actions séparées à préparer avant autorisation.
