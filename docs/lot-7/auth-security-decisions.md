# Décisions techniques préparatoires — auth

Sources primaires consultées le12novembre2026 ; mise en œuvre et validation du jalon non présumées. Les choix produit sont dans [la mission](auth-mission.md). Aucun service/auth/email réel activé.

## Hash de mot de passe

Choix **Argon2id**, `argon2-cffi==25.1.0`, paramètres explicites `memory_cost=19456`KiB, `time_cost=2`, `parallelism=1`, sel aléatoire16octets, tag32octets. L'[OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) propose cette combinaison minimale ; ce choix n'est pas une déclaration générale de conformité. Revalider coût et capacité sur cible autorisée avant activation.

Le module [argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/api.html) offre hash/vérification/inspection, des [wheels](https://argon2-cffi.readthedocs.io/en/stable/installation.html) Windows/Linux et un [guide de paramètres](https://argon2-cffi.readthedocs.io/en/stable/parameters.html). Le Developer devra pin les dépendances transitives et vérifier résolution/compatibilité dans l'environnement projet et CI Linux, sans réinstaller le reste inutilement.

Comparaison locale Windows/Python3.12.14 le12nov18:36UTC, trois secrets synthétiques identiques hashés avec sels nouveaux, aucun hash/secret publié :

| Primitive / paramètres | Hash ms (trois mesures) | Verify ms |
|---|---|---|
| Werkzeug3.1.9 scrypt32768/r8/p3 |1019,39 /1399,60 /1701,76|1035,32 /1698,62 /1759,16|
| Argon2id19456KiB/t2/p1 |20,92 /20,39 /20,54|20,31 /20,59 /20,77|

Les six vérifications correspondent, Argon2 ne demande pas rehash. Le scrypt par défaut Werkzeug32768/r8/p1 n'est pas la combinaison OWASP comparée ; ne pas utiliser un défaut de bibliothèque comme preuve de coût adéquat. La comparaison motive la dépendance dédiée plutôt que ce scrypt lent sur ce poste, sans classement universel des primitives.

Argon installé seulement dans un dossier de recherche ignoré isolé, sans changer venv/requirements du projet : bindings26.1.0/cffi2.1.1/pycparser3.12. 19MiB est le paramètre mémoire, **pas une mesure RSS** ; CPU/RSS/concurrence Render non mesurés. Aucune capacité Free déduite de ces temps locaux. Le jalon devra borner la concurrence KDF, et l'exploitation mesurer les ressources avant autorisation.

## Contrôles à implémenter et vérifier

L'[OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) motive longueur de passphrase, absence de troncature/composition arbitraire, réponses génériques et protection contre abus. Choix initial 15–128 caractères Unicode valides, espaces permis ; la couche HTTP doit borner taille et abus. Une politique de mots courants et ses données/droits devra être explicitée avant acceptation auth complète ; ce premier choix de longueur n'est pas une preuve de robustesse d'un mot particulier.

[Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) motive sessions opaques, expiration serveur idle/absolue et révocation. Choix interne initial 256bits CSPRNG, vérificateur hashé, 7jours absolus/24h idle ; cookies et CSRF seront vérifiés au jalon HTTP. Posséder un Account ORM n'est pas être authentifié.

[Email Validation](https://cheatsheetseries.owasp.org/cheatsheets/Email_Validation_and_Verification_Cheat_Sheet.html) et [Forgot Password](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html) motivent preuve mailbox avant login, consommation atomique/usage unique/expiry, non-énumération et révocation. Le choix propriétaire password-first ne permet pas d'activer un hash d'une autre demande ni d'écraser un compte déjà confirmé. La normalisation minimale ACC-01 n'est pas un validateur email complet ou une preuve de délivrabilité.

[CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) inclut login et session authentifiée, pas SameSite seul. [Flask web security](https://flask.palletsprojects.com/en/stable/web-security/) rappelle les limites de ressources et cookies à définir. Aucun de ces contrôles n'est déclaré livré par cette note ; chaque jalon fournit comportement négatif exercé et limites.
