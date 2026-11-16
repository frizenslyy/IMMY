"""IMMY — ИИ бота: реакция, агрессия, уклонения от снарядов и небесных атак."""

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
            if k == "bolt_warn" and dx < 70:
                self.crouch = True
                return
            if k in ("hand_warn", "pillar_warn") and dx < 75:
                self.jump = True
                return
        for pr in game.proj:
            if pr["owner"] is not foe:
                continue
            toward = (pr["x"] - f.x) * (pr.get("vx", 0) or 0) > 0 or (pr.get("vx", 0) * (f.x - pr["x"]) > 0)
            dx = abs(pr["x"] - f.x)
            if dx < 230 and toward:
                self.jump = True
                return

    def update(self, dt, foe, game):
        f = self.f
        if f.dead or f.stun_t > 0 or game.phase != "fight":
            f.vx = 0.0
            return
        self.t -= dt
        dist = abs(foe.x - f.x)
        d = 1 if foe.x > f.x else -1
        if self.t <= 0:
            self.t = f.reaction * random.uniform(0.7, 1.4)
            self.think(dist, d, foe, game)
        self.dodge_check(game, foe)
        f.vx = self.move * 270 * f.speed_mult
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
        if f.key == "DEADY":
            if not f.scythe_out and dist > 260 and f.cds[0] <= 0 and random.random() < 0.6:
                try_c(f, 0, foe)
            elif dist > 180 and f.cds[1] <= 0 and random.random() < 0.5:
                try_c(f, 1, foe)
            elif (low_hp or dist < 90) and f.cds[2] <= 0 and random.random() < 0.5:
                try_c(f, 2, foe)
        elif f.key == "LIGHTY":
            if dist < 170 and f.cds[0] <= 0 and random.random() < 0.6:
                try_c(f, 0, foe)
            elif dist > 200 and f.cds[1] <= 0 and random.random() < 0.55:
                try_c(f, 1, foe)
            elif low_hp and f.cds[2] <= 0:
                try_c(f, 2, foe)
        else:
            if dist > 240 and f.cds[0] <= 0 and random.random() < 0.6:
                try_c(f, 0, foe)
            elif 140 < dist < 420 and f.cds[1] <= 0 and random.random() < 0.5:
                try_c(f, 1, foe)
            elif dist < 200 and f.cds[2] <= 0 and (low_hp or random.random() < 0.3):
                try_c(f, 2, foe)
