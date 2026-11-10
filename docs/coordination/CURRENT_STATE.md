# Point de reprise RaceAtlas

- Horodatage : **2026-11-10T20:49:44Z**, lot3 correction2 WIP après tests sync ciblés.
- Branche `feature/auditable-sync`, worktree `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`.
- Base `origin/main` vérifiée `f33d837844abdc51ebcafc066da3c16cb4982f34`. Parent avant correction2 : `228074c231b8ed5c41c1f24602de5eff0cce9679` ; relever HEAD après ce commit/push de checkpoint.
- Draft PR https://github.com/TheoxProject/RaceAtlas/pull/5. Dernier Tester : **REQUEST CHANGES F2/P1 sur228074c** (F1 résolu). CI228074c verte mais périmée après modification ; aucune approbation du nouveau SHA.
- Mission `docs/lot-3/mission.md`, usage/handoff à aligner avant gel final.

## Intégration précédente

Lot2 DONE : PR https://github.com/TheoxProject/RaceAtlas/pull/4, Tester APPROVE `511208b7d5142f708106a3d4a8f51d170fb3e148`, CI success https://github.com/TheoxProject/RaceAtlas/actions/runs/42839321426, merge confirmé `f33d837844abdc51ebcafc066da3c16cb4982f34`, arbre identique au SHA testé. Lots0/1 et politique PR#3 déjà intégrés. Sources/droits FFC live non qualifiés.

| Tâche | Responsable | État |
|---|---|---|
| L3-01 cadrage/PR/checkpoint | Coordinator | DONE |
| L3-02 import/audit/identité | Developer | DONE, F1 corrigé |
| L3-03 communes/cache/intégration | Developer | DONE |
| L3-C2 fraîcheur présence/absence | Developer | IN_PROGRESS ;86sync ciblés PASS |
| L3-04 revue indépendante exacte | Tester | REQUEST CHANGES ancien228074c ; nouvelle revue TODO |
| L3-05 CI/fusion/bilan | Coordinator | TODO |

## Correction2 et preuves actuelles

F2 : anciens alias ou observations entre dernière fiche présente et absence plus récente rétablissaient present ; un item frais planifié mais futur/échoué prêtait une fausse autorité. Rapports/scripts ignorés `.local-tools/tester-report-lot3-228074c.md`, `tester-presence-freshness-lot3-c1.py`, `tester-failed-fresh-alias-lot3-c1.py`.

Repère interne **source_record.presence_checked_at** essentiel pour séparer dernière fiche et dernier contrôle de présence OU absence. Nouvelle migration statique **8a95eb41f220**, après65107930ec01 inchangée : backfill sur audits réels, exclusion d'un positif via n'importe quel alias/fenêtre du même run, réparation conservatrice des égalités uniquement en présence d'une vraie preuve d'absence. Colonne nullable compatible anciens writers/seed, contrainte présence>=fiche. API/sérialisation/contrats inchangés.

Baseline immuable par course au début du run ; historique rejeté avant géocodeur/preuves. Aucun consensus planifié ne donne de fraîcheur. Après succès effectif d'un item frais du run, un doublon historique strictement identique peut être audité **historical_duplicate** sans aucune mutation. Sinon reste stale/error. Égalité de timestamp avec absence : aucune présence réputée plus récente. Absences répétées avancent le repère même déjà to_verify ; dernière fiche et révision métier conservées. Erreur fournisseur : cache/diagnostic conservés mais aucun remplacement de l'item ; fenêtres indépendantes positives toujours autorisées.

**86tests sync ciblés PASS en62,97s**, comprenant migration aller-retour/drift, vrais scénarios de backfill antérieur/égal, positifs via alias, répétition d'absence, échecs futur/fournisseur/stockage et25nouvelles régressions. Ruff lint/format26fichiers PASS ;205tests globaux collectés, **suite complète encore à exécuter**. SQL initial a échoué sur alias réservé `window` (transaction annulée), corrigé ; tests ont ensuite révélé l'alignement nécessaire avant flush de scopes et le replay historique, corrigés avant ces86PASS. Aucun PASS global du nouveau SHA revendiqué.

## Décisions et restrictions

F1 reste protégé : conflits par identité résolue avant mutation, preuves sur baseline stable ; aucun rapprochement par nom/rang. Absence globale différée jusqu'au succès entier du périmètre, présence dédupliquée, centres connus préservés. Cache/provenance hors réseau, rectangle numérique sans preuve GIS polygonale.

Autonomie technique ; consultation pour produit majeur, silence jamais accord. Choix propriétaire futur lot5 explicitement résolu : **Altitude2.5D initial, Summit3D à la demande**. Aucun arbitrage en attente. Aucun achat, déploiement, fournisseur/source live, collecte régionale, mutation distante/production ou publication finale autorisé. Nouvelle migration exécutée uniquement en base locale jetable.

## Environnement/processus

Python3.12.14 `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`. PostgreSQL17.11 actif **127.0.0.1:55434**, cluster `.local-tools/pgdata-lot2-native`, log `.local-tools/postgres-lot2.log`. Bases `raceatlas_lot2_test` Developer / `raceatlas_lot2_review` Tester, utilisateur `raceatlas_local`, URL `postgresql+psycopg://raceatlas_local@127.0.0.1:55434/<base>`, opt-in `RACEATLAS_DISPOSABLE_DB=1`. Réinitialisations réservées aux bases jetables ; aucun test concurrent sur même base. Migration head8a95eb41f220 appliquée en base développeur.

Browser `PLAYWRIGHT_BROWSERS_PATH=C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/browsers`. Dépendances frontend déjà locales ; Vitest local nécessite si fork timeout `--pool=threads --maxWorkers=1` sans config produit changée. Aucun test développeur encore actif à ce checkpoint, cluster laissé actif.

Ne pas réinitialiser le cluster ni utiliser ancien `.local-tools/pgdata-lot2` incomplet ; copie deps partielle `.local-tools/frontend-deps-partial` ignorée. Processus natifs DB/Chromium hors sandbox, Git métadonnées partagées nécessite autorisation. Connecteur PR403 connu, fallback accès Git configuré autorisé sans secret affiché. Aucun rejet auto-review dans cette correction. Ne pas réutiliser aveuglément scripts PR4 pour PR5.

## Prochaine action sûre

Exécuter la **suite globale205tests** sur base Developer, puis contrats/lint/format et aligner usage/handoff/checkpoint sur le vrai périmètre final. Publier candidat complet, figer HEAD et demander nouvelle revue Tester +CI exactes. Ne pas lancer lot4 ni fusionner avant gates. Ce WIP ciblé n'est pas fusionnable.
