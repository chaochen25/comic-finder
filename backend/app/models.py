from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint

class Comic(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("marvel_id", name="uq_comic_marvel_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    marvel_id: Optional[int] = None 
    title: str
    author: Optional[str] = None
    onsale_date: Optional[date] = None
    format: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    issue_number: Optional[float] = None
