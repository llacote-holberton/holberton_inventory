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


class Base(DeclarativeBase):
    pass


class Branch(Base):
    """Defines model for branches"""
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(50), unique=True)
