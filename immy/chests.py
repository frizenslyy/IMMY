"""IMMY — сундуки: вероятности выпадения (без tkinter, тестируется в selftest)."""

import random

from .heroes import HEROES

CHAOS_COST = 30
HELL_COST = 150


def keys_of(rarity):
    return [k for k, v in HEROES.items() if v["rarity"] == rarity]


def roll_chaos():
    r = random.random()
    if r < 0.05:
        return ("hero", "DEVILY")
    if r < 0.13:
        return ("hero", random.choice(keys_of("mythic")))
    if r < 0.20:
        return ("hero", random.choice(keys_of("legendary")))
    if r < 0.36:
        return ("hero", random.choice(keys_of("epic")))
    if r < 0.60:
        return ("hero", random.choice(keys_of("uncommon")))
    return ("coins", random.randint(150, 500))


def roll_hell():
    r = random.random()
    if r < 0.03:
        return ("hero", "SATANY")
    if r < 0.09:
        return ("hero", "DEMONDY")
    if r < 0.18:
        return ("hero", "IMPY")
    if r < 0.24:
        return ("hero", random.choice(keys_of("mythic")))
    if r < 0.30:
        return ("hero", random.choice(keys_of("legendary")))
    if r < 0.40:
        return ("hero", random.choice(keys_of("epic")))
    if r < 0.50:
        return ("hero", random.choice(keys_of("uncommon")))
    if r < 0.56:
        return ("hero", random.choice(keys_of("common")))
    if r < 0.64:
        return ("gems", random.randint(15, 40))
    return ("coins", random.randint(400, 900))


def title(kind):
    return "ЧЕРТОГИ АДА" if kind == "hell" else "СОКРОВИЩНИЦА ХАОСА"
