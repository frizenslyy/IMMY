"""IMMY — сохранение прогресса (монеты, уровень бота) в JSON."""

import json

from .config import SAVE_FILE


def load_save():
    try:
        with open(SAVE_FILE) as fp:
            d = json.load(fp)
        return int(d.get("coins", 0)), int(d.get("bot_level", 1))
    except Exception:
        return 0, 1


def save_save(coins, level):
    try:
        with open(SAVE_FILE, "w") as fp:
            json.dump({"coins": coins, "bot_level": level}, fp)
    except Exception:
        pass
