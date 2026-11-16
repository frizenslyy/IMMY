"""IMMY — математические помощники и градиенты."""


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, a, b):
    return max(a, min(b, v))


def grad_color(stops, t):
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if t <= p1 or i == len(stops) - 2:
            tt = clamp((t - p0) / max(1e-6, p1 - p0), 0.0, 1.0)
            return "#%02x%02x%02x" % tuple(int(lerp(c0[j], c1[j], tt)) for j in range(3))
    return "#000000"


def gradient(cv, x0, y0, x1, y1, stops, steps=90, tag="bg"):
    hh = (y1 - y0) / steps
    for i in range(steps):
        t = i / (steps - 1)
        c = grad_color(stops, t)
        cv.create_rectangle(x0, y0 + i * hh, x1, y0 + (i + 1) * hh + 1, fill=c, outline=c, tags=(tag,))
