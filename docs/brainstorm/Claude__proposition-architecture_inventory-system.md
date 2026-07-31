# Architecture du Système de Gestion d'Inventaire

## Document de conception — Tâche 0

---

## 1. Principes directeurs

Quatre règles guident chaque décision de ce document :

1. **Séparation stricte des données** : le Backoffice ne stocke jamais de données produit (nom, prix, description, image). Il ne stocke que des identifiants produit associés à des quantités.
2. **Autorisation côté backend uniquement** : aucune règle de sécurité ne repose sur le frontend. Chaque route vérifie elle-même les droits de l'utilisateur authentifié.
3. **L'agent IA ne doit jamais halluciner** : toute donnée factuelle (produit, stock, branche) transite par un tool MCP. L'agent ne fait que reformuler ce que les tools lui retournent.
4. **Simplicité avant complexité** : à chaque bifurcation technique, on choisit l'option la plus simple qui couvre les exigences du sujet — pas l'option la plus impressionnante.

---

## 2. Vue d'ensemble des services

```
                         ┌─────────────────────┐
                         │   Product API        │
                         │   (Docker, fournie)   │
                         │   lecture seule       │
                         └──────────┬───────────┘
                                    │ HTTP
                    ┌───────────────┴───────────────┐
                    │                                │
         ┌──────────▼──────────┐          ┌─────────▼──────────┐
         │  Product MCP Server  │          │  Backoffice Service │
         │  (tools MCP)          │          │  (FastAPI + auth)   │
         └──────────┬───────────┘          └─────────┬──────────┘
                    │ MCP protocol                    │ SQLAlchemy
         ┌──────────▼───────────┐          ┌─────────▼──────────┐
         │  AI Query Service     │          │  Backoffice DB       │
         │  (agent + tools stock)│◄─────────┤  (PostgreSQL/SQLite) │
         └──────────┬───────────┘  lecture  └──────────────────────┘
                    │ REST            stock (via tool dédié)
         ┌──────────▼───────────┐          ┌──────────────────────┐
         │  Client Web Interface │          │  Backoffice Frontend  │
         │  (public, anonyme)     │          │  (interne, authentifié)│
         └────────────────────────┘          └──────────────────────┘
```

### Les 6 services et leurs responsabilités

| Service | Responsabilité | Accès |
|---|---|---|
| **Backoffice Service** | Auth, gestion utilisateurs, gestion stock | Authentifié (admin/manager) |
| **Backoffice DB** | Stocke users, branches, stock (jamais de données produit) | Privé, accessible seulement au Backoffice Service et au tool stock du MCP/AI Service |
| **Product API** | Source de vérité produit (fournie, lecture seule) | Interne au réseau Docker |
| **Product MCP Server** | Traduit les appels Product API en tools MCP exploitables par l'agent | Interne, appelé par l'AI Query Service |
| **AI Query Service** | Reçoit les questions en langage naturel, orchestre l'agent + les tools, génère une réponse ancrée dans les données réelles | Public via REST, mais logique interne isolée |
| **Client Web Interface** | Page simple (chat ou recherche), anonyme | Public |

**Pourquoi 6 services distincts et pas moins ?** Le sujet impose explicitement que l'AI Query Service soit indépendant du Backoffice (deux bases de préoccupations différentes : gestion interne vs interrogation publique). Le MCP Server est également imposé comme composant à part car son rôle est un rôle de *pont*, réutilisable indépendamment de l'agent qui l'utilise.

---

## 3. Détail par service

### 3.1 Backoffice Service

- **Stack** : FastAPI + SQLAlchemy + Jinja2 (SSR) ou FastAPI + frontend HTML/CSS/JS léger (REST). *Décision d'équipe à trancher — voir section 5.*
- **Responsabilités** :
  - Authentification (login, vérification du hash, émission de session/JWT).
  - CRUD utilisateurs (réservé à l'admin).
  - CRUD stock (réservé au manager, restreint à sa branche).
  - Appel à la Product API pour afficher les informations produit dans l'UI (jamais stockées localement).
- **Ne fait pas** : de logique IA, de génération de texte, d'accès direct au MCP server (ce n'est pas son rôle).

### 3.2 Backoffice DB (schéma minimal)

```
users
├── id (PK)
├── username (unique)
├── password_hash
├── role            -- "admin" | "manager", contrainte CHECK
├── branch_id (FK)  -- NULL pour admin, obligatoire pour manager
├── is_active       -- soft-delete
├── created_at
└── updated_at

branches
├── id (PK)
├── name
├── created_at

stock
├── id (PK)
├── branch_id (FK -> branches.id)
├── product_id      -- identifiant externe, PAS de données produit
├── quantity         -- CHECK (quantity >= 0)
├── updated_at
└── UNIQUE(branch_id, product_id)
```

**Points clés justifiés :**
- Une seule table `users` avec colonne `role` (pas d'héritage de classes) : admin et manager ne diffèrent que par des règles de permission, pas par leur structure de données.
- `branch_id` nullable uniquement pour l'admin — contrainte applicative (vérifiée en code), car une contrainte SQL conditionnelle complexifierait inutilement le schéma pour un gain marginal.
- Contrainte `UNIQUE(branch_id, product_id)` : une ligne = un couple branche/produit, évite les doublons de stock.
- `is_active` (soft-delete) : le login vérifie `is_active = true` en plus du mot de passe. Le stock d'un utilisateur désactivé n'est jamais touché — le stock est rattaché à la branche, pas à l'utilisateur, donc il n'y a rien à faire de spécial ici.

### 3.3 Product API (fournie)

Aucune décision à prendre : c'est un container Docker externe, en lecture seule, exposant `list products` et `get product details`.

### 3.4 Product MCP Server

- **Stack suggérée** : Python + SDK MCP officiel (`mcp` package), FastAPI/Starlette en interne si besoin d'un transport HTTP/SSE.
- **Tools exposés** :
  - `list_products()` → liste résumée (id, nom) pour limiter le bruit dans le contexte de l'agent.
  - `get_product_details(product_id)` → détails complets d'un produit, avec gestion explicite du cas "non trouvé".
  - `get_stock_by_product(product_id)` → *(extension du MCP, voir 3.5)* quantité par branche.
  - `get_stock_by_branch(branch_id)` → *(extension du MCP)* liste des produits en stock dans une branche.
- **Gestion des erreurs** : chaque tool retourne une structure explicite en cas d'échec (`{"error": "product_not_found"}` ou `{"error": "upstream_unavailable"}`) plutôt que de lever une exception opaque — l'agent doit pouvoir *lire* l'erreur et la reformuler proprement à l'utilisateur.

### 3.5 Accès au stock depuis l'IA : décision à justifier

**Décision recommandée : étendre le Product MCP Server avec des tools stock**, plutôt qu'utiliser un MCP Toolbox tiers pour bases de données.

| Option | Avantage | Inconvénient |
|---|---|---|
| **Étendre le MCP existant** (recommandé) | Un seul serveur MCP à maintenir et déployer ; contrôle total sur ce qui est exposé (pas de risque d'exposer une requête SQL arbitraire) ; cohérent avec le principe "l'agent ne voit que des tools contrôlés" | Il faut coder soi-même l'accès à la DB depuis le MCP server (mais c'est trivial avec SQLAlchemy) |
| **MCP Toolbox tiers pour DB** | Moins de code à écrire | Risque de sur-exposition (accès générique à la DB) contraire au principe de moindre privilège ; complexité de configuration supplémentaire pour un projet où le besoin est simple (2-3 requêtes fixes) |

Le MCP server stock a donc ses propres tools *dédiés* (`get_stock_by_product`, `get_stock_by_branch`) qui exécutent des requêtes SQLAlchemy **prédéfinies et paramétrées** — jamais de SQL libre généré par l'agent.

### 3.6 AI Query Service

- **Stack suggérée** : FastAPI (léger, async) + client MCP (SDK officiel) + appel à un modèle LLM (API Anthropic par exemple).
- **Architecture interne** :
  1. Réception de la question (REST, un seul endpoint `POST /ask`).
  2. L'agent reçoit la question + la liste des tools disponibles (produits + stock).
  3. L'agent décide quels tools appeler (ex : `list_products`, puis `get_stock_by_product`).
  4. Les résultats des tools sont injectés dans le contexte de génération.
  5. Le LLM génère une réponse *en s'appuyant uniquement sur ces résultats*. Prompt système explicite : *"Ne réponds qu'à partir des données retournées par les tools. Si l'information n'est pas disponible, dis-le clairement."*
- **Traçabilité** : logguer les tool calls (nom + arguments + résultat) pour pouvoir déboguer/démontrer lors de la soutenance — le sujet le demande explicitement ("possible to observe or debug which tool calls are being made").
- **Scope des questions supportées** (section 5, tâche 1) :
  - Détails d'un produit.
  - Disponibilité d'un produit (quelle(s) branche(s)).
  - Liste des produits disponibles dans une branche.
  - Faisabilité d'une liste d'achats multi-produits/multi-quantités (nécessite plusieurs appels `get_stock_by_product` + logique d'agrégation, potentiellement côté agent ou via un tool composite `check_shopping_list`).
  - Toute autre question → réponse explicite "hors du périmètre supporté".

### 3.7 Client Web Interface

- Page simple : champ texte + bouton + zone de réponse.
- Aucune authentification.
- Communication REST avec l'AI Query Service (voir section 4).
- Gestion des états : chargement, erreur réseau, réponse affichée.

---

## 4. Décisions de communication

### 4.1 Backoffice : REST + frontend léger, vs SSR

**Décision recommandée : REST API + frontend HTML/CSS/JS léger.**

- **Avantage** : séparation claire entre logique métier (API testable indépendamment) et présentation ; réutilisable si besoin d'un autre client plus tard ; cohérent avec l'utilisation de FastAPI qui excelle en API REST.
- **Trade-off** : un peu plus de code frontend à écrire qu'avec du SSR (templates Jinja2 générés directement), mais réduit le risque de mélanger logique d'autorisation et logique d'affichage.

*(Alternative SSR acceptable si l'équipe est plus à l'aise avec Jinja2 — les deux sont explicitement permis par le sujet.)*

### 4.2 Client Web Interface ↔ AI Query Service : REST vs WebSocket

**Décision : REST.**

- **Avantage** : chaque question est indépendante (le sujet le précise explicitement, pas d'historique à maintenir) — REST est donc naturellement suffisant et plus simple à implémenter, tester et débugger.
- **Trade-off assumé** : pas de streaming token-par-token de la réponse (moins "vivant" qu'un vrai chat), et légère latence perçue si l'agent met du temps à répondre (mitigée par un indicateur de chargement côté client).
- WebSocket n'aurait de sens que pour du streaming de réponse ou du contexte conversationnel multi-tour — aucun des deux n'est requis ici.

### 4.3 AI Query Service ↔ MCP Tools

**Décision : protocole MCP standard (stdio ou HTTP/SSE selon déploiement Docker), via le SDK officiel côté client (agent) et serveur (Product MCP Server).**

- **Avantage** : standard, découplé, le même MCP server pourrait être réutilisé par un autre agent/service à l'avenir.
- **Trade-off** : ajoute une couche de sérialisation/protocole par rapport à un simple appel de fonction Python direct — jugé largement justifié par l'exigence explicite du sujet d'implémenter un vrai MCP server.

---

## 5. Authentification et autorisation

- **Hashing** : bcrypt (salt automatique + facteur de coût réglable, résiste au brute-force contrairement à un hash rapide comme SHA256 seul).
- **Authentification** : JWT à courte expiration (stateless, simple à vérifier sur chaque route sans stockage de session serveur) — alternative session-based également valable et à documenter selon le choix final de l'équipe.
- **Autorisation** : middleware/dépendance FastAPI qui décode le token, charge l'utilisateur, et vérifie :
  - `role == "admin"` pour les routes de gestion utilisateurs.
  - `role == "manager" AND branch_id == route.branch_id` pour les routes de stock.
  - Utilisateur `is_active == True`, sinon rejet même si le token est valide.
- **Admin unique** : garanti par un script de seed idempotent exécuté au démarrage (vérifie l'absence d'un admin avant d'en créer un), jamais par une route API. Aucune route ne permet de créer un rôle `admin`.

---

## 6. Grounding de l'agent IA (anti-hallucination)

Trois mécanismes combinés :

1. **Tools obligatoires** : le prompt système interdit explicitement de répondre sans passer par un tool pour toute donnée factuelle (produit, prix, stock, branche).
2. **Erreurs explicites remontées** : si un tool retourne "not found" ou "unavailable", l'agent doit le refléter tel quel dans sa réponse ("je n'ai pas trouvé ce produit" / "cette information n'est pas disponible actuellement"), jamais inventer une valeur de remplacement.
3. **Scope de questions défini** : si la question sort du périmètre supporté (section 3.6), réponse standardisée plutôt que tentative de réponse improvisée.

---

## 7. Déploiement Docker

```yaml
services:
  product-api:        # fournie
  backoffice-db:      # PostgreSQL (ou SQLite fichier pour simplicité)
  backoffice-service: # FastAPI + SQLAlchemy
  backoffice-frontend:# HTML/CSS/JS statique ou servi par le backend
  product-mcp-server: # MCP server (produit + stock)
  ai-query-service:   # FastAPI + agent + client MCP
  client-web:         # page publique statique
```

7 containers au total (ou 6 si le frontend Backoffice est servi directement par le Backoffice Service, ce qui est probablement le plus simple). Orchestration via un seul `docker-compose.yml` — la complexité n'augmente pas significativement entre 4 et 7 containers pour un projet de cette taille ; le principal effort est la configuration réseau interne (noms de services comme hostnames) et les variables d'environnement partagées (URLs, secrets).

Aucune charge significative n'est attendue (projet pédagogique) — pas de préoccupation de performance à ce stade.

---

## 8. MVP — ce qui doit exister en premier

**Phase 1 (fondations, non négociable)**
1. Schéma DB + modèles SQLAlchemy + script de seed (admin + 2 branches + stock d'exemple).
2. Authentification + hashing bcrypt + JWT.
3. CRUD stock (manager) + CRUD users (admin), avec autorisation backend.
4. Product API intégrée dans le Backoffice (affichage simple).

**Phase 2 (cœur IA)**
5. Product MCP Server (list + get details) avec gestion d'erreurs.
6. Extension stock du MCP server (2 tools).
7. AI Query Service avec agent connecté aux tools, endpoint REST `/ask`.
8. Client Web Interface basique connectée en REST.

**Phase 3 (si le temps le permet — optionnel)**
- Question "liste de courses multi-produits" (la plus complexe côté agrégation).
- Tests automatisés complets (au minimum : hashing, autorisation, stock).
- Interface Backoffice plus soignée visuellement.
- Rate limiting / logging avancé des tool calls.

**Ne pas faire avant d'avoir la Phase 1 et 2 solides** : streaming WebSocket, historique de conversation, sous-classes Admin/Manager, MCP Toolbox tiers — aucun n'est requis par le sujet et tous ajoutent de la complexité sans bénéfice direct pour les critères d'évaluation.

---

## 9. Limites connues et axes d'amélioration (à mentionner en soutenance)

- Pas de gestion d'historique conversationnel (hors scope assumé).
- Pas de TLS (explicitement hors scope du sujet).
- Rate limiting non implémenté par défaut (mentionné comme amélioration possible).
- Agrégation "liste de courses multi-branches" : logique potentiellement simplifiée en MVP (ex: une seule branche qui satisfait tout, avant d'attaquer la répartition sur plusieurs branches).
