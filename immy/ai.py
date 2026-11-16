"""IMMY — ИИ бота: реакция, агрессия, уклонения и универсальный выбор способностей."""

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

    def dodge_check(self, game, foe):
        f = self.f
        if not f.on_ground:
            return
        for fx in game.fx:
            k = fx.get("kind", "")
            dx = abs(fx.get("x", -9999) - f.x)
            if k == "hand_warn" and dx < 75:
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

    def update(self, dt, foe, game):
        f = self.f
        if f.dead or f.stun_t > 0 or game.phase != "fight":
            f.vx_target = 0.0
            return
        self.t -= dt
        dist = abs(foe.x - f.x)
        d = 1 if foe.x > f.x else -1
        if self.t <= 0:
            self.t = f.reaction * random.uniform(0.7, 1.4)
            self.think(dist, d, foe, game)
        self.dodge_check(game, foe)
        f.vx_target = self.move * 270 * f.speed_mult
        f.crouch = self.crouch and f.on_ground
        if self.jump:
            self.jump = False
            if f.on_ground and not f.crouch:
                f.vy = -900.0
                f.on_ground = False
        if self.want_attack:
            self.want_attack = False
            f.start_attack(game)

    def think(self, dist, d, foe, game):
        f = self.f
        aggr = clamp(0.35 + self.level * 0.03, 0.35, 0.9)
        r = random.random()
        self.crouch = False
        if dist > 240:
            self.move = d
            if random.random() < 0.22:
                self.jump = True
        elif dist > 130:
            self.move = d if r < aggr else -d
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
        try_c = game.cast_ability
        for i, ab in enumerate(f.h["abilities"]):
            if f.cds[i] > 0:
                continue
            k = ab["kind"]
            if k == "scythe":
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
