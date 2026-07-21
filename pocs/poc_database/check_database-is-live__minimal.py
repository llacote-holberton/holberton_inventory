#!/usr/bin/env python3
from sqlalchemy import create_engine, text

# 1. Configuring the "connexion url"
# Format : dialect+driver://username:password@host:port/database_name
DATABASE_URL = "mysql+pymysql://root:H0lb3rt0n@localhost:3306/holberton_inventory"

# 2. Creating the "engine" (driver to interact with)
engine = create_engine(DATABASE_URL, echo=True)  # echo=True affiche les logs SQL générés

# 3. Executing single request
with engine.connect() as connection:
    # Utilisation de text() pour les requêtes SQL brutes
    result = connection.execute(text("SELECT * FROM users"))
    
    print("\n--- Contenu de la table 'users' ---")
    for row in result:
        # Chaque 'row' se comporte comme un tuple ou un dictionnaire
        print(f"ID: {row.id} | Nom: {row.user_name} | Rôle: {row.user_role}")
# NOTE: if we wanted to made a CUD operation we'd need engin.begin() as connection
#   so it can rollback if SQL transaction cannot be finished successfully for whatever reason.
