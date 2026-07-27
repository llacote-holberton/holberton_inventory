"""Module defining backoffice database 'as SQLAlchemy Entities'"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
import enum
from sqlalchemy import String, Enum
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, CheckConstraint, Index
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class Branch(Base):
    """Defines model for branches"""
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(50), unique=True)
    managers: Mapped[list["User"]] = relationship(
        primaryjoin="and_(Branch.id == User.branch_id, User.role == 'manager', User.is_active == True)",
        viewonly=True
    )


class Stock(Base):
    """Defines model for branches's stocks"""
    __tablename__ = "stocks"
    quantity: Mapped[int] = mapped_column(default=0)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    product_id: Mapped[int]
    __table_args__ = (
        PrimaryKeyConstraint("product_id", "branch_id"),
        CheckConstraint("quantity >=0", name="positive_stock"),
        Index("idx_stocks_by_pid", "product_id"),
    )


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"

    @staticmethod
    def get_values(cls):
        return [e.value for e in cls]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column("user_name", String(30), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        "user_role",
        Enum(UserRole, values_callable=UserRole.get_values),
        default=UserRole.MANAGER
    )
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    is_active: Mapped[bool]
