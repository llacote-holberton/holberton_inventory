#!/usr/bin/env python3
"""Manages the authentication and session generation to MariaDB"""

# REQUIRED to exploit "local environment variables"
from os import getenv
from dotenv import load_dotenv
# REQUIRED to manage "connexions to database"
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Defining connexion parameters
load_dotenv()
db_user = getenv("DB_HBNTORY_USER_ID")
db_pass = getenv("DB_HBNTORY_USER_PWD")
db_host = getenv("DB_HOST", "localhost")
db_port = getenv("DB_PORT", "3306")
db_name = getenv("DB_HBNTORY_BASENAME", "holberton_inventory")
DB_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

# Engine checks the "protocol" (here mysql+pymysql) and manages an inner pool
#   of TCP connexions to propagate queries.
# It will NOT actually create a connexion until the 1st query is made
#   through "query" or "execute" methods on db object ("lazy start").
engine = create_engine(DB_URL)
# This creates a "session maker" to spawn a session for each HTTP request.
# Bind means "use the TCP connexion pools provided by the engine"
# Autoflush False means "each SQL transaction making a change MUST be
#   commited explicitely through a db.flush() call".
#   Useful if/when app wants to control precisely when/how changes are saved.
# Autocommit False was the old way in versions 1.x, now it is default behaviour
SessionLocal = sessionmaker(bind=engine, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    print(dir(get_db))
    test = get_db()
    

    # Example of why deactivating auto-commit is useful
    # 1. lecture, objet chargé dans l'identity map
    # stock = db.query(Stock).filter(...).first()
    # 2. modification en mémoire, PAS encore en base
    # stock.quantity -= 5
    # 3. seulement maintenant, l'UPDATE part réellement
    # db.commit()
    # In case for some reason app crashes between lines 2 and 3,
    # OR if an explicit call to db.rollback() was made,
    # NOTHING would have been modified in base avoiding partial/incoherent writes.
