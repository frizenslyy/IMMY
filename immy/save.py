"""IMMY — сохранение прогресса (монеты, самоцветы, EXP, уровни, кампании,
достижения, фрагменты, артефакты, настройки) в JSON."""

import json

from .config import ART_SLOTS, MUSIC_VOL, SAVE_FILE, SFX_VOL
from .heroes import HEROES, STANDARD_KEYS

DEFAULT_STATS = {"wins": 0, "bosses": 0, "waves": 0, "specials": 0, "ults": 0,
                 "finishers": 0, "parries": 0, "max_combo": 0, "coins_earned": 0,
                 "buys": 0, "camp_stages": 0, "camps": 0, "strikes": 0, "injuries": 0,
                 "myth_ults": 0, "chests": 0, "gems_earned": 0, "fatalities": 0,
                 "online_wins": 0, "martyr_wins": 0, "max_damage": 0, "casts": 0,
                 "bleeds": 0, "chains": 0, "saws": 0, "roars": 0, "aoes": 0,
                 "haze": 0, "legend_ults": 0, "crafts": 0, "traps": 0, "headshots": 0}

DEFAULT_SETTINGS = {"music": MUSIC_VOL, "sfx": SFX_VOL, "mute": False,
                    "shake": True, "blood": True, "fullscreen": False}


def default_save():
    return {"coins": 0, "gems": 0, "bot_level": 1, "owned": list(STANDARD_KEYS), "exp": 0,
            "plvl": 1, "camp": {}, "camp_claimed": [], "ach": [],
            "stats": dict(DEFAULT_STATS),
            "settings": dict(DEFAULT_SETTINGS),
            "frags": {}, "arts": [], "equip": {}, "bps": {}}


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
    settings = raw.get("settings", {})
    if isinstance(settings, dict):
        s = d["settings"]
        s["music"] = max(0.0, min(1.0, float(settings.get("music", s["music"]))))
        s["sfx"] = max(0.0, min(1.0, float(settings.get("sfx", s["sfx"]))))
        s["mute"] = bool(settings.get("mute", False))
        s["shake"] = bool(settings.get("shake", True))
        s["blood"] = bool(settings.get("blood", True))
        s["fullscreen"] = bool(settings.get("fullscreen", False))
    frags = raw.get("frags", {})
    if isinstance(frags, dict):
        d["frags"] = {str(k): max(0, int(v)) for k, v in frags.items()}
    arts = raw.get("arts", [])
    if isinstance(arts, list):
        d["arts"] = [a for a in arts if isinstance(a, str)]
    equip = raw.get("equip", {})
    if isinstance(equip, dict):
        eq = {}
        for k, v in equip.items():
            if isinstance(v, list):
                slots = [a for a in v if isinstance(a, str)][:ART_SLOTS]
                eq[str(k)] = slots
        d["equip"] = eq
    bps = raw.get("bps", {})
    if isinstance(bps, dict):
        d["bps"] = {str(k): max(0, int(v)) for k, v in bps.items()}
    return d


def save_save(d):
    try:
        with open(SAVE_FILE, "w") as fp:
            json.dump(d, fp)
    except Exception:
        pass
