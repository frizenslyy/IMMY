"""IMMY — главный класс игры: окна, ввод, магазин, кампании, достижения, музыка."""

import random
import time
import tkinter as tk

from . import achievements, campaign
from .arena import Arena
from .background import (MAPS, draw_ambient, draw_fight_bg, draw_hero_icon,
                         draw_menu_bg, draw_screen_bg, draw_torches)
from .config import (COL_GOLD, COL_ORANGE, COL_RED, COL_SAND, exp_to_next, F_BIG,
                     F_MID, F_SMALL, F_SQUARE, F_TINY, H, TICK_MS, TITLE, W)
from .fighter import Fighter
from .heroes import HEROES, RARITY_COLOR, RARITY_LABEL, STAT_NAMES
from .particles import Embers, Particles
from .save import load_save, save_save
from .sound import Music
from .ui import Ui

CYR_CHAR = {"ц": "w", "ф": "a", "ы": "s", "в": "d", "а": "f"}
CYR_NAME = {"tse": "w", "ef": "a", "yeru": "s", "ve": "d", "a": "f"}
VK_MAP = {87: "w", 65: "a", 83: "s", 68: "d", 70: "f"}
ARROWS = {"left": "a", "right": "d", "up": "w", "down": "s"}


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
        self.save = load_save()
        self.coins = self.save["coins"]
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
        self.toasts = []
        self.camp_idx = 0
        self.camp_ctx = None
        self.ach_page = 0
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
            self.preview = Fighter(self.hero_sel, 640, 1, scale=2.4)
            self.preview.y = 596
        else:
            self.preview = None

    def persist(self):
        self.save["coins"] = self.coins
        self.save["bot_level"] = self.bot_level
        self.save["owned"] = self.owned
        self.save["exp"] = self.exp
        self.save["plvl"] = self.plvl
        self.save["stats"]["plvl"] = self.plvl
        granted = achievements.check(self.save)
        for a in granted:
            self.toasts.append(("ДОСТИЖИЕ: " + a["name"], a["reward"], time.time() + 4.0))
        self.coins = self.save["coins"]
        save_save(self.save)

    def earn(self, n):
        self.coins += n
        self.save["stats"]["coins_earned"] = self.save["stats"].get("coins_earned", 0) + n

    def add_exp(self, amount):
        if amount <= 0:
            return
        self.exp += amount
        while self.exp >= exp_to_next(self.plvl):
            self.exp -= exp_to_next(self.plvl)
            self.plvl += 1
            self.toasts.append(("УРОВЕНЬ %d!" % self.plvl, 0, time.time() + 4.0))

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
        self.set_state("shop")

    def goto_campaigns(self):
        self.set_state("campaigns")

    def open_camp(self, idx):
        self.camp_idx = idx
        self.set_state("camp_stages")

    def goto_achievements(self):
        self.ach_page = 0
        self.set_state("achievements")

    def pick_hero(self, key):
        self.hero_sel = key
        if self.state in ("heroes", "select"):
            self.preview = Fighter(key, 640, 1, scale=2.4)
            self.preview.y = 596

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

    def start_fight(self):
        nm = getattr(self, "next_mode", "bot")
        self.camp_ctx = None
        if nm == "survival":
            self.arena = Arena(self.hero_sel, "DEADY", 1, False, map=random.choice(MAPS), survival=True)
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
            if self.state != "menu":
                self.set_state("menu")
            return
        if k == "m" and k not in self.keys:
            self.music.toggle()
        if self.state == "fight":
            if k == "w":
                self.events.add("jump")
            elif k == "f":
                self.events.add("parry")
            elif k in ("1", "2", "3", "4"):
                self.events.add(k)
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
               "special": None}
        if "a" in self.keys:
            inp["move"] -= 1
        if "d" in self.keys:
            inp["move"] += 1
        for e in self.events:
            if e in ("1", "2", "3", "4"):
                inp["cast"] = int(e) - 1
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
        if self.state in ("heroes", "select") and self.preview is not None:
            self.preview.anim_t += dt
            if random.random() < dt * 4:
                hero = HEROES[self.hero_sel]
                self.parts.items.append({"x": 640 + random.uniform(-50, 50), "y": 596 - random.uniform(20, 170),
                                         "vx": random.uniform(-20, 20), "vy": random.uniform(-70, -25),
                                         "t": 0.6, "life": 0.6, "color": hero["glow"], "r": 2.5, "g": -40})
            self.parts.update(dt)
        if self.state == "fight" and self.arena is not None:
            inp = self.build_input()
            self.arena.update(dt, inp)
            if self.arena.phase == "end" and not self.arena.rewarded:
                self.finish_fight()
        self.draw()

    def finish_fight(self):
        a = self.arena
        a.rewarded = True
        st = self.save["stats"]
        exp_gain = 0
        if a.survival:
            waves = max(0, a.wave - 1)
            exp_gain = 10 * waves + max(0, waves - 3) * 5
            st["waves"] += waves
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
                a.finish_bonus = 25 * a.quality_finish
                a.reward += a.finish_bonus
                exp_gain += 25 * a.quality_finish
        a.exp_gain = exp_gain
        st["specials"] += a.stats["specials"]
        st["ults"] += a.stats["ults"]
        st["parries"] += a.stats["parries"]
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
                self.earn(campaign.first_clear_reward(stage))
                a.reward += campaign.first_clear_reward(stage)
                st["camp_stages"] += 1
                exp_gain += 50 + 6 * stage
                if campaign.is_final(idx, stage) and not rec["done"]:
                    rec["done"] = True
                    hero = campaign.CAMPAIGNS[idx]["hero"]
                    if hero not in self.owned:
                        self.owned.append(hero)
                    self.toasts.append(("ЭКСКЛЮЗИВ: %s!" % hero, 0, time.time() + 5.0))
            else:
                bonus = campaign.replay_reward(stage)
                self.earn(bonus)
                a.reward += bonus
            exp_gain += 50 + 6 * stage
        st["camps"] = sum(1 for ci in range(len(campaign.CAMPAIGNS))
                          if campaign.camp_done(self.save, ci))
        self.add_exp(exp_gain)
        self.persist()

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
            txt = name + ("  +%d МОНЕТ" % reward if reward else "")
            cv.create_text(W / 2 + 2, y + 2, text=txt, font=F_SMALL, fill="#2a0503", tags=("dyn",))
            cv.create_text(W / 2, y, text=txt, font=F_SMALL, fill=COL_GOLD, tags=("dyn",))

    def draw_menu(self):
        cv = self.cv
        cx = W // 2
        self.ui.button(cv, cx - 100, 260, cx + 100, 440, "PLAY", self.goto_mode, font=F_SQUARE)
        self.ui.button(cv, cx - 160, 470, cx + 160, 526, "HEROES", self.goto_heroes, font=F_MID)
        self.ui.button(cv, cx - 160, 536, cx + 160, 592, "КАМПАНИИ", self.goto_campaigns, font=F_MID)
        self.ui.button(cv, cx - 160, 602, cx + 160, 658, "SHOP", self.goto_shop, font=F_MID)
        self.ui.button(cv, cx - 160, 668, cx + 160, 706, "НАГРАДЫ", self.goto_achievements, font=F_SMALL)
        self.ui.coins(cv, 30, H - 40, self.coins)
        self.draw_level_bar(cv, 30, 24)
        cv.create_text(W - 30, H - 40, text="БОТ: УР. %d" % self.bot_level, anchor="e",
                       fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        cv.create_text(W / 2, H - 14, text="ЛКМ — атака · WASD — движение · F — парирование · 1/2/3/4 — способности · A+S/W+S — спецприёмы",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))

    def draw_mode(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 133, text="ВЫБОР РЕЖИМА", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 130, text="ВЫБОР РЕЖИМА", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.button(cv, W / 2 - 160, 200, W / 2 + 160, 300, "VS БОТ", self.goto_select, font=F_SQUARE)
        self.ui.button(cv, W / 2 - 160, 320, W / 2 + 160, 400, "ВЫЖИВАНИЕ",
                       lambda: self.goto_select("survival"), font=F_MID)
        self.ui.button(cv, W / 2 - 160, 420, W / 2 + 160, 500, "КАМПАНИИ",
                       self.goto_campaigns, font=F_MID)
        cv.create_text(W / 2, 540, text="БОТ: УРОВЕНЬ %d" % self.bot_level, fill=COL_ORANGE,
                       font=F_MID, tags=("dyn",))
        if self.bot_level % 10 == 0:
            cv.create_text(W / 2, 572, text="!! ВНИМАНИЕ: ЭТО БОСС !!", fill=COL_RED, font=F_MID, tags=("dyn",))
        cv.create_text(W / 2, 604, text="ВЫЖИВАНИЕ: волны врагов · каждая 5-я — мини-босс",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))
        cv.create_text(W / 2, 626, text="+50 монет за воина · +100 за мини-босса · бонус за волну",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))
        self.ui.coins(cv, W / 2 - 40, 646, self.coins)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def draw_campaigns(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="КАМПАНИИ", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="КАМПАНИИ", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.coins(cv, W - 190, 50, self.coins)
        for i, c in enumerate(campaign.CAMPAIGNS):
            y0 = 130 + i * 172
            x0, x1, y1 = 60, W - 60, y0 + 152
            locked = not campaign.unlocked(i, self.save)
            prog = campaign.camp_progress(self.save, i)
            done = campaign.camp_done(self.save, i)
            cv.create_rectangle(x0, y0, x1, y1, fill="#1a0908",
                                outline=c["color"] if not locked else "#3a1410", width=3, tags=("dyn",))
            cv.create_text(x0 + 24, y0 + 34, text=c["name"], anchor="w", font=F_BIG,
                           fill=c["color"] if not locked else "#6a3020", tags=("dyn",))
            cv.create_text(x0 + 24, y0 + 64, text=c["desc"], anchor="w", fill=COL_SAND,
                           font=F_SMALL, tags=("dyn",))
            cv.create_text(x0 + 24, y0 + 92, text="НАГРАДА: ЭКСКЛЮЗИВНЫЙ БОЕЦ %s" % c["hero"],
                           anchor="w", fill=COL_GOLD, font=F_SMALL, tags=("dyn",))
            if locked:
                if i == 0:
                    lock_txt = "ОТКРОЕТСЯ НА УРОВНЕ %d" % campaign.UNLOCK_PLVL
                else:
                    lock_txt = "ЗАВЕРШИТЕ ПРЕДЫДУЩУЮ КАМПАНИЮ"
                cv.create_text(x1 - 24, y0 + 76, text=lock_txt, anchor="e", fill="#8a4a20",
                               font=F_MID, tags=("dyn",))
            else:
                cv.create_text(x1 - 24, y0 + 44, text="СТУПЕНЬ %d / %d%s" % (prog, c["stages"],
                               " · ПРОЙДЕНА" if done else ""), anchor="e", fill=COL_ORANGE,
                               font=F_SMALL, tags=("dyn",))
                self.ui.button(cv, x1 - 190, y0 + 92, x1 - 24, y0 + 132, "ВОЙТИ",
                               lambda idx=i: self.open_camp(idx), font=F_SMALL)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def draw_camp_stages(self):
        cv = self.cv
        c = campaign.CAMPAIGNS[self.camp_idx]
        prog = campaign.camp_progress(self.save, self.camp_idx)
        cv.create_text(W / 2 + 3, 93, text=c["name"], font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text=c["name"], font=F_BIG, fill=c["color"], tags=("dyn",))
        cv.create_text(W / 2, 126, text="Ступени открываются по порядку · финальная ступень — БОСС кампании",
                       fill=COL_SAND, font=F_SMALL, tags=("dyn",))
        cols = 5
        cw, ch = 150, 96
        gx = W / 2 - (cols * (cw + 14) - 14) / 2
        for n in range(1, c["stages"] + 1):
            col, row = (n - 1) % cols, (n - 1) // cols
            x0 = gx + col * (cw + 14)
            y0 = 160 + row * (ch + 14)
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
                cv.create_text(x0 + cw / 2, y0 + 72, text="ПРОЙДЕНО", font=F_TINY,
                               fill="#8aff8a", tags=("dyn",))
            elif open_it:
                cv.create_text(x0 + cw / 2, y0 + 72, text="В БОЙ", font=F_TINY,
                               fill=COL_GOLD, tags=("dyn",))
                self.buttons.append((x0, y0, x1, y1,
                                     lambda s=n: self.goto_select(("campaign", self.camp_idx, s))))
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_campaigns, font=F_SMALL)

    def draw_achievements(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="ДОСТИЖЕНИЯ", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="ДОСТИЖЕНИЯ", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.coins(cv, W - 190, 50, self.coins)
        stats = self.save["stats"]
        claimed = set(self.save["ach"])
        per = 15
        page = self.ach_page
        chunk = achievements.ACHIEVEMENTS[page * per:(page + 1) * per]
        for i, a in enumerate(chunk):
            y0 = 124 + i * 34
            got = a["id"] in claimed
            cur = min(stats.get(a["stat"], 0), a["goal"])
            cv.create_rectangle(60, y0, W - 60, y0 + 30, fill="#1a0908" if got else "#160607",
                                outline=COL_GOLD if got else "#3a1410", width=1, tags=("dyn",))
            cv.create_text(76, y0 + 15, text=a["name"], anchor="w", font=F_SMALL,
                           fill=COL_GOLD if got else "#8a4a20", tags=("dyn",))
            cv.create_text(320, y0 + 15, text=a["desc"], anchor="w", font=F_TINY,
                           fill=COL_SAND if got else "#7a4030", tags=("dyn",))
            cv.create_text(W - 220, y0 + 15, text="%d / %d" % (cur, a["goal"]), anchor="e",
                           font=F_TINY, fill="#8aff8a" if got else COL_SAND, tags=("dyn",))
            cv.create_text(W - 76, y0 + 15, text="+%d" % a["reward"], anchor="e", font=F_SMALL,
                           fill=COL_GOLD if got else "#6a5010", tags=("dyn",))
        cv.create_text(W / 2, 648, text="СТРАНИЦА %d / %d" % (page + 1, 3), font=F_SMALL,
                       fill=COL_SAND, tags=("dyn",))
        if page > 0:
            self.ui.button(cv, W / 2 - 220, 630, W / 2 - 120, 666, "<",
                           lambda: self._ach_page(-1), font=F_SMALL)
        if page < 2:
            self.ui.button(cv, W / 2 + 120, 630, W / 2 + 220, 666, ">",
                           lambda: self._ach_page(1), font=F_SMALL)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

    def _ach_page(self, d):
        self.ach_page = max(0, min(2, self.ach_page + d))

    def draw_heroes(self, select_mode):
        cv = self.cv
        sel = self.hero_sel
        keys = [k for k in HEROES if k in self.owned] if select_mode else list(HEROES)
        if sel not in keys and keys:
            sel = keys[0]
            self.hero_sel = sel
            self.preview = Fighter(sel, 640, 1, scale=2.4)
            self.preview.y = 596
        cv.create_rectangle(24, 100, 400, 660, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(212, 122, text="БОЙЦЫ", fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        for i, key in enumerate(keys):
            col, row = i % 3, i // 3
            x0 = 32 + col * 122
            y0 = 144 + row * 49
            x1, y1 = x0 + 116, y0 + 44
            selected = key == sel
            rcol = RARITY_COLOR.get(HEROES[key]["rarity"], "#5a1c10")
            cv.create_rectangle(x0, y0, x1, y1, fill="#2a0f0a" if selected else "#200a08",
                                outline=COL_GOLD if selected else rcol,
                                width=3 if selected else 2, tags=("dyn",))
            draw_hero_icon(cv, key, x0 + 7, y0 + 7, 30)
            cv.create_text(x0 + 44, y0 + 14, text=key, anchor="w", fill=COL_GOLD, font=F_SMALL, tags=("dyn",))
            if not select_mode and key not in self.owned:
                cv.create_text(x0 + 44, y0 + 32, text="%d" % HEROES[key]["price"],
                               anchor="w", fill="#8a4a20", font=F_TINY, tags=("dyn",))
            self.buttons.append((x0, y0, x1, y1, lambda k=key: self.pick_hero(k)))

        if self.preview is not None:
            cv.create_oval(500, 580, 780, 620, fill="#160607", outline="#5a1c10", width=2, tags=("dyn",))
            self.preview.render(cv)
            self.parts.draw(cv)

        hero = HEROES[sel]
        cv.create_rectangle(880, 100, 1256, 668, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(1068, 132, text=sel, fill=COL_GOLD, font=F_BIG, tags=("dyn",))
        cv.create_text(1068, 162, text=hero["title"], fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
        rar = RARITY_LABEL.get(hero["rarity"], hero["rarity"].upper())
        rcol = RARITY_COLOR.get(hero["rarity"], COL_SAND)
        price_tag = "" if hero["price"] <= 0 else " · %d МОНЕТ" % hero["price"]
        cv.create_text(1068, 184, text=rar + price_tag, fill=rcol, font=F_TINY, tags=("dyn",))
        cv.create_text(1068, 226, text=hero["desc"], fill="#e8c9a0", font=F_TINY, width=340, tags=("dyn",))
        cv.create_text(900, 292, text="СТАТЫ", anchor="w", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
        for j, (skey, sname, scol) in enumerate(STAT_NAMES):
            val = hero["stats"][skey]
            yy = 310 + j * 20
            cv.create_text(900, yy, text=sname, anchor="w", fill=COL_SAND, font=F_TINY, tags=("dyn",))
            cv.create_rectangle(990, yy - 5, 1180, yy + 5, fill="#160607", outline="#5a1c10", width=1, tags=("dyn",))
            cv.create_rectangle(990, yy - 5, 990 + val * 19, yy + 5, fill=scol, outline="", tags=("dyn",))
            cv.create_text(1200, yy, text=str(val), anchor="e", fill=COL_GOLD, font=F_TINY, tags=("dyn",))
        cv.create_text(900, 378, text="СПОСОБНОСТИ", anchor="w", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
        step = 50 if len(hero["abilities"]) > 3 else 62
        y = 402
        for i, ab in enumerate(hero["abilities"]):
            ult_tag = " · УЛЬТ" if ab["kind"] == "ult" else ""
            cv.create_text(900, y, text="[%d] %s%s" % (i + 1, ab["name"], ult_tag), anchor="w",
                           fill=COL_RED if ab["kind"] == "ult" else COL_GOLD, font=F_SMALL, tags=("dyn",))
            cv.create_text(1236, y, text="%dс" % ab["cd"], anchor="e", fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
            cv.create_text(920, y + 18, text=ab["desc"], anchor="w", fill=COL_SAND, font=F_TINY,
                           width=310, tags=("dyn",))
            y += step
        sps = hero.get("specials", ())
        if sps:
            cv.create_text(900, y + 2, text="СПЕЦПРИЁМЫ", anchor="w",
                           fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
            cv.create_text(1236, y + 2, text="энергия · кд",
                           anchor="e", fill="#8a4a20", font=F_TINY, tags=("dyn",))
            for sp in sps:
                y += 20
                cv.create_text(900, y, text="[%s] %s" % (sp["combo"], sp["name"]), anchor="w",
                               fill="#ffd24a", font=F_SMALL, tags=("dyn",))
                cv.create_text(1236, y, text="%d · %dс" % (sp["cost"], sp.get("cd", 8)), anchor="e",
                               fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
            y += 20

        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)
        if select_mode:
            nm = getattr(self, "next_mode", "bot")
            if nm == "survival":
                cv.create_text(W / 2, 650, text="РЕЖИМ: ВЫЖИВАНИЕ", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
            elif isinstance(nm, tuple) and nm[0] == "campaign":
                c = campaign.CAMPAIGNS[nm[1]]
                cv.create_text(W / 2, 650, text="КАМПАНИЯ: %s · СТУПЕНЬ %d" % (c["name"], nm[2]),
                               fill=c["color"], font=F_SMALL, tags=("dyn",))
            self.ui.button(cv, W / 2 - 150, 672, W / 2 + 150, 714, "В БОЙ!", self.start_fight, font=F_SMALL)

    def draw_shop(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="МАГАЗИН БОЙЦОВ", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="МАГАЗИН БОЙЦОВ", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.coins(cv, W - 190, 50, self.coins)
        keys = [k for k, v in HEROES.items() if v["rarity"] in ("common", "uncommon", "epic")]
        for i, key in enumerate(keys):
            col, row = i % 5, i // 5
            x0 = 20 + col * 248
            y0 = 120 + row * 120
            x1, y1 = x0 + 240, y0 + 112
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
        if self.shop_msg is not None:
            txt, deadline = self.shop_msg
            if time.time() < deadline:
                cv.create_text(W / 2 + 2, 672, text=txt, font=F_MID, fill="#2a0503", tags=("dyn",))
                cv.create_text(W / 2, 670, text=txt, font=F_MID, fill=COL_GOLD, tags=("dyn",))
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

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
        elif st == "campaigns":
            self.draw_campaigns()
        elif st == "camp_stages":
            self.draw_camp_stages()
        elif st == "achievements":
            self.draw_achievements()
        elif st == "fight":
            if self.arena is not None:
                self.arena.draw(cv, self.coins + (self.arena.run_reward if self.arena.survival else 0))
                draw_ambient(cv, time.time(), self.arena.map)
                draw_torches(cv, time.time(), self.arena.map)
                if self.arena.phase == "end":
                    self.ui.button(cv, W / 2 - 280, 470, W / 2 - 40, 530, "РЕВАНШ", self.start_fight, font=F_SMALL)
                    self.ui.button(cv, W / 2 + 40, 470, W / 2 + 280, 530, "В МЕНЮ", self.goto_menu, font=F_SMALL)
        self.draw_toasts(cv)


def clamp01(v):
    return max(0.0, min(1.0, v))
