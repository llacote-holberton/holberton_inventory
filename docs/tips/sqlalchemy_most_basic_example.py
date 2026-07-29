from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 1.MANDATORY STEP FOR SQLAlchemy
# MUST make this "intermediate" even if we don't do anything inside
#   because ORM uses the "inheritance from Base class" to know
#   the list of tables to create when using the command
#   Base.metadata.create_all(engine)
# Other reason is to get all tables under the same "namespace"
#   which allows SQLAlchemy to "read" table relationships to
#   automatically translate "python attribute chain" syntax
#   (ex user.address.city -> column city in table address joined on address_id)
class Base(DeclarativeBase):
    pass

# 2. La table minimale
class Branch(Base):
    # MANDATORY: table name
    __tablename__ = "branches"

    # Mapped is a "glue" code which...
    # 1/ Helps end-user by providing type hints to code editors or 'mypy'
    #    (ex b = branch() --> IDE knows that b.branch_id is expected to be int)
    # 2/ Helps SQLAlchemy know the actual data type and constraints in SQL.
    #    ex1 Mapped[int] -> INTEGER NOT NULL
    #    ex2 Mapped[str | None] (or Optional[str]) -> VARCHAR (NULL)
    #    ex3 Mapped[list["Stock"]] -> defines 1 to N relation to "Stock model"
    branch_id: Mapped[int] = mapped_column(primary_key=True)
    # mapped_column function in Alc2.0 replaces the Column() function from 1.0
    # It is used to define all specific SQL parameters beyond data type.
    # Typically primary keys (confer above), but also unicity or "target index"
    #   ex user_name: Mapped[str] = mapped_column(unique=True, index=True)
    # Or data type related constraints such as length...
    # user_name: Mapped[str] = mapped_column(String(30)) (=> VARCHAR(30))
    # "Default value" and foreign keys
    # quantity: Mapped[int] = mapped_column(default=0)
    # branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))
    # Calling mapped_column is not required IF "data is plain INT or STR".
