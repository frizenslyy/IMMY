"""IMMY — главный класс игры: окна, ввод, магазин, цикл кадров, музыка."""

import random
import time
import tkinter as tk

from .arena import Arena
from .background import (MAPS, draw_fight_bg, draw_hero_icon, draw_menu_bg,
                         draw_screen_bg, draw_torches)
from .config import (COL_GOLD, COL_ORANGE, COL_SAND, F_BIG, F_MID, F_SMALL,
                     F_SQUARE, F_TINY, H, TICK_MS, TITLE, W)
from .fighter import Fighter
from .heroes import HEROES, RARITY_LABEL
from .particles import Embers, Particles
from .save import load_save, save_save
from .sound import Music
from .ui import Ui

CYR = {"ц": "w", "ф": "a", "ы": "s", "в": "d",
       "tse": "w", "ef": "a", "yeru": "s", "ve": "d"}


def norm_key(e):
    k = (e.keysym or "").lower()
    if k.startswith("cyrillic_"):
        return CYR.get(k[9:], k)
    ch = (getattr(e, "char", "") or "").lower()
    if ch in CYR:
        return CYR[ch]
    return k


class Game(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry("%dx%d" % (W, H))
        self.resizable(False, False)
        self.cv = tk.Canvas(self, width=W, height=H, bg="#120406", highlightthickness=0)
        self.cv.pack()
        self.coins, self.bot_level, self.owned = load_save()
        self.state = "menu"
        self.hero_sel = "DEADY"
        self.keys = set()
        self.events = set()
        self.buttons = []
        self.mouse = (0, 0)
        self.arena = None
        self.preview = None
        self.parts = Particles()
        self.ui = Ui(self)
        self.embers = Embers()
        self.music = Music()
        self.shop_msg = None
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

    def goto_menu(self):
        self.set_state("menu")

    def goto_mode(self):
        self.set_state("mode")

    def goto_heroes(self):
        self.set_state("heroes")

    def goto_select(self):
        self.set_state("select")

    def goto_shop(self):
        self.shop_msg = None
        self.set_state("shop")

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
        save_save(self.coins, self.bot_level, self.owned)
        self.shop_msg = ("КУПЛЕНО: %s!" % hero["name"], time.time() + 2.5)

    def start_fight(self):
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
            elif k in ("1", "2", "3"):
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
               "attack": "attack" in self.events, "cast": None}
        if "a" in self.keys:
            inp["move"] -= 1
        if "d" in self.keys:
            inp["move"] += 1
        for e in self.events:
            if e in ("1", "2", "3"):
                inp["cast"] = int(e) - 1
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
                self.arena.rewarded = True
                if self.arena.win:
                    self.coins += self.arena.reward
                    self.bot_level += 1
                    save_save(self.coins, self.bot_level, self.owned)
        self.draw()

    def draw_menu(self):
        cv = self.cv
        cx = W // 2
        self.ui.button(cv, cx - 100, 300, cx + 100, 500, "PLAY", self.goto_mode, font=F_SQUARE)
        self.ui.button(cv, cx - 160, 545, cx + 160, 615, "HEROES", self.goto_heroes, font=F_MID)
        self.ui.button(cv, cx - 160, 628, cx + 160, 694, "SHOP", self.goto_shop, font=F_MID)
        self.ui.coins(cv, 30, H - 40, self.coins)
        cv.create_text(W - 30, H - 40, text="БОТ: УР. %d" % self.bot_level, anchor="e",
                       fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        cv.create_text(W / 2, H - 14, text="ЛКМ — атака · WASD — движение · 1/2/3 — способности · M — музыка",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))

    def draw_mode(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 133, text="ВЫБОР РЕЖИМА", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 130, text="ВЫБОР РЕЖИМА", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.button(cv, W / 2 - 120, 240, W / 2 + 120, 480, "VS БОТ", self.goto_select, font=F_SQUARE)
        cv.create_text(W / 2, 530, text="БОТ: УРОВЕНЬ %d" % self.bot_level, fill=COL_ORANGE,
                       font=F_MID, tags=("dyn",))
        if self.bot_level % 10 == 0:
            cv.create_text(W / 2, 566, text="!! ВНИМАНИЕ: ЭТО БОСС !!", fill="#ff2a1a", font=F_MID, tags=("dyn",))
        self.ui.coins(cv, W / 2 - 40, 610, self.coins)
        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)

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
        cv.create_text(212, 128, text="БОЙЦЫ", fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        for i, key in enumerate(keys):
            col, row = i % 2, i // 2
            x0 = 40 + col * 182
            y0 = 150 + row * 72
            x1, y1 = x0 + 170, y0 + 64
            selected = key == sel
            cv.create_rectangle(x0, y0, x1, y1, fill="#2a0f0a" if selected else "#200a08",
                                outline=COL_GOLD if selected else "#5a1c10",
                                width=3 if selected else 2, tags=("dyn",))
            draw_hero_icon(cv, key, x0 + 10, y0 + 12, 40)
            cv.create_text(x0 + 58, y0 + 26, text=key, anchor="w", fill=COL_GOLD, font=F_SMALL, tags=("dyn",))
            if not select_mode and key not in self.owned:
                cv.create_text(x0 + 58, y0 + 47, text="%d МОНЕТ" % HEROES[key]["price"],
                               anchor="w", fill="#8a4a20", font=F_TINY, tags=("dyn",))
            self.buttons.append((x0, y0, x1, y1, lambda k=key: self.pick_hero(k)))

        if self.preview is not None:
            cv.create_oval(500, 580, 780, 620, fill="#160607", outline="#5a1c10", width=2, tags=("dyn",))
            self.preview.render(cv)
            self.parts.draw(cv)

        hero = HEROES[sel]
        cv.create_rectangle(880, 100, 1256, 660, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(1068, 136, text=sel, fill=COL_GOLD, font=F_BIG, tags=("dyn",))
        cv.create_text(1068, 168, text=hero["title"], fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
        rar = RARITY_LABEL.get(hero["rarity"], hero["rarity"].upper())
        price_tag = "" if hero["price"] <= 0 else " · %d МОНЕТ" % hero["price"]
        cv.create_text(1068, 190, text=rar + price_tag, fill=COL_SAND, font=F_TINY, tags=("dyn",))
        cv.create_text(1068, 236, text=hero["desc"], fill="#e8c9a0", font=F_TINY, width=340, tags=("dyn",))
        cv.create_text(1068, 300, text="СПОСОБНОСТИ", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
        y = 330
        for i, ab in enumerate(hero["abilities"]):
            cv.create_text(900, y, text="[%d] %s" % (i + 1, ab["name"]), anchor="w", fill=COL_GOLD,
                           font=F_SMALL, tags=("dyn",))
            cv.create_text(1236, y, text="%dс" % ab["cd"], anchor="e", fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
            cv.create_text(920, y + 22, text=ab["desc"], anchor="w", fill=COL_SAND, font=F_TINY,
                           width=310, tags=("dyn",))
            y += 100

        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)
        if select_mode:
            self.ui.button(cv, W / 2 - 150, 672, W / 2 + 150, 714, "В БОЙ!", self.start_fight, font=F_SMALL)

    def draw_shop(self):
        cv = self.cv
        cv.create_text(W / 2 + 3, 93, text="МАГАЗИН БОЙЦОВ", font=F_BIG, fill="#2a0503", tags=("dyn",))
        cv.create_text(W / 2, 90, text="МАГАЗИН БОЙЦОВ", font=F_BIG, fill=COL_GOLD, tags=("dyn",))
        self.ui.coins(cv, W - 190, 50, self.coins)
        keys = [k for k, v in HEROES.items() if v["rarity"] != "standard"]
        for i, key in enumerate(keys):
            col, row = i % 4, i // 4
            x0 = 40 + col * 300
            y0 = 140 + row * 165
            x1, y1 = x0 + 280, y0 + 150
            hero = HEROES[key]
            owned = key in self.owned
            afford = self.coins >= hero["price"]
            cv.create_rectangle(x0, y0, x1, y1, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
            draw_hero_icon(cv, key, x0 + 14, y0 + 14, 56)
            cv.create_text(x0 + 84, y0 + 34, text=hero["name"], anchor="w", fill=COL_GOLD,
                           font=F_MID, tags=("dyn",))
            rar = RARITY_LABEL.get(hero["rarity"], hero["rarity"].upper())
            cv.create_text(x0 + 84, y0 + 58, text=rar, anchor="w", fill=COL_SAND, font=F_TINY, tags=("dyn",))
            if owned:
                cv.create_text(x0 + 14, y1 - 24, text="КУПЛЕНО", anchor="w", fill="#8aff8a",
                               font=F_SMALL, tags=("dyn",))
            else:
                price_col = COL_GOLD if afford else "#8a4a20"
                cv.create_text(x0 + 14, y1 - 24, text="%d МОНЕТ — КУПИТЬ" % hero["price"],
                               anchor="w", fill=price_col, font=F_SMALL, tags=("dyn",))
                self.buttons.append((x0, y0, x1, y1, lambda k=key: self.buy_hero(k)))
        if self.shop_msg is not None:
            txt, deadline = self.shop_msg
            if time.time() < deadline:
                cv.create_text(W / 2 + 2, 672, text=txt, font=F_MID, fill="#2a0503", tags=("dyn",))
                cv.create_text(W / 2, 670, text=txt, font=F_MID, fill=COL_GOLD, tags=("dyn",))
        cv.create_text(W / 2, 706, text="Нажмите на карточку бойца, чтобы купить его",
                       fill=COL_SAND, font=F_TINY, tags=("dyn",))
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
        elif st == "fight":
            if self.arena is not None:
                self.arena.draw(cv, self.coins)
                draw_torches(cv, time.time(), self.arena.map)
                if self.arena.phase == "end":
                    self.ui.button(cv, W / 2 - 280, 470, W / 2 - 40, 530, "РЕВАНШ", self.start_fight, font=F_SMALL)
                    self.ui.button(cv, W / 2 + 40, 470, W / 2 + 280, 530, "В МЕНЮ", self.goto_menu, font=F_SMALL)
