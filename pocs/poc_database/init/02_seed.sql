
-- Displaying information messages with "universal method"
SELECT '===== Holberton Inventory: (re)Filling tables with default content =====' AS [LOG];
SELECT '  Entities: User, Branch, Stock' AS [LOG];

-- ----------------------------------------
-- Task 0: (re)filling users table
-- ----------------------------------------
SELECT '--- (re)Inserting default users ---' AS [LOG];

INSERT IGNORE INTO users (user_name, user_role, password_hash)
VALUES
    ('god', 'admin', "pseudo password hash en attendant"),
    ('yoann', 'manager', 34),
    ('luc@example.com', 'Luc', 22);
