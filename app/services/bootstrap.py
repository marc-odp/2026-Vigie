from app.database import get_session
from app.services.auth import get_password_hash
from app.models.domain import Owner, UserRole, Category, Operation, OperationType, OperationCategory
from sqlmodel import select

def bootstrap_categories(session):
    """
    Populates the Category table with defaults if empty.
    """
    categories = session.exec(select(Category)).all()
    if not categories:
        print("Categories empty. Creating default categories...")
        # Map some categories to ENTREE/SORTIE
        # LOYER/REVERSEMENT/FRAIS_BANCAIRES are sorted out
        for cat_enum in OperationCategory:
            cat_type = OperationType.SORTIE
            if cat_enum == OperationCategory.LOYER:
                cat_type = OperationType.ENTREE
            
            new_cat = Category(
                name=cat_enum.value, 
                type=cat_type,
                is_reversement=(cat_enum == OperationCategory.REVERSEMENT)
            )
            session.add(new_cat)
        session.commit()
        print("Default categories created.")

from sqlalchemy import text

def migrate_operations_to_categories(session):
    """
    Migrates existing operations to use category_id based on the old category column.
    """
    # Check if the legacy 'category' column still exists in the table
    try:
        session.exec(text("SELECT category FROM operation LIMIT 1"))
    except Exception:
        # Column likely dropped, migration no longer possible/needed
        return
    
    # Check if there are any operations without category_id
    res = session.exec(text("SELECT id, category FROM operation WHERE category_id IS NULL")).all()
    if not res:
        return
    
    print(f"Migrating {len(res)} operations to categories...")
    
    # Pre-fetch all categories for lookup
    categories = session.exec(select(Category)).all()
    cat_map = {c.name.upper(): c.id for c in categories}
    
    for op_id, old_cat in res:
        if old_cat and old_cat.upper() in cat_map:
            new_id = cat_map[old_cat.upper()]
            session.execute(text("UPDATE operation SET category_id = :cat_id WHERE id = :op_id"), 
                            {"cat_id": new_id, "op_id": op_id})
    
    session.commit()
    print("Migration complete.")

def bootstrap_data():
    """
    Creates initial data and runs migrations.
    """
    with next(get_session()) as session:
        # 1. Categories Bootstrap & Migration
        bootstrap_categories(session)
        migrate_operations_to_categories(session)

        # 2. Owners Bootstrap
        owners = session.exec(select(Owner)).all()
        if not owners:
            print("Database empty. Creating initial admin user...")
            admin = Owner(
                name="Administrateur",
                email="admin@vigie.local",
                role=UserRole.ADMIN,
                theme="DARK",
                password_hash=get_password_hash("vigie2026")
            )
            session.add(admin)
            session.commit()
            print("Admin user created: admin@vigie.local / vigie2026")
