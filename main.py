#!/usr/bin/env python3
"""Front Page - 19 November 2026.

Draws a 1024x1024 broadsheet newspaper front page ("THE WORLD IN ONE DAY")
as a PNG, using only the Python standard library. No network, no image
assets, fully deterministic: two runs produce byte-identical output.

Usage:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 232)
INK = (22, 22, 22)
RED = (196, 30, 30)
GREY = (110, 108, 100)
LIGHT_LINE = (180, 175, 162)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 bits, '#' = on, '.' = off. Uppercase + digits +
# the punctuation this poster needs.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '•': ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
    '€': ("00110", "01001", "10000", "11110", "10000", "01001", "00110"),
}

# ------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.clip = None  # optional (x0, y0, x1, y1) exclusive bounds
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[i * 3] = bg[0]
            self.px[i * 3 + 1] = bg[1]
            self.px[i * 3 + 2] = bg[2]

    def set(self, x, y, c):
        if self.clip is not None:
            cx0, cy0, cx1, cy1 = self.clip
            if not (cx0 <= x < cx1 and cy0 <= y < cy1):
                return
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def border(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if abs(d - r * r) <= r:
                        self.set(xx, yy, c)

    def disc(self, cx, cy, r, c):
        self.circle(cx, cy, r, c, fill=True)

    def ring(self, cx, cy, r, c, t=2):
        for k in range(t):
            self.circle(cx, cy, r - k, c, fill=False)

    def poly(self, pts, c):
        """Scanline fill of a polygon given as [(x, y), ...]."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, c)


# ------------------------------------------------------------- PNG encoder
def _chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------- text
def text_width(s, scale):
    """Width in px of string s at the given font scale."""
    return len(s) * (5 * scale + scale) - scale


def draw_char(cv, x, y, ch, scale, c):
    glyph = FONT[ch]
    for row in range(7):
        bits = glyph[row]
        for col in range(5):
            if bits[col] == '1':
                cv.rect(x + col * scale, y + row * scale, scale, scale, c)


def draw_text(cv, x, y, s, scale, c):
    """Draw s (uppercased into the 5x7 font) left-aligned at (x, y)."""
    s = s.upper()
    cx = x
    for ch in s:
        draw_char(cv, cx, y, ch, scale, c)
        cx += 5 * scale + scale
    return cx


def draw_text_centered(cv, cx, y, s, scale, c):
    w = text_width(s, scale)
    draw_text(cv, cx - w // 2, y, s, scale, c)
    return w


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns list of lines, each <= max_w px."""
    cw = 5 * scale + scale
    max_chars = max(1, max_w // cw)
    lines = []
    for para in s.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            trial = w if not cur else cur + " " + w
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                # long single word: hard-split it
                while len(w) > max_chars:
                    lines.append(w[:max_chars])
                    w = w[max_chars:]
                cur = w
        if cur:
            lines.append(cur)
    return lines


def draw_para(cv, x, y, s, scale, c, max_w, leading=None):
    """Draw a wrapped paragraph; returns the y just below the last line."""
    if leading is None:
        leading = 7 * scale + scale + 3
    for line in wrap_text(s, scale, max_w):
        draw_text(cv, x, y, line, scale, c)
        y += leading
    return y


# ------------------------------------------------------- Vice City art
def draw_vice_city(cv, x, y, w, h):
    """Neon Vice City skyline: dusk gradient sky, striped sun, towers,
    palm trees and a reflective bay. All procedural. Clipped to its box
    so no tower or palm can ever spill into a neighbouring panel."""
    cv.clip = (x, y, x + w, y + h)
    # dusk sky: horizontal bands, deep purple -> magenta -> orange
    bands = [
        ((24, 10, 54), 0.00),
        ((58, 16, 88), 0.22),
        ((110, 26, 96), 0.42),
        ((178, 48, 92), 0.60),
        ((232, 96, 66), 0.74),
        ((250, 160, 90), 0.84),
    ]
    for yy in range(h):
        t = yy / max(1, h - 1)
        # pick band colour by interpolation between stops
        col = bands[0][0]
        for i in range(len(bands) - 1):
            c0, t0 = bands[i]
            c1, t1 = bands[i + 1]
            if t0 <= t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                col = tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                break
        else:
            col = bands[-1][0]
        cv.hline(x, y + yy, w, col)

    # stars in the upper sky
    stars = [(18, 12), (52, 30), (96, 8), (150, 22), (210, 10), (260, 28),
             (330, 14), (380, 26), (430, 8), (480, 20), (120, 44), (300, 40)]
    for sx, sy in stars:
        if sx < w - 4 and sy < int(h * 0.3):
            cv.rect(x + sx, y + sy, 2, 2, (255, 240, 200))

    # striped retro sun, raised so it clears the tallest towers
    scx, scy, sr = x + w // 2, y + int(h * 0.34), 50
    cv.disc(scx, scy, sr, (255, 214, 90))
    cv.disc(scx, scy, sr - 8, (255, 170, 60))
    # horizontal slits across the lower half of the sun
    for k, gap in enumerate((4, 7, 10, 14)):
        yy = scy + 8 + k * 9
        cv.hline(scx - sr, yy, 2 * sr, (232, 96, 66), gap)

    # skyline: deterministic tower silhouettes with lit windows
    # (heights lowered so the sun stays visible above the rooftops)
    horizon = y + int(h * 0.68)
    towers = [
        (0.00, 0.30, 0.14), (0.07, 0.22, 0.24), (0.15, 0.34, 0.17),
        (0.24, 0.26, 0.32), (0.33, 0.40, 0.22), (0.42, 0.24, 0.27),
        (0.50, 0.36, 0.15), (0.58, 0.28, 0.34), (0.66, 0.42, 0.20),
        (0.75, 0.26, 0.28), (0.83, 0.34, 0.18), (0.90, 0.30, 0.24),
    ]
    for fx, fw, fh in towers:
        tx = x + int(fx * w)
        tw = int(fw * w)
        th = int(fh * h)
        cv.rect(tx, horizon - th, tw, th, (26, 10, 44))
        # rooftop beacon
        cv.rect(tx + tw // 2 - 2, horizon - th - 5, 4, 5, (255, 80, 90))
        # lit windows
        for wy in range(horizon - th + 8, horizon - 6, 14):
            for wx in range(tx + 5, tx + tw - 5, 12):
                if (wx * 7 + wy * 13) % 5 < 2:
                    cv.rect(wx, wy, 4, 5, (255, 214, 120))

    # bay: dark water with neon reflections
    cv.rect(x, horizon, w, y + h - horizon, (16, 8, 40))
    for k, (fx, col) in enumerate(((0.30, (255, 170, 60)), (0.52, (255, 120, 140)),
                                   (0.72, (120, 220, 255)), (0.12, (255, 120, 140)))):
        rx = x + int(fx * w)
        for j in range(4):
            rw = 46 - j * 9
            cv.hline(rx - rw // 2, horizon + 8 + j * 9, rw, col, 2)

    # palm trees, left and right foreground (brighter, taller, trunks
    # visible against the water)
    def palm(px, py, s, lean):
        trunk = (110, 72, 44)
        cv.line(px, py, px + lean, py - int(56 * s), trunk, 4)
        top = (px + lean, py - int(56 * s))
        fronds = [(-1, -0.4), (-0.7, -0.9), (-0.2, -1.0), (0.3, -0.95),
                  (0.8, -0.7), (1.0, -0.3)]
        for fx, fy in fronds:
            ex = top[0] + int(fx * 38 * s)
            ey = top[1] + int(fy * 18 * s)
            cv.line(top[0], top[1], ex, ey, (46, 170, 96), 3)
            cv.line(top[0], top[1], ex, ey + 7, (46, 170, 96), 3)

    palm(x + 30, y + h - 4, 1.3, 12)
    palm(x + w - 36, y + h - 4, 1.15, -14)
    cv.clip = None
    cv.border(x, y, w, h, INK, 2)


# ------------------------------------------------------------- page
def draw_panel(cv, x, y, w, h, kicker, headline_lines, deck,
               head_scale=3, pad=16):
    """A bordered news panel: red kicker, headline lines, rule, deck."""
    cv.border(x, y, w, h, INK, 2)
    cx = x + pad
    cw = w - 2 * pad
    cy = y + 14
    draw_text(cv, cx, cy, kicker, 2, RED)
    cy += 14 + 10
    for line in headline_lines:
        draw_text(cv, cx, cy, line, head_scale, INK)
        cy += 7 * head_scale + 8
    cy += 2
    cv.hline(cx, cy, cw, LIGHT_LINE, 2)
    cy += 10
    cy = draw_para(cv, cx, cy, deck, 2, INK, cw, leading=17)
    return cy


def draw_bridge(cv, x, y, w, h):
    """Small bridge silhouette: deck, arc, towers, cables."""
    deck_y = y + h - 6
    cv.hline(x, deck_y, w, INK, 3)
    # arc above the deck
    import math
    for k in range(61):
        t = k / 60.0
        ax = x + int(t * w)
        ay = deck_y - int(4 * (h - 10) * t * (1 - t))
        cv.rect(ax - 1, ay - 1, 3, 3, INK)
    for fx in (0.25, 0.75):
        tx = x + int(fx * w)
        cv.vline(tx, deck_y - int(h * 0.6), int(h * 0.6), INK, 4)
        cv.rect(tx - 5, deck_y - int(h * 0.6) - 4, 13, 4, INK)
    # cables
    for fx in (0.25, 0.75):
        tx = x + int(fx * w)
        cv.line(tx, deck_y - int(h * 0.55), x + int(w * 0.5), deck_y, GREY, 2)


def draw_cyclone(cv, cx, cy, rmax):
    """Spiral storm: concentric broken rings + spiral arms."""
    import math
    for r in range(rmax, 5, -6):
        for deg in range(0, 360, 5):
            if (deg // 30) % 2 == 0:
                continue
            a = math.radians(deg)
            cv.rect(int(cx + r * math.cos(a)) - 1,
                    int(cy + r * math.sin(a) * 0.8) - 1, 2, 2, INK)
    # spiral arms
    for k in range(80):
        t = k / 79.0
        a = t * math.pi * 3.2
        r = 4 + t * (rmax - 4)
        cv.rect(int(cx + r * math.cos(a)) - 1,
                int(cy + r * math.sin(a) * 0.8) - 1, 2, 2, RED)
    cv.disc(cx, cy, 4, INK)


def build_page():
    cv = Canvas(W, H, PAPER)
    cv.border(16, 16, W - 32, H - 32, INK, 3)

    # masthead
    draw_text_centered(cv, W // 2, 30, "THE WORLD IN ONE DAY", 7, INK)
    cv.hline(24, 92, W - 48, INK, 2)
    cv.hline(24, 97, W - 48, INK, 1)

    # red date banner
    cv.rect(24, 104, W - 48, 36, RED)
    draw_text_centered(cv, W // 2, 112, "THURSDAY, 19 NOVEMBER 2026", 3,
                       (255, 255, 255))

    # ---- lead story -------------------------------------------------
    cv.border(24, 152, 576, 438, INK, 2)
    draw_text(cv, 40, 166, "CULTURE", 2, RED)
    draw_text(cv, 40, 190, "GAMERS ENTER", 5, INK)
    draw_text(cv, 40, 233, "VICE CITY", 5, INK)
    cv.hline(40, 282, 544, LIGHT_LINE, 2)
    draw_para(cv, 40, 294,
              "After a 13-year wait, Grand Theft Auto VI begins its "
              "global rollout; gamers enter Vice City.",
              2, INK, 544, leading=17)
    draw_vice_city(cv, 40, 354, 544, 220)

    # ---- right column ----------------------------------------------
    draw_panel(cv, 616, 152, 384, 212,
               "ASIA • APEC SUMMIT",
               ["TRUMP, XI AND PUTIN", "MEET IN SHENZHEN"],
               "Xi hugs Trump on the tarmac as the three leaders gather "
               "in Shenzhen for a first trilateral meeting.")
    draw_panel(cv, 616, 376, 384, 214,
               "UNITED STATES",
               ["JEFFRIES SET TO", "MAKE HISTORY"],
               "Democrat Hakeem Jeffries nominated as Speaker - set to be "
               "the first African-American to hold the post.")

    # ---- bottom row -------------------------------------------------
    draw_panel(cv, 24, 602, 480, 186,
               "UKRAINE",
               ["CRIMEAN BRIDGE", "HIT AGAIN"],
               "The Crimean Bridge is attacked again, a Russian "
               "official says.")
    draw_bridge(cv, 48, 748, 432, 32)
    draw_panel(cv, 520, 602, 480, 186,
               "WEATHER • INDIA",
               ["CYCLONE AKVAN", "NEARS INDIA"],
               "Cyclone Akvan is likely to cross the coast between "
               "Machilipatnam and Puri.")
    draw_cyclone(cv, 760, 770, 24)

    # ---- In Brief ---------------------------------------------------
    cv.border(24, 800, 976, 166, INK, 2)
    draw_text(cv, 40, 814, "IN BRIEF", 3, INK)
    cv.hline(40, 840, 944, RED, 3)
    brief = [
        "Van Gogh painting sells for a record $190.4m.",
        "Claude-maker Anthropic poised for a $1.4tn+ stock market debut.",
        "Myanmar faces a historic ICJ genocide verdict over the Rohingya.",
        "EU proposes a €45 billion Ukraine loan.",
        "NASA's Voyager 1 believed to have reached a 'light-day' milestone.",
        "Israeli military launches a rare ground operation in Gaza beyond "
        "the Yellow Line.",
    ]
    for col, items in enumerate((brief[:3], brief[3:])):
        x = 40 + col * 484
        y = 850
        for item in items:
            y = draw_para(cv, x, y, "• " + item, 2, INK, 460, leading=15)
            y += 4

    # footer
    draw_text_centered(cv, W // 2, 976,
                       "ALL EVENTS OF THURSDAY, 19 NOVEMBER 2026", 2, GREY)
    return cv


ALL_TEXT = [
    "THE WORLD IN ONE DAY",
    "THURSDAY, 19 NOVEMBER 2026",
    "CULTURE", "GAMERS ENTER", "VICE CITY",
    "After a 13-year wait, Grand Theft Auto VI begins its global rollout; "
    "gamers enter Vice City.",
    "ASIA • APEC SUMMIT", "TRUMP, XI AND PUTIN", "MEET IN SHENZHEN",
    "Xi hugs Trump on the tarmac as the three leaders gather in Shenzhen "
    "for a first trilateral meeting.",
    "UNITED STATES", "JEFFRIES SET TO", "MAKE HISTORY",
    "Democrat Hakeem Jeffries nominated as Speaker - set to be the first "
    "African-American to hold the post.",
    "UKRAINE", "CRIMEAN BRIDGE", "HIT AGAIN",
    "The Crimean Bridge is attacked again, a Russian official says.",
    "WEATHER • INDIA", "CYCLONE AKVAN", "NEARS INDIA",
    "Cyclone Akvan is likely to cross the coast between Machilipatnam "
    "and Puri.",
    "IN BRIEF",
    "Van Gogh painting sells for a record $190.4m.",
    "Claude-maker Anthropic poised for a $1.4tn+ stock market debut.",
    "Myanmar faces a historic ICJ genocide verdict over the Rohingya.",
    "EU proposes a €45 billion Ukraine loan.",
    "NASA's Voyager 1 believed to have reached a 'light-day' milestone.",
    "Israeli military launches a rare ground operation in Gaza beyond the "
    "Yellow Line.",
    "ALL EVENTS OF THURSDAY, 19 NOVEMBER 2026",
]


def main():
    missing = sorted({ch for s in ALL_TEXT for ch in s.upper()
                      if ch not in FONT})
    if missing:
        raise SystemExit("characters missing from font: %r" % (missing,))
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build_page()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
