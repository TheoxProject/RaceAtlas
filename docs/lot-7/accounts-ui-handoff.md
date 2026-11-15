# UI-2A — Handoff ciblé PR14

Branche `feature/accounts-ui`, [Draft PR14](https://github.com/TheoxProject/RaceAtlas/pull/14), baseb55f4c66e579046c09ee5cd8745fbeed4f566848. Candidat à figer après ce commit ; SHA exact communiqué au push. Gate UI-1 **bbc4e1f09ddb72a8fb4f9d42d08fa712ceb56022 APPROVE**, CI43625467407 development290/85. Checkpoint WIP **e80c0a6e953ea2f23281e4b8de8f230d49fb982f**, CI43627955030 development290backend278,41s/96frontend/gardes exactes ; ne valide pas les nouvelles preuves locales/catch corrigé.

## Livré UI-2A

- Store propriétaire des sauvegardes, ticket d'opération distinct de contextEpoch/acteur, nettoyage immédiat à revalidation/switch ; publication normale ET erreur sous lease complète, contrôlée après await. Pas de listeA sousB ni retry implicite, résultat réseau inconnu impose une lecture explicite.
- ScopeSaveActions : création/modification/retrait sur scope exact/IDopaque encodé, quatre statuts serveur, Inscrit déclaré/nonFFC. Anonyme ouvre connexion puis doit agir à nouveau, aucune sauvegarde différée. Focus revient à Compte si le déclencheur a disparu après login.
- SeasonPanel dans dialog existant : toutes sauvegardes hors filtres publics, détail DTO du seulscope/règles/incertitudes/source/centrecommune, sans témoins inventés. Carte/calendrier/Summit/caméra/période/filtres conservés. **UI-2B export et contrôles sensibles restent TODO/non attribués.**
- Whitelist CI ajoute seulement season-desktop/mobile avec accord Coordinator, contrôles PNG régulier/non-symlink/rétention1jour inchangés. Aucun backend/migration/dépendance modifié.

## Preuves réelles

- Frontend actuel : **30PASS13,01s**, `vitest run src/season.test.js src/privateAccount.test.js src/SeasonPanel.test.jsx src/AccountPanel.test.jsx --pool=threads --maxWorkers=1` ; lint PASS, build5,64s PASS. Réutilisation App9/e80 CI96 pour chemins publics inchangés, pas verdict copié.
- Browser carte/scopes/deuxacteurs/horsfiltres/Summit60°/DEM>100/caméra : **1PASS40,94s**, `.local-tools/ui2a-desktop-complete.xml`.
- Browser calendrier/mobile390/scopes/détailprivé/focus/moisconservé : **1PASS** dans `.local-tools/ui2a-browser-first.xml` (run1FAILdesktop/1PASSmobile59,28s) ; chemin normal inchangé par correction catch tardif, preuve réutilisée explicitement.
- Browser deuxcontextes cookies : **1PASS14,26s**, `.local-tools/ui2a-devices.xml` ; mêmeA voit mêmes sauvegardes, switchB sur device2 ne change pas identité/saisonA sur device1.
- Ruff lint/format82, Node26contrats/diff PASS ; API/modèles/migrations/pins/MapView/Calendar/Filters/source inchangés par diff. Pas fullbackend local. Fixtures_test opt-in vérifient schemaa74, runtimes fermés avant Engines.

Incidents conservés : première attente sélection défaut5s avant finAPI≈6s puis test15s cohérent calendrier (strictcaméra10s inchangé) ; toggleExplorer du test refermait panneau déjàouvert, corrigé conditionnellement sans forceclick. Catch ancienTypeError mêmeepoch reproduit8PASS/1FAIL puis garde ticket+epoch+acteur corrigée. Fork Vitest n'avait démarré aucun test ; exécution threads ciblée sans configuration changée. Ce ne sont pas des passes réétiquetées.

Captures synthétiques **vues** : `.local-tools/accounts-ui-screenshots/season-desktop.png` et `season-mobile.png`. Deuxflows réels depuis carte ET calendrier,2scopes d'une race,2acteurs/statuts distincts et2devices ; aucune email/network réel. Handoff/commandes environnement : [local](accounts-ui-local-development.md). Initiale copie202 corrigée UI1-F1, formulation retenue par le Coordinateur ; rapport initial préservé en Git/PR, pas attribution mot-pour-mot propriétaire.

Prochaineaction : publier/geler ce SHA pour revue ciblée UI-2A et CIdevelopment courante ; STOP éditions ensuite. UI-2B uniquement après nouveau gate. Avant fusion finale PR14 : acceptation complète et **integrated** exact obligatoire puis mainCI. Ni délivrabilité/service/DNS/remoteDB/deploy/collecte ni lot7 complet déclarés. Aucun test/browser/serveur retenu, PG38028 conservé, _review réservé au Tester.
