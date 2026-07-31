#!/usr/bin/env python
"""Module dedicated to actual CRUD operations on database"""
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from db_models import Stock
from db_models import User, UserRole
from db_models import Branch
from sqlalchemy.orm import selectinload
# Category used to warn about a "SQL Constraint Violation" raised in DB.
from sqlalchemy.exc import IntegrityError

# ========================= STOCK RELATED CRUD =========================
def get_stock(db: Session, *, product_id: int, branch_id: int) -> Stock | None:
    return (
        db.query(Stock)
        .filter(Stock.product_id == product_id, Stock.branch_id == branch_id)
        .first()
    )


def add_stock(db: Session, *, product_id: int, branch_id: int, amount: int) -> int:
    """Adds/update 'stock row' and returns the updated quantity"""
    stmt = mysql_insert(Stock).values(
        branch_id=branch_id, product_id=product_id, quantity=amount
    )
    # Incompatible with test suite using SQLite for maximum isolation
    #   because that function translates into MySQL-specific instructions.
    # stmt = stmt.on_duplicate_key_update(quantity=Stock.quantity + amount)
    # Tried a "direct insert" and intercepted error "row exists" to "convert"
    #   to update
    # try: db.execute(stmt); db.commit()
    # except IntegrityError: db.rollback() raise
    # Now we first try to retrieve a matching row, then process differently
    #   depending on whether we got one or not, using the ORM abstraction layer.
    # Which is the "most portable way" because UPSERT operation has no universal
    #   standard in SQL language.
    stock = db.query(Stock).filter_by(
        branch_id=branch_id, product_id=product_id
    ).first()
    if stock:
        stock.quantity += amount
    else:
        stock = Stock(branch_id=branch_id, product_id=product_id, quantity=amount)
        db.add(stock)
    db.commit()
    # Reminder: forces SQLAlchemy to reread to get up to date values for attributes.
    db.refresh(stock)

    return stock.quantity


class InsufficientStockError(Exception):
    def __init__(self, available: int):
        self.available = available
        super().__init__(f"insufficient stock: {available} available")


def remove_stock(db: Session, branch_id: int,
                 product_id: int, amount: int) -> int | None:
    result = db.execute(
        update(Stock)
        .where(
            Stock.branch_id == branch_id,
            Stock.product_id == product_id,
            Stock.quantity >= amount
        )
        .values(quantity=Stock.quantity - amount)
    )
    db.commit()

    # I prefer having the "success case" apart.
    if result.rowcount > 0:
        updated_stock = get_stock(
            db,
            product_id=product_id,
            branch_id=branch_id
        )
        return updated_stock.quantity
    # Row count 0 means failure, we try to get stock to determine
    #   it fails because "no matching row" OR "insufficient stock"
    stock = get_stock(db, product_id=product_id, branch_id=branch_id)
    if stock is None:
        return None
    raise InsufficientStockError(available=stock.quantity)


# ==== "Global Stock read methods" (used by Internal API) ====
def list_stocks_for_product(db: Session, *, product_id: int) -> list[Stock]:
    all_product_stocks_stmt = select(Stock).where(Stock.product_id == product_id)
    return db.scalars(all_product_stocks_stmt).all()


def list_stocks_for_branch(db: Session, *, branch_id: int) -> list[Stock]:
    all_stocks_for_branch_stmt = select(Stock).where(Stock.branch_id == branch_id)
    return db.scalars(all_stocks_for_branch_stmt).all()


def set_stock(db: Session, *, product_id: int, branch_id: int, quantity: int) -> int:
    """(re)Sets the quantity for a given stock — usage : setup/reset entre tests"""
    stock = get_stock(db, product_id=product_id, branch_id=branch_id)
    if stock:
        stock.quantity = quantity
    else:
        stock = Stock(branch_id=branch_id, product_id=product_id, quantity=quantity)
        db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock.quantity


def delete_stock(db: Session, *, product_id: int, branch_id: int) -> bool:
    """Entirely deletes a row from Stocks table"""
    from sqlalchemy import delete
    stmt = delete(Stock).where(
        Stock.product_id == product_id,
        Stock.branch_id == branch_id
    )
    db.execute(stmt)
    db.commit()

# ========================= USERS RELATED CRUD =========================
def list_users(db: Session):
    """Returns as a list of ORM Users all users in database"""
    ls_usrs_stmt = select(User).order_by(User.id, User.role)
    users_list = db.scalars(ls_usrs_stmt).all()
    return users_list


def create_user(
    db: Session, user_name: str, pwd_hash: str,
    role: UserRole = UserRole.MANAGER, branch_id: int | None = None
) -> User:
    # Business rule: an Admin must not be associated with a branch
    if role == UserRole.ADMIN:
        branch_id = None
    new_user = User(
        name=user_name,
        password_hash=pwd_hash,
        role=role,
        branch_id=branch_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_name(db: Session, user_name: str):
    """Returning the one user which user_name matches input
        Used by login
    """
    find_usr_stmt = select(User).where(User.name == user_name)
    matching_usr = db.scalars(find_usr_stmt).first()
    return matching_usr


def reset_user_password(db: Session, *, user_id: int, password_hash: str) -> bool:
    """Resets a given user's password, identified by its id"""
    result = db.execute(
        update(User).where(User.id == user_id).values(password_hash=password_hash)
    )
    db.commit()
    return result.rowcount > 0


from typing import Optional  # Import specific to this method
def assign_branch(db: Session, *, user_id: int, branch_id: int | None = None) -> bool:
    """Changes the branch a user is associated with IF user is Manager"""
    result = db.execute(
        update(User)
        .where(User.id == user_id, User.role == UserRole.MANAGER)
        .values(branch_id=branch_id)
    )
    db.commit()
    return result.rowcount > 0


def set_user_active_state(db: Session, *, user_id: int, is_active: bool) -> bool:
    result = db.execute(
        update(User).where(User.id == user_id).values(is_active=is_active)
    )
    db.commit()
    return result.rowcount > 0


# ========================= BRANCHES RELATED CRUD =========================
def list_branches(db: Session) -> list[Branch]:
    all_branches_infos_stmt = select(Branch)
    return db.scalars(all_branches_infos_stmt).all()


def list_branches_ordered_by_label(db: Session):
    ordered_branches_stmt = select(Branch).order_by(Branch.label)
    return db.scalars(ordered_branches_stmt).all()


def get_branches_with_active_managers(db: Session):
    stmt = select(Branch).options(selectinload(Branch.managers)).order_by(Branch.label)
    return db.scalars(stmt).all()


def find_branches_by_name(db: Session, *, search_string: str) -> List[Branch]:
    """Returns branches which label 'has' search_string, ordered by label"""
    matching_branches_stmt = (
        select(Branch)
        .where(Branch.label.ilike(f"%{search_string}%"))
        .order_by(Branch.label)
    )
    return list(db.scalars(matching_branches_stmt).all())
