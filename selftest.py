#!/usr/bin/env python3
"""IMMY — самопроверка игровой логики без дисплея (tkinter не нужен).

Запуск:  python3 selftest.py
"""

import random

from immy.arena import Arena
from immy.heroes import HEROES


class Cv:
    """Заглушка canvas: принимает любые вызовы отрисовки."""

    def __getattr__(self, name):
        def f(*a, **k):
            return 1
        return f


def play(arena, frames, attack_every=13, cast_every=31, jump_every=47, seed=5):
    random.seed(seed)
    for i in range(frames):
        if arena.phase == "fight":
            if i % attack_every == 0:
                arena.update(1 / 60, {"move": 0, "jump": False, "crouch": False,
                                      "attack": True, "cast": None})
                arena.update(1 / 60, {"move": 0, "jump": False, "crouch": False,
                                      "attack": False, "cast": None})
                continue
            cast = random.randint(0, 2) if i % cast_every == 0 else None
            inp = {"move": 1 if (i // 40) % 2 == 0 else -1,
                   "jump": i % jump_every == 0, "crouch": False,
                   "attack": False, "cast": cast}
        else:
            inp = {"move": 0, "jump": False, "crouch": False, "attack": False, "cast": None}
        arena.update(1 / 60, inp)
        if arena.phase == "end" and i > 200:
            break
    return arena


def main():
    for hero in HEROES:
        a = Arena(hero, "EMBERY" if hero != "EMBERY" else "DEADY", 1, False)
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
        a.update(1 / 60, {"move": 0, "jump": False, "crouch": False, "attack": False, "cast": None})
    assert a.p.cds[0] > 0 and a.p.attack_cd == 0
    for _ in range(540):
        a.update(1 / 60, {"move": 0, "jump": False, "crouch": False, "attack": False, "cast": None})
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
    a.update(1 / 60, {"move": 0, "jump": False, "crouch": False, "attack": False, "cast": None})
    assert a.p.hp == hp0
    print("soul invulnerability ok")

    print("SELFTEST OK")


if __name__ == "__main__":
    main()
