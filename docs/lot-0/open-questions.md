# Incertitudes et décisions avant exploitation

| ID | Incertitude / risque | État et gate |
|---|---|---|
| FFC-01 | Complétude forte charge et partition dense ; filtres réels et plafonds serveur | Partiel : 9=9+0 sur Drôme seulement. Bloque déclaration d'import régional complet ; autorise fixtures |
| FFC-02 | Dates passées ignorées/clampées ; borne future ; format dates | ISO ponctuellement vérifié, pas garantie générale. Toujours comparer fenêtre effective ; incohérence => arrêt de publication de cette fenêtre |
| FFC-03 | Identifiant durable de liste et stabilité | Non établi ; rapprochement ambigu gelé, aucune réaffectation de favori par rang |
| FFC-04 | Alias lorsqu'une saison/numéro source est corrigé | Revue et preuve nécessaires ; UUID interne immuable |
| FFC-05 | Libellés génériques et restrictions complexes | Normalisation uniquement confirmée/versionnée ; sinon ambiguë et exclusion des correspondances de catégories affirmées |
| FFC-06 | Régime précis des droits FFC et des documents | Aucun accord obtenu ; bloque collecte récurrente/régionale et republication publique. Ni utilisateur ni ce lot ne peuvent accorder les droits de tiers |
| FFC-07 | Robots, validateurs HTTP, flux incrémental | Robots vérifié ponctuellement le11novembre ; règles respectées, aucun droit de réutilisation déduit. Validateurs/flux incrémental non établis globalement. [Qualification](../readiness/ffc-qualification.md) |
| FFC-08 | Compatibilité réelle du dialecte HTML synthétique | Échecs reproduits sur calendrier et fiche ciblés : layout_changed/debut et html_structure. Bloque activation de l'import live ; fixtures et travaux indépendants autorisés. [Preuves et suite](../readiness/ffc-qualification.md) |
| OPS-01 | Comptes Render/Neon/GitHub et plafonds financiers effectifs | Non testés ; offres exclusivement gratuites ; garde-fous et approbation propriétaire avant activation |
| OPS-02 | Expéditeur et délivrabilité d'email de récupération | Resend Free choisi ; domaine email déclaré raceatlas.ucthonon.fr et From cible RaceAtlas <notifications@raceatlas.ucthonon.fr>. DNS/clé/envoi/délivrabilité non validés ; aucune activation autorisée, aucun email de changement de course |
| OPS-03 | Support de sauvegarde et restauration | À désigner et tester avant données personnelles réelles |
| MAP-01 | Performance WebGL, mobile, DEM indisponible et licences finales | Lot5 intégré avec WebGL réel, mobile390px, pannes DEM/fond/WebGL et crédits vérifiés. Qualification Summit live et matériel mobile/régional/licences finales restent à achever avant ouverture publique |

Les échecs de source maintiennent les anciennes données avec fraîcheur visible et présence `to_verify`. Une absence n'est pas une annulation. Aucun dépassement facturé ou basculement automatique vers offre payante n'est acceptable ; une indisponibilité est préférable. Les anciennes estimations de quotas ne sont pas une preuve actuelle : relire les documentations officielles et vérifier les comptes à l'étape d'exploitation.
