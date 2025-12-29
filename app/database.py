import os

from sqlmodel import SQLModel, create_engine, Session

sqlite_data_dir = os.getenv("VIGIE_DATA_DIR", "/app/data")
sqlite_url = f"sqlite:///{sqlite_data_dir}/vigie.db"

# Enable WAL mode and busy_timeout for concurrency
connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    # Helper to enable WAL mode
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL;")
        connection.exec_driver_sql("PRAGMA synchronous=NORMAL;")
    
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
