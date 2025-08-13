from datetime import date
from sqlmodel import Session, select
from .db import engine, init_db
from .models import Comic

def run():
    print("Starting seed...")
    init_db()
    samples = [
        Comic(title="Fantastic Four #1", author="Ryan North", onsale_date=date(2025, 8, 6), format="Comic"),
        Comic(title="Amazing Spider-Man #100", author="Zeb Wells", onsale_date=date(2025, 8, 13), format="Comic"),
        Comic(title="X-Men: Red Vol. 1", author="Al Ewing", onsale_date=date(2025, 8, 20), format="Trade Paperback"),
        Comic(title="Avengers Annual 2025", author="Jed MacKay", onsale_date=date(2025, 8, 27), format="Comic"),
    ]
    inserted = 0
    with Session(engine) as session:
        for c in samples:
            exists = session.exec(
                select(Comic).where((Comic.title == c.title) & (Comic.onsale_date == c.onsale_date))
            ).first()
            if not exists:
                session.add(c)
                inserted += 1
        session.commit()
    print(f"Seed complete. Inserted {inserted} new rows.")

if __name__ == "__main__":
    run()
