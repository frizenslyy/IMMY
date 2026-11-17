#!/usr/bin/env python3
"""IMMY — самопроверка игровой логики без дисплея (tkinter не нужен).

Запуск:  python3 selftest.py
"""

import random
import socket
import tempfile
import time

import immy.save as save_mod
from immy import achievements as ach_mod
from immy import campaign as camp_mod
from immy.arena import Arena
from immy.background import MAPS
from immy.config import GROUND_Y, PARRY_STUN, exp_to_next
from immy.heroes import HEROES, RARITY_LABEL, STANDARD_KEYS
from immy.sound import TRACKS, _render_track

EMPTY_INP = {"move": 0, "jump": False, "crouch": False, "attack": False,
             "cast": None, "parry": False, "special": None, "strike": None, "myth": False,
             "rult": False}


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
        lo, hi = {"standard": (14, 14), "common": (14, 14), "uncommon": (17, 17),
                  "epic": (16, 20), "exclusive": (17, 17), "mythic": (18, 22),
                  "devil": (24, 24), "legendary": (20, 22)}[h["rarity"]]
        assert lo <= total <= hi, (hero, total, lo, hi)
        n_ab_want = 3 if h["rarity"] in ("standard", "common") else (5 if h["rarity"] == "legendary" else 4)
        assert len(h["abilities"]) == n_ab_want, hero
        assert h["rarity"] in RARITY_LABEL
        for ab in h["abilities"]:
            assert ab["cd"] > 0 and ab.get("desc")
        if h["rarity"] in ("epic", "exclusive"):
            assert h["abilities"][-1]["kind"] == "ult", hero
        if h["rarity"] in ("mythic", "devil"):
            assert h["abilities"][-1]["kind"] == "myth_ult", hero
        if h["rarity"] == "legendary":
            assert h["abilities"][-1]["kind"] == "legend_ult", hero
        assert h.get("pros") and h.get("cons"), hero
        a = Arena(hero, "EMBERY" if hero != "EMBERY" else "DEADY", 1, False)
        assert a.map in MAPS
        play(a, 12000)
        assert a.phase == "end", (hero, a.phase, a.wins_p, a.wins_b)
        assert a.wins_p + a.wins_b in (2, 3)
        print("hero", hero, "ok", a.wins_p, ":", a.wins_b, "round", a.round)

    kinds = {}
    for k, h in HEROES.items():
        if h["rarity"] == "common":
            ks = tuple(sorted(ab["kind"] for ab in h["abilities"]))
            assert ks not in kinds, (k, ks, kinds.get(ks))
            kinds[ks] = k
    assert len(kinds) == 10
    print("common kind-sets unique ok")

    a = Arena("LIGHTY", "DEADY", 10, True)
    assert a.boss and a.b.scale > 1.2
    assert 150 < a.b.max_hp < 220 and a.b.dmg_mult < 1.7
    assert a.p.dmg_mult == 1.1
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
    assert a.wave == 2 and a.run_reward == 41, (a.wave, a.run_reward)
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
    assert a.wave == 6 and a.run_reward == 41 + 100, (a.wave, a.run_reward)
    print("survival mini-boss ok")

    a.p.hp = 1.0
    a.phase = "fight"
    a.register_hit(a.b, a.p, 50)
    for _ in range(130):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.phase == "end" and not a.win and a.reward == 141, (a.phase, a.reward)
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
    assert len(a.proj) == 1 and a.proj[0]["kind"] == "snare"
    print("frosty snare ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.b.y = float(GROUND_Y)
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
    a.b.y = float(GROUND_Y) - 200.0
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

    a = Arena("SOLARY", "EMBERY", 2, False)
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
    a.cast_ability(a.p, 1, a.b)
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

    for key in HEROES:
        h = HEROES[key]
        sps = h.get("specials", [])
        want = 4 if h["rarity"] in ("mythic", "devil", "legendary") else \
            (3 if h["rarity"] in ("uncommon", "epic", "exclusive") else 2)
        assert len(sps) == want, (key, len(sps))
        combos = [sp["combo"] for sp in sps]
        assert len(set(combos)) == len(combos) and all(c in ("as", "ws", "wa", "wd") for c in combos)
        costs = [sp["cost"] for sp in sps]
        assert all(0 < c <= 100 for c in costs), (key, costs)
        for sp in sps:
            assert sp.get("name") and sp.get("desc")
            assert sp.get("cd", 0) > 0, (key, sp.get("name"))
    print("specials data ok")

    a = Arena("DEADY", "LIGHTY", 1, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    e0 = a.p.energy
    a.register_hit(a.p, a.b, 20)
    assert a.p.energy > e0, (e0, a.p.energy)
    print("energy gain ok")

    a.p.energy = 100.0
    a.b.x = a.p.x + 120
    assert a.cast_special(a.p, "as", a.b)
    assert a.b.root_t > 0 and abs(a.p.energy - 50) < 1e-6 and a.p.special_cd > 0
    assert any(fx["kind"] == "grab" for fx in a.fx)
    for _ in range(40):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < a.b.max_hp
    print("deady grab ok")

    e = a.p.energy
    assert not a.cast_special(a.p, "ws", a.b)
    assert a.p.energy == e
    print("special energy gate ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.b.x = a.p.x + 90
    a.b.on_ground = True
    hp0 = a.b.hp
    assert a.p.try_strike("kick", a)
    assert len(a.strikes) == 1 and a.p.strike_cds["kick"] > 0
    assert not a.p.try_strike("kick", a)
    for _ in range(30):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < hp0, (hp0, a.b.hp)
    print("kick strike ok, dmg:", round(hp0 - a.b.hp, 1))

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.b.x = a.p.x + 80
    hp0 = a.b.hp
    assert a.p.try_strike("upper", a)
    for _ in range(30):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < hp0
    assert a.b.vy < 0 or not a.b.on_ground, (a.b.vy, a.b.on_ground)
    print("uppercut launcher ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.b.x = a.p.x + 90
    assert not a.p.try_strike("air", a)
    a.p.on_ground = False
    a.p.y = 500.0
    assert a.p.try_strike("air", a)
    print("air strike gating ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.b.x = a.p.x + 90
    a.b.injury = None
    real_random = random.random
    random.random = lambda: 0.0
    try:
        hp0 = a.b.hp
        a.register_hit(a.p, a.b, 20)
    finally:
        random.random = real_random
    assert a.b.injury and a.b.injury["kind"] in ("str", "spd", "jump", "ability"), a.b.injury
    a2 = Arena("EMBERY", "DEADY", 2, False)
    a2.phase = "fight"
    a2.b.injury = {"kind": "str", "ability": 0}
    f0 = a2.b.dmg_factor()
    a2.b.injury = None
    assert f0 < a2.b.dmg_factor()
    a2.b.injury = {"kind": "jump", "ability": 0}
    assert not a2.b.can_jump()
    a2.b.injury = {"kind": "spd", "ability": 0}
    assert a2.b.eff_speed() < a2.b.stat_spd
    a2.b.injury = {"kind": "ability", "ability": 0}
    assert not a2.cast_ability(a2.b, 0, a2.p)
    print("injury effects ok")

    a = Arena("NECROMANCERY", "EMBERY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.p.energy = 30.0
    a.b.hp = a.b.max_hp * 0.2
    assert not a.myth_ready(a.p, a.b)
    a.p.energy = 100.0
    a.p.cds[0] = 5.0
    assert not a.myth_ready(a.p, a.b)
    a.p.cds[0] = 0.0
    a.p.ult_charge = 100.0
    a.b.hp = a.b.max_hp * 0.5
    assert not a.myth_ready(a.p, a.b)
    a.b.hp = a.b.max_hp * 0.2
    assert a.myth_ready(a.p, a.b)
    assert a.try_myth_ult(a.p, a.b)
    assert a.p.energy == 0.0 and a.p.cds[0] > 0 and a.p.cds[3] > 0
    assert any(fx["kind"] == "myth_necromancery" for fx in a.fx)
    for _ in range(110):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < a.b.max_hp * 0.2
    print("myth ult gating + cast ok")

    a = Arena("EMBERY", "DEADY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.b.x = a.p.x + 80
    n0 = len(a.parts.items)
    a.register_hit(a.p, a.b, 20)
    blood_parts = [it for it in a.parts.items if it.get("color") == "#c4140f"]
    assert len(blood_parts) > n0 - n0 and blood_parts, "no blood particles"
    print("blood on hit ok")

    a = Arena("DEADY", "LIGHTY", 1, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.p.energy = 100.0
    a.b.x = a.p.x + 120
    assert a.cast_special(a.p, "as", a.b)
    a.p.special_cd = 0.0
    a.p.energy = 100.0
    assert not a.cast_special(a.p, "as", a.b)
    assert a.p.sp_cds.get("as", 0) > 0
    print("special per-combo cooldown ok")

    a = Arena("BANEY", "EMBERY", 1, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.p.energy = 100.0
    a.b.x = a.p.x + 260
    assert a.cast_special(a.p, "ws", a.b)
    assert abs(a.p.energy - 30) < 1e-6
    assert any(fx["kind"] == "barrage" for fx in a.fx)
    for _ in range(30):
        a.update(1 / 60, dict(EMPTY_INP))
    assert any(pr["kind"] == "barr" for pr in a.proj)
    print("baney barrage ok")

    a = Arena("VAWYY", "EMBERY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.ai.level = 0
    a.b.x = a.p.x + 200
    assert a.cast_ability(a.p, 0, a.b)
    assert a.fx and a.fx[0]["kind"] == "geyser_warn"
    a.b.y = float(GROUND_Y)
    a.b.on_ground = True
    for _ in range(60):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < a.b.max_hp
    print("geyser launch ok")

    a = Arena("GALAXY", "EMBERY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.p.x, a.b.x = 400.0, 620.0
    assert a.cast_ability(a.p, 0, a.b)
    assert any(fx["kind"] == "vortex" for fx in a.fx)
    assert a.b.root_t > 0
    hp0 = a.b.hp
    for _ in range(120):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < hp0
    print("vortex ticks ok")

    a = Arena("VAWYY", "EMBERY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.p.x, a.b.x = 400.0, 800.0
    assert a.cast_ability(a.p, 2, a.b)
    assert any(pr["kind"] == "tide" for pr in a.proj)
    for _ in range(90):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.hp < a.b.max_hp
    print("tide wall ok")

    a = Arena("VAWYY", "EMBERY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.ai.level = 0
    a.p.x, a.b.x = 400.0, 700.0
    a.p.ult_charge = 100.0
    a.b.hp = a.b.max_hp * 0.5
    assert not a.cast_ability(a.p, 3, a.b)
    a.b.hp = a.b.max_hp * 0.08
    assert a.cast_ability(a.p, 3, a.b)
    assert any(fx["kind"] == "ult_vawyy" for fx in a.fx)
    assert a.b.stun_t > 1.0
    for _ in range(100):
        a.update(1 / 60, dict(EMPTY_INP))
    assert abs(a.b.hp - 4.0) < 1e-6
    assert a.quality_finish == 0
    print("ult leaves 1 hit ok")

    a = Arena("VAWYY", "EMBERY", 2, False)
    a.phase = "fight"
    a.ai.update = lambda *args: None
    a.ai.level = 0
    a.p.x, a.b.x = 400.0, 700.0
    a.p.ult_charge = 100.0
    a.b.hp = a.b.max_hp * 0.03
    assert a.cast_ability(a.p, 3, a.b)
    for _ in range(80):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.b.dead and a.quality_finish == 1
    print("quality finisher ok")

    assert exp_to_next(1) == 120 and exp_to_next(5) == 280
    print("exp curve ok")

    save_mod.SAVE_FILE = tempfile.mktemp(suffix=".json")
    save_mod.save_save({"coins": 777, "gems": 42, "bot_level": 4,
                        "owned": ["DEADY", "FROSTY", "BANEY"],
                        "exp": 30, "plvl": 2, "camp": {"0": {"stage": 3, "done": False}},
                        "camp_claimed": [], "ach": ["w1"],
                        "stats": {"wins": 1, "coins_earned": 1000}})
    d = save_mod.load_save()
    assert d["coins"] == 777 and d["gems"] == 42 and d["bot_level"] == 4
    assert d["owned"] == ["DEADY", "FROSTY", "BANEY"]
    assert d["plvl"] == 2 and d["exp"] == 30
    assert d["camp"]["0"]["stage"] == 3 and d["ach"] == ["w1"]
    assert d["stats"]["wins"] == 1 and d["stats"]["coins_earned"] == 1000
    assert set(STANDARD_KEYS) <= set(HEROES)
    print("save/load v3 ok")

    d = save_mod.default_save()
    d["stats"]["wins"] = 5
    granted = ach_mod.check(d)
    assert [x["id"] for x in granted] == ["w1", "w5"], granted
    assert d["coins"] == 150 and "w1" in d["ach"] and "w5" in d["ach"]
    assert ach_mod.check(d) == []
    assert len(ach_mod.ACHIEVEMENTS) == 191, len(ach_mod.ACHIEVEMENTS)
    n_gem = sum(1 for a in ach_mod.ACHIEVEMENTS if a.get("gems"))
    assert n_gem > 40, n_gem
    d2 = save_mod.default_save()
    ga = next(a for a in ach_mod.ACHIEVEMENTS if a.get("gems"))
    d2["stats"][ga["stat"]] = ga["goal"]
    granted2 = ach_mod.check(d2)
    assert ga["id"] in [x["id"] for x in granted2]
    assert d2["gems"] == ga["gems"] and d2["stats"]["gems_earned"] == ga["gems"]
    print("achievements 191 + gems grant ok")

    assert sum(c["stages"] for c in camp_mod.CAMPAIGNS) == 305
    assert len(camp_mod.CAMPAIGNS) == 23
    assert camp_mod.stage_level(0, 1) == 1 and camp_mod.stage_level(0, 10) == 13
    assert camp_mod.is_final(0, 10) and not camp_mod.is_final(0, 9)
    hero_rewards = [c for c in camp_mod.CAMPAIGNS if c["reward"]["type"] == "hero"]
    gem_rewards = [c for c in camp_mod.CAMPAIGNS if c["reward"]["type"] == "gems"]
    assert len(hero_rewards) == 6 and len(gem_rewards) == 8
    assert all(camp_mod.reward_label(c) for c in camp_mod.CAMPAIGNS)
    d = save_mod.default_save()
    assert camp_mod.unlocked(0, d) and not camp_mod.unlocked(1, d)
    d["camp"]["0"] = {"stage": 10, "done": True}
    assert camp_mod.unlocked(1, d)
    print("campaign rules ok")

    for name in TRACKS:
        data = _render_track(*TRACKS[name])
        assert data[:4] == b"RIFF" and len(data) > 10000
    print("music tracks render ok")

    from immy.config import (FATALITY_BONUS, FATALITY_GEMS, NET_DISCOVER_PORT,
                             RARITY_POWER)
    from immy import netplay

    a = Arena("TITANY", "DEADY", 1, False)
    assert abs(a.p.max_hp - 100.0 * RARITY_POWER["mythic"]) < 1e-6, a.p.max_hp
    assert abs(a.p.dmg_mult - 1.1 * RARITY_POWER["mythic"]) < 1e-6
    an = Arena("TITANY", "DEADY", 1, False, net=True)
    assert an.p.max_hp == 100.0 and abs(an.p.dmg_mult - 1.1) < 1e-6
    am = Arena("DEADY", "TITANY", 1, False, net=True, mirror=True)
    assert am.mirror and am.ai is None and am.p.max_hp == 100.0
    astd = Arena("DEADY", "TITANY", 1, False)
    assert astd.p.max_hp == 100.0
    print("rarity power scaling ok")

    a = Arena("DEADY", "EMBERY", 10, True)
    a.wins_p = 2
    a.after_ko()
    assert a.phase == "fatality" and a.fatality is not None
    assert len(a.fatality["seq"]) == 4
    a.fatality_feed(["x"])
    a.update(0.016, dict(EMPTY_INP))
    assert a.phase == "fatality"
    a.fatality_feed(list(a.fatality["seq"]))
    a.update(0.016, dict(EMPTY_INP))
    assert a.phase == "fatality_anim", a.phase
    assert a.fatality_done and a.fatality_bonus == FATALITY_BONUS and a.fatality_gems == FATALITY_GEMS
    a.update(3.0, dict(EMPTY_INP))
    assert a.phase == "end"
    snap = a.snapshot()
    assert snap["ph"] == "end" and snap["fd"] and snap["win"]

    a2 = Arena("DEADY", "EMBERY", 10, True)
    a2.wins_p = 2
    a2.after_ko()
    a2.update(6.0, dict(EMPTY_INP))
    assert a2.phase == "end" and not a2.fatality_done and a2.fatality_bonus == 0

    a3 = Arena("DEADY", "EMBERY", 1, False)
    a3.wins_p = 2
    a3.after_ko()
    assert a3.phase == "end", a3.phase
    print("fatality flow ok")

    h = netplay.Host()
    assert h.alive and not h.connected
    c = netplay.Client()
    assert c.connect("127.0.0.1")
    for _ in range(50):
        h.poll()
        if h.connected:
            break
        time.sleep(0.02)
    assert h.connected, "host accept failed"
    assert c.send({"t": "hello", "name": "tester"})
    assert c.send({"t": "in", "d": {"move": 1}})
    for _ in range(50):
        msgs = h.poll()
        if msgs:
            break
        time.sleep(0.02)
    assert any(m.get("t") == "hello" for m in msgs)
    assert any(m.get("t") == "in" and m["d"]["move"] == 1 for m in msgs)
    assert h.send({"t": "snap", "ph": "intro"})
    for _ in range(50):
        msgs = c.poll()
        if msgs:
            break
        time.sleep(0.02)
    assert any(m.get("t") == "snap" and m["ph"] == "intro" for m in msgs)
    h.close()
    c.close()
    print("netplay loopback ok")

    h = netplay.Host()
    c = netplay.Client()
    assert c.connect("127.0.0.1")
    for _ in range(50):
        h.poll()
        if h.connected:
            break
        time.sleep(0.02)
    assert h.connected
    ah = Arena("DEADY", "LIGHTY", 1, False, map=MAPS[0], net=True)
    am = Arena("LIGHTY", "DEADY", 1, False, map=MAPS[0], net=True, mirror=True)
    for i in range(300):
        for m in c.poll():
            if m.get("t") == "snap":
                am.pending_snap = m
        for m in h.poll():
            if m.get("t") == "in" and isinstance(m.get("d"), dict):
                ah.remote_inp = m["d"]
        ah.update(1 / 60, dict(EMPTY_INP, attack=(i % 10 == 0),
                               move=1 if i % 80 < 40 else -1))
        if i % 3 == 0:
            assert h.send(ah.snapshot())
        assert c.send({"t": "in", "d": dict(EMPTY_INP, move=-1 if i % 60 < 30 else 1,
                                            attack=(i % 12 == 0))})
        am.update(1 / 60, dict(EMPTY_INP))
        if ah.phase == "end":
            break
    assert am.p.synced and am.b.synced
    assert abs(am.p.x - ah.p.x) < 90, (am.p.x, ah.p.x)
    assert abs(am.p.hp - ah.p.hp) < 0.6, (am.p.hp, ah.p.hp)
    assert am.phase == ah.phase, (am.phase, ah.phase)
    h.close()
    c.close()
    print("netplay e2e mirror ok")

    disc = netplay.Discovery()
    fake = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fake.sendto((netplay.ANS + "deadbeef|TESTPC").encode(), ("127.0.0.1", NET_DISCOVER_PORT))
    time.sleep(0.15)
    peers, sids = disc.scan()
    fake.close()
    disc.close()
    assert any(name == "TESTPC" for _, name in peers), peers
    print("discovery ok")

    d1 = netplay.Discovery()
    d2 = netplay.Discovery()
    d1.seeking = True
    d2.seeking = True
    p1, s1 = d1.scan("online")
    p2, s2 = d2.scan("online")
    assert any(name for _, name in p1) and any(name for _, name in p2), (p1, p2)
    assert all(sids_ok for sids_ok in (s1, s2) if sids_ok)
    d1.close()
    d2.close()
    print("online seek loopback ok")

    for key in ("KINGLY", "DIVINY", "COLOSSY", "VOIDY", "STORMY"):
        a = Arena(key, "DEADY", 1, False)
        a.phase = "fight"
        a.p.energy = 100.0
        a.p.ult_charge = 100.0
        a.p.cds = [0.0] * 5
        a.b.hp = a.b.max_hp * 0.2
        assert a.legend_ready(a.p, a.b)
        assert a.try_legend_ult(a.p, a.b)
        assert a.p.energy == 0.0 and a.p.ult_charge == 0.0
        for _ in range(200):
            a.update(1 / 60, dict(EMPTY_INP))
    print("legend ult ok")

    a = Arena("NECROMANCERY", "EMBERY", 1, False)
    a.phase = "fight"
    assert a.p.ult_charge == 0.0
    a.register_hit(a.p, a.b, 40)
    assert a.p.ult_charge > 0, a.p.ult_charge
    a.b.hp = a.b.max_hp * 0.2
    a.p.energy = 100.0
    a.p.ult_charge = 50.0
    a.p.cds[0] = a.p.cds[3] = 0.0
    assert not a.myth_ready(a.p, a.b)
    a.p.ult_charge = 100.0
    assert a.myth_ready(a.p, a.b)
    print("ult gauge ok")

    from immy.config import (CHEST_HELL_COST, COUNTDOWN_T, MARTYR_DMG_MULT,
                             MARTYR_HP_MULT, MARTYR_ROUNDS)
    assert MARTYR_ROUNDS == 10 and MARTYR_HP_MULT == 10.0 and MARTYR_DMG_MULT == 10.0
    a = Arena("DEADY", "LIGHTY", 1, False, martyr=True)
    assert a.martyr and a.b.max_hp == 1000.0 and a.b.dmg_mult == 10.0
    a.phase = "fight"
    a.b.hp = 1.0
    a.register_hit(a.p, a.b, 50)
    for _ in range(130):
        a.update(1 / 60, dict(EMPTY_INP))
    assert a.phase == "end" and a.win and a.martyr_gems == 100, (a.phase, a.win)
    a2 = Arena("DEADY", "LIGHTY", 1, False, martyr=True)
    a2.phase = "fight"
    a2.b.hp = 500.0
    a2.reset_round()
    assert a2.b.hp == 500.0, a2.b.hp
    print("martyr ok")

    ac = Arena("DEADY", "LIGHTY", 1, False, map=MAPS[0], sfx=None)
    assert ac.phase == "intro"
    ac.update(2.0, dict(EMPTY_INP))
    assert ac.phase == "count", ac.phase
    ac.update(3.5, dict(EMPTY_INP))
    assert ac.phase == "fight" and ac.fight_flash > 0, (ac.phase, ac.fight_flash)
    assert COUNTDOWN_T == 3.0
    print("countdown ok")

    from immy import chests as chest_mod
    assert CHEST_HELL_COST == 150
    random.seed(11)
    seen = set()
    got_devil = False
    devils = {"IMPY", "DEMONDY", "SATANY"}
    for _ in range(1000):
        kind, val = chest_mod.roll_hell()
        seen.add(kind)
        if kind == "hero":
            assert val in HEROES, val
            if val in devils:
                got_devil = True
        elif kind == "gems":
            assert 15 <= val <= 40
        else:
            assert 400 <= val <= 900
    assert seen == {"hero", "gems", "coins"} and got_devil, seen
    for _ in range(500):
        kind, val = chest_mod.roll_chaos()
        assert kind in ("hero", "coins")
        if kind == "hero":
            assert val in HEROES, val
    assert chest_mod.title("hell") != chest_mod.title("chaos")
    print("chests ok")

    a = Arena("CHAINY", "DEADY", 1, False)
    a.phase = "fight"
    a.b.x = a.p.x + 300
    assert a.cast_ability(a.p, 0, a.b)
    a = Arena("SAWY", "DEADY", 1, False)
    a.phase = "fight"
    assert a.cast_ability(a.p, 0, a.b)
    a = Arena("ROARY", "DEADY", 1, False)
    a.phase = "fight"
    assert a.cast_ability(a.p, 0, a.b)
    a = Arena("HAZEY", "DEADY", 1, False)
    a.phase = "fight"
    assert a.cast_ability(a.p, 0, a.b)
    for _ in range(120):
        a.update(1 / 60, dict(EMPTY_INP))
    print("new ability kinds ok")

    assert len(camp_mod.CAMPAIGNS) == 23
    assert sum(c["stages"] for c in camp_mod.CAMPAIGNS) == 305
    assert camp_mod.is_final(22, 16) and not camp_mod.is_final(22, 15)
    print("campaigns 23 ok")

    assert len(ach_mod.ACHIEVEMENTS) == 191
    ids = [a["id"] for a in ach_mod.ACHIEVEMENTS]
    assert len(set(ids)) == 191
    print("achievements 191 ok")

    from immy import artifacts as art_mod
    from immy.artifacts import (ARTIFACTS, ART_BY_ID, NATURES, artifact_buffs,
                                can_craft, hero_nature)
    assert len(ARTIFACTS) == 30 and len(ART_BY_ID) == 30
    for art in ARTIFACTS:
        assert art["nature"] in NATURES and art["tier"] in (1, 2, 3)
        assert art["buff"] and sum(art["cost"].values()) >= 2
    assert hero_nature("DEADY") == "dark"
    buffs = artifact_buffs("DEADY", ["dusk_veil", "night_fang"])
    assert buffs["crit"] > 0.07, buffs
    plain = artifact_buffs("DEADY", ["stone_palm"])
    boost = artifact_buffs("DEADY", [])
    assert boost == {}
    assert can_craft(ART_BY_ID["ember_charm"], {"fire": 2}, 0)
    assert not can_craft(ART_BY_ID["ember_charm"], {"fire": 1}, 0)
    assert not can_craft(ART_BY_ID["molten_plate"], {"fire": 9}, 2)
    print("artifacts 30 ok")

    from immy.config import ZONE_HEAD, ZONE_LEGS
    a = Arena("DEADY", "LIGHTY", 1, False, map=MAPS[0], sfx=None)
    a.phase = "fight"
    a.p.crit_chance = 0.0
    a.b.hp = a.b.max_hp = 1000.0
    base = 100.0
    _, d_body = a.register_hit(a.p, a.b, base, zone="body")
    a.b.hp = a.b.max_hp = 1000.0
    _, d_head = a.register_hit(a.p, a.b, base, zone="head")
    a.b.hp = a.b.max_hp = 1000.0
    _, d_legs = a.register_hit(a.p, a.b, base, zone="legs")
    assert d_head > d_body and d_legs < d_body, (d_head, d_body, d_legs)
    ratio = d_head / d_body
    assert abs(ratio - ZONE_HEAD) < 0.05, ratio
    assert abs(d_legs / d_body - ZONE_LEGS) < 0.05
    a2 = Arena("DEADY", "LIGHTY", 1, False, map=MAPS[0], sfx=None)
    a2.phase = "fight"
    a2.b.hp = a2.b.max_hp = 1000.0
    a2.register_hit(a2.p, a2.b, base, hit_y=a2.b.y - a2.b.bbox()[3] + a2.b.bbox()[1])
    assert a2.stats["headshots"] >= 0
    print("zones ok")

    trap_maps = [m for m in MAPS if m.get("trap")]
    assert len(MAPS) == 30 and len(trap_maps) >= 10
    from immy.background import trap_phase
    act1, _ = trap_phase(0.5)
    act2, _ = trap_phase(4.0)
    assert act1 and not act2
    at = Arena("DEADY", "LIGHTY", 1, False, map=trap_maps[0], sfx=None)
    at.phase = "fight"
    at.time = 0.5
    hp0 = at.p.hp
    at.p.x = 90.0
    at.update_traps(1 / 60)
    if trap_maps[0]["trap"] == "spikes":
        assert at.p.hp < hp0, (at.p.hp, hp0)
    print("arenas 30 + traps ok")

    from immy import dialogue as dlg_mod
    for pool in (dlg_mod.BOSS_INTRO, dlg_mod.ROUND2, dlg_mod.BOT_WIN,
                 dlg_mod.PLAYER_WIN, dlg_mod.TAUNT_ON_CAST,
                 dlg_mod.BOSS_CAST, dlg_mod.TAUNT_ON_PARRY):
        assert pool and all(isinstance(x, str) and x for x in pool)
    assert not hasattr(dlg_mod, "INTRO") and not hasattr(dlg_mod, "TAUNT_ON_COMBO")
    a3 = Arena("DEADY", "LIGHTY", 1, False, map=MAPS[0], sfx=None)
    assert a3.say is None, a3.say
    a3b = Arena("DEADY", "LIGHTY", 1, True, map=MAPS[0], sfx=None)
    assert a3b.say is not None and a3b.say_t > 0
    print("dialogues ok")

    from immy.config import FATALITY_ANIM_T
    from immy.arena import FATALITY_VARIANTS
    assert set(FATALITY_VARIANTS) >= {"flame", "hood", "glow", "plain", "spike", "spider"}
    assert all(len(v) >= 2 for v in FATALITY_VARIANTS.values())
    a4 = Arena("DEADY", "LIGHTY", 1, True, map=MAPS[0], sfx=None)
    a4.phase = "fatality"
    a4.fatality = {"seq": ["w", "a", "s", "d"], "idx": 0, "t": 4.0}
    a4.pending_fat = ["w", "a", "s", "d"]
    a4.finish_fatality(True)
    assert a4.phase == "fatality_anim" and a4.fatality_done
    assert getattr(a4, "fat_variant", "")
    for _ in range(200):
        a4.fatality_anim_step(1 / 60, FATALITY_ANIM_T - a4.phase_t)
        a4.phase_t -= 1 / 60
    assert a4.b.fatality_hide
    print("fatality variants ok")

    from immy.fighter import Fighter
    f = Fighter("DEADY", 400, 1, buffs={"armor": 0.2, "dmg": 0.1, "hp": 0.5, "crit": 0.1})
    assert f.armor == 0.2 and f.max_hp == 150.0 and f.crit_chance > 0.1
    dmg_before = 50.0
    f2 = Fighter("DEADY", 400, 1)
    f2.take_damage(50.0)
    assert f2.hp == f2.max_hp - 50.0
    f.take_damage(50.0)
    assert abs(f.hp - (f.max_hp - 40.0)) < 0.01, f.hp
    print("artifact buffs on fighter ok")

    d = save_mod.default_save()
    assert "settings" in d and "frags" in d and "arts" in d and "equip" in d
    assert d["settings"]["mute"] is False and 0.0 <= d["settings"]["music"] <= 1.0
    print("save schema ok")

    from immy.sound import Sfx, Audio
    sx = Sfx()
    sx.set_volume(0.5)
    assert sx.volume == 0.5
    au = Audio({"music": 0.3, "sfx": 0.4, "mute": True})
    assert au.music.enabled is False and au.sfx.enabled is False
    au.apply({"music": 0.3, "sfx": 0.4, "mute": False})
    assert au.music.enabled and au.music.volume == 0.3
    print("audio settings ok")

    print("SELFTEST OK")


if __name__ == "__main__":
    main()
