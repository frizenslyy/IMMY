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
     "torch": ("#ff5a1a", "#ff8c1a", "#ffd23f")},
    {"name": "ЛЕДНИК",
     "stops": [(0.0, (6, 14, 30)), (0.55, (26, 64, 96)), (1.0, (110, 170, 210))],
     "moon": "#cfe8ff", "moon_cr": "#a8ccec",
     "pillar": "#16324a", "pillar_top": "#22486a",
     "floor": "#14283a", "floor_line": "#7fd4ff", "tile": "#1a3a50",
     "torch": ("#7fd4ff", "#a8e4ff", "#e0f6ff")},
    {"name": "ПУСТЫНЯ",
     "stops": [(0.0, (26, 16, 6)), (0.55, (110, 70, 20)), (1.0, (232, 192, 90))],
     "moon": "#ffd23f", "moon_cr": "#e8a83a",
     "pillar": "#4a3418", "pillar_top": "#5e4420",
     "floor": "#3a2a10", "floor_line": "#e8a83a", "tile": "#463414",
     "torch": ("#ff8c1a", "#e8a83a", "#ffd23f")},
    {"name": "НОЧНОЙ ЛЕС",
     "stops": [(0.0, (4, 14, 8)), (0.55, (12, 48, 24)), (1.0, (42, 106, 52))],
     "moon": "#baffd4", "moon_cr": "#8ae0b0",
     "pillar": "#0e2414", "pillar_top": "#16341e",
     "floor": "#0c1c10", "floor_line": "#4ad16a", "tile": "#12281a",
     "torch": ("#4ad16a", "#8ae05a", "#d2ff8a")},
    {"name": "МИР ТЕНЕЙ",
     "stops": [(0.0, (8, 4, 18)), (0.55, (36, 18, 60)), (1.0, (106, 58, 138))],
     "moon": "#b08aff", "moon_cr": "#8a5ad1",
     "pillar": "#1a1030", "pillar_top": "#281a48",
     "floor": "#140c24", "floor_line": "#8a5ad1", "tile": "#1e1436",
     "torch": ("#8a5ad1", "#b08aff", "#d8c0ff")},
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


def draw_menu_bg(cv):
    gradient(cv, 0, 0, W, H, MENU_STOPS)
    cv.create_text(W / 2 + 5, 125, text="IMMY", font=F_TITLE, fill="#2a0503", tags=("bg",))
    cv.create_text(W / 2, 120, text="IMMY", font=F_TITLE, fill=COL_GOLD, tags=("bg",))
    cv.create_rectangle(W / 2 - 270, 172, W / 2 + 270, 178, fill="#7a1c10", outline="", tags=("bg",))
    cv.create_text(W / 2, 202, text="PIXEL FIGHTING", font=F_SMALL, fill=COL_SAND, tags=("bg",))


def draw_screen_bg(cv):
    gradient(cv, 0, 0, W, H, MENU_STOPS)


def draw_fight_bg(cv, m):
    gradient(cv, 0, 0, W, GROUND_Y, m["stops"], steps=70)
    cv.create_oval(W - 310, 55, W - 140, 225, fill=m["moon"], outline=COL_GOLD, width=4, tags=("bg",))
    cv.create_oval(W - 275, 95, W - 245, 125, fill=m["moon_cr"], outline="", tags=("bg",))
    cv.create_oval(W - 215, 150, W - 190, 175, fill=m["moon_cr"], outline="", tags=("bg",))
    for px in (60, W - 60):
        cv.create_rectangle(px - 26, GROUND_Y - 330, px + 26, GROUND_Y, fill=m["pillar"], outline="", tags=("bg",))
        cv.create_rectangle(px - 32, GROUND_Y - 338, px + 32, GROUND_Y - 326, fill=m["pillar_top"], outline="", tags=("bg",))
    cv.create_rectangle(0, GROUND_Y, W, H, fill=m["floor"], outline="", tags=("bg",))
    cv.create_rectangle(0, GROUND_Y, W, GROUND_Y + 6, fill=m["floor_line"], outline="", tags=("bg",))
    rnd = random.Random(7)
    for _ in range(46):
        x = rnd.uniform(0, W)
        y = rnd.uniform(GROUND_Y + 16, H - 10)
        w2 = rnd.uniform(8, 30)
        cv.create_rectangle(x, y, x + w2, y + 4, fill=m["tile"], outline="", tags=("bg",))
    for tx in (150, W - 150):
        cv.create_rectangle(tx - 6, GROUND_Y - 200, tx + 6, GROUND_Y - 110, fill="#4a2410", outline="", tags=("bg",))
        cv.create_rectangle(tx - 14, GROUND_Y - 212, tx + 14, GROUND_Y - 196, fill="#6b4a2a", outline="", tags=("bg",))


def draw_torches(cv, time_now, m):
    cols = m["torch"]
    for tx in (150, W - 150):
        base_y = GROUND_Y - 204
        for i, (dxo, hgt) in enumerate(((-7, 26), (0, 34), (7, 22))):
            tip = base_y - hgt - 6 * math.sin(time_now * 10 + i * 2.1 + tx)
            cv.create_polygon(tx + dxo - 6, base_y, tx + dxo + 6, base_y, tx + dxo, tip,
                              fill=cols[i], outline="", tags=("dyn",))
