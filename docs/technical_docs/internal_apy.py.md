# Internal API Module Technical Documentation

This document consolidates security mechanisms, header authentication patterns, fallbacks, and data aggregation details extracted from `internal_api.py`.

---

## 1. Security & Authentication Architecture

### Header-Based API Key Verification
* **Implementation:** `verify_internal_key(x_api_key: str = Header(...))`
* **Header Name:** Expects the custom HTTP header `X-API-KEY` (automatically normalized from `x_api_key`).
* **Dependency Injection:** Enforced at the endpoint definition level via `dependencies=[Depends(verify_internal_key)]`.

### Timing Attack Mitigation (Constant-Time Comparison)
* **Implementation:** `hmac.compare_digest(x_api_key, INTERNAL_API_KEY)`
* **Rationale:** Replaces standard Python string inequality (`!=`) with cryptographic constant-time comparison.
* **Benefit:** Eliminates side-channel timing attacks where an attacker measures response times to brute-force the API key character-by-character.
* **Failure Response:** Raises `HTTPException(status_code=403, detail="forbidden")` if the key is missing, empty, or invalid.

---

## 2. API Design & Endpoint Behavior

### Non-Existent Stock Defaulting Strategy
* **Endpoints:** `GET /internal/stock`, `GET /internal/branches/{branch_id}/stock/{product_id}`
* **Pattern:** When querying a product/branch combination with no corresponding database row (`stock is None`), the endpoint returns a default response with `quantity = 0` rather than raising a `404 Not Found` exception.
* **Rationale:** Simplifies client-side integration by treating absent inventory records as zero stock available.

### On-the-Fly Stock Aggregation
* **Endpoint:** `GET /internal/products/{product_id}/stocks`
* **Response Model:** `ProductStockSummary`
* **Aggregation Logic:** Fetches all branch stock rows for a specific product and dynamically calculates total inventory using `sum(stock.quantity for stock in product_stocks)`.
* **Serialization:** Returns a composite payload containing the product ID, calculated total quantity, and per-branch detail list.

---

## 3. Route & Dependency Matrix

| Endpoint Route | HTTP Method | Response Model | Auth Protection |
| :--- | :--- | :--- | :--- |
| `/internal/stock` | `GET` | Raw Dict | `verify_internal_key` |
| `/internal/branches/{branch_id}/stock/{product_id}` | `GET` | `StockOut` | `verify_internal_key` |
| `/internal/products/{product_id}/stocks` | `GET` | `ProductStockSummary` | `verify_internal_key` |
| `/internal/branches/{branch_id}/stocks` | `GET` | `list[StockOut]` | `verify_internal_key` |
| `/internal/branches/list` | `GET` | `list[BranchOut]` | `verify_internal_key` |
