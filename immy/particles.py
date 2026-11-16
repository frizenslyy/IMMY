"""IMMY — система частиц с лимитами: искры, пыль, взрывы, всплывающий урон, угольки."""

import math
import random
import time

from .config import COL_GOLD, H, MAX_EMBERS, MAX_PARTS, W


def update_parts(lst, dt):
    for q in lst[:]:
        q["t"] -= dt
        if q["t"] <= 0:
            lst.remove(q)
            continue
        if q.get("kind") == "text":
            q["y"] += q["vy"] * dt
        else:
            q["x"] += q["vx"] * dt
            q["y"] += q["vy"] * dt
            q["vy"] += q.get("g", 500) * dt


class Particles:
    def __init__(self):
        self.items = []

    def _room(self, n):
        return max(0, min(n, MAX_PARTS - len(self.items)))

    def burst(self, x, y, color, n=10, sp=180):
        n = self._room(n)
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * sp
            self.items.append({"x": x, "y": y, "vx": math.cos(a) * v, "vy": math.sin(a) * v - 60,
                               "t": random.uniform(0.3, 0.7), "life": 0.7,
                               "color": color, "r": random.uniform(2, 4.5), "g": 600})

    def spark(self, x, y):
        if not self._room(1):
            return
        self.items.append({"x": x, "y": y, "vx": random.uniform(-40, 40), "vy": random.uniform(-80, -20),
                           "t": 0.3, "life": 0.3, "color": "#fff7b0", "r": 2.5, "g": 0})

    def dust(self, x, y, n=3):
        n = self._room(n)
        for _ in range(n):
            self.items.append({"x": x + random.uniform(-16, 16), "y": y,
                               "vx": random.uniform(-60, 60), "vy": random.uniform(-50, -10),
                               "t": 0.3, "life": 0.3, "color": "#8a4a20", "r": 2.5, "g": 300})

    def trail(self, x, y, color):
        if not self._room(1):
            return
        self.items.append({"x": x, "y": y, "vx": random.uniform(-15, 15), "vy": random.uniform(-40, 10),
                           "t": 0.3, "life": 0.3, "color": color, "r": 3.0, "g": 0})

    def rise(self, x, y, color):
        if not self._room(1):
            return
        self.items.append({"x": x + random.uniform(-20, 20), "y": y - random.uniform(20, 140),
                           "vx": random.uniform(-15, 15), "vy": random.uniform(-90, -40),
                           "t": 0.9, "life": 0.9, "color": color, "r": 3.0, "g": -60})

    def dmg_text(self, x, y, n, color=COL_GOLD, big=False, txt=None):
        if not self._room(1):
            return
        self.items.append({"kind": "text", "x": x, "y": y, "vy": -80, "t": 0.9, "life": 0.9,
                           "txt": txt if txt is not None else str(int(n)), "color": color, "big": big})

    def ring(self, x, y, color, r0=6, r1=46, t=0.35):
        if not self._room(1):
            return
        self.items.append({"kind": "ring", "x": x, "y": y, "vx": 0, "vy": 0, "g": 0,
                           "t": t, "life": t, "color": color, "r": r0, "r1": r1})

    def update(self, dt):
        update_parts(self.items, dt)

    def clear(self):
        self.items = []

    def draw(self, cv, ox=0.0, oy=0.0):
        for q in self.items:
            if q.get("kind") == "text":
                f = ("Courier", 20, "bold") if q.get("big") else ("Courier", 16, "bold")
                cv.create_text(q["x"] + ox + 2, q["y"] + oy + 2, text=q["txt"],
                               fill="#2a0503", font=f, tags=("dyn",))
                cv.create_text(q["x"] + ox, q["y"] + oy, text=q["txt"],
                               fill=q.get("color", COL_GOLD), font=f, tags=("dyn",))
            elif q.get("kind") == "ring":
                k = 1.0 - q["t"] / q["life"]
                r = q["r"] + (q["r1"] - q["r"]) * k
                w = max(1, int(4 * (1.0 - k)))
                cv.create_oval(q["x"] - r + ox, q["y"] - r + oy, q["x"] + r + ox, q["y"] + r + oy,
                               outline=q["color"], width=w, tags=("dyn",))
            else:
                r = q["r"] * max(0.35, q["t"] / q["life"])
                cv.create_oval(q["x"] - r + ox, q["y"] - r + oy, q["x"] + r + ox, q["y"] + r + oy,
                               fill=q["color"], outline="", tags=("dyn",))


class Embers:
    def __init__(self, n=MAX_EMBERS):
        self.items = [{"x": random.uniform(0, W), "y": random.uniform(0, H),
                       "v": random.uniform(18, 55), "w": random.uniform(0.5, 2.0),
                       "ph": random.uniform(0, 6.28), "r": random.uniform(1.2, 2.6),
                       "c": random.choice(("#ff5a1a", "#ff8c1a", "#ffd23f", "#b3341a"))}
                      for _ in range(n)]

    def update(self, dt):
        now = time.time()
        for em in self.items:
            em["y"] -= em["v"] * dt
            em["x"] += math.sin(now * em["w"] + em["ph"]) * 14 * dt
            if em["y"] < -12:
                em["x"] = random.uniform(0, W)
                em["y"] = H + 12
                em["v"] = random.uniform(18, 55)

    def draw(self, cv):
        for em in self.items:
            cv.create_oval(em["x"] - em["r"], em["y"] - em["r"], em["x"] + em["r"], em["y"] + em["r"],
                           fill=em["c"], outline="", tags=("dyn",))
