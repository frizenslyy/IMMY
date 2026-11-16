"""IMMY — фоны, иконки героев и портреты."""

import math
import random

from .config import (COL_GOLD, COL_ORANGE, COL_SAND, FIGHT_STOPS, F_SMALL, F_TITLE,
                     GROUND_Y, H, MENU_STOPS, W)
from .heroes import HEROES
from .util import gradient


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
    if key == "DEADY":
        cv.create_polygon(hx - 4, hy + hw, hx + hw + 4, hy + hw, hx + hw / 2, hy - 8,
                          fill=hero["body"], outline="", tags=("dyn",))
    elif key == "LIGHTY":
        cv.create_rectangle(hx - 4, hy - 4, hx + hw + 4, hy + hw + 4, outline=hero["glow"],
                            width=2, tags=("dyn",), stipple="gray50")
    else:
        cv.create_polygon(hx + hw / 2 - 6, hy, hx + hw / 2 + 6, hy, hx + hw / 2, hy - 12,
                          fill=hero["accent"], outline="", tags=("dyn",))


def draw_menu_bg(cv):
    gradient(cv, 0, 0, W, H, MENU_STOPS)
    cv.create_text(W / 2 + 5, 125, text="IMMY", font=F_TITLE, fill="#2a0503", tags=("bg",))
    cv.create_text(W / 2, 120, text="IMMY", font=F_TITLE, fill=COL_GOLD, tags=("bg",))
    cv.create_rectangle(W / 2 - 270, 172, W / 2 + 270, 178, fill="#7a1c10", outline="", tags=("bg",))
    cv.create_text(W / 2, 202, text="PIXEL FIGHTING", font=F_SMALL, fill=COL_SAND, tags=("bg",))


def draw_fight_bg(cv):
    gradient(cv, 0, 0, W, GROUND_Y, FIGHT_STOPS, steps=70)
    cv.create_oval(W - 310, 55, W - 140, 225, fill="#ff5a1a", outline=COL_GOLD, width=4, tags=("bg",))
    cv.create_oval(W - 275, 95, W - 245, 125, fill="#e8431a", outline="", tags=("bg",))
    cv.create_oval(W - 215, 150, W - 190, 175, fill="#e8431a", outline="", tags=("bg",))
    for px in (60, W - 60):
        cv.create_rectangle(px - 26, GROUND_Y - 330, px + 26, GROUND_Y, fill="#160607", outline="", tags=("bg",))
        cv.create_rectangle(px - 32, GROUND_Y - 338, px + 32, GROUND_Y - 326, fill="#24100c", outline="", tags=("bg",))
    cv.create_rectangle(0, GROUND_Y, W, H, fill="#200c08", outline="", tags=("bg",))
    cv.create_rectangle(0, GROUND_Y, W, GROUND_Y + 6, fill="#ff5a1a", outline="", tags=("bg",))
    rnd = random.Random(7)
    for _ in range(46):
        x = rnd.uniform(0, W)
        y = rnd.uniform(GROUND_Y + 16, H - 10)
        w2 = rnd.uniform(8, 30)
        cv.create_rectangle(x, y, x + w2, y + 4, fill="#2c120a", outline="", tags=("bg",))
    for tx in (150, W - 150):
        cv.create_rectangle(tx - 6, GROUND_Y - 200, tx + 6, GROUND_Y - 110, fill="#4a2410", outline="", tags=("bg",))
        cv.create_rectangle(tx - 14, GROUND_Y - 212, tx + 14, GROUND_Y - 196, fill="#6b4a2a", outline="", tags=("bg",))


def draw_torches(cv, time_now):
    for tx in (150, W - 150):
        base_y = GROUND_Y - 204
        for i, (dxo, hgt, col) in enumerate(((-7, 26, "#ff5a1a"), (0, 34, COL_ORANGE), (7, 22, COL_GOLD))):
            tip = base_y - hgt - 6 * math.sin(time_now * 10 + i * 2.1 + tx)
            cv.create_polygon(tx + dxo - 6, base_y, tx + dxo + 6, base_y, tx + dxo, tip,
                              fill=col, outline="", tags=("dyn",))
