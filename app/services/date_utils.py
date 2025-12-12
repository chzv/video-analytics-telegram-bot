from __future__ import annotations

from datetime import datetime
from typing import Tuple, Optional

import dateparser


def parse_date_string(value: str) -> datetime:
    if not value:
        raise ValueError("Empty date string")

    dt = dateparser.parse(value, languages=["ru", "en"])
    if dt is None:
        raise ValueError(f"Could not parse date from string: {value!r}")
    return dt


def parse_date_range(natural_text: str) -> Tuple[datetime, datetime]:
    text = natural_text.strip()
    if not text:
        raise ValueError("Empty natural_text for date range")

    if text.lower().startswith("с "):
        text = text[2:].strip()

    lower = text.lower()
    if " по " in lower:
        parts = text.split(" по ", maxsplit=1)
        left_raw = parts[0].strip()
        right_raw = parts[1].strip()

        start_dt = parse_date_string(left_raw)
        end_dt = parse_date_string(right_raw)
        return start_dt, end_dt

    single = parse_date_string(text)
    return single, single


def ensure_date_range(
    start_str: Optional[str],
    end_str: Optional[str],
) -> Tuple[Optional[datetime], Optional[datetime]]:

    start_dt = parse_date_string(start_str) if start_str else None
    end_dt = parse_date_string(end_str) if end_str else None
    return start_dt, end_dt
