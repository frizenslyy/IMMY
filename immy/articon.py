"""IMMY — пиксельные иконки артефактов (рамка тира, цвет природы, знак природы, пипсы тира)."""

import math

from .artifacts import NATURE_COLOR

_TIER_COL = {1: "#8a949e", 2: "#8aff8a", 3: "#5ab0ff", 4: "#c9a0ff", 5: "#ffd23f"}


def draw(cv, art, x, y, size, tags=("dyn",)):
    nat = art.get("nature", "light")
    tier = int(art.get("tier", 1))
    col = NATURE_COLOR.get(nat, "#ffd23f")
    col2 = _TIER_COL.get(tier, "#8a949e")
    x2, y2 = x + size, y + size

    cv.create_rectangle(x, y, x2, y2, fill="#180606", outline=col2, width=max(2, size // 18), tags=tags)
    pad = size * 0.10
    ix0, iy0, ix1, iy1 = x + pad, y + pad, x2 - pad, y2 - pad
    cx, cy = (x + x2) / 2.0, (y + y2) / 2.0
    hw = (ix1 - ix0) / 2.0

    if nat == "light":
        cv.create_oval(ix0, iy0, ix1, iy1, fill=col, outline="#fff7d0", tags=tags)
        for a in range(4):
            ang = a * math.pi / 4 + math.pi / 4
            cv.create_line(cx + math.cos(ang) * hw * 0.72, cy + math.sin(ang) * hw * 0.72,
                           cx + math.cos(ang) * hw * 1.05, cy + math.sin(ang) * hw * 1.05,
                           fill=col, width=max(2, size // 14), tags=tags)
    elif nat == "dark":
        cv.create_polygon(cx, iy0, ix1, iy1, ix0, iy1, fill="#2a1440", outline=col, tags=tags)
        cv.create_oval(cx - hw * 0.30, cy - hw * 0.18, cx - hw * 0.10, cy + hw * 0.10,
                       fill=col, outline="", tags=tags)
        cv.create_oval(cx + hw * 0.10, cy - hw * 0.18, cx + hw * 0.30, cy + hw * 0.10,
                       fill=col, outline="", tags=tags)
    elif nat == "fire":
        cv.create_polygon(cx, iy0, cx + hw * 0.75, iy1, cx - hw * 0.75, iy1,
                          fill="#ff5a1a", outline="", tags=tags)
        cv.create_polygon(cx, iy0 + size * 0.22, cx + hw * 0.42, iy1, cx - hw * 0.42, iy1,
                          fill="#ff8c1a", outline="", tags=tags)
        cv.create_polygon(cx, iy0 + size * 0.42, cx + hw * 0.2, iy1, cx - hw * 0.2, iy1,
                          fill=col, outline="", tags=tags)
    elif nat == "earth":
        cv.create_rectangle(ix0, cy, ix1, iy1, fill="#4a2c12", outline=col, tags=tags)
        for i in range(3):
            gx = ix0 + hw * (0.5 + i * 0.75)
            cv.create_polygon(gx, cy + size * 0.05, gx + size * 0.06, cy, gx + size * 0.12,
                              cy + size * 0.05, fill=col, outline="", tags=tags)
    elif nat == "water":
        cv.create_polygon(cx, iy0, cx + hw * 0.7, cy, cx, iy1, cx - hw * 0.7, cy,
                          fill=col, outline="#bfe9ff", tags=tags)
        cv.create_arc(ix0, cy - size * 0.1, ix1, cy + size * 0.2, start=190, extent=160,
                      style="arc", outline="#e8f6ff", width=max(1, size // 20), tags=tags)
    elif nat == "wind":
        for k in range(3):
            yy = iy0 + size * (0.25 + k * 0.25)
            cv.create_arc(ix0, yy - size * 0.12, x2 - size * 0.05, yy + size * 0.14,
                          start=200, extent=280, style="arc", outline=col,
                          width=max(2, size // 14), tags=tags)
    elif nat == "blood":
        cv.create_polygon(cx - hw * 0.5, iy0, cx + hw * 0.5, iy0, cx, iy1, fill=col, outline="", tags=tags)
        cv.create_oval(cx - hw * 0.12, iy1 - size * 0.06, cx + hw * 0.12, iy1,
                       fill=col, outline="", tags=tags)
    elif nat == "ice":
        for a in range(3):
            ang = a * math.pi / 3
            cv.create_line(cx - math.cos(ang) * hw, cy - math.sin(ang) * hw,
                           cx + math.cos(ang) * hw, cy + math.sin(ang) * hw,
                           fill=col, width=max(2, size // 14), tags=tags)
    elif nat == "metal":
        cv.create_polygon(cx, iy0, ix1, cy, cx, iy1, ix0, cy, fill="#9aa2ac", outline="", tags=tags)
        cv.create_polygon(cx, iy0 + size * 0.14, ix1 - size * 0.14, cy, cx, iy1 - size * 0.14,
                          ix0 + size * 0.14, cy, fill="#c8d0da", outline="", tags=tags)
    elif nat == "poison":
        cv.create_arc(ix0, iy0 + size * 0.1, x2 - size * 0.05, iy1, start=30, extent=280,
                      style="arc", outline=col, width=max(2, size // 12), tags=tags)
        cv.create_oval(cx - size * 0.08, iy1 - size * 0.12, cx + size * 0.08, iy1,
                       fill=col, outline="", tags=tags)
    elif nat == "soul":
        cv.create_oval(cx - hw * 0.55, iy0, cx + hw * 0.55, cy + size * 0.05, fill=col, outline="", tags=tags)
        cv.create_polygon(cx - hw * 0.55, cy, cx + hw * 0.55, cy, cx, iy1, fill=col, outline="", tags=tags)
        cv.create_rectangle(cx - size * 0.14, cy - size * 0.14, cx - size * 0.04, cy - size * 0.04,
                            fill="#180606", outline="", tags=tags)
        cv.create_rectangle(cx + size * 0.04, cy - size * 0.14, cx + size * 0.14, cy - size * 0.04,
                            fill="#180606", outline="", tags=tags)

    pw = max(2, size // 10)
    px = x2 - pad - pw * (2 + 2 * tier) / 2.0
    for t in range(tier):
        cv.create_rectangle(px + t * (pw + 2), y2 - pad - pw, px + t * (pw + 2) + pw, y2 - pad,
                            fill=col2, outline="", tags=tags)
