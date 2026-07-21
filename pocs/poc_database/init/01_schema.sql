-- Displaying information messages with "universal method"
SELECT '===== Holberton Inventory: (re)Creating tables =====' AS [LOG];
SELECT '  Entities: User, Branch, Stock' AS [LOG];

-- ----------------------------------------
-- Task 0: (re)creating users table
-- ----------------------------------------
SELECT '--- Forcefully (re)creating the users table ---' AS [LOG];

DROP TABLE IF EXISTS users;
-- Keeping "if not exists" to easily change the script mode by just removing above line.
CREATE TABLE IF NOT EXISTS users
(   -- BEWARE difference of syntax (for SQLite it's AUTOINCREMENT without _)
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    -- NOTE: Varchar much better than char but mariadb REQUIRES a given limit for varchar
    user_name VARCHAR(30) NOT NULL UNIQUE,
    -- Max size because hash are usually big
    password_hash VARCHAR(255),
    -- We know we wille only 'use' two roles so can restrain directly here.
    user_role VARCHAR(15) NOT NULL CHECK (user_role IN ('admin', 'manager')),
    branch_id INTEGER,
    is_active BOOLEAN NOT NULL
);

