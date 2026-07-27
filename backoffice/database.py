#!/usr/bin/env python3
"""Manages the authentication and session generation to MariaDB"""

from os import getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
db_user = getenv("DB_HBNTORY_USER_ID")
db_pass = getenv("DB_HBNTORY_USER_PWD")
db_host = getenv("DB_HOST", "localhost")
db_port = getenv("DB_PORT", "3306")
db_name = getenv("DB_HBNTORY_BASENAME", "holberton_inventory")
DB_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DB_URL)
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
