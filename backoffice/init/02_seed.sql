-- ----------------------------------------------------------------------------
-- FILLING THE TABLE with arbitrary data
-- In prod we would only create the admin user using environment variables
-- For now we create the whole dataset to ease up development and demonstration
-- ----------------------------------------------------------------------------

-- Displaying information messages with "universal method"
SELECT '===== Holberton Inventory: (re)Filling tables with default content =====' AS log;
SELECT '  Entities: User, Branch, Stock' AS log;

-- ----------------------------------------------------------------------------
-- Task 0: (re)filling branches table
-- NOTE: done BEFORE users because of foreign keys constraints
-- ----------------------------------------------------------------------------
SELECT '--- (re)Inserting default branches ---' AS log;

INSERT IGNORE INTO branches (id, label)
VALUES
    (1, "Toulouse Esquirol"),
    (2, "Toulouse Carmes"),
    (3, "Rodez"),
    (4, "Caussade"),
    (5, "Paris La Défense");

-- ----------------------------------------------------------------------------
-- Task 1: (re)filling users table
-- ----------------------------------------------------------------------------
SELECT '--- (re)Inserting default users ---' AS log;

INSERT IGNORE INTO users (user_name, user_role, password_hash, branch_id)
VALUES
    ('god', 'admin', "pseudo password hash en attendant", NULL),
    ('yoann', 'manager', "gureto passewordu", 1),
    ('laurent', 'manager', "my top password", 5),
    -- SHOWS that CHECK on user_role value is enabled, will not be inserted.
    -- HOWEVER with an ENUM it is different the invalid value will be ignored
    --   and replaced with NULL, which is hugely problematic.
    -- ('luc@example.com', 'Luc', 22, 3);
;

-- SHOWS that a user can be created without filling everything
--   will end with "manager" role and NULL branch
INSERT IGNORE INTO users (user_name, password_hash)
VALUES
    ('newbie', 'badpass123456');

-- ----------------------------------------------------------------------------
-- Task 2: (re)filling stocks table
-- NOTE: product with id 32 is "discontinued"
-- NOTE: only have products from id 1 to 39, backoffice should ensure
--   no row can be inserted with non-existing product.
-- ----------------------------------------------------------------------------
SELECT '--- (re)Inserting default stocks ---' AS log;

INSERT IGNORE INTO stocks (branch_id, product_id, quantity)
VALUES
    -- QUESTION: should we allow stock with 0? Shouldn't it be removed automatically?
    -- Case: product HB-LAP-1002 with stocks only in one branch, Caussade branch_id 4
    (4, 2, 777),
    -- Case: product_id 4 HB-MON-2102 having stocks in Toulouse (1, 2) and Paris (5),
    --       total should be 15+8+7 = 30
    (1, 4, 15),
    (1, 4, 8),
    (1, 4, 7),
    -- SHOWS that check on quantity works, will not be inserted
    (1, 35, -6),
    -- SHOWS that check on branch_id works, will not be inserted
    (666, 2, 10),
    -- SHOWS that (for now) quantity 0 is allowed, will be inserted
    -- Product id 6 sku HB-KBD-4101 in Caussade
    (4, 6, 0),
    -- INVALID ENTRY to double check backoffice behaviour (inexisting product id)
    (1, 666, 45)
;


