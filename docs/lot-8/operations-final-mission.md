# Lot 8 — préparation opérationnelle finale

Base vérifiée : `1f1d50b1395eaf271d1a22e255555cc027f34bf1` après intégration N2 et CI main44150897395 verte. Branche `feature/operations-final-readiness`, worktree isolé add4. AGENTS.md, AGENT_WORKFLOW.md et lot-0/delivery.md font foi. [Preuves N2](n2-integration.md).

Le reliquat OPS-E/B/V forme une PR cohérente avec trois jalons. Chaque jalon important est figé pour revue ciblée indépendante ; la fin exige acceptation complète du SHA final, CI integrated, Ready puis main. E et B sont indépendants, V consolide leurs preuves. Cette organisation conserve les tests ciblés en développement et la CI complète à la fusion, sans ajouter de portée produit.

| Jalon | Résultat observable |
|---|---|
| OPS-E | Matrice erreurs/couverture/quotas honnête ; une couture source incomplète vers notifications sans fausse alerte, puis reprise et replay |
| OPS-B | Dump/restauration PG17 entre deux bases locales neuves synthétiques, manifeste/contraintes et API réellement vérifiés |
| OPS-V | Matrice V1 et rapport candidat, preuves applicables au SHA, limites externes et conditions d'activation explicites |

## OPS-E — première tâche bornée

Réutiliser les preuves existantes après comparaison des chemins : couverture après échec/reprise (test_catalog_sync), fenêtres partielles/stales et audit commit incertain, quotas email/admission simulés, replis terrain/DB et activation fermée. Ne pas créer un faux transport FFC429 : le contrat source reste WindowBatch offline.

Ajouter au plus une couture dans `tests/backend/test_ops_errors.py` ou un test existant cohérent : import valide, sauvegarde d'un scope exact, détail incomplet sur clé annoncée, couverture incomplete/dernier succès conservé, course scheduled/present et compteur privé0 ; reprise valide avec vrai delta, couverture consistent_sample et compteur1 du scope suivi ; replay stable. Vrai synchronize et PG/contrats existants, sans PN préparée ni endpoint supplémentaire. Utiliser l'API de couverture et le service/API privé existant quand cela clarifie la preuve.

Ownership Developer E : test de couture, docs errors-validation/errors-handoff et CURRENT_STATE. Aucun runtime/source/auth/UI/ICS/migration/dépendance modifié sans défaut concret présenté au Coordinateur. Ciblés : nouveau test et coutures coverage/recovery pertinentes ; pas nouvelle campagne locale1019 ou navigateurs inchangés. Gel et revue E avant B.

## OPS-B — attribution distincte après revue E

CLI locale proposée `ops/backup_proof.py`, gardes/argv testés dans `tests/backend/test_backup_proof.py`. Avant tout CREATE : host et hostaddr127.0.0.1, port/utilisateur/cluster/data_directory et binaires PG17 attendus, noms source/destination distincts dans un namespace unique et absents, environnement libpq isolé ; aucun détournement via PGSERVICE/PGHOSTADDR/PGOPTIONS hérités. Aucune cible existante, --clean, drop automatique, base distante ou données réelles.

Créer uniquement source neuve avec Alembic b806 et fixtures autorisées, dump custom dans un répertoire privé ignoré, hash/manifeste, puis destination neuve et pg_restore atomique sans owner/privileges. Vérifier identités/faits/versions/contraintes avant les API ; ensuite vrai login fictif/planning/notifications/ICS/public sur la restauration. Les effets légitimes des API ne doivent pas être comparés comme un état initial immuable. Runtime fermé avant Engine.dispose.

Les tests de gardes en CI sont complétés par DEUX preuves natives locales, Developer puis Tester indépendant au SHA exact avec nonces distincts. Cette preuve CLI est annoncée hors suiteCI, sans skip trompeur ; pas installation PGclient en CI ni outil payant. Aucun dump/manifeste privé/credential dans Git ou les artefacts publics. La rétention, le chiffrement et le stockage de sauvegardes réelles restent à qualifier avant exploitation.

Ownership B précisé au transfert : ops module/fixtures minimales, tests, documentation Windows et checkpoint. Si nécessaire, étendre seulement les chemins Ruff CI de ops/ci_selection.py vers ops pour inclure le nouveau module ; aucune permission, garde, sélection conservatrice ou suite réduite.

## OPS-V et gates finaux

Matrice PASS/FAIL/BLOCKED pour toutes les exigences V1, avec SHA/commandes/environnement et réutilisation nommée après diff nul. Le candidat doit distinguer les preuves locales des qualifications non effectuées : Render/Neon Free/TLS/capacité, ResendDNS/délivrabilité, droits FFC/terrain, GPU physique et sauvegarde opérationnelle externe. Aucun tag, release ou déploiement final.

Après gel : aucun fichier suivi modifié pour une progression CI. Rapports et intégration exacte sont consignés dans la PR, puis main/tree/CI confirmés. Les anciens verdicts ne sont jamais transférés implicitement à un nouveau SHA. Reviewer final accepte tout le périmètre livré ; les contrôles main précèdent la déclaration de fin du lot8.

## Environnement et limites

PG17 local add4/.local-tools/pgdata-lot2-native, dernierPID9780/127.0.0.1:55434 ; _test Developer, _review Tester, b806. B utilise deux bases nouvelles distinctes. Vérifier les processus et versions avant réemploi ; pas initdb/reseed aveugle/ancien checkout sur schéma actuel. Caches Python/Node24/pnpm10/browsers1a1e réutilisés. Un seul writer suivi, tests isolés, fermeture runtime avant engines.

Aucun email réel, DNS, achat/upgrade, création de service, mutation distante, déploiement, collecte live ou publication/tag final sans autorisation distincte. Les choix produit majeurs restent au propriétaire. Les quotas inconnus ne sont pas estimés ; checkpoint et arrêt propre si interruption, pas de promesse de reprise automatique.
