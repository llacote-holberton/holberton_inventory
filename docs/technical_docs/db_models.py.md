# Database Models Technical Documentation

This document consolidates inline developer notes, architectural choices, and code explanations extracted from the SQLAlchemy database models (`db_models.py`).

---

## 1. Architectural Decision Records (ADRs) & Technical Choices

### View-Only Relationship for Active Branch Managers
* **Associated Model & Attribute:** `Branch.managers`
* **Associated Import:** `from sqlalchemy.orm import relationship`
* **Decision:** Define `managers` as a dynamic, view-only ORM relationship using `primaryjoin` with `viewonly=True`.
* **Rationale:** Delegates joined reading and filtering logic directly to SQLAlchemy ORM. It exposes a convenient Python property (`branch.managers`) containing only active managers, without altering table schemas or risking invalid database writes.

---

### Explicit Composite Primary Key Declaration
* **Associated Model:** `Stock`
* **Associated Table Argument:** `PrimaryKeyConstraint("product_id", "branch_id")`
* **Decision:** Declare the composite primary key explicitly inside `__table_args__` rather than setting `primary_key=True` inline on individual `mapped_column` attributes.
* **Rationale:** Setting `primary_key=True` inline forces the composite key index ordering to match the physical order in which Python attributes are declared. Explicit `PrimaryKeyConstraint` in `__table_args__` provides explicit control over key sequence and index structure regardless of attribute definition order.

---

### SQL Column Name Aliasing
* **Associated Model & Attributes:** `User.name` (`"user_name"`), `User.role` (`"user_role"`)
* **Decision:** Separate Python attribute names from physical SQL column names by passing explicitly named string parameters to `mapped_column()`.
* **Rationale:** Avoids redundant or verbose attribute names in Python code (e.g., using `user.name` instead of `user.user_name`) while complying with standard relational database column naming conventions.

---

### String Enum Double Inheritance Pattern
* **Associated Model/Enum:** `UserRole(str, enum.Enum)`
* **Decision:** Implement Enum classes by inheriting from both `str` and `enum.Enum`.
* **Rationale:**
  * **String Compatibility:** Inheriting from `str` allows direct string comparisons in Python code (e.g., `UserRole.ADMIN == "admin"` evaluates to `True`).
  * **Validation:** Inheriting from `Enum` guarantees value validation upon instantiation.
  * *Note:* In Python versions/SQLAlchemy setups supporting Python 3.11+, `enum.StrEnum` offers native support for this behavior.

---

### Custom Enum Value Mapping
* **Associated Model Attribute:** `User.role`
* **Associated Method:** `UserRole.get_values`
* **Decision:** Pass `values_callable=UserRole.get_values` to SQLAlchemy's `Enum` column specification.
* **Rationale:** Forces SQLAlchemy to validate and store the Enum's underlying string values (`"admin"`, `"manager"`) rather than string representations of the internal Enum member keys (`"ADMIN"`, `"MANAGER"`).

---

## 2. Code Explanations

### Implicit `NOT NULL` Constraints in SQLAlchemy 2.0
* **Associated Concept:** `Mapped[T]` Type Annotations
* **Explanation:** In SQLAlchemy 2.0 type mapping, specifying a non-optional primitive type (e.g., `Mapped[int]`, `Mapped[str]`) implicitly configures the database column as `NOT NULL`. Optional columns must be explicitly annotated as nullable (e.g., `Mapped[int | None]`).

---

### Implicit Auto-Increment Behavior
* **Associated Model Attribute:** `User.id`
* **Explanation:** Annotating a single `int` column with `primary_key=True` automatically configures `AUTO_INCREMENT` behavior in SQL database engines. This implicit default applies strictly to single-column integer primary keys.

---

### Inline vs. Table-Level Unicity Constraints
* **Associated Model Attribute:** `User.name` (`unique=True`)
* **Explanation:** Passing `unique=True` inside `mapped_column()` generates standard single-column unique constraints without requiring explicit imports. Explicit `UniqueConstraint` imports are necessary only when defining custom constraint names or creating multi-column unique constraints in `__table_args__`.

---

### Primitive Type Translation
* **Associated Model Attribute:** `User.is_active` (`Mapped[bool]`)
* **Explanation:** SQLAlchemy 2.0 maps standard Python primitive types directly to underlying SQL data types (e.g., `bool` maps automatically to `Boolean`). Manual instantiation of core type classes (such as `sqlalchemy.Boolean`) is no longer required for basic column mappings.
