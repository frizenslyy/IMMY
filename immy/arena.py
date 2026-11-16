"""IMMY — арена: бой, раунды, способности, снаряды, эффекты, HUD."""

import math
import random

from .ai import BotAI
from .background import MAPS, draw_hero_icon
from .config import (COMBO_KB, COL_DEEPRED, COL_DARK, COL_FRAME, COL_GOLD, COL_ORANGE, COL_RED, COL_SAND,
                     CRIT_MULT, F_BIG, F_HUGE, F_MID, F_SMALL, F_TINY, GROUND_Y, H, MELEE_RANGE,
                     PARRY_CD, PARRY_STUN, W, WALL)
from .fighter import Fighter
from .heroes import HEROES
from .particles import Particles
from .util import clamp


class Arena:
    def __init__(self, player_key, bot_key, level, boss, map=None, survival=False):
        self.level = level
        self.boss = boss
        self.survival = survival
        self.wave = 1
        self.run_reward = 0
        self.mini = False
        self.map = map if map is not None else random.choice(MAPS)
        self.round = 1
        self.wins_p = 0
        self.wins_b = 0
        self.phase = "intro"
        self.phase_t = 1.6
        self.p = Fighter(player_key, W * 0.32, 1)
        self.b = Fighter(bot_key, W * 0.68, -1, scale=1.35 if boss else 1.0)
        self.b.is_bot = True
        self.b.max_hp = 100.0 * (1 + level * 0.045) * (1.35 if boss else 1.0)
        self.b.hp = self.b.max_hp
        self.b.disp_hp = self.b.max_hp
        self.b.base_dmg = (1 + level * 0.035) * (1.15 if boss else 1.0)
        self.b.base_speed = 1 + min(0.4, level * 0.015)
        self.b.reaction = max(0.18, 0.55 - level * 0.015)
        self.b.dmg_mult = self.b.base_dmg
        self.b.speed_mult = self.b.base_speed
        self.p.dmg_mult = 1.1
        self.ai = BotAI(self.b, level)
        if survival:
            self.spawn_wave()
        self.proj = []
        self.fx = []
        self.parts = Particles()
        self.melee = []
        self.shake = 0.0
        self.hitstop = 0.0
        self.combo_count = 0
        self.combo_show = 0.0
        self.win = False
        self.reward = 0
        self.rewarded = False
        self.time = 0.0

    def foe_of(self, f):
        return self.b if f is self.p else self.p

    def reset_round(self):
        for fighter, x, fc in ((self.p, W * 0.32, 1), (self.b, W * 0.68, -1)):
            fighter.x = float(x)
            fighter.y = float(GROUND_Y)
            fighter.vx = fighter.vx_target = fighter.vy = fighter.kvx = 0.0
            fighter.facing = fc
            fighter.hp = fighter.max_hp
            fighter.disp_hp = fighter.max_hp
            fighter.dead = False
            fighter.dead_t = 0.0
            fighter.cds = [0.0] * len(fighter.h["abilities"])
            fighter.crouch = False
            fighter.on_ground = True
            fighter.combo = 0
            fighter.combo_t = 0.0
            fighter.stun_t = fighter.hurt_t = fighter.attack_t = fighter.attack_cd = 0.0
            fighter.scythe_out = False
            fighter.buffs = {"flash": 0.0, "rage": 0.0, "soul": 0.0,
                             "guard": 0.0, "swift": 0.0, "vamp": 0.0}
            fighter.soul_target = None
            fighter.parry_t = fighter.parry_cd = fighter.parry_flash = 0.0
            fighter.root_t = 0.0
            fighter.poison_t = fighter.poison_dps = fighter.poison_tick = 0.0
            fighter.special_cd = 0.0
        self.b.dmg_mult = self.b.base_dmg * (1.15 if self.round >= 2 else 1.0)
        self.b.speed_mult = self.b.base_speed * (1.10 if self.round >= 2 else 1.0)
        self.proj = []
        self.fx = []
        self.melee = []
        self.parts.clear()
        self.combo_count = 0

    def spawn_wave(self):
        mini = self.wave % 5 == 0
        self.mini = mini
        key = random.choice([k for k in HEROES if k != self.p.key])
        self.b = Fighter(key, W * 0.68, -1, scale=1.25 if mini else 1.0)
        self.b.is_bot = True
        self.b.max_hp = 100.0 * (1 + self.wave * 0.08) * (1.5 if mini else 1.0)
        self.b.hp = self.b.max_hp
        self.b.disp_hp = self.b.max_hp
        self.b.base_dmg = (1 + self.wave * 0.03) * (1.15 if mini else 1.0)
        self.b.base_speed = 1 + min(0.4, self.wave * 0.012)
        self.b.reaction = max(0.18, 0.55 - self.wave * 0.012)
        self.b.dmg_mult = self.b.base_dmg
        self.b.speed_mult = self.b.base_speed
        self.ai = BotAI(self.b, min(self.wave, 20))

    def after_ko(self):
        if self.survival:
            if self.p.dead:
                self.win = False
                self.reward = self.run_reward
                self.phase = "end"
                self.phase_t = 1e9
            else:
                self.run_reward += (100 if self.mini else 50) + self.wave * 10
                hp0 = self.p.hp
                self.wave += 1
                self.reset_round()
                self.spawn_wave()
                self.p.hp = min(self.p.max_hp, hp0 + self.p.max_hp * 0.4)
                self.p.disp_hp = self.p.hp
                self.phase = "intro"
                self.phase_t = 1.6
            return
        if self.wins_p >= 2 or self.wins_b >= 2:
            self.win = self.wins_p >= 2
            self.reward = (100 if self.boss else 50) * self.level
            self.phase = "end"
            self.phase_t = 1e9
        else:
            self.round += 1
            self.reset_round()
            self.phase = "intro"
            self.phase_t = 1.6

    def update(self, dt, inp):
        self.time += dt
        self.phase_t -= dt
        self.shake = max(0.0, self.shake - 40 * dt)
        self.combo_show = max(0.0, self.combo_show - dt)
        if self.hitstop > 0:
            self.hitstop -= dt
            self.parts.update(dt * 0.15)
            return
        self.parts.update(dt)
        if self.phase == "intro":
            if self.phase_t <= 0:
                self.phase = "fight"
            return
        if self.phase == "end":
            return
        if self.phase == "ko":
            if self.phase_t <= 0:
                self.after_ko()
            return

        p, b = self.p, self.b
        if p.dead or p.stun_t > 0:
            p.vx_target = 0.0
            p.crouch = False
        else:
            p.crouch = inp["crouch"] and p.on_ground
            p.vx_target = inp["move"] * 330 * p.eff_speed() * (0.45 if p.crouch else 1.0)
            if inp["jump"] and p.on_ground and not p.crouch:
                p.vy = -960.0
                p.on_ground = False
            if inp["attack"]:
                p.start_attack(self)
            if inp.get("parry"):
                p.try_parry()
            if inp["cast"] is not None:
                self.cast_ability(p, inp["cast"], b)
            if inp.get("special"):
                self.cast_special(p, inp["special"], b)
        self.ai.update(dt, p, self)
        p.update(dt, b, self)
        b.update(dt, p, self)

        d = b.x - p.x
        if abs(d) < 56 and not p.dead and not b.dead:
            s = 1 if d >= 0 else -1
            p.x -= s * 60 * dt
            b.x += s * 60 * dt

        for m in self.melee[:]:
            m[1] -= dt
            if m[1] <= 0:
                self.melee.remove(m)
                self.do_melee(m[0], m[2])

        self.update_proj(dt)
        self.update_fx(dt)

        if p.hp <= 0 and not p.dead:
            p.dead = True
            self.wins_b += 1
            self.parts.burst(p.x, p.y - 90 * p.scale, p.h["accent"], 26, 280)
            self.shake = 8
            self.hitstop = 0.12
            self.phase = "ko"
            self.phase_t = 1.8
        elif b.hp <= 0 and not b.dead:
            b.dead = True
            self.wins_p += 1
            self.parts.burst(b.x, b.y - 90 * b.scale, b.h["accent"], 26, 280)
            self.shake = 8
            self.hitstop = 0.12
            self.phase = "ko"
            self.phase_t = 1.8

    def register_hit(self, att, foe, base, heavy=False, kb_force=None, stun=0.0, force_crit=False):
        if foe.dead:
            return "miss", 0.0
        if force_crit:
            dmg = base * att.stat_dmg * att.out_mult() * CRIT_MULT
            crit = True
        else:
            dmg, crit = att.roll_damage(base)
        res = foe.take_damage(dmg, kb_dir=att.facing, stun=stun, kb_force=kb_force)
        if res == "parry":
            att.stun_t = max(att.stun_t, PARRY_STUN)
            att.attack_t = 0.0
            self.parts.ring(foe.x, foe.y - 95 * foe.scale, "#ffd23f", 8, 58, 0.35)
            self.parts.dmg_text(foe.x, foe.y - 195 * foe.scale, 0, txt="ПАРИРОВАНИЕ",
                                color="#ffd23f", big=True)
            self.shake = max(self.shake, 4)
            return res, 0.0
        if res == "guard":
            self.parts.ring(foe.x, foe.y - 95 * foe.scale, foe.h["glow"], 30, 52, 0.25)
            self.parts.dmg_text(foe.x, foe.y - 185 * foe.scale, 0, txt="БЛОК", color="#b0baf0")
            return res, 0.0
        if res != "hit":
            return res, 0.0
        if crit:
            self.parts.burst(foe.x - foe.facing * 12, foe.y - 95 * foe.scale, "#fff2b0", 14, 260)
            self.parts.dmg_text(foe.x, foe.y - 185 * foe.scale, dmg, color="#ff5a1a", big=True)
            self.parts.ring(foe.x, foe.y - 95 * foe.scale, "#ff5a1a", 10, 60, 0.3)
            self.shake = max(self.shake, 10)
            self.hitstop = max(self.hitstop, 0.12)
        else:
            self.parts.burst(foe.x - foe.facing * 12, foe.y - 95 * foe.scale, "#ffd23f", 10, 220)
            self.parts.dmg_text(foe.x, foe.y - 170 * foe.scale, dmg, big=heavy)
            self.shake = max(self.shake, 7 if heavy else 5)
            self.hitstop = max(self.hitstop, 0.09 if heavy else 0.05)
        att.gain_energy(dmg)
        if att.buffs["vamp"] > 0 and att.vamp_pct > 0:
            heal = dmg * att.vamp_pct
            att.hp = min(att.max_hp, att.hp + heal)
            self.parts.dmg_text(att.x, att.y - 205 * att.scale, heal, color="#8aff8a")
        if att is self.p:
            self.combo_count += 1
            self.combo_show = 1.2
        return res, dmg

    def do_melee(self, att, stage=0):
        foe = self.foe_of(att)
        if foe.dead or att.dead:
            return
        rng = MELEE_RANGE * att.scale
        dx = (foe.x - att.x) * att.facing
        if dx < 0 or dx > rng:
            return
        a_top = att.y - 155 * att.scale
        b0, b1 = foe.bbox()[1], foe.bbox()[3]
        if a_top > b1 or att.y < b0:
            return
        self.register_hit(att, foe, att.melee_damage(stage), heavy=stage >= 2,
                          kb_force=COMBO_KB[min(stage, 2)])

    def cast_ability(self, f, idx, foe):
        if f.dead or f.stun_t > 0 or self.phase != "fight":
            return False
        abilities = f.h["abilities"]
        if idx < 0 or idx >= len(abilities) or f.cds[idx] > 0:
            return False
        ab = abilities[idx]
        if ab["kind"] == "scythe" and f.scythe_out:
            return False
        if not self.exec_kind(f, ab, foe):
            return False
        f.cds[idx] = ab["cd"]
        return True

    def cast_special(self, f, combo, foe):
        if f.dead or f.stun_t > 0 or self.phase != "fight":
            return False
        if f.special_cd > 0:
            return False
        sp = next((s for s in f.h.get("specials", []) if s["combo"] == combo), None)
        if sp is None or f.energy < sp["cost"]:
            return False
        if not self.exec_kind(f, sp, foe):
            return False
        f.energy -= sp["cost"]
        f.special_cd = 1.0
        return True

    def exec_kind(self, f, ab, foe):
        k = ab["kind"]
        if k == "scythe" and f.scythe_out:
            return False
        f.attack_t = 0.25
        f.attack_kind = "cast"
        if k == "scythe":
            f.scythe_out = True
            self.proj.append({"kind": "scythe", "owner": f, "x": f.x + f.facing * 40 * f.scale,
                              "y": f.y - 110 * f.scale, "vx": 520 * f.facing, "dir": f.facing,
                              "phase": "out", "timer": 0.0, "traveled": 0.0, "dmg": ab.get("dmg", 14), "spin": 0.0})
            self.parts.burst(f.x + f.facing * 40, f.y - 110 * f.scale, "#cfd6dd", 6, 120)
        elif k == "hand":
            self.fx.append({"kind": "hand_warn", "x": foe.x, "owner": f, "t": ab.get("warn", 0.8),
                            "dmg": ab.get("dmg", 18)})
        elif k == "soul":
            f.buffs["soul"] = ab.get("dur", 1.2)
            f.soul_target = foe
            self.parts.burst(f.x, f.y - 80 * f.scale, f.h["glow"], 16, 200)
        elif k == "orb":
            n = ab.get("count", 1)
            spread = ab.get("spread", 0)
            for i in range(n):
                yy = f.y - 100 * f.scale + (i - (n - 1) / 2.0) * spread
                self.proj.append({"kind": "orb", "owner": f, "x": f.x + f.facing * 44 * f.scale,
                                  "y": yy, "vx": ab.get("speed", 460) * f.facing,
                                  "dmg": ab.get("dmg", 12), "r": ab.get("r", 14),
                                  "color": f.h["accent"], "poison": ab.get("poison", 0.0),
                                  "poison_dur": ab.get("poison_dur", 3.0)})
        elif k == "ground":
            self.fx.append({"kind": "ground_warn", "x": foe.x, "owner": f, "t": ab.get("warn", 0.8),
                            "dmg": ab.get("dmg", 18), "dodge": ab.get("dodge", "jump"),
                            "radius": ab.get("radius", 60), "heavy": ab.get("heavy", False),
                            "stun": ab.get("stun", 0), "color": f.h["glow"]})
        elif k == "shock":
            rng = ab.get("range", 170)
            self.fx.append({"kind": "shock", "owner": f, "t": 0.3, "range": rng,
                            "x0": f.x + f.facing * 30 * f.scale, "y0": f.y - 95 * f.scale})
            if not foe.dead and foe.buffs["soul"] <= 0:
                dx = (foe.x - f.x) * f.facing
                if 0 <= dx <= rng and abs(foe.y - f.y) < 170:
                    self.register_hit(f, foe, ab.get("dmg", 12), stun=ab.get("stun", 1.5))
                    self.parts.burst(foe.x, foe.y - 100 * foe.scale, f.h["glow"], 14, 240)
                    self.shake = max(self.shake, 5)
        elif k == "buff_def":
            f.buffs["flash"] = ab.get("dur", 3.0)
            f.flash_mult = ab.get("mult", 0.4)
            self.parts.burst(f.x, f.y - 90 * f.scale, f.h["glow"], 20, 260)
        elif k == "buff_atk":
            f.buffs["rage"] = ab.get("dur", 5.0)
            f.rage_mult = ab.get("mult", 1.5)
            self.parts.burst(f.x, f.y - 90 * f.scale, f.h["accent"], 20, 240)
        elif k == "blink":
            self.parts.burst(f.x, f.y - 85 * f.scale, f.h["glow"], 14, 220)
            f.x = clamp(foe.x - foe.facing * 95, WALL + 30, W - WALL - 30)
            self.parts.burst(f.x, f.y - 85 * f.scale, f.h["accent"], 14, 220)
        elif k == "heal":
            amount = ab.get("amount", 20)
            f.hp = min(f.max_hp, f.hp + amount)
            self.parts.rise(f.x, f.y, f.h["glow"])
            self.parts.dmg_text(f.x, f.y - 180 * f.scale, amount, color="#8aff8a")
        elif k == "snare":
            self.proj.append({"kind": "snare", "owner": f, "x": f.x + f.facing * 44 * f.scale,
                              "y": f.y - 100 * f.scale, "vx": ab.get("speed", 620) * f.facing,
                              "dmg": ab.get("dmg", 4), "r": ab.get("r", 14),
                              "dur": ab.get("dur", 1.0), "color": f.h["accent"]})
        elif k == "summon":
            self.fx.append({"kind": "summon", "owner": f, "t": ab.get("dur", 2.0),
                            "dmg": ab.get("dmg", 5), "count": ab.get("count", 3), "bite_t": 0.4})
            self.parts.burst(f.x, f.y - 40 * f.scale, f.h["accent"], 12, 180)
        elif k == "poison":
            rng = ab.get("range", 420)
            self.fx.append({"kind": "poison", "owner": f, "t": 0.4, "x": foe.x})
            if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - f.x) <= rng:
                dur = ab.get("dur", 4.0)
                foe.poison_t = dur
                foe.poison_dps = ab.get("pct", 0.08) * foe.max_hp / dur
                self.parts.burst(foe.x, foe.y - 90 * foe.scale, "#7ad12a", 16, 200)
                self.parts.dmg_text(foe.x, foe.y - 190 * foe.scale, 0, txt="ЯД", color="#7ad12a")
        elif k == "strike":
            rng = ab.get("range", 150)
            self.fx.append({"kind": "strike", "owner": f, "t": 0.25, "x0": f.x, "range": rng})
            dx = (foe.x - f.x) * f.facing
            if not foe.dead and foe.buffs["soul"] <= 0 and 0 <= dx <= rng:
                self.register_hit(f, foe, ab.get("dmg", 24), force_crit=True, kb_force=380)
        elif k == "pull":
            rng = ab.get("range", 460)
            self.fx.append({"kind": "pull", "owner": f, "t": 0.45})
            if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - f.x) <= rng:
                foe.kvx += (1 if f.x > foe.x else -1) * 520
                self.register_hit(f, foe, ab.get("dmg", 5))
        elif k == "guard":
            f.buffs["guard"] = ab.get("dur", 1.4)
            self.parts.ring(f.x, f.y - 90 * f.scale, f.h["glow"], 20, 70, 0.4)
        elif k == "buff_spd":
            f.buffs["swift"] = ab.get("dur", 5.0)
            self.parts.burst(f.x, f.y - 90 * f.scale, f.h["glow"], 16, 220)
        elif k == "drain":
            rng = ab.get("range", 220)
            self.fx.append({"kind": "drain", "owner": f, "t": 0.4, "tx": foe.x,
                            "ty": foe.y - 90 * foe.scale})
            if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - f.x) <= rng:
                res, dmg = self.register_hit(f, foe, ab.get("dmg", 16))
                if res == "hit":
                    heal = dmg * ab.get("heal_pct", 0.6)
                    f.hp = min(f.max_hp, f.hp + heal)
                    self.parts.dmg_text(f.x, f.y - 205 * f.scale, heal, color="#8aff8a")
        elif k == "drain_aura":
            f.buffs["vamp"] = ab.get("dur", 5.0)
            f.vamp_pct = ab.get("vamp_pct", 0.45)
            self.parts.burst(f.x, f.y - 90 * f.scale, "#8aff8a", 16, 220)
        elif k == "leap":
            d = 1 if foe.x > f.x else -1
            f.vy = -820.0
            f.on_ground = False
            f.vx_target = d * 620.0
            self.fx.append({"kind": "leap", "owner": f, "t": 0.55, "dmg": ab.get("dmg", 20),
                            "radius": ab.get("radius", 120)})
        elif k == "beam":
            rng = ab.get("range", 520)
            self.fx.append({"kind": "beam", "owner": f, "t": 0.28, "x0": f.x + f.facing * 30 * f.scale,
                            "y0": f.y - 100 * f.scale, "range": rng})
            if not foe.dead and foe.buffs["soul"] <= 0:
                dx = (foe.x - f.x) * f.facing
                if 0 <= dx <= rng and not (foe.crouch and foe.on_ground):
                    self.register_hit(f, foe, ab.get("dmg", 20), heavy=True)
                    self.shake = max(self.shake, 8)
        elif k == "wave":
            n = ab.get("count", 3)
            gap = ab.get("gap", 0.14)
            for i in range(n):
                self.fx.append({"kind": "ground_warn",
                                "x": clamp(f.x + f.facing * (120 + i * 130), WALL + 40, W - WALL - 40),
                                "owner": f, "t": ab.get("warn", 0.7) + i * gap,
                                "dmg": ab.get("dmg", 14), "dodge": ab.get("dodge", "jump"),
                                "color": f.h["glow"]})
        elif k == "rain":
            n = ab.get("count", 4)
            for i in range(n):
                self.fx.append({"kind": "ground_warn",
                                "x": clamp(foe.x + random.uniform(-150, 150), WALL + 40, W - WALL - 40),
                                "owner": f, "t": ab.get("warn", 0.8) + i * 0.15,
                                "dmg": ab.get("dmg", 10), "dodge": ab.get("dodge", "crouch"),
                                "color": f.h["glow"]})
        elif k == "grab":
            if foe.buffs["soul"] > 0 or foe.dead or abs(foe.x - f.x) > ab.get("range", 240):
                return False
            self.register_hit(f, foe, ab.get("dmg", 12), kb_force=0)
            foe.root_t = max(foe.root_t, ab.get("dur", 2.0))
            foe.stun_t = max(foe.stun_t, 0.4)
            self.fx.append({"kind": "grab", "owner": f, "foe": foe, "t": ab.get("dur", 2.0),
                            "dmg": ab.get("tick", 4), "tick_t": 0.5, "color": f.h["accent"]})
            self.shake = max(self.shake, 6)
        elif k == "barrage":
            self.fx.append({"kind": "barrage", "owner": f, "t": ab.get("dur", 2.2),
                            "n": ab.get("count", 5), "spawn_t": 0.1, "gap": ab.get("gap", 0.18),
                            "dmg": ab.get("dmg", 8), "speed": ab.get("speed", 720), "color": f.h["accent"]})
        else:
            return False
        return True

    def update_proj(self, dt):
        for pr in self.proj[:]:
            foe = self.foe_of(pr["owner"])
            if pr["kind"] == "scythe":
                pr["spin"] += 10 * dt
                if pr["phase"] == "out":
                    pr["x"] += pr["vx"] * dt
                    pr["traveled"] += abs(pr["vx"] * dt)
                    if not foe.dead and foe.buffs["soul"] <= 0 and self.circ_hit(pr, foe, 26):
                        self.register_hit(pr["owner"], foe, pr["dmg"])
                        self.parts.burst(pr["x"], pr["y"], "#cfd6dd", 10, 200)
                        pr["phase"] = "hold"
                        pr["timer"] = 3.0
                    elif pr["traveled"] >= 560:
                        pr["phase"] = "hold"
                        pr["timer"] = 3.0
                elif pr["phase"] == "hold":
                    pr["timer"] -= dt
                    if pr["timer"] <= 0:
                        pr["phase"] = "return"
                else:
                    tx = pr["owner"].x
                    ty = pr["owner"].y - 100 * pr["owner"].scale
                    dxx, dyy = tx - pr["x"], ty - pr["y"]
                    dd = math.hypot(dxx, dyy)
                    if dd < 34:
                        pr["owner"].scythe_out = False
                        self.proj.remove(pr)
                        self.parts.burst(pr["x"], pr["y"], "#cfd6dd", 8, 160)
                        continue
                    sp = 760 * dt
                    pr["x"] += dxx / dd * sp
                    pr["y"] += dyy / dd * sp
                    if not foe.dead and foe.buffs["soul"] <= 0 and self.circ_hit(pr, foe, 24):
                        self.register_hit(pr["owner"], foe, pr["dmg"] * 0.7)
            else:
                pr["x"] += pr["vx"] * dt
                pr["y"] += pr.get("vy", 0.0) * dt
                if pr["y"] < 40 or pr["y"] > GROUND_Y + 10:
                    self.proj.remove(pr)
                    continue
                if random.random() < dt * 40:
                    self.parts.trail(pr["x"], pr["y"] + random.uniform(-6, 6), pr["color"])
                if not foe.dead and foe.buffs["soul"] <= 0 and self.circ_hit(pr, foe, pr["r"] + 14):
                    self.register_hit(pr["owner"], foe, pr["dmg"])
                    if pr["kind"] == "snare":
                        foe.root_t = max(foe.root_t, pr["dur"])
                        self.parts.ring(foe.x, foe.y - 10, pr["color"], 14, 52, 0.35)
                        self.parts.dmg_text(foe.x, foe.y - 190 * foe.scale, 0, txt="СВЯЗАН", color=pr["color"])
                    elif pr.get("poison"):
                        foe.poison_t = pr.get("poison_dur", 3.0)
                        foe.poison_dps = pr["poison"] * foe.max_hp / pr.get("poison_dur", 3.0)
                    self.parts.burst(pr["x"], pr["y"], pr["color"], 14, 240)
                    self.shake = max(self.shake, 4)
                    self.proj.remove(pr)
                    continue
                if pr["x"] < 20 or pr["x"] > W - 20:
                    self.parts.burst(pr["x"], pr["y"], pr["color"], 10, 180)
                    self.proj.remove(pr)

    def circ_hit(self, pr, foe, r):
        x0, y0, x1, y1 = foe.bbox()
        return x0 - r <= pr["x"] <= x1 + r and y0 - r <= pr["y"] <= y1 + r

    def update_fx(self, dt):
        for fx in self.fx[:]:
            k = fx["kind"]
            if k == "summon":
                fx["t"] -= dt
                fx["bite_t"] -= dt
                if fx["bite_t"] <= 0:
                    fx["bite_t"] = 0.5
                    foe = self.foe_of(fx["owner"])
                    if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - fx["owner"].x) < 420:
                        self.register_hit(fx["owner"], foe, fx.get("dmg", 5))
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k == "leap":
                fx["t"] -= dt
                if fx["t"] <= 0:
                    f = fx["owner"]
                    foe = self.foe_of(f)
                    if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - f.x) <= fx["radius"] \
                            and abs(foe.y - f.y) < 220:
                        self.register_hit(f, foe, fx.get("dmg", 20), heavy=True, kb_force=420)
                    self.parts.burst(f.x, GROUND_Y - 20, f.h["glow"], 20, 300)
                    self.parts.ring(f.x, GROUND_Y - 10, f.h["accent"], 12, fx["radius"], 0.4)
                    self.shake = max(self.shake, 9)
                    self.fx.remove(fx)
                continue
            if k == "pull":
                fx["t"] -= dt
                foe = self.foe_of(fx["owner"])
                if not foe.dead and foe.buffs["soul"] <= 0 and foe.root_t <= 0:
                    foe.kvx += (1 if fx["owner"].x > foe.x else -1) * 2600 * dt
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k == "grab":
                fx["t"] -= dt
                foe = fx["foe"]
                fx["tick_t"] -= dt
                if fx["tick_t"] <= 0:
                    fx["tick_t"] = 0.5
                    if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - fx["owner"].x) < 260:
                        self.register_hit(fx["owner"], foe, fx["dmg"], kb_force=0)
                    else:
                        fx["t"] = 0.0
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k == "barrage":
                fx["t"] -= dt
                fx["spawn_t"] -= dt
                f = fx["owner"]
                foe = self.foe_of(f)
                if fx["spawn_t"] <= 0 and fx["n"] > 0 and not f.dead:
                    fx["spawn_t"] = fx["gap"]
                    fx["n"] -= 1
                    sx, sy = f.x + f.facing * 40 * f.scale, f.y - 110 * f.scale
                    tx, ty = foe.x, foe.y - 80 * foe.scale
                    dd = math.hypot(tx - sx, ty - sy) or 1.0
                    sp = fx["speed"]
                    self.proj.append({"kind": "barr", "owner": f, "x": sx, "y": sy,
                                      "vx": (tx - sx) / dd * sp, "vy": (ty - sy) / dd * sp,
                                      "dmg": fx["dmg"], "r": 9, "color": fx["color"]})
                    self.parts.burst(sx, sy, fx["color"], 4, 120)
                if fx["t"] <= 0 or (fx["n"] <= 0 and fx["spawn_t"] < fx["gap"] - 0.05 and not any(
                        p["owner"] is f for p in self.proj)):
                    self.fx.remove(fx)
                continue
            fx["t"] -= dt
            if fx["t"] > 0:
                continue
            if k == "hand_warn":
                foe = self.foe_of(fx["owner"])
                if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - fx["x"]) < 62 and foe.y > GROUND_Y - 70:
                    self.register_hit(fx["owner"], foe, fx["dmg"])
                    self.parts.burst(fx["x"], GROUND_Y - 50, "#e8e4d0", 14, 220)
                    self.shake = max(self.shake, 5)
                fx["kind"] = "hand"
                fx["t"] = 0.5
            elif k == "ground_warn":
                foe = self.foe_of(fx["owner"])
                if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - fx["x"]) < fx.get("radius", 60):
                    dodge = fx.get("dodge", "jump")
                    safe = foe.crouch if dodge == "crouch" else foe.y <= GROUND_Y - 70
                    if not safe:
                        self.register_hit(fx["owner"], foe, fx["dmg"], heavy=fx.get("heavy", False),
                                          stun=fx.get("stun", 0))
                        self.parts.burst(fx["x"], GROUND_Y - 60, fx.get("color", "#ffd23f"), 18, 260)
                        self.shake = max(self.shake, 7)
                fx["kind"] = "ground"
                fx["t"] = 0.4
            else:
                self.fx.remove(fx)

    def draw_scythe_at(self, cv, x, y, ang):
        dxn, dyn = math.cos(ang), math.sin(ang)
        cv.create_line(x - dxn * 35, y - dyn * 35, x + dxn * 35, y + dyn * 35,
                       fill="#6b4a2a", width=5, tags=("dyn",))
        bx, by = x + dxn * 35, y + dyn * 35
        dx2, dy2 = -dyn, dxn
        cv.create_polygon(bx, by,
                          bx + dx2 * 26 - dxn * 8, by + dy2 * 26 - dyn * 8,
                          bx + dx2 * 40 + dxn * 6, by + dy2 * 40 + dyn * 6,
                          bx + dx2 * 16 + dxn * 10, by + dy2 * 16 + dyn * 10,
                          fill="#d7dee6", outline="#8a949e", tags=("dyn",))

    def draw_fx(self, cv, ox, oy, warn_only):
        now = self.time
        for fx in self.fx:
            k = fx["kind"]
            is_warn = k.endswith("_warn")
            if is_warn != warn_only:
                continue
            if k == "hand_warn":
                r = 26 + 6 * math.sin(now * 12)
                cv.create_oval(fx["x"] - r + ox, GROUND_Y - r * 0.5 + oy, fx["x"] + r + ox, GROUND_Y + r * 0.5 + oy,
                               outline="#ff2a1a", width=3, tags=("dyn",))
            elif k == "ground_warn":
                col = fx.get("color", "#ffd23f")
                rad = fx.get("radius", 60)
                if fx.get("heavy"):
                    cv.create_line(fx["x"] + ox, 0, fx["x"] + ox, GROUND_Y, fill=col, width=2,
                                   dash=(4, 8), tags=("dyn",))
                r = rad + 6 * math.sin(now * 14)
                cv.create_oval(fx["x"] - r + ox, GROUND_Y - r * 0.45 + oy, fx["x"] + r + ox, GROUND_Y + r * 0.45 + oy,
                               outline=col, width=3, tags=("dyn",))
            elif k == "hand":
                p = 1 - fx["t"] / 0.5
                hgt = 95 * min(1.0, p * 5) * (1.0 if fx["t"] > 0.12 else fx["t"] / 0.12)
                x = fx["x"]
                cv.create_oval(x - 30 + ox, GROUND_Y - 10 + oy, x + 30 + ox, GROUND_Y + 8 + oy,
                               fill="#0a0402", outline="", tags=("dyn",))
                cv.create_rectangle(x - 15 + ox, GROUND_Y - hgt + oy, x + 15 + ox, GROUND_Y + oy,
                                    fill="#e8e4d0", outline="#8a8570", width=2, tags=("dyn",))
                for fdx in (-10, 0, 10):
                    cv.create_rectangle(x + fdx - 4 + ox, GROUND_Y - hgt - 16 + oy, x + fdx + 4 + ox, GROUND_Y - hgt + oy,
                                        fill="#e8e4d0", outline="", tags=("dyn",))
            elif k == "ground":
                col = fx.get("color", "#ff8c1a")
                flick = random.uniform(0.8, 1.2)
                hgt = 300 if fx.get("heavy") else 230
                wid = 34 if fx.get("heavy") else 26
                cv.create_rectangle(fx["x"] - wid * flick + ox, GROUND_Y - hgt + oy,
                                    fx["x"] + wid * flick + ox, GROUND_Y + oy,
                                    fill=col, stipple="gray50", outline="", tags=("dyn",))
                cv.create_rectangle(fx["x"] - 12 * flick + ox, GROUND_Y - hgt + oy,
                                    fx["x"] + 12 * flick + ox, GROUND_Y + oy,
                                    fill="#ffffff", stipple="gray25", outline="", tags=("dyn",))
            elif k == "shock":
                f = fx["owner"]
                x0, y0 = fx["x0"] + ox, fx["y0"] + oy
                pts = [x0, y0]
                for i in range(1, 7):
                    tt = i / 6
                    pts += [x0 + f.facing * fx.get("range", 185) * tt, y0 + random.uniform(-16, 16) * (1 - tt)]
                cv.create_line(*pts, fill="#ffd23f", width=9, tags=("dyn",), stipple="gray50")
                cv.create_line(*pts, fill="#fff7b0", width=4, tags=("dyn",))
            elif k == "beam":
                f = fx["owner"]
                x0, y0 = fx["x0"] + ox, fx["y0"] + oy
                x1 = x0 + f.facing * fx.get("range", 520)
                cv.create_line(x0, y0, x1, y0, fill=f.h["accent"], width=26, tags=("dyn",), stipple="gray25")
                cv.create_line(x0, y0, x1, y0, fill=f.h["glow"], width=10, tags=("dyn",))
                cv.create_line(x0, y0, x1, y0, fill="#ffffff", width=3, tags=("dyn",))
            elif k == "strike":
                f = fx["owner"]
                x0 = fx["x0"] + ox
                r = fx.get("range", 150) * (0.4 + 0.6 * (1 - fx["t"] / 0.25))
                a0 = -50 if f.facing > 0 else 130
                cv.create_arc(x0 - r, GROUND_Y - 200 + oy, x0 + r, GROUND_Y - 20 + oy,
                              start=a0, extent=80, style="arc", outline=f.h["glow"], width=5, tags=("dyn",))
            elif k == "poison":
                x = fx["x"] + ox
                p = 1 - fx["t"] / 0.4
                r = 30 + 40 * p
                cv.create_oval(x - r, GROUND_Y - 150 - r * 0.5 + oy, x + r, GROUND_Y - 150 + r * 0.5 + oy,
                               outline="#7ad12a", width=3, tags=("dyn",), stipple="gray50")
            elif k == "drain":
                f = fx["owner"]
                x0, y0 = f.x + ox, f.y - 95 * f.scale + oy
                x1, y1 = fx["tx"] + ox, fx["ty"] + oy
                for i in range(3):
                    tt = (now * 2.5 + i / 3.0) % 1.0
                    px, py = x0 + (x1 - x0) * (1 - tt), y0 + (y1 - y0) * (1 - tt)
                    cv.create_oval(px - 4, py - 4, px + 4, py + 4, fill="#8aff8a", outline="", tags=("dyn",))
                cv.create_line(x0, y0, x1, y1, fill="#8aff8a", width=2, tags=("dyn",), stipple="gray25")
            elif k == "summon":
                f = fx["owner"]
                for i in range(fx.get("count", 3)):
                    sx = f.x + math.sin(now * 5 + i * 2.1) * 70 + (i - 1) * 34 + ox
                    sy = GROUND_Y - 12 + math.sin(now * 9 + i) * 4 + oy
                    cv.create_oval(sx - 9, sy - 7, sx + 9, sy + 7,
                                   fill=f.h["body"], outline=f.h["accent"], width=2, tags=("dyn",))
                    for la in (-1, 1):
                        cv.create_line(sx + la * 8, sy, sx + la * 15, sy + 8, fill=f.h["accent"], width=2, tags=("dyn",))
                    cv.create_oval(sx - 4, sy - 5, sx - 1, sy - 2, fill=f.h["eye"], outline="", tags=("dyn",))
                    cv.create_oval(sx + 1, sy - 5, sx + 4, sy - 2, fill=f.h["eye"], outline="", tags=("dyn",))
            elif k == "pull":
                f = fx["owner"]
                x0, y0 = f.x + ox, f.y - 90 * f.scale + oy
                for i in range(5):
                    a = now * 9 + i * 1.257
                    rr = 30 + 26 * i
                    cv.create_line(x0 + math.cos(a) * rr, y0 + math.sin(a) * rr * 0.4,
                                   x0 + math.cos(a + 1.2) * rr * 0.6, y0 + math.sin(a + 1.2) * rr * 0.24,
                                   fill=f.h["glow"], width=2, tags=("dyn",))
            elif k == "leap":
                f = fx["owner"]
                r = fx["radius"]
                cv.create_oval(f.x - r + ox, GROUND_Y - r * 0.3 + oy, f.x + r + ox, GROUND_Y + r * 0.3 + oy,
                               outline=f.h["accent"], width=3, tags=("dyn",), dash=(6, 6))
            elif k == "grab":
                f, foe = fx["owner"], fx["foe"]
                x0, y0 = f.x + f.facing * 26 * f.scale + ox, f.y - 90 * f.scale + oy
                x1, y1 = foe.x + ox, foe.y - 80 * foe.scale + oy
                cv.create_line(x0, y0, x1, y1, fill=fx["color"], width=5, tags=("dyn",), stipple="gray50")
                cv.create_line(x0, y0, x1, y1, fill="#fff7b0", width=2, tags=("dyn",))
                for i in range(4):
                    tt = (now * 3.0 + i / 4.0) % 1.0
                    px, py = x0 + (x1 - x0) * tt, y0 + (y1 - y0) * tt
                    cv.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#fff7b0", outline="", tags=("dyn",))

    def draw_proj(self, cv, ox, oy):
        for pr in self.proj:
            if pr["kind"] == "scythe":
                self.draw_scythe_at(cv, pr["x"] + ox, pr["y"] + oy, pr["spin"])
            else:
                x, y = pr["x"] + ox, pr["y"] + oy
                r = pr.get("r", 14)
                cv.create_oval(x - r, y - r, x + r, y + r, fill=pr.get("color", "#ff5a1a"), outline="#ffd23f",
                               width=2, tags=("dyn",))
                cv.create_oval(x - r * 0.5, y - r * 0.5, x + r * 0.5, y + r * 0.5, fill="#fff7b0",
                               outline="", tags=("dyn",))

    def hp_bar(self, cv, x, w, f, align_left):
        frac = clamp(f.hp / f.max_hp, 0.0, 1.0)
        dfrac = clamp(f.disp_hp / f.max_hp, 0.0, 1.0)
        fw = int(w * frac)
        dw = int(w * dfrac)
        cv.create_rectangle(x - 3, 29, x + w + 3, 65, fill="#160404", outline=COL_FRAME, width=2, tags=("dyn",))
        if align_left:
            if dw > fw:
                cv.create_rectangle(x, 32, x + dw, 62, fill="#ffffff", outline="", tags=("dyn",), stipple="gray50")
            cv.create_rectangle(x, 32, x + fw, 62, fill=COL_DEEPRED, outline="", tags=("dyn",))
            px = x + 2
            draw_hero_icon(cv, f.key, px, 68, 34, border=False)
            cv.create_text(x + 44, 16, text=f.h["name"], anchor="w", fill=COL_GOLD, font=F_SMALL, tags=("dyn",))
        else:
            if dw > fw:
                cv.create_rectangle(x + w - dw, 32, x + w, 62, fill="#ffffff", outline="", tags=("dyn",), stipple="gray50")
            cv.create_rectangle(x + w - fw, 32, x + w, 62, fill=COL_DEEPRED, outline="", tags=("dyn",))
            px = x + w - 36
            draw_hero_icon(cv, f.key, px, 68, 34, border=False)
            label = f.h["name"] + ("  [БОТ]" if f.is_bot else "")
            cv.create_text(x + w - 44, 16, text=label, anchor="e", fill=COL_GOLD, font=F_SMALL, tags=("dyn",))

    def draw_hud(self, cv, coins):
        self.hp_bar(cv, 100, 380, self.p, True)
        self.hp_bar(cv, W - 480, 380, self.b, False)
        efrac = clamp(self.p.energy / 100.0, 0.0, 1.0)
        cv.create_rectangle(141, 70, 483, 84, fill="#160404", outline="#5a1c10", width=2, tags=("dyn",))
        if efrac > 0:
            cv.create_rectangle(144, 73, 144 + int(336 * efrac), 81, fill=COL_GOLD, outline="", tags=("dyn",))
        cv.create_text(480, 77, text="ЭНЕРГИЯ", anchor="e", font=F_TINY,
                       fill="#5a1c10" if efrac > 0.85 else "#a1700a", tags=("dyn",))
        for i in range(0 if self.survival else 2):
            for side, wins in ((-1, self.wins_p), (1, self.wins_b)):
                cx = W / 2 + side * (44 + i * 30)
                filled = wins > i
                cv.create_oval(cx - 10, 36, cx + 10, 56,
                               fill=COL_DEEPRED if filled else "#1a0908",
                               outline=COL_GOLD if filled else COL_FRAME, width=2, tags=("dyn",))
        if self.survival:
            lvl_txt = ("ВОЛНА %d · МИНИ-БОСС" % self.wave) if self.mini else ("ВОЛНА %d" % self.wave)
        else:
            lvl_txt = ("БОСС · УР. %d" if self.boss else "БОТ · УР. %d") % self.level
        cv.create_text(W - 60, 110, text=lvl_txt, anchor="e", font=F_MID,
                       fill="#ff2a1a" if (self.boss or (self.survival and self.mini)) else COL_ORANGE, tags=("dyn",))
        cv.create_oval(44, 74, 62, 92, fill=COL_GOLD, outline="#a1700a", width=2, tags=("dyn",))
        cv.create_text(70, 83, text=str(coins), anchor="w", fill=COL_GOLD, font=F_MID, tags=("dyn",))
        n_ab = len(self.p.h["abilities"])
        total = (n_ab + 1) * 66 - 6
        x0 = W // 2 - total // 2
        for i in range(n_ab):
            x = x0 + i * 66
            ab = self.p.h["abilities"][i]
            nm, cdmax = ab["name"], ab["cd"]
            frac = self.p.cds[i] / cdmax if cdmax else 0.0
            ready = self.p.cds[i] <= 0
            cv.create_rectangle(x, H - 76, x + 60, H - 16, fill=COL_DARK,
                                outline=COL_GOLD if ready else "#5a1c10", width=2, tags=("dyn",))
            if frac > 0:
                cv.create_rectangle(x, H - 76, x + 60, H - 76 + 60 * frac, fill="#000000",
                                    stipple="gray50", outline="", tags=("dyn",))
                cv.create_text(x + 30, H - 44, text="%.0f" % math.ceil(self.p.cds[i]), fill="#e8c9a0",
                               font=F_SMALL, tags=("dyn",))
            cv.create_text(x + 30, H - 58, text=str(i + 1), fill=COL_GOLD if ready else "#8a4a20",
                           font=F_MID, tags=("dyn",))
            cv.create_text(x + 30, H - 27, text=nm.split()[0][:9], fill=COL_ORANGE, font=F_TINY, tags=("dyn",))
        x = x0 + n_ab * 66
        pcd = self.p.parry_cd
        ready = pcd <= 0
        col = "#ffd23f" if self.p.parry_t > 0 else (COL_GOLD if ready else "#5a1c10")
        cv.create_rectangle(x, H - 76, x + 60, H - 16, fill=COL_DARK, outline=col, width=2, tags=("dyn",))
        if pcd > 0:
            frac = pcd / PARRY_CD
            cv.create_rectangle(x, H - 76, x + 60, H - 76 + 60 * frac, fill="#000000",
                                stipple="gray50", outline="", tags=("dyn",))
            cv.create_text(x + 30, H - 44, text="%.1f" % pcd, fill="#e8c9a0", font=F_SMALL, tags=("dyn",))
        cv.create_text(x + 30, H - 58, text="F", fill=COL_GOLD if ready else "#8a4a20", font=F_MID, tags=("dyn",))
        cv.create_text(x + 30, H - 27, text="ПАРИР", fill=COL_ORANGE, font=F_TINY, tags=("dyn",))
        sps = self.p.h.get("specials", ())
        sx = x0 + total + 12
        for i, sp in enumerate(sps):
            x = sx + i * 58
            can = self.p.energy >= sp["cost"] and self.p.special_cd <= 0
            col = "#ffd24a" if can else "#5a1c10"
            cv.create_rectangle(x, H - 76, x + 54, H - 16, fill=COL_DARK, outline=col, width=2, tags=("dyn",))
            cv.create_text(x + 27, H - 58, text=sp["combo"].upper(), fill="#ffd24a" if can else "#8a4a20",
                           font=F_SMALL, tags=("dyn",))
            cv.create_text(x + 27, H - 40, text=sp["name"].split()[0][:8], fill=COL_ORANGE, font=F_TINY, tags=("dyn",))
            cv.create_text(x + 27, H - 25, text=str(sp["cost"]), fill="#ffd24a" if can else "#8a4a20",
                           font=F_TINY, tags=("dyn",))
        if self.combo_show > 0 and self.combo_count >= 2:
            cv.create_text(W / 2 + 2, 132, text="COMBO x%d" % self.combo_count, font=F_BIG, fill="#2a0503", tags=("dyn",))
            cv.create_text(W / 2, 130, text="COMBO x%d" % self.combo_count, font=F_BIG, fill=COL_GOLD, tags=("dyn",))

    def banner(self, cv, txt, col, y=270):
        slide = max(0.0, self.phase_t - 1.2) if self.phase_t < 1e9 else 0.0
        off = int(slide * 900)
        cv.create_text(W / 2 + off + 4, y + 4, text=txt, font=F_HUGE, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2 + off, y, text=txt, font=F_HUGE, fill=col, tags=("dyn",))

    def draw(self, cv, coins):
        sh = self.shake
        ox = random.uniform(-sh, sh) if sh > 0.5 else 0.0
        oy = random.uniform(-sh, sh) if sh > 0.5 else 0.0
        cv.delete("dyn")
        self.draw_fx(cv, ox, oy, True)
        self.p.render(cv, ox, oy)
        self.b.render(cv, ox, oy)
        self.draw_fx(cv, ox, oy, False)
        self.draw_proj(cv, ox, oy)
        self.parts.draw(cv, ox, oy)
        self.draw_hud(cv, coins)
        cv.create_rectangle(0, 0, W, 24, fill="#000000", stipple="gray12", outline="", tags=("dyn",))
        cv.create_rectangle(0, H - 24, W, H, fill="#000000", stipple="gray12", outline="", tags=("dyn",))
        cv.create_rectangle(0, 0, 28, H, fill="#000000", stipple="gray12", outline="", tags=("dyn",))
        cv.create_rectangle(W - 28, 0, W, H, fill="#000000", stipple="gray12", outline="", tags=("dyn",))

        if self.p.buffs["soul"] > 0 or self.b.buffs["soul"] > 0:
            cv.create_rectangle(0, 0, W, H, fill="#1a0a2a", stipple="gray25", outline="", tags=("dyn",))

        if self.phase == "intro":
            if self.survival:
                txt = ("ВОЛНА %d" % self.wave) if self.phase_t > 0.6 else "БОЙ!"
            else:
                txt = "РАУНД %d" % self.round if self.phase_t > 0.6 else "БОЙ!"
            col = COL_GOLD if self.phase_t > 0.6 else COL_RED
            self.banner(cv, txt, col)
        elif self.phase == "ko":
            self.banner(cv, "НОКАУТ!", COL_RED)
        elif self.phase == "end":
            cv.create_rectangle(0, 0, W, H, fill="#0a0202", stipple="gray50", outline="", tags=("dyn",))
            cv.create_rectangle(W / 2 - 340, 170, W / 2 + 340, 560, fill=COL_DARK, outline=COL_GOLD,
                                width=3, tags=("dyn",))
            if self.survival:
                cv.create_text(W / 2, 245, text="ВЫЖИВАНИЕ ОКОНЧЕНО", font=F_HUGE, fill=COL_GOLD, tags=("dyn",))
                if self.reward > 0:
                    cv.create_text(W / 2, 315, text="+%d МОНЕТ" % self.reward, font=F_BIG, fill=COL_ORANGE, tags=("dyn",))
                cv.create_text(W / 2, 360, text="Пройдено волн: %d" % (self.wave - 1),
                               font=F_SMALL, fill="#e8c9a0", tags=("dyn",))
            else:
                t1 = "ПОБЕДА!" if self.win else "ПОРАЖЕНИЕ"
                cv.create_text(W / 2, 245, text=t1, font=F_HUGE,
                               fill=COL_GOLD if self.win else "#8a4a20", tags=("dyn",))
                if self.win:
                    cv.create_text(W / 2, 315, text="+%d МОНЕТ" % self.reward, font=F_BIG, fill=COL_ORANGE, tags=("dyn",))
                    sub = "Уровень %d%s пройден!" % (self.level, " (БОСС ×2)" if self.boss else "")
                    cv.create_text(W / 2, 360, text=sub, font=F_SMALL, fill="#e8c9a0", tags=("dyn",))
                else:
                    cv.create_text(W / 2, 325, text="Бот уровня %d оказался сильнее." % self.level,
                                   font=F_SMALL, fill="#e8c9a0", tags=("dyn",))
                cv.create_text(W / 2, 420, text="Счёт раундов  %d : %d" % (self.wins_p, self.wins_b),
                               font=F_SMALL, fill=COL_SAND, tags=("dyn",))
