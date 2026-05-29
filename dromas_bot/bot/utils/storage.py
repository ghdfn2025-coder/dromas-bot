from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from bot.config import DATA_DIR, DATA_FILE, INITIAL_STATS
from bot.utils.time import today_key, week_key

DEFAULT_DATA: dict[str, Any] = {
    "users": {},
    "fortunes": {},
    "record_week": week_key(),
}


class DataStore:
    def __init__(self, path: Path = DATA_FILE) -> None:
        self.path = path
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.save(deepcopy(DEFAULT_DATA))

    def load(self) -> dict[str, Any]:
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = deepcopy(DEFAULT_DATA)

        data.setdefault("users", {})
        data.setdefault("fortunes", {})
        data.setdefault("record_week", week_key())

        self.ensure_weekly_reset(data)

        return data

    def save(self, data: dict[str, Any]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        temp_path = self.path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        temp_path.replace(self.path)

    def ensure_weekly_reset(self, data: dict[str, Any]) -> None:
        current_week = week_key()

        if data.get("record_week") == current_week:
            return

        for user_data in data.get("users", {}).values():
            for dromas in user_data.get("dromases", []):
                name = dromas.get("name", "이름 없는 드로마스")

                dromas.clear()
                dromas["name"] = name
                dromas.update(deepcopy(INITIAL_STATS))
                dromas["daily"] = self._fresh_daily()

        data["record_week"] = current_week
        self.save(data)

    def get_user(self, data: dict[str, Any], user_id: int) -> dict[str, Any]:
        uid = str(user_id)
        users = data.setdefault("users", {})

        if uid not in users:
            users[uid] = {"dromases": []}

        users[uid].setdefault("dromases", [])

        return users[uid]

    def find_dromas(self, user_data: dict[str, Any], name: str) -> dict[str, Any] | None:
        for dromas in user_data.get("dromases", []):
            if dromas.get("name") == name:
                return dromas

        return None

    def create_dromas(self, name: str) -> dict[str, Any]:
        dromas = {"name": name}
        dromas.update(deepcopy(INITIAL_STATS))
        dromas["daily"] = self._fresh_daily()

        return dromas

    def ensure_daily(self, dromas: dict[str, Any]) -> None:
        daily = dromas.setdefault("daily", self._fresh_daily())

        if daily.get("date") != today_key():
            dromas["daily"] = self._fresh_daily()

    def _fresh_daily(self) -> dict[str, Any]:
        return {
            "date": today_key(),
            "feed": 0,
            "play": 0,
            "explore": 0,
            "last_feed": 0,
            "last_play": 0,
            "last_explore": 0,
            "last_enhance": 0,
        }


store = DataStore()
