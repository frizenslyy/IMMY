"""IMMY — карты арен (30 шт., часть с ловушками), фоны, иконки героев и портреты."""

import math
import random

from .config import (COL_GOLD, COL_SAND, F_SMALL, F_TITLE, TRAP_ACTIVE, TRAP_CYCLE,
                     GROUND_Y, H, MENU_STOPS, W)
from .heroes import HEROES
from .util import gradient


def _m(name, c0, c1, c2, moon, moon_cr, pillar, pillar_top, floor, floor_line,
       tile, torch, mountain, mountain2, stars, deco, trap=None):
    return {"name": name, "stops": [(0.0, c0), (0.55, c1), (1.0, c2)],
            "moon": moon, "moon_cr": moon_cr, "pillar": pillar, "pillar_top": pillar_top,
            "floor": floor, "floor_line": floor_line, "tile": tile, "torch": torch,
            "mountain": mountain, "mountain2": mountain2, "stars": stars, "deco": deco,
            "trap": trap}


MAPS = [
    _m("ВУЛКАН", (16, 3, 8), (88, 14, 10), (190, 62, 16), "#ff5a1a", "#e8431a",
       "#160607", "#24100c", "#200c08", "#ff5a1a", "#2c120a",
       ("#ff5a1a", "#ff8c1a", "#ffd23f"), "#3a0e0a", "#240806", False, "embers"),
    _m("ЛЕДНИК", (6, 14, 30), (26, 64, 96), (110, 170, 210), "#cfe8ff", "#a8ccec",
       "#16324a", "#22486a", "#14283a", "#7fd4ff", "#1a3a50",
       ("#7fd4ff", "#a8e4ff", "#e0f6ff"), "#1e4260", "#122c44", True, "stars"),
    _m("ПУСТЫНЯ", (26, 16, 6), (110, 70, 20), (232, 192, 90), "#ffd23f", "#e8a83a",
       "#4a3418", "#5e4420", "#3a2a10", "#e8a83a", "#463414",
       ("#ff8c1a", "#e8a83a", "#ffd23f"), "#6a481c", "#4a3010", False, "dust"),
    _m("НОЧНОЙ ЛЕС", (4, 14, 8), (12, 48, 24), (42, 106, 52), "#baffd4", "#8ae0b0",
       "#0e2414", "#16341e", "#0c1c10", "#4ad16a", "#12281a",
       ("#4ad16a", "#8ae05a", "#d2ff8a"), "#0c2818", "#081c10", True, "spores"),
    _m("МИР ТЕНЕЙ", (8, 4, 18), (36, 18, 60), (106, 58, 138), "#b08aff", "#8a5ad1",
       "#1a1030", "#281a48", "#140c24", "#8a5ad1", "#1e1436",
       ("#8a5ad1", "#b08aff", "#d8c0ff"), "#241440", "#160c2c", True, "stars"),
    _m("КРОВАВЫЙ СТАДИОН", (20, 2, 4), (96, 10, 8), (210, 40, 14), "#ff3b14", "#c41e0a",
       "#1a0606", "#2a0c08", "#240a08", "#ff3b14", "#300e0a",
       ("#ff3b14", "#ff6a1a", "#ffd23f"), "#420e0a", "#2a0806", False, "embers", "spikes"),
    _m("ЛИТЫЙ ЗАЛ", (24, 8, 4), (120, 36, 10), (230, 120, 30), "#ffb01a", "#e88a1a",
       "#2a1008", "#3a1a0c", "#2a140a", "#ffb01a", "#361a0e",
       ("#ffb01a", "#ffd23f", "#fff2b0"), "#4a1e0c", "#301208", False, "embers", "flame"),
    _m("КАТАКОМБЫ", (6, 4, 6), (28, 20, 26), (74, 56, 66), "#c9b8d8", "#9a88aa",
       "#141014", "#201820", "#120e12", "#9a88aa", "#1a141a",
       ("#b08aff", "#c9b8d8", "#e8e0f0"), "#1c141c", "#100c10", False, "dust", "spikes"),
    _m("НЕБЕСНЫЙ МОСТ", (10, 20, 44), (60, 110, 170), (170, 210, 240), "#fff7d0", "#dfe6ff",
       "#3a5a80", "#4a6a94", "#2a3f5c", "#bfe0ff", "#33506e",
       ("#bfe0ff", "#d8eeff", "#ffffff"), "#33608c", "#22466a", True, "stars"),
    _m("ЖЕРЛОВО", (30, 4, 2), (140, 20, 6), (255, 90, 20), "#ffd23f", "#ff8c1a",
       "#200808", "#301010", "#280c08", "#ff8c1a", "#34100a",
       ("#ff8c1a", "#ffd23f", "#fff2b0"), "#4a1008", "#300a06", False, "embers", "flame"),
    _m("РЖАВЫЙ ДОК", (10, 10, 12), (70, 44, 30), (150, 100, 60), "#e8c98a", "#b8905a",
       "#241a12", "#32241a", "#1c1410", "#c9905a", "#281e14",
       ("#ff8c1a", "#e8a83a", "#ffd23f"), "#2e2016", "#1c130c", False, "dust", "saw"),
    _m("ХРУСТАЛЬНЫЙ ГРОТ", (4, 12, 26), (20, 70, 90), (90, 180, 200), "#d0f6ff", "#9adcee",
       "#123240", "#1a4454", "#0e242e", "#7fd4ff", "#14303c",
       ("#7fd4ff", "#b0ecff", "#e0f8ff"), "#16404e", "#0e2c36", True, "stars"),
    _m("ПЕПЕЛИЩЕ", (10, 8, 8), (60, 44, 38), (140, 110, 90), "#ffb01a", "#d88040",
       "#181412", "#241e1a", "#161210", "#e8a860", "#1e1814",
       ("#ff8c1a", "#e8a860", "#ffd8a0"), "#2a221c", "#1a1410", False, "dust", "flame"),
    _m("ТРОННЫЙ ЗАЛ", (16, 8, 2), (90, 56, 12), (210, 160, 50), "#ffd23f", "#e8a83a",
       "#241806", "#322208", "#1e1408", "#ffd23f", "#2a1e0a",
       ("#ffd23f", "#ffe88a", "#fff7d0"), "#3a2a0c", "#261a08", False, "embers"),
    _m("БОЛОТО ДУШ", (4, 10, 6), (16, 40, 22), (48, 92, 44), "#baffd4", "#7ad1a0",
       "#0c1810", "#14241a", "#0a140c", "#5ad17a", "#102016",
       ("#5ad17a", "#8ae0a0", "#d2ffd8"), "#10241a", "#0a180e", True, "spores", "spikes"),
    _m("КУЗНЯ", (20, 6, 2), (110, 30, 8), (240, 110, 24), "#ff8c1a", "#ff5a1a",
       "#1c0c06", "#28140a", "#180a06", "#ff8c1a", "#241008",
       ("#ff5a1a", "#ff8c1a", "#ffd23f"), "#341008", "#220a06", False, "embers", "flame"),
    _m("ЛУННАЯ ОПУШКА", (6, 10, 20), (30, 44, 70), (90, 110, 150), "#e8f0ff", "#b8c8e8",
       "#141c2c", "#1e2a3e", "#101624", "#b8c8e8", "#182234",
       ("#b8c8e8", "#d8e4ff", "#ffffff"), "#1a2638", "#101826", True, "stars"),
    _m("ГРОЗОВОЙ УТЕС", (4, 8, 18), (24, 40, 76), (80, 110, 170), "#fff2b0", "#c8d4f0",
       "#10182c", "#182238", "#0c1220", "#ffe88a", "#121a2c",
       ("#ffe88a", "#fff7d0", "#ffffff"), "#162040", "#0e1628", True, "stars", "spikes"),
    _m("ПЕСЧАНАЯ БУРЯ", (20, 12, 6), (90, 60, 24), (200, 150, 70), "#ffe0a0", "#d8b070",
       "#342410", "#44301a", "#281c0c", "#e8b870", "#322410",
       ("#ffcf6a", "#e8a83a", "#ffe0a0"), "#4a3414", "#30200c", False, "dust"),
    _m("ЗАТОНУВШИЙ ХРАМ", (2, 10, 14), (12, 44, 56), (40, 100, 110), "#a0e8e0", "#70c8c0",
       "#0c2028", "#142c34", "#0a181e", "#5ad1c9", "#10262c",
       ("#5ad1c9", "#8ae8e0", "#d0fff8"), "#123038", "#0a2026", True, "stars", "saw"),
    _m("КУПОЛ ПЛАМЕНИ", (18, 4, 4), (100, 18, 10), (235, 80, 20), "#ffcf6a", "#ff8c1a",
       "#1e0806", "#2c100a", "#1a0806", "#ff8c1a", "#26100a",
       ("#ff8c1a", "#ffcf6a", "#fff2b0"), "#3a0e08", "#260806", False, "embers", "flame"),
    _m("ЛЕДЯНАЯ ТЮРЬМА", (4, 8, 16), (18, 44, 72), (70, 120, 170), "#cfe8ff", "#8ab8e0",
       "#10202e", "#182c40", "#0c1824", "#8ac8ff", "#142434",
       ("#8ac8ff", "#b8e4ff", "#e8f6ff"), "#14283c", "#0c1a28", True, "stars", "spikes"),
    _m("КЛАДБИЩЕ КОРАБЛЕЙ", (4, 8, 10), (20, 40, 48), (56, 92, 100), "#c8d8d0", "#94b0a8",
       "#101c1e", "#182828", "#0c1416", "#88b0a8", "#142022",
       ("#88b0a8", "#b0d0c8", "#e0f0e8"), "#142424", "#0c1818", True, "stars", "saw"),
    _m("ОГНЕННАЯ КОЛОННАДА", (16, 4, 4), (80, 16, 8), (200, 60, 16), "#ffb01a", "#ff6a1a",
       "#180806", "#24100a", "#140606", "#ff6a1a", "#200c08",
       ("#ff6a1a", "#ffb01a", "#ffd23f"), "#2e0c08", "#1c0806", False, "embers"),
    _m("САД ТЕНЕЙ", (6, 4, 10), (24, 18, 40), (64, 48, 90), "#c0a8ff", "#8a6ad1",
       "#12101c", "#1a1828", "#0e0c16", "#a88ae0", "#161424",
       ("#a88ae0", "#c8b0ff", "#e8e0ff"), "#1a1628", "#100e1a", True, "spores", "spikes"),
    _m("МЕДНЫЕ ПЕЩЕРЫ", (12, 6, 4), (72, 40, 18), (170, 110, 50), "#ffcf6a", "#d89040",
       "#201408", "#2c1c0c", "#181008", "#d89040", "#221608",
       ("#d89040", "#ffcf6a", "#ffe8b0"), "#2c1c0c", "#1c1208", False, "dust", "saw"),
    _m("ЗАЛ МОЛНИЙ", (8, 8, 4), (60, 56, 16), (170, 160, 50), "#fff7b0", "#d8d070",
       "#1c1a08", "#28260c", "#141208", "#ffe88a", "#1c1a0c",
       ("#ffe88a", "#fff7d0", "#ffffff"), "#26240c", "#181608", True, "stars", "spikes"),
    _m("КРАСНЫЙ КАНЬОН", (14, 6, 4), (96, 34, 16), (210, 100, 40), "#ffd23f", "#e88a3a",
       "#28120a", "#361a0e", "#1e0e08", "#ff9a4a", "#2a140c",
       ("#ff9a4a", "#ffcf6a", "#ffe8b0"), "#3e1810", "#28100a", False, "dust"),
    _m("ОБСИДИАНОВАЯ АРЕНА", (4, 2, 4), (24, 12, 20), (70, 40, 56), "#ffd23f", "#c8901a",
       "#0e0a0e", "#161016", "#0a080a", "#c8901a", "#120e12",
       ("#c8901a", "#ffd23f", "#fff2b0"), "#160e14", "#0c080c", True, "embers", "spikes"),
    _m("ВРАТА БЕЗДНЫ", (6, 2, 10), (30, 8, 44), (84, 24, 96), "#e04aff", "#a02ad1",
       "#140818", "#1e0c24", "#100614", "#c04aff", "#180a1e",
       ("#c04aff", "#e04aff", "#f0c0ff"), "#1c0a24", "#120618", True, "stars", "flame"),
]


def trap_phase(t):
    """(активна ли ловушка, прогресс 0..1) — детерминировано от времени."""
    ph = t % TRAP_CYCLE
    return ph < TRAP_ACTIVE, ph / TRAP_ACTIVE


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


def draw_trap_static(cv, m):
    """Постоянные элементы ловушек (гнёзда, пазы) — рисуются в слой bg."""
    trap = m.get("trap")
    if trap == "spikes":
        for side in (0, W):
            x = 6 if side == 0 else W - 6
            sgn = 1 if side == 0 else -1
            for i in range(6):
                sy = GROUND_Y - 40 - i * 44
                cv.create_polygon(x, sy + 34, x, sy, x + sgn * 26, sy + 17,
                                  fill="#3a1410", outline="#5a2418", tags=("bg",))
    elif trap == "saw":
        for sx in (WALL + 8, W - WALL - 8):
            cv.create_rectangle(sx - 20, GROUND_Y + 6, sx + 20, GROUND_Y + 26,
                                fill="#241410", outline="#3a2018", tags=("bg",))
    elif trap == "flame":
        for i in range(4):
            fx = 260 + i * 340
            cv.create_rectangle(fx - 26, GROUND_Y - 4, fx + 26, GROUND_Y + 8,
                                fill="#1c0a06", outline="#3a140a", tags=("bg",))


def draw_traps(cv, time_now, m):
    """Активные ловушки: шипы из стен, пила по полу, огненные жерла."""
    trap = m.get("trap")
    if not trap:
        return
    active, _ph = trap_phase(time_now)
    if trap == "spikes":
        for side in (0, W):
            x = 6 if side == 0 else W - 6
            sgn = 1 if side == 0 else -1
            ext = 30 if active else 8
            for i in range(6):
                sy = GROUND_Y - 40 - i * 44
                cv.create_polygon(x, sy + 34, x, sy - ext, x + sgn * ext, sy + 17 - ext / 2,
                                  fill="#c9b8a8" if active else "#5a4a3a", outline="#e8d8c8" if active else "",
                                  tags=("dyn",))
    elif trap == "saw":
        sx = WALL + 40 + (W - 2 * WALL - 80) * ((time_now / TRAP_CYCLE) % 1.0)
        r = 26
        spin = time_now * 14
        col = "#c0c8d0" if active else "#6a7480"
        cv.create_oval(sx - r, GROUND_Y - r, sx + r, GROUND_Y + r, fill=col,
                       outline="#e8f0f8" if active else "#8890a0", width=2, tags=("dyn",))
        for k in range(6):
            a = spin + k * math.pi / 3
            cv.create_line(sx, GROUND_Y, sx + math.cos(a) * r, GROUND_Y + math.sin(a) * r,
                           fill="#3a4048", width=2, tags=("dyn",))
    elif trap == "flame":
        for i in range(4):
            fx = 260 + i * 340
            if active and (i + int(time_now / TRAP_CYCLE)) % 2 == 0:
                hgt = 60 + 24 * math.sin(time_now * 12 + i)
                for k, (c, wdt) in enumerate((("#ff5a1a", 22), ("#ff8c1a", 14), ("#ffd23f", 7))):
                    cv.create_polygon(fx - wdt, GROUND_Y, fx + wdt, GROUND_Y,
                                      fx, GROUND_Y - hgt + k * 12, fill=c, outline="", tags=("dyn",))


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
