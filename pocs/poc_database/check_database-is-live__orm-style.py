#!/usr/bin/env python3
# ============ DATABASE MODELS MAPPING ==================
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Class de base dont héritent tous nos modèles
class Base(DeclarativeBase):
    pass

class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relation ORM : Permet d'accéder directement aux utilisateurs de cette branche
    # (ex: ma_branche.users)
    users: Mapped[List["User"]] = relationship(back_populates="branch")

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_role: Mapped[str] = mapped_column(String(15), nullable=False)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branches.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relation ORM : Permet d'accéder directement à l'objet Branch associé
    # (ex: mon_utilisateur.branch.label)
    branch: Mapped[Optional[Branch]] = relationship(back_populates="users")

    # Déclaration de la contrainte CHECK
    __table_args__ = (
        CheckConstraint("user_role IN ('admin', 'manager')", name="chk_user_role"),
    )

# ============ DATABSE INTERACTIONS ===========================
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


# 1. Connexion
DATABASE_URL = "mysql+pymysql://root:H0lb3rt0n@localhost:3306/holberton_inventory"
engine = create_engine(DATABASE_URL, echo=False)

# (Optionnel) Si tes tables n'existaient pas déjà via le script SQL d'init, 
# SQLAlchemy pourrait les créer avec cette ligne :
# Base.metadata.create_all(engine)


# 2. Utilisation de la Session avec un context manager (with)
with Session(engine) as session:

    # ---------------------------------------------------------
    # A. INSERTION (CREATE)
    # ---------------------------------------------------------
    print("--- Création des données ---")
    
    # On instancie les objets Python
    hq_branch = Branch(label="Siège Paris")
    
    admin_user = User(
        user_name="alice",
        password_hash="super_hash_123",
        user_role="admin",
        is_active=True,
        branch=hq_branch  # SQLAlchemy lie automatiquement la branche et sa clé étrangère !
    )
    
    # Ajout à la session et sauvegarde dans la base
    session.add(hq_branch)
    session.add(admin_user)
    session.commit()
    print("Données insérées avec succès.")

    # ---------------------------------------------------------
    # B. LECTURE (READ)
    # ---------------------------------------------------------
    print("\n--- Lecture des utilisateurs ---")
    
    # Syntaxe SQLAlchemy 2.0 : select(Classe).where(...)
    stmt = select(User).where(User.user_role == "admin")
    
    # scalars() extrait les objets 'User' directement
    users = session.scalars(stmt).all()
    
    for u in users:
        # Grâce aux 'relationship', on peut lire le nom de la branche sans faire de JOIN manuel !
        branch_name = u.branch.label if u.branch else "Sans branche"
        print(f"User: {u.user_name} | Rôle: {u.user_role} | Branche: {branch_name}")

    # ---------------------------------------------------------
    # C. MISE À JOUR (UPDATE)
    # ---------------------------------------------------------
    print("\n--- Mise à jour ---")
    user_to_update = session.scalars(select(User).where(User.user_name == "alice")).first()
    if user_to_update:
        user_to_update.is_active = False # On modifie juste l'attribut Python
        session.commit()                # SQLAlchemy détecte le changement et génère l'UPDATE
        print(f"{user_to_update.user_name} est maintenant inactif.")

    # ---------------------------------------------------------
    # D. SUPPRESSION (DELETE)
    # ---------------------------------------------------------
    # session.delete(user_to_update)
    # session.commit()
