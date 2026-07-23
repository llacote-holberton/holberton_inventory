#!/usr/bin/env python3
"""Module defining backoffice database 'as SQLAlchemy Entities'"""

# ========== DEPENDENCIES ==============
# Tools for "database schema as Python classes one per table"
# ORM for Object Relational Mapper

from sqlalchemy.orm import DeclarativeBase  # Strictly required for every model
from sqlalchemy.orm import Mapped           # Confer example in "tips" folder.
from sqlalchemy.orm import mapped_column    # Required to "configure" a column

class Base(DeclarativeBase):
    pass


class Branch(Base):
    """Defines model for branches"""
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str]
