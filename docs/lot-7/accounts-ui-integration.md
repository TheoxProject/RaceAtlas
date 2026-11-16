# Comptes et Ma saison — intégration locale

15 novembre 2026. [PR14](https://github.com/TheoxProject/RaceAtlas/pull/14), tête revue `de4e7c449a0e6f6124d9238381ad9a263a066787`, merge confirmé `c74086365df62bf1c71623e080bb1f649c9981f5`. Arbre identique `1663a7d19bf3610696156156291f5abeb5693154`, fetch et diff réels ; copie personnelle main préservée.

[Tester APPROVE complet](https://github.com/TheoxProject/RaceAtlas/pull/14#issuecomment-6898826817) pour UI-1 + UI-2A + UI-2B au SHA exact. Parcours modifié saison : 1 PASS27,57s ; réutilisation explicite des preuves immuables de signup/confirmation/reset, deux comptes/scopes, réponses tardives, export ICS parsé, révocations et suppression. [Mission](accounts-ui-mission.md), [handoff](accounts-ui-handoff.md), [auth](auth-integration.md), [planning](planning-integration.md).

| Contrôle | Résultat réel |
|---|---|
| PR integrated43743920900 | SUCCESS891backend408,69s/118frontend |
| Ready integrated43744817098 | SUCCESS891backend357,92s/118frontend |
| Main push43745685937, merge c740863 | SUCCESS891backend262,96s/118frontend |

Les trois contrôles complets vérifient le SHA avant/après, les contrats, le lint/format, le build et les dépendances. Aucun résultat development utilisé comme gate de fusion.

Les échecs43736947900 (890/1),43740601544 (889/2) et43742604527 (890/1) restent documentés. Trois cycles ciblés ont séparé transport/publication, ajouté une trace publique bornée et préservé l'exception initiale en cas de capture bloquée. Délais UI15s, caméra60°/10s et DEM>100 inchangés. Leur cause générale n'est pas démontrée par les succès instrumentés ; variabilité du renderer CI à conserver comme limite, pas promesse SLA.

Les comptes et la saison sont intégrés et validés localement. L'activation réelle des emails reste distincte : Resend Free retenu, domaine d'expédition prévu `raceatlas.ucthonon.fr`, From `RaceAtlas <notifications@raceatlas.ucthonon.fr>` non vérifié, URL Render réelle inconnue. Aucun email réel, DNS, service, migration distante, déploiement, collecte ou publication finale effectué. Droits fournisseurs, délivrabilité et capacité Free restent à qualifier avant activation autorisée. Le lot8 peut commencer depuis ce main validé.
