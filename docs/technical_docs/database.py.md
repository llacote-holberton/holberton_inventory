# Database Configuration & Session Management Documentation

This document consolidates architectural choices, configuration parameters, and session lifecycle mechanisms extracted from `database.py`.

---

## 1. Architectural Choices & Driver Configuration

### Connection String & Dialect
* **Database URL:** Dynamically constructed using standard environment variables (`DB_HBNTORY_USER_ID`, `DB_HBNTORY_USER_PWD`, `DB_HOST`, `DB_PORT`, `DB_HBNTORY_BASENAME`).
* **Driver Protocol:** Uses `mysql+pymysql` for PyMySQL-driven connectivity to MariaDB/MySQL.
* **Fallback Defaults:** Defaults to host `localhost` and port `3306` targeting `holberton_inventory` if network environment parameters are omitted.

### Lazy Engine Initialization & Connection Pooling
* **Engine Creation:** Configured via `create_engine(DB_URL)`.
* **Lazy Behavior:** The SQLAlchemy engine manages an internal TCP connection pool but defers establishing actual network sockets until the first database operation (`execute` or query execution) is triggered.

---

## 2. Session Factory & Transaction Management

### Session Configuration (`SessionLocal`)
* **Engine Binding:** `bind=engine` links session instances directly to the engine connection pool.
* **Autoflush Configuration (`autoflush=False`):**
  * **Rationale:** Disables automatic SQL flushing prior to query execution.
  * **Benefit:** Provides granular control over when SQL statements (`INSERT`, `UPDATE`, `DELETE`) are emitted to the database. It prevents intermediate or unvalidated state changes from being flushed prematurely.
* **Explicit Commit & Atomicity Strategy:**
  * Changes made to ORM objects remain strictly in-memory (in the session identity map) until an explicit call to `.commit()` or `.flush()` is issued.
  * Ensures transaction atomicity: if an exception occurs or `.rollback()` is called prior to commit, no partial or corrupted writes persist to the database.

---

## 3. Session Lifecycle & Resource Cleanup

### Dependency Generator (`get_db`)
* **Pattern:** Generator function using `yield` designed for request-scoped database sessions (ideal for framework dependency injection).
* **Connection Lifecycle:** Instantiates a fresh `SessionLocal` instance and enforces deterministic cleanup via `db.close()` inside a `finally` block, preventing database connection leaks.
