# Préparation V1 après lot 5

Base vérifiée : **5f8229245f31ff64f678cad9df331f7302bef76f**, lot5 intégré. Branche `feature/v1-readiness`, worktree isolé `add4/RaceAtlas` réutilisé après vérification de propreté et arrêt de tous les agents/tests. Le checkout personnel `main` est préservé.

Cette PR de soutien exécute la nouvelle mission propriétaire du11novembre2026 ; elle ne remplace pas les lots6–8 et n'autorise aucun déploiement.

## Fonctions et critères

1. **RDY-01 workflow/documentation** : validation progressive durable dans AGENTS/workflow ; tests Developer ciblés, revues indépendantes aux jalons importants, revue complète du lot final, CI inspectée après chaque push et corrigée rapidement. README reflétant les lots réellement intégrés et setup Windows. Qualification FFC limitée documentée avec provenance, inconnues et arrêt sur incompatibilité/droits.
2. **RDY-02 CI** : PR vérifiée sur son SHA courant, contrôle de checkout et de tête distante, annulation des anciens runs, contrôles complets après push sur `main`. Échecs automatiquement visibles par annotations/résumé et artefacts synthétiques bornés. Garder les validations existantes et permissions minimales ; pas de bot d'écriture, workflow privilégié ou déploiement. Séparer rapide/lourd seulement si bénéfice réel démontré.
3. **RDY-03 configuration locale d'hébergement** : un Web Service Render Free monolithique Flask/React compilé, Waitress, Neon PostgreSQL via environnement et TLS vérifié. Blueprint préparatoire hors activation, auto-déploiements/previews désactivés ; aucun service créé. Build/start reproductibles, migrations séparées et jamais exécutées au démarrage/build, secrets absents du dépôt.
4. **RDY-04 accès et exploitation préparés** : mécanisme de preview privée réellement fermé sans credentials et protégeant API/assets, health checks minimaux, redémarrages/veille documentés, procédure sûre de sauvegarde/restauration hors filesystem éphémère. Tests synthétiques locaux ; pas de mutation de base distante ni affirmation de handshake Neon/déploiement réel.
5. **RDY-05 validation finale** : tests pertinents, CI du SHA final verte et APPROVE indépendant exact avant merge ; vérifier ensuite le SHA et la CI de `main`. Rapport de pré-déploiement propriétaire à produire après le lot6 avec ressources, limites gratuites revérifiées, risques de facturation, protection et tests après déploiement.

## Responsabilités et contraintes

Coordinator possède initialement AGENTS/workflow/README/qualification/checkpoint. Après revue ciblée du jalon RDY-01, Developer aura le périmètre explicite CI/configuration/tests/docs opérationnelles. Un seul writer dans le worktree ; Tester lit uniquement les sources figées. Aucun changement fonctionnel carte/calendrier, aucun assouplissement des gates ni des permissions GitHub.

Réutiliser Python/Node/Chromium/PostgreSQL locaux décrits au checkpoint. Les bases `_test` et `_review` restent distinctes. Interdits : Render/Neon créés ou déployés, services payants, secrets dans Git, remote migrations, collecte FFC massive/récurrente, publication finale. Les limites fournisseurs sont consultées officiellement au moment de préparation et doivent être revérifiées à l'activation.

Après intégration et CI main verte : démarrer le **lot6 calendrier mensuel** depuis main actualisé. Décision déjà acquise : ouvrir le calendrier sélectionne le mois affiché ; le retour carte conserve ce mois, les autres filtres et la caméra.
