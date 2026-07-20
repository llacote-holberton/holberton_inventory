# Project Overview

<details><summary>Read project context</summary>

## Introduction

In this project, you will design and build an inventory management system for a fictional retail company with multiple branches.

The system will include two main areas:

1. A **Backoffice** used by authenticated internal users to manage stock and users.
2. A **Client Web Interface** where external users can ask questions about products and stock using natural language.

The project integrates backend development, relational databases, authentication, external APIs, AI agents, MCP servers, and web interfaces into a single software system.

This is your first complex integrative project in the trimester. You are expected to make technical decisions, justify them, and organize the implementation as a team. Some requirements are fixed, but several architectural decisions are intentionally left open so that you can evaluate alternatives and explain your choices.

---

## General Learning Objectives

By completing this project, you should be able to:

- Design a medium-sized software system composed of multiple services.
- Model and implement a relational database schema.
- Use SQLAlchemy to access and manipulate relational data.
- Implement authentication and role-based authorization.
- Build a functional Backoffice interface.
- Consume an external product API.
- Implement an MCP server as a bridge to an external service.
- Integrate one or more AI agents into a backend service.
- Build a simple web client for natural-language inventory queries.
- Decide between REST and WebSocket communication based on technical trade-offs.
- Explain and justify architectural decisions.
- Work collaboratively using a Git-based workflow.

---

## Project Context

The fictional company has several physical branches. Each branch can hold stock for different products.

Products are managed by an external product system. Your application must not store product names, descriptions, prices, or metadata in the Backoffice database. The Backoffice database will only store local system data, such as users, branches, and stock quantities associated with product identifiers.

An external Product API will be provided as a Docker container. This API is read-only and allows you to:

- List available products.
- Get the details of a specific product.

Your system must use this Product API whenever product information is required.

---

## High-Level System Components

Your final system should include the following components:

1. **Backoffice Service**
     - Authenticated internal web application.
     - Manages users and branch stock.
     - Uses SQLAlchemy to access the database.

2. **Relational Database**
     - Stores users, branches, and stock quantities.
     - Does not store product details.

3. **External Product API**
     - Provided as a Docker container.
     - Read-only source of product data.
     - [GitHub Repository](/rltoken/FSRzdtVompgAOJDqL3DGgw)

4. **Product MCP Server**
     - Implemented by your team.
     - Acts as a bridge between the AI system and the Product API.

5. **AI Query Service**
     - Independent backend service.
     - Contains one or more AI agents.
     - Processes natural-language questions from the Client Web Interface.

6. **Client Web Interface**
     - Simple chat or search-box interface.
     - Allows anonymous users to ask questions about products and stock.

---

## Mandatory Functional Scope

### Backoffice: Common Users

Common users must be assigned to exactly one branch.

A common user can only operate on the stock of their assigned branch.

Common users must be able to:

- Add stock.
- Remove stock.
- Consult stock.
- List products currently in stock for their branch.

Common users must not be able to manage users or operate on another branch.

---

### Backoffice: Admin User

There will be only one administrator user: `admin`.

You do not need to implement functionality for creating additional administrator users.

The admin user must be able to:

- List users.
- Create common users.
- Assign common users to a branch.
- Soft-delete users.
- Modify users.
- Change a user&#39;s password.
- Change a user&#39;s assigned branch.

The admin user must not manage stock.

---

### Product Data

Product information must come from the provided external Product API.

Your Backoffice database must not store:

- Product names.
- Product descriptions.
- Product prices.
- Product images.
- Product metadata.

Your database may store only the product identifier required to associate stock with a product from the external API.

---

### Stock Data

Your system must store stock quantities per branch and product.

At minimum, your stock model must support:

- Branch identification.
- Product identification.
- Available quantity.

Stock quantity must never become negative.

Adding or removing stock must validate the requested quantity.

---

### Authentication and Authorization

Backoffice access must require authentication.

Authorization rules must be enforced on the backend, not only in the user interface.

Passwords must be stored securely in the database.

You must not store plain-text passwords.

Your team must be able to explain:

- Which password hashing mechanism you used.
- Why it is appropriate for password storage.
- How authentication is performed.
- How role-based access is enforced.

For this project, SSL/TLS is not required for the web application or API.

---

### Client Web Interface

The public client interface must be a simple web page where anonymous users can ask questions about products and stock.

Users do not need to log in.

Each question must be treated independently. You are not required to store or track conversation history.

Example questions:

- “Which branch has stock of product X?”
- “What products can I find in branch Y?”
- “If I want to buy 3 units of X, 2 units of Y, and 4 units of Z, which branch or branches should I visit?”
- “Give me details about product XX.”

The interface may be implemented as:

- A chat-style interface.
- A search-box style interface.

The design should be simple and functional. Visual polish is not the priority of this project.

---

### Client Communication Strategy

Your team must decide whether the Client Web Interface communicates with the AI Query Service using:

- REST API requests.
- WebSocket communication.

Both options are valid.

You must justify your decision.

A REST API may be simpler because each question is independent.

WebSockets may be justified if your team wants to support real-time behavior, streaming responses, or a chat-like experience.

You are not required to implement both.

---

### AI Query Service

The backend that serves the Client Web Interface must be an independent service from the Backoffice.

This service must use one or more AI agents to process natural-language questions and generate responses.

The AI system should be able to answer questions using:

- Product data from the external Product API through your MCP server.
- Stock data from the relational database or through a database MCP integration.

Your agent should avoid inventing information. If the available tools do not provide enough information, the response should clearly state that the information is unavailable.

---

### MCP Requirements

You must implement an MCP server that acts as a bridge to the external Product API.

This MCP server should expose tools that allow the AI agent to:

- List products.
- Retrieve product details.

Additionally, your team must decide how the AI system will access stock information.

You may either:

- Extend your own MCP server to provide controlled stock queries.
- Use a third-party database MCP tool, such as MCP Toolbox for Databases.

You must justify your choice.

---

## Suggested Project Structure

You may organize the repository as you prefer, but your structure should make the separation between components clear.

One possible structure is:

```text
project-root/
  backoffice/
  ai_service/
  product_mcp_server/
  client_web/
  docs/
  docker-compose.yml
  README.md
```

This structure is only a suggestion. You may use a different organization if you can justify it clearly.

</details>

# Tasks details

## 0. Architecture and Planning

<details>

### Goal

Define the architecture of your system before implementing features.

Your team must identify the services, responsibilities, data flow, and main technical decisions.


### Tasks

#### 1 - Define the System Architecture

Create an architecture document that explains:

- Which services your system will include.
- The responsibility of each service.
- How the services communicate with each other.
- Which data is stored locally.
- Which data comes from the external Product API.
- How the AI agent will access product and stock information.

Your document should be clear enough for another team to understand your design.

Do not write implementation code for this task.

---

#### 2 - Choose Communication Strategies

Decide:

- Whether the Backoffice will use REST + HTML/CSS/JS or Server-Side Rendering.
- Whether the Client Web Interface will use REST or WebSockets.
- How the AI Query Service will communicate with MCP tools.

For each decision, explain:

- The option you selected.
- The main benefit of your choice.
- The main trade-off or limitation.

You are not expected to choose the most complex option. You are expected to choose an option that fits the project requirements and your team&#39;s capacity.

---

#### 3 - Define the Minimum Viable Product

Define your MVP.

Your MVP must include all mandatory requirements, but it should avoid unnecessary extra features.

List:

- What your team will implement first.
- What your team will leave for later.
- Which optional features you will only attempt if time allows.

This task is important. A clear MVP reduces the risk of incomplete integration at the end of the project.

### Expected Deliverables

- Architecture document.
- Initial service diagram.
- Written decision record for communication strategies.
- MVP definition.

</details>

## 1. Database Design and Backoffice Foundation

<details>

### Goal

Design the relational database and implement the foundation of the Backoffice service.

### Tasks

#### 1 - Design the Database Schema

Design a relational schema for the Backoffice database.

At minimum, your schema must support:

- Users.
- Branches.
- Stock per branch and product.

Your design must enforce or support the following rules:

- A common user belongs to exactly one branch.
- The admin user is not assigned stock-management responsibilities.
- Stock is associated with a branch and an external product identifier.
- Product details are not stored locally.
- Deleted users are soft-deleted, not physically removed.

You may add additional fields if they are justified.

Recommended fields to consider:

- Creation timestamps.
- Update timestamps.
- Active/deleted status.
- Role.
- Password hash.

Do not add tables only because they seem realistic. Add them only if they support project requirements.

---

#### 2 - Implement SQLAlchemy Models

Implement SQLAlchemy models based on your schema.

Your models should clearly represent:

- Relationships between users and branches.
- Relationships between branches and stock.
- Stock quantities by product identifier.

Your implementation should avoid duplicating product data from the Product API.

---

#### 3 - Create Initial Data

Create a reliable way to initialize the system with basic data.

At minimum, the system must include:

- One admin user.
- At least two branches.
- Enough sample stock to test the system.

The admin password must still be stored securely.

Do not hardcode plain-text passwords into the database.

---

#### 4 - Validate Stock Rules

Implement validation rules to ensure:

- Stock quantity cannot become negative.
- Stock changes require positive integer quantities.
- Stock operations reference valid branches.
- Stock operations reference product identifiers that exist in the external Product API, when applicable.

You may decide where to place this validation, but you must be able to explain your decision.

### Expected Deliverables

- Database schema documentation.
- SQLAlchemy models.
- Database initialization script or migration strategy.
- Explanation of validation rules.

</details>


## 2. Backoffice Authentication and Authorization

<details>

### Goal

Implement secure access control for the Backoffice.

### Tasks

#### 1 - Implement User Authentication

Implement login functionality for Backoffice users.

Your authentication system must:

- Verify user credentials securely.
- Reject deleted users.
- Establish an authenticated session or token.
- Protect Backoffice routes from anonymous access.

You may use session-based authentication or token-based authentication.

You must justify your choice.

---

#### 2 - Store Passwords Securely

Implement password hashing.

Your solution must avoid storing plain-text passwords.

You should use a mechanism designed for password storage, such as:

- bcrypt.
- Argon2.
- PBKDF2.

You must document:

- Which mechanism you used.
- How passwords are hashed.
- How password verification works.
- Why a general-purpose hash such as plain SHA256 is not sufficient by itself.

---

#### 3 - Implement Role-Based Authorization

Implement authorization rules for:

- Admin users.
- Common users.

Your backend must enforce that:

- Common users can manage stock only for their assigned branch.
- Common users cannot manage users.
- Admin can manage users.
- Admin cannot manage stock.

Do not rely only on hiding buttons in the interface. Authorization must be enforced in backend logic.

### Expected Deliverables

- Login functionality.
- Secure password handling.
- Authorization rules.
- Documentation explaining the authentication and authorization strategy.

</details>


## 3. Backoffice Functionalities

<details>

### Goal

Implement the operational Backoffice features for both user types.

### Tasks

#### 1 - Common User Stock Operations

Implement the stock operations available to common users.

A common user must be able to:

- Add stock to their assigned branch.
- Remove stock from their assigned branch.
- List products currently in stock in their assigned branch.
- Check the quantity available for a product in their assigned branch.

The interface must make it clear which branch the user is operating on.

The backend must prevent operations on other branches.

---

#### 2 - Admin User Management

Implement admin operations.

The admin user must be able to:

- List users.
- Create common users.
- Assign users to branches.
- Soft-delete users.
- Change a user&#39;s password.
- Change a user&#39;s assigned branch.

When a user is soft-deleted:

- The user should not be able to log in.
- Existing stock records must not be deleted.

---

#### 3 - Product API Integration in Backoffice

Integrate the provided **Product API** where needed.

The Backoffice should allow users to understand which product identifier they are operating on.

You may choose how to expose this information, for example:

- Product selector populated from the Product API.
- Product search by identifier.
- Product list with basic details retrieved from the API.

The important requirement is that product details come from the external API, not from your local database.

---

#### 4 - Backoffice Interface

Implement the Backoffice interface using one of the following approaches:

- REST API with a lightweight HTML/CSS/JS frontend.
- Server-Side Rendering.

Your interface should be simple, functional, and clear.

You must not prioritize visual complexity over correctness, validation, and authorization.

### Expected Deliverables

- Working common-user stock operations.
- Working admin user-management operations.
- Product API integration.
- Functional Backoffice interface.
- Explanation of your UI/backend approach.

</details>


## 4. Product MCP Server

<details>

### Goal

Implement an MCP server that allows the AI system to access the external Product API through tools.

### Tasks

#### 1 - Define MCP Tools

Define the tools your MCP server will expose.

At minimum, your tools must allow the AI agent to:

- List available products.
- Get details for one product.

Your tool definitions should use clear input and output structures.

Avoid exposing unnecessary Product API behavior.

---

#### 2 - Implement Product API Communication

Implement communication between your MCP server and the provided Product API.

Your MCP server should handle:

- Successful product listing.
- Product detail retrieval.
- Product not found responses.
- Product API connection errors.

The MCP server should not silently fail. It should return clear error information that the AI agent can use.

---

#### 3 - Test MCP Tools Manually

Before connecting the AI agent, test your MCP server manually.

Verify that:

- Product listing works.
- Product detail lookup works.
- Invalid product identifiers are handled correctly.
- Product API failures are handled clearly.

### Expected Deliverables

- Product MCP server implementation.
- Tool definitions.
- Manual test evidence or documented test steps.
- Explanation of error handling.

</details>


## 5. AI Query Service

<details>

### Goal

Build an independent backend service that receives user questions, uses AI agents and tools, and returns grounded answers.

### Tasks

#### 1 - Define Supported Question Types

Define the question types your AI service will support.

At minimum, it should support:

- Asking for product details.
- Asking where a product is available.
- Asking what products are available in a branch.
- Asking which branch or branches are convenient for a list of desired products and quantities.

You are not required to support every possible natural-language request.

Your system should respond clearly when a question is outside the supported scope.

---

#### 2 - Connect the Agent to Product Tools

Connect your AI agent to the Product MCP Server.

The agent should use the MCP tools to obtain product information instead of inventing product details.

Your implementation should make it possible to observe or debug which tool calls are being made.

---

#### 3 - Provide Stock Access to the Agent

Decide how the AI service will access stock information.

You may:

- Extend your MCP server with stock-query tools.
- Use a database MCP tool.
- Implement a controlled internal API used by the AI service.

Your choice must preserve clear boundaries and avoid unsafe direct access patterns.

At minimum, the AI service must be able to obtain:

- Stock of a product across branches.
- Stock available in one branch.
- Whether a shopping list can be satisfied by one or more branches.

---

#### 4 - Generate Grounded Responses

The AI service must generate responses based on actual data.

It should not invent:

- Product names.
- Product details.
- Stock quantities.
- Branch availability.

If the required information is unavailable, the response must say so clearly.

Your team should consider how to include enough information in the agent context without exposing unnecessary internal details.

---

#### 5 - Expose the AI Query Endpoint

Expose an endpoint for the Client Web Interface.

You may use:

- REST.
- WebSockets.

Your endpoint must receive a user question and return an answer.

Since conversation history is not required, each request may be treated independently.

### Expected Deliverables

- AI Query Service.
- Agent integration with product tools.
- Stock-query strategy.
- Query endpoint for the client.
- Documentation of supported question types.

</details>

## 6. Client Web Interface

<details>

### Goal

Build a simple public web interface where users can ask natural-language questions about products and stock.

### Tasks

#### 1 - Build the Basic Interface

Create a simple page with:

- A text input.
- A submit button.
- A response area.

You may present it as:

- A chat interface.
- A search interface.

The interface does not require authentication.

---

#### 2 - Connect the Interface to the AI Query Service

Connect the page to your AI Query Service using your chosen communication strategy.

The page should:

- Send the user&#39;s question.
- Display the response.
- Show basic loading or waiting feedback.
- Show a clear error message if the service fails.

---

#### 3 - Validate the User Experience

Test the interface with realistic questions.

Use examples such as:

- Product detail questions.
- Branch availability questions.
- Product availability across branches.
- Shopping-list recommendation questions.

The user experience should be simple but understandable.

### Expected Deliverables

- Functional public client page.
- Connection to AI Query Service.
- Basic error handling.
- Example questions documented in the README.

</details>

## 7. Integration, Testing, and Documentation

<details>

### Goal

Integrate all components into a coherent system and prepare the final delivery.

### Tasks

#### 1 - Integrate the Complete Flow

Verify the complete system flow:

1. Product API is running.
2. Backoffice database is initialized.
3. Backoffice users can authenticate.
4. Common users can manage branch stock.
5. Admin can manage users.
6. Product MCP Server can access product data.
7. AI Query Service can answer questions using product and stock information.
8. Client Web Interface can display answers.

Do not leave integration for the final day.

---

#### 2 - Test Critical Scenarios

Test at least the following scenarios:

- Common user adds valid stock.
- Common user removes valid stock.
- Common user cannot remove more stock than available.
- Common user cannot operate on another branch.
- Admin can create a common user.
- Admin can soft-delete a user.
- Deleted user cannot log in.
- Admin cannot manage stock.
- Product details are obtained from the external API.
- AI can answer where a product is available.
- AI can answer what products are available in a branch.
- AI gives a clear response for unknown products.
- AI gives a clear response when information is unavailable.

You may implement automated tests, manual test scripts, or both.

Automated tests are strongly recommended for critical backend logic.

---

#### 3 - Write the README

Your README must include:

- Project overview.
- Team members.
- Architecture summary.
- Setup instructions.
- How to run each service.
- How to initialize the database.
- How to access the Backoffice.
- How to use the Client Web Interface.
- Main technical decisions.
- Known limitations.
- Optional features implemented, if any.

The README must be sufficient for a mentor to run and evaluate your project.

---

#### 4 - Prepare the Final Presentation

Prepare a final presentation explaining:

- What your system does.
- How the architecture is organized.
- How authentication and authorization work.
- How product data is integrated.
- How the AI agent uses MCP tools.
- Which technical decisions you made and why.
- What trade-offs you accepted.
- What you would improve with more time.

The presentation should include a live or recorded demonstration.

### Expected Deliverables

- Integrated application.
- README.
- Architecture documentation.
- Test evidence.
- Final presentation.

</details>


