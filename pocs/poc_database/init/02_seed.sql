
-- Displaying information messages with "universal method"
SELECT '===== Holberton Inventory: (re)Filling tables with default content =====' AS log;
SELECT '  Entities: User, Branch, Stock' AS log;

-- ----------------------------------------
-- Task 0: (re)filling branches table
-- NOTE: done BEFORE users because of foreign keys constraints
-- ----------------------------------------
SELECT '--- (re)Inserting default users ---' AS log;

INSERT IGNORE INTO branches (id, label)
VALUES
    (1, "Toulouse Esquirol"),
    (2, "Toulouse Carmes"),
    (3, "Rodez"),
    (4, "Caussade"),
    (5, "Paris La Défense");

-- ----------------------------------------
-- Task 0: (re)filling users table
-- ----------------------------------------
SELECT '--- (re)Inserting default users ---' AS log;

INSERT IGNORE INTO users (user_name, user_role, password_hash, branch_id)
VALUES
    ('god', 'admin', "pseudo password hash en attendant", 1),
    ('yoann', 'manager', "gureto passewordu", 1),
    ('laurent', 'manager', "my top password", 5),
    -- SHOWS that check on user_role value is enabled, will not be inserted.
    ('luc@example.com', 'Luc', 22, 3);

