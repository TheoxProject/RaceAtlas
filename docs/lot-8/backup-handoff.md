# OPS-B — handoff ciblé

PR17, `feature/operations-final-readiness`, base `1f1d50b1395eaf271d1a22e255555cc027f34bf1`. Preuve native Developer complète au codepropre **0f9af1b3a68601b7248d4e4ef2a1c4da9e760886** ; finalisation docs seule ensuite, SHA final communiqué au gel. Aucun APPROVE B présumé ; Reviewer doit refaire sur DEUX bases neuves/autrenonce au SHA figé.

Fichiers : ops/backup_proof.py CLI et machineàétapes ; backup_fixture.py fixtures/domaines/contrôlesHTTPworker ; backup_common.py codeserreurs partagés ; test_backup_proof.py gardes sansSQL/skip ; CI seuleextensionRuff versops ; docsB/checkpoint et précisionhosting. Produit/auth/source/UI/DBschema/pins/selectionCI/permissions inchangés.

## Commandes et résultats

Pythonvenv `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe`, binPG17.11 existants1a1e. Aucune réinstallation, _test/_review/preview nonmutés pour B.

```powershell
python -m ops.backup_proof --pg-bin C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/pgsql/bin --expected-data-directory C:/Users/theop/.codex/worktrees/add4/RaceAtlas/.local-tools/pgdata-lot2-native --source-name raceatlas_backup_src_20261117b0000005 --restore-name raceatlas_backup_dst_20261117b0000005 --output-directory C:/Users/theop/.codex/worktrees/add4/RaceAtlas/.local-tools/backup-proof/20261117b0000005
```

**PASS exit0**, session17219, pas durée native inventée. Ne pas recopier ces noms existants : Reviewer choisit autre16hex inédit.30tables/hashs/4séquences/144structurescontraintes égales,25CHECKdéparses déclarés/336domainesPASS,7DML+rollbackPASS,21APIrestauréesPASS. [Validation et checksum](backup-validation.md), [procédure Windows](backup-local-development.md). Empreinte des trois fichiers outils identique à la preuve pendant docs : `e0317993d87cb8d63e85f28c123e506fdf5b118214cc924c934acaa7ffc9ca25`.

Unités exécutées : `pytest tests/backend/test_backup_proof.py -q --tb=short --junitxml=.local-tools/ops-b-unit-final.xml`39PASS1,29s ; `-k restored_factory`3PASS1,56s ; dernier `-k 'worker or explicit_local_parameters'`10PASS1,09s (`ops-b-worker-exit-final.xml`).51cas distincts au total, groupes chevauchants d’un testenv. Autres groupes31/32/38 sont historiques chevauchants, pas passes additionnelles. Ruffcheck/format `raceatlas migrations tests/backend ops` PASS106 ; diffcheck complet base..HEAD à renouveler aprèscommit. Contrats26E réutilisés à diffnul, app/runtimes immuables ; pas fullbackend local ni N2browsers répétés.

## Quatre échecs préservés (pas relabellisés)

| Nonce | Résultat réel et correction bornée |
|---|---|
| 20261117b0000001 | FAILpréflight inet::text incluait/32, aucune DB créée ; host(inet_server_addr()) garde IPexacte |
| 20261117b0000002 | FAILmanifest textuel après dump/restore, tables/séquences identiques ; comparaisonstructureexacte +DDLbrutprivé+domaines remplace fauxcritère byteDDL ;24casts et1ANDquota constatés indépendamment |
| 20261117b0000003 | FAILDataError22001 au SHAa750propre : sentinelleenum trop longue pourVARCHAR16 avantCHECK ; !1char corrigé,336sondesSELECTreadonly ensuitePASS, pas preuve entière |
| 20261117b0000004 | FAILHTTPRuntimeError au SHA771propre après données/336domaines/7DMLPASS : create_app lit DATABASE_URLenvironavantoverride. WorkeràENVminimalRESTOREexplicite corrige le harnais, aucun patchapp/globalENV |

Rapports1/2 portentbaseb338+empreinteCLI WIP, pas preuve d’outil àb338. Tous dossiers/archives/DBcréées restent privés ignorés, aucune réutilisation/cleanup. Incidentsunitaires : imports/formatRuff corrigés ; workerinitial7PASS1FAIL car make_url ometoptions=vide, canonicalisationattendue corrigée sans autoriseroptionsnonvides/PGOPTIONSambiant. Derniergroupeworker exige exit0 ET resultpassed, rejette exit1mêmesistdoutannoncepassed.

## Gates et limites

EAPPROVE6958216564 acquis. CIa75044160225621 FAIL1055/3 en491,33s +138front : seasonrequestfinished15s/notificationsdesktopcount/mobilecentre, Rootdiagnosticdistinct ; aucun correctifGUI effectué ici, aucune cause déclarée résolue par CI77144162444692 SUCCESS1062/138. CI du code exécuté `0f9af1b`, run44164167525/job134325641968 : SUCCESS1071backend374,56s/138frontend, gardes exactes avant/après. Les deux campagnes suivant a750 sont vertes ; les trois échecs GUI historiques restent inexpliqués et demandent une évaluation ciblée distincte. La nouvelle CI documentaire et le verdict B restent à obtenir.

EnfantHTTP stdinIDsfictifs seulement, envsystèmeminimal/DBURLrestore/PGparamètres explicites, parentinchangé, pas DSN/password enargv/logs ni cookie/CSRFstdout. Passfilevide explicite et refusPG*ambients pourparent ; targetsource avantAlembic et restore avantAPI. Aucunprocessus natifpending ; runtimeclose avantEngine. PG9780conservé, DBsynthétiques nouvelles seulement. Pas production/externalbackup/chiffrement/rétention qualifiés ni email/DNS/live/service/remoteDB/deploy/achat/tag. GelB et STOP pourReviewerindépendant ; V/finalPR17 restent TODO.


## Gel documentaire du 18 novembre

Reprise sans relance : six documents préservés, aucun nouveau test/SQL/proof/GUI. Empreinte des outils comparée au rapport natif5 : identique ; diff nul sur ops/tests/CI et tout code applicatif depuis0f9. Statut natif seulement : PG9780 actif sur clusteradd4/127.0.0.1:55434, aucun démarrage/réensemencement. Aucun Python/Chrome actif à la reprise.

Cette publication modifie uniquement la documentation. Le SHA exact final est transmis au Coordinateur après push, puis GEL/STOP et libération du worktree pour revue B. Rapport borné : `.local-tools/ops-b-native5-public-result.json` ; checkpoint local ignoré : `.local-tools/developer-backup-current.md`. Aucune archive ni donnée privée publiée. Reviewer utilise un nonce neuf, pas celui déjà existant de la commande historique ci-dessus.


## Correction OPS-B-F1 (18 novembre, avant nouvelle native)

Reviewer REQUEST CHANGES P2 au39c879e : is_symlink seul omettait les jonctions Win32. La tentative native Reviewer au39c n’a PAS été exécutée, nonce20261118c0000001 non consommé. Correction : guard_path commun inspecte chaque composant depuis la racine avant résolution/accès, refuse symlink+jonction via pathlib3.12 et erreurs d’inspection. Output/datadir/binaires/archive/passfile couverts ; worker garde le passfile avant toute lecture. Pas protection contre administrateur hostile ni course TOCTOU revendiquée.59unités pures PASS3,28s, sans privilège de création de liens, réseau ou SQL.

La native Developer0f9/nonce0005 reste historique distincte, pas automatiquement validation de F1. Nouveau code propre à publier avant native nonce20261118b0000001 sur deux bases inédites ; résultat encore à acquérir. CI39c44258674236 : FAIL1068/3 en462,99s +138front, trois GUI immuables et aucun testBFAIL ; diagnosticGUI séparé par Root, aucun correctif de ce périmètre ici.
