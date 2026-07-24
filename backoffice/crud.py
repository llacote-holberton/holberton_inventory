#!/usr/bin/env python
"""Module dedicated to actual CRUD operations on database"""
from sqlalchemy.orm import Session
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
        # 
    )


if __name__ == "__main__":
    # On the fly import just for quick and dirty "self-test"
    # Note: we don't use the get_db() because get_db just returns
    #   a session generator (yield db) which is usually managed
    #   automatically by FastAPI (next(db)).
    # So simpler to just generate a session "manually" here.
    from database import SessionLocal
    db = SessionLocal()
    try:
        # Should get "no line found"
        result = get_stock(db, product_id=32, branch_id=1)
        print(result.quantity if result else "No such product in that branch")
        # Should return 15
        result = get_stock(db, product_id=4, branch_id=1)
        print(result.quantity if result else "No such product in that branch")
    finally:
        db.close()
