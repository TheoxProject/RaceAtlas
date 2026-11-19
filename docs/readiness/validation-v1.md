# Validation de RaceAtlas V1

La V1 est figée au commit `3967729a21ee8ab8086180e27f1fa24841c54020`. La suite intégrée a passé 1 052 tests backend et Chromium ainsi que 141 tests frontend. Elle vérifie aussi les contrats, le lint, le build React et les migrations PostgreSQL sur une base jetable. [Tag v1.0.0](https://github.com/TheoxProject/RaceAtlas/tree/v1.0.0) · [CI du commit tagué](https://github.com/TheoxProject/RaceAtlas/actions/runs/44500584892/attempts/2)

| Périmètre | Vérification |
|---|---|
| Catalogue et engagement | L’API de carte et la sélection paginée appliquent les mêmes filtres. Les tests PostgreSQL vérifient que le mode ET ne combine pas les conditions de listes distinctes. [Guide du catalogue](../lot-4/local-development.md) |
| Carte et calendrier | Les parcours Chromium exercent le relief Altitude et Summit, le regroupement par commune, les replis en cas de panne cartographique, les semaines ISO, les courses multijours et la préservation de la caméra. [Carte](../lot-5/integration.md) · [Calendrier](../lot-6/integration.md) |
| Comptes et Ma saison | Les parcours couvrent confirmation, récupération, révocation, suppression du compte, isolation entre utilisateurs et export ICS. Les tests substituent un transport e-mail simulé. [Authentification](../lot-7/auth-integration.md) · [Planning](../lot-7/planning-integration.md) · [Interface des comptes](../lot-7/accounts-ui-integration.md) |
| Import et notifications | Les scénarios vérifient le réimport idempotent, la couverture partielle, la reprise et les notifications par liste et par compte. [Journal des imports](../lot-8/n1-integration.md) · [Notifications](../lot-8/n2-integration.md) · [Erreurs et reprise](../lot-8/errors-validation.md) |
| Accès public | Le lanceur sert l’interface et le catalogue sans mot de passe partagé. Les API personnelles exigent une session. La carte, le calendrier et les résultats partagent les couleurs des types d’épreuve. [Ouverture publique, PR 21](https://github.com/TheoxProject/RaceAtlas/pull/21) |
| Rendu Chromium | Les tests desktop réduisent le framebuffer logiciel avant l’exercice du relief Summit et comparent la caméra et le dimensionnement avant et après. [Stabilisation, PR 22](https://github.com/TheoxProject/RaceAtlas/pull/22) |
| Restauration | Une sauvegarde synthétique a été restaurée sur une base locale neuve et vérifiée par le Développeur et le Testeur. [Exercice et limites](../lot-8/backup-validation.md) |

## Données et exploitation

Le chargement FFC 2027 et la qualification technique initiale sont deux opérations documentées. Les droits et le périmètre doivent être établis avant toute collecte récurrente. Une course sans localisation corroborée reste consultable sans marqueur. [Bilan du chargement ponctuel](https://github.com/TheoxProject/RaceAtlas/pull/19#issuecomment-6987381129) · [Qualification initiale](ffc-qualification.md) · [Relevé des premières localisations](https://github.com/TheoxProject/RaceAtlas/blob/v1.0.0/docs/coordination/CURRENT_STATE.md)

L’exploitation d’une instance demande ses propres vérifications de connexion PostgreSQL, de réception des e-mails, de sauvegarde et de quotas sur les services retenus. La CI utilise des jeux synthétiques et ne mesure ni la délivrabilité ni les capacités de l’hébergement. [Hébergement](hosting.md) · [Configuration des e-mails](../lot-7/resend-guide.md)
