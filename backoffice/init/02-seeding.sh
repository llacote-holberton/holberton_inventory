#!/bin/bash
set -e

# Environment variables should be set in the .env file at project root
#   and read by Docker then propagated to MariaDb.
# Confer .env.example for help.
INIT_MODE="${INIT_MODE:-demo}"

echo "==> Initializing application data in mode: [$INIT_MODE]"

if [ "$INIT_MODE" = "demo" ]; then
    echo "==> Injecting demonstration data from demo-data sql file..."
    mariadb -u root -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE" < /docker-entrypoint-initdb.d/seeds/demo-data.sql
    echo "==> Demonstration data successfully inserted."

elif [ "$INIT_MODE" = "minimal" ]; then
    echo "==> Creating only minimal data for app to be usable (Admin user and branches)..."

    # 1. Creating the "first admin"
    ADMIN_USER="${INITIAL_ADMIN_USER:-admin}"
    # Hash for password "Holberton Inventory Admin"
#    DEFAULT_ADMIN_HASH='$2y$10$XlhkMZlzPNf1yVanLzUEDONVp95m9JWA2il/M1wuTxGqqDlwPrR22'
    DEFAULT_ADMIN_HASH='$2y$10$Vq.1ue1wo82Uxe9z2Oupu.USb3HwxlxIxOEp8KQ76nZzTN1NmCss.'

    if [ -z "$INITIAL_ADMIN_HASH" ]; then
        echo "WARNING! No INITIAL_ADMIN_HASH environment var found."
        echo "Using fallback hash by default matching password 'Holberton Inventory Admin' (DO NOT USE IN PROD)"
        ADMIN_HASH_PWD=$DEFAULT_ADMIN_HASH
    else
      ADMIN_HASH_PWD="$INITIAL_ADMIN_HASH"
    fi

    #ADMIN_HASH_PWD="${INITIAL_ADMIN_HASH:-$DEFAULT_ADMIN_HASH}"

    mariadb -u root -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE" -e "
        INSERT INTO users (user_name, password_hash, user_role, is_active) 
        VALUES ('$ADMIN_USER', '$ADMIN_HASH_PWD', 'admin', 1);
    "
    echo "    -> Application Admin '$ADMIN_USER' created."

    # 2. Parsing env var INITIAL_BRANCHES to create branches
    # Setting ',' as separator to split string into array, from env var string.
    RAW_BRANCHES="${INITIAL_BRANCHES:-Paris,Toulouse}"
    IFS=',' read -ra BRANCH_ARRAY <<< "$RAW_BRANCHES"
    for branch in "${BRANCH_ARRAY[@]}"; do
        # Nettoyage des espaces autour du nom
        CLEAN_BRANCH=$(echo "$branch" | xargs)
        if [ -n "$CLEAN_BRANCH" ]; then
            mariadb -u root -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE" -e "
                INSERT INTO branches (label) VALUES ('$CLEAN_BRANCH');
            "
            echo "    -> New branch created: $CLEAN_BRANCH"
        fi
    done

    echo "==> Minimal init successfully finished."
else
    echo "WARNING: INIT_MODE '$INIT_MODE' unsupported. No data has been injected."
fi
