from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from bot.config import KST_TIMEZONE

KST = ZoneInfo(KST_TIMEZONE)


def now_kst() -> datetime:
    return datetime.now(KST)


def today_key() -> str:
    return now_kst().strftime("%Y-%m-%d")


def week_key() -> str:
    year, week, _ = now_kst().isocalendar()
    return f"{year}-W{week:02d}"


def unix_now() -> int:
    return int(now_kst().timestamp())
