# FastAPI Backoffice API Technical Documentation

This document consolidates security patterns, OAuth2 standards compliance, error handling strategies, and serialization details extracted from `backoffice_api.py`.

---

## 1. Security & Compliance Design Standards

### User Enumeration Prevention
* **Endpoint:** `POST /login`
* **Implementation:** Returns a generic `401 Unauthorized` status with the detail message `"invalid_credentials"` for any authentication failure (whether the username does not exist, the account is inactive, or the password is incorrect).
* **Rationale:** Prevents malicious actors from probing valid usernames through differential error messaging (reconnaissance mitigation).

### OAuth2 RFC 6749 Compliance
* **Endpoint:** `POST /login`
* **Specification:** Formats the token response payload as `{"access_token": jwt, "token_type": "bearer"}`.
* **Rationale:** Complies strictly with RFC 6749 Section 5.1 (Successful Response) to ensure seamless compatibility with standard OAuth2 clients and OpenAPI (Swagger UI) authorization workflows.

### Response Data Sanitization (Pydantic Out Models)
* **Endpoint:** `GET /users`
* **Implementation:** Employs `response_model=list[UserOut]`.
* **Rationale:** Although the CRUD layer fetches complete SQLAlchemy `User` models containing internal state (such as `password_hash`), FastAPI automatically filters out all fields not explicitly defined in the `UserOut` schema prior to JSON serialization.

---

## 2. Serialization & Enum Handling

### Enum String Value Extraction
* **Attribute:** `user.role.value`
* **Implementation:** Explicitly accesses `.value` when constructing the JWT payload (`create_access_token(...)`).
* **Rationale:** Prevents potential JSON serialization issues where raw Python Enum instances are passed directly into string payload builders or response streams.

---

## 3. Database Exception Handling & Transaction Integrity

### Foreign Key Violation Handling
* **Endpoint:** `POST /users/{user_id}/assign_branch`
* **Exception Caught:** `sqlalchemy.exc.IntegrityError`
* **Workflow:**
  1. Catches database-level integrity violations caused by referencing non-existent foreign keys (e.g., invalid `branch_id`).
  2. Executes explicit transaction rollback (`db.rollback()`) to reset the session state.
  3. Raises `HTTPException(status_code=400, detail="invalid_branch_id")`.

---

## 4. API Authorization & Dependency Injection Matrix

| Endpoint | HTTP Method | Required Dependency / Role | Success Output | Error Details |
| :--- | :--- | :--- | :--- | :--- |
| `/login` | `POST` | None (Public) | JWT Access Token | `401 invalid_credentials` |
| `/whoami` | `GET` | Valid JWT (`get_jwt_payload`) | Decoded Token Claims | `401 token_expired / invalid_token` |
| `/users` | `GET` | Admin (`require_admin`) | List of `UserOut` | `403 forbidden` |
| `/users/{id}/activate` | `POST` | Admin (`require_admin`) | Activation confirmation | `404 user_not_found` |
| `/users/{id}/deactivate` | `POST` | Admin (`require_admin`) | Deactivation confirmation | `404 user_not_found` |
| `/users/{id}/reset_password`| `POST` | Admin (`require_admin`) | Reset confirmation | `404 user_not_found` |
| `/users/{id}/assign_branch` | `POST` | Admin (`require_admin`) | Branch assignment | `400 invalid_branch_id`<br>`404 user_not_found_or_not_manager` |
