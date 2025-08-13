"""
Creates a SQLModel database and the helper to create tables
"""
from sqlmodel import SQLModel, create_engine
from .config import DATABASE_URL

# lets you see SQL queries in the terminal while developing
engine = create_engine(DATABASE_URL, echo=True)

def init_db() -> None:
    # create database tables if they don't already exist
    SQLModel.metadata.create_all(engine)
