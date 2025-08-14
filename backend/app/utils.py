# backend/app/utils.py
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

def parse_ymd(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        y, m, d = [int(x) for x in s[:10].split("-")]
        return date(y, m, d)
    except Exception:
        return None

def ymd(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def week_window_from_wed(wed_s: str) -> Tuple[date, date]:
    """Given a YYYY-MM-DD that is a Wednesday, return inclusive [Wed, Tue]."""
    w = parse_ymd(wed_s)
    if not w:
        raise ValueError("Invalid date: Use YYYY-MM-DD")
    # If not a Wednesday (2 = Wednesday? No: Mon=0, Tue=1, Wed=2)
    # Python: Monday=0 ... Sunday=6
    if w.weekday() != 2:
        # snap back to the most recent Wednesday before/at this date
        delta = (w.weekday() - 2) % 7
        w = w - timedelta(days=delta)
    start = w
    end = w + timedelta(days=6)
    return start, end
