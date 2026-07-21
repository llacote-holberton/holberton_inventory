-- Displaying information messages
SELECT '===== Holberton Inventory: (re)Creating tables =====' AS log;
SELECT '   Entities: User, Branch, Stock' AS log;

-- ----------------------------------------
-- Task 0: (re)creating users table
-- ----------------------------------------
SELECT '--- Forcefully (re)creating the users table ---' AS log;

DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users
(
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(30) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    user_role VARCHAR(15) NOT NULL CHECK (user_role IN ('admin', 'manager')),
    branch_id INTEGER,
    is_active BOOLEAN NOT NULL
    -- OPTIONAL in real project: created_at and updated_at
);

-- ----------------------------------------
-- Task 1: (re)creating branches table
-- ----------------------------------------
SELECT '--- Forcefully (re)creating the branches table ---' AS log;

DROP TABLE IF EXISTS branches;

CREATE TABLE IF NOT EXISTS branches
(
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    label VARCHAR(50) NOT NULL UNIQUE
);

-- ----------------------------------------
-- Task 3: Adding constraints of foreign keys on tables
-- ----------------------------------------
ALTER TABLE users
    ADD CONSTRAINT fk_users_branches
    FOREIGN KEY (branch_id) REFERENCES branches(id);
