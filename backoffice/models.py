#!/usr/bin/env python3
"""Module defining backoffice database 'as SQLAlchemy Entities'"""

# ========== DEPENDENCIES ==============
# Tools for "database schema as Python classes one per table"
# ORM for Object Relational Mapper
# Base classes and functions required for any kind of modelling.
from sqlalchemy.orm import DeclarativeBase  # Strictly required for every model
from sqlalchemy.orm import Mapped           # Confer example in "tips" folder.
from sqlalchemy.orm import mapped_column    # Required to "configure" a column

# "SQL Data types"
from sqlalchemy import String
# SQL Constraints
from sqlalchemy import ForeignKey, PrimaryKeyConstraint


class Base(DeclarativeBase):
    pass


class Branch(Base):
    """Defines model for branches"""
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(50), unique=True)


class Stock(Base):
    """Defines model for branches's stocks"""
    __tablename__ = "stocks"
    # Reminder: "just the type" implies "NOT NULL" (otherwise [int | None])
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    product_id: Mapped[int]
    # NOTE: could also define "combined primary key" by just directly adding
    #  'primary_key=True' as another option of mapped_column() in both columns
    #  ex product_id: Mapped[int] = mapped_column(default=0, primary_key=True)
    # BUT in that case the column used to index the "combined PK" would always
    #   be the FIRST column declared. Meanwhile, the explicit syntax belows
    #   lets dev choose which to use whatever happens.
    __table_args__ = (
        PrimaryKeyConstraint("product_id", "branch_id"),
    )
