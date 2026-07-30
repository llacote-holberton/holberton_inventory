# Architecture

This document aims at providing more in-depth information on how (and why) the app was built.

## Data management

### Stocks, Users and Branches

As the business requirements imposed to use a "product catalog" provided by an external API, we had the strict constraint of not storing anything else than the Product ID in our database.
Alongside, the business rules implicitely put out of scope the management of branches themselves (creating/deleting it).

As such, our database schema for the v1 is simple on purpose. In a v2 we would probably add additional metadata for users (last logged in, last modified) and possibly computed data on branches to set up a tracking system to follow and historize operations on every part, journalized into a file on system.

```

erDiagram
    BRANCHES {
        int id PK
        string name
    }

    USERS {
        int id PK
        string username
        string password_hash
        string role "admin | manager"
        int branch_id FK "NULL si role=admin"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    STOCK {
        int id PK
        int branch_id FK
        string product_id "réf. externe, pas de FK"
        int quantity "CHECK >= 0"
        datetime updated_at
    }

    BRANCHES ||--o{ USERS : "assigné à (NULL si admin)"
    BRANCHES ||--o{ STOCK : "détient"

```

Note that in stocks only the product id is stored per explicit project requirement.
As such actual exploitation of data requires assembly of product id and its details provided through the external Products API, which contract and specifications can be read [on its repository](https://github.com/hbtn-edu/hbntory-products-api/blob/main/docs/api_contract.md).

Currently the assembly is done in two functional spaces, the Backoffice and the MCP server, as we needed to parallelize to implement features as quickly as possible.
In a v2 it would be probably refactored so that the Backoffice prepares once and for all the products catalog (since it needs it anyways for Managers to add/remove stocks) and expose it on a single API endpoint (with support for batching request and filters to avoid useless load).

## Docker

Why Docker? Because it is a widely popular engine for creating fully isolated environment (named "docker containers") to provide a specific tool or service, while streamlining some important aspects of software management (restraining access for security, exposing on network for communications, making the deployment reproductible for maintenability, abstracting host context for portability).

### Services

- stocks-db: along with a persistent volume stocks-db-data, is the service exposing relational database (driven by official MariaDB image).
- products-api: built on the fly from a public Github repository, using its provided dockerfile.
- internal-api: custom service exposing curated methods to get read-only information from products's stocks.
- backoffice: service exposing access-restricted web interfaces and APIs for humans to manage the "managers teams" (role: Admin) and the stocks for each branch (role: Managers).
- mcp-server: service bridging machine to machine communication, exposing a specific set of informations and methods for AI agent to consume.
- ai-service: custom API relying on a LLM model under the hood to process end-user queries made in natural language and answer them the best it can with the help of tools and resources exposed by mcp-server.
- web-client: small Python based web server dedicated to serving a web interface for end-users and bridging it with the AI agent.

### Source and network composition scheme

```text
                          +-------------------------+
                          |   Browser / End User    |
                          +-------------------------+
                             |                   |
               (Port 8080)   |                   | (Port 8000)
                             v                   v
+------------------------------------+  +------------------------------------+
|             web-client             |  |             backoffice             |
| Default Port: 8080:8080            |  | Default Port: 8000:8000            |
| Source: ./client_web/              |  | Source: ./backoffice/              |
|         Dockerfile.client_web      |  |         Dockerfile.backoffice      |
+------------------------------------+  +------------------------------------+
                 |                                         |
                 v                                         |
+------------------------------------+                     |
|             ai-service             |                     |
| Default Port: 8003:8003            |                     |
| Source: ./ai_service/              |                     |
|         Dockerfile.ai_service      |                     |
+------------------------------------+                     |
                 |                                         |
                 v                                         |
+------------------------------------+                     |
|             mcp-server             |                     |
| Default Port: 8001:8001            |                     |
| Source: ./product_mcp_server/      |                     |
|         Dockerfile.mcp_server      |                     |
+------------------------------------+                     |
           |                      |                        |
           | (Port 5000)          | (Port 8002)            |
           v                      v                        |
+----------------------+  +----------------------+         |
|     products-api     |  |     internal-api     |         |
| Default Port:        |  | Default Port:        |         |
| 5000:5000            |  | 8002:8002            |         |
| Source: Git Repo     |  | Source: ./backoffice/|         |
| (hbntory-prod-api)   |  | Dockerfile.internal  |         |
+----------------------+  +----------------------+         |
                                     |                     |
                         (Port 3306) |                     | (Port 3306)
                                     v                     v
                          +------------------------------------+
                          |             stocks-db              |
                          | Default Port: 3306:3306            |
                          | Source: Image mariadb:latest       |
                          +------------------------------------+

```

## Networking

Each and every service has its internal and external port configurable.
Although technically when run "as Docker composition" services can automatically know each other thanks to Docker's internal hostname resolution relying on service names, it was decided to still make...
- The "Host" port (on the left side of port:port declaration) to allow each component to also be targetable from "outside Docker compose" while giving a nifty way to avoid any potential collision with pre-existing services on project user's machine.
- The "Container" port (on the right side of the port:port declaration) in case it may be simpler for project user to reconfigure ports for easy memorization or harmonizing with infrastructure policy.

So, you could for example configure all "host side" ports to use a small range of ports to make local firewall configuration easier (like 50000 to 50020), and/or decide that "inside container" all components will use the same port 9000.

Please note on that point that the project expects all port values to be provided by filling the related keys in the local environment variables file (.env copied and changed from .env.example).
In case some keys are missing, fallback values are provided at two levels: Docker compose file and inside Python files.
Here is the list of fallback defaults

| Service                         | Host port : container port     |
| :---                            | :---                           |
| MariaDb                         | 3306:3306                      |
| Backoffice UX + DB crud API     | 8000:8000                      | 
| Internal API (Stocks read-only) | 8002:8002                      |
| MCP server                      | 8001:8001                      |
| AI Agent                        | 8003:8003                      |
| Web client                      | 8080:8080                      |


## Sequence diagrams

As all interactions for each interface follow the same process, for Admin interface and Manager interface only one example will be represented in the diagram.

### Admin role operations from UX

<details>
<summary>Example given: create a user</summary>

```

+---------------------+           +------------------------+           +----------------------+
|  Admin Browser UI   |           | Backoffice (FastAPI)   |           |  stocks-db (MariaDB) |
|   (Port 8080/8000)  |           |      (Port 8000)       |           |     (Port 3306)      |
+---------------------+           +------------------------+           +----------------------+
           |                                   |                                   |
           | 1. Click on "Créer l'utilisateur" |                                   |
           |    (Event Listener submit)        |                                   |
           |------------------------------->   |                                   |
           |    HTTP POST /users               |                                   |
           |    Headers: Authorization Bearer  |                                   |
           |    Payload: {username, role...}   |                                   |
           |                                   |                                   |
           |                                   | 2. Valid. JWT & Admin Role        |
           |                                   |-----------------------+           |
           |                                   |                       |           |
           |                                   |<----------------------+           |
           |                                   |                                   |
           |                                   | 3. Hashing password               |
           |                                   |    (passlib / bcrypt)             |
           |                                   |-----------------------+           |
           |                                   |                       |           |
           |                                   |<----------------------+           |
           |                                   |                                   |
           |                                   | 4. SQL Request (SQLAlchemy)       |
           |                                   |    INSERT INTO users (...)        |
           |                                   |---------------------------------->|
           |                                   |                                   |
           |                                   | 5. Validating write & getting ID  |
           |                                   |    SQL OK (Commit)                |
           |                                   |<----------------------------------|
           |                                   |                                   |
           | 6. Response HTTP 201 Created      |                                   |
           |    Payload: UserOut Schema (JSON) |                                   |
           |<----------------------------------|                                   |
           |                                   |                                   |
           | 7. DOM update to add new row      |                                   |
           |    (Form reset + toast notif      |                                   |
           |    + list refresh)                |                                   |
           |-----------------------+           |                                   |
           |                       |           |                                   |
           |<----------------------+           |                                   |

```

</details>

### Manager role operations from UX

Given example to show Server-Sent Events: adding amount to an existing stock (triggering a SSE to update listing for others Managers of the same branch currently connected.)

<details><summary>Add amount to existing stock</summary>

```

+--------------------+      +----------------------+      +--------------------+      +-----------------------+
|     Manager UI     |      | Backoffice (FastAPI) |      | stocks-db(MariaDB) |      | Connected Clients UI  |
|  (Port 8080/8000)  |      |     (Port 8000)      |      |    (Port 3306)     |      |   (SSE Listeners)     |
+--------------------+      +----------------------+      +--------------------+      +-----------------------+
          |                            |                            |                             |
          | 1. Click "Add Stock"       |                            |                             |
          |    HTTP POST /stocks       |                            |                             |
          |    Header: Bearer <JWT>    |                            |                             |
          |--------------------------->|                            |                             |
          |                            |                            |                             |
          |                            | 2. Validate JWT & Role     |                             |
          |                            |    Ensure Branch Scope OK  |                             |
          |                            |-----------------------+    |                             |
          |                            |                       |    |                             |
          |                            |<----------------------+    |                             |
          |                            |                            |                             |
          |                            | 3. SQL Query (SQLAlchemy)  |                             |
          |                            |    UPDATE/INSERT stock     |                             |
          |                            |--------------------------->|                             |
          |                            |                            |                             |
          |                            | 4. DB Commit Success       |                             |
          |                            |<---------------------------|                             |
          |                            |                            |                             |
          |                            | 5. Publish to asyncio      |                             |
          |                            |    Queue (SSE Broadcaster) |                             |
          |                            |-----------------------+    |                             |
          |                            |                       |    |                             |
          |                            |<----------------------+    |                             |
          |                            |                            |                             |
          | 6. HTTP 200 OK Response    |                            |                             |
          |    Payload: Updated Stock  |                            |                             |
          |<---------------------------|                            |                             |
          |                            |                            |                             |
          |                            | 7. Stream event over SSE   |                             |
          |                            |    event: stock_update     |                             |
          |                            |    data: {"branch_id"...}  |                             |
          |                            |--------------------------------------------------------->|
          |                            |                            |                             |
          | 8. Update UI               |                            |                             | 8. Update Live UI
          |    (Reset form & toast)    |                            |                             |    (Highlight row/qty)
          |--------------------+       |                            |                             |-----------------------+
          |                    |       |                            |                             |                       |
          |<-------------------+       |                            |                             |<----------------------+

```

</details>

### Web client

<details><summary>Ask something about stocks/products</summary>

```

+-------------------+      +------------------+      +--------------------+      +-----------------------+      +------------------+
|   Web Client UI   |      |    AI Service    |      |     MCP Server     |      |  Products / Internal  |      |    stocks-db     |
|    (Port 8080)    |      |   (Port 8003)    |      |    (Port 8001)     |      |  APIs (8002 / 5000)   |      |   (Port 3306)    |
+-------------------+      +------------------+      +--------------------+      +-----------------------+      +------------------+
          |                         |                          |                         |                             |
          | 1. Submit Prompt        |                          |                         |                             |
          |    "Stock for Toulouse?"|                          |                         |                             |
          |    HTTP POST /chat      |                          |                         |                             |
          |------------------------>|                          |                         |                             |
          |                         |                          |                         |                             |
          |                         | 2. Query LLM Engine      |                         |                             |
          |                         |    (LiteLLM / Google ADK)|                         |                             |
          |                         |-----[LLM Request]----->  |                         |                             |
          |                         |<----[Tool Call Requested]|                         |                             |
          |                         |                          |                         |                             |
          |                         | 3. Execute MCP Tool      |                         |                             |
          |                         |    `get_stock(branch)`   |                         |                             |
          |                         |------------------------->|                         |                             |
          |                         |                          |                         |                             |
          |                         |                          | 4. Resolve SKU / ID     |                             |
          |                         |                          |    HTTP GET /products   |                             |
          |                         |                          |------------------------>|                             |
          |                         |                          |<------------------------|                             |
          |                         |                          |                         |                             |
          |                         |                          | 5. Fetch Stock Records  |                             |
          |                         |                          |    HTTP GET /stocks     |                             |
          |                         |                          |    Header: X-API-KEY    |                             |
          |                         |                          |------------------------>|                             |
          |                         |                          |                         | 6. SQL Query (SQLAlchemy)   |
          |                         |                          |                         |    SELECT stock BY branch   |
          |                         |                          |                         |---------------------------->|
          |                         |                          |                         |                             |
          |                         |                          |                         | 7. Return Raw Stock Data    |
          |                         |                          |                         |<----------------------------|
          |                         |                          |<------------------------|                             |
          |                         |                          |                         |                             |
          |                         | 8. Structured Tool Output|                         |                             |
          |                         |<-------------------------|                         |                             |
          |                         |                          |                         |                             |
          |                         | 9. Send Tool Results     |                         |                             |
          |                         |    to LLM for synthesis  |                         |                             |
          |                         |-----[LLM Synthesis]--->  |                         |                             |
          |                         |<----[Natural Response]-- |                         |                             |
          |                         |                          |                         |                             |
          | 10. HTTP 200 OK Response|                          |                         |                             |
          |     Payload: {answer}   |                          |                         |                             |
          |<------------------------|                          |                         |                             |
          |                         |                          |                         |                             |
          | 11. Render Chat Reply   |                          |                         |                             |
          |     (DOM Append & Scroll|                          |                         |                             |
          |-------------------+     |                          |                         |                             |
          |                   |     |                          |                         |                             |
          |<------------------+     |                          |                         |                             |

```

</details>
