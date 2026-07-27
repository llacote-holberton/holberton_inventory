# Authentication & Authorization Module Technical Documentation

This document consolidates security mechanisms, cryptographic standards, architectural trade-offs, and token lifecycle details extracted from `auth.py`.

---

## 1. Architectural Decision Records (ADRs) & Design Choices

### Stateless Token Payload Authentication
* **Design Choice:** The dependency function `get_jwt_payload` decodes and returns the JWT payload dictionary directly, rather than executing a database query to re-fetch a `User` entity on every request (commonly named `get_current_user`).
* **Rationale:** Reduces database load and latency by relying entirely on cryptographic signatures to verify client identity and authorization claims (`user_id`, `role`, `branch_id`).
* **Trade-off / Security Boundary:** Token revocation is stateless. If a user's access or account status changes in the database (e.g., account deactivation), their active JWT remains valid until its natural expiration time (`exp`).

---

### Role-Based Access Control (RBAC) via FastAPI Dependencies
* **Implementation:** Modular dependency functions (`require_manager`, `require_admin`) wrapping `get_jwt_payload`.
* **Rationale:** Encapsulates role assertion logic cleanly using FastAPI's `Depends` mechanism. Routes restricted to specific roles can declare these dependencies directly, returning `403 Forbidden` if claims are unsatisfied.

---

### OpenAPI Schema Integration
* **Implementation:** `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")`
* **Rationale:** Configures FastAPI's security scheme to automatically extract the Bearer token from incoming request HTTP `Authorization` headers, while enabling interactive token authentication in Swagger UI via the `/login` endpoint.

---

## 2. Security & Cryptography Implementation

### Password Hashing Specification (Bcrypt)
* **Algorithm:** Bcrypt with dynamic salting (`bcrypt.gensalt()`).
* **Encoding Requirements:** Accepts UTF-8 encoded string inputs and casts generated raw hash bytes back to UTF-8 strings for persistent database storage.
* **Hash Structure Format Breakdown:**
  * Example: `$2b$12$KIXQx5Z8vN3mR7wYtL9pOeJhX2Wn4Fk6Ds8Tq1Vr0Cy5Ab3Ez.Wm`
  * `$2b$`: Algorithm identifier (Bcrypt variant).
  * `$12$`: Cost factor (work factor controlling time complexity against brute-force attacks).
  * `KIXQx5Z8vN3mR7wYtL9pOe`: 22-character salt value.
  * Remaining payload: Computed digest hash.

---

### JWT Payload Claims & Expiration Strategy
* **Standard Claims:**
  * `sub` (*Subject*): User identifier formatted as a string (e.g., `str(user_id)`).
  * `exp` (*Expiration Time*): Expiration datetime generated using `datetime.now(timezone.utc)` + `JWT_EXPIRE_MINUTES`.
* **Custom Claims:**
  * `role`: User authorization role (`admin`, `manager`).
  * `branch_id`: Associated branch identifier (optional/nullable).
* **Automated Expiration Check:** The `pyjwt` decoding function automatically compares the payload's `exp` timestamp against current system time (in UTC) during token validation, raising `jwt.ExpiredSignatureError` if exceeded.

---

## 3. Error Handling & HTTP Status Code Mapping

| Exception Encountered | Raised HTTP Exception | Status Code | Detail Message |
| :--- | :--- | :--- | :--- |
| `jwt.ExpiredSignatureError` | `HTTPException` | `401 Unauthorized` | `"token_expired"` |
| `jwt.InvalidTokenError` | `HTTPException` | `401 Unauthorized` | `"invalid_token"` |
| Role Check Failure | `HTTPException` | `403 Forbidden` | `"forbidden"` |
