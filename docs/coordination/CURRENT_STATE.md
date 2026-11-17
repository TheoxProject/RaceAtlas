# OPS-N2B1 — candidat intermédiaire contrôleur/rendu à geler

**17 novembre 2026, 12:56 UTC.** add4/feature/notifications-interface / [DraftPR16](https://github.com/TheoxProject/RaceAtlas/pull/16). HEAD/origin avant publication8581b5b23b52d5c884583eff2e8d84aebea06a35 ; base/main014bda3480d0f8c0233f8e6f68d0ae82886b83db reconfirmés. N2A APPROVE6943153896/F1F2CLOSED ; CI44048466660 development1016backend294,41s/118front/statiques/guards historique, pas validation de l’UI.

N2B1 implémenté : store privé notifications, count global serveur, pagination composites/curseurRAM/allowlist stricte ; loadSeason attend/coalesce listTask ScopeSaveActions derrière dialog puis pipeline entries→notifications avec preuve liée. Acteur/epoch capturés à l’appel et ticket avant attente initiale ; guards après await/publication/catch/finally et avant émission HTTP. ACK204→GET sans faux0 ni retry ; retrait204 filtre CEscope et invalide count horspage. RenduFR des clés changed (delta source déjà différentiel via record_change), comparaison défensive compatible snapshots complets ; provenance/conditions corrélées/to_verify distinct annulé. Carte/calendrier/ICS/backend inchangés.

## Preuves réellement exécutées, sans replay à reprise

- Premier run sandbox :0test/4fork-start timeout, NONPASS ; CSS mauvais cwd échoué sans écrire. Puis commandes natives sans changer Vitest/délais/config.
- Dernier groupe contrôleur : **47PASS3,32s** (notificationsController/privateAccount/season/accountSensitive).
- Dernier groupe React/App : **20PASS11,09s** (SeasonPanel/NotificationsPanel/AccountPanel/App), session98162 finalisée exit0 ; ESLint PASS, build PASS4,44s (avertissement chunk>500KiB déjà connu).
- Préliminaire utilitaire/rendu : **7PASS3,56s** ; groupes précédents13/34/3PASS recoupés, pas additionnés. Sorties retenues `.local-tools/ops-n2b1-observed-checks.md`, commandes exactes [handoff](../lot-8/notifications-handoff.md). Aucun artifact Vitest/JUnit prétendu.

Developer seul writer, Tester STOP. Aucun test/session pending ; reprise native12:54UTC sans Python/Chrome, Nodes externes préservés. Aucun nouveau test/DB/serveur/browser lancé à reprise. N2B2 navigateur réel React→Flask→PG_test avec synchronize fixture reste TODO après gate ciblée N2B1, captures desktop/mobile390 et QA réelles pas encore faites. Pas backend1016local/reinstall. _review réservée, PG9780/55434b806 existants à revalider avant futurPG.

**Prochain geste sûr : publier WIP cohérent et GEL court N2B1, STOP éditions pour revue ciblée lease/store/rendu + CI courante.** Pas acceptation N2 complète : N2B2 puis acceptation complète/integrated/main requises. Aucun email/live/DNS/service/DB distante/deploy/achat/tag.