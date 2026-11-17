# OPS-B — handoff WIP, preuve entière encore en attente

PR17 / feature/operations-final-readiness / base1f1d50b1395eaf271d1a22e255555cc027f34bf1. E ciblé APPROVE6958216564 et CI44154102929 acquis, pas verdict B/V. Writer unique Developer, Reviewer indépendant au SHA figé obligatoire ; aucun ancien verdict transféré.

## Interfaces

`ops/backup_proof.py` : ProofConfig, validations pures, préflight identité/absence/versions, targetcurrent_database avantmigration/API, machineàétapes run_proof et CLI. `backup_common.py` partage les erreurs à codes fixes entre exécution -m et helper sans exception brute ; `backup_fixture.py` construit un jeu strictement synthétique, compare domaines des CHECKdéparsesdifférents et teste contraintes/APIs. Aucun import de tests comme bibliothèque, aucun runtimeweb/route/migration/pin changé. CI limité à Ruffops élargi ; sélection/permissions/gardes/artefacts inchangés.

Les gardes ne prétendent pas résister à un administrateur local hostile ou à du code serveur arbitrairement saboté. Le CLI n’est pas un outil production : clusteradd4/loopback55434/userlocal/PG17 seulement, nouveauxnoms+nonce commun, refusPG*ambiants/passfilevide explicite/aucun--clean/drop/existingTarget. Voir backup-local-development.md pour commande complète. Archives et manifestes ignorés privés, pas Git/CIpublic ; pas chiffrement opérationnel prétendu.

## Commandes et preuves acquises

Python existant `C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe` ; pas installation. `python -m pytest tests/backend/test_backup_proof.py -q --tb=short --junitxml=.local-tools/ops-b-unit-final.xml` : **39PASS1,29s**. Unités sansSQL/CREATE/skip, gardes/argv/préflight/domaine/archives ; elles ne prouvent pas à elles seules la restauration. Groupes antérieurs :31PASS2,15s,32PASS2,22s puis4,11s,38PASS1,41s ; chevauchants, ne pas additionner. Ruffinitial imports/longues lignes échoués puis corrigés ; Ruff106/formatPASS sur code récent. Contrats26E réutilisés après diffnul, pas full1020 ni browsers N2 locaux.

Essais natifs conservés :

- Nonce20261117b0000001 : FAIL préflight server_endpoint, avantCREATE ; PostgreSQL inet::text avait/32. Corrigé précisément host(inet_server_addr()). Zéro DB confirmée pour cesnoms, dossierreport ignoré gardé.
- Nonce20261117b0000002 : FAIL manifest_mismatch après dump/restore ; toutes tables/hashs et4séquences égales,144structurescontraintes (72CHECK/30PK/15UQ/27FK),119DDLégaux/25CHECKreformulés (24castsARRAY+1ANDquota). Rapports1/2 portaient SHAdebaseb338 avecCLI WIP et empreintes, PAS preuve d’outil revu àb338. Dossiers/DB/archives conservés, aucune réutilisation.
- Nonce20261117b0000003 : FAIL DataError22001 àSHA PROPRE a750686df80a5e7a9412cabd99d26599e86d8257, phasemanifest ; sonde enum invalide21char débordait VARCHAR16 avantCHECK. Tables/structure/séquences comparées, pas contraintesDML/API. Correctif sentinelle !1char horsdomaines ; deuxunités cibléesPASS1,25s et diagnosticSELECTreadonly sur source/dst0003 :25CHECK/336évaluationsPASS. Ce diagnostic n’est PAS une preuve native entière et ne change pas le statut FAIL3.

Trois unités factorycible supplémentaires PASS1,56s (nonchevauchantes aux39), refusURLetcurrent_database _test/_review avantHTTP. CIa75044160225621 FAIL1055/3 en491,33s +138frontend : troisbrowsers immuables (seasonJanvier requestfinished, notificationdesktopcount, mobilecentre), aucuntestBFAIL ; logs lus et Rootalerté, aucune causeproduit/GPU revendiquée. Native4 : TODO après commitpropre du correctif, CIprécédente maintenantconclue. Nouveau nonce20261117b0000004, deuxDBnouvelles, aucun reuse/cleanup. Runrapport portera SHA et empreinte des trois fichiers outils ; si seuls docs changent ensuite, réutilisation explicitement nommée et comparaisonbyteoutils avantgel, Reviewer refait au SHAfinal exact avec autre nonce.

## Critère de fin B

Exiger exit0 complet : versions17/cluster/absence/targetsource, Alembicb806/fixtures, dumpcustomhash vérifié avantrestore, égalité tables/PK/faits/séquences/structurecontraintes, DDLprivés inspectables et rapport check_sql_text_match=false/diffcount/noms-hashes déclaré. Pas équivalence CHECKuniverselle : domaines explicites positifs/négatifs sur expressionsréelles sourceETrestore (enums/bornes1..100/cardinality/tuplesdiscipline-type/geocacherésultat), écartinconnu ou vérité différente FAIL. Ensuite7scénariosDML PK/UQ/FK/CHECK/RESTRICT/cascade avecSQLSTATEexact et rollbackintégral vérifié, puis authentification de deuxhashsrestaurés/cookies/sauvegardesscopeexact/notificationsread-unread/UIDICS/publicAPI. Runtime.close avantEngine.dispose ; tous effetsAPI interviennent APRÈS comparaisoninitiale, sessions/lastseen/ledger peuvent légitimement évoluer.

Pas données réelles, pas email/DNS/remoteDB/liveFFC/service/deploy/achat/tag. Rétention/chiffrement/stockage de sauvegardes réelles externes restent BLOCKED avant exploitation. B ne termine pas V ; Reviewer B exactSHA puis V/acceptation finale/integrated/Ready/main encore requis.
