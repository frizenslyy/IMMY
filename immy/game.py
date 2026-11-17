"""IMMY — главный класс игры: окна, ввод, магазин, сундуки, INFO, кампании, достижения."""

import math
import random
import time
import tkinter as tk

from . import achievements, campaign, netplay
from .arena import Arena
from .background import (MAPS, draw_ambient, draw_fight_bg, draw_hero_icon,
                         draw_menu_bg, draw_screen_bg, draw_torches)
from .config import (CHEST_COST, COL_BLOOD, COL_GEM, COL_GOLD, COL_ORANGE,
                     COL_RED, COL_SAND, FATALITY_BONUS, FATALITY_GEMS,
                     FATALITY_KEYS, FINISHER_BONUS, F_BIG, F_HUGE, F_MID,
                     F_SMALL, F_SQUARE, F_TINY, FPS, GROUND_Y, H,
                     NET_SNAP_HZ, RARITY_POWER, TICK_MS, TITLE, W, exp_to_next)
from .fighter import Fighter
from .heroes import HEROES, RARITY_COLOR, RARITY_LABEL, STAT_NAMES
from .particles import Embers, Particles
from .save import load_save, save_save
from .sound import Music
from .ui import Ui

CYR_CHAR = {"ц": "w", "ф": "a", "ы": "s", "в": "d", "а": "f", "у": "e"}
CYR_NAME = {"tse": "w", "ef": "a", "yeru": "s", "ve": "d", "a": "f", "u": "e"}
VK_MAP = {87: "w", 65: "a", 83: "s", 68: "d", 70: "f", 69: "e", 82: "r"}
ARROWS = {"left": "a", "right": "d", "up": "w", "down": "s"}

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
    ("CAMPAIGN: 13 кампаний — награды: герои, монеты, самоцветы", COL_GOLD),
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
    ("МУЧЕНИК: 3 раунда против врага x6 HP и x4 урона — нанесите максимум урона", COL_RED),
    ("МУЧЕНИК: победа (2 раунда) = 100 самоцветов · поражение = монеты за урон", COL_GEM),
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
        self.title(TITLE)
        self.geometry("%dx%d" % (W, H))
        self.resizable(False, False)
        self.cv = tk.Canvas(self, width=W, height=H, bg="#120406", highlightthickness=0)
        self.cv.pack()
        try:
            self.update_idletasks()
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            if sw and sh:
                self.geometry("+%d+%d" % (max(0, (sw - W) // 2), max(0, (sh - H) // 2)))
        except Exception:
            pass
        self.save = load_save()
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
        self.music = Music()
        self.shop_msg = None
        self.shop_tab = "heroes"
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
        else:
            draw_screen_bg(self.cv)
        if s == "fight":
            self.music.play("battle")
        else:
            self.music.play("menu")
        if s in ("heroes", "select"):
            self.preview = Fighter(self.hero_sel, W / 2, 1, scale=2.4)
            self.preview.y = GROUND_Y - 19
        else:
            self.preview = None

    def persist(self):
        self.save["coins"] = self.coins
        self.save["gems"] = self.gems
        self.save["bot_level"] = self.bot_level
        self.save["owned"] = self.owned
        self.save["exp"] = self.exp
        self.save["plvl"] = self.plvl
        self.save["stats"]["plvl"] = self.plvl
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
        return [k for k, v in HEROES.items() if v["rarity"] == rarity]

    def roll_chest(self):
        r = random.random()
        if r < 0.05:
            return ("hero", "DEVILY")
        if r < 0.13:
            return ("hero", random.choice(self.chest_keys("mythic")))
        if r < 0.20:
            return ("hero", random.choice(self.chest_keys("legendary")))
        if r < 0.36:
            return ("hero", random.choice(self.chest_keys("epic")))
        if r < 0.60:
            return ("hero", random.choice(self.chest_keys("uncommon")))
        return ("coins", random.randint(150, 500))

    def buy_chest(self):
        if self.gems < CHEST_COST:
            self.shop_msg = ("НЕ ХВАТАЕТ САМОЦВЕТОВ (%d/%d)" % (self.gems, CHEST_COST),
                             time.time() + 2.5)
            return
        self.gems -= CHEST_COST
        self.save["gems"] = self.gems
        self.save["stats"]["chests"] = self.save["stats"].get("chests", 0) + 1
        kind, val = self.roll_chest()
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

    def collect_chest(self):
        self.chest_t = None
        self.chest_reward = None
        self.set_state("shop")

    def start_fight(self):
        nm = getattr(self, "next_mode", "bot")
        self.camp_ctx = None
        if nm == "survival":
            self.arena = Arena(self.hero_sel, "DEADY", 1, False, map=random.choice(MAPS), survival=True)
        elif nm == "martyr":
            bot_key = random.choice([k for k in HEROES if k != self.hero_sel])
            self.arena = Arena(self.hero_sel, bot_key, self.bot_level, False,
                               map=random.choice(MAPS), martyr=True)
        elif isinstance(nm, tuple) and nm[0] == "campaign":
            _, idx, stage = nm
            level = campaign.stage_level(idx, stage)
            boss = campaign.is_final(idx, stage)
            bot_key = random.choice([k for k in HEROES if k != self.hero_sel])
            self.arena = Arena(self.hero_sel, bot_key, level, boss, map=random.choice(MAPS))
            self.camp_ctx = (idx, stage)
        else:
            level = self.bot_level
            boss = level % 10 == 0
            bot_key = random.choice([k for k in HEROES if k != self.hero_sel])
            self.arena = Arena(self.hero_sel, bot_key, level, boss, map=random.choice(MAPS))
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

    def on_motion(self, e):
        self.mouse = (e.x, e.y)

    def on_click(self, e):
        if self.state == "fight":
            if self.arena is None:
                return
            if self.arena.phase == "end":
                for x0, y0, x1, y1, action in self.buttons:
                    if x0 <= e.x <= x1 and y0 <= e.y <= y1:
                        action()
                        return
            elif self.arena.phase == "fatality":
                self.events.add("attack")
            elif self.arena.phase == "fight":
                self.events.add("attack")
            return
        for x0, y0, x1, y1, action in self.buttons:
            if x0 <= e.x <= x1 and y0 <= e.y <= y1:
                action()
                return

    def build_input(self):
        inp = {"move": 0, "jump": "jump" in self.events, "crouch": "s" in self.keys,
               "attack": "attack" in self.events, "cast": None, "parry": "parry" in self.events,
               "special": None, "strike": None, "myth": False, "rult": "r" in self.events}
        if "a" in self.keys:
            inp["move"] -= 1
        if "d" in self.keys:
            inp["move"] += 1
        digits = sorted(e for e in self.events if e in ("1", "2", "3", "4"))
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
        self.loop_body(dt)
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
        elif a.martyr:
            exp_gain = 70 if a.win else max(10, int(a.dmg_dealt // 15))
            if a.win:
                st["martyr_wins"] = st.get("martyr_wins", 0) + 1
                self.earn_gems(a.martyr_gems)
                a.reward = 0
            st["max_damage"] = max(st.get("max_damage", 0), int(a.dmg_dealt))
        elif a.win:
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
        if a.win and not a.survival:
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
                elif r["type"] == "gems":
                    gm = campaign.first_clear_gems(stage)
                    self.earn_gems(gm)
                    self.toasts.append(("НАГРАДА: +%d САМОЦВЕТОВ" % gm, "", time.time() + 5.0))
                bonus = campaign.first_clear_coins(stage)
                self.earn(bonus)
                a.reward += bonus
                st["camp_stages"] += 1
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
                    "legend_ults"):
            st[key] = st.get(key, 0) + a.stats.get(key, 0)

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
        self.ui.button(cv, cx - 160, 554, cx + 160, 604, "ONLINE", self.goto_online, font=F_MID)
        self.ui.button(cv, cx - 160, 608, cx + 160, 658, "FRIEND", self.goto_net, font=F_MID)
        self.ui.button(cv, cx - 160, 662, cx + 160, 712, "CAMPAIGN", self.goto_campaigns, font=F_MID)
        self.ui.button(cv, cx - 160, 716, cx + 160, 766, "SHOP", self.goto_shop, font=F_MID)
        self.ui.button(cv, cx - 160, 770, cx + 160, 820, "INFO", self.goto_info, font=F_SMALL)
        self.ui.button(cv, cx - 160, 824, cx + 160, 874, "AWARDS", self.goto_achievements, font=F_SMALL)
        self.ui.coins(cv, 30, H - 40, self.coins)
        self.ui.gems(cv, 240, H - 40, self.gems)
        self.draw_level_bar(cv, 30, 24)
        cv.create_text(W - 30, H - 40, text="БОТ: УР. %d" % self.bot_level, anchor="e",
                       fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        cv.create_text(W / 2, H - 14, text="ЛКМ — атака · WASD — движение · E — пинок · S+ЛКМ — апперкот · F — парирование · 1-4 — способности · 1+4 — миф-ульта · A+S/W+S — спецприёмы",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))

    def draw_mode(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 153, text="ВЫБОР РЕЖИМА", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 150, text="ВЫБОР РЕЖИМА", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.button(cv, W / 2 - 160, 240, W / 2 + 160, 330, "VS БОТ", self.goto_select, font=F_SQUARE)
        self.ui.button(cv, W / 2 - 160, 344, W / 2 + 160, 424, "ВЫЖИВАНИЕ",
                       lambda: self.goto_select("survival"), font=F_MID)
        self.ui.button(cv, W / 2 - 160, 438, W / 2 + 160, 518, "CAMPAIGN",
                       self.goto_campaigns, font=F_MID)
        self.ui.button(cv, W / 2 - 160, 532, W / 2 + 160, 612, "МУЧЕНИК",
                       lambda: self.goto_select("martyr"), font=F_MID)
        cv.create_text(W / 2, 640, text="БОТ: УРОВЕНЬ %d" % self.bot_level, fill=COL_ORANGE,
                       font=F_MID, tags=("dyn",))
        if self.bot_level % 10 == 0:
            cv.create_text(W / 2, 668, text="!! ВНИМАНИЕ: ЭТО БОСС !!", fill=COL_RED, font=F_MID, tags=("dyn",))
        cv.create_text(W / 2, 694, text="ВЫЖИВАНИЕ: волны врагов · каждая 5-я — мини-босс · МУЧЕНИК: 3 раунда против гиганта",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))
        cv.create_text(W / 2, 716, text="МУЧЕНИК: победа = 100 самоцветов · поражение = монеты за нанесённый урон",
                       fill=COL_GEM, font=F_TINY, tags=("dyn",))
        self.ui.coins(cv, W / 2 - 90, 740, self.coins)
        self.ui.gems(cv, W / 2 + 60, 740, self.gems)
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
        keys = list(HEROES)
        cv.create_rectangle(24, 100, 560, 860, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(292, 122, text="ВСЕ БОЙЦЫ · БАЛАНС", fill=COL_ORANGE, font=F_MID, tags=("dyn"))
        for i, key in enumerate(keys):
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
        cv.create_text(1308, 216, text=hero["desc"], fill="#e8c9a0", font=F_TINY, width=480, tags=("dyn"))
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
            y += 44
        sps = hero.get("specials", ())
        if sps:
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
        for i, c in enumerate(campaign.CAMPAIGNS):
            col, row = i % 3, i // 3
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
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

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
        keys = [k for k in HEROES if k in self.owned] if select_mode else list(HEROES)
        if sel not in keys and keys:
            sel = keys[0]
            self.hero_sel = sel
            self.preview = Fighter(sel, W / 2, 1, scale=2.4)
            self.preview.y = GROUND_Y - 19
        cv.create_rectangle(24, 100, 460, 860, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(242, 122, text="БОЙЦЫ", fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        for i, key in enumerate(keys):
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
        cv.create_text(1358, 232, text=hero["desc"], fill="#e8c9a0", font=F_TINY, width=400, tags=("dyn"))
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
        step = 46 if len(hero["abilities"]) > 3 else 58
        for i, ab in enumerate(hero["abilities"]):
            if ab["kind"] == "ult":
                tag, tcol = " · УЛЬТ", COL_RED
            elif ab["kind"] == "myth_ult":
                tag, tcol = " · МИФ-УЛЬТА (1+4)", "#ff2a8a"
            else:
                tag, tcol = "", COL_GOLD
            cv.create_text(1170, y, text="[%d] %s%s" % (i + 1, ab["name"], tag), anchor="w",
                           fill=tcol, font=F_SMALL, tags=("dyn",))
            cv.create_text(1560, y, text="%dс" % ab["cd"], anchor="e", fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
            cv.create_text(1176, y + 15, text=ab["desc"], anchor="w", fill=COL_SAND, font=F_TINY,
                           width=374, tags=("dyn",))
            y += step
        sps = hero.get("specials", ())
        if sps:
            cv.create_text(1170, y + 2, text="СПЕЦПРИЁМЫ", anchor="w",
                           fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
            cv.create_text(1560, y + 2, text="энергия · кд",
                           anchor="e", fill="#8a4a20", font=F_TINY, tags=("dyn",))
            for sp in sps:
                y += 20
                cv.create_text(1170, y, text="[%s] %s" % (sp["combo"], sp["name"]), anchor="w",
                               fill="#ffd24a", font=F_SMALL, tags=("dyn",))
                cv.create_text(1560, y, text="%d · %dс" % (sp["cost"], sp.get("cd", 8)), anchor="e",
                               fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
        pros = hero.get("pros", ())
        cons = hero.get("cons", ())
        if pros or cons:
            y += 22
            if pros:
                cv.create_text(1170, y, text="ПЛЮСЫ", anchor="w", fill="#8aff8a", font=F_TINY, tags=("dyn",))
                for p in pros:
                    y += 18
                    cv.create_text(1180, y, text="+ " + p, anchor="w", fill="#8aff8a", font=F_TINY, tags=("dyn",))
            if cons:
                y += 18
                cv.create_text(1170, y, text="МИНУСЫ", anchor="w", fill="#ff5a1a", font=F_TINY, tags=("dyn",))
                for c in cons:
                    y += 18
                    cv.create_text(1180, y, text="- " + c, anchor="w", fill="#ff5a1a", font=F_TINY, tags=("dyn",))

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

    def draw_shop(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="SHOP", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="SHOP", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.coins(cv, W - 360, 50, self.coins)
        self.ui.gems(cv, W - 190, 50, self.gems)
        self.ui.button(cv, W / 2 - 280, 116, W / 2 - 20, 148, "БОЙЦЫ",
                       lambda: self._shop_tab("heroes"), font=F_SMALL)
        self.ui.button(cv, W / 2 + 20, 116, W / 2 + 280, 148, "СУНДУКИ",
                       lambda: self._shop_tab("chests"), font=F_SMALL)
        if self.shop_tab == "heroes":
            cv.create_rectangle(W / 2 - 280, 116, W / 2 - 20, 148, outline=COL_GOLD, width=3, tags=("dyn",))
            self.draw_shop_heroes()
        else:
            cv.create_rectangle(W / 2 + 20, 116, W / 2 + 280, 148, outline=COL_GOLD, width=3, tags=("dyn",))
            self.draw_chest_tab()
        if self.shop_msg is not None:
            txt, deadline = self.shop_msg
            if time.time() < deadline:
                cv.create_text(W / 2 + 2, 886, text=txt, font=F_MID, fill="#2a0503", tags=("dyn",))
                cv.create_text(W / 2, 884, text=txt, font=F_MID, fill=COL_GOLD, tags=("dyn",))
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def _shop_tab(self, tab):
        self.shop_tab = tab

    def draw_shop_heroes(self):
        cv = self.cv
        keys = [k for k, v in HEROES.items() if v["rarity"] in ("common", "uncommon", "epic", "mythic")]
        for i, key in enumerate(keys):
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

    def draw_chest_tab(self):
        cv = self.cv
        cx = W // 2
        t = time.time()
        bob = math.sin(t * 2) * 6
        cv.create_rectangle(cx - 340, 190, cx + 340, 800, fill="#1a0908",
                            outline="#ff2a8a", width=3, tags=("dyn",))
        cv.create_text(cx + 2, 234, text="СОКРОВИЩНИЦА ХАОСА", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(cx, 232, text="СОКРОВИЩНИЦА ХАОСА", font=F_BIG, fill="#ff2a8a", tags=("dyn",))
        glow_r = 150 + math.sin(t * 3) * 10
        cv.create_oval(cx - glow_r, 480 + bob - glow_r, cx + glow_r, 480 + bob + glow_r,
                       outline="#ff2a8a", stipple="gray25", tags=("dyn",))
        cv.create_rectangle(cx - 120, 400 + bob, cx + 120, 440 + bob, fill="#7a2210",
                            outline="#2a0503", width=2, tags=("dyn",))
        cv.create_rectangle(cx - 110, 440 + bob, cx + 110, 560 + bob, fill="#5a1c10",
                            outline="#2a0503", width=2, tags=("dyn",))
        cv.create_rectangle(cx - 16, 440 + bob, cx + 16, 480 + bob, fill=COL_GOLD,
                            outline="#a1700a", width=2, tags=("dyn",))
        cv.create_text(cx, 620, text="ЦЕНА: %d САМОЦВЕТОВ" % CHEST_COST, fill=COL_GEM,
                       font=F_MID, tags=("dyn",))
        cv.create_text(cx, 650, text="НЕОБЫЧНЫЙ 24% · ЭПИЧЕСКИЙ 16% · ЛЕГЕНДАРНЫЙ 7%", fill=COL_SAND,
                       font=F_TINY, tags=("dyn",))
        cv.create_text(cx, 672, text="МИФИЧЕСКИЙ 8% · DEVILY 5%", fill=COL_SAND,
                       font=F_TINY, tags=("dyn",))
        cv.create_text(cx, 694, text="МОНЕТЫ 40% (150-500) · повтор героя: компенсация", fill=COL_SAND,
                       font=F_TINY, tags=("dyn",))
        self.ui.button(cv, cx - 140, 720, cx + 140, 770, "ОТКРЫТЬ СУНДУК", self.buy_chest, font=F_SMALL)

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
                cv.create_text(cx, 560, text="СОКРОВИЩНИЦА ХАОСА", font=F_TINY, fill=COL_SAND, tags=("dyn",))
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
        elif st == "net_scan":
            self.draw_net_scan()
        elif st == "net_select":
            self.draw_net_select()
        elif st == "fight":
            if self.arena is not None:
                self.arena.draw(cv, self.coins + (self.arena.run_reward if self.arena.survival else 0))
                draw_ambient(cv, time.time(), self.arena.map)
                draw_torches(cv, time.time(), self.arena.map)
                if self.arena.phase == "end":
                    if self.arena.net and self.arena.mirror:
                        self.ui.button(cv, W / 2 - 120, 610, W / 2 + 120, 670, "В МЕНЮ", self.net_back, font=F_SMALL)
                    elif self.arena.net:
                        self.ui.button(cv, W / 2 - 280, 610, W / 2 - 40, 670, "РЕВАНШ", self.net_start, font=F_SMALL)
                        self.ui.button(cv, W / 2 + 40, 610, W / 2 + 280, 670, "В МЕНЮ", self.net_back, font=F_SMALL)
                    else:
                        self.ui.button(cv, W / 2 - 280, 610, W / 2 - 40, 670, "РЕВАНШ", self.start_fight, font=F_SMALL)
                        self.ui.button(cv, W / 2 + 40, 610, W / 2 + 280, 670, "В МЕНЮ", self.goto_menu, font=F_SMALL)
        self.draw_toasts(cv)


def clamp01(v):
    return max(0.0, min(1.0, v))
