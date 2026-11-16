#!/usr/bin/env python3
"""IMMY — самопроверка игровой логики без дисплея (tkinter не нужен).

Запуск:  python3 selftest.py
"""

import random
import tempfile

import immy.save as save_mod
from immy.arena import Arena
from immy.background import MAPS
from immy.heroes import HEROES, STANDARD_KEYS
from immy.sound import TRACKS, _render_track

EMPTY_INP = {"move": 0, "jump": False, "crouch": False, "attack": False, "cast": None}


def play(arena, frames, attack_every=13, cast_every=31, jump_every=47, seed=5):
    random.seed(seed)
    for i in range(frames):
        if arena.phase == "fight":
            if i % attack_every == 0:
                arena.update(1 / 60, dict(EMPTY_INP, attack=True))
                arena.update(1 / 60, dict(EMPTY_INP))
                continue
            cast = random.randint(0, 2) if i % cast_every == 0 else None
            inp = {"move": 1 if (i // 40) % 2 == 0 else -1,
                   "jump": i % jump_every == 0, "crouch": False,
                   "attack": False, "cast": cast}
        else:
            inp = dict(EMPTY_INP)
        arena.update(1 / 60, inp)
        if arena.phase == "end" and i > 200:
            break
    return arena


def main():
    for hero in HEROES:
        a = Arena(hero, "EMBERY" if hero != "EMBERY" else "DEADY", 1, False)
        assert a.map in MAPS
        play(a, 6000)
        assert a.phase == "end", (hero, a.phase, a.wins_p, a.wins_b)
        assert a.wins_p + a.wins_b in (2, 3)
        print("hero", hero, "ok", a.wins_p, ":", a.wins_b, "round", a.round)

    a = Arena("LIGHTY", "DEADY", 10, True)
    assert a.boss and a.b.scale > 1.2 and a.b.max_hp > 200
    play(a, 8000, attack_every=9)
    assert a.phase == "end"
    print("boss ok, reward:", a.reward)

    a = Arena("DEADY", "LIGHTY", 3, False)
    a.phase = "fight"
    ok = a.cast_ability(a.p, 0, a.b)
    assert ok and a.p.scythe_out and len(a.proj) == 1
    for _ in range(60):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.p.cds[0] > 0 and a.p.attack_cd == 0
    for _ in range(540):
        a.update(1 / 60, dict(EMPTY_INP))
    assert len(a.proj) == 0 and not a.p.scythe_out
    print("scythe throw/return ok")

    a = Arena("LIGHTY", "EMBERY", 2, False)
    a.phase = "fight"
    a.b.x = a.p.x + 150
    a.cast_ability(a.p, 0, a.b)
    assert a.b.stun_t >= 1.9
    print("shock stun ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 2, a.b)
    assert a.p.buffs["rage"] > 0 and a.p.out_mult() > 1.4
    print("rage ok")

    a = Arena("DEADY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 2, a.b)
    assert a.p.buffs["soul"] > 0
    a.cast_ability(a.b, 0, a.p)
    hp0 = a.p.hp
    a.update(1 / 60, dict(EMPTY_INP))
    assert a.p.hp == hp0
    print("soul invulnerability ok")

    a = Arena("FROSTY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 0, a.b)
    assert len(a.proj) == 1 and a.proj[0]["kind"] == "orb"
    assert a.proj[0]["color"] == a.p.h["accent"] and a.proj[0]["r"] > 0
    my_orb = a.proj[0]
    for _ in range(200):
        a.update(1 / 60, dict(EMPTY_INP))
    assert my_orb not in a.proj
    print("generic orb ok")

    a = Arena("FROSTY", "EMBERY", 2, False)
    a.phase = "fight"
    a.b.y = 615.0
    a.b.on_ground = True
    a.cast_ability(a.p, 1, a.b)
    assert a.fx and a.fx[0]["kind"] == "ground_warn" and a.fx[0]["dodge"] == "jump"
    for _ in range(60):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < a.b.max_hp
    print("generic ground hits grounded foe ok")

    a = Arena("FROSTY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 1, a.b)
    a.b.vy = -900.0
    a.b.on_ground = False
    a.b.y = 615.0 - 200.0
    for _ in range(60):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp == a.b.max_hp
    print("ground dodge by jump ok")

    a = Arena("SHADOWY", "EMBERY", 2, False)
    a.phase = "fight"
    a.b.x = a.p.x + 400
    a.cast_ability(a.p, 1, a.b)
    assert abs(a.p.x - (a.b.x + 95)) < 1.0
    print("blink behind foe ok")

    a = Arena("LUNARY", "EMBERY", 2, False)
    a.phase = "fight"
    a.p.hp = 40.0
    a.cast_ability(a.p, 2, a.b)
    assert a.p.hp == 65.0
    print("heal ok")

    a = Arena("FROSTY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 2, a.b)
    assert a.p.buffs["flash"] > 0 and a.p.flash_mult == 0.5
    print("buff_def mult ok")

    save_mod.SAVE_FILE = tempfile.mktemp(suffix=".json")
    save_mod.save_save(777, 4, ["DEADY", "FROSTY"])
    coins, level, owned = save_mod.load_save()
    assert (coins, level) == (777, 4) and owned == ["DEADY", "FROSTY"]
    assert set(STANDARD_KEYS) <= set(HEROES)
    print("save/load with owned ok")

    for name in TRACKS:
        data = _render_track(*TRACKS[name])
        assert data[:4] == b"RIFF" and len(data) > 10000
    print("music tracks render ok")

    print("SELFTEST OK")


if __name__ == "__main__":
    main()
