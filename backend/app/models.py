from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field

class Comic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    marvel_id: Optional[int] = Field(default=None, index=True, unique=True)
    title: str
    author: Optional[str] = None
    onsale_date: Optional[date] = None
    format: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    issue_number: Optional[float] = None
