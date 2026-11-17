"""IMMY — сохранение прогресса (монеты, самоцветы, EXP, уровни, кампании, достижения) в JSON."""

import json

from .config import SAVE_FILE
from .heroes import HEROES, STANDARD_KEYS

DEFAULT_STATS = {"wins": 0, "bosses": 0, "waves": 0, "specials": 0, "ults": 0,
                 "finishers": 0, "parries": 0, "max_combo": 0, "coins_earned": 0,
                 "buys": 0, "camp_stages": 0, "camps": 0, "strikes": 0, "injuries": 0,
                 "myth_ults": 0, "chests": 0, "gems_earned": 0}


def default_save():
    return {"coins": 0, "gems": 0, "bot_level": 1, "owned": list(STANDARD_KEYS), "exp": 0,
            "plvl": 1, "camp": {}, "camp_claimed": [], "ach": [],
            "stats": dict(DEFAULT_STATS)}


def load_save():
    d = default_save()
    try:
        with open(SAVE_FILE) as fp:
            raw = json.load(fp)
    except Exception:
        return d
    if not isinstance(raw, dict):
        return d
    d["coins"] = int(raw.get("coins", 0))
    d["gems"] = max(0, int(raw.get("gems", 0)))
    d["bot_level"] = max(1, int(raw.get("bot_level", 1)))
    owned = [k for k in raw.get("owned", []) if k in HEROES]
    d["owned"] = owned if owned else list(STANDARD_KEYS)
    d["exp"] = max(0, int(raw.get("exp", 0)))
    d["plvl"] = max(1, int(raw.get("plvl", 1)))
    camp = raw.get("camp", {})
    d["camp"] = {str(k): dict(v) for k, v in camp.items()} if isinstance(camp, dict) else {}
    claimed = raw.get("camp_claimed", [])
    d["camp_claimed"] = [x for x in claimed if isinstance(x, int)] if isinstance(claimed, list) else []
    ach = raw.get("ach", [])
    d["ach"] = [x for x in ach if isinstance(x, str)] if isinstance(ach, list) else []
    stats = raw.get("stats", {})
    if isinstance(stats, dict):
        for k, v in DEFAULT_STATS.items():
            d["stats"][k] = max(0, int(stats.get(k, 0)))
    return d


def save_save(d):
    try:
        with open(SAVE_FILE, "w") as fp:
            json.dump(d, fp)
    except Exception:
        pass
