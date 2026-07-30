# Architecture

This document aims at providing more in-depth information on how (and why) the app was built.

## Data management

As the business requirements imposed to use a "product catalog" provided by an external API, 

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

