"""IMMY — боец: физика, статы, комбо-атаки, баффы и процедурный пиксель-рендер."""

import math
import random

from .config import (COMBO_MULT, COMBO_WINDOW, CRIT_MULT, GROUND_Y, GRAVITY,
                     KICK_CD, PARRY_CD, PARRY_WINDOW, UPPERCUT_CD, W, WALL)
from .heroes import HEROES
from .util import clamp

STRIKES = {
    "kick":  {"dur": 0.24, "cd": KICK_CD, "delay": 0.10},
    "upper": {"dur": 0.30, "cd": UPPERCUT_CD, "delay": 0.13},
    "sweep": {"dur": 0.26, "cd": 1.2, "delay": 0.11},
    "air":   {"dur": 0.26, "cd": 1.0, "delay": 0.09},
    "dive":  {"dur": 0.34, "cd": 1.2, "delay": 0.16},
}
STRIKE_KINDS = tuple(STRIKES)


class Fighter:
    W_BBOX = 36
    H_STAND = 168
    H_CROUCH = 114

    def __init__(self, key, x, facing, scale=1.0):
        self.key = key
        self.h = HEROES[key]
        self.x = float(x)
        self.y = float(GROUND_Y)
        self.vx = 0.0
        self.vx_target = 0.0
        self.vy = 0.0
        self.kvx = 0.0
        self.facing = facing
        self.scale = scale
        self.max_hp = 100.0
        self.hp = 100.0
        self.disp_hp = 100.0
        self.on_ground = True
        self.crouch = False
        self.anim_t = random.uniform(0, 5)
        self.attack_t = 0.0
        self.attack_cd = 0.0
        self.attack_kind = "melee"
        self.combo = 0
        self.combo_t = 0.0
        self.hurt_t = 0.0
        self.hit_flash = 0.0
        self.stun_t = 0.0
        self.dead = False
        self.dead_t = 0.0
        self.cds = [0.0] * len(self.h["abilities"])
        self.buffs = {"flash": 0.0, "rage": 0.0, "soul": 0.0,
                      "guard": 0.0, "swift": 0.0, "vamp": 0.0}
        self.vamp_pct = 0.0
        st = self.h["stats"]
        self.stat_dmg = 0.85 + st["str"] * 0.03
        self.crit_chance = 0.04 + st["agi"] * 0.016
        self.stat_spd = 0.80 + st["spd"] * 0.04
        self.parry_window = PARRY_WINDOW + st["agi"] * 0.008
        self.parry_t = 0.0
        self.parry_cd = 0.0
        self.parry_flash = 0.0
        self.root_t = 0.0
        self.energy = 0.0
        self.special_cd = 0.0
        self.sp_cds = {}
        self.strike_cds = {}
        self.injury = None
        self.poison_t = 0.0
        self.poison_dps = 0.0
        self.poison_tick = 0.0
        self.soul_target = None
        self.scythe_out = False
        self.speed_mult = 1.0
        self.dmg_mult = 1.0
        self.base_dmg = 1.0
        self.base_speed = 1.0
        self.is_bot = False
        self.reaction = 0.5
        self.synced = False
        self.tx = self.x
        self.ty = self.y
        self.fatality_hide = False
        self.flash_mult = 0.4
        self.rage_mult = 1.5
        self.has_scythe = any(ab.get("kind") == "scythe" for ab in self.h["abilities"])

    def out_mult(self):
        return self.dmg_mult * (self.rage_mult if self.buffs["rage"] > 0 else 1.0)

    def bbox(self):
        h = (self.H_CROUCH if (self.crouch and self.on_ground) else self.H_STAND) * self.scale
        w = self.W_BBOX * self.scale
        return (self.x - w, self.y - h, self.x + w, self.y)

    def start_attack(self, game):
        if self.dead or self.stun_t > 0 or self.hurt_t > 0:
            return
        if self.attack_cd > 0 or self.attack_t > 0:
            return
        if self.has_scythe and self.scythe_out:
            return
        if self.combo_t > 0:
            self.combo = (self.combo + 1) % 3
        else:
            self.combo = 0
        self.combo_t = COMBO_WINDOW
        self.attack_t = 0.28
        self.attack_cd = 0.38 if self.combo < 2 else 0.52
        self.attack_kind = "melee"
        game.melee.append([self, 0.12, self.combo])

    def try_strike(self, kind, game):
        if kind not in STRIKES:
            return False
        if self.dead or self.stun_t > 0 or self.hurt_t > 0:
            return False
        if self.attack_cd > 0 or self.attack_t > 0:
            return False
        if self.strike_cds.get(kind, 0.0) > 0:
            return False
        if self.has_scythe and self.scythe_out:
            return False
        if kind in ("air", "dive") and self.on_ground:
            return False
        if kind == "sweep" and not (self.crouch and self.on_ground):
            return False
        spec = STRIKES[kind]
        if self.combo_t > 0:
            self.combo = (self.combo + 1) % 3
        else:
            self.combo = 0
        self.combo_t = COMBO_WINDOW
        self.attack_t = spec["dur"]
        self.attack_cd = spec["dur"] + 0.14
        self.attack_kind = kind
        self.strike_cds[kind] = spec["cd"]
        game.strikes.append([self, spec["delay"], kind, self.combo])
        return True

    def can_jump(self):
        return not (self.injury and self.injury["kind"] == "jump")

    def dmg_factor(self):
        f = self.stat_dmg
        if self.injury and self.injury["kind"] == "str":
            f *= 0.75
        return f

    def try_parry(self):
        if self.dead or self.stun_t > 0 or self.root_t > 0 or self.parry_cd > 0 or self.parry_t > 0:
            return False
        self.parry_t = self.parry_window
        self.parry_cd = PARRY_CD
        return True

    def roll_damage(self, base):
        crit = random.random() < self.crit_chance
        dmg = base * self.dmg_factor() * self.out_mult()
        if crit:
            dmg *= CRIT_MULT
        return dmg, crit

    def gain_energy(self, dmg):
        if dmg > 0:
            self.energy = min(100.0, self.energy + 6.0 + dmg * 0.15)

    def eff_speed(self):
        m = self.speed_mult * self.stat_spd
        if self.buffs["swift"] > 0:
            m *= 1.45
        if self.injury and self.injury["kind"] == "spd":
            m *= 0.7
        return m

    def take_damage(self, dmg, kb_dir=0.0, stun=0.0, kb_force=None, pierce_guard=False):
        if self.dead or self.buffs["soul"] > 0:
            return "miss"
        if self.parry_t > 0:
            self.parry_t = 0.0
            self.parry_flash = 0.3
            return "parry"
        if self.buffs["guard"] > 0 and not pierce_guard:
            return "guard"
        if self.buffs["flash"] > 0:
            dmg *= self.flash_mult
        self.hp = max(0.0, self.hp - dmg)
        self.hit_flash = 0.12
        self.hurt_t = 0.2
        self.kvx += kb_dir * (240.0 if kb_force is None else kb_force)
        if stun > 0:
            self.stun_t = max(self.stun_t, stun)
        return "hit"

    def update(self, dt, foe, game):
        self.anim_t += dt
        if self.dead:
            self.dead_t += dt
        prev_soul = self.buffs["soul"]
        for k in self.buffs:
            if self.buffs[k] > 0:
                self.buffs[k] = max(0.0, self.buffs[k] - dt)
        if prev_soul > 0 and self.buffs["soul"] == 0 and self.soul_target is not None:
            e = self.soul_target
            self.x = clamp(e.x - e.facing * 95, WALL + 30, W - WALL - 30)
            self.soul_target = None
            game.parts.burst(self.x, self.y - 80 * self.scale, self.h["accent"], 14, 200)
        for i in range(len(self.cds)):
            self.cds[i] = max(0.0, self.cds[i] - dt)
        self.parry_t = max(0.0, self.parry_t - dt)
        self.parry_cd = max(0.0, self.parry_cd - dt)
        self.parry_flash = max(0.0, self.parry_flash - dt)
        self.special_cd = max(0.0, self.special_cd - dt)
        for k in self.sp_cds:
            self.sp_cds[k] = max(0.0, self.sp_cds[k] - dt)
        for k in self.strike_cds:
            self.strike_cds[k] = max(0.0, self.strike_cds[k] - dt)
        self.root_t = max(0.0, self.root_t - dt)
        if self.poison_t > 0:
            self.poison_t = max(0.0, self.poison_t - dt)
            self.poison_tick += self.poison_dps * dt
            if self.poison_tick >= 2.0:
                n = int(self.poison_tick)
                self.poison_tick -= n
                self.hp = max(1.0, self.hp - n)
                game.parts.dmg_text(self.x, self.y - 150 * self.scale, n, "#7ad12a")
            if random.random() < dt * 8:
                game.parts.rise(self.x, self.y - 60 * self.scale, "#7ad12a")
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.attack_t = max(0.0, self.attack_t - dt)
        self.hurt_t = max(0.0, self.hurt_t - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.stun_t = max(0.0, self.stun_t - dt)
        if self.combo_t > 0:
            self.combo_t = max(0.0, self.combo_t - dt)
            if self.combo_t == 0:
                self.combo = 0
        if self.disp_hp > self.hp:
            self.disp_hp = max(self.hp, self.disp_hp - 26.0 * dt)
        else:
            self.disp_hp = self.hp
        if foe is not None and self.attack_t <= 0:
            self.facing = 1 if foe.x >= self.x else -1
        if not self.on_ground:
            self.vy += GRAVITY * dt
            self.y += self.vy * dt
            if self.y >= GROUND_Y:
                self.y = float(GROUND_Y)
                self.vy = 0.0
                self.on_ground = True
                game.parts.dust(self.x, self.y)
        if self.root_t > 0:
            self.vx_target = 0.0
            self.vx = 0.0
            self.kvx *= math.exp(-12 * dt)
        self.vx += (self.vx_target - self.vx) * min(1.0, dt * 16.0)
        self.x += (self.vx + self.kvx) * dt
        self.kvx *= math.exp(-7 * dt)
        self.x = clamp(self.x, WALL + 30, W - WALL - 30)
        if self.h["style"] == "glow" and random.random() < dt * 6:
            game.parts.spark(self.x + random.uniform(-26, 26) * self.scale,
                             self.y - random.uniform(30, 150) * self.scale)
        if self.dead and random.random() < dt * 8:
            game.parts.rise(self.x, self.y, self.h["glow"])

    def melee_damage(self, stage):
        return random.uniform(8, 13) * COMBO_MULT[min(stage, 2)]

    def draw_scythe(self, cv, hx, hy, ang, s, fc):
        L = 78
        ex = hx + fc * math.cos(ang) * L * s
        ey = hy - math.sin(ang) * L * s
        cv.create_line(hx, hy, ex, ey, fill="#6b4a2a", width=max(2, int(5 * s)), tags=("dyn",))
        pts = [ex, ey,
               ex + fc * 30 * s, ey - 16 * s,
               ex + fc * 46 * s, ey + 4 * s,
               ex + fc * 18 * s, ey + 20 * s]
        cv.create_polygon(*pts, fill="#d7dee6", outline="#8a949e", tags=("dyn",))
        tx = hx + fc * math.cos(ang + 0.5) * L * 0.6 * s
        ty = hy - math.sin(ang + 0.5) * L * 0.6 * s
        cv.create_line(hx, hy, tx, ty, fill="#ffffff", width=2, tags=("dyn",), stipple="gray25")

    def render_dead(self, cv, X, Y, s, kw, body, body2):
        lie = min(1.0, self.dead_t * 2.2)
        drop = int(90 * lie)
        cv.create_oval(X - 46 * s, Y - 10 * s, X + 46 * s, Y + 8 * s,
                       fill="#000000", outline="", tags=("dyn",), stipple="gray50")
        cv.create_rectangle(X - 40 * s, Y - 22 * s - drop * 0.1, X + 34 * s, Y - 2 * s,
                            fill=body, outline="", tags=("dyn",), **kw)
        cv.create_rectangle(X - 40 * s, Y - 10 * s, X + 34 * s, Y - 2 * s,
                            fill=body2, outline="", tags=("dyn",), **kw)
        hx = X + self.facing * 44 * s
        cv.create_rectangle(hx - 13 * s, Y - 20 * s, hx + 13 * s, Y - 2 * s,
                            fill=body, outline="", tags=("dyn",), **kw)
        eye = self.h["eye"]
        cv.create_rectangle(hx - 8 * s, Y - 14 * s, hx - 4 * s, Y - 10 * s,
                            fill=eye, outline="", tags=("dyn",), **kw)
        cv.create_rectangle(hx + 2 * s, Y - 14 * s, hx + 6 * s, Y - 10 * s,
                            fill=eye, outline="", tags=("dyn",), **kw)
        for i, fx in enumerate((-26, -6, 16)):
            cv.create_rectangle(X + fx * s, Y - 30 * s - (i % 2) * 3, X + (fx + 12) * s, Y - 22 * s,
                                fill=body2, outline="", tags=("dyn",), **kw)

    def render(self, cv, ox=0.0, oy=0.0):
        s = self.scale
        t = self.anim_t
        fc = self.facing
        X = self.x + ox
        Y = self.y + oy
        C = self.h
        dead = self.dead
        soul = self.buffs["soul"] > 0
        flash_hit = self.hit_flash > 0
        st = "gray25" if (soul or dead) else None
        kw = {"stipple": st} if st else {}

        body = "#ffffff" if flash_hit else C["body"]
        body2 = "#ffffff" if flash_hit else C["body2"]
        bone = "#ffffff" if flash_hit else C["bone"]
        accent = "#ffffff" if flash_hit else C["accent"]

        if dead:
            self.render_dead(cv, X, Y, s, kw, body, body2)
            return

        def R(dx0, dy0, dx1, dy1, color):
            cv.create_rectangle(X + fc * dx0 * s, Y + dy0 * s, X + fc * dx1 * s, Y + dy1 * s,
                                fill=color, outline="", tags=("dyn",), **kw)

        cv.create_oval(X - 30 * s, Y - 6 * s, X + 30 * s, Y + 8 * s,
                       fill="#000000", outline="", tags=("dyn",), stipple="gray50")

        crouch = self.crouch and self.on_ground
        walking = self.on_ground and abs(self.vx) > 10 and not crouch
        airborne = not self.on_ground
        ph = t * 11
        bob = math.sin(ph * 2) * 2 * s if walking else 0.0

        if crouch:
            hip, leg_h = -38, 38
            shoulder, head_b, head_t = -84, -88, -114
        elif airborne:
            hip, leg_h = -54, 36
            shoulder, head_b, head_t = -120, -124, -152
        else:
            hip, leg_h = -54, 54
            shoulder, head_b, head_t = -120, -124, -152

        prog = 0.0
        attacking = self.attack_t > 0 and self.attack_kind == "melee"
        striking = self.attack_t > 0 and self.attack_kind in STRIKE_KINDS
        if attacking or striking:
            prog = 1 - self.attack_t / (0.28 if attacking else STRIKES[self.attack_kind]["dur"])
            X += fc * (9 + 4 * self.combo) * s * math.sin(prog * math.pi)

        if walking:
            sw = math.sin(ph) * 9
            l1, l2 = -10 + sw, 10 - sw
        elif airborne:
            l1, l2 = -14, 12
        else:
            l1, l2 = -10, 10
        R(l1 - 6, hip, l1 + 6, hip + leg_h, body2)
        R(l2 - 6, hip, l2 + 6, hip + leg_h, body)
        R(l1 - 7, hip + leg_h - 10, l1 + 7, hip + leg_h, C["bone"])
        R(l2 - 7, hip + leg_h - 10, l2 + 7, hip + leg_h, C["bone"])

        R(-19, shoulder + bob, 19, hip, body)
        R(-19, hip - 8 + bob, 19, hip, accent)
        R(-19, shoulder + bob, 19, shoulder + 12 + bob, body2)

        ext = 0.0
        if attacking:
            ext = 22 + 46 * math.sin(prog * math.pi)
            R(14, shoulder + 2 + bob, 14 + ext, shoulder + 15 + bob, body)
            R(-26, shoulder + 6 + bob, -15, shoulder + 44 + bob, body2)
            R(14 + ext - 8, shoulder - 1 + bob, 14 + ext + 2, shoulder + 18 + bob, C["bone"])
        elif striking:
            sw_ext = 34 + 30 * math.sin(prog * math.pi)
            kind = self.attack_kind
            if kind == "kick":
                R(-8, hip - 8, 6, hip + 16, body2)
                R(6, hip - 12, 6 + sw_ext, hip - 2, body)
                R(6 + sw_ext - 8, hip - 12, 6 + sw_ext + 2, hip - 2, C["bone"])
            elif kind == "upper":
                R(12, shoulder - sw_ext + 6, 24, shoulder + 12, body)
                R(12, shoulder - sw_ext, 24, shoulder - sw_ext + 10, C["bone"])
                R(-26, shoulder + 6, -15, shoulder + 40, body2)
            elif kind == "sweep":
                R(-8, hip - 4, 4, hip + leg_h - 6, body2)
                R(4, hip + leg_h - 14, 4 + sw_ext, hip + leg_h, body)
                R(4 + sw_ext - 8, hip + leg_h - 14, 4 + sw_ext + 2, hip + leg_h - 4, C["bone"])
            elif kind == "air":
                R(10, shoulder - 4, 22, shoulder - sw_ext * 0.7, body)
                R(10, shoulder - sw_ext * 0.7 - 8, 22, shoulder - sw_ext * 0.7, C["bone"])
                R(-14, hip - 4, -4, hip + leg_h + 8, body2)
            else:
                R(8, shoulder, 20, shoulder + sw_ext, body)
                R(8, shoulder + sw_ext - 8, 20, shoulder + sw_ext, C["bone"])
                R(-20, hip - 18, -8, hip + 6, body2)
        elif walking:
            sw2 = math.sin(ph) * 5
            R(15 + sw2, shoulder + 4 + bob, 26 + sw2, shoulder + 42 + bob, body)
            R(-26 - sw2, shoulder + 4 + bob, -15 - sw2, shoulder + 42 + bob, body2)
        else:
            R(15, shoulder + 4 + bob, 26, shoulder + 42 + bob, body)
            R(-26, shoulder + 4 + bob, -15, shoulder + 42 + bob, body2)

        R(-14, head_t + bob, 14, head_b + bob, body)

        style = C["style"]
        if style == "hood":
            R(0, head_t + 6 + bob, 12, head_b - 2 + bob, body2)
            R(3, head_t + 11 + bob, 7, head_t + 16 + bob, accent)
            R(9, head_t + 11 + bob, 12, head_t + 16 + bob, accent)
            R(-4, hip - 40 + bob, 4, hip - 32 + bob, bone)
        else:
            R(2, head_t + 10 + bob, 7, head_t + 16 + bob, C["eye"])
            R(9, head_t + 10 + bob, 13, head_t + 16 + bob, C["eye"])
            if style == "flame" and not flash_hit:
                for i, (dxo, hgt, col) in enumerate(((-8, 20, C["accent"]), (0, 30, C["glow"]), (8, 18, C["bone"]))):
                    fx0 = X + (dxo - 5) * s
                    fx1 = X + (dxo + 5) * s
                    tipy = Y + (head_t - hgt - 5 * math.sin(t * 12 + i * 2.1)) * s + bob
                    cv.create_polygon(fx0, Y + (head_t + 2) * s + bob, fx1, Y + (head_t + 2) * s + bob,
                                      X + dxo * s, tipy, fill=col, outline="", tags=("dyn",), **kw)
            elif style == "spike" and not flash_hit:
                for i in range(3):
                    sx = -9 + i * 9
                    tipy = Y + (head_t - 13 - 4 * math.sin(t * 6 + i * 1.9)) * s + bob
                    cv.create_polygon(X + (sx - 4) * s, Y + (head_t + 2) * s + bob,
                                      X + (sx + 4) * s, Y + (head_t + 2) * s + bob,
                                      X + sx * s, tipy, fill=C["glow"], outline="", tags=("dyn",), **kw)
            elif style == "spider" and not flash_hit:
                R(-9, head_t + 6 + bob, -5, head_t + 10 + bob, C["eye"])
                R(7, head_t + 6 + bob, 11, head_t + 10 + bob, C["eye"])
                for dy, ln in ((-52, 26), (-70, 30), (-88, 26), (-104, 18)):
                    for sgn in (-1, 1):
                        my = shoulder + dy + bob
                        cv.create_line(X + sgn * 19 * s, Y + my * s,
                                       X + sgn * (19 + ln * 0.6) * s, Y + (my - 14) * s,
                                       X + sgn * (19 + ln) * s, Y + (my + 26) * s,
                                       fill=C["body2"], width=max(2, int(4 * s)), tags=("dyn",), **kw)
            elif style == "plain" and not flash_hit:
                R(-12, head_t - 5 + bob, 12, head_t + 3 + bob, accent)

        if style == "glow" and not flash_hit:
            g = C["glow"]
            cv.create_rectangle(X - 32 * s, Y - 162 * s, X + 32 * s, Y + 4 * s,
                                outline=g, width=2, tags=("dyn",), stipple="gray50")
            if (t * 14) % 2 < 1.3:
                cv.create_rectangle(X - 38 * s, Y - 168 * s, X + 38 * s, Y + 8 * s,
                                    outline=g, width=1, tags=("dyn",), stipple="gray25")

        if self.buffs["flash"] > 0:
            cv.create_oval(X - 55 * s, Y - 180 * s, X + 55 * s, Y + 10 * s,
                           outline=C["glow"], width=3, tags=("dyn",), stipple="gray25")

        if self.buffs["rage"] > 0:
            cv.create_rectangle(X - 30 * s, Y - 160 * s, X + 30 * s, Y + 4 * s,
                                outline=C["accent"], width=3, tags=("dyn",), stipple="gray25")

        if self.has_scythe and not self.scythe_out and not soul:
            if attacking:
                hx, hy = X + fc * (14 + ext) * s, Y + (shoulder + 9 + bob) * s
                ang = 1.5 - 2.2 * prog
            else:
                hx, hy = X + fc * 21 * s, Y + (shoulder + 40 + bob) * s
                ang = 0.85 + math.sin(t * 2) * 0.05
            self.draw_scythe(cv, hx, hy, ang, s, fc)

        if attacking:
            a0 = -45 if fc > 0 else 135
            cv.create_arc(X - 78 * s, Y - 160 * s, X + 78 * s, Y - 4 * s, start=a0, extent=90,
                          style="arc", outline=accent, width=4, tags=("dyn",))
        elif striking:
            kind = self.attack_kind
            col = C["glow"] if kind in ("upper", "dive") else accent
            if kind == "kick":
                a0 = -20 if fc > 0 else 110
                cv.create_arc(X - 92 * s, Y - 120 * s, X + 92 * s, Y + 30 * s, start=a0, extent=55,
                              style="arc", outline=col, width=4, tags=("dyn",))
            elif kind == "upper":
                a0 = 20 if fc > 0 else 70
                cv.create_arc(X - 70 * s, Y - 210 * s, X + 70 * s, Y - 60 * s, start=a0, extent=100,
                              style="arc", outline=col, width=5, tags=("dyn",))
            elif kind == "sweep":
                a0 = 15 if fc > 0 else 105
                cv.create_arc(X - 96 * s, Y - 60 * s, X + 96 * s, Y + 34 * s, start=a0, extent=60,
                              style="arc", outline=col, width=4, tags=("dyn",))
            elif kind == "air":
                cv.create_line(X, Y - 150 * s, X + fc * 26 * s, Y - 90 * s,
                               fill=col, width=4, tags=("dyn",), stipple="gray25")
            else:
                cv.create_line(X - fc * 20 * s, Y - 150 * s, X + fc * 40 * s, Y - 60 * s,
                               fill=col, width=5, tags=("dyn",), stipple="gray25")

        if self.stun_t > 0:
            hy0 = Y + (head_t - 16) * s
            pts = []
            for i in range(7):
                pts += [X + (i - 3) * 7 * s, hy0 + (5 if i % 2 else -5) * s]
            cv.create_line(*pts, fill="#ffd23f", width=3, tags=("dyn",))

        if self.parry_t > 0:
            cv.create_arc(X - 62 * s, Y - 152 * s, X + 62 * s, Y - 16 * s,
                          start=-30 if fc > 0 else 120, extent=60, style="arc",
                          outline="#ffd23f", width=4, tags=("dyn",))
        elif self.parry_flash > 0:
            cv.create_arc(X - 66 * s, Y - 156 * s, X + 66 * s, Y - 12 * s,
                          start=-30 if fc > 0 else 120, extent=60, style="arc",
                          outline="#fff2b0", width=2, tags=("dyn",))

        if self.buffs["guard"] > 0:
            cv.create_oval(X - 44 * s, Y - 168 * s, X + 44 * s, Y + 6 * s,
                           outline=C["glow"], width=3, tags=("dyn",), stipple="gray50")

        if self.root_t > 0:
            for i in range(6):
                a = i * math.pi / 3.0
                cv.create_line(X, Y, X + math.cos(a) * 34 * s, Y - abs(math.sin(a)) * 12 * s,
                               fill=C["accent"], width=2, tags=("dyn",))
            cv.create_line(X - 40 * s, Y - 4 * s, X + 40 * s, Y - 4 * s,
                           fill=C["accent"], width=2, tags=("dyn",))

        if self.poison_t > 0 and not flash_hit:
            for i in range(3):
                bx = X + math.sin(t * 2.2 + i * 2.1) * 20 * s
                by = Y - (30 + ((t * 40 + i * 55) % 120)) * s
                r = 3.0 * s
                cv.create_oval(bx - r, by - r, bx + r, by + r,
                               fill="#7ad12a", outline="", tags=("dyn",), stipple="gray50")

        if self.buffs["swift"] > 0:
            for i in range(3):
                ly = Y - (60 + i * 34) * s
                cv.create_line(X - fc * 34 * s, ly, X - fc * (58 + i * 8) * s, ly,
                               fill=C["glow"], width=2, tags=("dyn",), stipple="gray50")

        if self.combo_t > 0 and self.combo >= 2 and self.attack_t > 0:
            cv.create_text(X, Y + (head_t - 34) * s, text="COMBO x%d" % (self.combo + 1),
                           fill=C["glow"], font=("Courier", 12, "bold"), tags=("dyn",))

        if self.injury:
            cv.create_text(X, Y + (head_t - 20) * s, text="✖",
                           fill="#c4140f", font=("Courier", 13, "bold"), tags=("dyn",))
