"""IMMY — арена: бой, раунды, способности, снаряды, эффекты, HUD."""

import math
import random

from .ai import BotAI
from .background import MAPS, draw_hero_icon
from .config import (COMBO_KB, COL_DEEPRED, COL_DARK, COL_FRAME, COL_GOLD, COL_ORANGE, COL_RED, COL_SAND,
                     F_BIG, F_HUGE, F_MID, F_SMALL, F_TINY, GROUND_Y, H, MELEE_RANGE, W, WALL)
from .fighter import Fighter
from .particles import Particles
from .util import clamp


class Arena:
    def __init__(self, player_key, bot_key, level, boss, map=None):
        self.level = level
        self.boss = boss
        self.map = map if map is not None else random.choice(MAPS)
        self.round = 1
        self.wins_p = 0
        self.wins_b = 0
        self.phase = "intro"
        self.phase_t = 1.6
        self.p = Fighter(player_key, W * 0.32, 1)
        self.b = Fighter(bot_key, W * 0.68, -1, scale=1.35 if boss else 1.0)
        self.b.is_bot = True
        self.b.max_hp = 100.0 * (1 + level * 0.06) * (2.0 if boss else 1.0)
        self.b.hp = self.b.max_hp
        self.b.disp_hp = self.b.max_hp
        self.b.base_dmg = (1 + level * 0.045) * (1.5 if boss else 1.0)
        self.b.base_speed = 1 + min(0.5, level * 0.02)
        self.b.reaction = max(0.14, 0.55 - level * 0.018)
        self.b.dmg_mult = self.b.base_dmg
        self.b.speed_mult = self.b.base_speed
        self.ai = BotAI(self.b, level)
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
            fighter.cds = [0.0, 0.0, 0.0]
            fighter.crouch = False
            fighter.on_ground = True
            fighter.combo = 0
            fighter.combo_t = 0.0
            fighter.stun_t = fighter.hurt_t = fighter.attack_t = fighter.attack_cd = 0.0
            fighter.scythe_out = False
            fighter.buffs = {"flash": 0.0, "rage": 0.0, "soul": 0.0}
            fighter.soul_target = None
        self.b.dmg_mult = self.b.base_dmg * (1.25 if self.round >= 2 else 1.0)
        self.b.speed_mult = self.b.base_speed * (1.15 if self.round >= 2 else 1.0)
        self.proj = []
        self.fx = []
        self.melee = []
        self.parts.clear()
        self.combo_count = 0

    def after_ko(self):
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
            p.vx_target = inp["move"] * 300 * p.speed_mult * (0.45 if p.crouch else 1.0)
            if inp["jump"] and p.on_ground and not p.crouch:
                p.vy = -920.0
                p.on_ground = False
            if inp["attack"]:
                p.start_attack(self)
            if inp["cast"] is not None:
                self.cast_ability(p, inp["cast"], b)
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

    def register_hit(self, att, foe, dmg, heavy=False):
        foe.take_damage(dmg, kb_dir=att.facing)
        self.parts.burst(foe.x - foe.facing * 12, foe.y - 95 * foe.scale, "#ffd23f", 10, 220)
        self.parts.dmg_text(foe.x, foe.y - 170 * foe.scale, dmg, big=heavy)
        self.shake = max(self.shake, 7 if heavy else 5)
        self.hitstop = max(self.hitstop, 0.09 if heavy else 0.05)
        if att is self.p:
            self.combo_count += 1
            self.combo_show = 1.2

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
        heavy = stage >= 2
        dmg = att.melee_damage(stage)
        foe.take_damage(dmg, kb_dir=att.facing, kb_force=COMBO_KB[min(stage, 2)])
        self.register_hit(att, foe, dmg, heavy=heavy)

    def cast_ability(self, f, idx, foe):
        if f.dead or f.stun_t > 0 or self.phase != "fight":
            return False
        abilities = f.h["abilities"]
        if idx < 0 or idx >= len(abilities) or f.cds[idx] > 0:
            return False
        ab = abilities[idx]
        k = ab["kind"]
        if k == "scythe" and f.scythe_out:
            return False
        f.cds[idx] = ab["cd"]
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
            self.proj.append({"kind": "orb", "owner": f, "x": f.x + f.facing * 44 * f.scale,
                              "y": f.y - 100 * f.scale, "vx": ab.get("speed", 460) * f.facing,
                              "dmg": ab.get("dmg", 12), "r": ab.get("r", 14), "color": f.h["accent"]})
        elif k == "ground":
            self.fx.append({"kind": "ground_warn", "x": foe.x, "owner": f, "t": ab.get("warn", 0.8),
                            "dmg": ab.get("dmg", 18), "dodge": ab.get("dodge", "jump"),
                            "color": f.h["glow"]})
        elif k == "shock":
            rng = ab.get("range", 170)
            self.fx.append({"kind": "shock", "owner": f, "t": 0.3, "range": rng,
                            "x0": f.x + f.facing * 30 * f.scale, "y0": f.y - 95 * f.scale})
            if not foe.dead and foe.buffs["soul"] <= 0:
                dx = (foe.x - f.x) * f.facing
                if 0 <= dx <= rng and abs(foe.y - f.y) < 170:
                    dmg = ab.get("dmg", 12) * f.out_mult()
                    foe.take_damage(dmg, kb_dir=f.facing, stun=ab.get("stun", 1.5))
                    self.parts.burst(foe.x, foe.y - 100 * foe.scale, f.h["glow"], 14, 240)
                    self.parts.dmg_text(foe.x, foe.y - 175 * foe.scale, dmg)
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
        else:
            f.cds[idx] = 0.0
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
                        dmg = pr["dmg"] * pr["owner"].out_mult()
                        foe.take_damage(dmg, kb_dir=pr["owner"].facing)
                        self.parts.dmg_text(foe.x, foe.y - 170 * foe.scale, dmg)
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
                        dmg = pr["dmg"] * 0.7 * pr["owner"].out_mult()
                        foe.take_damage(dmg, kb_dir=1 if dxx > 0 else -1)
                        self.parts.dmg_text(foe.x, foe.y - 170 * foe.scale, dmg)
            else:
                pr["x"] += pr["vx"] * dt
                if random.random() < dt * 40:
                    self.parts.trail(pr["x"], pr["y"] + random.uniform(-6, 6), pr["color"])
                if not foe.dead and foe.buffs["soul"] <= 0 and self.circ_hit(pr, foe, pr["r"] + 14):
                    dmg = pr["dmg"] * pr["owner"].out_mult()
                    foe.take_damage(dmg, kb_dir=pr["owner"].facing)
                    self.parts.burst(pr["x"], pr["y"], pr["color"], 14, 240)
                    self.parts.dmg_text(foe.x, foe.y - 170 * foe.scale, dmg)
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
            fx["t"] -= dt
            k = fx["kind"]
            if fx["t"] > 0:
                continue
            if k == "hand_warn":
                foe = self.foe_of(fx["owner"])
                if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - fx["x"]) < 62 and foe.y > GROUND_Y - 70:
                    dmg = fx["dmg"] * fx["owner"].out_mult()
                    foe.take_damage(dmg)
                    self.parts.burst(fx["x"], GROUND_Y - 50, "#e8e4d0", 14, 220)
                    self.parts.dmg_text(fx["x"], GROUND_Y - 150, dmg)
                    self.shake = max(self.shake, 5)
                fx["kind"] = "hand"
                fx["t"] = 0.5
            elif k == "ground_warn":
                foe = self.foe_of(fx["owner"])
                if not foe.dead and foe.buffs["soul"] <= 0 and abs(foe.x - fx["x"]) < 60:
                    dodge = fx.get("dodge", "jump")
                    safe = foe.crouch if dodge == "crouch" else foe.y <= GROUND_Y - 70
                    if not safe:
                        dmg = fx["dmg"] * fx["owner"].out_mult()
                        foe.take_damage(dmg)
                        self.parts.burst(fx["x"], GROUND_Y - 60, fx.get("color", "#ffd23f"), 18, 260)
                        self.parts.dmg_text(fx["x"], GROUND_Y - 170, dmg)
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
                cv.create_line(fx["x"] + ox, 0, fx["x"] + ox, GROUND_Y, fill=col, width=2,
                               dash=(4, 8), tags=("dyn",))
                r = 24 + 6 * math.sin(now * 14)
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
                cv.create_rectangle(fx["x"] - 26 * flick + ox, GROUND_Y - 230 + oy, fx["x"] + 26 * flick + ox, GROUND_Y + oy,
                                    fill=col, stipple="gray50", outline="", tags=("dyn",))
                cv.create_rectangle(fx["x"] - 12 * flick + ox, GROUND_Y - 230 + oy, fx["x"] + 12 * flick + ox, GROUND_Y + oy,
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
        for i in range(2):
            for side, wins in ((-1, self.wins_p), (1, self.wins_b)):
                cx = W / 2 + side * (44 + i * 30)
                filled = wins > i
                cv.create_oval(cx - 10, 36, cx + 10, 56,
                               fill=COL_DEEPRED if filled else "#1a0908",
                               outline=COL_GOLD if filled else COL_FRAME, width=2, tags=("dyn",))
        lvl_txt = ("БОСС · УР. %d" if self.boss else "БОТ · УР. %d") % self.level
        cv.create_text(W - 60, 110, text=lvl_txt, anchor="e", font=F_MID,
                       fill="#ff2a1a" if self.boss else COL_ORANGE, tags=("dyn",))
        cv.create_oval(44, 74, 62, 92, fill=COL_GOLD, outline="#a1700a", width=2, tags=("dyn",))
        cv.create_text(70, 83, text=str(coins), anchor="w", fill=COL_GOLD, font=F_MID, tags=("dyn",))
        total = 3 * 66 - 6
        x0 = W // 2 - total // 2
        for i in range(3):
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

        if self.p.buffs["soul"] > 0 or self.b.buffs["soul"] > 0:
            cv.create_rectangle(0, 0, W, H, fill="#1a0a2a", stipple="gray25", outline="", tags=("dyn",))

        if self.phase == "intro":
            txt = "РАУНД %d" % self.round if self.phase_t > 0.6 else "БОЙ!"
            col = COL_GOLD if self.phase_t > 0.6 else COL_RED
            self.banner(cv, txt, col)
        elif self.phase == "ko":
            self.banner(cv, "НОКАУТ!", COL_RED)
        elif self.phase == "end":
            cv.create_rectangle(0, 0, W, H, fill="#0a0202", stipple="gray50", outline="", tags=("dyn",))
            cv.create_rectangle(W / 2 - 340, 170, W / 2 + 340, 560, fill=COL_DARK, outline=COL_GOLD,
                                width=3, tags=("dyn",))
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
