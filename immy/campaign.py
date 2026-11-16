"""IMMY — кампании: 3 кампании, нарастающая сложность, эксклюзивные награды."""

CAMPAIGNS = [
    {"name": "КРОВАВЫЙ ЗАМОР", "desc": "Проклятый замок гулей: 10 ступеней ужаса.",
     "stages": 10, "base": 1, "step": 1.6, "hero": "GHOULEY", "color": "#8aff8a"},
    {"name": "ПЕПЕЛЬНЫЕ ПУСТОШИ", "desc": "Выжженные земли пепла: 12 ступеней ярости.",
     "stages": 12, "base": 4, "step": 1.8, "hero": "ASHY", "color": "#e8c9a0"},
    {"name": "ТРОН ПЛАМЕНИ", "desc": "Цитадель владыки огня: 15 ступеней ада.",
     "stages": 15, "base": 8, "step": 2.0, "hero": "PYROY", "color": "#ff8c1a"},
]

UNLOCK_PLVL = 5


def stage_level(camp_idx, stage):
    c = CAMPAIGNS[camp_idx]
    return max(1, int(round(c["base"] + (stage - 1) * c["step"])))


def is_final(camp_idx, stage):
    return stage >= CAMPAIGNS[camp_idx]["stages"]


def unlocked(camp_idx, save):
    if camp_idx == 0:
        return save.get("plvl", 1) >= UNLOCK_PLVL
    prev = CAMPAIGNS[camp_idx - 1]["name"]
    cleared = save.get("camp", {}).get(str(camp_idx - 1), {}).get("done", False)
    return cleared


def camp_progress(save, camp_idx):
    return save.get("camp", {}).get(str(camp_idx), {}).get("stage", 0)


def camp_done(save, camp_idx):
    return save.get("camp", {}).get(str(camp_idx), {}).get("done", False)


def first_clear_reward(stage):
    return 120 + stage * 30


def replay_reward(stage):
    return 30 + stage * 10
