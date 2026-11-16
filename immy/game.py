"""IMMY — главный класс игры: окна, ввод, цикл кадров."""

import random
import time
import tkinter as tk

from .arena import Arena
from .background import draw_fight_bg, draw_hero_icon, draw_menu_bg, draw_torches
from .config import (COL_GOLD, COL_ORANGE, COL_SAND, F_BIG, F_MID, F_SMALL, F_SQUARE,
                     F_TINY, H, TICK_MS, TITLE, W)
from .fighter import Fighter
from .heroes import HEROES
from .particles import Embers, Particles
from .save import load_save, save_save
from .ui import Ui


class Game(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry("%dx%d" % (W, H))
        self.resizable(False, False)
        self.cv = tk.Canvas(self, width=W, height=H, bg="#120406", highlightthickness=0)
        self.cv.pack()
        self.coins, self.bot_level = load_save()
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
        if s == "fight":
            draw_fight_bg(self.cv)
        else:
            draw_menu_bg(self.cv)
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

    def pick_hero(self, key):
        self.hero_sel = key
        if self.state in ("heroes", "select"):
            self.preview = Fighter(key, 640, 1, scale=2.4)
            self.preview.y = 596

    def start_fight(self):
        level = self.bot_level
        boss = level % 10 == 0
        bot_key = random.choice([k for k in HEROES if k != self.hero_sel])
        self.arena = Arena(self.hero_sel, bot_key, level, boss)
        self.set_state("fight")

    def on_key(self, e):
        k = e.keysym.lower()
        if k == "escape":
            if self.state != "menu":
                self.set_state("menu")
            return
        if self.state == "fight":
            if k == "w":
                self.events.add("jump")
            elif k in ("1", "2", "3"):
                self.events.add(k)
        self.keys.add(k)

    def on_key_release(self, e):
        self.keys.discard(e.keysym.lower())

    def on_motion(self, e):
        self.mouse = (e.x, e.y)

    def on_click(self, e):
        if self.state == "fight":
            if self.arena is not None and self.arena.phase == "fight":
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
                    save_save(self.coins, self.bot_level)
        self.draw()

    def draw_menu(self):
        cv = self.cv
        cx = W // 2
        self.ui.button(cv, cx - 100, 300, cx + 100, 500, "PLAY", self.goto_mode, font=F_SQUARE)
        self.ui.button(cv, cx - 160, 550, cx + 160, 624, "HEROES", self.goto_heroes, font=F_MID)
        self.ui.coins(cv, 30, H - 40, self.coins)
        cv.create_text(W - 30, H - 40, text="БОТ: УР. %d" % self.bot_level, anchor="e",
                       fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        cv.create_text(W / 2, H - 14, text="ЛКМ — атака · WASD — движение · 1/2/3 — способности",
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
        cv.create_rectangle(24, 100, 396, 660, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(210, 130, text="БОЙЦЫ", fill=COL_ORANGE, font=F_MID, tags=("dyn",))
        for i, key in enumerate(HEROES):
            y0 = 160 + i * 165
            selected = key == sel
            cv.create_rectangle(40, y0, 380, y0 + 145, fill="#2a0f0a" if selected else "#200a08",
                                outline=COL_GOLD if selected else "#5a1c10",
                                width=3 if selected else 2, tags=("dyn",))
            draw_hero_icon(cv, key, 56, y0 + 22, 100)
            cv.create_text(180, y0 + 72, text=key, fill=COL_GOLD, font=F_BIG, tags=("dyn",))
            self.buttons.append((40, y0, 380, y0 + 145, lambda k=key: self.pick_hero(k)))

        if self.preview is not None:
            cv.create_oval(500, 580, 780, 620, fill="#160607", outline="#5a1c10", width=2, tags=("dyn",))
            self.preview.render(cv)
            self.parts.draw(cv)

        hero = HEROES[sel]
        cv.create_rectangle(880, 100, 1256, 660, fill="#1a0908", outline="#5a1c10", width=2, tags=("dyn",))
        cv.create_text(1068, 140, text=sel, fill=COL_GOLD, font=F_BIG, tags=("dyn",))
        cv.create_text(1068, 176, text=hero["title"], fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
        cv.create_text(1068, 240, text=hero["desc"], fill="#e8c9a0", font=F_TINY, width=340, tags=("dyn",))
        cv.create_text(1068, 316, text="СПОСОБНОСТИ", fill=COL_ORANGE, font=F_SMALL, tags=("dyn",))
        y = 352
        for i, (nm, ds, cd) in enumerate(hero["abilities"]):
            cv.create_text(900, y, text="[%d] %s" % (i + 1, nm), anchor="w", fill=COL_GOLD,
                           font=F_SMALL, tags=("dyn",))
            cv.create_text(1236, y, text="%dс" % cd, anchor="e", fill="#ff5a1a", font=F_SMALL, tags=("dyn",))
            cv.create_text(920, y + 22, text=ds, anchor="w", fill=COL_SAND, font=F_TINY, width=310, tags=("dyn",))
            y += 92

        self.ui.button(cv, 24, 24, 150, 70, "НАЗАД", self.goto_menu, font=F_SMALL)
        if select_mode:
            self.ui.button(cv, W / 2 - 150, 672, W / 2 + 150, 714, "В БОЙ!", self.start_fight, font=F_SMALL)

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
        elif st == "fight":
            if self.arena is not None:
                self.arena.draw(cv, self.coins)
                draw_torches(cv, time.time())
                if self.arena.phase == "end":
                    self.ui.button(cv, W / 2 - 280, 470, W / 2 - 40, 530, "РЕВАНШ", self.start_fight, font=F_SMALL)
                    self.ui.button(cv, W / 2 + 40, 470, W / 2 + 280, 530, "В МЕНЮ", self.goto_menu, font=F_SMALL)
