"""
Defines the SQLModel tables
"""
from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field
# if table=True tells SQLModel this is a table
# 'id' is an auto-increment primary key
# includes a few fields to use when calling Marvel's API
class Comic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author: Optional[str] = None
    onsale_date: Optional[date] = None  # filter by week
    format: Optional[str] = None        # ie.) "Comic", "Trade Paperback"
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
