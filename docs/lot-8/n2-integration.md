# N2 — intégration confirmée

[PR16](https://github.com/TheoxProject/RaceAtlas/pull/16) fusionnée le17nov2026 à18:43:20UTC. Head revu **5bda8792dccd419bc445cf8959e9e2b8c9e0f85c**, [APPROVE complet backend+UI](https://github.com/TheoxProject/RaceAtlas/pull/16#issuecomment-6950102292). Merge main **1f1d50b1395eaf271d1a22e255555cc027f34bf1** ; fetch, diff et arbre égal **0ea469ff584d9b3cfa90a16c5e5a8e3e8212142f** vérifiés.

| Gate exact | Résultat |
|---|---|
| integrated44097016097/job134086899571 au head | SUCCESS1019backend485,80s/138frontend |
| Ready44149073337/job134272076185 au même head | SUCCESS1019backend365,11s/138frontend |
| main44150897395/job134278617527 au merge | SUCCESS1019backend467,95s/138frontend |

Statiques, contrats, build et gardes avant/après réussis. Ancien development44096798781 annulé automatiquement et remplacé par integrated sur le mêmeSHA, sans suite requise omise. Aucun succès de développement n'a servi de gate de fusion.

N2 fournit la section Changements récents dans Ma saison, count global et pagination au même snapshot, lecture de toutes les notifications disponibles, compte/scopes isolés et retrait/réajout sans historique ancien. Curseurs F1 et dates extrêmes F2 fermés ; callbacks tardifs/ABA et résultats réseau inconnus protégés. Les politiques d'admission20/60 restent intactes ; l'échec CI429 d9 est conservé et le scénario automatisé utilise une horloge de test qualifiée.

Preuve actuelle Tester : deux navigateurs React compilé→Flask→PG **2PASS60,45s**, vrais synchronize de fixtures ;52messages/50visibles puis ACK52, Bob26 préservé, nouveau2/27, retrait/réajout et prochain3 ; mobile390 absence nonannulée/restauration, clavier/carte/calendrier conservés. Captures desktop/mobile ouvertes réellement. Ruff101/contrats26/rangePASS ; réutilisation backend/frontend précédente nommée dans le rapport après chemins byte-identiques.

Les échecs initiaux de fixture et de groupe React incomplet restent dans le handoff/rapports ; aucune passe relabellisée, aucune garantie de temps constant ou de capacité distante. Lot8 reste en cours avec OPS-E/B/V. Aucun service, DNS, email réel, migration distante, collecte live, déploiement ou tag final activé.
