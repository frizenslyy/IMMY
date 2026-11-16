"""IMMY — карты арен, фоны, иконки героев и портреты."""

import math
import random

from .config import (COL_GOLD, COL_SAND, F_SMALL, F_TITLE,
                     GROUND_Y, H, MENU_STOPS, W)
from .heroes import HEROES
from .util import gradient

MAPS = [
    {"name": "ВУЛКАН",
     "stops": [(0.0, (16, 3, 8)), (0.55, (88, 14, 10)), (1.0, (190, 62, 16))],
     "moon": "#ff5a1a", "moon_cr": "#e8431a",
     "pillar": "#160607", "pillar_top": "#24100c",
     "floor": "#200c08", "floor_line": "#ff5a1a", "tile": "#2c120a",
     "torch": ("#ff5a1a", "#ff8c1a", "#ffd23f"),
     "mountain": "#3a0e0a", "mountain2": "#240806", "stars": False, "deco": "embers"},
    {"name": "ЛЕДНИК",
     "stops": [(0.0, (6, 14, 30)), (0.55, (26, 64, 96)), (1.0, (110, 170, 210))],
     "moon": "#cfe8ff", "moon_cr": "#a8ccec",
     "pillar": "#16324a", "pillar_top": "#22486a",
     "floor": "#14283a", "floor_line": "#7fd4ff", "tile": "#1a3a50",
     "torch": ("#7fd4ff", "#a8e4ff", "#e0f6ff"),
     "mountain": "#1e4260", "mountain2": "#122c44", "stars": True, "deco": "stars"},
    {"name": "ПУСТЫНЯ",
     "stops": [(0.0, (26, 16, 6)), (0.55, (110, 70, 20)), (1.0, (232, 192, 90))],
     "moon": "#ffd23f", "moon_cr": "#e8a83a",
     "pillar": "#4a3418", "pillar_top": "#5e4420",
     "floor": "#3a2a10", "floor_line": "#e8a83a", "tile": "#463414",
     "torch": ("#ff8c1a", "#e8a83a", "#ffd23f"),
     "mountain": "#6a481c", "mountain2": "#4a3010", "stars": False, "deco": "dust"},
    {"name": "НОЧНОЙ ЛЕС",
     "stops": [(0.0, (4, 14, 8)), (0.55, (12, 48, 24)), (1.0, (42, 106, 52))],
     "moon": "#baffd4", "moon_cr": "#8ae0b0",
     "pillar": "#0e2414", "pillar_top": "#16341e",
     "floor": "#0c1c10", "floor_line": "#4ad16a", "tile": "#12281a",
     "torch": ("#4ad16a", "#8ae05a", "#d2ff8a"),
     "mountain": "#0c2818", "mountain2": "#081c10", "stars": True, "deco": "spores"},
    {"name": "МИР ТЕНЕЙ",
     "stops": [(0.0, (8, 4, 18)), (0.55, (36, 18, 60)), (1.0, (106, 58, 138))],
     "moon": "#b08aff", "moon_cr": "#8a5ad1",
     "pillar": "#1a1030", "pillar_top": "#281a48",
     "floor": "#140c24", "floor_line": "#8a5ad1", "tile": "#1e1436",
     "torch": ("#8a5ad1", "#b08aff", "#d8c0ff"),
     "mountain": "#241440", "mountain2": "#160c2c", "stars": True, "deco": "stars"},
]


def draw_hero_icon(cv, key, x, y, size, border=True):
    hero = HEROES[key]
    if border:
        cv.create_rectangle(x, y, x + size, y + size, fill="#160607", outline="#5a1c10", width=2, tags=("dyn",))
    hx = x + size * 0.32
    hy = y + size * 0.16
    hw = size * 0.36
    cv.create_rectangle(hx, hy, hx + hw, hy + hw, fill=hero["body"], outline="", tags=("dyn",))
    cv.create_rectangle(hx + hw * 0.25, hy + hw * 0.35, hx + hw * 0.5, hy + hw * 0.55,
                        fill=hero["accent"], outline="", tags=("dyn",))
    cv.create_rectangle(hx + hw * 0.65, hy + hw * 0.35, hx + hw * 0.85, hy + hw * 0.55,
                        fill=hero["accent"], outline="", tags=("dyn",))
    cv.create_rectangle(x + size * 0.16, y + size * 0.58, x + size * 0.84, y + size * 0.95,
                        fill=hero["body2"], outline="", tags=("dyn",))
    if hero["style"] == "hood":
        cv.create_polygon(hx - 4, hy + hw, hx + hw + 4, hy + hw, hx + hw / 2, hy - 8,
                          fill=hero["body"], outline="", tags=("dyn",))
    elif hero["style"] == "glow":
        cv.create_rectangle(hx - 4, hy - 4, hx + hw + 4, hy + hw + 4, outline=hero["glow"],
                            width=2, tags=("dyn",), stipple="gray50")
    elif hero["style"] == "flame":
        cv.create_polygon(hx + hw / 2 - 6, hy, hx + hw / 2 + 6, hy, hx + hw / 2, hy - 12,
                          fill=hero["accent"], outline="", tags=("dyn",))
    elif hero["style"] == "spike":
        for i in range(3):
            sx = hx + hw * (0.15 + 0.35 * i)
            cv.create_polygon(sx - 4, hy, sx + 4, hy, sx, hy - 10,
                              fill=hero["glow"], outline="", tags=("dyn",))
    elif hero["style"] == "spider":
        for sgn in (-1, 1):
            for i, dy in enumerate((6, 12, 18)):
                cv.create_line(hx + (hw if sgn > 0 else 0), hy + hw * 0.5 + dy,
                               hx + hw / 2 + sgn * (hw * 0.9 + i * 4), hy + hw * 0.5 + dy + 8,
                               fill=hero["accent"], width=2, tags=("dyn",))
        cv.create_rectangle(hx + hw * 0.2, hy + hw * 0.3, hx + hw * 0.42, hy + hw * 0.45,
                            fill=hero["eye"], outline="", tags=("dyn",))
        cv.create_rectangle(hx + hw * 0.58, hy + hw * 0.3, hx + hw * 0.8, hy + hw * 0.45,
                            fill=hero["eye"], outline="", tags=("dyn",))


def draw_menu_bg(cv):
    gradient(cv, 0, 0, W, H, MENU_STOPS)
    cv.create_rectangle(14, 14, W - 14, H - 14, outline="#7a1c10", width=3, tags=("bg",))
    cv.create_rectangle(22, 22, W - 22, H - 22, outline="#4a0e08", width=1, tags=("bg",))
    for cx, cy in ((14, 14), (W - 14, 14), (14, H - 14), (W - 14, H - 14)):
        d = 16
        cv.create_polygon(cx, cy - d, cx + d, cy, cx, cy + d, cx - d, cy,
                          fill="", outline=COL_GOLD, width=2, tags=("bg",))
        cv.create_polygon(cx, cy - 8, cx + 8, cy, cx, cy + 8, cx - 8, cy,
                          fill=COL_GOLD, outline="", tags=("bg",))
    cv.create_oval(W / 2 - 260, 30, W / 2 + 260, 210, fill="#ff8c1a", outline="",
                   tags=("bg",), stipple="gray12")
    cv.create_oval(W / 2 - 190, 50, W / 2 + 190, 190, fill="#ffd23f", outline="",
                   tags=("bg",), stipple="gray12")
    cv.create_text(W / 2 + 6, 126, text="IMMY", font=F_TITLE, fill="#2a0503", tags=("bg",))
    cv.create_text(W / 2, 120, text="IMMY", font=F_TITLE, fill=COL_GOLD, tags=("bg",))
    cv.create_polygon(W / 2 - 300, 175, W / 2 - 288, 175, W / 2 - 294, 167, fill=COL_GOLD, outline="", tags=("bg",))
    cv.create_polygon(W / 2 + 300, 175, W / 2 + 288, 175, W / 2 + 294, 167, fill=COL_GOLD, outline="", tags=("bg",))
    cv.create_rectangle(W / 2 - 270, 172, W / 2 + 270, 178, fill="#7a1c10", outline="", tags=("bg",))
    cv.create_text(W / 2, 202, text="PIXEL FIGHTING", font=F_SMALL, fill=COL_SAND, tags=("bg",))


def draw_screen_bg(cv):
    gradient(cv, 0, 0, W, H, MENU_STOPS)


def draw_fight_bg(cv, m):
    gradient(cv, 0, 0, W, GROUND_Y, m["stops"], steps=70)
    if m.get("stars"):
        rnd = random.Random(11)
        for _ in range(40):
            sx, sy = rnd.uniform(0, W), rnd.uniform(0, GROUND_Y - 180)
            r = rnd.uniform(1.0, 2.4)
            cv.create_oval(sx - r, sy - r, sx + r, sy + r, fill="#fff7d0", outline="", tags=("bg",))
    cv.create_oval(W - 310, 55, W - 140, 225, fill=m["moon"], outline=COL_GOLD, width=4, tags=("bg",))
    cv.create_oval(W - 275, 95, W - 245, 125, fill=m["moon_cr"], outline="", tags=("bg",))
    cv.create_oval(W - 215, 150, W - 190, 175, fill=m["moon_cr"], outline="", tags=("bg",))
    cv.create_polygon(-40, GROUND_Y, 180, GROUND_Y - 300, 340, GROUND_Y - 170, 430, GROUND_Y - 260,
                      620, GROUND_Y, fill=m["mountain"], outline="", tags=("bg",))
    cv.create_polygon(560, GROUND_Y, 800, GROUND_Y - 230, 980, GROUND_Y - 310, 1160, GROUND_Y - 190,
                      W + 40, GROUND_Y, fill=m["mountain"], outline="", tags=("bg",))
    cv.create_polygon(-40, GROUND_Y, 120, GROUND_Y - 180, 300, GROUND_Y - 90, 480, GROUND_Y,
                      fill=m["mountain2"], outline="", tags=("bg",))
    cv.create_polygon(700, GROUND_Y, 900, GROUND_Y - 150, 1100, GROUND_Y - 70, W + 40, GROUND_Y,
                      fill=m["mountain2"], outline="", tags=("bg",))
    for px in (60, W - 60):
        cv.create_rectangle(px - 26, GROUND_Y - 330, px + 26, GROUND_Y, fill=m["pillar"], outline="", tags=("bg",))
        cv.create_rectangle(px - 32, GROUND_Y - 338, px + 32, GROUND_Y - 326, fill=m["pillar_top"], outline="", tags=("bg",))
    cv.create_rectangle(0, GROUND_Y, W, H, fill=m["floor"], outline="", tags=("bg",))
    cv.create_rectangle(0, GROUND_Y, W, GROUND_Y + 6, fill=m["floor_line"], outline="", tags=("bg",))
    for fy, sh in ((GROUND_Y + 24, 0.35), (GROUND_Y + 54, 0.62), (GROUND_Y + 84, 0.85)):
        inset = int(300 * sh)
        cv.create_line(inset, fy, W - inset, fy, fill=m["floor_line"], width=1,
                       tags=("bg",), stipple="gray25")
    rnd = random.Random(7)
    for _ in range(46):
        x = rnd.uniform(0, W)
        y = rnd.uniform(GROUND_Y + 16, H - 10)
        w2 = rnd.uniform(8, 30)
        cv.create_rectangle(x, y, x + w2, y + 4, fill=m["tile"], outline="", tags=("bg",))
    for tx in (150, W - 150):
        cv.create_rectangle(tx - 6, GROUND_Y - 200, tx + 6, GROUND_Y - 110, fill="#4a2410", outline="", tags=("bg",))
        cv.create_rectangle(tx - 14, GROUND_Y - 212, tx + 14, GROUND_Y - 196, fill="#6b4a2a", outline="", tags=("bg",))


def draw_ambient(cv, t, m):
    deco = m.get("deco", "embers")
    if deco == "embers":
        cols = ("#ff5a1a", "#ff8c1a", "#ffd23f")
    elif deco == "stars":
        cols = ("#fff7d0", "#dfe6ff")
    elif deco == "spores":
        cols = ("#8ae05a", "#d2ff8a")
    else:
        cols = ("#e8c98a", "#c9a15a")
    for i in range(18):
        ph = i * 2.39
        x = (i * 137 + math.sin(t * 0.5 + ph) * 60) % W
        y = (GROUND_Y - 40 - (i * 53 + t * (14 + i % 5 * 6)) % 420)
        r = 1.4 + (i % 3) * 0.7
        c = cols[i % len(cols)]
        cv.create_oval(x - r, y - r, x + r, y + r, fill=c, outline="", tags=("dyn",))


def draw_torches(cv, time_now, m):
    cols = m["torch"]
    for tx in (150, W - 150):
        base_y = GROUND_Y - 204
        for i, (dxo, hgt) in enumerate(((-7, 26), (0, 34), (7, 22))):
            tip = base_y - hgt - 6 * math.sin(time_now * 10 + i * 2.1 + tx)
            cv.create_polygon(tx + dxo - 6, base_y, tx + dxo + 6, base_y, tx + dxo, tip,
                              fill=cols[i], outline="", tags=("dyn",))
