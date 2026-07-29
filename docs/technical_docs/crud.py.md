# CRUD Operations & Technical Documentation

This document consolidates inline developer notes, architectural choices, and code explanations extracted from the database CRUD module.

---

## 1. Architectural Decision Records (ADRs) & Technical Choices

### Global Session Management Pattern
* **Associated Parameter:** `db: Session` across all CRUD functions
* **Decision:** Apply Dependency Injection by requiring callers to supply an external `sqlalchemy.orm.Session` instance rather than creating session instances inside the functions.
* **Rationale:**
  * **Mock Testing:** Allows tests to pass alternative database engines (such as in-memory SQLite) without modifying function internals.
  * **Transaction Composition:** Enables grouping multiple CRUD operations across different functions into a single atomic SQL transaction before issuing a final `commit()`.
  * **Context Flexibility:** Decouples database operations from specific session lifecycles (e.g., FastAPI dependency injection vs. CLI scripts).

---

### Forced Keyword-Only Arguments
* **Associated Functions:** `add_stock`, `get_stock`, `remove_stock`, `list_stocks_for_product`, `list_stocks_for_branch`, `set_stock`, `delete_stock`, `reset_user_password`, `assign_branch`, `set_user_active_state`, `find_branches_by_name`
* **Decision:** Enforce parameter naming by placing `*,` early in function signatures.
* **Rationale:** Prevents developer error caused by swapping positional integer arguments (e.g., passing `branch_id` where `product_id` is expected).

---

### Decoupling Password Hashing from CRUD Layer
* **Associated Functions:** `create_user`, `reset_user_password`
* **Decision:** Accept pre-computed password hashes directly rather than raw passwords or internal hashing routines.
* **Rationale:** Preserves single responsibility. CRUD operations interact strictly with prepared values ready for database storage. Authentication logic and cryptographic algorithms remain isolated in upper application layers.

---

### Exception Strategy for Inventory Depletion
* **Associated Element:** Class `InsufficientStockError` & Function `remove_stock`
* **Decision:** Raise a dedicated domain exception `InsufficientStockError` rather than returning compound objects (e.g., `{"success": False, "message": "..."}`) or ambiguous values like `None`.
* **Rationale:**
  * Returning a response dictionary mixes CRUD concerns with API-layer payload formats.
  * Returning `None` creates ambiguity between "product/branch row does not exist" and "insufficient quantity to deduct."
  * Raising an explicit domain exception enables clean error propagation and distinct handling upstream.

---

### Atomic SQL-Level Defensive Stock Checks
* **Associated Function:** `remove_stock`
* **Decision:** Include `Stock.quantity >= amount` directly inside the SQL `UPDATE` statement's `where` clause.
* **Rationale:** Avoids race conditions and database constraint violations (`quantity >= 0`). If requested quantity exceeds available stock, zero rows are modified, eliminating the need to execute manual checks or transaction rollbacks.

---

### Post-Mutation Re-Reading for Accurate State
* **Associated Function:** `add_stock`
* **Decision:** Perform a fresh read via `get_stock` after executing upsert statements instead of computing local arithmetic in Python.
* **Rationale:** Guarantees absolute accuracy by fetching actual row state from the database engine, accounting for potential concurrent writes or server-side default calculations.

---

### Eager Loading for ORM Relationships
* **Associated Import:** `from sqlalchemy.orm import selectinload`
* **Associated Function:** `get_branches_with_active_managers`
* **Decision:** Use `selectinload(Branch.managers)` when querying branch records.
* **Rationale:** Pre-populates child relationship collections efficiently in a second SELECT query, avoiding N+1 query performance penalties.

---

### Isolation of Test Helper Utilities
* **Associated Functions:** `set_stock`, `delete_stock`
* **Decision:** Mark imperative reset/delete helpers explicitly as internal test methods.
* **Rationale:** Prevents unsafe state manipulation routines from being exposed through production API routes.

---

### Script Execution Session Instantiation
* **Associated Block:** `if __name__ == "__main__":`
* **Decision:** Instantiate `SessionLocal()` directly rather than using dependency yield functions like `get_db()`.
* **Rationale:** Web framework generators (such as FastAPI's `get_db()`) rely on framework request lifecycles. Direct session instantiation is simpler and clearer for standalone CLI scripts and quick self-tests.

---

## 2. Code Explanations

### `get_stock`
* **Query Unwrapping:** `.first()` is explicitly called on `db.query(Stock)` because ORM query execution returns an iterable collection by default even when single-row matches are expected.
* **Missing Record Standard:** Returns `None` when no record matches input parameters, reflecting the exact current state of the database table.

---

### `add_stock`
* **Statement Declarations:** Variable `stmt` represents a declarative SQL statement object generated via `mysql_insert`.
* **Upsert Behavior:** `.on_duplicate_key_update()` generates an `INSERT ... ON DUPLICATE KEY UPDATE` query in MySQL/MariaDB, performing an insertion or an in-place increment if the primary key exists.
* **Integrity Exception Handling:** Captures `IntegrityError` to execute `db.rollback()`, ensuring transaction cleanup before re-raising the exception for upstream handling.

---

### `remove_stock`
* **Row Count Inspection:** Uses `result.rowcount` to evaluate query success:
  * `rowcount > 0`: Deduction succeeded; re-fetches updated stock amount.
  * `rowcount == 0`: Indicates either missing stock record (returns `None`) or insufficient stock (raises `InsufficientStockError`).

---

### `list_stocks_for_product` & `list_stocks_for_branch`
* **Read-Only Safety:** Explicit `try/except` blocks are unnecessary for read-only queries. If no matching rows exist, SQLAlchemy returns an empty list `[]`.
* **Python Type Hints:** Utilizes native generics (`list[Stock]`) available in Python 3.9+.

---

### `set_stock`
* **Session Refresh:** `db.refresh(stock)` forces a database re-read to update in-memory Python object attributes with values generated by the database engine (e.g., defaults, triggers).

---

### `list_users` & `get_user_by_name`
* **Scalar Results:** `db.scalars()` unwraps single-column ORM result tuples (e.g., `(<User object>,)`) directly into model instances (`User`).

---

### `create_user`
* **Session Lifecycle Phases:**
  * `db.add()`: Registers the entity into the unit-of-work pending change set (no SQL emitted yet).
  * `db.commit()`: Flushes changes, executes SQL `INSERT`, and commits the transaction.
  * `db.refresh()`: Re-queries the newly inserted row to populate auto-generated primary keys (`id`).

---

### `assign_branch` & `set_user_active_state`
* **Boolean Return Mapping:** Evaluates `result.rowcount > 0` as a boolean return value. A `False` result indicates that the specified `user_id` did not exist or failed precondition checks (e.g., missing `MANAGER` role).

---

### `find_branches_by_name`
* **Case-Insensitive Pattern Matching:** Employs `.ilike(f"%{search_string}%")` to perform case-insensitive substring matching across target database dialects.
