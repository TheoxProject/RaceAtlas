# OPS-B — exercice Windows local (preuve synthétique)

Ne lancer qu’après attribution explicite B. Aucun rôle production ; ce CLI refuse host/hostaddr différents de127.0.0.1, port différent de55434, user différent de raceatlas_local, cluster différent du disposableadd4. Il refuse TOUT PG* ambiant ; inspecter les noms seulement et régler volontairement sa session de commande, jamais effacer/modifier les secrets système à l’aveugle. Il crée un passfile vide explicite privé, désactive SSL/GSS pour cette seule preuve loopback et fournit les paramètres aux connexions et outils. Pas de changement moteur/auth global. Aucun client à installer : binaires17.11 déjà présents.

```powershell
Get-ChildItem Env:PG* | Select-Object Name
# Choisir un nonce16hex NOUVEAU pour chaque exécution ; ne pas réutiliser les noms ci-dessous.
$proofNonce = '<16hex-inédit>'
& 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.venv/Scripts/python.exe' -m ops.backup_proof --pg-bin 'C:/Users/theop/.codex/worktrees/1a1e/RaceAtlas/.local-tools/pgsql/bin' --expected-data-directory 'C:/Users/theop/.codex/worktrees/add4/RaceAtlas/.local-tools/pgdata-lot2-native' --source-name "raceatlas_backup_src_$proofNonce" --restore-name "raceatlas_backup_dst_$proofNonce" --output-directory "C:/Users/theop/.codex/worktrees/add4/RaceAtlas/.local-tools/backup-proof/$proofNonce"
```

La configuration est volontairement bornée au cluster autorisé. Ne jamais adapter host/port/data_directory vers une base distante pour faire passer la garde. La validation vérifie version/identité/absence puis current_database de la source AVANT Alembic et de la destination AVANT lesAPI. Environnement sous-processus isolé, URL source explicite en mémoire seulement. stdout : résultat/phase/codes/versions/checksums/empreinteoutil/SHA, aucun DSN/motdepasse/token ; stderr outils n’est jamais rejoué dans logs publics. Pas d’email ni fournisseur externe, comptes et clés exclusivement synthétiques.

Artifacts privés ignorés `.local-tools/backup-proof/<nonce>` : empty.pgpass, synthetic.dump, manifest-source/restored, report.json. Ne rien publier dans Git/CI. Chiffrement/rétention/stockage externe de données réelles NONqualifiés ; le dossier hérite des protections du workspace utilisateur, aucune confidentialité cryptographique prétendue. Aucun cleanup/drop automatique ; conserver DB et archive pour audit, nettoyage séparé seulement après noms/autorisation exacts.

Preuve native hors suiteCI : un exit0 exige le cycle entier ET contraintes/APIs restaurées. En cas refus/échec, préserver rapport/étape et diagnostiquer avant un nouveau nonce ; aucun retry jusqu’auvert ou réutilisation destination. Reviewer indépendant doit refaire au SHA figé avec son nonce. Preuve Developer complète au code0f9af1b/nonce0005, voir backup-validation.md ; Reviewer indépendant encore requis. Les unités `python -m pytest tests/backend/test_backup_proof.py -q` sont des gardes sans connexion ni CREATE ; elles ne prouvent pas à elles seules la restauration native. CI couvre Ruffops et ces unités sans testSKIP caché.
