#!/usr/bin/env python3

from sqlalchemy import create_engine, select, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

# 1. Modèles minimalistes
class Base(DeclarativeBase):
    pass

class Branch(Base):
    __tablename__ = "branches"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(50), unique=True)

class Stock(Base):
    __tablename__ = "stocks"
    
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    product_id: Mapped[int]
    quantity: Mapped[int]
    
    __table_args__ = (
        PrimaryKeyConstraint("product_id", "branch_id"),
    )

# 2. Connexion à la base de données (remplacer avec vos identifiants MariaDB)
DATABASE_URL = "mysql+pymysql://root:H0lb3rt0n@localhost:3306/holberton_inventory"
engine = create_engine(DATABASE_URL)

# 3. Lecture et affichage
with Session(engine) as session:
    print("=== BRANCHES ===")
    for branch in session.scalars(select(Branch)):
        print(f"ID: {branch.id} | Label: {branch.label}")

    print("\n=== STOCKS ===")
    for stock in session.scalars(select(Stock)):
        print(f"Branch ID: {stock.branch_id} | Product ID: {stock.product_id} | Quantité: {stock.quantity}")
