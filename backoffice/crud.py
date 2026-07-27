#!/usr/bin/env python
"""Module dedicated to actual CRUD operations on database"""
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from db_models import Stock
from db_models import User, UserRole

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


# ==== "Global Stock read methods" (used by Internal API) ====
# Reminder: signature with list return works natively from >=3.9
def list_stocks_for_product(db: Session, *, product_id: int) -> list[Stock]:
    all_product_stocks_stmt = select(Stock).where(Stock.product_id == product_id)
    # Reminder: no need for try since it's a read only, worse case returns empty list.
    return db.scalars(all_product_stocks_stmt).all()


def list_stocks_for_branch(db: Session, * , branch_id: int) -> list[Stock]:
    all_stocks_for_branch_stmt = select(Stock).where(Stock.branch_id == branch_id)
    return db.scalars(all_stocks_for_branch_stmt).all()


# ==== TESTMETHODS (FIXME check if can be removed once automated tests ====
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
    """Returns as a list of ORM Users all users in database"""
    ls_usrs_stmt = select(User).order_by(User.id, User.role)
    # Scalar is the combination of "execute query" and "unwrap tuples"
    #   returned by db as model objects (here Users)
    users_list = db.scalars(ls_usrs_stmt).all()
    return users_list


# NOTE: expects hash for password to be already computed
def create_user(
    db: Session, user_name: str, pwd_hash: str,
    role: UserRole = UserRole.MANAGER, branch_id: int | None = None
) -> User:
    new_user = User(
        name=user_name,
        password_hash=pwd_hash,
        role=role,
        branch_id=branch_id,
        is_active=True
    )
    # Adds an object to the list of "pending changes" in Session.
    #   Nothing actually done SQL-wise yet.
    db.add(new_user)
    # Generates the actual SQL INSERT query, waits for SQL to confirm,
    # By a COMMIT command in MariaDB. From there change is visible by
    #   other connexions to Db, if any.
    db.commit()
    # Reads the line just created in Db to retrieve the auto-generated id
    db.refresh(new_user)
    return new_user


def get_user_by_name(db: Session, user_name: str):
    """Returning the one user which user_name matches input
       Used by login
    """
    # FIXME what if None given as user_name ??
    find_usr_stmt = select(User).where(User.name == user_name)
    # Not the best method here, returns a tuple of single object
    # ex (<db_models.User object at 0x77ab7a1d5940>,)
    # matching_usr = db.execute(find_usr_stmt).first()
    matching_usr = db.scalars(find_usr_stmt).first()
    # Scalar unwraps the first element so we directly have the User "inside".
    return matching_usr

# Note: because we try to keep the principle that CRUD methods just
#  interact with database with "prepared values", this method requires
#  an already hashed password "ready to store".
def reset_user_password(db: Session, *, user_id: int, password_hash: str) -> bool:
    """Resets a given user's password, identified by its id"""
    result = db.execute(
        update(User).where(User.id == user_id).values(password_hash=password_hash)
    )
    db.commit()
    return result.rowcount > 0


def assign_branch(db: Session, *, user_id: int, branch_id: int) -> bool:
    """Changes the branch a user is associated with IF user is Manager"""
    result = db.execute(
        update(User)
        .where(User.id == user_id, User.role == UserRole.MANAGER)
        .values(branch_id=branch_id)
    )
    db.commit()
    # False if inexisting user or had not 'manager' role.
    return result.rowcount > 0


def set_user_active_state(db: Session, *, user_id: int, is_active: bool) -> bool:
    result = db.execute(
        update(User).where(User.id == user_id).values(is_active=is_active)
    )
    db.commit()
    # If no row means user_id didn't exist
    return result.rowcount > 0


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

            # === INTERNAL API's related methods
            # Attempt to get all stock for product of id 4
            details = list_stocks_for_product(db, product_id=4)
            print(details)

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
    def users_crud_tests():
        from auth import hash_password
        users_session = SessionLocal()
        # print(list_users(users_session))

        # print(get_user_by_name(users_session, None))
        # print(get_user_by_name(users_session, "laurent"))

        # Adding a user in Toulouse branch
        # new_user_pwd_hash = hash_password("I am test_user")
        # new_user = create_user(users_session, user_name="test_user", pwd_hash=new_user_pwd_hash, branch_id=1)
        # nu2_hash = hash_password("I am not affected yet")
        # nu2 = create_user(users_session, user_name="SBF", pwd_hash=nu2_hash)
        # FIXME IMPROVE create_user to properly manage exceptions including 
        # "sqlalchemy.exc.IntegrityError: (pymysql.err.IntegrityError) (1062, "Duplicate entry 'test_user' for key 'user_name'")"
        new_admin_pwd_hash = hash_password("admin_password")
        new_admin = create_user(users_session, user_name="test_admin", pwd_hash=new_admin_pwd_hash, role="admin")

    # users_crud_tests()
    stock_crud_tests()
