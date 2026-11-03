import calendar
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ATLAS = json.loads(
    (Path(__file__).parent / "data/atlas.json").read_text(encoding="utf-8")
)
CITY_IDS = {city["id"] for city in ATLAS["cities"]}


def anniversary_days(start: date, annual: bool, today: date | None = None):
    today = today or datetime.now(ZoneInfo("Asia/Shanghai")).date()
    upcoming = start
    if annual and start < today:

        def occurrence(year: int):
            # Celebrate leap-day anniversaries on Feb 28 in a non-leap year.
            return date(
                year,
                start.month,
                min(start.day, calendar.monthrange(year, start.month)[1]),
            )

        upcoming = occurrence(today.year)
        if upcoming < today:
            upcoming = occurrence(today.year + 1)
    return {
        "elapsed_days": (today - start).days,
        "next_date": upcoming.isoformat() if upcoming >= today else None,
        "days_until": (upcoming - today).days if upcoming >= today else None,
    }
