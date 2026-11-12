# ACC-01 — validation locale de la fondation privée

Jalon interne : aucun formulaire, route de compte, mot de passe, cookie de session ou export ICS livré ici. Les données synthétiques permettent de tester la persistance sans prétendre qu'un utilisateur est connecté. Le reste du lot 7 demeure indépendant et à développer.

Réutiliser Python 3.12/PostgreSQL 17 et le setup du [README](../../README.md). Vérifier PostgreSQL/processus avant tests ; ne pas initialiser un autre cluster ou réinstaller les caches aveuglément. Les fixtures appliquent migrations/check, downgrade/upgrade/check et tronquent uniquement la DB jetable avec opt-in. Ne jamais pointer une base distante, de développement à conserver ou de production.

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://raceatlas:raceatlas@127.0.0.1:5432/raceatlas_test'
$env:RACEATLAS_DISPOSABLE_DB = '1'
python -m pytest tests/backend/test_planning.py -q --tb=short
python -m pytest tests/backend/test_foundation.py tests/backend/test_catalog.py tests/backend/test_catalog_sync.py -q --tb=short
python -m ruff check raceatlas migrations tests/backend
python -m ruff format --check raceatlas migrations tests/backend
node --test tests/contracts/contracts.test.mjs
git diff --check
```

La migration `c40a7162b901` suit `b7f4208ac112`. Toute migration reste manuelle hors tests, jamais au build/start. Le schéma ajoute uniquement identités et sauvegardes privées ; pas d'invalidation du catalogue public pour ces écritures. Les tests de concurrence ont leurs propres connexions, barrières et délais bornés ; les imports utilisent des observations synthétiques en mémoire.

Interface pour la phase suivante : acteur **Account persistant de la même Session ORM**, chargé par le futur Auth serveur, jamais ID/header public ou instance détachée. Email trim/lower minimal, points/plus-tags conservés, aucune qualification complète RFC ou boîte mail. SavedEntry cible scope seul, statut déclaratif, révision1 puis incrément sur vrai changement ; no-op garde ID/horodatages/révision. Timestamps privés retournés en UTC indépendamment du TimeZone PG. Course dérivée par `entry.scope.race_id` ; pas de réconciliation de favoris par texte/position.

Un compte marqué pour suppression dans la Session est déjà refusé, même avant flush et avec attributs expirés ; le service ne déclenche pas implicitement sa suppression pour décider de l'acteur. Les cibles doivent être des chaînes de 1 à 64 caractères, sans NUL et encodables en UTF-8 ; aucun format UUID imposé. Les refus passent par le domaine générique not_found avant requête, et les tests vérifient la transaction toujours utilisable sans rollback correctif. Cela ne constitue pas un parcours HTTP/authentifié.

Les chemins de tests ne sont pas des mécanismes d'authentification disponibles dans l'application. Pour les preuves et le SHA courant : [handoff](developer-handoff.md), [mission](mission.md), [checkpoint](../coordination/CURRENT_STATE.md). Aucun compte/service email, message réel, DNS, achat ou déploiement autorisé par ces commandes ; expéditeur absent et premier déploiement après lot 8.
