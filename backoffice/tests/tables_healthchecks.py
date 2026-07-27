#!/usr/bin/env python3

# REQUIRED to reconstruct dynamically the path to parent folder in which
#   the models are located.
import sys
from pathlib import Path
# Adds the parent of current folder to the list of paths
#   to parse when looking for modules (a bit like bash PATH)
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# REQUIRED to exploit "local environment variables"
from os import getenv
from dotenv import load_dotenv

load_dotenv()
db_user = getenv("DB_HBNTORY_USER_ID")
db_pass = getenv("DB_HBNTORY_USER_PWD")
db_host = getenv("DB_HOST", "localhost")
db_port = getenv("DB_PORT", "3306")
db_name = getenv("DB_HBNTORY_BASENAME", "holberton_inventory")


# Now imports are simplified as the ones related to models are delegated.
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Importing models from my own code.
from db_models import Branch, Stock

# 2. Connexion à la base de données (remplacer avec vos identifiants MariaDB)
DB_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DB_URL)

# 3. Lecture et affichage
with Session(engine) as session:
    print("=== BRANCHES ===")
    for branch in session.scalars(select(Branch)):
        print(f"ID: {branch.id} | Label: {branch.label}")

    print("\n=== STOCKS ===")
    for stock in session.scalars(select(Stock)):
        stock_info = " | ".join([
            f"Branch ID: {stock.branch_id}",
            f"Product ID: {stock.branch_id}",
            f"Current stock: {stock.quantity}",
        ])
        print(stock_info)
