"""
Inserts a few sample comics so you can test the API before using Marvel's API.
"""
from datetime import date
from sqlmodel import Session
from .db import engine, init_db
from .models import Comic

def run():
    init_db()
    samples = [
        Comic(title="Fantastic Four #1", author="Ryan North", onsale_date=date(2025, 8, 6), format="Comic",
              thumbnail_url=None, description="The First Family returns."),
        Comic(title="Amazing Spider-Man #100", author="Zeb Wells", onsale_date=date(2025, 8, 13), format="Comic"),
        Comic(title="X-Men: Red Vol. 1", author="Al Ewing", onsale_date=date(2025, 8, 20), format="Trade Paperback"),
        Comic(title="Avengers Annual 2025", author="Jed MacKay", onsale_date=date(2025, 8, 27), format="Comic"),
    ]
    with Session(engine) as session:
        # avoid duplicates
        for c in samples:
            exists = session.exec(
                # simple check by title + onsale_date
                Comic.select().where((Comic.title == c.title) & (Comic.onsale_date == c.onsale_date))
            ).first()
            if not exists:
                session.add(c)
        session.commit()
    print("Seed complete.")

if __name__ == "__main__":
    run()
