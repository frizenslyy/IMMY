#!/usr/bin/env python3
"""IMMY — самопроверка игровой логики без дисплея (tkinter не нужен).

Запуск:  python3 selftest.py
"""

import random
import tempfile

import immy.save as save_mod
from immy.arena import Arena
from immy.background import MAPS
from immy.config import CRIT_MULT, PARRY_STUN
from immy.heroes import HEROES, RARITY_LABEL, STANDARD_KEYS
from immy.sound import TRACKS, _render_track

EMPTY_INP = {"move": 0, "jump": False, "crouch": False, "attack": False,
             "cast": None, "parry": False}


def play(arena, frames, attack_every=13, cast_every=31, jump_every=47, seed=5):
    random.seed(seed)
    n_ab = len(arena.p.h["abilities"])
    for i in range(frames):
        if arena.phase == "fight":
            if i % attack_every == 0:
                arena.update(1 / 60, dict(EMPTY_INP, attack=True))
                arena.update(1 / 60, dict(EMPTY_INP))
                continue
            cast = random.randint(0, n_ab - 1) if i % cast_every == 0 else None
            inp = {"move": 1 if (i // 40) % 2 == 0 else -1,
                   "jump": i % jump_every == 0, "crouch": False,
                   "attack": False, "cast": cast, "parry": False}
        else:
            inp = dict(EMPTY_INP)
        arena.update(1 / 60, inp)
        if arena.phase == "end" and i > 200:
            break
    return arena


def main():
    for hero in HEROES:
        h = HEROES[hero]
        assert "stats" in h and set(h["stats"]) == {"str", "agi", "spd"}
        total = sum(h["stats"].values())
        want = 17 if h["rarity"] == "uncommon" else 14
        assert total == want, (hero, total, want)
        assert len(h["abilities"]) == (4 if h["rarity"] == "uncommon" else 3)
        assert h["rarity"] in RARITY_LABEL
        for ab in h["abilities"]:
            assert ab["cd"] > 0 and ab.get("desc")
        a = Arena(hero, "EMBERY" if hero != "EMBERY" else "DEADY", 1, False)
        assert a.map in MAPS
        play(a, 6000)
        assert a.phase == "end", (hero, a.phase, a.wins_p, a.wins_b)
        assert a.wins_p + a.wins_b in (2, 3)
        print("hero", hero, "ok", a.wins_p, ":", a.wins_b, "round", a.round)

    a = Arena("LIGHTY", "DEADY", 10, True)
    assert a.boss and a.b.scale > 1.2 and a.b.max_hp > 200
    assert a.b.max_hp < 300 and a.b.dmg_mult < 2.0
    play(a, 8000, attack_every=9)
    assert a.phase == "end"
    print("boss ok, reward:", a.reward)

    a = Arena("EMBERY", "DEADY", 1, False, survival=True)
    assert a.survival and a.wave == 1 and not a.mini and a.b.is_bot
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.b.hp = 1.0
    a.register_hit(a.p, a.b, 50)
    for _ in range(130):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.wave == 2 and a.run_reward == 60, (a.wave, a.run_reward)
    assert a.phase == "intro" and not a.b.dead
    print("survival wave clear ok")

    a.wave = 5
    a.spawn_wave()
    assert a.mini and a.b.scale > 1.2 and a.b.max_hp > 200
    a.phase = "fight"
    a.b.hp = 1.0
    a.register_hit(a.p, a.b, 50)
    for _ in range(130):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.wave == 6 and a.run_reward == 60 + 150, (a.wave, a.run_reward)
    print("survival mini-boss ok")

    a.p.hp = 1.0
    a.phase = "fight"
    a.register_hit(a.b, a.p, 50)
    for _ in range(130):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.phase == "end" and not a.win and a.reward == 210, (a.phase, a.reward)
    print("survival end reward ok")

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
    a.ai.level = 0
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

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 0, a.b)
    assert len(a.proj) == 1 and a.proj[0]["kind"] == "orb"
    my_orb = a.proj[0]
    for _ in range(200):
        a.update(1 / 60, dict(EMPTY_INP))
    assert my_orb not in a.proj
    print("generic orb ok")

    a = Arena("FROSTY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 0, a.b)
    assert len(a.proj) == 3, len(a.proj)
    print("orb fan (count/spread) ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.b.y = 615.0
    a.b.on_ground = True
    a.ai.level = 0
    a.ai.update = lambda *args: None
    a.cast_ability(a.p, 1, a.b)
    assert a.fx and a.fx[0]["kind"] == "ground_warn" and a.fx[0]["dodge"] == "jump"
    for _ in range(60):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < a.b.max_hp
    print("generic ground hits grounded foe ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.cast_ability(a.p, 1, a.b)
    a.b.vy = -900.0
    a.b.on_ground = False
    a.b.y = 615.0 - 200.0
    for _ in range(60):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp == a.b.max_hp
    print("ground dodge by jump ok")

    a = Arena("FROSTY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 1, a.b)
    warns = [fx for fx in a.fx if fx["kind"] == "ground_warn"]
    assert len(warns) == 3, len(warns)
    print("ice spikes wave ok")

    a = Arena("SHADOWY", "EMBERY", 2, False)
    a.phase = "fight"
    a.b.x = a.p.x + 400
    a.cast_ability(a.p, 1, a.b)
    assert abs(a.p.x - (a.b.x + 95)) < 1.0
    print("blink behind foe ok")

    a = Arena("SHADOWY", "EMBERY", 2, False)
    a.phase = "fight"
    a.ai.level = 0
    a.b.x = a.p.x + 100
    hp0 = a.b.hp
    a.cast_ability(a.p, 2, a.b)
    dmg = hp0 - a.b.hp
    assert dmg > 30, dmg
    print("strike guaranteed crit ok, dmg:", round(dmg, 1))

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

    a = Arena("WINDY", "EMBERY", 2, False)
    a.phase = "fight"
    a.p.x, a.b.x = 400.0, 800.0
    a.ai.update = lambda *args: None
    a.cast_ability(a.p, 1, a.b)
    assert a.b.kvx < 0, a.b.kvx
    x0 = a.b.x
    for _ in range(20):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.x < x0 - 20, (x0, a.b.x)
    print("pull ok")

    a = Arena("WINDY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 2, a.b)
    assert a.p.buffs["swift"] > 0 and a.p.eff_speed() > a.p.stat_spd
    print("swift buff ok")

    a = Arena("NECROY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 2, a.b)
    assert a.p.buffs["vamp"] > 0 and a.p.vamp_pct > 0.4
    a.p.hp = a.p.max_hp * 0.5
    hp0 = a.p.hp
    a.b.x = a.p.x + 80
    a.register_hit(a.p, a.b, 20)
    assert a.p.hp > hp0
    print("vamp aura ok")

    a = Arena("DEADY", "EMBERY", 2, False)
    a.phase = "fight"
    a.b.x = a.p.x + 80
    assert a.p.try_parry() and a.p.parry_t > 0
    hp0 = a.p.hp
    res, dmg = a.register_hit(a.b, a.p, 20)
    assert res == "parry" and a.p.hp == hp0
    assert a.b.stun_t >= PARRY_STUN - 1e-9
    assert not a.p.try_parry()
    print("parry ok")

    a = Arena("BANEY", "EMBERY", 2, False)
    a.phase = "fight"
    a.p.x, a.b.x = 400.0, 700.0
    a.ai.update = lambda *args: None
    a.cast_ability(a.p, 0, a.b)
    assert a.proj and a.proj[0]["kind"] == "snare"
    for _ in range(30):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.root_t > 0, a.b.root_t
    a.b.vx_target = 300.0
    x0 = a.b.x
    for _ in range(20):
        a.update(1 / 60, dict(EMPTY_INP))
    assert abs(a.b.x - x0) < 6.0
    print("snare root ok")

    a = Arena("BANEY", "EMBERY", 2, False)
    a.phase = "fight"
    a.p.x, a.b.x = 400.0, 700.0
    a.cast_ability(a.p, 2, a.b)
    assert a.b.poison_t > 0 and a.b.poison_dps > 0
    hp0 = a.b.hp
    for _ in range(120):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < hp0
    assert a.b.hp >= 1.0
    print("poison dot ok")

    a = Arena("BANEY", "EMBERY", 2, False)
    a.phase = "fight"
    a.p.x, a.b.x = 400.0, 700.0
    a.ai.update = lambda *args: None
    a.cast_ability(a.p, 1, a.b)
    assert any(fx["kind"] == "summon" for fx in a.fx)
    hp0 = a.b.hp
    for _ in range(150):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < hp0
    print("summon bites ok")

    a = Arena("CRYSTAY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 1, a.b)
    assert a.p.buffs["guard"] > 0
    hp0 = a.p.hp
    res, dmg = a.register_hit(a.b, a.p, 30)
    assert res == "guard" and a.p.hp == hp0
    print("guard block ok")

    a = Arena("INFERNOY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 0, a.b)
    assert any(fx["kind"] == "beam" for fx in a.fx)
    print("beam ok")

    a = Arena("MAGNEY", "EMBERY", 2, False)
    a.phase = "fight"
    a.cast_ability(a.p, 0, a.b)
    assert a.fx[0]["kind"] == "ground_warn" and a.fx[0]["heavy"]
    print("heavy meteor ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.ai.level = 0
    a.b.x = a.p.x + 80
    a.b.on_ground = True
    hp0 = a.b.hp
    a.do_melee(a.p, 0)
    assert a.b.hp < hp0
    a2 = Arena("EMBERY", "DEADY", 2, False)
    a2.phase = "fight"
    assert a2.b.hp == a2.b.max_hp
    print("melee single application ok")

    save_mod.SAVE_FILE = tempfile.mktemp(suffix=".json")
    save_mod.save_save(777, 4, ["DEADY", "FROSTY", "BANEY"])
    coins, level, owned = save_mod.load_save()
    assert (coins, level) == (777, 4) and owned == ["DEADY", "FROSTY", "BANEY"]
    assert set(STANDARD_KEYS) <= set(HEROES)
    print("save/load with owned ok")

    for name in TRACKS:
        data = _render_track(*TRACKS[name])
        assert data[:4] == b"RIFF" and len(data) > 10000
    print("music tracks render ok")

    print("SELFTEST OK")


if __name__ == "__main__":
    main()
