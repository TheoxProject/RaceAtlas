# Audit FFC — preuves et limites

Date : 2026-11-10. Observations réseau réalisées par le coordinateur, sans authentification ni contournement. Douze GET ciblés au total pour cette qualification, sans archivage du HTML brut ou données de participants. Le présent document conserve uniquement URLs, métadonnées et résultats factuels nécessaires. Ce n'est pas un jeu de données réutilisable.

## Mécanisme établi

Source : https://competitions.ffc.fr/calendrier/ . Lecture directe de fonctions intégrées au HTML : `refresh` construit `URLSearchParams` puis change `window.location.href`; `addToSearch` écarte les filtres vides ; `showOrganisationScroll` révèle dix éléments `.organisation-scroll-hide` déjà présents. Aucune API publique documentée n'est établie. Ce constat ne démontre pas l'absence d'autres endpoints ou plafonds serveur.

Paramètres observés : `nom`, `categorie`, `discipline`, `departement`, `type`, `sexe`, `distance`, `autourType`, `nbjours`, `groupe`, `debut`, `lat`, `lng`, `carte`. `type` désigne le niveau international/national/régional, pas le type sportif CLM/XCO. Valeurs proposées pour `nbjours` : 1 à 14. Une réponse HTTP 200 ne garantit ni l'application des paramètres ni la complétude.

## Fenêtres et comptages

Les liens suivants sont les requêtes observées ; leur contenu est évolutif. Horodatages UTC. « Clés » signifie paires saison/numéro distinctes repérées dans le calendrier, pas nombre de manifestations.

| UTC le 10 novembre | Requête | HTTP | Période affichée | Compte affiché / clés |
|---|---|---|---|---|
| 09:52:01.4968116Z | [ISO 10 novembre, 14 jours, Drôme](https://competitions.ffc.fr/calendrier/?departement=26&debut=2026-11-10&nbjours=14) | 200 | 10–23 novembre | 9 / 9 |
| 09:52:01.9136341Z | [ISO 10 novembre, 7 jours, Drôme](https://competitions.ffc.fr/calendrier/?departement=26&debut=2026-11-10&nbjours=7) | 200 | 10–16 novembre | 9 / 9 |
| 09:52:02.2461985Z | [ISO 17 novembre, 7 jours, Drôme](https://competitions.ffc.fr/calendrier/?departement=26&debut=2026-11-17&nbjours=7) | 200 | 17–23 novembre | 0 / 0 |
| 09:52:02.7507022Z | [ISO 10 novembre, 28 jours, Drôme](https://competitions.ffc.fr/calendrier/?departement=26&debut=2026-11-10&nbjours=28) | 200 | 10 novembre seulement ; sélection effective 1 jour | 0 / 0 |

L'union des deux fenêtres de sept jours égale celle de quatorze jours pour ce seul échantillon. La seconde partition est vide : ce contrôle est faible, ne prouve ni une partition dense, ni une complétude annuelle, régionale ou sous forte charge. Statut de couverture : `consistent_sample`, jamais `complete` sur cette base.

Clés retrouvées dans les deux premières fenêtres : `2026/C4126302011`, `2026/C4126302012`, `2027/C4126010002`, `2027/C4126010003`, `2027/C4126010004`, `2027/C4126010005`, `2027/C4126010010`, `2027/C4126010012`, `2027/C4126010013`. Elles servent ici de preuve de comparaison, sans recopier fiches, résultats ou participants.

Autres contrôles ponctuels : `debut=2026-11-11&nbjours=1` et `debut=11/11/2026&nbjours=1` ont affiché sept épreuves le 11 novembre. `debut=09/11/2026` a affiché une fenêtre commençant le 10 ; la cause n'est pas établie. La forme compacte `20261118` a été ignorée et a renvoyé le 10. Utiliser ISO dans un futur adaptateur mais vérifier systématiquement la fenêtre effective, pas seulement la chaîne demandée. Les archives/passés et le comportement aux autres dates restent inconnus.

À 09:50:34/35Z, deux réponses sur `debut=09%2F11%2F2026`, Drôme, 14 et 7 jours avaient les en-têtes `Cache-Control: no-store, must-revalidate, no-cache, private`, sans `ETag` ni `Last-Modified`. Il ne s'agit pas d'une garantie pour toutes les fiches. La comparaison d'empreintes économise des écritures, pas nécessairement des téléchargements.

## Listes et admissibilité

Méthode exacte du comptage : repérer les liens par `/calendrier/competition/(?<s>\d{4})/(?<i>[^/\"'<> ]+)/`, former les paires saison/numéro, trier et dédupliquer ; compteur extrait du `div` dont l'identifiant se termine par `InfoJourSelection`. Les doublons d'affichage ne comptent pas plusieurs fois. Sonde supplémentaire à 09:51:19.9320200Z : `?departement=26&debut=20261110&nbjours=28` a renvoyé HTTP 200, sept clés et le 11 novembre seulement, sélection effective d'un jour. Deux paramètres étant invalides, ne pas attribuer le résultat à une seule cause.

À 09:52:33.3724052Z, GET 200 de [Saint-Sorlin Access](https://competitions.ffc.fr/calendrier/competition/2027/C4126010012/st-sorlin-en-valloire-cyclo-cross-du-moulin-access/). Conteneurs observés : `#epreuvesDiv`, `#epreuvesContenu > .epreuve`. Critères : Access 1 à 4 ; hommes dès 18 ans en fin de saison 2027. Date civile : 11 novembre 2026 ; saison : 2027. Ces règles sont corrélées et ne doivent pas être détachées des catégories.

Aucun identifiant durable de liste n'a été établi dans les attributs `id`/`data-*` sélectionnés par cette extraction ciblée. Cela ne démontre pas son absence dans tout le HTML ou côté serveur, et ne prouve aucune stabilité. Aucun endpoint d'engagement/authentification n'a été appelé pour l'obtenir. Ne jamais prendre le rang « Liste 1 » pour un identifiant garanti.

À 09:52:29.6213643Z, GET 200 de [Rugles](https://competitions.ffc.fr/calendrier/competition/2026/C4927279235/rugles-access-1-2-3-4-clm-le-matin/), sans marqueur de liste/critères retrouvé par l'extraction ciblée. La vue indexée lors de la conception antérieure affichait une liste Access 1 mais ce résultat n'a pas été reproduit live : ne pas le présenter comme état actuel. Un slug ne fournit en aucun cas une preuve d'admissibilité.

## Complétude : protocole futur avant exploitation

1. Limiter les fenêtres à 1–14 jours tant qu'aucun autre contrat n'est établi ; vérifier début, fin et filtre réellement appliqués.
2. Comparer le compteur source, les clés distinctes, les doublons HTML liste/carte et la couverture attendue.
3. Tester une partition dense avec les deux sous-fenêtres non vides, une frontière mensuelle/annuelle et les dates passées si autorisées. L'échantillon actuel ne couvre pas ces cas.
4. Détecter plafonnement, décalage ou paramètres ignorés : marquer la fenêtre `incomplete` et ne pas en déduire une disparition ou annulation.
5. Une fenêtre cohérente ne prouve pas que toutes les courses existent dans la source. Conserver couverture opérationnelle et exhaustivité intrinsèque comme notions distinctes.

## Droits et portée

Les fiches pointent les [mentions légales FFC](https://velo.ffc.fr/mentions-legales/), dont les clauses de réutilisation et de constitution de bases exigent clarification avant exploitation. Leur périmètre rédigé mentionne notamment FFC.fr/inf.ffc.fr ; l'applicabilité exacte au sous-domaine compétitions n'est pas tranchée ici. Aucun droit ouvert n'est présumé. `robots.txt` non vérifié ; absence de vérification n'est ni permission ni interdiction. Pas de contact envoyé, pas de collecte massive, pas d'autorisation FFC obtenue. Les contrats et tests restent utilisables sur données synthétiques.
