# OPS-B — mission bornée et état

[Mission finale](operations-final-mission.md) : preuve locale PostgreSQL17 sur DEUX bases NEUVES synthétiques, pas outil de restauration production. CLI+helperfixtures+testsunitaires+docs, seuleextensionCI Ruffops. Aucun appruntime/route/migration/pin/policy modifié.

Gardes avantCREATE : host=hostaddr127.0.0.1/port55434/userlocal/data_directoryclusteradd4/clientsserveur17, noms src/dst16hex commun distincts et absents, namespacefermé, passfilevideexplicite, refusPG*ambiants, envsousprocessusminimale. current_database source avantAlembic et restore avantfactory/API ; aucun os.environparentmodifié. Pas existingSourceDump/target/--clean/drop/cleanupauto ni compte/serviceexterne.

Cycle : sourcecrééeparrun→b806/fixturesautorisées→manifestecanonique+dumpcustomhash→destinationneuve/restoreatomique→données/PK/faits/séquences/structurecontraintes exactes→domainesCHECK+refusDML/rollback→vraiesAPIauth/planning/notifs/ICS/public dans enfantisolé. DDLbruts source/restauré privés ;25diffs connus deparser (24casts/1ANDquota) déclarés, pas équivalenceCHECKuniverselle. Domaines explicites sur expressionsPG des deuxDB ; inconnu/vérité différenteFAIL. Hasharchive revérifié avantrestore. Runtimefermé avantEngine.

État Developer : **première native complète PASS**, nonce20261117b0000005 au codepropre0f9af1b,30tables/4séquences/144structures/336domaines/7DML/21API. Quatreéchecs antérieurs conservés, [handoff](backup-handoff.md). Unités51cas par groupes nommés, pas suite native cachée/skipCI ; preuve manuelleDeveloper horsCI, Reviewerindépendant autre nonce au SHAfigé obligatoire. [Validation](backup-validation.md), [commande Windows](backup-local-development.md).

E ciblé n’approuvepas B ; B n’approuvepas V/PR17. Prochaine étape : gel documentaire à outilsbyteidentiques aprèsCIcourante puis revueB ; blocagesGUIglobaux à diagnosticdistinct, integrated/Ready/main et acceptationVfinale nécessaires. Archives/manifeste/passfile ignorés privés, aucun Git/CIartifact ; chiffrement/rétention/stockagebackup réels restent nonqualifiés. Aucunmail/DNS/service/DBdistante/livecollecte/deploy/achat/tag autorisé.
