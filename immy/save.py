"""IMMY — сохранение прогресса (монеты, уровень бота, купленные бойцы) в JSON."""

import json

from .config import SAVE_FILE
from .heroes import HEROES, STANDARD_KEYS


def load_save():
    try:
        with open(SAVE_FILE) as fp:
            d = json.load(fp)
        coins = int(d.get("coins", 0))
        level = int(d.get("bot_level", 1))
        owned = [k for k in d.get("owned", []) if k in HEROES]
        if not owned:
            owned = list(STANDARD_KEYS)
        return coins, level, owned
    except Exception:
        return 0, 1, list(STANDARD_KEYS)


def save_save(coins, level, owned):
    try:
        with open(SAVE_FILE, "w") as fp:
            json.dump({"coins": coins, "bot_level": level, "owned": list(owned)}, fp)
    except Exception:
        pass
