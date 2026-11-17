"""IMMY — глобальные константы: размеры, физика, шрифты, палитра, бой."""

import os
import sys

TITLE = "IMMY"

W, H = 1600, 900
FPS = 110
TICK_MS = 1000 // FPS
GROUND_Y = 770
WALL = 80
GRAVITY = 2400.0

if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SAVE_FILE = os.path.join(_BASE_DIR, "immy_save.json")

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

MYTH_ENERGY = 100
MYTH_FOE_HP = 0.25
LEGEND_FOE_HP = 0.30
ULT_CHARGE_MAX = 100.0
THORNS_PCT = 0.30
RIPOSTE_DUR = 0.9
RIPOSTE_MULT = 1.3
CURSE_MULT = 0.7
MARTYR_ROUNDS = 3
MARTYR_HP_MULT = 6.0
MARTYR_DMG_MULT = 4.0
MARTYR_GEMS = 100
MARTYR_COIN_PER_DMG = 2

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

RARITY_POWER = {"standard": 1.0, "common": 1.0, "uncommon": 1.06,
                "exclusive": 1.10, "epic": 1.13, "mythic": 1.20, "devil": 1.28,
                "legendary": 1.35}

FATALITY_WINDOW = 4.5
FATALITY_BONUS = 150
FATALITY_GEMS = 5
FATALITY_ANIM_T = 2.6
FATALITY_KEYS = ("w", "a", "s", "d", "e", "f", "attack")
FATALITY_TXT = {"w": "W", "a": "A", "s": "S", "d": "D", "e": "E", "f": "F", "attack": "ЛКМ"}

NET_DISCOVER_PORT = 55555
NET_FIGHT_PORT = 55556
NET_SCAN_TIMEOUT = 0.8
NET_SNAP_HZ = 30

ZONE_HEAD = 1.30
ZONE_BODY = 1.00
ZONE_LEGS = 0.80
ZONE_HEAD_STUN = 0.12
ZONE_LEGS_SLOW = 0.9

TRAP_CYCLE = 6.0
TRAP_ACTIVE = 1.6
TRAP_DMG = (8, 15)
TRAP_BLEED = 2.0
TRAP_ZONE = 120

ART_SLOTS = 3
NATURE_MATCH_BONUS = 0.07

MUSIC_VOL = 0.7
SFX_VOL = 0.8

SURV_FRAG_CHANCE = 0.55
SURV_FRAG_BOSS_CHANCE = 1.0

DIALOG_INTRO_T = 1.6
