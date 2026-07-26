-- Displaying information messages
SELECT '===== Holberton Inventory: (re)Creating tables =====' AS log;
SELECT '   Entities: User, Branch, Stock' AS log;

-- -----------------------------------------------------------------
-- Task 0: (re)creating users table
-- -----------------------------------------------------------------
SELECT '--- Forcefully (re)creating the users table ---' AS log;

DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users
(
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(30) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    -- WARNING: IF an INSERT without any value for user_role arrived
    --   Then MariaDb WOULD NOT USE THE DEFAULT but insert "NULL"
    -- Causing problems in app.
    user_role ENUM('admin', 'manager') NOT NULL DEFAULT 'manager',
    branch_id INTEGER,
    is_active BOOLEAN NOT NULL
    -- OPTIONAL in real project: created_at and updated_at
);

-- -----------------------------------------------------------------
-- Task 1: (re)creating branches table
-- -----------------------------------------------------------------
SELECT '--- Forcefully (re)creating the branches table ---' AS log;

DROP TABLE IF EXISTS branches;

CREATE TABLE IF NOT EXISTS branches
(
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    label VARCHAR(50) NOT NULL UNIQUE
);


-- -----------------------------------------------------------------
-- Task 2: Adding foreign key relationship for users <-> branches
-- -----------------------------------------------------------------
ALTER TABLE users
    ADD CONSTRAINT fk_users_branches
    FOREIGN KEY (branch_id) REFERENCES branches(id);


-- -----------------------------------------------------------------
-- Task 2: (re)creating stock table
-- -----------------------------------------------------------------
SELECT '--- Forcefully (re)creating the stocks table ---' AS log;

DROP TABLE IF EXISTS stocks;

CREATE TABLE IF NOT EXISTS stocks
(
    
    branch_id INT NOT NULL,  -- Foreign Key
    product_id INT NOT NULL, -- External key provided from API
    quantity   INT NOT NULL DEFAULT 0,
    -- Primary Key is logically the combination of the branch and product
    PRIMARY KEY (branch_id, product_id),
    CONSTRAINT fk_branch FOREIGN KEY (branch_id) REFERENCES branches(id),
    CONSTRAINT chk_quantity_positive CHECK (quantity >= 0)
);

-- And its related indexes
CREATE INDEX idx_stock_by_product ON stocks(product_id);
-- Redundant because primary key automatically has index based on its first component
-- CREATE INDEX idx_stock_by_branch  ON stocks(branch_id);
