"""IMMY — глобальные константы: размеры, физика, шрифты, палитра, бой."""

import os

TITLE = "IMMY"

W, H = 1600, 900
FPS = 75
TICK_MS = 1000 // FPS
GROUND_Y = 770
WALL = 80
GRAVITY = 2400.0

SAVE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "immy_save.json")

F_TITLE = ("Courier", 64, "bold")
F_HUGE = ("Courier", 48, "bold")
F_SQUARE = ("Courier", 40, "bold")
F_BIG = ("Courier", 26, "bold")
F_MID = ("Courier", 18, "bold")
F_SMALL = ("Courier", 13, "bold")
F_TINY = ("Courier", 11)

MENU_STOPS = [(0.0, (26, 5, 8)), (0.55, (122, 22, 10)), (1.0, (255, 140, 30))]

COL_GOLD = "#ffd23f"
COL_ORANGE = "#ff8c1a"
COL_RED = "#ff3b14"
COL_DEEPRED = "#ff4a1a"
COL_DARK = "#1c0a08"
COL_FRAME = "#7a1c10"
COL_SAND = "#c9a07a"
COL_GEM = "#3fd97a"
COL_BLOOD = "#c4140f"

MELEE_RANGE = 112
COMBO_WINDOW = 0.9
COMBO_MULT = (1.0, 1.18, 1.4)
COMBO_KB = (240.0, 300.0, 420.0)

PARRY_WINDOW = 0.2
PARRY_CD = 1.2
PARRY_STUN = 0.1
CRIT_MULT = 1.8

KICK_CD = 1.0
UPPERCUT_CD = 2.0
SWEEP_CD = 1.2
AIR_CD = 1.0

INJURY_CHANCE = 0.04

MYTH_ENERGY = 50
MYTH_FOE_HP = 0.25

MAX_PARTS = 220
MAX_EMBERS = 26

CHEST_COST = 30


def exp_to_next(level):
    return 80 + level * 40


ULT_HP = 0.10
ULT_QUALITY = 0.05
ULT_LEFT = 4.0
ULT_RANGE_Y = 200
FINISHER_BONUS = 25
