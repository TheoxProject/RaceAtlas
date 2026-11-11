# Lot 5 — Carte interactive Altitude / Summit

Base `3bd018bff1b60f3831606348831fd72375f557dd`, PR #6 intégrée, arbre identique au SHA approuvé `7cab9a3a3390e01b09f925fe6e9e6321997bc74a`. Branche `feature/map-experience`, worktree `add4/RaceAtlas`.

## Périmètre

Remplacer l'écran de démonstration par la carte React utilisant l'API catalogue réelle. MapLibre GL JS **5.11.0**, fond `https://tiles.openfreemap.org/styles/liberty`, DEM `https://tiles.mapterhorn.com/tilejson.json`, Terrarium 512 px. Aucun fournisseur payant, compte externe, PMTiles/téléchargement régional, collecte FFC ou déploiement. Pas de page liste distincte. Le calendrier mensuel vient au lot 6, sans bouton factice ou détail d'implémentation dans les parcours produit.

Décisions propriétaire acquises : **Altitude initial**, Summit 3D à la demande ; ouvrir le calendrier sélectionnera le mois affiché, conservé au retour carte, autres filtres et caméra préservés. Concevoir l'état partagé en ce sens sans implémenter prématurément le calendrier.

## Tâches et acceptation

- L5-01 Coordinator : cadrage/checkpoint/Draft PR.
- L5-02 Developer : données/API/état temporel et filtres, moteur et présentation responsive.
- L5-03 Developer : détails, non-localisées, erreurs/attributions, preuves navigateur et handoff.
- L5-04 Tester : SHA figé, revue indépendante, navigateur desktop/mobile et régression.
- L5-05 Coordinator : gates CI/Tester, fusion et bilan.

1. Carte WebGL réelle, pas simple mock moteur. Altitude avec ombrage 2,5D ; Summit avec terrain incliné. Attributions OpenStreetMap/OpenMapTiles et Mapterhorn visibles. Échec DEM : repli Altitude, données/filtres/détails accessibles, message utilisateur sans trace technique. WebGL indisponible : erreur utilisable et accès aux données non localisées/détails.
2. Consommer les endpoints du lot 4 et toutes les pages tant que next_cursor existe, y compris page items vide en mode rayon. Version périmée => reprise bornée/état clair sans mélanger les versions ; requêtes anciennes annulées/ignorées. Uniquement les centres de communes sourcés ; aucune coordonnée de départ inventée. Regrouper les Features par commune côté UI, puis clustering entre communes proches. Nombre de courses distinctes, pas de scopes ou marqueurs.
3. Contrôles Année/Mois/Semaine ISO initialisés depuis **l'année civile courante Europe/Paris**, jamais saison FFC. Frontières ISO et années bissextiles correctes. Une modification temporelle ne réinitialise ni centre, zoom, orientation ou inclinaison de caméra. Géographie/départements/rayon, disciplines/types, recherche et catégories ET/OU conformes à l'API ; CLM est Route. Filtres de session seulement.
4. Panneau détails desktop et bottom sheet mobile : nom/date/discipline/types, source/fraîcheur/statut, scopes et restrictions corrélées, incertitudes visibles. Pas d'éligibilité personnelle inventée. Annulation explicite distincte d'une fiche à vérifier. Non-localisées consultables distinctement, candidates rayon jamais ajoutées au total confirmé. Pas de latitude/longitude de départ fictive ni inscription vérifiée supposée.
5. Interface sportive navy `#111F37`, orange `#F97316`, lisible et utilisable à 390 px et desktop ; contrôles nommés/keyboard, chargement/vide/erreurs/retry, aucun débordement horizontal ou exception JavaScript non gérée. Ne pas exposer IDs techniques ni détails de lots au public. Les données synthétiques restent clairement identifiées.
6. Scénarios intégrés React → Flask → PostgreSQL réellement exercés : marqueurs/communes, détails/règles, filtres/caméra, périodes/ISO, non localisées/rayon, échec DEM, API en échec/curseur périmé, responsive. Tests unitaires ciblés de calculs temporels et cycle de données ; captures examinées visuellement. Tests déterministes hors réseau avec styles/DEM interceptés, moteur réel ; une qualification limitée des fournisseurs ne vaut pas autorisation de collecte source.
7. Regressions backend/contrats, lint/build et migration pertinente. Les anciens tests de démonstration peuvent évoluer vers le nouveau parcours complet ; conserver leurs garanties PostgreSQL/états vides/indisponibles. Handoff, commandes Windows, limites et screenshots locaux identifiés, SHA exact gelé avant Tester.

Une petite extension backend de métadonnées pour les options de filtres dynamiques peut être nécessaire : proposer au Coordinator la route et la compatibilité contractuelle avant de l'ajouter, sans modifier les réponses catalogue validées. Les décisions techniques ordinaires restent autonomes ; consulter le propriétaire seulement pour un choix produit majeur non couvert ici.
