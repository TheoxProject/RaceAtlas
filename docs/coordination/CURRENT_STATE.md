# OPS-N2A backend — candidat à geler

**17 novembre 2026, 07:55 UTC.** Checkout isolé add4/feature/notifications-interface, [Draft PR16](https://github.com/TheoxProject/RaceAtlas/pull/16). Base/main014bda3480d0f8c0233f8e6f68d0ae82886b83db ; HEAD/origin avant publication finale **d3544eb70caa2903e8dcb4cc2abcec7cd8b1a0ce**. WIP actuel tests/docs seulement, runtime identique au WIP publié.

CI d354 [43932247137](https://github.com/TheoxProject/RaceAtlas/actions/runs/43932247137) **development SUCCESS979backend290,58s/118frontend**, fallback full/statiques/contrats/build/guards ; pas gatefusion ni validation des compléments non encore publiés. Main N1CI43928375559 SUCCESS967/118, [intégration N1](../lot-8/n1-integration.md). Aucun verdict N2A présumé.

| Tâche | État |
|---|---|
| OPS-N1 journal/baselines/projection/sync | DONE intégré/mainCI vert |
| N2A services, routes, contrats, ciblés | Implémenté ; gel/revue ciblée TODO |
| N2B section Ma saison/store/UI/browser | TODO, non attribué avant gate N2A |
| N2 complet, exploitation/backup/candidat V1 | TODO ; acceptation complète/integrated/main requises |

Livré : E virtuelle SavedEntry courant→ScopeChange>baseline→RaceChange LEFT PN, non matérialisé non lu. Count global/page/graphes scope exact au MÊME SELECT snapshot, CTE limit+1 avant joins règles, aucun N+1. Curseur HMAC domaine distinct lié acteur, pagination live sans snapshot durable interrequêtes. ACK un INSERTSELECT/ONCONFLICT de TOUTES les éligibles sous Account lock ; cutoff MVCC de l’instruction, pas timestamp ; read_at ancien préservé. GET/POST privés additifs, CSRF/Origin/cookie/contexte/no-store/204 après commit+close. Contrats et bornes explicites, aucun drop ou projection256 obligatoire. [Mission](../lot-8/notifications-mission.md) / [handoff commandes](../lot-8/notifications-handoff.md).

## Preuves réelles réconciliées, aucun rerun à la reprise

- Services : **4FAIL5,48s** JSON non hashable via unique, corrigé clé composite puis **4PASS4,50s**.
- HTTP initial : **8PASS6,24s** ; Ruff import/F811fixture corrigé, délégation fixture revérifiée **1PASS3,60s**.
- Snapshot/pending/atomicité : **7PASS6,765s**, ops-n2a-snapshot.xml. 1005 éligibles/256 matérialisées, ACK1005 ; vraies barrières PG sur row-lock PN DANS ONCONFLICT, commit source avant/après snapshot avec created_at plus ancien ; timeout rollback, unsave/readd/autrui/Accountdelete, limites.
- Négatifs/HTTP : **10PASS1FAIL5,902s**, ops-n2a-validation.xml. Unique échec = walker OpenAPI exigeait à tort ./ devant auth.openapi.json ; validation locale canonique corrigée sans modification produit.
- Contrat corrigé + Basic/nonverified + coutures auth/admission/contexte : **19PASS7,578s**, ops-n2a-seams.xml. Session68566 terminée exit0 avant interruption ; XML19/0/0/0 relu à reprise, pas de replay des passes.
- Ruff lint/format99 et26contrats publics déjà PASS, à revérifier lors publication ; JSON notifications + refs OpenAPI validés séparément dans tests. Range diffcheck base..HEAD avant/après commit obligatoire.

Developer seul writer suivi, Root PR/CI, Tester STOP/_review réservée. PG9780/127.0.0.1:55434 existant vérifié nativement17nov07:53UTC ; tests précédents exclusivement `_test` b806, aucune nouvelle migration. Aucun Python/Chrome ni commande/test/session pending ; Nodes externes préservés, tous listeners/threads/runtimes/engines de tests fermés. Pas967local/browser/build inchangés répétés.

**Prochain geste sûr : publier le candidat, communiquer SHA exact puis STOP éditions pour revue ciblée N2A et CI courante.** Pas frontend/UI avant gate ; N2 final exige acceptation complète + integrated/main. Modèles/b806/source/ICS/frontend/CI/deps inchangés ; auth seulement raccord route/action admission. Limites : pagination live et timeout SQL, aucune rétention/TTL produit inventée. Aucun email réel/liveFFC/DNS/service/DB distante/deploy/achat/tag final.