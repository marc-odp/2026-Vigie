from sqlmodel import Session, select
from app.models.domain import Operation, OperationType, Category, Allocation
from decimal import Decimal
from datetime import date

def test_create_simple_operation(session: Session, test_account, test_lot, default_categories):
    # Find a category
    cat = session.exec(select(Category).where(Category.name == "LOYER")).first()
    
    op = Operation(
        date=date(2023, 1, 1),
        amount=Decimal("100.00"),
        lot_id=test_lot.id,
        bank_account_id=test_account.id,
        type=OperationType.ENTREE,
        category_id=cat.id,
        label="Loyer reçu"
    )
    session.add(op)
    session.commit()
    
    assert op.id is not None
    assert op.category_id == cat.id

def test_reversement_logic_flag(session: Session, test_account, default_categories):
    # Find the category with is_reversement=True
    rev_cat = session.exec(select(Category).where(Category.is_reversement == True)).first()
    assert rev_cat is not None
    
    # Simulate the logic used in UI: check if category_id is in reversement_ids
    reversement_ids = {c.id for c in session.exec(select(Category)).all() if c.is_reversement}
    assert rev_cat.id in reversement_ids
    
    # Create operation without lot_id (allowed for reversement)
    op = Operation(
        date=date.today(),
        amount=Decimal("50.00"),
        lot_id=None,
        bank_account_id=test_account.id,
        type=OperationType.SORTIE,
        category_id=rev_cat.id,
        label="Reversement test"
    )
    session.add(op)
    session.commit()
    assert op.id is not None
    assert op.lot_id is None
