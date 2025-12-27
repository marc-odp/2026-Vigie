from sqlmodel import Session, select
from app.models.domain import Category, OperationType
from app.services.bootstrap import bootstrap_categories

def test_bootstrap_categories(session: Session):
    bootstrap_categories(session)
    cats = session.exec(select(Category)).all()
    assert len(cats) >= 10
    
    names = [c.name for c in cats]
    assert "LOYER" in names
    assert "REVERSEMENT" in names
    
    rev_cat = session.exec(select(Category).where(Category.name == "REVERSEMENT")).first()
    assert rev_cat.is_reversement is True

def test_add_custom_category(session: Session):
    new_cat = Category(name="Internet", type=OperationType.SORTIE, is_reversement=False)
    session.add(new_cat)
    session.commit()
    
    saved = session.exec(select(Category).where(Category.name == "Internet")).first()
    assert saved.id is not None
    assert saved.type == OperationType.SORTIE
