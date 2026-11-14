# ACC-UI — comptes et saison dans React

Lot 7, branche `feature/accounts-ui`, checkout isolé `C:/Users/theop/.codex/worktrees/add4/RaceAtlas`, base main validée `b55f4c66e579046c09ee5cd8745fbeed4f566848`. Dépendances ACC-01/ACC-02/PLAN intégrées ; [planning](planning-integration.md), [auth](auth-integration.md), contrats et invariants AGENTS.md font foi. Réutiliser le checkout propre pour ce travail séquentiel ; ne pas modifier les autres worktrees.

## Périmètre et responsabilités

Root cadre, publie la Draft PR et suit les gates. Après transfert explicite, Developer est le seul writer suivi (code/tests/handoffs/checkpoint), jusqu'au gel. Tester lit et teste le SHA exact, sans modifier les sources. Root utilise alors PR/notes ignorées pour le statut. Deux jalons dans la même PR : **UI-1** fondations et parcours compte, revue ciblée ; **UI-2** saison, sauvegardes, export et opérations sensibles, puis revue complète du périmètre final. Aucun verdict intermédiaire ne vaut acceptation du lot.

Fichiers autorisés : frontend bootstrap/main/App, nouveaux client/contrôleur/formulaires/dialog/CSS/tests ; RaceDetails et actions par scope pour UI-2. Flask shell HTML pour les headers ciblés ; `auth/csrf.py` et `planning_http.py` pour la liaison de lecture ci-dessous, contrats/documentation associés ; tests backend/browser et fixtures locales nécessaires. MapView/Calendar seulement pour un raccord minimal justifié, aucune refonte du moteur. Pas de dépendance supplémentaire sans besoin démontré, nouvelle migration ou modification du métier auth/ICS attendue.

## UI-1 — observable et borné

- Bouton Compte et dialog natif accessible, React public toujours monté au même emplacement/key. Carte/calendrier, caméra, mode Altitude/Summit, période, filtres et sélection restent identiques à l'ouverture/fermeture et après connexion. Pas de troisième page de découverte ni refetch public provoqué par l'identité.
- Connexion, inscription email+mot de passe+confirmation, renvoi, oubli, confirmation explicite et nouveau mot de passe en français. Inscription non vérifiée, aucun auto-login après confirmation/reset. Réponse 202 générique sans promesse d'envoi/délivrabilité. Auth désactivée/indisponible ne casse jamais la découverte.
- Avant createRoot et tout effet, capturer en RAM puis supprimer le fragment de l'URL via replaceState. Formes strictes `#confirm-email=<43 URLsafe>` et `#reset-password=<43 URLsafe>` ; valeur malformée refusée sobrement. Aucun POST au montage/ouverture d'un lien. Proof seulement dans X-Account-Proof à l'action explicite, jamais URL/query/DOM/stockage/log/rapport. StrictMode ne réexécute pas le bootstrap impur.
- Nouveaux mots de passe : politique exacte serveur, 15–128 points Unicode et au plus 512 octets UTF-8 ; refuser surrogates isolés, ne pas tronquer/trim/normaliser. Ne pas utiliser maxlength UTF-16 pour la limite Unicode et ne pas appliquer la blocklist aux connexions existantes. Labels/autocomplete, erreurs accessibles et confirmation exacte.
- Client même origine, routes constantes, cookies HttpOnly seuls bearers, credentials same-origin/cache no-store/redirect error/referrer no-referrer. Aucun header privé sur fetch public, MapLibre/DEM/tiers ; aucun token de session JS/webstorage. CSRF reste en RAM.
- Contrôleur séparé du catalogue : génération + AbortControllers + identité attendue ; ignorer les réponses tardives même si abort est ignoré. 401 de login erroné ne purge pas le compte courant ; 401 passive périmée ne purge pas une nouvelle génération ; 403 réauth erronée conserve le compte. Focus/pageshow/visibility revalident raisonnablement sans polling intensif.
- Une intention privée utilise CSRF lié au cookie, puis GETme comparé au compte attendu, puis l'opération avec CE proof ; aucun rafraîchissement silencieux/retry de l'intention sous un autre compte. Pour les lectures privées, ajouter la liaison compatible décrite ci-dessous dès UI-1.
- Shell HTML Flask : X-Frame-Options DENY, CSP directive isolée frame-ancestors 'none', Referrer-Policy no-referrer. Ne pas ajouter de restrictions CSP générales qui cassent workers/terrain. Vérifier les vrais headers de React compilé servi par Flask.

## Liaison des lectures à l'intention UI

Extension technique minimale et compatible : `verify_request(..., *, mutation=True)` conserve son défaut pour toutes les mutations. En mode False, Origin absent est permis, mais Origin fourni et Sec-Fetch-Site restent contrôlés. Dans GETme, GET saved-entries et GET/HEAD calendar.ics, si X-CSRF-Token est **présent**, vérifier son nonce/MAC/expiration/liaison au cookie avant admission/session/snapshot/ledger. Header vide ou invalide =>403, aucun fallback. Sans header, clients GET actuels inchangés. Le proof ne confère aucune identité sans cookie.

UI : CSRF → GETme attendu portant CE proof → GET données/export avec le même proof, puis garde génération avant publication/download. Un switch A→B entre preflight et GET doit refuser avant de lire B ; restaurer A ensuite ne transforme pas ce refus en succès. Pas besoin de nouveau bearer, acteur client, token URL ou identifiant dans l'ICS. Documenter le header optionnel dans le contrat de lecture. Ce raccord répond au nouveau besoin d'intention UI, sans prétendre à un défaut d'autorisation historique du backend.

## UI-2 — saison et compte complet

- Actions pour LE entry_scope affiché : interested, planned, registered, completed, suppression explicite. Libellés français cohérents (Intéressé, Prévue, Inscrit, Terminée). « Inscrit » déclaré par l'utilisateur, pas vérifié FFC. Anonyme : invitation connexion puis nouvelle action explicite, jamais autosave différé.
- Ma saison montre toutes les sauvegardes du compte, sans filtres publics. Détails à partir du snapshot privé du seul scope, règles/restrictions/provenance/incertitudes/localisation conservées ; pas admissibilité inventée ni fusion de scopes.
- Export explicite ICS, planned+registered (« Prévues et Inscrit »), fichier statique sans feed ni nouvelles options. Requête privée liée au contexte ci-dessus, status/type/taille 2MiB vérifiés ; Blob URL éphémère révoquée, nom exact `raceatlas-planning.ics`, aucune publication de réponse obsolète. Expliquer qu'un import antérieur ne se synchronise pas automatiquement.
- Déconnexion courante, tous appareils, changement mot de passe et suppression avec réauthentification/confirmation appropriée. Succès seulement après 204 ; erreur réseau/commit inconnu n'est pas présenté comme rollback ou succès certain. Reset B sous cookie A préserve A si le serveur le préserve ; reset A/révocation traités après vraie relecture. Aucun retry automatique d'écriture.

## Acceptation et preuves

Developer fournit fichiers/SHA/commandes/résultats réels et risques. Tests utiles de bootstrap/politique Unicode/transport/générations ; éviter tests qui recopient simplement le markup. Tests Flask→PG du mode lecture : sans header compatible, bon proof sans Origin accepté, mauvais/expiré/vide/autre cookie refusé avant SQL privé, sans Set-Cookie ; mutations gardent Origin obligatoire.

Vrai navigateur React **compilé → Flask → PostgreSQL jetable**, DevelopmentEmailProvider lu en RAM par la fixture, sans endpoint debug-mail produit. Inscription→lien→scrub avant appels→action explicite→confirmation→connexion ; erreurs, renvoi et reset. UI-2 : deux comptes/devices, scope exact, saison hors filtres, ICS parsé indépendamment, logout/global/change/delete/révocations. Interleavings déterministes : réponse A tardive après B, late401, login erroné conservant A, réauth403, preuve A/cookie B puis retour A sans téléchargement. Pas de simples sleeps pour les barrières.

Desktop et mobile390px : clavier complet/Escape/focus restauré, labels/live errors, scroll jusqu'aux dernières actions, pas overflow. Vérifier caméra noninitiale/zoom/Summit60°, période/filtres/sélection avant/après ; fixture DateProxy seulement (pas page.clock.set_fixed_time). Providers carte/terrain interceptés offline selon map_support existant. Captures synthétiques seulement, aucun HAR ou log de headers/bodies secrets. Arrêter serveurs/browsers/workers puis runtime.close avant Engine.dispose.

Contrats Node, lint/format appropriés, frontend unit/lint/build, PostgreSQL ciblé, browser réel et non-régression publique ; CI développement ciblée à chaque push avec gardes SHA ; CI complète nommée integrated obligatoire au head final avant fusion et sur main après merge. Un development vert ne suffit jamais à la fusion. Geler UI-1 pour revue ciblée puis UI-2 pour acceptation complète finale ; toute modification suivie renouvelle revue/CI. Fusion seulement après gates AGENTS.md et mainCI vert.

## Restrictions et limites

Aucun Resend réel/email/DNS/achat/service/déploiement/DB distante/collecte. Development local/tests, clés fictives seulement. Futur domaine email raceatlas.ucthonon.fr et From non vérifiés, APP_BASE_URL Render inconnue. Lot 7 local et délivrabilité réelle restent distingués ; les préconditions externes de livraison ne sont pas déclarées satisfaites. Lot8 dépendant attend le gate défini et toute décision produit importante reste propriétaire.
