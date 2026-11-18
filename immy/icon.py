"""IMMY — игровая пиксельная иконка 32x32 (череп с короной в тёплой палитре)."""

PALETTE = {
    ".": None,
    "k": "#120404",
    "r": "#7a1a08",
    "o": "#c93a10",
    "d": "#2a0806",
    "y": "#ffd23f",
    "Y": "#ff8c1a",
    "w": "#e8d8c0",
    "W": "#fff2dc",
    "g": "#8a6a10",
    "R": "#ff3b14",
}


def grid32():
    g = [["." for _ in range(32)] for _ in range(32)]

    def px(x, y, c):
        if 0 <= x < 32 and 0 <= y < 32:
            g[y][x] = c

    def rect(x0, y0, x1, y1, c):
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                px(xx, yy, c)

    for yy in range(32):
        for xx in range(32):
            dx, dy = xx - 15.5, yy - 15.5
            if dx * dx + dy * dy <= 14.5 * 14.5:
                px(xx, yy, "k")
            dxr, dyr = xx - 15.5, yy - 15.5
            if 14.5 * 14.5 - 3 * 14.5 <= dxr * dxr + dyr * dyr <= 14.5 * 14.5:
                px(xx, yy, "r")

    crown = [
        (6, 3, 25, 5, "y"),
        (6, 3, 6, 3, "y"), (10, 2, 10, 3, "y"), (14, 2, 14, 3, "y"),
        (18, 2, 18, 3, "y"), (22, 2, 22, 3, "y"), (25, 3, 25, 3, "y"),
    ]
    rect(6, 5, 25, 7, "g")
    rect(5, 5, 6, 2, "y")
    rect(10, 3, 10, 4, "y")
    rect(14, 2, 15, 4, "y")
    rect(18, 3, 18, 4, "y")
    rect(22, 3, 22, 4, "y")
    rect(25, 5, 26, 2, "y")
    for x0, y0, x1, y1, c in crown:
        rect(x0, y0, x1, y1, c)
    rect(4, 8, 27, 20, "w")
    rect(6, 6, 7, 8, "w")
    rect(24, 6, 25, 8, "w")
    rect(5, 10, 8, 13, "W")
    rect(23, 10, 26, 13, "W")
    for yy in range(9, 19):
        rect(4, yy, 4, yy, "w")
        rect(27, yy, 27, yy, "w")
    rect(8, 11, 12, 15, "k")
    rect(19, 11, 23, 15, "k")
    rect(9, 12, 11, 14, "R")
    rect(20, 12, 22, 14, "R")
    rect(15, 15, 16, 17, "k")
    rect(14, 17, 17, 18, "k")
    rect(11, 21, 20, 25, "w")
    for tx in range(11, 21, 2):
        rect(tx, 23, tx, 25, "k")
    rect(11, 25, 20, 26, "g")
    return ["".join(r) for r in g]


def build_icon():
    import tkinter as tk

    img = tk.PhotoImage(width=32, height=32)
    rows = grid32()
    for y, row in enumerate(rows):
        cells = " ".join(PALETTE.get(ch) or "#000000" for ch in row)
        if any(PALETTE.get(ch) for ch in row):
            img.put("{%s}" % cells, to=(0, y))
    return img
