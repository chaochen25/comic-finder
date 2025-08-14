#models.py
from __future__ import annotations
from datetime import date
from typing import Optional
from sqlmodel import Field, SQLModel
#pulling database models for comics
class Comic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    marvel_id: Optional[int] = Field(index=True, unique=True, default=None)

    title: str
    author: Optional[str] = None
    onsale_date: Optional[date] = Field(default=None, index=True)
    format: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    issue_number: Optional[str] = None
