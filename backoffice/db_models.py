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
from sqlalchemy import String, Enum
# SQL Constraints
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, CheckConstraint, Index


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
    quantity: Mapped[int] = mapped_column(default=0)
    # Reminder: "just the type" implies "NOT NULL" (otherwise [int | None])
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    product_id: Mapped[int]  # For autonamed index: mapped_column(index=True)
    # NOTE: could also define "combined primary key" by just directly adding
    #  'primary_key=True' as another option of mapped_column() in both columns
    #  ex product_id: Mapped[int] = mapped_column(default=0, primary_key=True)
    # BUT in that case the column used to index the "combined PK" would always
    #   be the FIRST column declared. Meanwhile, the explicit syntax belows
    #   lets dev choose which to use whatever happens.
    __table_args__ = (
        PrimaryKeyConstraint("product_id", "branch_id"),
        CheckConstraint("quantity >=0", name="positive_stock"),
        Index("idx_stocks_by_pid", "product_id"),  # Explicit index name
    )


import enum  # Import put here for now to stress relation with User model.
# Apparently in Alchemy 2.0 no need to import the related Alchemy Enum anymore
# from sqlalchemy import Enum
# https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html
#   #using-python-enum-or-pep-586-literal-types-in-the-type-map

class UserRole(str, enum.Enum):  # FIXME check that weird syntax how it works
    ADMIN = "admin"
    MANAGER = "manager"

    @staticmethod
    def get_values(cls):
        return [e.value for e in cls]



class User(Base):
    __tablename__ = "users"

    # Note: "int" + "primary_key" => "auto_increment" is implicit.
    # ONLY true for primary_key made of a single INT column.
    id: Mapped[int] = mapped_column(primary_key = True)
    # Dissociating "property name in Python" from "column name in SQL engine"
    #   to have similar "id" between Models and avoid redundancy (User.user_id)
    name: Mapped[str] = mapped_column("user_name", String(30), unique=True)
    # Note: no need to add specific UniqueConstraint with import UNLESS we would
    #   want an arbitrary name like for above Index or if we needed to "compose"
    #   the Unicity check upon several columns at once.
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        "user_role",
        # Detailed Enum required for Alchemy to check on values and not keys
        Enum(UserRole, values_callable=UserRole.get_values),
        default=UserRole.MANAGER
    )
    branch_id: Mapped[int|None] = mapped_column(ForeignKey("branches.id"))
    # Same as for enum, with Alchemy 2.0 native Python core data types are
    #   automatically "translated" into the inner Alchemy class (here Boolean)
    is_active: Mapped[bool]



# SELF-TEACHING NOTES
# About class UserRole(str, enum.Enum):
# This weird syntax is called "double inheritance" (confer lessons on classes)
# UserRole FIRST inherits from core String class (so gets all related methods)
# THEN from Enum gets the automatic validation that when trying to instanciate
#   the provided value matches one of the class attributes (fail -> ValueError)
# The double inheritance allows things like UserRole.ADMIN == "admin" -> True
# Otherwise just Enum would make properties be "only Enum objects" making
#   things like "direct string comparison" impossible.
# To instanciate, best practice vs "less robust practice"
# new_user = User(name="Alice", role=UserRole.ADMIN)
# new_user = User(name="Bob", role="manager")
# Best practice is using the enum "keys" whenever possible.
# Note: in SQLAlchemy 2.0 its Enum class natively provides a subclass for this.
#    enum.StrEnum
