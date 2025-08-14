#db.py
from __future__ import annotations
from sqlmodel import SQLModel, create_engine
from .config import DATABASE_URL
#args are required for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
#create db using URL
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
## ensure comic models are imported
def init_db() -> None:
    from .models import Comic 
    SQLModel.metadata.create_all(engine)
