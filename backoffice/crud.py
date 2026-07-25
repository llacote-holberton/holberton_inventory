#!/usr/bin/env python
"""Module dedicated to actual CRUD operations on database"""
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert
from models import Stock

# Warning: session is not created inside but "must" provided "externally", why?
#   a) To allow efficient "mockup testing" (one can test the function while
#      targeting an entirely different database, typically a SQLite "test base".
#   b) To be able to "compose a SQL commit" by propagating the same Session
#      to several "crud functions" and make a single SQL Transaction in the end
#      (ex: reducing several stocks to reflect an order shipped).
#   c) To allow reuse of the crud function in different contexts which have
#      their own "session lifecycle"
# Basically it's "dependency injection" fully applied.
def get_stock(db: Session, product_id: int, branch_id: int) -> Stock | None:
    return (
        db.query(Stock)
        .filter(Stock.product_id == product_id, Stock.branch_id == branch_id)
        # REQUIRED even if only one actual row matching because
        #   the return of Query is always a List.
        .first()
        # NOTE: returns None because only role of that function is
        #   "tell the truth about table state given input".
    )

def add_stock(db: Session, product_id: int, branch_id: int, amount: int) -> int:
    """Adds/update 'stock row' and returns the updated quantity"""
    # Step 1: adding stock.
    # Using special function to create a Statement object to use neat function.
    # Note: 'stmt' stands for (SQL) statement meaning "declarational query".
    stmt = mysql_insert(Stock).values(
        branch_id=branch_id, product_id=product_id, quantity=amount
    )
    # Function being one that either "INSERTS" or "UPDATES" if row exists.
    stmt = stmt.on_duplicate_key_update(quantity=Stock.quantity + amount)
    db.execute(stmt)
    db.commit()
    # Step 2: returning updated amount by reading it from the table (as we
    #   never read it before updating + another write could have happened)
    return (get_stock(db, product_id, branch_id)).quantity

if __name__ == "__main__":
    # On the fly import just for quick and dirty "self-test"
    # Note: we don't use the get_db() because get_db just returns
    #   a session generator (yield db) which is usually managed
    #   automatically by FastAPI (next(db)).
    # So simpler to just generate a session "manually" here.
    from database import SessionLocal
    db = SessionLocal()
    try:
        # === READ OPERATIONS ===
        # Should get "no line found"
        result = get_stock(db, product_id=32, branch_id=1)
        print(result.quantity if result else "No such product in that branch")
        # Should return 15
        result = get_stock(db, product_id=4, branch_id=1)
        print(result.quantity if result else "No such product in that branch")
        # === ADD OPERATIONS ===
        # Add 55 amount to a row of branch_id 4, product_id 6, previously had 0
        print("Amount of Mechanical Keyboard (6) in Caussade before update: ", 
              (get_stock(db, 6, 4)).quantity)
        updated = add_stock(db, 6, 4, 55)
        print("Amount after adding 55: ", 
              (get_stock(db, 6, 4)).quantity)
        # Adds new row: 1000 amount of product_id 40 (HB-LGT-1801) to branch 5.

    finally:
        db.close()
