# backend/app/db.py
from __future__ import annotations
from sqlmodel import SQLModel, create_engine
from .config import DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def init_db() -> None:
    from .models import Comic  # ensure models are imported
    SQLModel.metadata.create_all(engine)
