# Handoff Developer — préparation V1, jalon RDY-02

Branche `feature/v1-readiness`, Draft PR https://github.com/TheoxProject/RaceAtlas/pull/8, base **5f8229245f31ff64f678cad9df331f7302bef76f**. RDY-01 **136768cd6499f18858e27834926bd3bf216150f7** approuvé uniquement sur son périmètre documentaire, CI43031656451 success. Le commit contenant ce handoff est le candidat RDY-02 ; relever HEAD local/distant/PR. Éditions suivies arrêtées après push pour revue ciblée. **Pas de verdict final, aucun merge ou déploiement.**

## Changements

`.github/workflows/ci.yml` conserve jobintegrated, permissions contentsread et tous contrôles dépendances/lint/contrats/frontend/build/Chromium/pytest/migrations. Checkout du head source exact PR ou SHA push, sans credentials persistés. La même garde vérifie HEAD et la refpublique `refs/pull/N/head` anonymement avant et après validation ; une révision périmée échoue. Concurrence annule anciens runs d'une PR. Le pushmain déclenchera les contrôles après intégration ; aucun runmain de cette nouvelle configuration prétendu avant merge.

Sur échec : résumé et annotation liés au SHA, JUnit pytest et seulement sept captures synthétiques connues copiées vers RUNNER_TEMP non caché, upload rétention1jour. Aucun upload global.local-tools/hiddenfiles, provider-altitude, console/env ou données réelles. Pas de permissions supplémentaires, workflow_run privilégié, bot d'écriture, schedule ou déploiement. Pipeline série fail-fast conservé ; aucune réduction des tests.

Nit RDY-01 autorisé : SHA complet rendu copiable dans `docs/lot-5/integration.md`. Checkpoint actualisé, aucun changement applicatif.

## Vérifications locales réellement effectuées

Extraction des scriptsBash du YAML vers fichiers ignorés `.local-tools/ci-check-source-probe.sh` et `ci-stage-probe.sh`, puis `C:/Program Files/Git/bin/bash.exe -n` : PASS pour les deux. Exécution native en lecturepubliqueGitHub, sans helpercredential ni extraHeader :

- HEAD136768cd et PR8 actuelle : PASS.
- SHA attendu000… au lieu du checkout : refus code1 attendu, pas un échec produit.
- HEAD courant mais refPR7 différente : refus code1 attendu, pas une ancienne révision acceptée.
- Branche sans numéroPR (chemin push) : PASS du contrôle local ; pas une affirmation de CI pushmain exécutée.
- Staging des seules captures connues : sept PNG,683478octets, provider-altitude/env exclus. Répertoire isolé référencé dans `.local-tools/ci-probe-temp-path.txt`, aucun fichier existant supprimé.

`git diff --check` PASS. Aucun backend/frontend produit modifié ; tests complets à exécuter par la CI de ce SHA. PyYAML absent des cachesPython interrogés, aucune installation effectuée pour ce seul contrôle et aucune validationYAML locale prétendue. Le succès de plateforme reste indispensable avant revue finale/fusion.

## Revue et prochaine fonction

Tester vérifie SHA/propreté/base, préservation des contrôles et permissions, checkout source exact, gardes début/fin, échec visible, artefacts limités et trigger main. CI réelle du SHA obligatoire. Les sondes négatives locales ne sont pas des résultats rouges de CI, ni un contournement des permissions. Pendant gel, aucun writer.

Après libération de ce jalon : RDY-03/04 configuration RenderFree/NeonTLS, launcherWaitress et guardpreview privé, tests locaux négatifs/integration, procédures migrations/backups séparées et docshosting. Rien de cela n'est encore implémenté ou qualifié ici. Aucun service créé, remoteDB connecté/muté, compte payant, appelFFC ou déploiement. Rapport pré-déploiement propriétaire après lot6 ; finalpublication/tag et activationlive soumis à autorisation.

Références primaires consultées2026-11-11 : [sourceSHA pull_request](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request), [upload-artifact](https://github.com/actions/upload-artifact#uploading-hidden-files). Les copies explicites en répertoire non caché évitent d'activer globalement l'upload des fichiers cachés.
