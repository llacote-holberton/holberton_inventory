#!/usr/bin/env python
"""Module dedicated to actual CRUD operations on database"""
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from db_models import Stock

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
    stmt = stmt.on_duplicate_key_update(quantity=Stock.quantity + amount)
    try:
        db.execute(stmt)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    return (get_stock(db, product_id=product_id, branch_id=branch_id)).quantity


class InsufficientStockError(Exception):
    def __init__(self, available: int):
        self.available = available
        super().__init__(f"insufficient stock: {available} available")


def remove_stock(db: Session, branch_id: int,
                 product_id: int, amount: int) -> int | None:
    result = db.execute(
        update(Stock)
        .where(Stock.branch_id == branch_id, Stock.product_id == product_id,
               Stock.quantity >= amount)
        .values(quantity=Stock.quantity - amount)
    )
    db.commit()
    stock = get_stock(db, product_id=product_id, branch_id=branch_id)
    if result.rowcount > 0:
        return get_stock(db, product_id=product_id,
                         branch_id=branch_id).quantity
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
