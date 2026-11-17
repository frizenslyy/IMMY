"""IMMY — ИИ бота: тактики, комбо-мышление, уклонения и выбор способностей."""

import random

from .util import clamp


class BotAI:
    def __init__(self, f, level):
        self.f = f
        self.level = level
        self.t = 0.6
        self.move = 0
        self.want_attack = False
        self.jump = False
        self.crouch = False
        self.tactic = "rush"

    def dodge_check(self, game, foe):
        f = self.f
        if not f.on_ground:
            return
        for fx in game.fx:
            k = fx.get("kind", "")
            dx = abs(fx.get("x", -9999) - f.x)
            if k in ("hand_warn", "geyser_warn") and dx < 75:
                self.jump = True
                return
            if k == "ground_warn" and dx < 70:
                if fx.get("dodge") == "crouch":
                    self.crouch = True
                else:
                    self.jump = True
                return
        for pr in game.proj:
            if pr["owner"] is foe:
                dx = abs(pr["x"] - f.x)
                toward = (pr.get("vx", 0) or 0) * (f.x - pr["x"]) > 0
                if dx < 230 and toward:
                    self.jump = True
                    return

    def punish(self, dist, foe, game):
        f = self.f
        frac = foe.hp / foe.max_hp if foe.max_hp else 1.0
        if frac <= 0.25 and game.myth_ready(f, foe):
            if game.try_myth_ult(f, foe):
                return True
        for i, ab in enumerate(f.h["abilities"]):
            if ab["kind"] == "ult" and f.cds[i] <= 0 and frac < 0.10:
                dx = (foe.x - f.x) * f.facing
                if 0 <= dx <= ab.get("range", 200) and game.cast_ability(f, i, foe):
                    return True
        if f.special_cd <= 0 and self.level >= 2:
            for sp in f.h.get("specials", ()):
                if f.energy < sp["cost"] or f.sp_cds.get(sp["combo"], 0.0) > 0:
                    continue
                k = sp["kind"]
                if k in ("grab", "strike", "vortex", "geyser") or dist < 300:
                    if game.cast_special(f, sp["combo"], foe):
                        return True
        self.want_attack = True
        return False

    def pick_tactic(self, foe):
        kinds = {ab["kind"] for ab in self.f.h["abilities"]}
        has_range = bool(kinds & {"orb", "wave", "rain", "beam", "hand", "poison",
                                  "tide", "geyser", "vortex", "scythe", "snare"})
        frac = foe.hp / foe.max_hp if foe.max_hp else 1.0
        if frac < 0.25:
            self.tactic = "rush"
        elif has_range and random.random() < 0.45:
            self.tactic = "poke"
        else:
            self.tactic = "rush" if random.random() < 0.6 else "poke"

    def update(self, dt, foe, game):
        f = self.f
        if f.dead or f.stun_t > 0 or game.phase != "fight":
            f.vx_target = 0.0
            return
        if f.root_t > 0:
            f.vx_target = 0.0
            f.crouch = False
            return
        dist = abs(foe.x - f.x)
        d = 1 if foe.x > f.x else -1
        if foe.attack_t > 0 and dist < 180 and f.parry_cd <= 0:
            if random.random() < self.level * 0.010:
                f.try_parry()
        if foe.stun_t > 0.3 or foe.root_t > 0.3:
            self.punish(dist, foe, game)
        self.t -= dt
        if self.t <= 0:
            self.t = f.reaction * random.uniform(0.7, 1.4)
            self.think(dist, d, foe, game)
        self.dodge_check(game, foe)
        f.vx_target = self.move * 280 * f.eff_speed()
        f.crouch = self.crouch and f.on_ground
        if self.jump:
            self.jump = False
            if f.on_ground and not f.crouch:
                f.vy = -960.0
                f.on_ground = False
        if self.want_attack:
            self.want_attack = False
            if dist < 150 and self.level >= 2 and f.attack_cd <= 0 and f.attack_t <= 0:
                r = random.random()
                if r < 0.12:
                    f.try_strike("kick", game)
                elif r < 0.20:
                    f.try_strike("upper", game)
                elif f.crouch and r < 0.28:
                    f.try_strike("sweep", game)
                else:
                    f.start_attack(game)
            else:
                f.start_attack(game)

    def think(self, dist, d, foe, game):
        f = self.f
        aggr = clamp(0.35 + self.level * 0.03, 0.35, 0.9)
        r = random.random()
        self.crouch = False
        if random.random() < 0.3:
            self.pick_tactic(foe)
        if self.tactic == "poke":
            if dist < 200:
                self.move = -d
            elif dist > 340:
                self.move = d
            else:
                self.move = random.choice((-d, 0, d)) if random.random() < 0.4 else 0
            if dist < 130 and r < 0.5:
                self.want_attack = True
        else:
            if dist > 130:
                self.move = d
                if random.random() < 0.22:
                    self.jump = True
            else:
                if r < aggr:
                    self.want_attack = True
                    self.move = 0
                elif r < aggr + 0.25:
                    self.move = -d
                else:
                    self.move = 0
                    if random.random() < 0.3:
                        self.crouch = True
        self.cast_logic(dist, foe, game)

    def cast_logic(self, dist, foe, game):
        f = self.f
        low_hp = f.hp < f.max_hp * 0.5
        if self.level >= 2 and f.special_cd <= 0 and random.random() < 0.35:
            for sp in f.h.get("specials", ()):
                if f.energy < sp["cost"] or f.sp_cds.get(sp["combo"], 0.0) > 0:
                    continue
                k = sp["kind"]
                if k in ("grab", "strike"):
                    ok = dist < sp.get("range", 240)
                elif k == "vortex":
                    ok = dist < 300
                elif k in ("tide", "wave", "orb", "barrage", "rain"):
                    ok = dist > 180
                elif k == "geyser":
                    ok = dist > 100
                elif k == "heal":
                    ok = low_hp
                elif k in ("buff_atk", "buff_def", "buff_spd", "summon"):
                    ok = dist < 340
                else:
                    ok = dist > 180
                if ok and game.cast_special(f, sp["combo"], foe):
                    return
        try_c = game.cast_ability
        for i, ab in enumerate(f.h["abilities"]):
            if f.cds[i] > 0:
                continue
            k = ab["kind"]
            if k == "ult":
                frac = foe.hp / foe.max_hp if foe.max_hp else 1.0
                dx = (foe.x - f.x) * f.facing
                if frac < 0.10 and 0 <= dx <= ab.get("range", 200):
                    try_c(f, i, foe)
                    return
            elif k == "geyser":
                if dist > 100 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "vortex":
                if dist < 320 and random.random() < 0.55:
                    try_c(f, i, foe)
                    return
            elif k == "tide":
                if dist > 200 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "scythe":
                if not f.scythe_out and dist > 260 and random.random() < 0.6:
                    try_c(f, i, foe)
                    return
            elif k == "hand":
                if dist > 180 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "soul":
                if (low_hp or dist < 90) and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "orb":
                if dist > 220 and random.random() < 0.6:
                    try_c(f, i, foe)
                    return
            elif k == "ground":
                if dist > 140 and random.random() < 0.45:
                    try_c(f, i, foe)
                    return
            elif k == "shock":
                if dist < ab.get("range", 170) and random.random() < 0.6:
                    try_c(f, i, foe)
                    return
            elif k == "blink":
                if (dist < 110 or low_hp) and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "heal":
                if low_hp and random.random() < 0.7:
                    try_c(f, i, foe)
                    return
            elif k == "buff_def":
                if low_hp and random.random() < 0.6:
                    try_c(f, i, foe)
                    return
            elif k == "buff_atk":
                if dist < 260 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "buff_spd":
                if dist > 300 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "wave":
                if dist > 200 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "rain":
                if dist > 140 and random.random() < 0.45:
                    try_c(f, i, foe)
                    return
            elif k == "snare":
                if dist > 160 and random.random() < 0.55:
                    try_c(f, i, foe)
                    return
            elif k == "summon":
                if dist < 340 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "poison":
                if dist < ab.get("range", 420) and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "strike":
                if dist < ab.get("range", 150) and random.random() < 0.6:
                    try_c(f, i, foe)
                    return
            elif k == "pull":
                if dist > 240 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "guard":
                if foe.attack_t > 0 and dist < 200 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "drain":
                if dist < ab.get("range", 220) and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "drain_aura":
                if dist < 280 and random.random() < 0.5:
                    try_c(f, i, foe)
                    return
            elif k == "leap":
                if dist > 200 and random.random() < 0.45:
                    try_c(f, i, foe)
                    return
            elif k == "beam":
                if dist < ab.get("range", 520) and random.random() < 0.55:
                    try_c(f, i, foe)
                    return
