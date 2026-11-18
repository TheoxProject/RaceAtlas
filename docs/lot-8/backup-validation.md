# OPS-B — validation locale synthétique

Preuve Developer complète : **PASS**,17novembre2026, codepropre `0f9af1b3a68601b7248d4e4ef2a1c4da9e760886`, nonce `20261117b0000005`. `python -m ops.backup_proof` a terminé exit0 (session17219 ; durée native non chronométrée). Ce résultat n’est ni un verdict Reviewer, ni une qualification de sauvegarde réelle/externe, ni une acceptation finale du lot8.

| Contrôle réellement exécuté | Résultat |
|---|---|
| Client/serveur et cibles avant mutation | pg_dump/pg_restore17.11, serveur170011, host=hostaddr127.0.0.1:55434/userlocal/data_directoryadd4 ; deux noms absents avantCREATE et current_database revalidé source avantAlembic/restore avantAPI |
| Migration/jeu synthétique | b806e44f7901 ;12races/13scopes/2comptes et credentials/3sauvegardes/2RaceChange/4ScopeChange/6PNread-unread/2ledgerICS/1geocache |
| Données restaurées |30tables, hash canonique complet incluant PK/identités/faits privés identique,4séquences identiques ; source et destination neuves de CE run uniquement |
| Contraintes |144structures exactes (72CHECK/30PK/15UQ/27FK), noms/colonnes/cibles/actions/validité/defer/noinherit ; DDLbruts gardés privés séparément |
| CHECK déparsés | check_sql_text_match=false ;25diffs (24castsARRAY,1ANDquota/cardinality), noms/hashes rapportés ;336évaluations des expressionsPG réelles sourceETrestore : domaines enums positifs/négatifs, bornes1..100/cardinality, couplesdiscipline/type, résultatgeocache. Aucune équivalenceuniverselle revendiquée |
| Contrôles DML |7scénarios PK/UQ/FK/CHECK/RESTRICT/cascade, SQLSTATEexacts ; rollback et manifeste intégral vérifiés ensuite ; données d’autrui préservées |
| Application restaurée |21contrôles : publiccatalogue/carte, anonyme401, deux vrais login sur hash restauré/cookies, planning exact2scopesAlice/1Bob, notificationsAlice4dont2nonlues/Bob2nonlues, ICS2événementsAlice/0Bob et UIDstables. FactoryURL/current_database vérifiés avantHTTP |
| Fermeture | WorkerHTTPisolé sans secret enargv/stdout ; runtime.close avantdispose, moteurs fermés, aucun processus de preuve conservé |

ArchiveSHA256 `b92f5f91c8f2d89e24c3b940b085743255ec9ef953c13d8d58d1e73ac4ccd529`, revérifié immédiatement avantrestore. ManifesteSHA256 `a38a06250c7c3f5781f735d3cbd9cd3ddced03965d4e68774ac99d8b8134a927`. Empreinte concaténée ops/backup_proof.py+backup_fixture.py+backup_common.py : `e0317993d87cb8d63e85f28c123e506fdf5b118214cc924c934acaa7ffc9ca25`, revérifiée identique pendant finalisation documentaire. Le SHA final de docs peut différer du SHA d’outil exécuté ; cette réutilisation est explicite et Reviewer doit refaire avec un autre nonce au SHA figé.

Rapport borné ignoré : `.local-tools/ops-b-native5-public-result.json`. Rapport complet noms/hashesCHECK : `.local-tools/backup-proof/20261117b0000005/report.json`. Archive, DDL, manifestes et passfile restent ignorés dans ce dernier dossier ; ne pas les publier en Git/CI. DBconservées : `raceatlas_backup_src_20261117b0000005` et `raceatlas_backup_dst_20261117b0000005`. Aucun cleanup automatique.

Unités : fichier51cas, groupes réels39PASS1,29s puis3factoryPASS1,56s et10worker/envPASS1,09s (un testenv chevauche les39, ne pas additionner52). Ruff106 et formatPASS ; pas nouvelle campagne localefull1020/N2browsers. Les unités ne remplacent pas la native horsCI. Quatre échecs natifs précédents sont conservés et détaillés dans [handoff](backup-handoff.md).

Limites : stockage local utilisateur ignoré, hérite des protections du workspace ; pas chiffrement ni politique de rétention réelle qualifiés. Pas backupimportant, Neon/Render, email/DNS/service/collecte/deploy/achat/tag. La preuve synthétique ne résout pas l’incompatibilité du lecteur FFC réel déjà documentée, ni les qualifications de droits/capacités/fournisseurs. Les trois échecs GUI de CIa750 restent historiques et inexpliqués, à évaluer de façon ciblée ; les campagnes suivantes CI771 et CI0f9 sont vertes. La CI0f944164167525 confirme1071backend374,56s/138frontend avec gardes exactes. E ne valide pas B, B ne valide pas V ; Reviewerindépendant+integrated/Ready/main restent obligatoires.


## Contre-validation de la garde Windows le 18 novembre

La [revue du commit 39c879e](https://github.com/TheoxProject/RaceAtlas/pull/17#issuecomment-6972118788) a constaté que le contrôle des liens symboliques omettait les jonctions Windows. Le testeur s’est arrêté avant toute création de base. Le gardien commun vérifie maintenant chaque composant du chemin avant résolution ou lecture, y compris dans le processus qui teste les API. Les 59 tests ciblés couvrent les jonctions simulées et le refus avant accès.

Deux nouveaux exercices complets ont passé sur le code `958cc3c7fcea5d78b1575c838a9f44dd27ab3c30`, chacun avec ses propres bases neuves. Le développeur a exécuté le nonce `20261118b0000001`. Le testeur indépendant a exécuté `20261118c0000001` en 14,201 s et a revérifié l’archive et les manifestes. Les deux exercices concordent sur 30 tables, 4 séquences, la structure de 144 contraintes, 25 différences de texte de CHECK déclarées, 336 évaluations de domaines, 7 scénarios DML avec rollback et 21 contrôles API. La [contre-revue](https://github.com/TheoxProject/RaceAtlas/pull/17#issuecomment-6972369820) approuve cette preuve au SHA testé et ferme le défaut de jonctions.

Les quatre essais natifs historiques et la première preuve complète au `0f9af1b` restent documentés. Les essais portent sur des archives synthétiques produites par l’outil local. Le chiffrement et la rétention des sauvegardes réelles restent à qualifier avant exploitation.
