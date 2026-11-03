from datetime import date

import pytest
from app.memories import anniversary_days


@pytest.mark.parametrize(
    "start,annual,today,elapsed,remaining,next_date",
    [
        ("2024-11-03", True, "2026-11-03", 730, 0, "2026-11-03"),
        ("2026-12-31", True, "2027-01-01", 1, 364, "2027-12-31"),
        ("2024-02-29", True, "2025-02-27", 364, 1, "2025-02-28"),
        ("2027-11-03", True, "2026-11-03", -365, 365, "2027-11-03"),
        ("2026-07-01", False, "2026-07-02", 1, None, None),
    ],
)
def test_anniversary_calendar(start, annual, today, elapsed, remaining, next_date):
    assert anniversary_days(
        date.fromisoformat(start), annual, date.fromisoformat(today)
    ) == {
        "elapsed_days": elapsed,
        "days_until": remaining,
        "next_date": next_date,
    }
