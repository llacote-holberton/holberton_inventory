# Holberton Inventory - A proof-of-concept of full-fledged application

## Summary


<details>
<summary><b>Table of Contents (Click to expand)</b></summary>

- [Summary](#summary)
- [How to install and run](#how-to-install-and-run)
  - [Prerequisites](#prerequisites)
  - [1. Downloading](#1-downloading)
  - [2. Compiling](#2-compiling)
- [How to use](#how-to-use)
  - [Starting program](#starting-program)
  - [Usage overview](#usage-overview)
- [Features and limitations](#features-and-limitations)
  - [Supported (v1.0)](#supported-v10)
  - [Not supported (yet)](#not-supported-yet)
  - [Accessible help](#accessible-help)
- [Examples of use](#examples-of-use)
  - [Valid examples](#valid-examples)
  - [Failing examples](#failing-examples)
- [Technical information](#technical-information)
  - [General architecture](#general-architecture)
  - [Process Flow](#process-flow)
  - [Memory management](#memory-management)
- [Testing](#testing)
- [Project constraints and methodology](#project-constraints-and-methodology)
  - [Imposed constraints](#imposed-constraints)
    - [Allowed Functions and System Calls](#allowed-functions-and-system-calls)
    - [Requirements](#requirements)
  - [Project methodology](#project-methodology)
  - [Acknowledgments](#acknowledgments)
- [Technologies Used](#technologies-used)
- [Authors](#authors)
- [License](#license)

</details>

## How to install and run

<details>
<summary>(Click for detailed information on prerequisites, download and installation/configuration/run steps)</b></summary>

### Prerequisite

To run the Hbntory platform, **Docker** and **Docker Compose** are the only core system requirements. Because all services (Backoffice API, External Products API, MCP Server, AI Service, and Frontend) are fully containerized, you do not need to install Python, MySQL, or Node.js locally on your host system.

#### Additional Requirements:
- **Git**: To clone the project repository.
- **Modern Web Browser**: Chrome, Firefox, Edge, or Safari to access the Backoffice Web UI and AI Client.

---

#### Installing Docker on your OS

##### Windows 10
1. Download and install **[Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/)**.
2. During installation, make sure the **Use WSL 2 instead of Hyper-V** option is checked.
3. Restart your computer after installation completes.

##### Windows Subsystem for Linux (WSL / WSL 2)
1. Install Docker Desktop on Windows (as described above).
2. Open Docker Desktop, navigate to **Settings > Resources > WSL Integration**.
3. Toggle the switch to enable integration for your installed Linux distribution (e.g., Ubuntu).
4. Open your WSL terminal; `docker` and `docker compose` will now be available directly.

##### Debian-based Linux (Ubuntu, Debian, Mint)
Run the following commands in your terminal:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Note: Log out and log back in for the group membership change to take effect.
```

##### Arch-based Linux (Arch Linux, Manjaro)
```
sudo pacman -Syu docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Note: Log out and log back in for the group membership change to take effect.
```

### 2. Configuring and running

Hbntory uses Docker Compose to orchestrate all microservices. Configuration is driven entirely through environment variables defined in a `.env` file at the root of the repository.

---

#### Step 1: Environment Configuration (one-shot)

Copy the provided `.env.example` file to create your local `.env` configuration:

```bash
cp .env.example .env
# If you want to edit in command line with vim
vim .env
```
Open with your favorite GUI text editor and adjusted the required values.

##### WARNING about CRITICAL CONFIGURATION VALUES
Before launching the stack, you must update the following placeholder values in your .env file:
- DB_ROOT_PASSWORD & DB_HBNTORY_USER_PWD: change these from the default placeholders to secure passwords.
- INTERNAL_API_KEY: security key used by the MCP Server to communicate with the Backoffice API.
  You can generate a secure random string using Python if you have it installed:  
  `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- JWT_SECRET: used by the Backoffice API to sign authentication tokens.
  Generate a unique secret string using the same command above.
- LLA_MODEL_NAME: provide here a "machine name" for the desired model (confer Annex 1 for more information) FIXME change .env.example value for ollama/llama3.
- LLM_MODEL_API_KEY: provide your API key for the configured LLM provider

For more information on LLM configuration specifically, please confer the Annex 1: choosing your LLM model (FIXME ADD ANNEX either inline at document end or as a separate document in docs.).


# Step 2: Managing the environment (repeatable)

NOTE: all the following commands expect you to run them from the project's root so the 'compose' command automatically finds the related docker-compose.yml file.
Otherwise you will need to specify the path to the compose file.

## Starting
To build all container images and start all microservices, run:
`docker compose up -d --build`

What does it do?
- docker: name of the "containarization tool" which allows you to create and run apps and operating systems in a total isolation.
- compose: one of the first level commands of docker: instructs it to find file(s) with specific name(s) in current filetree and parse them to get a series of instructions to create several "containers" lumped together. Here it will automatically target the "docker-compose.yml"
- '--build': forces the composition process to double-check the files which define how each container should be created, and (re)create them if need be.
- '-d': means "detached mode", aka the compose process will tell you about what it is doing on the terminal while working but when finished will "give terminal back to you". Without this option, the terminal would be "locked" to show runtime information. Which is a mode usually kept for debugging.

## Monitoring

You can check the status of all running containers at any time with:
`docker compose ps` (ps standing for "process status")
You can also check the logs of the containers by doing the following command, with or without a service name as parameter.
`docker compose logs <optional:name-of-service-as-defined-in-compose-file>`

## Stopping
To stop the stack without losing any information, just run this.
`docker compose down`.

## Deleting all information (containers AND database)

If you want to completely and cleanly uninstall this project (or just restart it from scratch), you can simply do `docker compose down -v`. The -v option means "Volume deletion" and implies that the persistent storage for database will be deleted from your machine.

</details>

## How to use

### Starting program
* For a "one-shot manual execution": (all-in-one automatic demo, OPTIONAL ONLY IF WE HAVE ENOUGH TIME)
* Otherwise run FIXME 

### Usage overview
Once compiled (e.g. as an executable file shs.out) you can manually run it (confer [Starting program](#starting-program) section) to use it in interactive mode.  
For examples of use please go to [Examples of use](#examples-of-use)

## Features and limitations

As this was a short-timed and severely constrained project tailored for pedagogy first, it is simple by design.

### Supported (v1.0)

Simple management and query of product stocks through the combination of a persistent database to store stock informations, access-restricted web interfaces to manage stock for each company's store ('branch'), and a public interface for anyone to learn about products and their potential availability across branches.

#### Multi-Branch & Inventory Core Management
- **Branch-Specific Stock Tracking**: Manage and inspect stock quantities independently per physical or virtual store branch.
- **Atomic Stock Adjustments**: Fast and secure addition and removal of stock items with built-in validation (e.g., preventing negative inventory balances).
- **Product Catalog Integration**: Seamless integration with external product reference APIs, supporting instant lookups by numeric Product ID or alphanumeric SKU.
- **Discontinued Item Protection**: Automatic validation preventing stock additions for phased-out catalog items while preserving existing inventory records.

#### Real-Time Synchronization (Server-Sent Events)
- **Live UI Updates**: Pub/Sub architecture built with Python `asyncio.Queue` streaming stock modifications live via **Server-Sent Events (SSE)**.
- **Zero-Polling Reactivity**: Connected Manager dashboards dynamically update quantities and alert visual states across open browser sessions in real-time without full page refreshes.

#### Security & Role-Based Access Control (RBAC)
- **JWT Authentication**: Stateless authentication issuing signed JSON Web Tokens (`/login`, `/whoami`).
- **Strict Role Isolation**:
  - **Admin**: Full access to global user management (create, activate/deactivate, reset passwords), global branch listing, and manager assignments.
  - **Manager**: Strict scope isolation enforcing access exclusively to their assigned branch's stock data.
- **Inter-Service Authentication**: Protected internal API communication secured with static API key headers (`X-API-KEY`) between the MCP Server and Backoffice.

#### AI Assistant & Model Context Protocol (MCP) Integration
- **Natural Language Inventory Queries**: Chat-based AI assistant capable of answering complex inventory questions and executing stock checks using natural language.
- **FastMCP Integration**: Custom MCP server exposing structured **Tools** (`get_stock`, `list_branches`, `get_all_branch_stocks`) and **Resources** (`inventory://catalog-summary`) directly to the LLM agent.
- **Multi-LLM Provider Support**: Powered by LiteLLM / Google ADK, allowing seamlessly swapping between 100+ LLMs (OpenAI, Google Gemini, Anthropic, NVIDIA NIM, Groq, local Ollama, etc.) via simple environment configuration.

#### Containerized Architecture & Portability
- **Fully Orchestrated Stack**: 6-container Docker Compose setup (`stocks-db`, `products-api`, `internal-api`, `backoffice`, `mcp-server`, `ai-service`, `web-client`).
- **Database Abstraction**: MariaDB relational backend for persistent production storage paired with SQLAlchemy ORM for test portability.



### Accessible help

FIXME (OPTIONAL built-in doc)

## Examples of use

<details>
<summary>(Click to expand)</b></summary>

### Valid examples

FIXME

| Use case                                         | Prompt                              | Answer              |
|--------------------------------------------------|-------------------------------------------|---------------|
| Listing all products of a branch      | `echo "ls -latr /tmp" | ./hsh`            |


### Failing examples
Couple of use-cases which are not supported.

| Use case                                                                        | Command line                                  |
|---------------------------------------------------------------------------------|-----------------------------------------------|
| FIXME   | FIXME |


</details>

## Technical information

### General architecture

FIXME

### Process Flow

FIXME Mermaid diagram

For a deep dive into the inner workings and design choices, including PATH resolution and function-level architecture, please read our dedicated [Architecture](./ARCHITECTURE.md) page.

### Memory management & Performance

FIXME (evaluation of average memory used by all docker containers )


## Testing

FIXME OPTIONAL if we have enough time to really make tests
For detailed instructions on how to run our manual and automated test suites, please refer to our [Testing Guide](./TESTING.md).

## Project constraints and methodology

### Imposed constraints

This project has been realized in compliance with all business specifications and technical constraints detailed in the [Project context](./PROJECT.md)

#### Requirements

Confer PROJECT.md

### Project methodology

To ensure we shared the vision and limit conflicts when pushing code we enforced a few simple rules throughout the duration.
1. Starting with the Flowchart to understand the global architecture and identify potential challenges.
2. As soon as starting to code, never push directly on dev but make a Pull Request from "personal branch", which had to be checked and approved by peer: this allowed fresh eyes to view code and detect potential flaws while also making reviewer understand and "learn" about peer's code naturally.
3. Test features as we code them.
4. Reintegrate changes pushed onto dev inside personal branch as soon as made available to keep history as "single-lined" as possible and avoid creating conflicts down the road.

We also used Github's tickets and Wiki scarcely, as we realized a few days in we didn't need it as our communication and collaboration workflow was working fine without them.

Beyond Git and Visual Studio Code / Kate as our main tools for code writing and sharing, we occasionally used online collaboration and testing tools for brainstorms, https://codeshare.io/ and https://www.onlinegdb.com/online_c_compiler respectively.

### Acknowledgments

- Holberton School for the project guidelines
- Betty style guide contributors
- All peer reviewers and testers

## Technologies Used

FIXME

<p align="left">
    <img src="https://img.shields.io/badge/C-a8b9cc?logo=&logoColor=black&style=for-the-badge" alt="C badge">
    <img src="https://img.shields.io/badge/GIT-f05032?logo=git&logoColor=white&style=for-the-badge" alt="Git badge">
    <img src="https://img.shields.io/badge/GITHUB-181717?logo=github&logoColor=white&style=for-the-badge" alt="GitHub badge">
    <img src="https://img.shields.io/badge/VALGRIND-purple?logo=v&logoColor=white&style=for-the-badge" alt="Valgrind badge">
    <img src="https://img.shields.io/badge/VIM-019733?logo=vim&logoColor=white&style=for-the-badge" alt="VIM badge">
    <img src="https://img.shields.io/badge/KDE-blue?logo=kde&logoColor=white&style=for-the-badge" alt="KDE badge">
</p>


## Authors

- **Laurent Lacôte** - [GitHub](https://github.com/llacote-holberton)
- **Yoann Lages** - [GitHub](https://github.com/Yo13038)

## License

This project is part of the Holberton School curriculum and is made available under the General Public License v3.0, confer [License text](./LICENSE.md) for details.

---
