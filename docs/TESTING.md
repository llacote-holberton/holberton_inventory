# Testing methodology and coverage

## Overview

Considering the short time constraints for the project, we decided to focus on the most sensitive parts aka operations potentially affecting database and the ones providing information to the AI agent.

We also decided to rely on an LLM services (case in point Google Gemini here) to generate the unit tests associated with each CRUD method or endpoint API along with its implementation as we felt it was typically the kind of use-case where the functional scope of the requests and technical constraints of the response made the AI reliable enough on the first attempt.

Please note however that as we started doing this mid-part of the project there are some big gaps in backoffice testing.
Also there have been no security or functional testing whatsoever done (yet) on the frontoffice to check for security vulnerabilities or AI agent's response quality.

## Running tests

In order to be able to run tests locally you must have Python3 (>=3.11, 3.14+ recommended) and the related libraries fastapi, pytest, httpx2, sqlalchemy installed (on a local Python env run `pip install pytest httpx2 sqlalchemy fastapi`).


To start all tests you can simply open a terminal, "put yourself" at project's root and run `pytest`. The program will automatically search, collect and run files named `test_*.py`.
Alternatively, if you want to run only one file, you just need to provide its path as an argument.

## Test coverage (for v1.0)

### 1. Completely Missing Test File

* **`test_auth.py` (Unit tests for security and authentication module)**:
  * Password hashing (`hash_password`) and verification (`verify_password`) using Bcrypt.
  * JWT token encoding and payload structure (`create_access_token`: validation of `sub`, `role`, `branch_id`, `exp` claims).
  * Token decoding and exception handling in `get_jwt_payload`:
    * Expired token (raises 401 `token_expired`).
    * Tampered / invalid token (raises 401 `invalid_token`).
  * Isolated validation of role dependencies: `require_manager`, `require_admin`, `require_admin_or_manager`.

### 2. Covered Test Cases

#### Authentication & Security (API & Internal API)
* Rejection of unauthenticated requests (401) on protected endpoints[cite: 4, 5, 6].
* Rejection of malformed or invalid JWT tokens (401)[cite: 4, 5].
* Internal API authentication via `x-api-key` header (200 if valid, 401/403/422 if missing or incorrect).

#### Branch Management (`/branches`)
* **API (`test_api_branches.py`)**:
  * Fetching branch list (Manager / Admin).
  * Default sorting by label (`ordered_by_label=true` vs `false`).
  * Boolean parameter validation (422 if invalid).
  * Including managers (`with_managers=true`): allowed for Admin (200), forbidden for Manager (403).
  * Branch search by pattern (`/search/branches/{pattern}`): Manager/Admin success, partial match, 404 error if no match.
* **CRUD (`test_crud_branches.py`)**:
  * Empty database behavior.
  * Alphabetical sorting of branches.
  * Case-insensitive pattern search.
  * Eager loading of active managers (`get_branches_with_active_managers`), excluding inactive accounts and Admins.

#### Stock Management (`/branches/{id}/stocks`)
* **API (`test_api_stocks.py`)**:
  * Manager retrieving stock for their assigned branch (200).
  * Rejection if a Manager attempts to retrieve stock for another branch (403).
  * Rejection of stock access for Admin role (403).
  * Stock addition (`POST /add`): row creation, quantity accumulation, rejection for other branches (403), payload validation (422).
  * Stock removal (`POST /remove`): decrementing quantity, insufficient stock (400), product not found in branch (404), payload validation (422).
* **CRUD (`test_crud_stocks.py`)**:
  * Core operations: `get_stock`, `set_stock`, `add_stock`, `remove_stock`.
  * Raising custom exception `InsufficientStockError` when requesting more than available quantity.
  * Exact removal bringing stock quantity to 0.
  * Query consolidation (`list_stocks_for_product`, `list_stocks_for_branch`) and record deletion (`delete_stock`).

#### User Management (`/users`)
* **API (`test_api_users.py`)**:
  * User creation by Admin (201).
  * Password security (verifying password/hash does not leak in response body).
  * Rejection of creation attempt by Manager (403) or unauthenticated caller (401).
  * Creation attempt with a duplicate username.
  * Activation (`POST /{id}/activate`) and Deactivation (`POST /{id}/deactivate`).
  * Handling 404 errors for non-existent users.
* **CRUD (`test_crud_users.py`)**:
  * Business rule: Admin user creation forces `branch_id = None`.
  * Business rule: Manager user creation allows direct branch assignment.
  * SQL Integrity errors on non-existent `branch_id` or duplicate username (`IntegrityError`).
  * Password reset via `reset_user_password`.
  * Branch assignment/unassignment (`assign_branch`) restricted to Managers.
  * Toggling active/inactive state via `set_user_active_state`.

#### Internal API (`test_internal_api.py`)
* Endpoint `/internal/branches/{id}/stock/{product_id}` (200 or 0 if missing).
* Global stock aggregation by product `/internal/products/{id}/stocks`.
* Listing stock for a specific branch `/internal/branches/{id}/stocks`.
* Listing all branches `/internal/branches/list`.

### 3. Missing / Uncovered Test Cases

#### Authentication & Account Routes (`main.py`)
* `POST /login`:
  * Successful authentication for active users (returns JWT Bearer token).
  * Failure with invalid password (401 `invalid_credentials`).
  * Failure with non-existent username (401 `invalid_credentials`).
  * Failure for deactivated users (`is_active=False`) (401 `invalid_credentials`).
* `GET /whoami`:
  * Returning decoded payload for a valid JWT.
  * Rejection (401) without token or with expired token.

#### User Management Routes (`main.py`)
* `GET /users`:
  * Admin retrieving full user list.
  * Rejection (403) if called by a Manager.
* `POST /users/{user_id}/reset_password`:
  * Successful password reset by Admin (200 `password_successfully_reset`).
  * Reset attempt on non-existent `user_id` (404 `user_not_found`).
  * Rejection if called by Manager (403) or unauthenticated user (401).
  * Payload validation for `PasswordReset` schema (422 if missing/invalid).
* `POST /users/{user_id}/assign_branch`:
  * Successful branch assignment to a Manager by an Admin (200).
  * Unassigning / resetting branch (`branch_id = null`).
  * Attempting to assign a non-existent `branch_id` (400 `invalid_branch_id`).
  * Attempting assignment on a non-existent user or an Admin (404 `user_not_found_or_not_manager`).
  * Rejection for Manager role (403).

#### Real-time / Event-Driven (SSE Stream) (`main.py`)
* `GET /branches/{branch_id}/stocks/stream`:
  * Client connection to Server-Sent Events stream (`text/event-stream`).
  * Receiving JSON event payload (`data: ...`) upon stock updates (`POST /add` or `POST /remove`).
  * Event listener queue cleanup upon client disconnect.

#### Static File Serving & UI (`main.py`)
* `GET /`, `GET /login`, `GET /ui/login`, `GET /ui/admin`, `GET /ui/manager`:
  * Serving static HTML files with HTTP 200 status (`login.html`, `admin.html`, `manager.html`).

#### Database Edge Cases & Safety (`crud.py`)
* `find_branches_by_name`:
  * Querying search patterns containing SQL wildcards (`%`, `_`) to ensure safe `ilike` filter behavior.
