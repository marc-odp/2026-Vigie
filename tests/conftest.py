import pytest

@pytest.fixture(name="session")
def session_fixture():
    from sqlmodel import SQLModel, create_engine, Session
    # Use an in-memory SQLite database for tests
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="default_categories")
def default_categories_fixture(session):
    from sqlmodel import select
    from app.models.domain import Category
    from app.services.bootstrap import bootstrap_categories
    bootstrap_categories(session)
    return session.exec(select(Category)).all()

@pytest.fixture(name="test_account")
def test_account_fixture(session):
    from app.models.domain import BankAccount
    acc = BankAccount(name="Test Account", IBAN="BE0000000000")
    session.add(acc)
    session.commit()
    session.refresh(acc)
    return acc

@pytest.fixture(name="test_lot")
def test_lot_fixture(session):
    from app.models.domain import Lot
    lot = Lot(name="Test Lot")
    session.add(lot)
    session.commit()
    session.refresh(lot)
    return lot
