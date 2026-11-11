# Qualification FFC limitée — 11 novembre 2026

## Résultat et portée

**L'adaptateur actuel n'est pas compatible de bout en bout avec les deux exemples réels examinés.** Les erreurs sont explicites, sans import ni mutation. Les fixtures restent un dialecte synthétique ; elles ne deviennent pas des fixtures live validées.

Méthode : lecture des mentions légales et de robots, puis deux GET séquentiels ciblés à12:45:38–39UTC. Pages limitées à2Mo en mémoire, détruites ensuite ; aucun HTML brut, jeu de données FFC ou participant archivé. Aucun endpoint d'engagement, login, API ou handler appelé. Seules métadonnées, compteurs structurels et diagnostics sont conservés. Les sondes locales ignorées ne sont pas un mécanisme de synchronisation à réactiver.

## Accès et réutilisation

[robots.txt](https://competitions.ffc.fr/robots.txt) a répondu200. La règle générale interdit `/handlers/*`, `/?login` et `/api/*` ; AhrefsBot est entièrement interdit. Le calendrier n'est pas interdit par la règle générale. Deux GET robots ont été nécessaires, le premier affichage ayant échoué sur l'encodage Windows ; aucune protection n'a été contournée. Le sitemap indiqué n'a pas été consulté. Robots ne constitue pas un droit de réutilisation.

Les [mentions FFC](https://velo.ffc.fr/mentions-legales/) décrivent un usage privé et des restrictions de reproduction/constitution de bases, avec autorisation à clarifier. Leur périmètre déclaré mentionne FFC.fr/inf.ffc.fr ; son application précise au sous-domaine compétitions n'est pas tranchée ici. **Aucun droit ouvert, accord FFC ou autorisation de republication n'est établi.** Aucun contact n'a été envoyé. Collecte régionale/récurrente et diffusion publique restent bloquées.

## Observations techniques

| Exemple et provenance | Faits observés | Adaptateur actuel |
|---|---|---|
| [Calendrier Drôme, 11novembre, un jour](https://competitions.ffc.fr/calendrier/?departement=26&debut=2026-11-11&nbjours=1),12:45:38UTC, HTTP200,131626octets | Un compteur dont l'ID finit par InfoJourSelection ; sept paires saison/numéro distinctes. Aucun input/select avec les noms exacts debut/nbjours/departement attendus par le dialecte. Ces compteurs seuls ne prouvent ni fenêtre effective ni complétude. | `parse_calendar` échoue `layout_changed`, champ `debut`. Aucun constat de disparition ou annulation permis. |
| [Fiche déjà connue Saint-Sorlin Access](https://competitions.ffc.fr/calendrier/competition/2027/C4126010012/st-sorlin-en-valloire-cyclo-cross-du-moulin-access/),12:45:39UTC, HTTP200,102118octets | #epreuvesDiv et #epreuvesContenu présents une fois, une .epreuve. #raceDetails absent, aucun dl.regle ni canonical dans l'extraction ciblée. | `parse_race` échoue `html_structure`, champ html, avant extraction des faits. Le lecteur strict et le conteneur synthétique ne qualifient pas la fiche réelle. |

L'identité saison/numéro de l'URL ne fournit ni catégories, ni date civile, ni identifiant durable de liste. Dates/statuts/localisations et corrélation des critères n'ont pas été qualifiés par ces deux sondes. Les observations ponctuelles antérieures restent dans l'[audit du lot0](../lot-0/source-audit.md), avec leurs propres dates et limites ; elles ne prouvent pas une grammaire live complète.

## Travail nécessaire avant activation

- Établir les droits et le périmètre autorisé ; continuer indépendamment sur données synthétiques tant que cela reste incertain.
- Qualifier sur échantillon autorisé les contrôles effectifs, dates, statuts, communes, disciplines et règles corrélées ; tester changements de structure et champs inconnus.
- Préparer un lecteur tolérant au HTML de présentation tout en restant strict sur les faits, avec fixtures minimales réécrites et autorisées ; ne pas contourner les erreurs par déduction du slug.
- Établir l'identité durable des scopes/listes. Si elle reste inconnue : `unverified`/`needs_review`, aucune réaffectation de favori par ordre ou nom.
- Vérifier la fenêtre appliquée, les partitions denses et les compteurs avant toute conclusion de couverture. Une absence reste `to_verify`, jamais une annulation inventée.

Il s'agit d'une qualification technique partielle et d'un blocage de droits documenté, pas d'une autorisation juridique ou d'un import régional opérationnel.
