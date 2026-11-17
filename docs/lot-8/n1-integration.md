# OPS-N1 — intégration confirmée

16 novembre2026. [PR15](https://github.com/TheoxProject/RaceAtlas/pull/15), tête revue **60611f19763b112e798600293efa92783d9b5e0d**, merge **014bda3480d0f8c0233f8e6f68d0ae82886b83db** confirmé par GitHub et fetch. Arbre identique **fc0609c828146ed50288bd0e653877d6a93f1191**, diff nul. Copie personnelle main et autres worktrees préservés.

[APPROVE indépendant COMPLET N1A+B1+B2](https://github.com/TheoxProject/RaceAtlas/pull/15#issuecomment-6924953718) au SHA exact. Le journal scopé, les baselines/contraintes/cascades, les gardes de transaction, la projection privée, les imports réels et la finalisation de présence sont intégrés. API/UI notifications non livrés par N1.

| Gate | Résultat réel |
|---|---|
| Integrated43925227183 | SUCCESS967backend285,28s/118frontend |
| Ready43926697034 | SUCCESS967backend284,05s/118frontend |
| Main43928375559, merge014bda3 | SUCCESS967backend280,55s/118frontend |

Tous les contrôles complets vérifient les sources avant/après et incluent migrations, contrats, lint/format, build et dépendances. Aucun development utilisé comme gate de fusion. Le connecteur avait refusé ci:full (403) ; l'accès GitHub existant autorisé a posé le label avec vérification du SHA, sans contourner protection ni permission.

Preuves Reviewer :14PG ciblés10,11s et sonde après vrai commit ;44PG/5contrastes/N1A/B1 explicitement réutilisés après diffs nuls. Source→changement→projection, scopes/comptes/statuts, absence/replay/restauration/provenance calendrier, cap1000/1001, rollback et sauvegardes concurrentes exercés. [Mission](sync-notifications-mission.md), [handoff](developer-handoff.md), [commandes](local-development.md).

Les P2 historiques sont conservés : ordre de verrous entre appels (40P01) corrigé, et faux audit après commit réussi avec accusé perdu corrigé par confirmation durable. Commit confirmé : vrai bilan conservé ; confirmation impossible : outcome_unknown sans faux missing0, sans reprise silencieuse. Ancien b9f REQUEST CHANGES et sonde sont archivés/publiés dans PR15. Les anciens échecs de fixtures, l'installateur Ubuntu26.04 et l'attendu restauration pré-B2 restent distingués des succès actuels.

N2 peut démarrer depuis ce main validé. Le lot8 entier, la qualification réelle des fournisseurs et la V1 publique restent à terminer. Aucune collecte live, email réel, DNS, service, DB distante, déploiement, achat ou publication finale effectué.
