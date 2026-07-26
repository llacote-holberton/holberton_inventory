#!/usr/bin/env python
"""Module dedicated to actual CRUD operations on database"""
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from models import Stock
from models import User

# ========================= STOCK RELATED CRUD =========================

# Warning: session is not created inside but "must" provided "externally", why?
#   a) To allow efficient "mockup testing" (one can test the function while
#      targeting an entirely different database, typically a SQLite "test base".
#   b) To be able to "compose a SQL commit" by propagating the same Session
#      to several "crud functions" and make a single SQL Transaction in the end
#      (ex: reducing several stocks to reflect an order shipped).
#   c) To allow reuse of the crud function in different contexts which have
#      their own "session lifecycle"
# Basically it's "dependency injection" fully applied.
def get_stock(db: Session, *, product_id: int, branch_id: int) -> Stock | None:
    return (
        db.query(Stock)
        .filter(Stock.product_id == product_id, Stock.branch_id == branch_id)
        # REQUIRED even if only one actual row matching because
        #   the return of Query is always a List.
        .first()
        # NOTE: returns None because only role of that function is
        #   "tell the truth about table state given input".
    )


# Note: the *, in signature forces every following parameter to be provided
#   "as a named argument" instead of "positional argument".
# Required considering how easy it is to swap two integer ids...
def add_stock(db: Session, *, product_id: int, branch_id: int, amount: int) -> int:
    """Adds/update 'stock row' and returns the updated quantity"""
    # Step 1: adding stock.
    # Using special function to create a Statement object to use neat function.
    # Note: 'stmt' stands for (SQL) statement meaning "declarational query".
    stmt = mysql_insert(Stock).values(
        branch_id=branch_id, product_id=product_id, quantity=amount
    )
    # Function being one that either "INSERTS" or "UPDATES" if row exists.
    stmt = stmt.on_duplicate_key_update(quantity=Stock.quantity + amount)
    try:
        db.execute(stmt)
        db.commit()
    except IntegrityError:
        # Completely cancels the whole transaction.
        db.rollback()
        # Propagates the exception so caller can decide what to do with it.
        raise
    # Step 2: returning updated amount by reading it from the table (as we
    #   never read it before updating + another write could have happened)
    return (get_stock(db, product_id=product_id, branch_id=branch_id)).quantity

# Required because...
# 1/ We want to keep signature of remove_stock simple, inline with others
#     so just return "int" as "quantity post-update".
#   A dict with "success: bool, message: reason, quantity: int|None"
#     would mix up responsabilities between CRUD and API.
# BUT just returning "Int or None" would leave a compromise on failure case.
#   "None because no stock row in the first place"?
#   OR "Not enough existing stock to fulfill the remove request"
class InsufficientStockError(Exception):
    def __init__(self, available: int):
        self.available = available
        super().__init__(f"insufficient stock: {available} available")


def remove_stock(db: Session, branch_id: int,
                 product_id: int, amount: int) -> int | None:
    result = db.execute(
        update(Stock)
        .where(Stock.branch_id == branch_id, Stock.product_id == product_id,
                # Essential "defensive condition" to prevent trying to make a
                #   substraction which would end with a constraint violation
                #   of "quantity must not be below 0".
                # And because we decide to reject query instead of "altering"
                #   to "reduce up to 0" it is the best way.
                # As if there is not enough quantity in stock then there will
                #   be 0 row to update...
                # So not even any need to anticipate a potential rollback.
                Stock.quantity >= amount)
        .values(quantity=Stock.quantity - amount)
    )
    db.commit()
    stock = get_stock(db, product_id=product_id, branch_id=branch_id)
    # Optimal: row exists, quantity was enough for substraction.
    if result.rowcount > 0:
        return get_stock(db, product_id=product_id,
                         branch_id=branch_id).quantity
    # Business failure 1: no preexisting stock for product in branch
    if stock is None:
        return None
    # Business failure 2: removal request beyond available stock
    raise InsufficientStockError(available=stock.quantity)


# WARNING: ONLY USE FOR INTERNAL TESTS, do NOT EXPOSE.
def set_stock(db: Session, *, product_id: int, branch_id: int, quantity: int) -> int:
    """(re)Sets the quantity for a given stock — usage : setup/reset entre tests"""
    stock = get_stock(db, product_id=product_id, branch_id=branch_id)
    if stock:
        stock.quantity = quantity
    else:
        stock = Stock(branch_id=branch_id, product_id=product_id, quantity=quantity)
        db.add(stock)
    db.commit()
    db.refresh(stock)  # Forces a db re-read to make object attributes up to date
    return stock.quantity


# WARNING: ONLY USE FOR INTERNAL TESTS.
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
    ls_usrs_stmt = select(User).order_by(User.id, User.role)
    # Scalar is the combination of "execute query" and "unwrap tuples"
    #   returned by db as model objects (here Users)
    users_list = db.scalars(ls_usrs_stmt).all()
    return users_list


# ========================= Quick & dirty self-tests =========================
if __name__ == "__main__":
    # On the fly import just for quick and dirty "self-test"
    # Note: we don't use the get_db() because get_db just returns
    #   a session generator (yield db) which is usually managed
    #   automatically by FastAPI (next(db)).
    # So simpler to just generate a session "manually" here.
    from database import SessionLocal

    # ==== STOCK crud tests =====
    def stock_crud_tests():
        db = SessionLocal()
        try:
            # === READ OPERATIONS ===
            # Should get "no line found"
            result = get_stock(db, product_id=32, branch_id=1)
            print(result.quantity if result else "No such product in branch")
            # Should return 15
            result = get_stock(db, product_id=4, branch_id=1)
            print(result.quantity if result else "No such product in branch")

            # === ADD OPERATIONS ===
            # Add 55 amount to a row of branch 4, product 6, previously had 0
            print("Amount of Mecha Keyboard (6) in Caussade before update: ",
                (get_stock(db, product_id=6, branch_id=4)).quantity)
            updated = add_stock(db, product_id=6, branch_id=4, amount=55)
            print(f"Amount after adding 55 should be {updated}: ", 
                (get_stock(db, product_id=6, branch_id=4)).quantity)
            # Adds new row: 1000 amount of pid 40 (HB-LGT-1801) to branch 5.
            # Perfect illustration of how to crash app by inverting ids XD
            # newrow = (add_stock(db, 5, 40, 1000)).quantity
            nr = add_stock(db, product_id=40, branch_id=5, amount=1000)
            print("New row added as confirmed by amount: ", nr)

            # === RESET ===
            set_stock(db, product_id=4, branch_id=1, quantity=15)
            set_stock(db, product_id=6, branch_id=4, quantity=0)
            delete_stock(db, product_id=40, branch_id=5)

            # Test adds new line
            set_stock(db, product_id=35, branch_id=5, quantity=500)

            # === REMOVE OPERATIONS ===
            # Reduce stock just created from 500 to 400
            remove_stock(db, product_id=35, branch_id=5, amount=100)
            # Then back to exactly 0 (still valid operation)
            remove_stock(db, product_id=35, branch_id=5, amount=400)

            # Attempt to reduce by too big of an amount
            remove_stock(db, product_id=6, branch_id=4, amount=9999)
            # Attempt to reduce inexisting stock
            remove_stock(db, product_id=666, branch_id=666, amount=666)
        except Exception as e:
            print(e)
        finally:
            db.close()

    # === Users Crud tests ===
    users_session = SessionLocal()
    print(list_users(users_session))
