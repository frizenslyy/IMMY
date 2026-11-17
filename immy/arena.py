"""IMMY — арена: бой, раунды, способности, снаряды, эффекты, HUD."""

import math
import random

from .ai import BotAI
from .background import MAPS, draw_hero_icon
from .config import (COMBO_KB, COMBO_MULT, COL_BLOOD, COL_DEEPRED, COL_DARK, COL_FRAME, COL_GEM, COL_GOLD,
                     COL_ORANGE, COL_RED, COL_SAND, CRIT_MULT, FATALITY_ANIM_T, FATALITY_BONUS,
                     FATALITY_GEMS, FATALITY_KEYS, FATALITY_TXT, FATALITY_WINDOW, F_BIG, F_HUGE, F_MID,
                     F_SMALL, F_TINY, GROUND_Y, H, INJURY_CHANCE, LEGEND_FOE_HP, MARTYR_COIN_PER_DMG,
                     MARTYR_DMG_MULT, MARTYR_GEMS, MARTYR_HP_MULT, MARTYR_ROUNDS, MELEE_RANGE,
                     MYTH_ENERGY, MYTH_FOE_HP, PARRY_CD, PARRY_STUN, RIPOSTE_DUR, RIPOSTE_MULT,
                     RARITY_POWER, THORNS_PCT, ULT_CHARGE_MAX, ULT_HP, ULT_LEFT, ULT_QUALITY,
                     ULT_RANGE_Y, W, WALL)
from .fighter import Fighter
from .heroes import HEROES
from .particles import Particles
from .util import clamp

HAZE_SELF_KINDS = {"ground", "hand", "orb", "strike", "shock", "barrage", "roar", "aoe", "meteor", "rain", "wave"}


def _snap_fighter(f):
    return {"x": round(f.x, 1), "y": round(f.y, 1), "fc": f.facing, "cr": f.crouch, "gr": f.on_ground,
            "hp": round(f.hp, 1), "mhp": round(f.max_hp, 1), "dh": round(f.disp_hp, 1),
            "dd": f.dead, "dt": round(f.dead_t, 2), "at": round(f.attack_t, 3), "ak": f.attack_kind,
            "st": round(f.stun_t, 3), "ht": round(f.hurt_t, 3), "hf": round(f.hit_flash, 3),
            "en": round(f.energy, 1), "bf": {k: round(v, 2) for k, v in f.buffs.items()},
            "cb": f.combo, "rt": round(f.root_t, 2), "sc": f.scythe_out,
            "cds": [round(c, 2) for c in f.cds],
            "spcd": {k: round(v, 2) for k, v in f.sp_cds.items()},
            "stcd": {k: round(v, 2) for k, v in f.strike_cds.items()},
            "pcd": round(f.parry_cd, 2), "pt": round(f.parry_t, 2),
            "inj": f.injury["kind"] if f.injury else None,
            "inja": f.injury["ability"] if f.injury else 0}


class Arena:
    def __init__(self, player_key, bot_key, level, boss, map=None, survival=False, net=False, mirror=False,
                 martyr=False):
        self.level = level
        self.boss = boss
        self.survival = survival
        self.martyr = martyr
        self.dmg_dealt = 0.0
        self.martyr_gems = 0
        self.net = net or mirror
        self.mirror = mirror
        self.remote_inp = None
        self.pending_snap = None
        self.net_events = []
        self.pending_fat = []
        self.fatality = None
        self.fatality_done = False
        self.fatality_bonus = 0
        self.fatality_gems = 0
        self.fat_style = "plain"
        self.fat_anim_t = 0.0
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
        pw = 1.0 if self.net else RARITY_POWER.get(HEROES[player_key]["rarity"], 1.0)
        self.p.power = pw
        self.p.max_hp = 100.0 * pw
        self.p.hp = self.p.disp_hp = self.p.max_hp
        self.p.dmg_mult = 1.1 * pw
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
        self.ai = BotAI(self.b, level)
        if martyr:
            self.b.max_hp = 100.0 * MARTYR_HP_MULT
            self.b.hp = self.b.disp_hp = self.b.max_hp
            self.b.base_dmg = MARTYR_DMG_MULT
            self.b.dmg_mult = MARTYR_DMG_MULT
            self.b.reaction = 0.22
        if survival:
            self.spawn_wave()
        self.proj = []
        self.fx = []
        self.parts = Particles()
        self.melee = []
        self.strikes = []
        self.shake = 0.0
        self.hitstop = 0.0
        self.combo_count = 0
        self.combo_show = 0.0
        self.max_combo = 0
        self.quality_finish = 0
        self.stats = {"specials": 0, "ults": 0, "parries": 0, "strikes": 0, "injuries": 0, "myth_ults": 0,
                      "casts": 0, "bleeds": 0, "chains": 0, "saws": 0, "roars": 0, "aoes": 0,
                      "haze": 0, "legend_ults": 0}
        self.win = False
        self.reward = 0
        self.rewarded = False
        self.time = 0.0
        if self.mirror:
            self.ai = None

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
                             "guard": 0.0, "swift": 0.0, "vamp": 0.0,
                             "curse": 0.0, "thorns": 0.0, "riposte": 0.0}
            fighter.soul_target = None
            fighter.parry_t = fighter.parry_cd = fighter.parry_flash = 0.0
            fighter.root_t = 0.0
            fighter.poison_t = fighter.poison_dps = fighter.poison_tick = 0.0
            fighter.bleed_t = fighter.bleed_dps = fighter.bleed_tick = 0.0
            fighter.special_cd = 0.0
            fighter.sp_cds = {}
            fighter.strike_cds = {}
            fighter.injury = None
        self.b.dmg_mult = self.b.base_dmg * (1.15 if self.round >= 2 else 1.0)
        self.b.speed_mult = self.b.base_speed * (1.10 if self.round >= 2 else 1.0)
        self.proj = []
        self.fx = []
        self.melee = []
        self.strikes = []
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
        if self.martyr:
            if self.wins_p >= 2:
                self.win = True
                self.martyr_gems = MARTYR_GEMS
                self.phase = "end"
                self.phase_t = 1e9
            elif self.wins_b >= 2 or self.round >= MARTYR_ROUNDS:
                self.win = False
                self.reward = int(self.dmg_dealt * MARTYR_COIN_PER_DMG)
                self.phase = "end"
                self.phase_t = 1e9
            else:
                self.round += 1
                self.reset_round()
                self.phase = "intro"
                self.phase_t = 1.6
            return
        if self.survival:
            if self.p.dead:
                self.win = False
                self.reward = self.run_reward
                self.phase = "end"
                self.phase_t = 1e9
            else:
                self.run_reward += (70 if self.mini else 35) + self.wave * 6
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
            self.reward = 0 if self.net else (100 if self.boss else 30) * max(1, self.level // 2 + 1)
            if self.net or (self.boss and self.win):
                self.start_fatality()
            else:
                self.phase = "end"
                self.phase_t = 1e9
        else:
            self.round += 1
            self.reset_round()
            self.phase = "intro"
            self.phase_t = 1.6

    def start_fatality(self):
        self.phase = "fatality"
        self.phase_t = 1e9
        seq = [random.choice(FATALITY_KEYS) for _ in range(4)]
        self.fatality = {"seq": seq, "idx": 0, "t": FATALITY_WINDOW}
        self.pending_fat = []
        self.b.fatality_hide = False

    def fatality_feed(self, tokens):
        for tok in tokens:
            if tok in FATALITY_KEYS:
                self.pending_fat.append(tok)

    def finish_fatality(self, ok):
        self.fatality = None
        self.pending_fat = []
        if ok:
            self.fatality_done = True
            self.fatality_bonus = FATALITY_BONUS
            self.fatality_gems = FATALITY_GEMS
            self.reward += FATALITY_BONUS
            self.fat_style = self.p.h["style"]
            self.fat_anim_t = 0.0
            self.phase = "fatality_anim"
            self.phase_t = FATALITY_ANIM_T
            self.shake = 10
        else:
            self.phase = "end"
            self.phase_t = 1e9

    def fatality_anim_step(self, dt, t):
        foe = self.b
        fx, fy = foe.x, foe.y - 80 * foe.scale
        style = self.fat_style
        if t >= 0.9:
            foe.fatality_hide = True
        if style == "flame":
            if random.random() < dt * 70:
                self.parts.rise(fx + random.uniform(-34, 34), foe.y - random.uniform(0, 150) * foe.scale,
                                random.choice(("#ff5a1a", "#ff8c1a", "#ffd23f")))
            if random.random() < dt * 20:
                self.parts.spark(fx, fy)
        elif style == "hood":
            if random.random() < dt * 40:
                self.parts.rise(fx + random.uniform(-26, 26), foe.y - random.uniform(0, 120) * foe.scale,
                                random.choice(("#3fd97a", "#8aff8a", "#bfffd8")))
        elif style == "glow":
            if random.random() < dt * 30:
                self.parts.spark(fx + random.uniform(-40, 40), fy + random.uniform(-60, 60))
            if random.random() < dt * 8:
                self.parts.ring(fx, fy, "#fff2b0", 8, 90, 0.4)
        else:
            if t < 0.4 and random.random() < dt * 40:
                self.parts.gibs(fx, foe.y - 70 * foe.scale, 3)
            if random.random() < dt * 25:
                self.parts.blood(fx + random.uniform(-20, 20), foe.y - 60 * foe.scale, 2,
                                 random.choice((-1, 1)), big=True)
        self.shake = max(self.shake, 3)

    def apply_input(self, f, inp, foe):
        if f.dead or f.stun_t > 0:
            f.vx_target = 0.0
            f.crouch = False
            return
        f.crouch = inp["crouch"] and f.on_ground
        f.vx_target = inp["move"] * 330 * f.eff_speed() * (0.45 if f.crouch else 1.0)
        if inp["jump"] and f.on_ground and not f.crouch and f.can_jump():
            f.vy = -960.0
            f.on_ground = False
        if inp["attack"]:
            if f.crouch:
                f.try_strike("sweep", self)
            elif not f.on_ground:
                f.try_strike("air", self)
            else:
                f.start_attack(self)
        if inp.get("strike"):
            f.try_strike(inp["strike"], self)
        if inp.get("parry"):
            f.try_parry()
        if inp["cast"] is not None:
            self.cast_ability(f, inp["cast"], foe)
        if inp.get("special"):
            self.cast_special(f, inp["special"], foe)
        if inp.get("myth"):
            self.try_myth_ult(f, foe)
        if inp.get("rult"):
            if not self.try_myth_ult(f, foe):
                self.try_legend_ult(f, foe)

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
        if self.mirror:
            self.mirror_tick(dt)
            return
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
        if self.phase == "fatality":
            fat = self.fatality
            fat["t"] -= dt
            queue, self.pending_fat = self.pending_fat, []
            seq, idx = fat["seq"], fat["idx"]
            for tok in queue:
                if idx < len(seq) and tok == seq[idx]:
                    idx += 1
                    fat["idx"] = idx
                    self.parts.ring(self.p.x, self.p.y - 120 * self.p.scale, COL_GOLD, 10, 60, 0.3)
                    if idx >= len(seq):
                        self.finish_fatality(True)
                        break
                else:
                    fat["idx"] = 0
                    idx = 0
            if self.phase == "fatality" and fat["t"] <= 0:
                self.finish_fatality(False)
            self.p.anim_t += dt
            self.b.anim_t += dt
            return
        if self.phase == "fatality_anim":
            self.fatality_anim_step(dt, FATALITY_ANIM_T - self.phase_t)
            if self.phase_t <= 0:
                self.phase = "end"
                self.phase_t = 1e9
            return

        p, b = self.p, self.b
        if self.net:
            r = self.remote_inp
            self.remote_inp = None
            if r is not None:
                self.apply_input(b, r, p)
        else:
            self.ai.update(dt, p, self)
        self.apply_input(p, inp, b)
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

        for s in self.strikes[:]:
            s[1] -= dt
            if s[1] <= 0:
                self.strikes.remove(s)
                self.do_strike(s[0], s[2], s[3])

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

    def netfx(self, x, y, color):
        if self.net:
            self.net_events.append(("f", round(x, 1), round(y, 1), color))

    def snapshot(self):
        ev, self.net_events = self.net_events, []
        return {"t": "snap", "ph": self.phase,
                "pt": round(self.phase_t, 3) if self.phase_t < 1e8 else 1e9,
                "wp": self.wins_p, "wb": self.wins_b, "rnd": self.round,
                "shk": round(self.shake, 1), "cmb": self.combo_count,
                "win": self.win, "fd": self.fatality_done, "fb": self.fatality_bonus,
                "fst": self.fat_style, "p": _snap_fighter(self.p), "b": _snap_fighter(self.b),
                "ev": ev, "fat": dict(self.fatality) if self.fatality else None}

    def apply_snap(self, snap):
        prev = self.phase
        self.phase = snap.get("ph", prev)
        self.phase_t = snap.get("pt", 0.0)
        self.wins_p = snap.get("wp", 0)
        self.wins_b = snap.get("wb", 0)
        self.round = snap.get("rnd", 1)
        self.shake = max(self.shake, snap.get("shk", 0.0))
        self.combo_count = snap.get("cmb", 0)
        if self.combo_count >= 2:
            self.combo_show = 1.2
        self.win = not snap.get("win", False)
        self.fatality_done = snap.get("fd", False)
        self.fat_style = snap.get("fst", "plain")
        if self.fatality_done and not self.win:
            self.fatality_bonus = snap.get("fb", 0)
            self.fatality_gems = FATALITY_GEMS
            self.reward = self.fatality_bonus
        else:
            self.fatality_bonus = 0
            self.fatality_gems = 0
            self.reward = 0
        self.fatality = snap.get("fat")
        if self.phase == "fatality_anim" and prev != "fatality_anim":
            self.fat_anim_t = 0.0
            self.b.fatality_hide = False
        for key, f in (("p", self.p), ("b", self.b)):
            d = snap.get(key)
            if not d:
                continue
            if not f.synced:
                f.x = f.tx = d["x"]
                f.y = f.ty = d["y"]
                f.synced = True
            else:
                f.tx, f.ty = d["x"], d["y"]
            f.facing = d["fc"]
            f.crouch = d["cr"]
            f.on_ground = d["gr"]
            f.hp = d["hp"]
            f.max_hp = d["mhp"]
            f.disp_hp = d["dh"]
            f.dead = d["dd"]
            f.dead_t = d["dt"]
            f.attack_t = d["at"]
            f.attack_kind = d["ak"]
            f.stun_t = d["st"]
            f.hurt_t = d["ht"]
            f.hit_flash = d["hf"]
            f.energy = d["en"]
            f.buffs.update(d["bf"])
            f.combo = d["cb"]
            f.root_t = d["rt"]
            f.scythe_out = d["sc"]
            f.cds = list(d["cds"])
            f.sp_cds = dict(d["spcd"])
            f.strike_cds = dict(d["stcd"])
            f.parry_cd = d["pcd"]
            f.parry_t = d["pt"]
            f.injury = {"kind": d["inj"], "ability": d.get("inja", 0)} if d["inj"] else None
        for ev in snap.get("ev", ()):
            if ev[0] == "h":
                _, x, y, dmg, crit = ev
                self.parts.blood(x, y, 6 if crit else 4, self.p.facing, big=crit)
                self.parts.burst(x, y, "#ffd23f" if not crit else "#ff5a1a", 8, 220)
                self.parts.dmg_text(x, y - 60, dmg, big=crit)
            elif ev[0] == "f":
                _, x, y, color = ev
                self.parts.burst(x, y, color, 10, 240)
                self.parts.ring(x, y, color, 8, 54, 0.3)

    def mirror_tick(self, dt):
        snap = self.pending_snap
        if snap is not None:
            self.pending_snap = None
            self.apply_snap(snap)
        for f in (self.p, self.b):
            if f.synced:
                k = min(1.0, dt * 14)
                f.x += (f.tx - f.x) * k
                f.y += (f.ty - f.y) * k
                f.anim_t += dt
                if f.dead:
                    f.dead_t += dt
                f.disp_hp += (f.hp - f.disp_hp) * min(1.0, dt * 8)
        if self.phase == "fatality_anim":
            self.fatality_anim_step(dt, self.fat_anim_t)
            self.fat_anim_t += dt

    def register_hit(self, att, foe, base, heavy=False, kb_force=None, stun=0.0, force_crit=False,
                     pierce_guard=False, bleed=0.0):
        if foe.dead:
            return "miss", 0.0
        if force_crit:
            dmg = base * att.dmg_factor() * att.out_mult() * CRIT_MULT
            crit = True
        else:
            dmg, crit = att.roll_damage(base)
        if att.buffs["riposte"] > 0:
            dmg *= RIPOSTE_MULT
            att.buffs["riposte"] = 0.0
            self.parts.dmg_text(att.x, att.y - 215 * att.scale, 0, txt="\u041a\u041e\u041d\u0422\u0420\u0423\u0414\u0410\u0420",
                                color="#ffd23f")
        res = foe.take_damage(dmg, kb_dir=att.facing, stun=stun, kb_force=kb_force,
                              pierce_guard=pierce_guard)
        if res == "parry":
            if foe is self.p:
                self.stats["parries"] += 1
            att.stun_t = max(att.stun_t, PARRY_STUN)
            att.attack_t = 0.0
            foe.buffs["riposte"] = RIPOSTE_DUR
            foe.energy = min(100.0, foe.energy + 10.0)
            self.hitstop = max(self.hitstop, 0.14)
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
        if foe.buffs["thorns"] > 0 and att is not foe and abs(att.x - foe.x) < 230:
            ref = dmg * THORNS_PCT
            att.hp = max(0.0, att.hp - ref)
            att.hit_flash = 0.1
            self.parts.dmg_text(att.x, att.y - 190 * att.scale, ref, color="#ff8c1a")
            self.parts.burst(att.x, att.y - 95 * att.scale, "#ff5a1a", 8, 200)
        if bleed > 0 and not foe.dead:
            foe.bleed_t = 4.0
            foe.bleed_dps = bleed
            if att is self.p:
                self.stats["bleeds"] += 1
                self.parts.dmg_text(foe.x, foe.y - 210 * foe.scale, 0, txt="\u041a\u0420\u041e\u0412\u041e\u0422\u041e\u0427\u0415\u041d\u0418\u0415",
                                    color="#ff2a1a")
        if att is self.p:
            self.dmg_dealt += dmg
        if self.net:
            self.net_events.append(("h", round(foe.x, 1), round(foe.y - 100 * foe.scale, 1),
                                    round(dmg, 1), crit))
        self.parts.blood(foe.x, foe.y - 100 * foe.scale, 5 if crit else 3, att.facing, big=crit)
        if random.random() < (0.5 if crit else 0.3):
            self.parts.splat(foe.x, GROUND_Y, 3)
        self.roll_injury(att, foe, heavy or crit)
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
            self.max_combo = max(self.max_combo, self.combo_count)
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

    def strike_in_range(self, att, foe, rng, ytol=165):
        dx = (foe.x - att.x) * att.facing
        if dx < 0 or dx > rng:
            return False
        a_top = att.y - ytol * att.scale
        b0, b1 = foe.bbox()[1], foe.bbox()[3]
        return a_top <= b1 and att.y >= b0 - 50

    def do_strike(self, att, kind, stage=0):
        foe = self.foe_of(att)
        if foe.dead or att.dead:
            return
        if att is self.p:
            self.stats["strikes"] += 1
        if kind == "kick":
            rng = MELEE_RANGE * 1.15 * att.scale
            if self.strike_in_range(att, foe, rng):
                self.register_hit(att, foe, random.uniform(10, 15) * COMBO_MULT[min(stage, 2)],
                                  kb_force=560, pierce_guard=True)
                self.parts.ring(foe.x, foe.y - 90 * foe.scale, att.h["accent"], 8, 44, 0.25)
        elif kind == "upper":
            rng = MELEE_RANGE * 0.9 * att.scale
            if self.strike_in_range(att, foe, rng):
                res, dmg = self.register_hit(att, foe, random.uniform(14, 20) * COMBO_MULT[min(stage, 2)],
                                             kb_force=200, force_crit=True, pierce_guard=True)
                if res == "hit":
                    foe.vy = -760.0
                    foe.on_ground = False
                self.parts.ring(foe.x, foe.y - 120 * foe.scale, "#ffd23f", 8, 60, 0.3)
                self.shake = max(self.shake, 8)
        elif kind == "sweep":
            rng = MELEE_RANGE * 1.05 * att.scale
            if self.strike_in_range(att, foe, rng, ytol=90):
                res, dmg = self.register_hit(att, foe, random.uniform(8, 12) * COMBO_MULT[min(stage, 2)],
                                             kb_force=140)
                if res == "hit":
                    foe.root_t = max(foe.root_t, 0.6)
                    self.parts.dmg_text(foe.x, foe.y - 200 * foe.scale, 0, txt="ПОДСЕЧКА",
                                        color=att.h["accent"])
        elif kind == "air":
            if self.strike_in_range(att, foe, 130 * att.scale, ytol=260):
                self.register_hit(att, foe, random.uniform(9, 14) * COMBO_MULT[min(stage, 2)],
                                  kb_force=380)
        else:
            if self.strike_in_range(att, foe, 170 * att.scale, ytol=260):
                self.register_hit(att, foe, random.uniform(11, 16) * COMBO_MULT[min(stage, 2)],
                                  heavy=True, kb_force=420)
                self.shake = max(self.shake, 9)

    def roll_injury(self, att, foe, big):
        if foe.injury is not None or foe.dead:
            return
        chance = INJURY_CHANCE * (1.6 if big else 1.0)
        if random.random() >= chance:
            return
        kind = random.choice(("str", "spd", "jump", "ability"))
        ab_idx = random.randrange(len(foe.h["abilities"])) if kind == "ability" else None
        foe.injury = {"kind": kind, "ability": ab_idx}
        if foe is self.p:
            self.stats["injuries"] += 1
        txt = {"str": "ТРАВМА: РУКА", "spd": "ТРАВМА: НОГА",
               "jump": "ТРАВМА: КОЛЕНО", "ability": "ТРАВМА: СПОСОБНОСТЬ"}[kind]
        self.parts.dmg_text(foe.x, foe.y - 220 * foe.scale, 0, txt=txt, color=COL_BLOOD, big=True)
        self.parts.blood(foe.x, foe.y - 100 * foe.scale, 8, att.facing, big=True)
        self.parts.bone(foe.x, foe.y - 100 * foe.scale)
        self.parts.splat(foe.x, GROUND_Y, 8)
        self.shake = max(self.shake, 8)

    def myth_ready(self, f, foe):
        abilities = f.h["abilities"]
        if len(abilities) < 4 or abilities[3]["kind"] != "myth_ult":
            return False
        return (f.cds[0] <= 0 and f.cds[3] <= 0 and f.energy >= MYTH_ENERGY
                and f.ult_charge >= ULT_CHARGE_MAX
                and not foe.dead and foe.buffs["soul"] <= 0
                and foe.hp / foe.max_hp <= MYTH_FOE_HP)

    def legend_ready(self, f, foe):
        abilities = f.h["abilities"]
        if len(abilities) < 5 or abilities[4]["kind"] != "legend_ult":
            return False
        return (f.cds[4] <= 0 and f.energy >= 100.0 and f.ult_charge >= ULT_CHARGE_MAX
                and not foe.dead and foe.buffs["soul"] <= 0
                and foe.hp / foe.max_hp <= LEGEND_FOE_HP)

    def try_legend_ult(self, f, foe):
        if f.dead or f.stun_t > 0 or self.phase != "fight":
            return False
        if not self.legend_ready(f, foe):
            return False
        ab = f.h["abilities"][4]
        f.cds[4] = ab["cd"]
        f.energy = 0.0
        f.ult_charge = 0.0
        self.fx.append({"kind": "legend_" + f.key.lower(), "owner": f, "foe": foe,
                        "t": 2.6, "hit_t": 1.6, "applied": False, "dmg": ab.get("dmg", 80),
                        "x": foe.x, "y": foe.y - 90 * foe.scale})
        if f is self.p:
            self.stats["legend_ults"] += 1
        self.netfx(f.x, f.y - 90 * f.scale, "#ffc400")
        self.shake = max(self.shake, 12)
        self.parts.ring(f.x, f.y - 90 * f.scale, "#ffc400", 18, 160, 0.6)
        self.parts.burst(f.x, f.y - 90 * f.scale, "#ffd23f", 26, 340)
        return True

    def try_myth_ult(self, f, foe):
        if f.dead or f.stun_t > 0 or self.phase != "fight":
            return False
        if not self.myth_ready(f, foe):
            return False
        abilities = f.h["abilities"]
        ab = abilities[3]
        f.cds[0] = abilities[0]["cd"]
        f.cds[3] = ab["cd"]
        f.energy -= MYTH_ENERGY
        self.fx.append({"kind": "myth_" + f.key.lower(), "owner": f, "foe": foe,
                        "t": 2.2, "hit_t": 1.4, "applied": False, "dmg": ab.get("dmg", 65),
                        "x": foe.x, "y": foe.y - 90 * foe.scale})
        if f is self.p:
            self.stats["myth_ults"] += 1
        self.netfx(f.x, f.y - 90 * f.scale, "#ff2a8a")
        self.shake = max(self.shake, 10)
        self.parts.ring(f.x, f.y - 90 * f.scale, "#ff2a8a", 16, 130, 0.5)
        self.parts.burst(f.x, f.y - 90 * f.scale, "#ff2a8a", 20, 300)
        return True

    def cast_ability(self, f, idx, foe):
        if f.dead or f.stun_t > 0 or self.phase != "fight":
            return False
        abilities = f.h["abilities"]
        if idx < 0 or idx >= len(abilities) or f.cds[idx] > 0:
            return False
        if f.injury and f.injury["kind"] == "ability" and f.injury["ability"] == idx:
            self.parts.dmg_text(f.x, f.y - 220 * f.scale, 0, txt="ТРАВМА", color=COL_BLOOD)
            return False
        ab = abilities[idx]
        if ab["kind"] in ("myth_ult", "legend_ult"):
            return False
        if ab["kind"] == "scythe" and f.scythe_out:
            return False
        if not self.exec_kind(f, ab, foe):
            return False
        f.cds[idx] = ab["cd"]
        if f is self.p:
            self.stats["casts"] += 1
        self.netfx(f.x, f.y - 90 * f.scale, f.h["glow"])
        return True

    def cast_special(self, f, combo, foe):
        if f.dead or f.stun_t > 0 or self.phase != "fight":
            return False
        if f.special_cd > 0:
            return False
        sp = next((s for s in f.h.get("specials", []) if s["combo"] == combo), None)
        if sp is None or f.energy < sp["cost"]:
            return False
        if f.sp_cds.get(combo, 0.0) > 0:
            return False
        if not self.exec_kind(f, sp, foe):
            return False
        f.energy -= sp["cost"]
        f.special_cd = 1.0
        f.sp_cds[combo] = sp.get("cd", 8.0)
        if f is self.p:
            self.stats["specials"] += 1
            self.stats["casts"] += 1
        self.netfx(f.x, f.y - 90 * f.scale, f.h["accent"])
        self.parts.ring(f.x, f.y - 90 * f.scale, "#ffd23f", 14, 92, 0.35)
        self.parts.burst(f.x, f.y - 90 * f.scale, f.h["accent"], 12, 220)
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
        elif k == "geyser":
            self.fx.append({"kind": "geyser_warn", "x": foe.x, "owner": f,
                            "t": ab.get("warn", 0.7), "dmg": ab.get("dmg", 14),
                            "color": f.h["glow"]})
        elif k == "vortex":
            dur = ab.get("dur", 1.6)
            self.fx.append({"kind": "vortex", "owner": f, "foe": foe, "t": dur,
                            "tick_t": 0.35, "dmg": ab.get("dmg", 5),
                            "style": ab.get("style", "water"),
                            "x": foe.x, "y": foe.y - 90 * foe.scale})
            foe.root_t = max(foe.root_t, dur)
            self.shake = max(self.shake, 5)
        elif k == "tide":
            self.proj.append({"kind": "tide", "owner": f,
                              "x": f.x + f.facing * 50 * f.scale, "y": GROUND_Y - 60,
                              "vx": ab.get("speed", 380) * f.facing, "vy": 0.0,
                              "dmg": ab.get("dmg", 20), "r": ab.get("r", 40),
                              "color": f.h["accent"]})
            self.shake = max(self.shake, 4)
        elif k == "curse":
            if foe.dead or foe.buffs["soul"] > 0:
                return False
            foe.buffs["curse"] = ab.get("dur", 5.0)
            self.fx.append({"kind": "cursefx", "owner": f, "foe": foe, "t": 0.6,
                            "x": foe.x, "y": foe.y - 90 * foe.scale})
            self.parts.burst(foe.x, foe.y - 90 * foe.scale, "#b06aff", 16, 220)
            self.parts.dmg_text(foe.x, foe.y - 195 * foe.scale, 0,
                                txt="\u041f\u0420\u041e\u041a\u041b\u042f\u0422\u042c\u0415", color="#b06aff")
        elif k == "thorns":
            f.buffs["thorns"] = ab.get("dur", 4.0)
            self.parts.burst(f.x, f.y - 90 * f.scale, "#ff8c1a", 16, 220)
            self.parts.ring(f.x, f.y - 90 * f.scale, "#ff5a1a", 10, 74, 0.45)
        elif k == "aoe":
            if f is self.p:
                self.stats["aoes"] += 1
            self.fx.append({"kind": "aoefx", "owner": f, "t": 0.5, "hit_t": 0.2, "applied": False,
                            "x": f.x, "y": f.y - 90 * f.scale,
                            "r": ab.get("radius", 175), "dmg": ab.get("dmg", 20)})
        elif k == "roar":
            if f is self.p:
                self.stats["roars"] += 1
            rng = ab.get("range", 340)
            self.fx.append({"kind": "roarfx", "owner": f, "t": 0.45, "x0": f.x,
                            "y0": f.y - 95 * f.scale, "range": rng, "dir": f.facing})
            if not foe.dead and foe.buffs["soul"] <= 0:
                dx = (foe.x - f.x) * f.facing
                if 0 <= dx <= rng and abs(foe.y - f.y) < 200:
                    res, _d = self.register_hit(f, foe, ab.get("dmg", 14))
                    if res == "hit":
                        foe.vy = -420.0
                        foe.on_ground = False
        elif k == "meteor":
            self.fx.append({"kind": "meteor_warn", "x": foe.x, "owner": f, "t": ab.get("warn", 0.95),
                            "dmg": ab.get("dmg", 28), "radius": ab.get("radius", 120),
                            "color": f.h["glow"]})
        elif k == "chains":
            if f is self.p:
                self.stats["chains"] += 1
            rng = ab.get("range", 460)
            dur = ab.get("dur", 0.9)
            if foe.dead or foe.buffs["soul"] > 0 or abs(foe.x - f.x) > rng:
                return False
            self.register_hit(f, foe, ab.get("dmg", 18), kb_force=0)
            foe.root_t = max(foe.root_t, dur)
            fx = {"kind": "chainsfx", "owner": f, "foe": foe, "t": dur, "x": foe.x}
            self.fx.append(fx)
        elif k == "saws":
            if f is self.p:
                self.stats["saws"] += 1
            self.fx.append({"kind": "saws", "owner": f, "t": ab.get("dur", 1.6),
                            "dmg": ab.get("dmg", 16), "left": float(WALL + 10),
                            "right": float(W - WALL - 10), "hit_cd": 0.0})
            self.shake = max(self.shake, 5)
        elif k == "haze":
            if foe.dead:
                return False
            if f is self.p:
                self.stats["haze"] += 1
            self.fx.append({"kind": "hazefx", "owner": f, "foe": foe, "t": 1.0, "applied": False,
                            "x": foe.x, "y": foe.y - 90 * foe.scale})
        elif k == "ult":
            if f.ult_charge < ULT_CHARGE_MAX:
                return False
            rng = ab.get("range", 200)
            if foe.dead or foe.buffs["soul"] > 0:
                return False
            frac = foe.hp / foe.max_hp
            dx = (foe.x - f.x) * f.facing
            if frac >= ULT_HP or not (0 <= dx <= rng) or abs(foe.y - f.y) > ULT_RANGE_Y:
                return False
            f.ult_charge = 0.0
            foe.root_t = max(foe.root_t, 1.4)
            foe.stun_t = max(foe.stun_t, 1.4)
            self.fx.append({"kind": "ult_" + f.key.lower(), "owner": f, "foe": foe,
                            "t": 1.9, "hit_t": 1.2, "applied": False,
                            "x": foe.x, "y": foe.y - 90 * foe.scale})
            if f is self.p:
                self.stats["ults"] += 1
            self.shake = max(self.shake, 6)
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
            if k == "vortex":
                fx["t"] -= dt
                fx["tick_t"] -= dt
                f = fx["owner"]
                foe = fx["foe"]
                fx["x"] += (foe.x - fx["x"]) * min(1.0, dt * 8)
                fx["y"] = foe.y - 90 * foe.scale
                if not foe.dead and foe.buffs["soul"] <= 0:
                    foe.kvx += (1 if fx["x"] > foe.x else -1) * 900 * dt
                if fx["tick_t"] <= 0:
                    fx["tick_t"] = 0.4
                    if not foe.dead and foe.buffs["soul"] <= 0:
                        self.register_hit(f, foe, fx["dmg"], kb_force=0)
                if fx["t"] <= 0 or foe.dead:
                    self.fx.remove(fx)
                continue
            if k.startswith("myth_"):
                fx["t"] -= dt
                fx["hit_t"] -= dt
                foe = fx["foe"]
                fx["x"] = foe.x
                fx["y"] = foe.y - 90 * foe.scale
                if fx["hit_t"] <= 0 and not fx["applied"]:
                    fx["applied"] = True
                    if not foe.dead and foe.buffs["soul"] <= 0:
                        dmg, crit = fx["owner"].roll_damage(fx["dmg"])
                        foe.take_damage(dmg, kb_dir=fx["owner"].facing, stun=1.5,
                                        kb_force=460, pierce_guard=True)
                        foe.root_t = max(foe.root_t, 1.5)
                        self.parts.burst(foe.x, foe.y - 90 * foe.scale, fx["owner"].h["glow"], 30, 380)
                        self.parts.blood(foe.x, foe.y - 100 * foe.scale, 10, fx["owner"].facing, big=True)
                        self.parts.dmg_text(foe.x, foe.y - 205 * foe.scale, dmg, color="#ff2a8a", big=True)
                        self.shake = max(self.shake, 14)
                        self.hitstop = max(self.hitstop, 0.18)
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k.startswith("ult_"):
                fx["t"] -= dt
                fx["hit_t"] -= dt
                foe = fx["foe"]
                fx["x"] = foe.x
                fx["y"] = foe.y - 90 * foe.scale
                if fx["hit_t"] <= 0 and not fx["applied"]:
                    fx["applied"] = True
                    if not foe.dead and foe.buffs["soul"] <= 0:
                        if foe.hp / foe.max_hp <= ULT_QUALITY:
                            foe.hp = 0.0
                            self.quality_finish += 1
                            self.parts.dmg_text(foe.x, foe.y - 200 * foe.scale, 0,
                                                txt="ДОБИВАНИЕ!", color=COL_GOLD, big=True)
                            self.parts.burst(foe.x, foe.y - 90 * foe.scale, fx["owner"].h["glow"], 26, 340)
                            self.shake = max(self.shake, 12)
                            self.hitstop = max(self.hitstop, 0.2)
                        else:
                            foe.hp = min(foe.hp, ULT_LEFT)
                            self.parts.burst(foe.x, foe.y - 90 * foe.scale, fx["owner"].h["accent"], 18, 280)
                            self.shake = max(self.shake, 9)
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k == "hazefx":
                fx["t"] -= dt
                foe = fx["foe"]
                fx["x"] = foe.x
                fx["y"] = foe.y - 90 * foe.scale
                if not fx["applied"] and fx["t"] <= 0.4:
                    fx["applied"] = True
                    if not foe.dead and foe.buffs["soul"] <= 0:
                        ab0 = foe.h["abilities"][0]
                        if ab0["kind"] in HAZE_SELF_KINDS:
                            self.exec_kind(foe, ab0, foe)
                        else:
                            self.register_hit(foe, foe, 12)
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k == "chainsfx":
                fx["t"] -= dt
                f, foe = fx["owner"], fx["foe"]
                fx["x"] = foe.x
                if not foe.dead and foe.buffs["soul"] <= 0:
                    foe.root_t = max(foe.root_t, 0.25)
                    foe.kvx += (1 if f.x > foe.x else -1) * 2600 * dt
                if fx["t"] <= 0 or foe.dead:
                    self.fx.remove(fx)
                continue
            if k == "saws":
                fx["t"] -= dt
                fx["hit_cd"] = max(0.0, fx["hit_cd"] - dt)
                spd = 300
                fx["left"] += spd * dt
                fx["right"] -= spd * dt
                if fx["hit_cd"] <= 0:
                    for target in (self.p, self.b):
                        if target.dead or target.buffs["soul"] > 0:
                            continue
                        if target.y > GROUND_Y - 100 and min(abs(target.x - fx["left"]),
                                                             abs(target.x - fx["right"])) < 48:
                            res, _d = self.register_hit(fx["owner"], target, fx["dmg"])
                            if res == "hit":
                                target.bleed_t = 4.0
                                target.bleed_dps = max(2.0, target.max_hp * 0.025)
                                self.parts.splat(target.x, GROUND_Y, 5)
                            fx["hit_cd"] = 0.5
                            break
                if random.random() < dt * 30:
                    self.parts.spark(random.choice((fx["left"], fx["right"])), GROUND_Y - 20)
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k == "aoefx":
                fx["t"] -= dt
                fx["hit_t"] -= dt
                f = fx["owner"]
                if fx["hit_t"] <= 0 and not fx["applied"]:
                    fx["applied"] = True
                    for target in (self.p, self.b):
                        if target.dead or target.buffs["soul"] > 0:
                            continue
                        if abs(target.x - fx["x"]) <= fx["r"] and abs(target.y - fx["y"]) < 230:
                            res, _d = self.register_hit(f, target, fx["dmg"])
                            if res == "hit" and target is not f:
                                target.kvx += (1 if target.x >= f.x else -1) * 420
                    self.parts.ring(fx["x"], fx["y"], "#ff8c1a", 10, fx["r"], 0.45)
                    self.parts.burst(fx["x"], fx["y"], "#ff5a1a", 24, 320)
                    self.shake = max(self.shake, 9)
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k == "cursefx":
                fx["t"] -= dt
                fx["x"] = fx["foe"].x
                fx["y"] = fx["foe"].y - 90 * fx["foe"].scale
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            if k.startswith("legend_"):
                fx["t"] -= dt
                fx["hit_t"] -= dt
                foe = fx["foe"]
                fx["x"] = foe.x
                fx["y"] = foe.y - 90 * foe.scale
                if fx["hit_t"] <= 0 and not fx["applied"]:
                    fx["applied"] = True
                    if not foe.dead and foe.buffs["soul"] <= 0:
                        dmg, _c = fx["owner"].roll_damage(fx["dmg"])
                        foe.take_damage(dmg, kb_dir=fx["owner"].facing, stun=2.0,
                                        kb_force=520, pierce_guard=True)
                        foe.root_t = max(foe.root_t, 1.8)
                        if foe.hp / foe.max_hp <= ULT_QUALITY:
                            foe.hp = 0.0
                            self.quality_finish += 1
                            self.parts.dmg_text(foe.x, foe.y - 200 * foe.scale, 0,
                                                txt="\u0414\u041e\u0411\u0418\u0412\u0410\u041d\u0418\u0415!",
                                                color=COL_GOLD, big=True)
                        self.parts.burst(foe.x, foe.y - 90 * foe.scale, "#ffd23f", 34, 420)
                        self.parts.blood(foe.x, foe.y - 100 * foe.scale, 12, fx["owner"].facing, big=True)
                        self.parts.dmg_text(foe.x, foe.y - 215 * foe.scale, dmg, color="#ffc400", big=True)
                        self.shake = max(self.shake, 16)
                        self.hitstop = max(self.hitstop, 0.22)
                if fx["t"] <= 0:
                    self.fx.remove(fx)
                continue
            fx["t"] -= dt
            if fx["t"] > 0:
                continue
            if k == "meteor_warn":
                foe = self.foe_of(fx["owner"])
                if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - fx["x"]) < fx.get("radius", 120):
                    safe = foe.y <= GROUND_Y - 110
                    if not safe:
                        self.register_hit(fx["owner"], foe, fx["dmg"], heavy=True, kb_force=380)
                        self.parts.burst(fx["x"], GROUND_Y - 70, fx.get("color", "#ff8c1a"), 24, 320)
                        self.parts.splat(foe.x, GROUND_Y, 4)
                        self.shake = max(self.shake, 10)
                fx["kind"] = "meteor"
                fx["t"] = 0.5
            elif k == "hand_warn":
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
            elif k == "geyser_warn":
                foe = self.foe_of(fx["owner"])
                if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - fx["x"]) < 62 \
                        and foe.y > GROUND_Y - 70:
                    self.register_hit(fx["owner"], foe, fx["dmg"], kb_force=0)
                    foe.vy = -780.0
                    foe.on_ground = False
                    self.parts.burst(fx["x"], GROUND_Y - 60, fx.get("color", "#4ac9ff"), 20, 300)
                    self.shake = max(self.shake, 8)
                fx["kind"] = "geyser"
                fx["t"] = 0.5
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
            elif k == "geyser_warn":
                col = fx.get("color", "#4ac9ff")
                r = 26 + 6 * math.sin(now * 12)
                cv.create_oval(fx["x"] - r + ox, GROUND_Y - r * 0.5 + oy, fx["x"] + r + ox, GROUND_Y + r * 0.5 + oy,
                               outline=col, width=3, tags=("dyn",))
                cv.create_line(fx["x"] + ox, GROUND_Y - 240 + oy, fx["x"] + ox, GROUND_Y + oy,
                               fill=col, width=2, dash=(4, 8), tags=("dyn",))
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
            elif k == "geyser":
                col = fx.get("color", "#4ac9ff")
                p = 1 - fx["t"] / 0.5
                hgt = 260 * min(1.0, p * 4) * (1.0 if fx["t"] > 0.15 else fx["t"] / 0.15)
                w = 30 * (1.0 if fx["t"] > 0.15 else fx["t"] / 0.15 + 0.2)
                cv.create_rectangle(fx["x"] - w + ox, GROUND_Y - hgt + oy,
                                    fx["x"] + w + ox, GROUND_Y + oy,
                                    fill=col, stipple="gray50", outline="", tags=("dyn",))
                cv.create_rectangle(fx["x"] - w * 0.4 + ox, GROUND_Y - hgt + oy,
                                    fx["x"] + w * 0.4 + ox, GROUND_Y + oy,
                                    fill="#ffffff", stipple="gray25", outline="", tags=("dyn",))
            elif k == "vortex":
                col = "#3fa9ff" if fx.get("style", "water") == "water" else "#9a5cff"
                x, y = fx["x"] + ox, fx["y"] + oy
                for i in range(6):
                    a = now * 10 + i * 1.047
                    rr = 18 + 9 * i
                    cv.create_line(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.5,
                                   x + math.cos(a + 1.4) * rr * 0.7, y + math.sin(a + 1.4) * rr * 0.35,
                                   fill=col, width=3, tags=("dyn",))
                cv.create_oval(x - 14, y - 8, x + 14, y + 8, fill=col, stipple="gray50",
                               outline="", tags=("dyn",))
            elif k == "hazefx":
                x, y = fx["x"] + ox, fx["y"] + oy
                for i in range(5):
                    rr = 30 + i * 14
                    a = now * 3 + i
                    cv.create_oval(x + math.cos(a) * rr - 26, y + math.sin(a) * rr * 0.4 - 18,
                                   x + math.cos(a) * rr + 26, y + math.sin(a) * rr * 0.4 + 18,
                                   fill="#6a4a8a", stipple="gray50", outline="", tags=("dyn",))
                cv.create_text(x, y - 90, text="\u041f\u041e\u041c\u0423\u0422\u041d\u0415\u041d\u0418\u0415",
                               fill="#b06aff", font=F_SMALL, tags=("dyn",))
            elif k == "chainsfx":
                f, foe = fx["owner"], fx["foe"]
                x0, y0 = f.x + f.facing * 30 * f.scale + ox, GROUND_Y - 30 + oy
                x1, y1 = fx["x"] + ox, GROUND_Y - 30 + oy
                cv.create_line(x0, y0, x1, y1, fill="#8a8570", width=4, tags=("dyn",))
                n = max(2, int(abs(x1 - x0) / 26))
                for i in range(1, n):
                    px = x0 + (x1 - x0) * i / n
                    py = y0 + math.sin(now * 14 + i) * 4
                    cv.create_oval(px - 5, py - 5, px + 5, py + 5, outline="#d7dee6",
                                   width=2, tags=("dyn",))
            elif k == "saws":
                for sx in (fx["left"], fx["right"]):
                    x, y = sx + ox, GROUND_Y - 26 + oy
                    cv.create_oval(x - 26, y - 26, x + 26, y + 26, fill="#9aa4ae",
                                   outline="#5a646e", width=3, tags=("dyn",))
                    for i in range(8):
                        a = now * 16 + i * 0.785
                        cv.create_line(x + math.cos(a) * 26, y + math.sin(a) * 26,
                                       x + math.cos(a) * 38, y + math.sin(a) * 38,
                                       fill="#d7dee6", width=3, tags=("dyn",))
                    cv.create_oval(x - 6, y - 6, x + 6, y + 6, fill="#3a424a", outline="", tags=("dyn",))
            elif k == "aoefx":
                x, y = fx["x"] + ox, fx["y"] + oy
                p = 1 - fx["t"] / 0.5
                r = fx["r"] * min(1.0, p * 2)
                cv.create_oval(x - r, y - r * 0.7, x + r, y + r * 0.7,
                               fill="#ff8c1a", stipple="gray25", outline="#ffd23f", width=3, tags=("dyn",))
            elif k == "cursefx":
                x, y = fx["x"] + ox, fx["y"] + oy
                for i in range(4):
                    a = now * 8 + i * 1.571
                    rr = 20 + 8 * i
                    cv.create_oval(x + math.cos(a) * rr - 6, y + math.sin(a) * rr * 0.6 - 6,
                                   x + math.cos(a) * rr + 6, y + math.sin(a) * rr * 0.6 + 6,
                                   outline="#b06aff", width=2, tags=("dyn",))
            elif k == "roarfx":
                f = fx["owner"]
                x0, y0 = fx["x0"] + ox, fx["y0"] + oy
                p = 1 - fx["t"] / 0.45
                for i in range(3):
                    rr = (46 + i * 34) * (0.3 + p)
                    a0 = -40 if fx["dir"] > 0 else 140
                    cv.create_arc(x0 - rr, y0 - rr, x0 + rr, y0 + rr, start=a0, extent=80,
                                  style="arc", outline=f.h["glow"], width=4 - i, tags=("dyn",),
                                  stipple="gray50" if i else "")
            elif k == "meteor_warn":
                col = fx.get("color", "#ff8c1a")
                r = fx.get("radius", 120) + 6 * math.sin(now * 14)
                cv.create_oval(fx["x"] - r + ox, GROUND_Y - r * 0.45 + oy,
                               fx["x"] + r + ox, GROUND_Y + r * 0.45 + oy,
                               outline=col, width=3, tags=("dyn",))
                cv.create_line(fx["x"] + ox, 0, fx["x"] + ox, GROUND_Y, fill=col, width=2,
                               dash=(4, 8), tags=("dyn",))
            elif k == "meteor":
                p = 1 - fx["t"] / 0.5
                x = fx["x"] + ox
                y = GROUND_Y - (1 - p) * 520 + oy
                cv.create_oval(x - 30, y - 30, x + 30, y + 30, fill="#ff5a1a",
                               outline="#ffd23f", width=3, tags=("dyn",))
                cv.create_oval(x - 14, y - 14, x + 14, y + 14, fill="#ffd23f", outline="", tags=("dyn",))
                cv.create_line(x + 18, y - 40, x + 4, y - 6, fill="#ff8c1a", width=6,
                               tags=("dyn",), stipple="gray50")
            elif k.startswith("legend_"):
                f, foe = fx["owner"], fx["foe"]
                x, y = fx["x"] + ox, fx["y"] + oy
                p = 1 - fx["t"] / 2.6
                if k == "legend_kingly":
                    for i in range(14):
                        a = now * 10 + i * 0.449
                        rr = 36 + 13 * i * (0.4 + 0.6 * p)
                        cv.create_line(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.55,
                                       x + math.cos(a + 0.8) * rr * 0.7, y + math.sin(a + 0.8) * rr * 0.4,
                                       fill="#ffd23f" if i % 2 else "#fff2b0", width=3, tags=("dyn",))
                    cv.create_polygon(x - 40, y - 46, x - 20, y - 84, x, y - 50, x + 20, y - 84,
                                      x + 40, y - 46, fill="#ffd23f", outline="#a1700a",
                                      width=2, tags=("dyn",))
                elif k == "legend_diviny":
                    hgt = 400 * min(1.0, p * 2.4)
                    cv.create_rectangle(x - 52 + ox, GROUND_Y - hgt + oy, x + 52 + ox, GROUND_Y + oy,
                                        fill="#fff2b0", stipple="gray25", outline="", tags=("dyn",))
                    cv.create_rectangle(x - 22 + ox, GROUND_Y - hgt + oy, x + 22 + ox, GROUND_Y + oy,
                                        fill="#ffffff", outline="", tags=("dyn",))
                    for i in range(4):
                        mx = x + (-1) ** i * (70 + i * 26)
                        cv.create_line(mx, 0, mx, GROUND_Y, fill="#ffd23f", width=2,
                                       dash=(3, 9), tags=("dyn",))
                elif k == "legend_colossy":
                    for i in range(6):
                        sx = x + (i - 2.5) * 52
                        hgt = (200 + 40 * (i % 3)) * min(1.0, p * 3)
                        cv.create_polygon(sx - 18, GROUND_Y + oy, sx, GROUND_Y - hgt + oy,
                                          sx + 18, GROUND_Y + oy, fill="#8a4a20",
                                          outline="#ffd23f", width=2, tags=("dyn",))
                    cv.create_oval(x - 90, y - 40, x + 90, y + 40, outline="#ff8c1a",
                                   width=4, tags=("dyn",))
                elif k == "legend_voidy":
                    rr = 90 * (1 - p * 0.7)
                    cv.create_oval(x - rr, y - rr, x + rr, y + rr, fill="#0a0410",
                                   outline="#9a5cff", width=4, tags=("dyn",))
                    for i in range(10):
                        a = now * 12 + i * 0.628
                        cv.create_line(x + math.cos(a) * 130, y + math.sin(a) * 90,
                                       x + math.cos(a) * rr, y + math.sin(a) * rr,
                                       fill="#9a5cff" if i % 2 else "#5a2ea6", width=3, tags=("dyn",))
                elif k == "legend_stormy":
                    for i in range(6):
                        bx = x + (i - 2.5) * 58
                        pts = [bx, 0]
                        for s in range(1, 5):
                            pts += [bx + (s % 2 * 2 - 1) * 22, GROUND_Y * s / 4]
                        pts += [bx, GROUND_Y]
                        cv.create_line(*pts, fill="#fff7b0" if i % 2 else "#ffd23f",
                                       width=4, tags=("dyn",), stipple="gray50")
                    cv.create_oval(x - 60, y - 30, x + 60, y + 30, outline="#ffd23f",
                                   width=3, tags=("dyn",))
                else:
                    r = 80 + 40 * math.sin(now * 10)
                    cv.create_oval(x - r, y - r * 0.7, x + r, y + r * 0.7,
                                   outline="#ffc400", width=5, tags=("dyn",))
                    for i in range(4):
                        a = now * 14 + i * 1.571
                        cv.create_line(x + math.cos(a) * r, y + math.sin(a) * r * 0.7,
                                       x - math.cos(a) * r, y - math.sin(a) * r * 0.7,
                                       fill="#ffd23f", width=3, tags=("dyn",))
            elif k.startswith("myth_"):
                f = fx["owner"]
                x, y = fx["x"] + ox, fx["y"] + oy
                p = 1 - fx["t"] / 2.2
                if k == "myth_necromancery":
                    for i in range(12):
                        a = now * 9 + i * 0.524
                        rr = 40 + 16 * i * (0.4 + 0.6 * p)
                        cv.create_line(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.55,
                                       x + math.cos(a + 0.9) * rr * 0.7, y + math.sin(a + 0.9) * rr * 0.4,
                                       fill="#8aff8a" if i % 2 else "#4ad16a", width=3, tags=("dyn",))
                    cv.create_oval(x - 46, y - 26, x + 46, y + 26, outline="#baff4a", width=3, tags=("dyn",))
                elif k == "myth_chaosy":
                    for i in range(9):
                        a = now * 13 + i * 0.698
                        rr = 30 + 20 * (i % 4) + 60 * p
                        cv.create_line(x + math.cos(a) * rr, y - rr * 0.8,
                                       x - math.cos(a) * rr * 0.6, y + rr * 0.5,
                                       fill="#e04aff" if i % 2 else "#ff8adf", width=4, tags=("dyn",))
                    cv.create_oval(x - 38, y - 38, x + 38, y + 38, outline="#ff9aff", width=3, tags=("dyn",))
                elif k == "myth_titany":
                    hgt = 320 * min(1.0, p * 3)
                    cv.create_rectangle(x - 44 + ox, GROUND_Y - hgt + oy, x + 44 + ox, GROUND_Y + oy,
                                        fill="#ffd23f", stipple="gray50", outline="", tags=("dyn",))
                    cv.create_rectangle(x - 18 + ox, GROUND_Y - hgt + oy, x + 18 + ox, GROUND_Y + oy,
                                        fill="#ffffff", stipple="gray25", outline="", tags=("dyn",))
                    cv.create_oval(x - 60, y - 30, x + 60, y + 30, outline="#ffcf6a", width=4, tags=("dyn",))
                elif k == "myth_devily":
                    for i in range(10):
                        a = now * 11 + i * 0.628
                        rr = 34 + 12 * i * (0.4 + 0.6 * p)
                        cv.create_polygon(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.6 - 20,
                                          x + math.cos(a + 0.5) * rr * 0.6, y + math.sin(a + 0.5) * rr * 0.4,
                                          x + math.cos(a + 1.0) * rr * 0.5, y + math.sin(a + 1.0) * rr * 0.7,
                                          fill="#ff2a1a" if i % 2 else "#ff8c1a", outline="", tags=("dyn",))
                    cv.create_oval(x - 44, y - 30, x + 44, y + 30, outline="#ffd23f", width=3, tags=("dyn",))
                else:
                    r = 60 + 40 * math.sin(now * 10)
                    cv.create_oval(x - r, y - r * 0.7, x + r, y + r * 0.7,
                                   outline=f.h["glow"], width=4, tags=("dyn",))
            elif k.startswith("ult_"):
                f, foe = fx["owner"], fx["foe"]
                x, y = foe.x + ox, foe.y - 90 * foe.scale + oy
                p = 1 - fx["t"] / 1.9
                if k == "ult_vawyy":
                    for i in range(8):
                        a = now * 12 + i * 0.785
                        rr = 30 + 11 * i * (0.55 + 0.45 * p)
                        cv.create_line(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.55,
                                       x + math.cos(a + 1.6) * rr * 0.65, y + math.sin(a + 1.6) * rr * 0.36,
                                       fill="#3fa9ff" if i % 2 else "#bfe9ff", width=4, tags=("dyn",))
                    cv.create_oval(x - 42, y - 24, x + 42, y + 24, outline="#3fa9ff", width=3, tags=("dyn",))
                elif k == "ult_galaxy":
                    for i in range(10):
                        a = now * 7 + i * 0.628
                        rr = 90 * (1 - p * 0.5) * (0.35 + 0.65 * (i % 3) / 2.0)
                        cv.create_line(x + math.cos(a) * rr, y + math.sin(a) * rr * 0.5,
                                       x + math.cos(a + 0.5) * rr * 0.8, y + math.sin(a + 0.5) * rr * 0.4,
                                       fill="#c9a7ff" if i % 2 else "#5a2ea6", width=3, tags=("dyn",))
                    cv.create_oval(x - 34, y - 34, x + 34, y + 34, fill="#0a0410",
                                   outline="#9a5cff", width=3, tags=("dyn",))
                else:
                    r = 70 + 30 * math.sin(now * 10)
                    cv.create_oval(x - r, y - r * 0.6, x + r, y + r * 0.6,
                                   outline=f.h["glow"], width=4, tags=("dyn",))
                    for i in range(3):
                        a = now * 14 + i * 2.094
                        cv.create_line(x + math.cos(a) * r, y + math.sin(a) * r * 0.6,
                                       x - math.cos(a) * r, y - math.sin(a) * r * 0.6,
                                       fill=f.h["accent"], width=3, tags=("dyn",))

    def draw_proj(self, cv, ox, oy):
        for pr in self.proj:
            if pr["kind"] == "scythe":
                self.draw_scythe_at(cv, pr["x"] + ox, pr["y"] + oy, pr["spin"])
            elif pr["kind"] == "tide":
                x, y = pr["x"] + ox, pr["y"] + oy
                r = pr.get("r", 40)
                cv.create_rectangle(x - r, y - r * 1.6, x + r, y + r * 0.8,
                                    fill=pr.get("color", "#3fa9ff"), stipple="gray50",
                                    outline="#bfe9ff", width=2, tags=("dyn",))
                cv.create_oval(x - r * 0.5, y - r * 1.4, x + r * 0.5, y - r * 0.4,
                               fill="#ffffff", stipple="gray25", outline="", tags=("dyn",))
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

    INJURY_TXT = {"str": "ТРАВМА РУКИ: СИЛА -25%", "spd": "ТРАВМА НОГИ: СКОРОСТЬ -30%",
                  "jump": "ТРАВМА КОЛЕНА: ПРЫЖКИ НЕДОСТУПНЫ", "ability": "ТРАВМА: СПОСОБНОСТЬ ЗАБЛОКИРОВАНА"}

    def draw_hud(self, cv, coins):
        self.hp_bar(cv, 100, 460, self.p, True)
        self.hp_bar(cv, W - 560, 460, self.b, False)
        if self.p.injury:
            cv.create_text(104, 100, text=self.INJURY_TXT[self.p.injury["kind"]], anchor="w",
                           font=F_TINY, fill=COL_BLOOD, tags=("dyn",))
        if self.b.injury:
            cv.create_text(W - 104, 100, text=self.INJURY_TXT[self.b.injury["kind"]], anchor="e",
                           font=F_TINY, fill=COL_BLOOD, tags=("dyn",))
        efrac = clamp(self.p.energy / 100.0, 0.0, 1.0)
        cv.create_rectangle(103, 70, 557, 84, fill="#160404", outline="#5a1c10", width=2, tags=("dyn",))
        if efrac > 0:
            cv.create_rectangle(106, 73, 106 + int(448 * efrac), 81, fill=COL_GOLD, outline="", tags=("dyn",))
        cv.create_text(554, 77, text="ЭНЕРГИЯ", anchor="e", font=F_TINY,
                       fill="#5a1c10" if efrac > 0.85 else "#a1700a", tags=("dyn",))
        ufrac = clamp(self.p.ult_charge / ULT_CHARGE_MAX, 0.0, 1.0)
        ufull = ufrac >= 1.0
        ucol = "#ff2a8a" if ufull else "#8a2a5a"
        cv.create_rectangle(103, 90, 557, 100, fill="#160404", outline="#5a1c10", width=1, tags=("dyn",))
        if ufrac > 0:
            cv.create_rectangle(105, 92, 105 + int(450 * ufrac), 98, fill=ucol, outline="", tags=("dyn",))
        cv.create_text(554, 95, text="УЛЬТА", anchor="e", font=F_TINY,
                       fill="#ff9aff" if ufull else "#a1700a", tags=("dyn",))
        for i in range(0 if self.survival else 2):
            for side, wins in ((-1, self.wins_p), (1, self.wins_b)):
                cx = W / 2 + side * (44 + i * 30)
                filled = wins > i
                cv.create_oval(cx - 10, 36, cx + 10, 56,
                               fill=COL_DEEPRED if filled else "#1a0908",
                               outline=COL_GOLD if filled else COL_FRAME, width=2, tags=("dyn",))
        if self.survival:
            lvl_txt = ("ВОЛНА %d · МИНИ-БОСС" % self.wave) if self.mini else ("ВОЛНА %d" % self.wave)
        elif self.martyr:
            lvl_txt = "МУЧЕНИК · РАУНД %d/%d" % (self.round, MARTYR_ROUNDS)
        else:
            lvl_txt = ("БОСС · УР. %d" if self.boss else "БОТ · УР. %d") % self.level
        cv.create_text(W - 60, 110, text=lvl_txt, anchor="e", font=F_MID,
                       fill="#ff2a1a" if (self.boss or (self.survival and self.mini)) else COL_ORANGE, tags=("dyn",))
        cv.create_oval(44, 74, 62, 92, fill=COL_GOLD, outline="#a1700a", width=2, tags=("dyn",))
        cv.create_text(70, 83, text=str(coins), anchor="w", fill=COL_GOLD, font=F_MID, tags=("dyn",))
        n_ab = len(self.p.h["abilities"])
        total = (n_ab + 3) * 66 - 6
        x0 = W // 2 - total // 2
        for i in range(n_ab):
            x = x0 + i * 66
            ab = self.p.h["abilities"][i]
            nm, cdmax = ab["name"], ab["cd"]
            frac = self.p.cds[i] / cdmax if cdmax else 0.0
            ready = self.p.cds[i] <= 0
            blocked = self.p.injury and self.p.injury["kind"] == "ability" and self.p.injury["ability"] == i
            cv.create_rectangle(x, H - 86, x + 60, H - 26, fill=COL_DARK,
                                outline=COL_BLOOD if blocked else (COL_GOLD if ready else "#5a1c10"),
                                width=2, tags=("dyn",))
            if frac > 0:
                cv.create_rectangle(x, H - 86, x + 60, H - 86 + 60 * frac, fill="#000000",
                                    stipple="gray50", outline="", tags=("dyn",))
                cv.create_text(x + 30, H - 54, text="%.0f" % math.ceil(self.p.cds[i]), fill="#e8c9a0",
                               font=F_SMALL, tags=("dyn",))
            cv.create_text(x + 30, H - 68, text=str(i + 1), fill=COL_GOLD if ready else "#8a4a20",
                           font=F_MID, tags=("dyn",))
            cv.create_text(x + 30, H - 37, text=nm.split()[0][:9], fill=COL_ORANGE, font=F_TINY, tags=("dyn",))
        extra = (("E", "ПИНОК", self.p.strike_cds.get("kick", 0.0), 1.0),
                 ("S+ЛКМ", "АППЕРКОТ", self.p.strike_cds.get("upper", 0.0), 2.0))
        for j, (key_txt, nm2, cdl, cdmax) in enumerate(extra):
            x = x0 + (n_ab + 1 + j) * 66
            ready = cdl <= 0
            cv.create_rectangle(x, H - 86, x + 60, H - 26, fill=COL_DARK,
                                outline=COL_GOLD if ready else "#5a1c10", width=2, tags=("dyn",))
            if cdl > 0:
                frac = cdl / cdmax
                cv.create_rectangle(x, H - 86, x + 60, H - 86 + 60 * frac, fill="#000000",
                                    stipple="gray50", outline="", tags=("dyn",))
                cv.create_text(x + 30, H - 54, text="%.1f" % cdl, fill="#e8c9a0", font=F_SMALL, tags=("dyn",))
            cv.create_text(x + 30, H - 68, text=key_txt, fill=COL_GOLD if ready else "#8a4a20",
                           font=F_TINY, tags=("dyn",))
            cv.create_text(x + 30, H - 37, text=nm2, fill=COL_ORANGE, font=F_TINY, tags=("dyn",))
        x = x0 + (n_ab + 3) * 66 - 66
        pcd = self.p.parry_cd
        ready = pcd <= 0
        col = "#ffd23f" if self.p.parry_t > 0 else (COL_GOLD if ready else "#5a1c10")
        cv.create_rectangle(x, H - 86, x + 60, H - 26, fill=COL_DARK, outline=col, width=2, tags=("dyn",))
        if pcd > 0:
            frac = pcd / PARRY_CD
            cv.create_rectangle(x, H - 86, x + 60, H - 86 + 60 * frac, fill="#000000",
                                stipple="gray50", outline="", tags=("dyn",))
            cv.create_text(x + 30, H - 54, text="%.1f" % pcd, fill="#e8c9a0", font=F_SMALL, tags=("dyn",))
        cv.create_text(x + 30, H - 68, text="F", fill=COL_GOLD if ready else "#8a4a20", font=F_MID, tags=("dyn"))
        cv.create_text(x + 30, H - 37, text="ПАРИР", fill=COL_ORANGE, font=F_TINY, tags=("dyn",))
        specials = self.p.h.get("specials", ())
        for i, sp in enumerate(specials):
            x, y = 34, 170 + i * 70
            cdl = self.p.sp_cds.get(sp["combo"], 0.0)
            can = self.p.energy >= sp["cost"] and self.p.special_cd <= 0 and cdl <= 0
            col = "#ffd24a" if can else "#5a1c10"
            cv.create_rectangle(x, y, x + 62, y + 62, fill=COL_DARK, outline=col, width=2, tags=("dyn",))
            if cdl > 0:
                frac = cdl / max(0.001, sp.get("cd", 8.0))
                cv.create_rectangle(x, y, x + 62, y + 62 * frac, fill="#000000",
                                    stipple="gray50", outline="", tags=("dyn",))
                cv.create_text(x + 31, y + 31, text="%.0f" % math.ceil(cdl), fill="#e8c9a0",
                               font=F_SMALL, tags=("dyn",))
            cv.create_text(x + 31, y + 16, text=sp["combo"].upper(), fill="#ffd24a" if can else "#8a4a20",
                           font=F_SMALL, tags=("dyn",))
            cv.create_text(x + 31, y + 34, text=sp["name"].split()[0][:9], fill=COL_ORANGE, font=F_TINY, tags=("dyn",))
            cv.create_text(x + 31, y + 50, text=str(sp["cost"]), fill="#ffd24a" if can else "#8a4a20",
                           font=F_TINY, tags=("dyn",))
        rmyth = self.myth_ready(self.p, self.b)
        rlegend = self.legend_ready(self.p, self.b)
        if rmyth or rlegend:
            y = 170 + len(specials) * 70 + 8
            col = "#ffc400" if rlegend else "#ff2a8a"
            sub = "ЛЕГ" if rlegend else "МИФ"
            cv.create_rectangle(34, y, 96, y + 62, fill="#2a0820", outline=col, width=3, tags=("dyn",))
            cv.create_text(65, y + 22, text="R", fill=col, font=F_MID, tags=("dyn",))
            cv.create_text(65, y + 44, text=sub, fill="#ff9aff" if rmyth else "#fff2b0",
                           font=F_TINY, tags=("dyn",))
        if self.combo_show > 0 and self.combo_count >= 2:
            cv.create_text(W / 2 + 2, 132, text="COMBO x%d" % self.combo_count, font=F_BIG, fill="#2a0503", tags=("dyn",))
            cv.create_text(W / 2, 130, text="COMBO x%d" % self.combo_count, font=F_BIG, fill=COL_GOLD, tags=("dyn",))

    def banner(self, cv, txt, col, y=270):
        slide = max(0.0, self.phase_t - 1.2) if self.phase_t < 1e9 else 0.0
        off = int(slide * 900)
        cv.create_text(W / 2 + off + 4, y + 4, text=txt, font=F_HUGE, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2 + off, y, text=txt, font=F_HUGE, fill=col, tags=("dyn",))

    def draw_fatality_prompt(self, cv):
        fat = self.fatality
        if not fat:
            return
        seq, idx, t = fat["seq"], fat["idx"], max(0.0, fat["t"])
        n = len(seq)
        bw, gap = 74, 14
        x0 = W / 2 - (n * bw + (n - 1) * gap) / 2
        cv.create_text(W / 2, 535, text="УСПЕЙ НАБРАТЬ КОМБО:", fill="#e8c9a0", font=F_SMALL, tags=("dyn",))
        for i, tok in enumerate(seq):
            x = x0 + i * (bw + gap)
            done = i < idx
            cur = i == idx
            col = COL_GOLD if done else ("#ff5a1a" if (cur and int(t * 6) % 2) else "#ff8c1a" if cur else "#5a1c10")
            cv.create_rectangle(x, 560, x + bw, 620, fill="#1c0a08", outline=col, width=3, tags=("dyn",))
            cv.create_text(x + bw / 2, 590, text=FATALITY_TXT.get(tok, tok.upper()),
                           fill=COL_GOLD if done else ("#ffd23f" if cur else "#8a4a20"), font=F_MID, tags=("dyn",))
        frac = t / FATALITY_WINDOW
        cv.create_rectangle(W / 2 - 220, 640, W / 2 + 220, 654, fill="#160404", outline="#5a1c10",
                            width=1, tags=("dyn",))
        if frac > 0:
            cv.create_rectangle(W / 2 - 218, 642, W / 2 - 218 + int(436 * frac), 652,
                                fill=COL_RED if frac < 0.35 else COL_GOLD, outline="", tags=("dyn",))

    def draw_fracture(self, cv, f, ox, oy):
        kind = f.injury["kind"]
        yy = {"str": -120, "spd": -55, "jump": -70, "ability": -160}.get(kind, -90)
        x, y = f.x + ox, f.y + yy * f.scale + oy
        cv.create_line(x - 9, y - 9, x + 9, y + 9, fill="#f2ead8", width=3, tags=("dyn",))
        cv.create_line(x - 9, y + 9, x + 9, y - 9, fill="#f2ead8", width=3, tags=("dyn",))
        cv.create_oval(x - 3, y - 3, x + 3, y + 3, fill=COL_BLOOD, outline="", tags=("dyn",))

    def draw(self, cv, coins):
        sh = self.shake
        ox = random.uniform(-sh, sh) if sh > 0.5 else 0.0
        oy = random.uniform(-sh, sh) if sh > 0.5 else 0.0
        cv.delete("dyn")
        self.draw_fx(cv, ox, oy, True)
        self.p.render(cv, ox, oy)
        if not getattr(self.b, "fatality_hide", False):
            self.b.render(cv, ox, oy)
        self.draw_fx(cv, ox, oy, False)
        self.draw_proj(cv, ox, oy)
        for m in self.melee:
            f, stage = m[0], m[2]
            col = ("#fff7b0", "#ffd23f", "#ff8c1a")[min(2, stage)]
            r = 62 + stage * 16
            x0, y0 = f.x + f.facing * 26 * f.scale + ox, f.y - 95 * f.scale + oy
            a0 = -60 if f.facing > 0 else 120
            cv.create_arc(x0 - r, y0 - r, x0 + r, y0 + r, start=a0, extent=70,
                          style="arc", outline=col, width=3, tags=("dyn",))
        self.parts.draw(cv, ox, oy)
        for f in (self.p, self.b):
            if f.injury and not f.dead:
                self.draw_fracture(cv, f, ox, oy)
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
        elif self.phase == "fatality":
            cv.create_rectangle(0, 0, W, H, fill="#050101", stipple="gray50", outline="", tags=("dyn",))
            self.banner(cv, "ФАТАЛИТИ", COL_RED)
            self.draw_fatality_prompt(cv)
        elif self.phase == "fatality_anim":
            cv.create_rectangle(0, 0, W, H, fill="#050101", stipple="gray50", outline="", tags=("dyn",))
            self.banner(cv, "ФАТАЛИТИ!", COL_RED)
        elif self.phase == "end":
            cv.create_rectangle(0, 0, W, H, fill="#0a0202", stipple="gray50", outline="", tags=("dyn",))
            cv.create_rectangle(W / 2 - 400, 220, W / 2 + 400, 660, fill=COL_DARK, outline=COL_GOLD,
                                width=3, tags=("dyn",))
            if self.survival:
                cv.create_text(W / 2, 295, text="ВЫЖИВАНИЕ ОКОНЧЕНО", font=F_HUGE, fill=COL_GOLD, tags=("dyn",))
                if self.reward > 0:
                    cv.create_text(W / 2, 365, text="+%d МОНЕТ" % self.reward, font=F_BIG, fill=COL_ORANGE, tags=("dyn",))
                cv.create_text(W / 2, 410, text="Пройдено волн: %d" % (self.wave - 1),
                               font=F_SMALL, fill="#e8c9a0", tags=("dyn",))
                if getattr(self, "exp_gain", 0):
                    cv.create_text(W / 2, 442, text="+%d EXP" % self.exp_gain,
                                   font=F_SMALL, fill="#8aff8a", tags=("dyn",))
                if getattr(self, "max_combo", 0) >= 2:
                    cv.create_text(W / 2, 470, text="Макс. комбо: %d" % self.max_combo,
                                   font=F_SMALL, fill=COL_GEM, tags=("dyn",))
            else:
                t1 = "ПОБЕДА!" if self.win else "ПОРАЖЕНИЕ"
                cv.create_text(W / 2, 295, text=t1, font=F_HUGE,
                               fill=COL_GOLD if self.win else "#8a4a20", tags=("dyn",))
                if self.win and self.reward > 0 and not self.martyr:
                    cv.create_text(W / 2, 365, text="+%d МОНЕТ" % self.reward, font=F_BIG, fill=COL_ORANGE, tags=("dyn",))
                if self.net:
                    sub = "ДРУЖЕСКИЙ БОЙ · ПОЛНЫЙ БАЛАНС"
                else:
                    sub = "Уровень %d%s пройден!" % (self.level, " (БОСС ×2)" if self.boss else "")
                if self.win:
                    cv.create_text(W / 2, 410, text=sub, font=F_SMALL, fill="#e8c9a0", tags=("dyn",))
                if getattr(self, "exp_gain", 0):
                    cv.create_text(W / 2, 440, text="+%d EXP" % self.exp_gain,
                                   font=F_SMALL, fill="#8aff8a", tags=("dyn",))
                if getattr(self, "finish_bonus", 0):
                    cv.create_text(W / 2, 462, text="БОНУС ЗА ДОБИВАНИЕ +%d" % self.finish_bonus,
                                   font=F_SMALL, fill=COL_GOLD, tags=("dyn",))
                elif not self.win and not self.martyr:
                    cv.create_text(W / 2, 375, text="Бот уровня %d оказался сильнее." % self.level,
                                   font=F_SMALL, fill="#e8c9a0", tags=("dyn",))
                if self.martyr:
                    if self.win:
                        cv.create_text(W / 2, 365, text="+%d САМОЦВЕТОВ" % MARTYR_GEMS,
                                       font=F_BIG, fill=COL_GEM, tags=("dyn",))
                    else:
                        cv.create_text(W / 2, 365, text="+%d МОНЕТ ЗА УПОРСТВО" % self.reward,
                                       font=F_BIG, fill=COL_ORANGE, tags=("dyn",))
                    cv.create_text(W / 2, 410, text="Нанесено урона: %d" % int(self.dmg_dealt),
                                   font=F_SMALL, fill="#e8c9a0", tags=("dyn",))
                if self.fatality_bonus:
                    cv.create_text(W / 2, 488, text="ФАТАЛИТИ: +%d МОНЕТ +%d САМ." % (self.fatality_bonus, FATALITY_GEMS),
                                   font=F_SMALL, fill=COL_GEM, tags=("dyn",))
                cv.create_text(W / 2, 512, text="Счёт раундов  %d : %d   ·   Макс. комбо: %d" % (
                    self.wins_p, self.wins_b, self.max_combo),
                    font=F_SMALL, fill=COL_SAND, tags=("dyn",))
