# OPS-B — IN_PROGRESS, correctif de sonde prêt

2026-11-17 19:44 UTC. Worktree add4, feature/operations-final-readiness/PR17, HEAD/origin `7718399fa9ad9baa4d09b4560d0948b94fa789da`, base/main `1f1d50b1395eaf271d1a22e255555cc027f34bf1`. E APPROVE6958216564 +CI44154102929development1/138 acquis. CI WIP7eca44158520031 SUCCESS ; CIa75044160225621 job134311707156 encorebackendfull au dernier contrôle (statiques/front verts). Aucun deuxièmepush tant qu’elle n’est pas conclue.

| Tâche | État |
|---|---|
| OPS-E matrice/couture erreurs | DONE ciblé, pas verdict finalPR17 |
| OPS-B gardes +preuve native | IN_PROGRESS, trois échecs conservés, native4 attend codecommitté |
| OPS-V matrice/candidat | TODO non attribué |

WIP suivi : sentinelleCHECK ! courte dans backup_fixture.py, unité associée +gardeURL/current_database factory (3unités), documentationmission/handoff et cecheckpoint. Pas produit/auth/source/UI/DBmigration/pin modifié. CLI+fixture+common en ops ; seuleextensionCI Ruff vers ops, permissions/sélection/steps inchangés. Baselines/secrets fixtures uniquement synthétiques.

Preuves :39unitguardsPASS1,29s (.local-tools/ops-b-unit-final.xml), puis3unitésfactory nonchevauchantesPASS1,56s (.local-tools/ops-b-factory-unit.xml), Ruff106PASS. Précédents31/32/38unit sont chevauchants, ne pas additionner. Une lecturediagnostic après correction de sentinelle a évalué336domaines sur les25CHECKdiffs sourceETrestore du nonce3 : PASS ; ce n’est pas une preuve native entière.

Natifs conservés (.local-tools/backup-proof/<nonce>) :
- 20261117b0000001 : FAILpréflight server_endpoint, aucuneDBcréée. inet::text avait/32 ; correction précise host(inet_server_addr()).
- 20261117b0000002 : FAILmanifest_mismatch, source/dst nouvelles dump/restaurées ; tables/hashs et4séquences égales mais deparserCHECKdifférent. Rapports1/2 portentb338base+CLI WIPempreinte, PAS versionCLI revueàb338.
- 20261117b0000003 : FAILDataError22001 àa750propre, avant contraintesDML/APIs. Sondeinvalide21char dépassaitVARCHAR16. Correction !1char horsdomaines, pas CHECK/policyrelâché ; tables/structure/séquences comparées. DB/archives toutes conservées, jamais réutiliséescomme nouvellescibles.

Comparateur retenu : structureexacte144contraintes/type/colonnes/FK/actions/validité/defer ; DDLbruts privés et25diffs connus (24redistributionscastsARRAY+1ANDquota/cardinality). Pas équivalenceCHECKuniverselle. Probes domaines sur expressionsPG source/restauré ; écartinconnu ou vérité différente FAIL. Hasharchive vérifié justeavantrestore. Ensuite7probesDMLauxSQLSTATEexacts et rollback/cascade, puisvraislogin/privés/ICS/public surrestore UNIQUEMENT. Factorycible vérifiée avantHTTP. Ces dernièresétapes ne sont PASencore validées nativement.

Prochain geste sûr : après conclusionCIa750, commit/pushcorrectifPROPRE et notifierSHA, puis UNEpreuveNative4 nonce20261117b0000004 (deuxDBNEUVESsrc/dst, outputmêmenonce). Préflighttargetsource avantAlembic et targetrestore avantAPI, refusPG*ambient/passfilevide explicite/host+hostaddr127.0.0.1/55434/userlocal/PG17/datadiradd4. AucunexistingSourceDump/target/--clean/drop. Ne pas relancerprooffailed àl’aveugle. Developer_test/Reviewer_review/preview EXCLUS deB, PG9780existant conservé ; aucunecommandePython/Chrome en cours.

AuPASSentier : docs/handoff/range, gelB exact et STOP pourReviewerautrenonce/CI ; B n’approuvepas V/finalPR17. Tester mêmeagent reprendaprèsresetowner, aucunverdictBprésumé. Aucunemail/DNS/service/remoteDB/liveFFC/achat/deploy/tag ; chiffrement/rétention/stockagebackup réels NONqualifiés.

2026-11-17 19:47 UTC — CIa75044160225621 CONCLUEFAIL1055PASS/3FAIL491,33s+138frontPASS. Logs lus : vieuxbrowserseasonJanvier requestfinished15s, notificationsdesktopcount1absent15s, notifmobilecaméracentrechangé0,03567deg. Aucun testBFAIL ; aucune causeproduit/GPUconclue, aucunrerunCI ni éditionbrowser horsscope. Rootalerté, gatesPR17restentBLOQUÉSparcesdéfauts àattribuer. CorrectifB39unit1,29s+3factory1,56sPASS nonchevauchants prêt ; commit/pushcodepropre puisNative4nonce20261117b0000004, pasréutilisationDB.

2026-11-17 19:57 UTC — Native4 à771PROPRE nonce20261117b0000004 : FAILHTTPRuntimeError, après30tables/structure144/4séquences/336CHECK/7DMLcontraintes+rollbackPASS. Factoryapp lit DATABASE_URLenvironavantconfigoverride ; aucunAPIréelencore. WorkerHTTPenfant autorisé : ENVminimalDATABASE_URLrestore explicite/PGtargetrevalidé/parentinchangé/stdinIDsfictifs/aucunsecretstdout. Unitésworker initial7PASS1FAIL(options=vide omisparseURL), correctioncanonicalisationcontrôlée+PGOPTIONSvide ; dernier10PASS1,09s, dontexit1avecstdoutsuccessREFUSÉ. CI77144162444692 SUCCESS1062backend374,44s/138front/gardes771avantaprès ; ne clôtpascauses3browsersCIa750FAIL (Rootdiagnosticfutur). Prochain geste : commit/pushworkerpropre puisUNE Native5nonce20261117b0000005 ; pas repriseancienneDB.
