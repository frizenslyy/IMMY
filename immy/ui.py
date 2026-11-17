"""IMMY — элементы интерфейса: кнопки, счётчики монет и самоцветов."""

from .config import COL_GEM, F_BIG, F_MID


class Ui:
    def __init__(self, game):
        self.g = game

    def button(self, cv, x0, y0, x1, y1, text, action, font=F_BIG):
        mx, my = self.g.mouse
        hov = x0 <= mx <= x1 and y0 <= my <= y1
        cv.create_rectangle(x0 + 5, y0 + 5, x1 + 5, y1 + 5, fill="#160404", outline="", tags=("dyn",))
        cv.create_rectangle(x0, y0, x1, y1, fill="#5a1c10" if hov else "#3a100a",
                            outline="#ffd23f" if hov else "#7a1c10", width=3, tags=("dyn",))
        cv.create_rectangle(x0 + 6, y0 + 6, x1 - 6, y1 - 6, outline="#a13414", width=1, tags=("dyn",))
        cv.create_text((x0 + x1) // 2, (y0 + y1) // 2, text=text,
                       fill="#ffd23f" if hov else "#ff8c1a", font=font, tags=("dyn",))
        self.g.buttons.append((x0, y0, x1, y1, action))

    def coins(self, cv, x, y, coins):
        cv.create_oval(x, y - 9, x + 18, y + 9, fill="#ffd23f", outline="#a1700a", width=2, tags=("dyn",))
        cv.create_text(x + 28, y, text=str(coins), anchor="w", fill="#ffd23f", font=F_MID, tags=("dyn",))

    def gems(self, cv, x, y, gems):
        r = 10
        cv.create_polygon(x + r, y - r, x + r * 1.7, y, x + r, y + r, x + r * 0.3, y,
                          fill=COL_GEM, outline="#1a6a3a", width=2, tags=("dyn",))
        cv.create_text(x + r * 2.2, y, text=str(gems), anchor="w", fill=COL_GEM, font=F_MID, tags=("dyn",))
