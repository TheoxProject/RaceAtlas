# Lot 2 — Adaptateur FFC isolé

Base vérifiée : `2e03cd83931d2297df0b3be830c35974f588fbb8` (lots 0, 1 et politique agents fusionnés). Branche `feature/ffc-adapter`, worktree Codex `add4/RaceAtlas`.

## Périmètre et décisions

Transformer du HTML fourni explicitement en observations Python validées et en modèles du socle. Aucun client réseau, collecte, import récurrent, migration distante ou déploiement. Les sélecteurs attestés sont documentés dans `docs/lot-0/source-audit.md` ; les formes synthétiques supplémentaires sont une interface de test, jamais une preuve de compatibilité live.

Le parseur ne décide pas du rapprochement durable. Les IDs internes existants doivent être fournis/conservés ; les nouvelles identités sont opaques, jamais dérivées du titre, slug, date ou position. Listes sans preuve durable : `source_list_id=null`, identité `unverified` ; réorganisation ambiguë : `needs_review`, sans réaffectation automatique. La réconciliation et la synchronisation persistante restent au lot 3.

Décisions techniques ordinaires prises et documentées par l'équipe. Fonctionnel mineur : cohérence avec les contrats. Choix produit majeur ou alternatives avec impact visible : question précise au propriétaire, 2–3 options et recommandation ; seules les tâches indépendantes continuent. Limites juridiques, financières, sécurité et production inchangées ; le silence ne vaut jamais approbation.

## Tâches et critères d'acceptation

- L2-01 Coordinator : checkpoint, mission et Draft PR, environnement réutilisé.
- L2-02 Developer : parseur calendrier et fiche, observations typées, diagnostics structurés et projection vers le modèle existant.
- L2-03 Developer : fixtures HTML exclusivement synthétiques, tests positifs/négatifs et handoff.
- L2-04 Tester : revue indépendante du SHA figé, régression socle et intégration PostgreSQL/Flask.
- L2-05 Coordinator : CI verte au même SHA, fusion confirmée, bilan et reprise du lot 3.

Acceptation :

1. Saison sportive distincte de la date civile ; liens dédupliqués par saison/numéro, jamais par slug. Fenêtres demandées/effectives et compteurs contrôlés ; incohérences explicites, jamais couverture complète déduite d'un HTTP 200.
2. Discipline/type/catégories fondés sur contenu explicite ; CLM est Route ; inconnues et HTML changé diagnostiqués. Aucune inférence depuis le slug.
3. Restrictions corrélées conservées par règle et scope, catégories génériques non élargies sans preuve ; cas négatifs entre listes et catégories inconnues.
4. Identités internes conservées sur révision attestée ; aucune identité source de liste inventée, ambiguïté/reclassement signalés.
5. Provenance minimale/version de normalisation ; aucune donnée participant ou page brute conservée ; annulation uniquement explicite, absence jamais assimilée à annulation.
6. Parcours fixture → adaptateur → PostgreSQL jetable → API détail existante, validé contre le schéma ; tests de régression lots 0/1, lint/format/build pertinents.
7. Handoff, verdict Tester et CI du SHA final ; aucune activation réseau/source ni service externe.

## Limites assumées

La qualification live du HTML complet n'est pas établie par les observations du lot 0. Les dispositions inconnues doivent échouer explicitement plutôt que fabriquer des faits. Les droits et la collecte FFC restent bloqués selon `docs/lot-0/open-questions.md`. Aucun choix produit majeur requis pour ce lot isolé.
