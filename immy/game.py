"""IMMY — главный класс игры: окна, ввод, магазин, сундуки, INFO, кампании, достижения."""

import math
import random
import traceback
import textwrap
import time
import tkinter as tk

from . import achievements, artifacts, campaign, chests, netplay
from .arena import Arena
from .artifacts import (ARTIFACTS, ART_BY_ID, BPS_LABEL, BUFF_LABEL, NATURE_BY_STYLE,
                        NATURE_COLOR, NATURE_LABEL, NATURES, artifact_buffs, can_craft,
                        craft_cost_label, hero_nature)
from .background import (MAPS, draw_ambient, draw_fight_bg, draw_hero_icon,
                         draw_menu_bg, draw_screen_bg, draw_torches, draw_trap_static,
                         draw_traps)
from .config import (ART_SLOTS, CHEST_COST, CHEST_HELL_COST, COL_BLOOD, COL_GEM, COL_GOLD, COL_ORANGE,
                     COL_RED, COL_SAND, FATALITY_BONUS, FATALITY_GEMS,
                     FATALITY_KEYS, FINISHER_BONUS, F_BIG, F_HUGE, F_MID,
                     F_SMALL, F_SQUARE, F_TINY, FPS, GROUND_Y, H,
                     NET_SNAP_HZ, RARITY_POWER, SURV_FRAG_BOSS_CHANCE, SURV_FRAG_CHANCE,
                     WIN_MODES,
                     TICK_MS, TITLE, W, exp_to_next)
from .articon import draw as draw_art_icon
from .fighter import Fighter
from .heroes import HEROES, RARITY_COLOR, RARITY_LABEL, STAT_NAMES, sorted_keys
from .particles import Embers, Particles
from .save import load_save, save_save
from .sound import Audio
from .ui import Ui

WIN_MODE_LABEL = {"windowed": "WINDOW 1600x900", "boxed": "MAXIMIZED (FIT)",
                  "fullscreen": "FULLSCREEN"}

CYR_CHAR = {"ц": "w", "ф": "a", "ы": "s", "в": "d", "а": "f", "у": "e"}
CYR_NAME = {"tse": "w", "ef": "a", "yeru": "s", "ve": "d", "a": "f", "u": "e"}
VK_MAP = {87: "w", 65: "a", 83: "s", 68: "d", 70: "f", 69: "e", 82: "r"}
ARROWS = {"left": "a", "right": "d", "up": "w", "down": "s"}

CAMP_BP_CHANCE = 0.45

INFO_STRIKES = [
    ("КОМБО: 3 удара подряд усиливаются (x1.0 / x1.18 / x1.4), окно 0.9с", COL_ORANGE),
    ("E — ПИНОК: дальний удар, сильный отброс и пробитие блока", COL_SAND),
    ("S+ЛКМ — АППЕРКОТ: всегда крит, пробивает блок, подбрасывает врага", COL_SAND),
    ("S+E — ПОДСЕЧКА: бьёт низко, враг лежит 0.6с (уклоняет от верхних атак)", COL_SAND),
    ("ЛКМ в прыжке — УДАР С ВОЗДУХА: широкая дуга, достаёт приседающих", COL_SAND),
    ("E в прыжке — ДАЙВ-УДАР: тяжёлый удар вниз с разгона, тряска экрана", COL_SAND),
    ("F — ПАРИРОВАНИЕ: окно 0.2с, оглушает врага на 0.1с", COL_SAND),
    ("Присед (S) уклоняет от небесных способностей и высоких ударов", COL_SAND),
    ("Каждый удар имеет своё преимущество — комбинируй их в серии", COL_GEM),
    ("ЗОНЫ УДАРА: ГОЛОВА x1.3 (+стан) · ТЕЛО x1.0 · НОГИ x0.8 (замедление)", COL_GOLD),
    ("Урон ударов растёт от СИЛЫ героя и падает при травме руки", COL_SAND),
]

INFO_MECH = [
    ("ЭНЕРГИЯ копится за попадания по врагу и тратится на спецприёмы", COL_ORANGE),
    ("УЛЬТА-добивание: у врага <10% HP — оставляет 1 удар; <5% — полное убийство (+" + str(FINISHER_BONUS) + " монет)", COL_RED),
    ("МИФ-УЛЬТА (1+4): обе способности готовы, энергия ≥50, у врага ≤25% HP", "#ff2a8a"),
    ("ТРАВМЫ: шанс повредить сустав/кость — сила -25%, скорость -30%, без прыжков или блок способности (до конца раунда)", COL_BLOOD),
    ("КРОВЬ летит от каждого удара; криты брызжут сильнее", COL_BLOOD),
    ("РЕДКОСТИ: ОБЫЧНЫЙ 500 · НЕОБЫЧНЫЙ 2000 · ЭПИЧЕСКИЙ 5000 · МИФИЧЕСКИЙ 12000", COL_SAND),
    ("САМОЦВЕТЫ — валюта кампаний и достижений, обмениваются на сундуки", COL_GEM),
    ("СУНДУК «СОКРОВИЩНИЦА ХАОСА»: " + str(CHEST_COST) + " самоцветов — герой или монеты", COL_GEM),
    ("DEVILY — проклятый герой, выпадает только из сундука", "#8a0f0f"),
    ("CAMPAIGN: 23 кампании — награды: герои, монеты, самоцветы · после победы есть СЛЕД. УРОВЕНЬ", COL_GOLD),
    ("АРТЕФАКТЫ: 30 крафтов из эссенций и самоцветов · 3 слота на бойца (выбор героя)", COL_GOLD),
    ("ПРИРОДА (свет/тьма/огонь/земля/вода/ветер): совпала с природой бойца — +7% ко всем баффам", COL_GEM),
    ("ФРАГМЕНТЫ-ЭССЕНЦИИ падают в ВЫЖИВАНИИ; с мини-боссов (каждая 5-я волна) — всегда", COL_SAND),
    ("ЛОВУШКИ АРЕН: шипы из стен, пила по полу, огненные жерла — не стой рядом!", COL_BLOOD),
    ("НАСТРОЙКИ (шестерёнка в меню): громкость музыки/звуков, бесшумный режим, тряска, кровь", COL_SAND),
    ("ФАТАЛИТИ: у каждого героя несколько видов — серия ударов, магия и добивание в стиле персонажа", COL_RED),
    ("EXP растёт в каждом режиме; уровень игрока открывает кампании", COL_SAND),
    ("БОТ умнеет с уровнем: комбо, наказание ошибок, апперкоты и миф-ульты", COL_SAND),
    ("Каждые 10 уровней бота — БОСС: двойные монеты, огромная сила", COL_RED),
    ("У каждого героя есть плюсы и минусы — играй от сильных сторон", COL_GOLD),
    ("В умелых руках даже НЕОБЫЧНЫЙ герой побеждает ЭПИЧЕСКОГО", COL_GEM),
    ("СИЛА РЕДКОСТИ (против бота): НЕОБЫЧНЫЙ +6% · ЭКСКЛЮЗИВНЫЙ +10% · ЭПИЧЕСКИЙ +13% · МИФИЧЕСКИЙ +20% · DEVILY +28%", COL_GOLD),
    ("ФАТАЛИТИ: после победы над БОССОМ и в бою с другом экран темнеет — успей набрать комбо: +%d монет и +%d самоцвета" % (FATALITY_BONUS, FATALITY_GEMS), COL_RED),
    ("FRIEND: бой с другом по локальной сети — система находит компьютеры сам, сила всех героев равна", COL_SAND),
]


INFO_MODES = [
    ("МУЧЕНИК: 10 раундов против врага x10 HP и x10 урона — HP врага не восстанавливается", COL_RED),
    ("МУЧЕНИК: победа (убейте врага) = 100 самоцветов · поражение = монеты за урон", COL_GEM),
    ("ЛЕГЕНДАРНЫЙ — новая редкость: 5 героев, 4 способности, сильнейший ульт", COL_GOLD),
    ("УЛЬТА (R): полная энергия + полная шкала УЛЬТЫ; легендарным также враг <30% HP", "#ff2a8a"),
    ("ШКАЛА УЛЬТЫ (розовая, под энергией): заполняется от нанесённых и полученных ударов", "#ff2a8a"),
    ("МИФ-УЛЬТА (R или 1+4): обе способности готовы, полная энергия, враг ≤25% HP", "#ff2a8a"),
    ("ПОМУТНЕНИЕ РАЗУМА: враг бьёт себя своей первой способностью", COL_SAND),
    ("ЦЕПИ СУДЬБЫ: цепи тащат врага по полу к вам, нанося урон и обездвиживая", COL_SAND),
    ("ПИЛЫ: выезжают из пола с двух сторон, ранят обоих бойцов, кровотечение 4с", COL_BLOOD),
    ("AoE ВЗРЫВ: урон вокруг себя · ЗЛОБНЫЙ РЫК: волна урона + подброс врага", COL_SAND),
    ("ЗЛОБНЫЙ РЫК можно парировать — тогда враг не теряет контроль", COL_SAND),
    ("ШИПЫ: возвращают 30% урона в ближнем бою · РИПОСТА после парирования: x1.3", COL_SAND),
    ("КРОВОТЕЧЕНИЕ наносит урон со временем; переломы видны на модели бойца", COL_BLOOD),
    ("ONLINE: автоматический поиск противника · FRIEND: выбор компьютера в LAN", COL_GOLD),
    ("23 кампании · 305 ступеней · ЛЕГЕНДАРНЫЙ герой: 25000 монет или из сундука", COL_GEM),
]


def norm_key(e):
    ch = (getattr(e, "char", "") or "").lower()
    if ch in CYR_CHAR:
        return CYR_CHAR[ch]
    if len(ch) == 1 and ch.isalpha():
        return ch
    k = (e.keysym or "").lower()
    if k in ARROWS:
        return ARROWS[k]
    if k.startswith("cyrillic_"):
        k = k[9:]
    if k in CYR_NAME:
        return CYR_NAME[k]
    if k in ("??", ""):
        vk = getattr(e, "keycode", 0)
        if vk in VK_MAP:
            return VK_MAP[vk]
    return k


class Game(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            self.tk.call("tk", "scaling", 96.0 / 72.0)
        except Exception:
            pass
        self.title(TITLE)
        try:
            from .icon import build_icon
            self.iconphoto(True, build_icon())
        except Exception:
            pass
        self.configure(bg="#120406")
        self._vs = (1.0, 0.0, 0.0)
        self.geometry("%dx%d" % (W, H))
        self.resizable(False, False)
        self.cv = tk.Canvas(self, width=W, height=H, bg="#120406", highlightthickness=0)
        self.cv.place(x=0, y=0)
        self._home_geom = "%dx%d+0+0" % (W, H)
        try:
            self.update_idletasks()
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            if sw and sh:
                self._home_geom = "%dx%d+%d+%d" % (W, H, max(0, (sw - W) // 2), max(0, (sh - H) // 2))
                self.geometry("+%d+%d" % (max(0, (sw - W) // 2), max(0, (sh - H) // 2)))
        except Exception:
            pass
        self.save = load_save()
        self.bind("<Map>", self._fs_on_map, add="+")
        self.after(150, self.apply_fullscreen)
        self.coins = self.save["coins"]
        self.gems = self.save["gems"]
        self.bot_level = self.save["bot_level"]
        self.owned = self.save["owned"]
        self.exp = self.save["exp"]
        self.plvl = self.save["plvl"]
        self.state = "menu"
        self.hero_sel = "DEADY"
        self.keys = set()
        self.events = set()
        self.prev_combos = set()
        self.buttons = []
        self.mouse = (0, 0)
        self.arena = None
        self.preview = None
        self.parts = Particles()
        self.ui = Ui(self)
        self.embers = Embers()
        self.audio = Audio(self.save.get("settings"))
        self.music = self.audio.music
        self.sfx = self.audio.sfx
        self.shop_msg = None
        self.shop_tab = "heroes"
        self.art_page = 0
        self.camp_page = 0
        self.shop_hero_page = 0
        self.net_hero_page = 0
        self.hero_page = 0
        self.equip_page = 0
        self._wrap_cpl = {}
        self.chest_kind = "chaos"
        self.equip_scroll = 0
        self.info_page = 0
        self.chest_t = None
        self.chest_reward = None
        self.toasts = []
        self.camp_idx = 0
        self.camp_ctx = None
        self.ach_page = 0
        self.net_role = None
        self.net_mode = "friend"
        self.net_sids = {}
        self.online_t = 0.0
        self.net = None
        self.net_host = None
        self.disc = None
        self.net_peers = []
        self.net_my_pick = None
        self.net_foe_pick = None
        self.net_peer_name = ""
        self.net_msg = ""
        self.net_map = 0
        self._snap_n = 0
        self.last = time.time()
        self.bind("<KeyPress>", self.on_key)
        self.bind("<KeyRelease>", self.on_key_release)
        self.cv.bind("<Motion>", self.on_motion)
        self.cv.bind("<Button-1>", self.on_click)
        self.set_state("menu")
        self.after(TICK_MS, self.loop)

    def set_state(self, s):
        self.state = s
        self.parts.clear()
        self.events.clear()
        self.cv.delete("bg")
        if s == "menu":
            draw_menu_bg(self.cv)
        elif s == "fight" and self.arena is not None:
            draw_fight_bg(self.cv, self.arena.map)
            draw_trap_static(self.cv, self.arena.map)
        else:
            draw_screen_bg(self.cv)
        if s == "fight":
            if self.arena is not None and (self.arena.boss or self.arena.martyr):
                self.music.play("hell")
            else:
                self.music.play(random.choice(("battle", "battle2")))
        else:
            self.music.play("menu")
        if s in ("heroes", "select"):
            self.preview = Fighter(self.hero_sel, W / 2, 1, scale=2.4)
            self.preview.y = GROUND_Y - 19
        else:
            self.preview = None
        s_i, tx_i, ty_i = self._vs
        if s_i != 1.0 or tx_i or ty_i:
            self.cv.scale("bg", 0, 0, s_i, s_i)
            self.cv.move("bg", tx_i, ty_i)

    def persist(self):
        self.save["coins"] = self.coins
        self.save["gems"] = self.gems
        self.save["bot_level"] = self.bot_level
        self.save["owned"] = self.owned
        self.save["exp"] = self.exp
        self.save["plvl"] = self.plvl
        self.save["stats"]["plvl"] = self.plvl
        self.save["stats"]["arts_owned"] = len(self.save.get("arts", {}))
        self.save["stats"]["bps_have"] = sum(self.save.get("bps", {}).values())
        granted = achievements.check(self.save)
        for a in granted:
            rw = ""
            if a.get("reward"):
                rw += "+%d МОНЕТ" % a["reward"]
            if a.get("gems"):
                rw += ("  " if rw else "") + "+%d САМОЦВЕТОВ" % a["gems"]
            self.toasts.append(("ДОСТИЖЕНИЕ: " + a["name"], rw, time.time() + 4.0))
        self.coins = self.save["coins"]
        self.gems = self.save["gems"]
        save_save(self.save)

    def earn(self, n):
        self.coins += n
        self.save["stats"]["coins_earned"] = self.save["stats"].get("coins_earned", 0) + n

    def earn_gems(self, n):
        self.gems += n
        self.save["gems"] = self.gems
        self.save["stats"]["gems_earned"] = self.save["stats"].get("gems_earned", 0) + n

    def add_exp(self, amount):
        if amount <= 0:
            return
        self.exp += amount
        while self.exp >= exp_to_next(self.plvl):
            self.exp -= exp_to_next(self.plvl)
            self.plvl += 1
            self.toasts.append(("УРОВЕНЬ %d!" % self.plvl, "", time.time() + 4.0))

    def goto_menu(self):
        self.set_state("menu")

    def goto_mode(self):
        self.set_state("mode")

    def goto_heroes(self):
        self.set_state("heroes")

    def goto_select(self, mode="bot"):
        self.next_mode = mode
        self.set_state("select")

    def goto_shop(self):
        self.shop_msg = None
        self.chest_t = None
        self.chest_reward = None
        self.set_state("shop")

    def goto_info(self):
        self.info_page = 0
        self.set_state("info")

    def goto_campaigns(self):
        self.set_state("campaigns")

    def open_camp(self, idx):
        self.camp_idx = idx
        self.set_state("camp_stages")

    def goto_achievements(self):
        self.ach_page = 0
        self.set_state("achievements")

    def goto_net(self):
        self._net_enter("friend")

    def goto_online(self):
        self._net_enter("online")

    def _net_enter(self, mode):
        self.leave_net_soft()
        self.net_msg = ""
        self.net_peers = []
        self.net_sids = {}
        self.net_mode = mode
        self.online_t = 0.0
        self.disc = netplay.Discovery()
        self.disc.seeking = mode == "online"
        self.net_host = netplay.Host()
        if not self.net_host.alive:
            self.net_msg = "ХОСТ-ПОРТ ЗАНЯТ: ВЫ СМОЖЕТЕ ТОЛЬКО ПОДКЛЮЧАТЬСЯ"
        self.set_state("net_scan")
        self.net_peers, self.net_sids = self.disc.scan(mode)

    def leave_net(self):
        if self.net is not None:
            self.net.send({"t": "leave"})
            self.net.close()
            self.net = None
        self.leave_net_soft()
        self.net_role = None
        self.net_my_pick = None
        self.net_foe_pick = None
        self.net_peer_name = ""
        self.net_peers = []

    def net_connect(self, ip, name):
        client = netplay.Client()
        if not client.connect(ip):
            self.net_msg = "НЕ УДАЛОСЬ ПОДКЛЮЧИТЬСЯ К %s" % name
            return
        self.leave_net_soft()
        self.net = client
        self.net_role = "client"
        self.net_peer_name = name
        self.net.send({"t": "hello", "name": netplay.host_name()})
        self.net_my_pick = None
        self.net_foe_pick = None
        self.set_state("net_select")

    def leave_net_soft(self):
        if self.disc is not None:
            self.disc.close()
            self.disc = None
        if isinstance(getattr(self, "net_host", None), netplay.Host):
            self.net_host.close()
        self.net_host = None

    def pick_hero(self, key):
        self.hero_sel = key
        self.equip_page = 0
        if self.state in ("heroes", "select"):
            self.preview = Fighter(key, W / 2, 1, scale=2.4)
            self.preview.y = GROUND_Y - 19

    def buy_hero(self, key):
        hero = HEROES[key]
        if key in self.owned:
            return
        if self.coins < hero["price"]:
            self.shop_msg = ("НЕ ХВАТАЕТ МОНЕТ", time.time() + 2.0)
            return
        self.coins -= hero["price"]
        self.owned.append(key)
        self.save["stats"]["buys"] = self.save["stats"].get("buys", 0) + 1
        self.persist()
        self.shop_msg = ("КУПЛЕНО: %s!" % hero["name"], time.time() + 2.5)

    def chest_keys(self, rarity):
        return chests.keys_of(rarity)

    def roll_hell_chest(self):
        return chests.roll_hell()

    def roll_chest(self):
        return chests.roll_chaos()

    def buy_chest(self, chest="chaos"):
        cost = CHEST_COST if chest == "chaos" else CHEST_HELL_COST
        if self.gems < cost:
            self.shop_msg = ("НЕ ХВАТАЕТ САМОЦВЕТОВ (%d/%d)" % (self.gems, cost),
                             time.time() + 2.5)
            return
        self.gems -= cost
        self.save["gems"] = self.gems
        self.save["stats"]["chests"] = self.save["stats"].get("chests", 0) + 1
        self.chest_kind = chest
        kind, val = self.roll_chest() if chest == "chaos" else self.roll_hell_chest()
        if kind == "gems":
            self.earn_gems(val)
            self.chest_reward = ("gems", val)
        if kind == "hero":
            if val in self.owned:
                comp = HEROES[val]["price"] // 2 + 10
                self.earn(comp)
                self.earn_gems(10)
                self.chest_reward = ("dupe", val, comp)
            else:
                self.owned.append(val)
                self.save["stats"]["buys"] = self.save["stats"].get("buys", 0) + 1
                self.chest_reward = ("hero", val)
        else:
            self.earn(val)
            self.chest_reward = ("coins", val)
        self.persist()
        self.chest_t = 0.0
        self.set_state("chest_open")

    def chest_title(self):
        return chests.title(self.chest_kind)

    def collect_chest(self):
        self.chest_t = None
        self.chest_reward = None
        self.set_state("shop")

    def start_fight(self):
        nm = getattr(self, "next_mode", "bot")
        self.camp_ctx = None
        equip = self.save["equip"].get(self.hero_sel, [])
        if nm == "fair":
            bot_key = random.choice(sorted_keys([k for k in HEROES if k != self.hero_sel]))
            self.arena = Arena(self.hero_sel, bot_key, self.bot_level, False,
                               map=random.choice(MAPS), fair=True, sfx=self.sfx, equip=equip)
        elif nm == "survival":
            self.arena = Arena(self.hero_sel, "DEADY", 1, False, map=random.choice(MAPS),
                               survival=True, sfx=self.sfx, equip=equip)
        elif nm == "martyr":
            bot_key = random.choice([k for k in HEROES if k != self.hero_sel])
            self.arena = Arena(self.hero_sel, bot_key, self.bot_level, False,
                               map=random.choice(MAPS), martyr=True, sfx=self.sfx, equip=equip)
        elif isinstance(nm, tuple) and nm[0] == "campaign":
            _, idx, stage = nm
            level = campaign.stage_level(idx, stage)
            boss = campaign.is_final(idx, stage)
            bot_key = random.choice([k for k in HEROES if k != self.hero_sel])
            self.arena = Arena(self.hero_sel, bot_key, level, boss, map=random.choice(MAPS),
                               sfx=self.sfx, equip=equip)
            self.camp_ctx = (idx, stage)
        else:
            level = self.bot_level
            boss = level % 10 == 0
            bot_key = random.choice([k for k in HEROES if k != self.hero_sel])
            self.arena = Arena(self.hero_sel, bot_key, level, boss, map=random.choice(MAPS),
                               sfx=self.sfx, equip=equip)
        self.set_state("fight")

    def on_key(self, e):
        k = norm_key(e)
        if k == "escape":
            if self.state in ("net_scan", "net_select") or (self.state == "fight"
                                                            and self.arena is not None and self.arena.net):
                self.leave_net()
                self.arena = None
            if self.state != "menu":
                self.set_state("menu")
            return
        if k == "m" and k not in self.keys:
            self.music.toggle()
        if self.state == "fight":
            if self.arena is not None and self.arena.phase == "fatality":
                if k in FATALITY_KEYS:
                    self.events.add(k)
                return
            if k == "w":
                self.events.add("jump")
            elif k == "f":
                self.events.add("parry")
            elif k == "e":
                self.events.add("kick")
            elif k in ("1", "2", "3", "4"):
                self.events.add(k)
            elif k == "r":
                self.events.add("r")
        self.keys.add(k)

    def on_key_release(self, e):
        self.keys.discard(norm_key(e))

    def _ev_xy(self, e):
        s, tx, ty = self._vs
        if s != 1.0 or tx or ty:
            return ((e.x - tx) / s, (e.y - ty) / s)
        return (e.x, e.y)

    def on_motion(self, e):
        self.mouse = self._ev_xy(e)

    def on_click(self, e):
        mx, my = self._ev_xy(e)
        if self.state == "fight":
            if self.arena is None:
                return
            if self.arena.phase == "end":
                for x0, y0, x1, y1, action in self.buttons:
                    if x0 <= mx <= x1 and y0 <= my <= y1:
                        try:
                            action()
                        except Exception:
                            traceback.print_exc()
                            self.toasts.append(("ОШИБКА ДЕЙСТВИЯ", "", time.time() + 3.0))
                        return
            elif self.arena.phase == "fatality":
                self.events.add("attack")
            elif self.arena.phase == "fight":
                self.events.add("attack")
            return
        for x0, y0, x1, y1, action in self.buttons:
            if x0 <= mx <= x1 and y0 <= my <= y1:
                self.sfx.play("click")
                try:
                    action()
                except Exception:
                    traceback.print_exc()
                    self.toasts.append(("ОШИБКА ДЕЙСТВИЯ", "", time.time() + 3.0))
                return

    def build_input(self):
        inp = {"move": 0, "jump": "jump" in self.events, "crouch": "s" in self.keys,
               "attack": "attack" in self.events, "cast": None, "parry": "parry" in self.events,
               "special": None, "strike": None, "myth": False, "rult": "r" in self.events}
        if "a" in self.keys:
            inp["move"] -= 1
        if "d" in self.keys:
            inp["move"] += 1
        digits = sorted(e for e in self.events if e in ("1", "2", "3", "4", "5"))
        if {"1", "4"} <= set(digits):
            inp["myth"] = True
        elif digits:
            inp["cast"] = int(digits[-1]) - 1
        if self.arena is not None:
            p = self.arena.p
            if inp["attack"] and "s" in self.keys:
                inp["attack"] = False
                inp["strike"] = "upper"
            elif inp["attack"] and not p.on_ground:
                inp["attack"] = False
                inp["strike"] = "air"
            if "kick" in self.events:
                if p.on_ground and "s" in self.keys:
                    inp["strike"] = "sweep"
                elif not p.on_ground:
                    inp["strike"] = "dive"
                else:
                    inp["strike"] = "kick"
        combos = set()
        if {"a", "s"} <= self.keys:
            combos.add("as")
        if {"w", "s"} <= self.keys:
            combos.add("ws")
        if {"w", "a"} <= self.keys:
            combos.add("wa")
        if {"w", "d"} <= self.keys:
            combos.add("wd")
        fresh = combos - self.prev_combos
        if fresh:
            inp["special"] = sorted(fresh)[0]
        self.prev_combos = combos
        self.events.clear()
        return inp

    def loop(self):
        now = time.time()
        dt = min(0.05, now - self.last)
        self.last = now
        try:
            self.loop_body(dt)
        except Exception:
            traceback.print_exc()
        self.after(TICK_MS, self.loop)

    def loop_body(self, dt):
        self.embers.update(dt)
        if self.state == "net_scan":
            if isinstance(self.net_host, netplay.Host) and self.net_host.connected:
                self.net = self.net_host
                self.net_role = "host"
                self.net_peer_name = ""
                self.net_my_pick = None
                self.net_foe_pick = None
                self.set_state("net_select")
            elif self.net_mode == "online" and self.net is None:
                self.online_t += dt
                if self.online_t >= 1.2:
                    self.online_t = 0.0
                    self.net_peers, self.net_sids = self.disc.scan("online")
                    if self.net_peers and isinstance(self.net_host, netplay.Host):
                        ip, name = self.net_peers[0]
                        peer_sid = self.net_sids.get(ip, "")
                        if peer_sid and (self.disc.sid < peer_sid or not self.net_host.alive):
                            self.net_connect(ip, name)
            if self.disc is None:
                self.net_back()
        elif self.state == "net_select":
            self.net_poll_select()
        if self.state in ("heroes", "select") and self.preview is not None:
            self.preview.anim_t += dt
            if random.random() < dt * 4:
                hero = HEROES[self.hero_sel]
                self.parts.items.append({"x": W / 2 + random.uniform(-50, 50),
                                         "y": GROUND_Y - 19 - random.uniform(20, 170),
                                         "vx": random.uniform(-20, 20), "vy": random.uniform(-70, -25),
                                         "t": 0.6, "life": 0.6, "color": hero["glow"], "r": 2.5, "g": -40})
            self.parts.update(dt)
        elif self.state == "chest_open" and self.chest_t is not None:
            self.chest_t += dt
            if 0.8 < self.chest_t < 1.7 and random.random() < dt * 30:
                for _ in range(3):
                    self.parts.items.append({"x": W / 2 + random.uniform(-40, 40),
                                             "y": 430 + random.uniform(-20, 20),
                                             "vx": random.uniform(-160, 160), "vy": random.uniform(-320, -60),
                                             "t": 0.8, "life": 0.8,
                                             "color": random.choice((COL_GOLD, COL_GEM, COL_ORANGE)),
                                             "r": 3.0, "g": 300})
            self.parts.update(dt)
        if self.state == "fight" and self.arena is not None:
            if self.arena.mirror:
                self.net_mirror_frame(dt)
                if self.state == "fight" and self.arena is not None and self.arena.mirror:
                    if self.arena.phase == "fatality":
                        ev = [k for k in self.events if k in FATALITY_KEYS]
                        if ev:
                            self.net.send({"t": "fat", "ev": ev})
                    inp = self.build_input()
                    self.net.send({"t": "in", "d": inp})
                    if self.arena.phase == "end" and not self.arena.rewarded:
                        self.finish_fight()
            else:
                if self.arena.phase == "fatality" and (not self.arena.net or self.arena.win):
                    self.arena.fatality_feed(k for k in self.events if k in FATALITY_KEYS)
                if self.arena.net:
                    self.net_host_frame(dt)
                    if self.arena is None or self.state != "fight":
                        return
                inp = self.build_input()
                self.arena.update(dt, inp)
                if self.arena.net:
                    self._snap_n += 1
                    if self._snap_n % max(1, FPS // NET_SNAP_HZ) == 0:
                        self.net.send(self.arena.snapshot())
                if self.arena.phase == "end" and not self.arena.rewarded:
                    self.finish_fight()
        self.draw()

    def net_host_frame(self, dt):
        last_in = None
        for msg in self.net.poll():
            t = msg.get("t")
            if t == "in":
                last_in = msg.get("d")
            elif t == "fat":
                self.arena.fatality_feed(msg.get("ev", ()))
            elif t == "leave":
                self.net_dropped("Друг покинул бой")
                return
        if last_in is not None and isinstance(last_in, dict) and {
                "move", "jump", "crouch", "attack", "cast"} <= last_in.keys():
            self.arena.remote_inp = last_in

    def net_mirror_frame(self, dt):
        dropped = False
        for msg in self.net.poll():
            t = msg.get("t")
            if t == "snap":
                self.arena.pending_snap = msg
            elif t == "start":
                self.net_start_from_host(msg)
                return
            elif t == "leave":
                dropped = True
        if dropped or not self.net.connected:
            self.net_dropped("Соединение потеряно")

    def net_dropped(self, why):
        self.leave_net()
        self.arena = None
        self.set_state("menu")
        self.toasts.append((why, "", time.time() + 4.0))

    def net_start_from_host(self, msg):
        self.net_map = msg.get("map", 0)
        h1, h2 = msg.get("h1"), msg.get("h2")
        if h1 not in HEROES or h2 not in HEROES:
            self.net_dropped("Некорректный выбор героя")
            return
        self.start_net_fight(h2, h1, self.net_map, mirror=True)

    def finish_fight(self):
        a = self.arena
        a.rewarded = True
        st = self.save["stats"]
        exp_gain = 0
        if a.net:
            exp_gain = 30 if a.win else 12
            if a.win:
                st["online_wins"] = st.get("online_wins", 0) + 1
            if a.fatality_done and a.win:
                st["fatalities"] = st.get("fatalities", 0) + 1
            if a.fatality_gems:
                self.earn_gems(a.fatality_gems)
            if a.reward:
                self.earn(a.reward)
            self._count_arena_stats(st, a)
            a.exp_gain = exp_gain
            self.add_exp(exp_gain)
            self.persist()
            return
        if a.survival:
            waves = max(0, a.wave - 1)
            exp_gain = 10 * waves + max(0, waves - 3) * 5
            st["waves"] += waves
            frag_gains = self.drop_fragments(waves)
            if frag_gains:
                a.frag_gains = frag_gains
        elif a.martyr:
            exp_gain = 70 if a.win else max(10, int(a.dmg_dealt // 15))
            if a.win:
                st["martyr_wins"] = st.get("martyr_wins", 0) + 1
                self.earn_gems(a.martyr_gems)
                a.reward = 0
            st["max_damage"] = max(st.get("max_damage", 0), int(a.dmg_dealt))
        elif a.win:
            if a.fair:
                exp_gain = 30 + 6 * a.level
                st["fair_wins"] = st.get("fair_wins", 0) + 1
            else:
                exp_gain = 40 + 8 * a.level + (20 if a.boss else 0)
                st["wins"] += 1
                if a.boss:
                    st["bosses"] += 1
        else:
            exp_gain = 12
        if a.quality_finish:
            st["finishers"] += a.quality_finish
            if a.win:
                a.finish_bonus = FINISHER_BONUS * a.quality_finish
                a.reward += a.finish_bonus
                exp_gain += FINISHER_BONUS * a.quality_finish
        if a.fatality_done and a.win:
            st["fatalities"] = st.get("fatalities", 0) + 1
        if a.fatality_gems:
            self.earn_gems(a.fatality_gems)
        a.exp_gain = exp_gain
        self._count_arena_stats(st, a)
        st["max_combo"] = max(st["max_combo"], a.max_combo)
        if a.reward:
            self.earn(a.reward)
        if a.win and not a.survival and not a.fair:
            self.bot_level += 1
        if self.camp_ctx and a.win:
            idx, stage = self.camp_ctx
            rec = self.save["camp"].setdefault(str(idx), {"stage": 0, "done": False})
            if stage > rec["stage"]:
                rec["stage"] = stage
                r = campaign.CAMPAIGNS[idx]["reward"]
                if r["type"] == "hero":
                    if campaign.is_final(idx, stage) and not rec["done"]:
                        hero = r["hero"]
                        if hero not in self.owned:
                            self.owned.append(hero)
                        st["buys"] = st.get("buys", 0) + 1
                        self.toasts.append(("ЭКСКЛЮЗИВ: %s!" % hero, "", time.time() + 5.0))
                elif r["type"] == "blueprint":
                    if campaign.is_final(idx, stage) and not rec["done"]:
                        for _ in range(max(1, int(r.get("bps", 2)))):
                            aid_bp0 = self.grant_blueprint()
                            if aid_bp0:
                                self.toasts.append(("ЧЕРТЁЖ: " + artifacts.ART_BY_ID[aid_bp0]["name"],
                                                    "", time.time() + 5.0))
                elif r["type"] == "gems":
                    gm = campaign.first_clear_gems(stage)
                    self.earn_gems(gm)
                    self.toasts.append(("НАГРАДА: +%d САМОЦВЕТОВ" % gm, "", time.time() + 5.0))
                bonus = campaign.first_clear_coins(stage)
                self.earn(bonus)
                a.reward += bonus
                st["camp_stages"] += 1
            aid_bp = self.drop_blueprint(stage)
            if aid_bp:
                self.toasts.append(("РИСУНОК: " + artifacts.ART_BY_ID[aid_bp]["name"],
                                    "", time.time() + 5.0))
                if campaign.is_final(idx, stage) and not rec["done"]:
                    rec["done"] = True
                    self.toasts.append(("КАМПАНИЯ ЗАВЕРШЕНА!", "", time.time() + 5.0))
            else:
                bonus = campaign.replay_reward(stage)
                self.earn(bonus)
                a.reward += bonus
            exp_gain += 50 + 6 * stage
        st["camps"] = sum(1 for ci in range(len(campaign.CAMPAIGNS))
                          if campaign.camp_done(self.save, ci))
        self.add_exp(exp_gain)
        self.persist()

    def _count_arena_stats(self, st, a):
        for key in ("specials", "ults", "parries", "strikes", "injuries", "myth_ults",
                    "casts", "bleeds", "chains", "saws", "roars", "aoes", "haze",
                    "legend_ults", "supreme_ults", "headshots", "traps"):
            st[key] = st.get(key, 0) + a.stats.get(key, 0)

    def drop_fragments(self, waves):
        gains = []
        for wave in range(1, waves + 1):
            chance = SURV_FRAG_BOSS_CHANCE if wave % 5 == 0 else SURV_FRAG_CHANCE
            if random.random() < chance:
                nat = random.choice(artifacts.NATURES)
                self.save["frags"][nat] = self.save["frags"].get(nat, 0) + 1
                gains.append(nat)
        if gains:
            self.persist()
            for nat in gains:
                self.toasts.append(("ФРАГМЕНТ: " + artifacts.NATURE_LABEL[nat], "",
                                    time.time() + 4.0))
        return gains

    def grant_blueprint(self):
        bps = self.save.setdefault("bps", {})
        pool = [a["id"] for a in artifacts.ARTIFACTS if a.get("bps")
                and a["id"] not in self.save["arts"]
                and bps.get(a["id"], 0) < a["bps"]]
        if not pool:
            return None
        aid = random.choice(pool)
        bps[aid] = bps.get(aid, 0) + 1
        return aid

    def drop_blueprint(self, stage):
        if stage < 3 or random.random() > CAMP_BP_CHANCE:
            return None
        return self.grant_blueprint()

    def camp_next(self):
        if not self.camp_ctx or not self.arena.win:
            return None
        idx, stage = self.camp_ctx
        if stage >= campaign.CAMPAIGNS[idx]["stages"]:
            return None
        return ("campaign", idx, stage + 1)

    def draw_level_bar(self, cv, x, y):
        need = exp_to_next(self.plvl)
        frac = clamp01(self.exp / need) if need > 0 else 0.0
        cv.create_text(x, y, text="УРОВЕНЬ %d" % self.plvl, anchor="w", fill=COL_GOLD,
                       font=F_MID, tags=("dyn",))
        cv.create_rectangle(x, y + 8, x + 200, y + 22, fill="#160404", outline="#5a1c10",
                            width=1, tags=("dyn",))
        if frac > 0:
            cv.create_rectangle(x + 2, y + 10, x + 2 + int(196 * frac), y + 20,
                                fill=COL_ORANGE, outline="", tags=("dyn",))
        cv.create_text(x + 208, y + 15, text="%d/%d EXP" % (self.exp, need), anchor="w",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))

    def draw_toasts(self, cv):
        now = time.time()
        self.toasts = [t for t in self.toasts if now < t[2]]
        for i, (name, reward, _) in enumerate(self.toasts[:3]):
            y = 96 + i * 30
            txt = name
            if isinstance(reward, str) and reward:
                txt += "  " + reward
            elif isinstance(reward, int) and reward:
                txt += "  +%d МОНЕТ" % reward
            cv.create_text(W / 2 + 2, y + 2, text=txt, font=F_SMALL, fill="#2a0503", tags=("dyn",))
            cv.create_text(W / 2, y, text=txt, font=F_SMALL, fill=COL_GOLD, tags=("dyn",))

    def draw_menu(self):
        cv = self.cv
        cx = W // 2
        self.ui.button(cv, cx - 110, 300, cx + 110, 490, "PLAY", self.goto_mode, font=F_SQUARE)
        self.ui.button(cv, cx - 160, 500, cx + 160, 550, "HEROES", self.goto_heroes, font=F_MID)
        self.ui.button(cv, cx - 160, 554, cx + 160, 604, "SHOP", self.goto_shop, font=F_MID)
        self.ui.button(cv, cx - 160, 608, cx + 160, 658, "INFO", self.goto_info, font=F_MID)
        self.ui.button(cv, cx - 160, 662, cx + 160, 712, "AWARDS", self.goto_achievements, font=F_MID)
        self.draw_gear(cv)
        self.draw_door(cv)
        self.ui.coins(cv, 30, H - 40, self.coins)
        self.ui.gems(cv, 240, H - 40, self.gems)
        self.draw_level_bar(cv, 30, 24)
        cv.create_text(W - 30, H - 80, text="БОТ: УР. %d" % self.bot_level, anchor="e",
                       fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        cv.create_text(W / 2, H - 14, text="ЛКМ — атака · WASD — движение · E — пинок · S+ЛКМ — апперкот · F — парирование · 1-5 — способности · 1+4 — миф-ульта · A+S/W+S — спецприёмы",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))

    def draw_gear(self, cv):
        x0, y0, x1, y1 = W - 76, H - 76, W - 28, H - 28
        mx, my = self.mouse
        hov = x0 <= mx <= x1 and y0 <= my <= y1
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        col = COL_GOLD if hov else "#a13414"
        for i in range(8):
            a = i * math.pi / 4 + math.pi / 8
            cv.create_line(cx + math.cos(a) * 16, cy + math.sin(a) * 16,
                           cx + math.cos(a) * 22, cy + math.sin(a) * 22,
                           fill=col, width=3, tags=("dyn",))
        cv.create_oval(cx - 15, cy - 15, cx + 15, cy + 15, outline=col, width=3, tags=("dyn",))
        cv.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, outline=col, width=2, tags=("dyn",))
        self.buttons.append((x0, y0, x1, y1, self.goto_settings))

    def draw_door(self, cv):
        x0, y0, x1, y1 = W - 128, H - 76, W - 80, H - 28
        mx, my = self.mouse
        hov = x0 <= mx <= x1 and y0 <= my <= y1
        col = COL_GOLD if hov else "#a13414"
        cv.create_rectangle(x0 + 6, y0 + 2, x1 - 6, y1 - 2, outline=col, width=3, tags=("dyn",))
        cv.create_polygon(x0 + 6, y0 + 2, x0 + 19, y0 + 8, x0 + 19, y1 - 8, x0 + 6, y1 - 2,
                          fill="#7a2a10", outline=col, width=2, tags=("dyn",))
        cv.create_oval(x1 - 21, (y0 + y1) / 2 - 3, x1 - 15, (y0 + y1) / 2 + 3,
                       fill=col, outline="", tags=("dyn",))
        self.buttons.append((x0, y0, x1, y1, self.quit_game))

    def quit_game(self):
        try:
            self.persist()
            self.sfx.play("door")
        except Exception:
            pass
        try:
            self.music.stop()
        except Exception:
            pass
        self.destroy()

    def goto_settings(self):
        self.set_state("settings")

    def draw_settings(self):
        cv = self.cv
        s = self.save["settings"]
        cv.create_text(W / 2 + 3, 93, text="НАСТРОЙКИ", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="НАСТРОЙКИ", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        rows = (("МУЗЫКА", "music"), ("ЗВУКИ", "sfx"))
        for i, (label, key) in enumerate(rows):
            y = 200 + i * 120
            val = float(s[key])
            cv.create_text(W / 2 - 340, y + 20, text=label, anchor="w", fill=COL_ORANGE, font=F_MID, tags=("dyn",))
            bx0, bx1 = W / 2 - 160, W / 2 + 320
            cv.create_rectangle(bx0, y, bx1, y + 40, fill="#160607", outline="#5a1c10", width=2, tags=("dyn",))
            if val > 0:
                cv.create_rectangle(bx0 + 4, y + 4, bx0 + 4 + int((bx1 - bx0 - 8) * val), y + 36,
                                    fill=COL_ORANGE, outline="", tags=("dyn",))
            cv.create_text(bx1 + 50, y + 20, text="%d%%" % round(val * 100), fill=COL_GOLD,
                           font=F_MID, tags=("dyn",))
            self.ui.button(cv, bx0 - 90, y, bx0 - 20, y + 40, "-",
                           lambda k=key: self._set_vol(k, -0.1), font=F_MID)
            self.ui.button(cv, bx1 + 90, y, bx1 + 160, y + 40, "+",
                           lambda k=key: self._set_vol(k, 0.1), font=F_MID)
            self.buttons.append((bx0, y, bx1, y + 40,
                                 lambda k=key, bx0=bx0, bx1=bx1: self._bar_vol(k, bx0, bx1)))
        toggles = (("БЕСШУМНЫЙ РЕЖИМ", "mute"), ("ТРЯСКА ЭКРАНА", "shake"), ("КРОВЬ", "blood"))
        for i, (label, key) in enumerate(toggles):
            y = 470 + i * 76
            on = bool(s[key])
            cv.create_text(W / 2 - 340, y + 22, text=label, anchor="w", fill=COL_ORANGE, font=F_MID, tags=("dyn",))
            self.ui.button(cv, W / 2 - 60, y, W / 2 + 140, y + 44,
                           "ВКЛ" if on else "ВЫКЛ",
                           lambda k=key: self._toggle_set(k), font=F_SMALL)
        wm = s.get("win_mode", "windowed")
        if wm not in WIN_MODES:
            wm = "windowed"
        y = 470 + 3 * 76
        cv.create_text(W / 2 - 340, y + 22, text="РЕЖИМ ОКНА", anchor="w",
                       fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        self.ui.button(cv, W / 2 - 60, y, W / 2 + 140, y + 44, WIN_MODE_LABEL[wm],
                       self._cycle_win_mode, font=F_SMALL)
        cv.create_text(W / 2 + 170, y + 22, text="ТОЛЬКО ЭТИ РЕЖИМЫ", anchor="w",
                       fill="#7a4030", font=F_TINY, tags=("dyn",))
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def _cycle_win_mode(self):
        s = self.save["settings"]
        wm = s.get("win_mode", "windowed")
        if wm not in WIN_MODES:
            wm = "windowed"
        s["win_mode"] = WIN_MODES[(WIN_MODES.index(wm) + 1) % len(WIN_MODES)]
        self.apply_fullscreen()
        self.audio.apply(s)
        self.persist()

    def _set_vol(self, key, d):
        s = self.save["settings"]
        s[key] = max(0.0, min(1.0, round(float(s[key]) + d, 2)))
        self.audio.apply(s)
        self.persist()

    def _bar_vol(self, key, bx0, bx1):
        mx = self.mouse[0]
        self.save["settings"][key] = max(0.0, min(1.0, round((mx - bx0) / (bx1 - bx0), 2)))
        self.audio.apply(self.save["settings"])
        self.persist()

    def _toggle_set(self, key):
        s = self.save["settings"]
        s[key] = not s[key]
        self.audio.apply(s)
        self.persist()

    def _fs_on_map(self, _e=None):
        try:
            self.unbind("<Map>")
        except Exception:
            pass
        self.after(60, self.apply_fullscreen)

    def apply_fullscreen(self):
        wm = self.save["settings"].get("win_mode", "windowed")
        if wm not in WIN_MODES:
            wm = "windowed"
        try:
            self.resizable(False, False)
            if wm in ("boxed", "fullscreen"):
                self.attributes("-fullscreen", wm == "fullscreen")
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                if sw and sh:
                    scale = min(sw / float(W), sh / float(H))
                    self.geometry("%dx%d+0+0" % (sw, sh))
                    self.cv.config(width=sw, height=sh)
                    self.cv.place(x=0, y=0)
                    self._vs = (scale, (sw - W * scale) / 2.0, (sh - H * scale) / 2.0)
            else:
                self.attributes("-fullscreen", False)
                self.cv.config(width=W, height=H)
                self.cv.place(x=0, y=0)
                self.geometry(self._home_geom)
                self._vs = (1.0, 0.0, 0.0)
        except Exception:
            return
        if wm == "boxed":
            try:
                self.state("zoomed")
            except Exception:
                try:
                    self.geometry("%dx%d+0+0" % (self.winfo_screenwidth(), self.winfo_screenheight()))
                except Exception:
                    pass
            self.after(180, self._fit_boxed)
            return
        self.set_state(self.state)

    def _fit_boxed(self):
        try:
            self.update_idletasks()
            ww, wh = self.winfo_width(), self.winfo_height()
            if ww > 60 and wh > 60:
                scale = min(ww / float(W), wh / float(H))
                self.cv.config(width=ww, height=wh)
                self.cv.place(x=0, y=0)
                self._vs = (scale, (ww - W * scale) / 2.0, (wh - H * scale) / 2.0)
                self.set_state(self.state)
        except Exception:
            pass

    def _apply_vs(self, cv):
        s, tx, ty = self._vs
        if s != 1.0 or tx or ty:
            cv.scale("all", 0, 0, s, s)
            cv.move("all", tx, ty)
            cv.move("bg", -tx, -ty)
            cv.scale("bg", 0, 0, 1.0 / s, 1.0 / s)

    def draw_mode(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 123, text="PLAY", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 120, text="PLAY", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.button(cv, W / 2 - 340, 170, W / 2 - 20, 260, "VS BOT", self.goto_select, font=F_SQUARE)
        self.ui.button(cv, W / 2 + 20, 170, W / 2 + 340, 260, "SURVIVAL",
                       lambda: self.goto_select("survival"), font=F_SQUARE)
        self.ui.button(cv, W / 2 - 340, 280, W / 2 - 20, 370, "CAMPAIGN",
                       self.goto_campaigns, font=F_SQUARE)
        self.ui.button(cv, W / 2 + 20, 280, W / 2 + 340, 370, "MARTYR",
                       lambda: self.goto_select("martyr"), font=F_SQUARE)
        self.ui.button(cv, W / 2 - 340, 390, W / 2 - 20, 480, "ONLINE",
                       self.goto_online, font=F_SQUARE)
        self.ui.button(cv, W / 2 + 20, 390, W / 2 + 340, 480, "FRIEND",
                       self.goto_net, font=F_SQUARE)
        self.ui.button(cv, W / 2 - 340, 500, W / 2 + 340, 580, "FAIR FIGHT",
                       lambda: self.goto_select("fair"), font=F_SQUARE)
        cv.create_text(W / 2, 618, text="BOT: LEVEL %d" % self.bot_level, fill=COL_ORANGE,
                       font=F_MID, tags=("dyn",))
        if self.bot_level % 10 == 0:
            cv.create_text(W / 2, 646, text="!! WARNING: THIS IS A BOSS !!", fill=COL_RED, font=F_MID, tags=("dyn",))
        cv.create_text(W / 2, 670, text="SURVIVAL: enemy waves · every 5th is a mini-boss · artifact fragments",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))
        cv.create_text(W / 2, 692, text="MARTYR: win = 100 gems · ONLINE/FRIEND: full balance, no artifacts",
                       fill=COL_GEM, font=F_TINY, tags=("dyn",))
        cv.create_text(W / 2, 714, text="FAIR FIGHT: enemy hero is another fighter · power equalized to yours",
                       fill="#ffefd0", font=F_TINY, tags=("dyn",))
        self.ui.coins(cv, W / 2 - 90, 748, self.coins)
        self.ui.gems(cv, W / 2 + 60, 748, self.gems)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def draw_net_scan(self):
        cv = self.cv
        cx = W // 2
        online = self.net_mode == "online"
        title = "ONLINE · ПОИСК ИГРОКА" if online else "FRIEND · LAN"
        sub = ("АВТОМАТИЧЕСКИЙ ПОИСК ПРОТИВНИКА · ПОЛНЫЙ БАЛАНС" if online
               else "БОЙ С ДРУГОМ ПО ЛОКАЛЬНОЙ СЕТИ · ПОЛНЫЙ БАЛАНС")
        cv.create_text(cx + 3, 93, text=title, font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(cx, 90, text=title, font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        cv.create_text(cx, 136, text=sub, fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
        cv.create_text(cx, 162, text="Ваш компьютер: %s%s" % (netplay.host_name(),
                       "" if (self.disc and self.disc.hosting) else " · режим подключения"),
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))
        cv.create_rectangle(cx - 340, 190, cx + 340, 700, fill="#1a0908", outline="#5a1c10",
                            width=2, tags=("dyn",))
        cv.create_text(cx, 216, text="КОМПЬЮТЕРЫ В СЕТИ", fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        if not self.net_peers:
            if online:
                cv.create_text(cx, 300, text="ПОИСК ПРОТИВНИКА...", fill="#8a4a20", font=F_SMALL, tags=("dyn",))
                cv.create_text(cx, 330, text="Противник должен открыть вкладку ONLINE — соединение произойдёт само",
                               fill=COL_SAND, font=F_TINY, tags=("dyn",))
            else:
                cv.create_text(cx, 300, text="ПОКА НИКОГО НЕ НАЙДЕНО...", fill="#8a4a20", font=F_SMALL, tags=("dyn",))
                cv.create_text(cx, 330, text="Друг должен запустить IMMY и открыть вкладку FRIEND", fill=COL_SAND,
                               font=F_TINY, tags=("dyn",))
        elif online:
            cv.create_text(cx, 226, text="ПРОТИВНИК НАЙДЕН — СОЕДИНЯЕМ...", fill="#8aff8a", font=F_SMALL,
                           tags=("dyn",))
        for i, (ip, name) in enumerate(self.net_peers[:10]):
            y0 = 250 + i * 44
            self.ui.button(cv, cx - 300, y0, cx + 300, y0 + 38, "%s · %s" % (name, ip),
                           lambda ip=ip, name=name: self.net_connect(ip, name), font=F_SMALL)
        cv.create_text(cx, 730, text=self.net_msg, fill=COL_RED if "НЕ" in self.net_msg else COL_GEM,
                       font=F_SMALL, tags=("dyn",))
        self.ui.button(cv, cx - 160, 760, cx + 160, 810, "ОБНОВИТЬ", self.net_refresh, font=F_SMALL)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.net_back, font=F_SMALL)

    def net_refresh(self):
        if self.disc is not None:
            self.net_peers, self.net_sids = self.disc.scan(self.net_mode)
            self.net_msg = ""

    def net_back(self):
        self.leave_net()
        self.arena = None
        self.set_state("menu")

    def draw_net_select(self):
        cv = self.cv
        sel = self.net_my_pick or self.hero_sel
        keys = sorted_keys(list(HEROES))
        per = 32
        pages = (len(keys) + per - 1) // per
        page = max(0, min(self.net_hero_page, pages - 1))
        self.net_hero_page = page
        cv.create_rectangle(24, 100, 560, 860, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(292, 122, text="ВСЕ БОЙЦЫ · БАЛАНС", fill=COL_ORANGE, font=F_MID, tags=("dyn"))
        for i, key in enumerate(keys[page * per:(page + 1) * per]):
            col, row = i % 4, i // 4
            x0 = 34 + col * 130
            y0 = 150 + row * 78
            x1, y1 = x0 + 122, y0 + 70
            my = key == self.net_my_pick
            fo = key == self.net_foe_pick
            rcol = RARITY_COLOR.get(HEROES[key]["rarity"], "#5a1c10")
            cv.create_rectangle(x0, y0, x1, y1, fill="#2a0f0a" if my else "#200a08",
                                outline=COL_GOLD if my else ("#ff2a8a" if fo else rcol),
                                width=3 if (my or fo) else 2, tags=("dyn"))
            draw_hero_icon(cv, key, x0 + 6, y0 + 6, 40)
            cv.create_text(x0 + 54, y0 + 14, text=key, anchor="w", fill=COL_GOLD, font=F_TINY, tags=("dyn"))
            cv.create_text(x0 + 54, y0 + 32, text=HEROES[key]["title"][:16], anchor="w", fill="#c9884a",
                           font=F_TINY, tags=("dyn"))
            if fo and not my:
                cv.create_text(x1 - 6, y0 + 58, text="ВРАГ", anchor="e", fill="#ff2a8a", font=F_TINY, tags=("dyn"))
            self.buttons.append((x0, y0, x1, y1, lambda k=key: self.net_pick(k)))
        cv.create_text(292, 824, text="СТРАНИЦА %d / %d" % (page + 1, pages), fill=COL_SAND,
                       font=F_TINY, tags=("dyn",))
        if page > 0:
            self.ui.button(cv, 60, 806, 140, 842, "<", lambda: self._net_hero_page(-1), font=F_SMALL)
        if page < pages - 1:
            self.ui.button(cv, 440, 806, 520, 842, ">", lambda: self._net_hero_page(1), font=F_SMALL)

        cx = 800
        for j, (label, key, colr) in enumerate((("ВЫ", self.net_my_pick, COL_GOLD),
                                                ("ВРАГ", self.net_foe_pick, "#ff2a8a"))):
            bx = cx - 210 + j * 220
            cv.create_rectangle(bx - 95, 130, bx + 95, 430, fill="#1a0908",
                                outline=colr if key else "#5a1c10", width=3, tags=("dyn"))
            cv.create_text(bx, 156, text=label, fill=colr, font=F_MID, tags=("dyn"))
            if key:
                draw_hero_icon(cv, key, bx - 60, 190, 120, border=False)
                cv.create_text(bx, 350, text=HEROES[key]["name"], fill=COL_GOLD, font=F_SMALL, tags=("dyn"))
                rar = RARITY_LABEL.get(HEROES[key]["rarity"], "")
                cv.create_text(bx, 376, text=rar, fill=RARITY_COLOR.get(HEROES[key]["rarity"], COL_SAND),
                               font=F_TINY, tags=("dyn"))
                cv.create_text(bx, 402, text="СИЛА: БАЛАНС 1.00", fill=COL_SAND, font=F_TINY, tags=("dyn"))
            else:
                cv.create_text(bx, 280, text="ВЫБОР...", fill="#8a4a20", font=F_SMALL, tags=("dyn"))
        cv.create_text(cx, 470, text="В битве с другом сила редкости отключена — решают механики и комбо",
                       fill=COL_GEM, font=F_TINY, tags=("dyn"))

        hero = HEROES[sel]
        cv.create_rectangle(1040, 100, 1576, 860, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn"))
        cv.create_text(1308, 132, text=sel, fill=COL_GOLD, font=F_BIG, tags=("dyn"))
        cv.create_text(1308, 162, text=hero["title"], fill="#ff5a1a", font=F_SMALL, tags=("dyn"))
        cv.create_text(1308, 184, text="ДРУЖЕСКИЙ БОЙ · СИЛА 1.00", fill=COL_GEM, font=F_TINY, tags=("dyn"))
        for li, ln2 in enumerate(self._wrap(hero["desc"], 470, 11, cap=4)):
            cv.create_text(1070, 226 + li * 14, text=ln2, anchor="w", fill="#e8c9a0",
                           font=F_TINY, tags=("dyn",))
        cv.create_text(1070, 272, text="СТАТЫ", anchor="w", fill=COL_ORANGE, font=F_SMALL, tags=("dyn"))
        for j, (skey, sname, scol) in enumerate(STAT_NAMES):
            val = hero["stats"][skey]
            yy = 290 + j * 20
            cv.create_text(1070, yy, text=sname, anchor="w", fill=COL_SAND, font=F_TINY, tags=("dyn"))
            cv.create_rectangle(1150, yy - 5, 1490, yy + 5, fill="#160607", outline="#5a1c10",
                                width=1, tags=("dyn"))
            cv.create_rectangle(1150, yy - 5, 1150 + val * 24, yy + 5, fill=scol, outline="", tags=("dyn"))
        cv.create_text(1070, 366, text="СПОСОБНОСТИ", anchor="w", fill=COL_ORANGE, font=F_SMALL, tags=("dyn"))
        y = 386
        for i, ab in enumerate(hero["abilities"]):
            cv.create_text(1070, y, text="[%d] %s" % (i + 1, ab["name"]), anchor="w",
                           fill=COL_GOLD, font=F_SMALL, tags=("dyn"))
            cv.create_text(1560, y, text="%dс" % ab["cd"], anchor="e", fill="#ff5a1a", font=F_SMALL, tags=("dyn"))
            cv.create_text(1076, y + 15, text=ab["desc"], anchor="w", fill=COL_SAND, font=F_TINY,
                           width=470, tags=("dyn"))
            y += 17 + max(1, -(-len(ab["desc"]) // 58)) * 13 + 8
        sps = hero.get("specials", ())
        if sps and y < 760:
            cv.create_text(1070, y + 2, text="СПЕЦПРИЁМЫ", anchor="w", fill=COL_ORANGE, font=F_SMALL, tags=("dyn"))
            for sp in sps:
                y += 20
                cv.create_text(1070, y, text="[%s] %s" % (sp["combo"].upper(), sp["name"]), anchor="w",
                               fill="#ffd24a", font=F_SMALL, tags=("dyn"))

        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.net_back, font=F_SMALL)
        if self.net_role == "host":
            ready = self.net_my_pick and self.net_foe_pick
            if ready:
                self.ui.button(cv, cx - 150, 830, cx + 150, 886, "В БОЙ!", self.net_start, font=F_BIG)
            else:
                cv.create_text(cx, 858, text="ОЖИДАНИЕ ВЫБОРА ОБОИХ ИГРОКОВ...", fill=COL_ORANGE,
                               font=F_SMALL, tags=("dyn"))
        else:
            cv.create_text(cx, 858, text="Хост начинает бой..." if self.net_foe_pick else "Выберите бойца — хост начнёт бой",
                           fill=COL_ORANGE, font=F_SMALL, tags=("dyn"))

    def _net_hero_page(self, d):
        pages = (len(HEROES) + 31) // 32
        self.net_hero_page = max(0, min(pages - 1, self.net_hero_page + d))

    def net_pick(self, key):
        self.net_my_pick = key
        self.hero_sel = key
        if self.net is not None:
            self.net.send({"t": "pick", "hero": key})

    def net_poll_select(self):
        if self.net is None or not self.net.connected:
            self.net_dropped("Соединение потеряно")
            return
        for msg in self.net.poll():
            t = msg.get("t")
            if t == "hello":
                self.net_peer_name = str(msg.get("name", ""))[:22]
            elif t == "pick":
                k = msg.get("hero")
                if k in HEROES:
                    self.net_foe_pick = k
            elif t == "start":
                self.net_start_from_host(msg)
                return
            elif t == "leave":
                self.net_dropped("Друг покинул лобби")
                return

    def net_start(self):
        if self.net_role != "host" or not self.net_my_pick or not self.net_foe_pick:
            return
        self.net_map = random.randrange(len(MAPS))
        self.net.send({"t": "start", "map": self.net_map,
                       "h1": self.net_my_pick, "h2": self.net_foe_pick})
        self.start_net_fight(self.net_my_pick, self.net_foe_pick, self.net_map, mirror=False)

    def start_net_fight(self, my, foe, map_idx, mirror):
        self.arena = Arena(my, foe, 1, False, map=MAPS[map_idx % len(MAPS)], net=True, mirror=mirror)
        self.set_state("fight")

    def draw_campaigns(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="CAMPAIGN", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="CAMPAIGN", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.coins(cv, W - 360, 50, self.coins)
        self.ui.gems(cv, W - 190, 50, self.gems)
        per = 18
        pages = (len(campaign.CAMPAIGNS) + per - 1) // per
        page = max(0, min(self.camp_page, pages - 1))
        self.camp_page = page
        for j, i in enumerate(range(page * per, (page + 1) * per)):
            if i >= len(campaign.CAMPAIGNS):
                break
            c = campaign.CAMPAIGNS[i]
            col, row = j % 3, j // 3
            x0 = 24 + col * 520
            y0 = 126 + row * 92
            x1, y1 = x0 + 500, y0 + 86
            locked = not campaign.unlocked(i, self.save)
            prog = campaign.camp_progress(self.save, i)
            done = campaign.camp_done(self.save, i)
            cv.create_rectangle(x0, y0, x1, y1, fill="#1a0908",
                                outline=c["color"] if not locked else "#3a1410", width=3, tags=("dyn",))
            cv.create_text(x0 + 16, y0 + 24, text=c["name"], anchor="w", font=F_SMALL,
                           fill=c["color"] if not locked else "#6a3020", tags=("dyn",))
            cv.create_text(x0 + 16, y0 + 46, text=c["desc"][:56], anchor="w", fill=COL_SAND,
                           font=F_TINY, tags=("dyn",))
            cv.create_text(x0 + 16, y0 + 68, text=campaign.reward_label(c), anchor="w",
                           fill=COL_GOLD, font=F_TINY, tags=("dyn",))
            if locked:
                if i == 0:
                    lock_txt = "УРОВЕНЬ %d" % campaign.UNLOCK_PLVL
                else:
                    lock_txt = "ЗАВЕРШИТЕ ПРЕДЫДУЩУЮ"
                cv.create_text(x1 - 16, y0 + 24, text=lock_txt, anchor="e", fill="#8a4a20",
                               font=F_TINY, tags=("dyn",))
            else:
                cv.create_text(x1 - 16, y0 + 24, text="%d/%d%s" % (prog, c["stages"],
                               " ✓" if done else ""), anchor="e", fill=COL_ORANGE,
                               font=F_TINY, tags=("dyn",))
                self.ui.button(cv, x1 - 130, y0 + 44, x1 - 16, y0 + 78, "ВОЙТИ",
                               lambda idx=i: self.open_camp(idx), font=F_SMALL)
        cv.create_text(W / 2, 852, text="СТРАНИЦА %d / %d" % (page + 1, pages),
                       fill=COL_SAND, font=F_SMALL, tags=("dyn",))
        if page > 0:
            self.ui.button(cv, W / 2 - 260, 836, W / 2 - 180, 872, "<",
                           lambda: self._camp_page(-1), font=F_SMALL)
        if page < pages - 1:
            self.ui.button(cv, W / 2 + 180, 836, W / 2 + 260, 872, ">",
                           lambda: self._camp_page(1), font=F_SMALL)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def _camp_page(self, d):
        pages = (len(campaign.CAMPAIGNS) + 17) // 18
        self.camp_page = max(0, min(pages - 1, self.camp_page + d))

    def draw_camp_stages(self):
        cv = self.cv
        c = campaign.CAMPAIGNS[self.camp_idx]
        prog = campaign.camp_progress(self.save, self.camp_idx)
        cv.create_text(W / 2 + 3, 93, text=c["name"], font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text=c["name"], font=F_BIG, fill=c["color"], tags=("dyn",))
        cv.create_text(W / 2, 126, text=campaign.reward_label(c), fill=COL_GOLD,
                       font=F_SMALL, tags=("dyn",))
        cv.create_text(W / 2, 148, text="Ступени открываются по порядку · финальная ступень — БОСС кампании",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))
        cols = 5
        cw, ch = 220, 110
        gx = W / 2 - (cols * (cw + 14) - 14) / 2
        for n in range(1, c["stages"] + 1):
            col, row = (n - 1) % cols, (n - 1) // cols
            x0 = gx + col * (cw + 14)
            y0 = 170 + row * (ch + 14)
            x1, y1 = x0 + cw, y0 + ch
            final = campaign.is_final(self.camp_idx, n)
            open_it = n <= prog + 1
            cleared = n <= prog
            colr = c["color"] if not final else COL_RED
            cv.create_rectangle(x0, y0, x1, y1, fill="#1a0908",
                                outline=COL_GOLD if cleared else (colr if open_it else "#3a1410"),
                                width=3 if cleared else 2, tags=("dyn",))
            cv.create_text(x0 + cw / 2, y0 + 26, text="СТУПЕНЬ %d" % n, font=F_MID,
                           fill=COL_GOLD if open_it else "#6a3020", tags=("dyn",))
            label = "БОСС · УР. %d" % campaign.stage_level(self.camp_idx, n) if final \
                else "БОТ · УР. %d" % campaign.stage_level(self.camp_idx, n)
            cv.create_text(x0 + cw / 2, y0 + 50, text=label, font=F_TINY,
                           fill=COL_RED if final else COL_ORANGE, tags=("dyn",))
            if cleared:
                cv.create_text(x0 + cw / 2, y0 + 74, text="ПРОЙДЕНО", font=F_TINY,
                               fill="#8aff8a", tags=("dyn",))
            elif open_it:
                cv.create_text(x0 + cw / 2, y0 + 74, text="В БОЙ", font=F_TINY,
                               fill=COL_GOLD, tags=("dyn",))
                self.buttons.append((x0, y0, x1, y1,
                                     lambda s=n: self.goto_select(("campaign", self.camp_idx, s))))
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_campaigns, font=F_SMALL)

    def draw_achievements(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="AWARDS", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="AWARDS", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.coins(cv, W - 360, 50, self.coins)
        self.ui.gems(cv, W - 190, 50, self.gems)
        stats = self.save["stats"]
        claimed = set(self.save["ach"])
        per = 16
        pages = (len(achievements.ACHIEVEMENTS) + per - 1) // per
        page = max(0, min(self.ach_page, pages - 1))
        chunk = achievements.ACHIEVEMENTS[page * per:(page + 1) * per]
        for i, a in enumerate(chunk):
            y0 = 136 + i * 36
            got = a["id"] in claimed
            cur = min(stats.get(a["stat"], 0), a["goal"])
            cv.create_rectangle(60, y0, W - 60, y0 + 32, fill="#1a0908" if got else "#160607",
                                outline=COL_GOLD if got else "#3a1410", width=1, tags=("dyn",))
            cv.create_text(76, y0 + 16, text=a["name"], anchor="w", font=F_SMALL,
                           fill=COL_GOLD if got else "#8a4a20", tags=("dyn",))
            cv.create_text(340, y0 + 16, text=a["desc"], anchor="w", font=F_TINY,
                           fill=COL_SAND if got else "#7a4030", tags=("dyn",))
            cv.create_text(W - 260, y0 + 16, text="%d / %d" % (cur, a["goal"]), anchor="e",
                           font=F_TINY, fill="#8aff8a" if got else COL_SAND, tags=("dyn",))
            if a.get("gems"):
                r = 6
                gx = W - 172
                cv.create_polygon(gx + r, y0 + 16 - r, gx + r * 1.7, y0 + 16, gx + r, y0 + 16 + r,
                                  gx + r * 0.3, y0 + 16, fill=COL_GEM, outline="#1a6a3a",
                                  width=1, tags=("dyn",))
                cv.create_text(W - 140, y0 + 16, text="+%d" % a["gems"], anchor="e",
                               font=F_TINY, fill=COL_GEM, tags=("dyn",))
            cv.create_text(W - 76, y0 + 16, text="+%d" % a["reward"], anchor="e", font=F_SMALL,
                           fill=COL_GOLD if got else "#6a5010", tags=("dyn",))
        cv.create_text(W / 2, 780, text="СТРАНИЦА %d / %d" % (page + 1, pages), font=F_SMALL,
                       fill=COL_SAND, tags=("dyn",))
        if page > 0:
            self.ui.button(cv, W / 2 - 260, 760, W / 2 - 160, 800, "<",
                           lambda: self._ach_page(-1), font=F_SMALL)
        if page < pages - 1:
            self.ui.button(cv, W / 2 + 160, 760, W / 2 + 260, 800, ">",
                           lambda: self._ach_page(1), font=F_SMALL)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def _ach_page(self, d):
        pages = (len(achievements.ACHIEVEMENTS) + 15) // 16
        self.ach_page = max(0, min(pages - 1, self.ach_page + d))

    def draw_info(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="INFO", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="INFO", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        if self.info_page == 0:
            cv.create_text(W / 2, 136, text="УДАРЫ И КОМБО", font=F_MID, fill=COL_ORANGE, tags=("dyn",))
            lines = INFO_STRIKES
            step = 40
        elif self.info_page == 1:
            cv.create_text(W / 2, 136, text="МЕХАНИКИ ИГРЫ", font=F_MID, fill=COL_ORANGE, tags=("dyn",))
            lines = INFO_MECH
            step = 36
        else:
            cv.create_text(W / 2, 136, text="РЕЖИМЫ И РЕДКОСТИ", font=F_MID, fill=COL_ORANGE, tags=("dyn",))
            lines = INFO_MODES
            step = 40
        for i, (txt, colr) in enumerate(lines):
            cv.create_text(80, 180 + i * step, text=txt, anchor="w", font=F_SMALL,
                           fill=colr, tags=("dyn",))
        cv.create_text(W / 2, 812, text="Знание механик — половина победы. Тренируйся в режиме VS БОТ.",
                       fill=COL_GEM, font=F_TINY, tags=("dyn",))
        if self.info_page > 0:
            prev = ["< УДАРЫ", "< МЕХАНИКИ", "< МЕХАНИКИ"][self.info_page]
            self.ui.button(cv, W / 2 - 300, 820, W / 2 - 180, 860, prev,
                           lambda: self._info_page(-1), font=F_SMALL)
        if self.info_page < 2:
            nxt = ["МЕХАНИКИ >", "РЕЖИМЫ >"][self.info_page]
            self.ui.button(cv, W / 2 + 180, 820, W / 2 + 300, 860, nxt,
                           lambda: self._info_page(1), font=F_SMALL)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def _info_page(self, d):
        self.info_page = max(0, min(2, self.info_page + d))

    def draw_heroes(self, select_mode):
        cv = self.cv
        sel = self.hero_sel
        keys = sorted_keys([k for k in HEROES if k in self.owned]) if select_mode \
            else sorted_keys(list(HEROES))
        if sel not in keys and keys:
            sel = keys[0]
            self.hero_sel = sel
            self.preview = Fighter(sel, W / 2, 1, scale=2.4)
            self.preview.y = GROUND_Y - 19
        cv.create_rectangle(24, 100, 460, 860, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(242, 122, text="БОЙЦЫ", fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        per = 56
        pages = max(1, (len(keys) + per - 1) // per)
        page = max(0, min(self.hero_page, pages - 1))
        self.hero_page = page
        for i, key in enumerate(keys[page * per:(page + 1) * per]):
            col, row = i % 4, i // 4
            x0 = 32 + col * 108
            y0 = 150 + row * 46
            x1, y1 = x0 + 100, y0 + 40
            selected = key == sel
            rcol = RARITY_COLOR.get(HEROES[key]["rarity"], "#5a1c10")
            cv.create_rectangle(x0, y0, x1, y1, fill="#2a0f0a" if selected else "#200a08",
                                outline=COL_GOLD if selected else rcol,
                                width=3 if selected else 2, tags=("dyn",))
            draw_hero_icon(cv, key, x0 + 6, y0 + 6, 28)
            cv.create_text(x0 + 40, y0 + 12, text=key, anchor="w", fill=COL_GOLD, font=F_TINY, tags=("dyn",))
            if not select_mode and key not in self.owned:
                cv.create_text(x0 + 40, y0 + 30, text="%d" % HEROES[key]["price"],
                               anchor="w", fill="#8a4a20", font=F_TINY, tags=("dyn",))
            self.buttons.append((x0, y0, x1, y1, lambda k=key: self.pick_hero(k)))

        if len(keys) > per:
            cv.create_text(242, 826, text="СТРАНИЦА %d / %d" % (page + 1, pages),
                           fill=COL_SAND, font=F_TINY, tags=("dyn",))
            if page > 0:
                self.ui.button(cv, 40, 806, 120, 844, "<", lambda: self._hero_page(-1), font=F_SMALL)
            if page < pages - 1:
                self.ui.button(cv, 364, 806, 444, 844, ">", lambda: self._hero_page(1), font=F_SMALL)

        if self.preview is not None:
            cv.create_oval(W / 2 - 160, GROUND_Y - 38, W / 2 + 160, GROUND_Y + 4,
                           fill="#160607", outline="#5a1c10", width=2, tags=("dyn",))
            self.preview.render(cv)
            self.parts.draw(cv)

        hero = HEROES[sel]
        cv.create_rectangle(1140, 100, 1576, 860, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(1358, 132, text=sel, fill=COL_GOLD, font=F_BIG, tags=("dyn",))
        cv.create_text(1358, 162, text=hero["title"], fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
        rar = RARITY_LABEL.get(hero["rarity"], hero["rarity"].upper())
        rcol = RARITY_COLOR.get(hero["rarity"], COL_SAND)
        price_tag = "" if hero["price"] <= 0 else " · %d МОНЕТ" % hero["price"]
        cv.create_text(1358, 184, text=rar + price_tag, fill=rcol, font=F_TINY, tags=("dyn",))
        pw = RARITY_POWER.get(hero["rarity"], 1.0)
        cv.create_text(1358, 204, text=("СИЛА: x%.2f (против бота)" % pw) if pw > 1.0 else "СИЛА: x1.00",
                       fill=COL_GEM, font=F_TINY, tags=("dyn",))
        for li, ln2 in enumerate(self._wrap(hero["desc"], 392, 11, cap=4)):
            cv.create_text(1170, 218 + li * 14, text=ln2, anchor="w", fill="#e8c9a0",
                           font=F_TINY, tags=("dyn",))
        cv.create_text(1170, 292, text="СТАТЫ", anchor="w", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
        for j, (skey, sname, scol) in enumerate(STAT_NAMES):
            val = hero["stats"][skey]
            yy = 310 + j * 20
            cv.create_text(1170, yy, text=sname, anchor="w", fill=COL_SAND, font=F_TINY, tags=("dyn",))
            cv.create_rectangle(1250, yy - 5, 1490, yy + 5, fill="#160607", outline="#5a1c10", width=1, tags=("dyn",))
            cv.create_rectangle(1250, yy - 5, 1250 + val * 24, yy + 5, fill=scol, outline="", tags=("dyn",))
            cv.create_text(1510, yy, text=str(val), anchor="w", fill=COL_GOLD, font=F_TINY, tags=("dyn",))
        cv.create_text(1170, 392, text="СПОСОБНОСТИ", anchor="w", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
        y = 412
        for i, ab in enumerate(hero["abilities"]):
            if ab["kind"] == "ult":
                tag, tcol = " · УЛЬТ", COL_RED
            elif ab["kind"] == "supreme_ult":
                tag, tcol = " · ВЫСШ-УЛЬТА (5)", "#ffefd0"
            elif ab["kind"] == "myth_ult":
                tag, tcol = " · МИФ-УЛЬТА (1+4)", "#ff2a8a"
            elif ab["kind"] == "legend_ult":
                tag, tcol = " · ЛЕГ-УЛЬТА (R)", "#ffc400"
            else:
                tag, tcol = "", COL_GOLD
            if y > 596:
                cv.create_text(1170, y, text="См. INFO — остальные способности", anchor="w",
                               fill="#7a4030", font=F_TINY, tags=("dyn",))
                y = 614
                break
            nm = "[%d] %s%s" % (i + 1, ab["name"], tag)
            if len(nm) > 34:
                nm = nm[:33] + "…"
            cv.create_text(1170, y, text=nm, anchor="w",
                           fill=tcol, font=F_SMALL, tags=("dyn",))
            cv.create_text(1566, y, text="%d\u0441" % ab["cd"], anchor="e", fill="#ff5a1a",
                           font=F_SMALL, tags=("dyn",))
            dsc = ab["desc"]
            if ab["kind"] == "myth_ult":
                dsc = "Миф-ульта (1+4 или R): обе способности готовы, полная энергия + шкала УЛЬТЫ, враг ≤25% HP. Добивание."
            elif ab["kind"] == "legend_ult":
                dsc = "Лег-ульта (R): полная энергия + шкала УЛЬТЫ, враг ≤30% HP. Добивание."
            elif ab["kind"] == "supreme_ult":
                dsc = "Высш-ульта (5): полная энергия + шкала УЛЬТЫ, враг ≤35% HP. Экзекуция."
            dl = self._wrap(dsc, 388, 11, cap=3)
            for li, ln2 in enumerate(dl):
                cv.create_text(1176, y + 16 + li * 13, text=ln2, anchor="w", fill=COL_SAND,
                               font=F_TINY, tags=("dyn",))
            y += 17 + len(dl) * 13 + 6
        sps = hero.get("specials", ())
        if sps and y < 560:
            cv.create_text(1170, y + 2, text="СПЕЦПРИЁМЫ", anchor="w",
                           fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
            y += 22
            half = (len(sps) + 1) // 2
            for j, sp in enumerate(sps):
                col_x = 1170 if j < half else 1372
                row_y = y + (j if j < half else j - half) * 20
                cv.create_text(col_x, row_y, text="[%s] %s" % (sp["combo"], sp["name"][:14]), anchor="w",
                               fill="#ffd24a", font=F_SMALL, tags=("dyn",))
                cv.create_text(col_x + 182, row_y, text="%dэ" % sp["cost"], anchor="e",
                               fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
            y += half * 20 + 4
        pros = hero.get("pros", ())
        cons = hero.get("cons", ())
        pc_h = 18 + len(pros) * 16 + 16 + len(cons) * 16
        if pros and cons and y + pc_h < 682:
            if pros:
                cv.create_text(1170, y, text="ПЛЮСЫ", anchor="w", fill="#8aff8a", font=F_TINY, tags=("dyn",))
                for pr in pros:
                    y += 16
                    cv.create_text(1180, y, text="+ " + pr, anchor="w", fill="#8aff8a", font=F_TINY, tags=("dyn",))
            if cons:
                y += 16
                cv.create_text(1170, y, text="МИНУСЫ", anchor="w", fill="#ff5a1a", font=F_TINY, tags=("dyn",))
                for cn in cons:
                    y += 16
                    cv.create_text(1180, y, text="- " + cn, anchor="w", fill="#ff5a1a", font=F_TINY, tags=("dyn",))

        self.draw_artifact_equip(cv, sel)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)
        if select_mode:
            nm = getattr(self, "next_mode", "bot")
            if nm == "survival":
                cv.create_text(W / 2, 830, text="РЕЖИМ: ВЫЖИВАНИЕ", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
            elif isinstance(nm, tuple) and nm[0] == "campaign":
                c = campaign.CAMPAIGNS[nm[1]]
                cv.create_text(W / 2, 830, text="CAMPAIGN: %s · СТУПЕНЬ %d" % (c["name"], nm[2]),
                               fill=c["color"], font=F_SMALL, tags=("dyn",))
            self.ui.button(cv, W / 2 - 150, 848, W / 2 + 150, 890, "В БОЙ!", self.start_fight, font=F_SMALL)

    def _wrap(self, txt, width_px, pt, weight="normal", cap=None):
        key = (width_px, pt, weight)
        cpl = self._wrap_cpl.get(key, 0)
        if cpl < 12:
            try:
                import tkinter.font as tkfont
                fnt = tkfont.Font(family="Courier", size=pt, weight=weight)
                cpl = int(width_px / max(1.0, fnt.measure("ШШ") / 2.0))
            except Exception:
                cpl = 0
            if cpl < 12:
                cpl = max(12, int(width_px / (pt * 0.85)))
            self._wrap_cpl[key] = cpl
        lines = textwrap.wrap(txt, cpl) or [""]
        if cap and len(lines) > cap:
            lines = lines[:cap]
            lines[-1] = lines[-1][:max(1, cpl - 2)].rstrip() + "…"
        return lines

    def equip_of(self, key):
        return self.save["equip"].setdefault(key, [])

    def toggle_art(self, key, aid):
        slots = self.equip_of(key)
        if aid in slots:
            slots.remove(aid)
        elif len(slots) < ART_SLOTS:
            slots.append(aid)
        else:
            self.shop_msg = ("ЗАНЯТО: ВСЕ 3 СЛОТА", time.time() + 2.0)
            return
        self.sfx.play("click")
        self.persist()

    def draw_artifact_equip(self, cv, hero_key):
        slots = self.equip_of(hero_key)
        nat = hero_nature(hero_key)
        ncol = NATURE_COLOR[nat]
        cv.create_text(1170, 690, text="АРТЕФАКТЫ (%d/%d) · ПРИРОДА: %s" % (len(slots), ART_SLOTS,
                       NATURE_LABEL[nat]), anchor="w", fill=ncol, font=F_SMALL, tags=("dyn",))
        for i in range(ART_SLOTS):
            x0 = 1170 + i * 132
            x1 = x0 + 124
            aid = slots[i] if i < len(slots) else None
            art = ART_BY_ID.get(aid) if aid else None
            acol = NATURE_COLOR[art["nature"]] if art else "#3a1410"
            cv.create_rectangle(x0, 704, x1, 740, fill="#160607" if art else "#0e0404",
                                outline=acol, width=2, tags=("dyn",))
            if art:
                draw_art_icon(cv, art, x0 + 4, 708, 28, tags=("dyn",))
                cv.create_text(x0 + 36, 722, text=art["name"][:11], anchor="w", fill=ncol,
                               font=F_TINY, tags=("dyn",))
                self.buttons.append((x0, 704, x1, 740, lambda k=hero_key, a=aid: self.toggle_art(k, a)))
        owned = self.save["arts"]
        if not owned:
            cv.create_text(1170, 762, text="Нет артефактов — крафт в SHOP", anchor="w",
                           fill="#7a4030", font=F_TINY, tags=("dyn",))
            return
        cv.create_text(1170, 756, text="НАДЕТЬ/СНЯТЬ:", anchor="w", fill=COL_ORANGE,
                       font=F_TINY, tags=("dyn",))
        ordered = sorted(owned, key=lambda a: a not in slots)
        per, cols = 12, 3
        pages = max(1, (len(ordered) + per - 1) // per)
        page = max(0, min(self.equip_page, pages - 1))
        self.equip_page = page
        for j, aid in enumerate(ordered[page * per:(page + 1) * per]):
            art = ART_BY_ID.get(aid)
            if art is None:
                continue
            row, col = j // cols, j % cols
            x0 = 1170 + col * 132
            y0 = 776 + row * 20
            on = aid in slots
            match = art["nature"] == nat
            colr = NATURE_COLOR[art["nature"]]
            draw_art_icon(cv, art, x0, y0 - 8, 16, tags=("dyn",))
            cv.create_text(x0 + 20, y0, text=art["name"][:10], anchor="w",
                           fill=colr if on or match else "#8a4a20", font=F_TINY, tags=("dyn",))
            if match:
                cv.create_text(x0 + 118, y0, text="+7%", anchor="e", fill=COL_GEM,
                               font=F_TINY, tags=("dyn",))
            self.buttons.append((x0 - 4, y0 - 9, x0 + 124, y0 + 9,
                                 lambda k=hero_key, a=aid: self.toggle_art(k, a)))
        if pages > 1:
            if page > 0:
                self.ui.button(cv, 1300, 748, 1336, 772, "<",
                               lambda: self._equip_page(-1), font=F_SMALL)
            cv.create_text(1348, 760, text="СТР %d/%d" % (page + 1, pages),
                           anchor="w", fill=COL_SAND, font=F_TINY, tags=("dyn",))
            if page < pages - 1:
                self.ui.button(cv, 1540, 748, 1576, 772, ">",
                               lambda: self._equip_page(1), font=F_SMALL)

    def draw_shop(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="SHOP", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="SHOP", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.coins(cv, W - 360, 50, self.coins)
        self.ui.gems(cv, W - 190, 50, self.gems)
        self.ui.button(cv, W / 2 - 420, 116, W / 2 - 160, 148, "БОЙЦЫ",
                       lambda: self._shop_tab("heroes"), font=F_SMALL)
        self.ui.button(cv, W / 2 - 140, 116, W / 2 + 140, 148, "АРТЕФАКТЫ",
                       lambda: self._shop_tab("arts"), font=F_SMALL)
        self.ui.button(cv, W / 2 + 160, 116, W / 2 + 420, 148, "СУНДУКИ",
                       lambda: self._shop_tab("chests"), font=F_SMALL)
        if self.shop_tab == "heroes":
            cv.create_rectangle(W / 2 - 420, 116, W / 2 - 160, 148, outline=COL_GOLD, width=3, tags=("dyn",))
            self.draw_shop_heroes()
        elif self.shop_tab == "arts":
            cv.create_rectangle(W / 2 - 140, 116, W / 2 + 140, 148, outline=COL_GOLD, width=3, tags=("dyn",))
            self.draw_shop_arts()
        else:
            cv.create_rectangle(W / 2 + 160, 116, W / 2 + 420, 148, outline=COL_GOLD, width=3, tags=("dyn",))
            self.draw_chest_tab()
        if self.shop_msg is not None:
            txt, deadline = self.shop_msg
            if time.time() < deadline:
                cv.create_text(W / 2 + 2, 886, text=txt, font=F_MID, fill="#2a0503", tags=("dyn",))
                cv.create_text(W / 2, 884, text=txt, font=F_MID, fill=COL_GOLD, tags=("dyn",))
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def _shop_tab(self, tab):
        self.shop_tab = tab

    def draw_shop_arts(self):
        cv = self.cv
        frags = self.save["frags"]
        owned = self.save["arts"]
        per, cols = 10, 2
        pages = (len(ARTIFACTS) + per - 1) // per
        page = max(0, min(self.art_page, pages - 1))
        cv.create_text(70, 176, text="ФРАГМЕНТЫ:", anchor="w", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
        fx = 200
        for nat in NATURES:
            n = frags.get(nat, 0)
            col = NATURE_COLOR[nat]
            cv.create_rectangle(fx, 162, fx + 26, 190, fill="#160607", outline=col, width=2, tags=("dyn",))
            cv.create_text(fx + 13, 176, text=str(n), fill=col, font=F_TINY, tags=("dyn",))
            cv.create_text(fx + 32, 176, text=NATURE_LABEL[nat], anchor="w", fill=col,
                           font=F_TINY, tags=("dyn",))
            fx += 118
        bps = self.save.get("bps", {})
        cv.create_rectangle(fx, 162, fx + 26, 190, fill="#160607", outline=COL_GOLD, width=2, tags=("dyn",))
        cv.create_text(fx + 13, 176, text=str(sum(bps.values())), fill=COL_GOLD, font=F_TINY, tags=("dyn",))
        cv.create_text(fx + 32, 176, text=BPS_LABEL, anchor="w", fill=COL_GOLD, font=F_TINY, tags=("dyn",))
        arts_sorted = sorted(ARTIFACTS, key=lambda a: (a["tier"], a["name"]))
        chunk = arts_sorted[page * per:(page + 1) * per]
        for i, art in enumerate(chunk):
            col, row = i % cols, i // cols
            x0 = 60 + col * 750
            y0 = 214 + row * 104
            x1, y1 = x0 + 730, y0 + 94
            have = art["id"] in owned
            ncol = NATURE_COLOR[art["nature"]]
            ok = can_craft(art, frags, self.gems, bps)
            cv.create_rectangle(x0, y0, x1, y1, fill="#1a0908" if have else "#160607",
                                outline=ncol if have else (COL_GOLD if ok else "#3a1410"),
                                width=3 if have else 2, tags=("dyn",))
            draw_art_icon(cv, art, x0 + 10, y0 + 10, 72, tags=("dyn",))
            cv.create_text(x0 + 94, y0 + 20, text=art["name"], anchor="w", fill=ncol,
                           font=F_SMALL, tags=("dyn",))
            cv.create_text(x0 + 380, y0 + 20, text="УР. %d · %s" % (art["tier"], NATURE_LABEL[art["nature"]]),
                           anchor="w", fill=COL_SAND, font=F_TINY, tags=("dyn",))
            buffs = " ".join("%s %s%d%%" % (BUFF_LABEL[k], "" if v >= 0 else "-", round(abs(v) * 100))
                             for k, v in art["buff"].items())
            cv.create_text(x0 + 94, y0 + 44, text=buffs, anchor="w", fill=COL_GOLD, font=F_TINY, tags=("dyn",))
            cv.create_text(x0 + 94, y0 + 66, text=craft_cost_label(art, bps), anchor="w",
                           fill=COL_GEM if ok else "#8a4a20", font=F_TINY, tags=("dyn",))
            cv.create_text(x0 + 94, y0 + 84, text=art["desc"], anchor="w", fill="#7a5040",
                           font=F_TINY, tags=("dyn",))
            if have:
                cv.create_text(x1 - 14, y0 + 30, text="СКРАФЧЕН", anchor="e", fill=COL_GEM,
                               font=F_SMALL, tags=("dyn",))
            else:
                self.ui.button(cv, x1 - 170, y0 + 30, x1 - 14, y0 + 70, "СКРАФТИТЬ" if ok else "МАЛО РЕСУРСОВ",
                               lambda aid=art["id"]: self.craft_art(aid), font=F_TINY)
        cv.create_text(W / 2, 836, text="СТРАНИЦА %d / %d" % (page + 1, pages), fill=COL_SAND,
                       font=F_SMALL, tags=("dyn",))
        if page > 0:
            self.ui.button(cv, W / 2 - 260, 820, W / 2 - 180, 856, "<",
                           lambda: self._art_page(-1), font=F_SMALL)
        if page < pages - 1:
            self.ui.button(cv, W / 2 + 180, 820, W / 2 + 260, 856, ">",
                           lambda: self._art_page(1), font=F_SMALL)
        cv.create_text(W / 2, 886, text="Фрагменты падают в ВЫЖИВАНИИ · природа артефакта = природа бойца: +7% ко всем баффам · на бойца 3 слота",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))

    def _art_page(self, d):
        pages = (len(ARTIFACTS) + 9) // 10
        self.art_page = max(0, min(pages - 1, self.art_page + d))

    def craft_art(self, aid):
        art = ART_BY_ID.get(aid)
        if art is None or aid in self.save["arts"]:
            return
        frags = self.save["frags"]
        bps = self.save.setdefault("bps", {})
        if not can_craft(art, frags, self.gems, bps):
            self.shop_msg = ("НЕ ХВАТАЕТ РЕСУРСОВ", time.time() + 2.0)
            return
        for nat, n in art["cost"].items():
            frags[nat] = frags.get(nat, 0) - n
        if art.get("bps"):
            bps[art["id"]] = bps.get(art["id"], 0) - art["bps"]
        self.gems -= art["gems"]
        self.save["gems"] = self.gems
        self.save["arts"].append(aid)
        self.save["stats"]["crafts"] = self.save["stats"].get("crafts", 0) + 1
        self.sfx.play("craft")
        self.persist()
        self.shop_msg = ("СКРАФЧЕНО: " + art["name"], time.time() + 2.5)

    def draw_shop_heroes(self):
        cv = self.cv
        keys = sorted_keys([k for k, v in HEROES.items()
                            if v["rarity"] in ("common", "uncommon", "epic", "mythic", "legendary", "supreme")])
        per = 24
        pages = (len(keys) + per - 1) // per
        page = max(0, min(self.shop_hero_page, pages - 1))
        self.shop_hero_page = page
        for i, key in enumerate(keys[page * per:(page + 1) * per]):
            col, row = i % 6, i // 6
            x0 = 40 + col * 256
            y0 = 170 + row * 140
            x1, y1 = x0 + 248, y0 + 130
            hero = HEROES[key]
            owned = key in self.owned
            afford = self.coins >= hero["price"]
            rcol = RARITY_COLOR.get(hero["rarity"], "#5a1c10")
            cv.create_rectangle(x0, y0, x1, y1, fill="#1a0908", outline=rcol, width=2, tags=("dyn",))
            draw_hero_icon(cv, key, x0 + 12, y0 + 12, 48)
            cv.create_text(x0 + 70, y0 + 28, text=hero["name"], anchor="w", fill=COL_GOLD,
                           font=F_MID, tags=("dyn",))
            rar = RARITY_LABEL.get(hero["rarity"], hero["rarity"].upper())
            cv.create_text(x0 + 70, y0 + 52, text=rar, anchor="w", fill=rcol, font=F_TINY, tags=("dyn",))
            if owned:
                cv.create_text(x0 + 12, y1 - 18, text="КУПЛЕНО", anchor="w", fill="#8aff8a",
                               font=F_SMALL, tags=("dyn",))
            else:
                price_col = COL_GOLD if afford else "#8a4a20"
                cv.create_text(x0 + 12, y1 - 18, text="%d МОНЕТ — КУПИТЬ" % hero["price"],
                               anchor="w", fill=price_col, font=F_SMALL, tags=("dyn",))
                self.buttons.append((x0, y0, x1, y1, lambda k=key: self.buy_hero(k)))
        cv.create_text(W / 2, 866, text="СТРАНИЦА %d / %d" % (page + 1, pages), fill=COL_SAND,
                       font=F_SMALL, tags=("dyn",))
        if page > 0:
            self.ui.button(cv, W / 2 - 260, 848, W / 2 - 180, 884, "<",
                           lambda: self._shop_hero_page(-1), font=F_SMALL)
        if page < pages - 1:
            self.ui.button(cv, W / 2 + 180, 848, W / 2 + 260, 884, ">",
                           lambda: self._shop_hero_page(1), font=F_SMALL)

    def _hero_page(self, d):
        pages = max(1, (len(HEROES) + 55) // 56)
        self.hero_page = max(0, min(pages - 1, self.hero_page + d))

    def _equip_page(self, d):
        pages = max(1, (len(self.save["arts"]) + 11) // 12)
        self.equip_page = max(0, min(pages - 1, self.equip_page + d))

    def _shop_hero_page(self, d):
        keys = [k for k, v in HEROES.items()
                if v["rarity"] in ("common", "uncommon", "epic", "mythic", "legendary")]
        pages = (len(keys) + 23) // 24
        self.shop_hero_page = max(0, min(pages - 1, self.shop_hero_page + d))

    def draw_chest_tab(self):
        cv = self.cv
        t = time.time()
        bob = math.sin(t * 2) * 6
        cards = (
            ("СОКРОВИЩНИЦА ХАОСА", "#ff2a8a", CHEST_COST, "chaos",
             ("НЕОБЫЧНЫЙ 24% · ЭПИЧЕСКИЙ 16% · ЛЕГЕНДАРНЫЙ 7%",
              "МИФИЧЕСКИЙ 8% · DEVILY 5%",
              "МОНЕТЫ 40% (150-500) · повтор героя: компенсация")),
            ("ЧЕРТОГИ АДА", "#ff5a1a", CHEST_HELL_COST, "hell",
             ("IMPY 9% · DEMONDY 6% · SATANY 3% — только здесь",
              "Любой герой: НЕОБЫЧНЫЙ/ЭПИЧЕСКИЙ 10% · ОБЫЧНЫЙ 6%",
              "ЛЕГЕНДАРНЫЙ 6% · МИФИЧЕСКИЙ 6%",
              "МОНЕТЫ 36% (400-900) · САМОЦВЕТЫ 8% (15-40)")),
        )
        for i, (title, colr, price, kind, odds) in enumerate(cards):
            x0 = 40 + i * 780
            x1 = x0 + 760
            cx = (x0 + x1) / 2
            cv.create_rectangle(x0, 170, x1, 800, fill="#1a0908", outline=colr, width=3, tags=("dyn",))
            cv.create_text(cx + 2, 214, text=title, font=F_BIG, fill="#2a0503", tags=("dyn",))
            cv.create_text(cx, 212, text=title, font=F_BIG, fill=colr, tags=("dyn",))
            glow_r = 120 + math.sin(t * 3 + i * 1.7) * 8
            cv.create_oval(cx - glow_r, 420 + bob - glow_r, cx + glow_r, 420 + bob + glow_r,
                           outline=colr, stipple="gray25", tags=("dyn",))
            cv.create_rectangle(cx - 100, 350 + bob, cx + 100, 385 + bob, fill="#7a2210",
                                outline="#2a0503", width=2, tags=("dyn",))
            cv.create_rectangle(cx - 92, 385 + bob, cx + 92, 480 + bob, fill="#5a1c10",
                                outline="#2a0503", width=2, tags=("dyn",))
            lock_col = COL_GOLD if kind == "chaos" else "#ff2a1a"
            cv.create_rectangle(cx - 14, 385 + bob, cx + 14, 420 + bob, fill=lock_col,
                                outline="#a1700a", width=2, tags=("dyn",))
            cv.create_text(cx, 530, text="ЦЕНА: %d САМОЦВЕТОВ" % price,
                           fill=COL_GEM, font=F_MID, tags=("dyn",))
            for j, ln in enumerate(odds):
                cv.create_text(cx, 566 + j * 20, text=ln, fill=COL_SAND, font=F_TINY, tags=("dyn",))
            self.ui.button(cv, cx - 140, 668, cx + 140, 714, "ОТКРЫТЬ СГНДУК",
                           lambda k=kind: self.buy_chest(k), font=F_SMALL)
        cv.create_text(W / 2, 846, text="На монеты самый высокий шанс в обоих сундуках · в ЧЕРТОГАХ АДА шансы на редких героев выше",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))

    def draw_chest_open(self):
        cv = self.cv
        cx = W // 2
        if self.chest_reward is None:
            self.collect_chest()
            return
        t = self.chest_t or 0.0
        if t < 0.8:
            jx = int(math.sin(t * 60) * 6)
            jy = int(math.cos(t * 47) * 4)
            cv.create_rectangle(cx - 120 + jx, 400 + jy, cx + 120 + jx, 440 + jy, fill="#7a2210",
                                outline="#2a0503", width=2, tags=("dyn",))
            cv.create_rectangle(cx - 110 + jx, 440 + jy, cx + 110 + jx, 560 + jy, fill="#5a1c10",
                                outline="#2a0503", width=2, tags=("dyn",))
            cv.create_rectangle(cx - 16 + jx, 440 + jy, cx + 16 + jx, 480 + jy, fill=COL_GOLD,
                                outline="#a1700a", width=2, tags=("dyn",))
            cv.create_text(cx, 300, text="...", font=F_HUGE, fill=COL_GOLD, tags=("dyn",))
        elif t < 1.6:
            p = (t - 0.8) / 0.8
            r = 60 + 340 * p
            cv.create_oval(cx - r, 480 - r, cx + r, 480 + r, outline=COL_GOLD if int(p * 4) % 2 else "#ff2a8a",
                           width=4, tags=("dyn",))
            cv.create_text(cx, 300, text="!!", font=F_HUGE, fill="#ff2a8a", tags=("dyn",))
            self.parts.draw(cv)
        else:
            rw = self.chest_reward
            card_col = COL_GOLD
            if rw[0] in ("hero", "dupe"):
                card_col = RARITY_COLOR.get(HEROES[rw[1]]["rarity"], COL_GOLD)
            cv.create_rectangle(cx - 200, 250, cx + 200, 640, fill="#1a0908",
                                outline=card_col, width=4, tags=("dyn",))
            if rw[0] == "coins":
                cv.create_text(cx, 300, text="+%d МОНЕТ" % rw[1], font=F_BIG, fill=COL_GOLD, tags=("dyn",))
                cv.create_oval(cx - 48, 372, cx + 48, 468, fill=COL_GOLD, outline="#a1700a",
                               width=3, tags=("dyn",))
            elif rw[0] == "gems":
                cv.create_text(cx, 300, text="+%d САМОЦВЕТОВ" % rw[1], font=F_BIG, fill=COL_GEM, tags=("dyn",))
                cv.create_oval(cx - 48, 372, cx + 48, 468, fill=COL_GEM, outline="#0a4a3a",
                               width=3, tags=("dyn",))
                cv.create_text(cx, 560, text=self.chest_title(), font=F_TINY, fill=COL_SAND, tags=("dyn",))
            else:
                key = rw[1]
                hero = HEROES[key]
                rar = RARITY_LABEL.get(hero["rarity"], hero["rarity"].upper())
                cv.create_text(cx, 300, text=("ПОВТОР: %s" if rw[0] == "dupe" else "%s") % hero["name"],
                               font=F_BIG, fill=COL_GOLD, tags=("dyn",))
                draw_hero_icon(cv, key, cx - 48, 420, 96)
                cv.create_text(cx, 560, text=rar, font=F_MID,
                               fill=RARITY_COLOR.get(hero["rarity"], COL_SAND), tags=("dyn",))
                if rw[0] == "dupe":
                    cv.create_text(cx, 590, text="Компенсация +%d МОНЕТ +10 САМ." % rw[2],
                                   font=F_SMALL, fill=COL_GEM, tags=("dyn",))
                else:
                    cv.create_text(cx, 590, text="НОВЫЙ БОЕЦ!", font=F_SMALL, fill=COL_GEM, tags=("dyn",))
            self.parts.draw(cv)
            self.ui.button(cv, cx - 120, 680, cx + 120, 730, "ЗАБРАТЬ", self.collect_chest, font=F_SMALL)

    def draw(self):
        cv = self.cv
        cv.delete("dyn")
        self.buttons = []
        self.embers.draw(cv)
        st = self.state
        if st == "menu":
            self.draw_menu()
        elif st == "heroes":
            self.draw_heroes(False)
        elif st == "select":
            self.draw_heroes(True)
        elif st == "mode":
            self.draw_mode()
        elif st == "shop":
            self.draw_shop()
        elif st == "info":
            self.draw_info()
        elif st == "campaigns":
            self.draw_campaigns()
        elif st == "camp_stages":
            self.draw_camp_stages()
        elif st == "achievements":
            self.draw_achievements()
        elif st == "chest_open":
            self.draw_chest_open()
        elif st == "settings":
            self.draw_settings()
        elif st == "net_scan":
            self.draw_net_scan()
        elif st == "net_select":
            self.draw_net_select()
        elif st == "fight":
            if self.arena is not None:
                self.arena.draw(cv, self.coins + (self.arena.run_reward if self.arena.survival else 0))
                draw_traps(cv, self.arena.time, self.arena.map)
                draw_ambient(cv, time.time(), self.arena.map)
                draw_torches(cv, time.time(), self.arena.map)
                if self.arena.phase == "end":
                    if self.arena.net and self.arena.mirror:
                        self.ui.button(cv, W / 2 - 120, 610, W / 2 + 120, 670, "В МЕНЮ", self.net_back, font=F_SMALL)
                    elif self.arena.net:
                        self.ui.button(cv, W / 2 - 280, 610, W / 2 - 40, 670, "РЕВАНШ", self.net_start, font=F_SMALL)
                        self.ui.button(cv, W / 2 + 40, 610, W / 2 + 280, 670, "В МЕНЮ", self.net_back, font=F_SMALL)
                    else:
                        nxt = self.camp_next()
                        if nxt is not None:
                            self.ui.button(cv, W / 2 - 120, 560, W / 2 + 120, 600, "СЛЕДУЮЩИЙ УРОВЕНЬ",
                                           lambda: self.goto_select(nxt), font=F_SMALL)
                        self.ui.button(cv, W / 2 - 280, 610, W / 2 - 40, 670, "РЕВАНШ", self.start_fight, font=F_SMALL)
                        self.ui.button(cv, W / 2 + 40, 610, W / 2 + 280, 670, "В МЕНЮ", self.goto_menu, font=F_SMALL)
        self.draw_toasts(cv)
        self._apply_vs(cv)


def clamp01(v):
    return max(0.0, min(1.0, v))
