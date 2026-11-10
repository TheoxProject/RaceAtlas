# Décisions données et identité — contrat 1.0.0

## Identité

Les `id` RaceAtlas sont opaques et immuables. Ils ne contiennent ni titre, ni date, ni regroupement, ni rang d'affichage. La clé candidate FFC `(source, source_season, source_race_number)` sert au rapprochement, mais sa stabilité historique n'est pas prouvée. Une modification de titre/date/manifestation ne crée pas une nouvelle épreuve. `source_season` reste distinct de l'année de la date civile.

La table future `source_alias` relie plusieurs références attestées à un même ID interne, avec preuve et date de décision. Un changement de saison/numéro ne donne pas automatiquement un nouvel ID : recherche d'un lien explicite ou revue humaine, sinon anomalie non rapprochée. Ne jamais fusionner sur similarité de nom, commune, organisateur ou date. Les favoris conservent leur cible tant qu'une réconciliation attestée n'a pas eu lieu.

Une manifestation regroupe des épreuves seulement lorsque le regroupement est documenté. Modifier `competition_id` ne modifie aucun `race.id`, `scope.id` ou favori. Une manifestation singleton est acceptable en attendant une preuve. Les marqueurs par commune sont une projection d'affichage et ne définissent aucune identité métier.

`entry_scope` est l'unité d'engagement/admissibilité : une liste source, ou l'épreuve lorsque l'admissibilité est réellement publiée à ce niveau. Identifiant interne stable ; `source_list_id` nullable. Si un identifiant durable n'est pas établi, `identity_status=unverified`. L'ordre et le libellé ne sont pas des preuves suffisantes. Toute réorganisation ambiguë impose `needs_review` ; ne pas réaffecter les favoris, ne pas agréger les catégories et ne pas transférer des restrictions automatiquement.

## Admissibilité

Chaque scope contient zéro ou plusieurs règles ; chacune lie un ensemble de catégories à ses restrictions de sexe, âge (et sa référence temporelle), engageur et autres critères. Les règles alternatives ne sont pas aplaties. Exemple : Open 1 hommes 18+ et Open 2 femmes 18+ restent deux règles distinctes.

Le filtre sélectionne des catégories acceptées, pas l'éligibilité personnelle d'un licencié. OU : au moins une catégorie sélectionnée est explicitement acceptée. ET : toutes sont explicitement acceptées par un même scope ; il est permis d'utiliser plusieurs règles de ce scope mais leurs restrictions restent attachées aux catégories correspondantes. Cela n'affirme pas qu'un même individu remplit simultanément toutes ces règles. Jamais d'union entre scopes ou épreuves. L'API restitue les règles témoins et `personal_eligibility=not_evaluated`.

Sans sélection de catégorie, aucun critère de catégorie ne s'applique. Une admissibilité `unknown`/`ambiguous` ne confirme aucune catégorie sélectionnée. Access → Access 1–4 et Open → Open 1–3 uniquement sur une expansion confirmée et tracée ; les libellés bruts demeurent disponibles. Une confirmation partielle doit préciser les catégories connues dans des règles et signaler les autres limites, sans élargissement silencieux.

## Modèle PostgreSQL futur

| Entité | Relations et contraintes essentielles |
|---|---|
| competition | UUID, nom et preuve de regroupement |
| race | UUID ; parent nullable ; discipline ; types multiples ; niveau source ; dates ; commune nullable ; état explicite ; présence source indépendante |
| entry_scope | UUID ; race FK ; clé de liste nullable ; confiance d'identité ; état d'admissibilité |
| eligibility_rule / rule_category | scope FK ; restrictions corrélées ; association catégories ; preuve source et version de normalisation |
| source_record / source_alias | identité source candidate unique, alias vérifiés, URL et contrôle horodaté |
| source_revision | empreinte métier et extrait minimal utile ; jamais page complète ou participants |
| import_run / import_window | fenêtre demandée/effective, filtre, compteurs, verdict et version parseur |
| commune | code INSEE texte, nom, département/région, centre nullable et provenance/version du cache |
| saved_entry | utilisateur + scope uniques ; statut utilisateur, sans validation FFC de l'inscription |
| race_change / notification | révision et portée ; notification unique par utilisateur/changement/cible |

Dates sans heure restent `date`, jamais minuit fabriqué. `end_date >= start_date`. Horaires futurs optionnels avec fuseau explicite. CLM est un type Route. Le statut `cancelled` exige une preuve d'annulation ; `source_presence=missing` implique `to_verify`, pas annulation. Conserver les identités et favoris lors d'un retrait.

## Traçabilité et couverture

Un statut d'annulation déjà sourcé reste conservé même si la fiche disparaît ensuite : `source_presence` exprime l'incertitude du contrôle courant, sans écraser le fait historique. Un échec source ne remplace pas les anciennes données par des valeurs vides.

Conserver URL, date de contrôle, règles sources nécessaires, empreinte métier, version de normalisation et référence de preuve. Exclure comptes à rebours, classement et participants des empreintes et archives. Indexer dates, département, discipline, commune et catégories par scope. Mesurer stockage réel et borner la rétention ; aucune capacité annuelle FFC n'est déduite du petit échantillon.

`coverage.status` : `unknown`, `consistent_sample`, `incomplete` ou `complete`. `complete` signifie uniquement que toutes les fenêtres du périmètre demandé ont passé les contrôles techniques documentés, pas que la FFC connaît toutes les courses existantes. Chaque fenêtre inclut période et département demandés/effectifs, compte affiché et clés distinctes. Divergence ou fenêtre non appliquée => `incomplete`. Le lot 0 ne produit aucune couverture réelle `complete`.
