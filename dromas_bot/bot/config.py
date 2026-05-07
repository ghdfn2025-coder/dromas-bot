from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "dromas_data.json"

load_dotenv(BASE_DIR / ".env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GUILD_ID_RAW = os.getenv("GUILD_ID", "").strip()
GUILD_ID = int(GUILD_ID_RAW) if GUILD_ID_RAW.isdigit() else None

KST_TIMEZONE = "Asia/Seoul"
MAX_DROMAS_PER_USER = 5
MIN_DROMAS_NAME_LENGTH = 2
MAX_DROMAS_NAME_LENGTH = 10

DAILY_LIMITS = {
    "feed": 5,
    "play": 10,
    "explore": 3,
}

COOLDOWNS_SECONDS = {
    "feed": 60,
    "play": 60,
    "explore": 120,
}

INITIAL_STATS = {
    "level": 1,
    "exp": 0,
    "mood": 70,
    "satiety": 70,
    "bond": 0,
    "explore_count": 0,
}
