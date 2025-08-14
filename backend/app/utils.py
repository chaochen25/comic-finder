# backend/app/utils.py
#this classed was created with the help of AI
#it helps parse date data from obj to string, check for empty data, etc
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Optional, Tuple
#parse date obj
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
    if w.weekday() != 2:
        delta = (w.weekday() - 2) % 7
        w = w - timedelta(days=delta)
    start = w
    end = w + timedelta(days=6)
    return start, end
