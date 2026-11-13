# ACC-02B2 — preuves de confirmation et récupération

Base de travail du jalon : **c79c557e32fed3fd56c85ed1ce786f0bd46fde04**, branche `feature/account-authentication`, Draft PR12 non fusionnée. B1 a obtenu APPROVE ciblé exact, 68 tests email +10 sondes indépendantes, quatre rendus inspectés, CI43404533408 SUCCESS589backend176,18s/67frontend et source vérifiée avant/après. Rapport indépendant en PR. Ce verdict ne termine ni auth, ni lot7, ni activation.

Réutiliser Auth A et EmailService B1 ; aucune refonte. Le plan Developer `.local-tools/developer-b2-design.md` fournit des pistes, cette mission borne l'implémentation. Developer seul writer après attribution, puis arrêt au gel exact pour Tester.

## Périmètre attribuable

Services **internes** d'inscription, renvoi, confirmation et récupération, tables privées et migration après d82b9147a120, tests PostgreSQL/simulés et documentation. Fichiers : nouveaux modules `raceatlas/auth/`, ajouts privés `models.py`, nouvelle migration, nouveaux tests account flows/limites et ajustement minimal de fixtures si requis, docs lot7/checkpoint/.env.example pour la clé de limitation. Pas de Flask/routes/serve/frontend, source/catalogue/sync/FFC, ops ou CI. A et B1 restent inchangés sauf interface privée nécessaire démontrée et tests correspondants renouvelés. Pas de corpus password ajouté à ce jalon ; sa politique reste une gate auth finale à cadrer.

## Décisions acquises et invariant de sécurité

- Email + mot de passe saisis, compte non vérifié ; aucun login ou fonction personnelle avant preuve. Confirmation **24h**, usage unique et renvoi ; reset distinct **30min**, usage unique, aucune session automatique et révocation des anciennes sessions au reset.
- Resend Free via EmailService B1, **tous les envois simulés**. Domaine cible `raceatlas.ucthonon.fr`, From futur `RaceAtlas <notifications@raceatlas.ucthonon.fr>`, ni DNS ni Resend vérifiés. APP_BASE_URL URL réelle Render indépendante à renseigner. Aucun compte externe, DNS, clé réelle, email réel, déploiement ou coût autorisé.
- B1 livre les objets/boutons français, formats `/#confirm-email=<token>` et `/#reset-password=<token>`. B2 garantit les preuves réelles qui manquaient derrière ces modèles, sans route encore exposée.

## Contrat de service

1. Réutiliser Account unique/email normalisé ACC01 et PasswordCredential nullable d'A. Inscription nouvelle : hash Argon2 et email_verified_at=None. Réinscription pending : nouveau hash/version/challenge liés atomiquement, ancienne preuve incapable de confirmer le remplacement. Un credential déjà marqué vérifié, même daté dans le futur, n'est jamais écrasé par une inscription. Un pending ne réserve pas irrévocablement l'adresse contre son propriétaire légitime.
2. Table privée de challenge : compte FK CASCADE, purpose confirmation/reset strict, unique compte+purpose, version de credential, hash SHA256 avec domaine de purpose, création/expiration UTC. CSPRNG256bits/43URLsafe, **hash seul en PostgreSQL**, aucune URL/HTML/token brut dans outbox, journal ou repr. Borne exacte exclue : now>=expires refuse. Pas de timestamp fourni par client.
3. Confirmation : relecture sous verrou, hash/purpose/version/expiration valides, preuve consommée et date email vérifiée dans la même transaction ; aucune session émise. Renvoi pending : nouvelle preuve, ancien lien invalide, mot de passe conservé ; un renvoi refusé par limites ne doit pas invalider le lien encore valable.
4. Demande de reset seule : ne change ni credential ni session. Reset prouvé : valider le nouveau mot de passe, modifier le PHC, incrémenter version/révoquer toutes sessions et consommer la preuve atomiquement. Utiliser l'ordre et les primitives A. Version lie aussi les anciennes preuves à leur état : change_password/logout_all les rendent périmées ; documenter ce choix. Erreurs de lien génériques pour absent/expiré/rejoué/mauvais purpose, pas de reflet du secret.
5. Les interfaces internes proposées `request_registration`, `resend_confirmation`, `confirm_email`, `request_password_reset`, `complete_password_reset` sont acceptées. Elles utilisent une Session ORM fournie, **caller possède commit/rollback**, aucun commit implicite ou I/O email sous verrou. Les requests retournent un résultat générique et un intent privé optionnel en mémoire ; l'absence d'intent ne sera jamais sérialisée comme indice d'existence par HTTP.
6. Dispatch via EmailService seulement **après commit réussi**, avec operation UUID opaque stable pour la même opération. Rollback/commit échoué : ne pas dispatcher. Intents non durables, perte sur crash après commit documentée et renvoi comme récupération ; pas de worker/service/outbox de secrets ajouté. Échec provider après commit ne vérifie pas le compte et ne change pas le secret ; réservation de budget conservatrice maintenue.

## Verrous et limites persistantes

Account FOR UPDATE d'abord pour les états auth, relecture populate_existing ; lookup initial sans droit seulement pour identifier l'Account, jamais preuve. Pour limites : **Account → Budget singleton → quota adresse/purpose**, aucun retour Budget→Account. Adresse inconnue peut prendre Budget/quota mais ne verrouille pas un Account ensuite dans cette opération. Aucun flux multi-comptes sous un Budget. Les futurs wrappers HTTP respecteront ce contrat ; pas de connaissance ORM préchargée faisant autorité.

Un INSERT ON CONFLICT suivi d'un verrou peut créer un nouvel Account avant refus de budget. Refus **normal retourné**, pas exception imposant rollback global qui annulerait les compteurs. Retirer uniquement les lignes newly-created de cette opération si inutiles, jamais un pending/compte préexistant ; un savepoint compatible est possible si les compteurs admis restent corrects. Le caller peut volontairement rollback une opération entière, ce qui restaure normalement ses compteurs aussi. Le futur HTTP devra commit les résultats normaux même sans intent.

Valeurs initiales **techniques configurables**, pas décisions attribuées au propriétaire : cooldown **60s** et **3 demandes admises/heure/adresse/purpose**, budget de tentatives d'envoi combinées **80/jour UTC et2400/mois UTC**. Une réservation correspond à un intent, y compris si le transport échoue ensuite ; pas à une réception prouvée. Ces marges sous100/3000 Free ne garantissent pas quota disponible d'un compte partagé/inbound. Refus n'étend pas indéfiniment le cooldown et ne remplace pas une preuve encore active.

Quota adresse/purpose aussi pour les adresses absentes ; HMAC avec clé serveur dédiée stable, minimum32octets, jamais email brut/hash simple à dictionnaire dans les compteurs/logs. Valeur synthétique seulement en tests, clé réelle absente des exemples. TTL **2h**, purge bornée indexée, cardinalité ferme **4096** sous Budgetlock ; saturation refuse conservativement les nouvelles clés, sans supprimer une fenêtre encore active. Budget singleton jour/mois mis à jour sous verrou, pas accumulation illimitée par jour. Les tentatives invalides de token ne doivent pas créer une ligne par token arbitraire ; contrôle global borné possible. La couche HTTP C apportera ses limites d'admission/IP fiable ; ces compteurs internes ne sont pas une protection DDoS distribuée ou une preuve de timing uniforme.

## Adresses et non-énumération

B1 expédie des adresses ASCII ; valider ce sous-ensemble **avant mutation B2** pour éviter de créer un compte impossible à confirmer. Réutiliser normalisation email ACC01 et validation mailbox B1, aucun IDNA/EAI ou changement silencieux d'identité ajouté. Les modèles internes ACC01/A et leurs tests Unicode gardent leur contrat plus large ; la future API d'inscription documentera son sous-ensemble. Les mots de passe Unicode/espaces restent exactement ceux d'A, sans trim/lower/troncature.

Résultats externes futurs génériques pour connu/inconnu/confirmé/limité/panne, sans promesse d'envoi. Erreur de forme peut rester indépendante de l'existence. Ne pas exposer motif interne/intent/account/token. Le dispatch synchrone de ce jalon interne **ne prouve pas** résistance à l'énumération temporelle HTTP ; C devra cadrer et exercer ce point. Les erreurs de stockage inattendues ne sont pas masquées par un broad catch.

## Gate d'acceptation ciblée

- Vrai PG : pending non connectable, preuve valide/24h/30min/juste avant/à/après limite, rejouée/invalide/mauvais purpose/version ; renvoi et remplacement de hash ; aucun compte vérifié écrasé.
- Deux connexions avec barrières bornées et ordre observable : inscriptions même email, double consommation, reset contre login/change/logout_all/delete ; état ORM déjà chargé revalidé. Un seul succès durable ; pas de faux deadlock du harness.
- Reset révoque plusieurs appareils, autres comptes/SavedEntry/source intacts ; catalogue public inchangé. Rollback restaure état et aucune publication avant commit. Intent perdu/erreur de transport simulée ne vaut pas activation ni changement de password.
- Budgets durables/concurrents/jour/mois UTC/cooldown/TTL/cardinalité/refus ; aucun Account inutile au refus pour une nouvelle adresse, état préexistant préservé et compteurs corrects après commit normal. Hash-only DB/erreurs/repr, ASCII refusé avant mutation.
- Upgrade/check/downgradebase/upgrade/check sur DB locale jetable avec opt-in, pins et contrats inchangés ; régression A pertinente et B1 réutilisé après diff. Pas de suite complète backend/browser locale répétée sans risque nouveau.

Developer tient checkpoint/handoff avec preuves réelles/JUnit/code de sortie, commit/push cohérent puis gèle le SHA. Tester indépendant rend verdict sur ce SHA et CI exacte ; aucune clôture PR12/lot7 par ce seul jalon. HTTP/C, UI/planning/ICS et activation réelle restent ultérieurs.

## Contrat de livraison B2

Implémentation et preuves : [handoff des flux internes](account-flows-handoff.md). Session liée à un Engine transactionnel unique seulement ; une Session liée à une Connection externe est refusée avant mutation, car RELEASE SAVEPOINT ne prouve pas commit PostgreSQL. Les intents restent inertes jusqu’au commit racine réussi ; aucun envoi dans les événements. Limite adresse sur heure glissante via tableau de timestamps serveur borné à100, TTL2h/cap4096 inchangés. `AUTH_RATE_KEY` dédié vide dans .env.example. Ces détails techniques ne changent ni les décisions produit ni les restrictions d’activation.
