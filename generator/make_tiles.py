#!/usr/bin/env python3
"""Retro CRT tile banners for the cleanyourtv launcher: a 70s-style logo per app, then a phosphor pass (bloom, fringing,
scan lines, vignette, grain), like a logo photographed off an old tube.

    python3 make_tiles.py <out dir> [name ...]    # writes banner_retro_<name>.png; Pillow, NumPy

Tiles are 708x396, twice the launcher tile, so the 4-pixel scan line period lands on 2 screen pixels.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, SS = 708, 396, 2               # output size; logos are drawn at SS x and downsampled for smooth edges
CW, CH = W * SS, H * SS
SUP = "/System/Library/Fonts/Supplemental/"
CREAM, INK = (255, 236, 196), (24, 10, 6)
RED, ORANGE, GOLD, YELLOW = (240, 50, 22), (255, 110, 20), (255, 176, 20), (255, 222, 40)
VIOLET, TEAL, BLUE = (196, 110, 255), (40, 214, 206), (60, 120, 255)


def font(file, size, index=0):
    return ImageFont.truetype(SUP + file, size, index=index)


CLARENDON = lambda s: font("SuperClarendon.ttc", s, 7)         # Black
CLARENDON_IT = lambda s: font("SuperClarendon.ttc", s, 6)      # Black Italic
ROUNDED = lambda s: font("Arial Rounded Bold.ttf", s)


def word(d, cx, cy, text, f, fill=CREAM, stroke=10, shadow=8):
    """Centered wordmark with a dark outline and a drop shadow, the way 70s idents were cut."""
    d.text((cx + shadow, cy + shadow), text, font=f, fill=INK, anchor="mm", stroke_width=stroke, stroke_fill=INK)
    d.text((cx, cy), text, font=f, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=INK)


def bulb(d, cx, cy, rx, ry, colour):
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=tuple(int(c * 0.72) for c in colour))
    d.ellipse((cx - rx * 0.62, cy - ry * 0.7, cx + rx * 0.62, cy + ry * 0.7), fill=colour)
    d.ellipse((cx - rx * 0.25, cy - ry * 0.35, cx + rx * 0.2, cy + ry * 0.1), fill=(255, 250, 225))


PINK, AVOCADO, BROWN = (226, 52, 120), (112, 132, 36), (96, 44, 20)


def fit(d, text, fn, maxw, size):
    """Largest font from fn, up to size, that keeps text (with its outline) within maxw."""
    while size > 40 and d.textlength(text, font=fn(size)) + 28 > maxw:
        size -= 4
    return fn(size)


def lerp(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def grad(d, a, b, y0=0, y1=CH, across=False):
    """Vertical gradient between rows y0..y1, or left to right across the whole canvas."""
    n = CW if across else y1 - y0
    for i in range(n):
        c = lerp(a, b, i / (n - 1))
        d.line((i, 0, i, CH) if across else (0, y0 + i, CW, y0 + i), fill=c)


def layer(img, paint, blur=0):
    """Paint on a transparent layer (alpha fills), optionally blur it, and composite it on."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    paint(ImageDraw.Draw(lay))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)) if blur else lay)


def rays(d, cx, cy, n, colour):
    for k in range(0, n, 2):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        d.polygon([(cx, cy), (cx + 3000 * math.cos(a0), cy + 3000 * math.sin(a0)),
                   (cx + 3000 * math.cos(a1), cy + 3000 * math.sin(a1))], fill=colour)


def star(cx, cy, r, inner=0.45):
    return [(cx + r * (1 if i % 2 == 0 else inner) * math.cos(math.radians(-90 + 36 * i)),
             cy + r * (1 if i % 2 == 0 else inner) * math.sin(math.radians(-90 + 36 * i))) for i in range(10)]


def star_bulb(d, cx, cy, r, colour):
    d.polygon(star(cx, cy, r), fill=tuple(int(c * 0.72) for c in colour))
    d.polygon(star(cx, cy, r * 0.66), fill=colour)
    d.ellipse((cx - r * 0.16, cy - r * 0.2, cx + r * 0.12, cy + r * 0.04), fill=(255, 250, 225))


def shadowed(d, pts, fill, width=12, off=10):
    d.polygon([(x + off, y + off) for x, y in pts], fill=INK)
    d.polygon(pts, fill=fill, outline=INK, width=width)


def word_plus(d, cx, cy, text, f, pf, fill=CREAM, pfill=YELLOW, stroke=12, gap=8):
    tw, pw = d.textlength(text, font=f), d.textlength("+", font=pf)
    x0 = cx - (tw + gap + pw) / 2
    word(d, x0 + tw / 2, cy, text, f, fill, stroke)
    word(d, x0 + tw + gap + pw / 2, cy - f.size * 0.1, "+", pf, pfill, stroke)


# --- logos --------------------------------------------------------------------------------------------------------

def netflix(img, d):
    panel = Image.new("L", img.size, 255)                         # full bleed; the launcher rounds the corners
    d.rectangle((0, 0, CW, CH), fill=(236, 64, 18))
    strips = Image.new("RGBA", img.size, (0, 0, 0, 0))
    s = ImageDraw.Draw(strips)
    for angle, off, wdt in ((-14, -150, 110), (-14, 210, 110), (62, 380, 100), (70, -240, 90)):
        layer = Image.new("RGBA", (CW * 2, CH * 2), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        cy = CH + off
        ld.rectangle((0, cy - wdt // 2, CW * 2, cy + wdt // 2), fill=(70, 14, 6, 235))
        for x in range(0, CW * 2, 64):
            for side in (-1, 1):
                hy = cy + side * (wdt // 2 - 20)
                ld.rounded_rectangle((x, hy - 11, x + 30, hy + 11), 5, fill=(236, 64, 18, 255))
        for x in range(0, CW * 2, 230):
            ld.rectangle((x, cy - wdt // 2 + 34, x + 12, cy + wdt // 2 - 34), fill=(236, 64, 18, 255))
        layer = layer.rotate(angle, resample=Image.BICUBIC, center=(CW, CH))
        strips.alpha_composite(layer.crop((CW // 2, CH // 2, CW // 2 + CW, CH // 2 + CH)))
    strips.putalpha(Image.fromarray(np.minimum(np.asarray(strips.getchannel("A")), np.asarray(panel))))
    img.paste(strips, (0, 0), strips)
    word(d, CW // 2, CH // 2 + 120, "NETFLIX", CLARENDON(220), stroke=12)


NRED, NDARK = (214, 18, 24), (110, 6, 10)


def bow(layer, k=0.6):
    """Netflix's curved banner: each column stretched about the middle, more toward the ends."""
    out = Image.new(layer.mode, layer.size, 0)
    for x in range(CW):
        t = 1 + k * ((x - CW / 2) / (CW / 2)) ** 2
        h = int(CH * t)
        col = layer.crop((x, 0, x + 1, CH)).resize((1, h), Image.BICUBIC)
        out.paste(col, (x, (CH - h) // 2))
    return out


def netflix_bow(img, d):
    """The red wordmark on black, bowed like the real one, cut with an ink outline and drop shadow."""
    grad(d, (34, 6, 6), (6, 2, 2))
    f = font("Futura.ttc", 360, 4)

    def mask(dx, stroke):
        m = Image.new("L", (CW, CH), 0)
        ImageDraw.Draw(m).text((CW // 2 + dx, CH // 2 + dx), "NETFLIX", font=f, anchor="mm", fill=255, stroke_width=stroke, stroke_fill=255)
        return bow(m)

    for x in range(40, CW, 120):                                  # a marquee of dim bulbs top and bottom
        for y in (44, CH - 44):
            bulb(d, x, y, 22, 22, (150, 40, 20))
    img.paste(INK, (0, 0), mask(20, 16))
    img.paste(CREAM, (0, 0), mask(0, 16))
    img.paste(INK, (0, 0), mask(0, 8))
    img.paste(NRED, (0, 0), mask(0, 0))


def bowed(text, f, dx=0, dy=0, stroke=0):
    m = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(m).text((CW // 2 + dx, CH // 2 + dy), text, font=f, anchor="mm", fill=255, stroke_width=stroke, stroke_fill=255)
    return bow(m)


def netflix_groovy(img, d):
    """Bowed Clarendon in Netflix red, with a stack of gold-to-red echoes behind it on a brown sunburst."""
    d.rectangle((0, 0, CW, CH), fill=(70, 22, 8))
    rays(d, CW // 2, CH // 2, 28, (112, 40, 12))
    f = fit(d, "NETFLIX", CLARENDON, 1220, 400)
    for k, colour in ((3, GOLD), (2, ORANGE), (1, (190, 36, 18))):
        img.paste(INK, (0, 0), bowed("NETFLIX", f, -14 * k, 22 * k - 50, 26))
        img.paste(colour, (0, 0), bowed("NETFLIX", f, -14 * k, 22 * k - 50, 14))
    img.paste(INK, (0, 0), bowed("NETFLIX", f, 0, -50, 12))
    img.paste(NRED, (0, 0), bowed("NETFLIX", f, 0, -50))


def netflix_stripe(img, d):
    """Bowed red Clarendon riding red, orange and gold stripes across black, like a 70s station ident."""
    d.rectangle((0, 0, CW, CH), fill=(18, 8, 6))
    for k, colour in enumerate((GOLD, ORANGE, (200, 30, 20))):
        y = CH // 2 + 110 + k * 92
        d.rectangle((0, y, CW, y + 70), fill=colour)
    f = fit(d, "NETFLIX", CLARENDON, 1220, 400)
    img.paste(INK, (0, 0), bowed("NETFLIX", f, 18, -42, 30))
    img.paste(INK, (0, 0), bowed("NETFLIX", f, 0, -60, 30))
    img.paste(CREAM, (0, 0), bowed("NETFLIX", f, 0, -60, 20))
    img.paste(INK, (0, 0), bowed("NETFLIX", f, 0, -60, 8))
    img.paste(NRED, (0, 0), bowed("NETFLIX", f, 0, -60))


def netflix_lines(img, d):
    """The 70s-style Netflix ident: an N picked out by fattening a row of thin orange lines, over a glowing cream wordmark."""
    d.rectangle((0, 0, CW, CH), fill=(6, 4, 4))
    x0, x1, y0, y1, n = 460, 956, 64, 520, 13
    nm = Image.new("L", (CW, CH), 0)
    sw = 118
    ImageDraw.Draw(nm).polygon([(x0 + 40, y0), (x0 + 40 + sw, y0), (x1 - 40, y1), (x1 - 40 - sw, y1)], fill=255)
    ImageDraw.Draw(nm).rectangle((x0 + 40, y0, x0 + 40 + sw, y1), fill=255)
    ImageDraw.Draw(nm).rectangle((x1 - 40 - sw, y0, x1 - 40, y1), fill=255)
    nm = np.asarray(nm.filter(ImageFilter.GaussianBlur(26)), float) / 255
    ys, xs = np.mgrid[0:CH, 0:CW]
    lines = np.zeros((CH, CW))
    pitch = (x1 - x0) / (n - 1)
    for i in range(n):
        x = x0 + i * pitch
        half = 2 + 9 * np.clip(nm[:, int(x)] * 1.4, 0, 1)
        inside = (ys[:, 0] >= y0) & (ys[:, 0] <= y1)
        lines = np.maximum(lines, ((np.abs(xs - x) <= half[:, None]) & inside[:, None]).astype(float))
    m = Image.fromarray((lines * 255).astype(np.uint8))
    img.paste((96, 22, 6), (0, 0), m)                             # thin lines stay dim; only the N burns bright
    img.paste((230, 70, 20), (0, 0), Image.fromarray((lines * np.clip(nm * 1.6, 0, 1) * 255).astype(np.uint8)))
    f = fit(d, "NETFLIX", lambda s: font("Futura.ttc", s, 2), 560, 200)
    t = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(t).text((CW // 2, 650), "NETFLIX", font=f, anchor="mm", fill=255, stroke_width=3, stroke_fill=255)
    img.paste((60, 54, 44), (0, 0), t.filter(ImageFilter.GaussianBlur(22)))
    img.paste((214, 200, 170), (0, 0), t)


def netflix_n(img, d):
    """The ribbon N: two dark stems with the bright diagonal folded over them, glowing on black."""
    grad(d, (30, 6, 6), (4, 2, 2))
    cx, top, bot, w = CW // 2, 90, CH - 90, 150
    l, r = cx - 210, cx + 210 - w
    glow = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(glow).polygon([(l - 40, top - 30), (r + w + 40, top - 30), (r + w + 40, bot + 30), (l - 40, bot + 30)], fill=120)
    img.paste((120, 10, 14), (0, 0), glow.filter(ImageFilter.GaussianBlur(70)))
    for x in (l, r):
        d.rectangle((x + 16, top + 16, x + w + 16, bot + 16), fill=INK)
        d.rectangle((x, top, x + w, bot), fill=NDARK, outline=INK, width=10)
    diag = [(l, top), (l + w, top), (r + w, bot), (r, bot)]
    shadowed(d, diag, NRED, width=10, off=16)
    for x in (l, r):
        d.line((x + 18, top + 20, x + 18, bot - 20), fill=(150, 12, 16), width=10)


def youtube(img, d):
    cols, rows, rx, ry, gx, gy = 9, 5, 50, 56, 108, 100
    left, top = CW // 2 - (cols - 1) * gx // 2, 96
    for r in range(rows):
        for c in range(cols):
            u, v = c - (cols - 1) / 2, r - 2                              # cell offsets from the centre
            in_button = abs(u) <= 3 and abs(v) <= 2 and not (abs(u) == 3 and abs(v) == 2)
            colour = RED if in_button else (VIOLET if (r + c) % 2 else YELLOW)
            bulb(d, left + c * gx, top + r * gy, rx, ry, colour)
    cx, cy = CW // 2 + 20, top + 2 * gy                                  # play wedge over the red bulbs
    tri = [(cx - 110, cy - 130), (cx + 140, cy), (cx - 110, cy + 130)]
    d.polygon([(x + 10, y + 10) for x, y in tri], fill=INK)
    d.polygon(tri, fill=YELLOW, outline=INK, width=12)
    word(d, CW // 2, CH - 140, "YouTube", CLARENDON(190), fill=(255, 240, 170), stroke=12)


def youtube_tv(img, d):
    """The 70s YouTube ident: a rabbit-ear TV whose screen is a striped play pill, over a two-tone Clarendon wordmark."""
    cx, box = CW // 2, (478, 150, 938, 452)
    for x1, y1 in ((612, 52), (812, 36)):
        d.line((cx, 150, x1, y1), fill=INK, width=34)
        d.line((cx, 150, x1, y1), fill=(226, 222, 210), width=20)
        d.ellipse((x1 - 10, y1 - 10, x1 + 10, y1 + 10), fill=(226, 222, 210))
    d.pieslice((cx - 50, 122, cx + 50, 178), 180, 360, fill=(226, 222, 210), outline=INK, width=6)
    for x0, x1 in ((560, 528), (856, 888)):
        d.line((x0, 450, x1, 506), fill=(226, 222, 210), width=18)
    d.rectangle((box[0] + 14, box[1] + 14, box[2] + 14, box[3] + 14), fill=INK)
    d.rectangle(box, fill=(226, 222, 210), outline=INK, width=8)
    pill = (512, 178, 904, 424)
    m = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(m).rounded_rectangle(pill, 96, fill=255)
    bands = Image.new("RGB", (CW, CH))
    bd = ImageDraw.Draw(bands)
    w = (pill[2] - pill[0]) / 4
    for i, colour in enumerate(((228, 44, 26), ORANGE, (250, 150, 24), (252, 204, 36))):
        bd.rectangle((pill[0] + i * w, 0, pill[0] + (i + 1) * w, CH), fill=colour)
        if i:
            bd.rectangle((pill[0] + i * w - 5, 0, pill[0] + i * w + 5, CH), fill=(90, 30, 10))
    img.paste(bands, (0, 0), m)
    d.rounded_rectangle(pill, 96, outline=INK, width=10)
    tri = [(650, 240), (650, 364), (758, 302)]
    d.polygon(tri, fill=(236, 232, 220), outline=INK, width=8)
    f = CLARENDON(176)
    wy, wa = d.textlength("You", font=f), d.textlength("Tube", font=f)
    x = cx - (wy + wa) / 2
    for text, fill in (("You", (226, 222, 210)), ("Tube", (240, 84, 22))):
        d.text((x + 8, 640 + 8), text, font=f, anchor="lm", fill=INK, stroke_width=10, stroke_fill=INK)
        d.text((x, 640), text, font=f, anchor="lm", fill=fill, stroke_width=10, stroke_fill=INK)
        x += d.textlength(text, font=f)


def hbomax(img, d):
    """The 1975 HBO ident: three stripes running in from the left into a geometric HBO, the O laid over the B."""
    k, ox, oy = 1.4, 30, CH // 2 - 345 * 1.4                   # drawn in the ident's own 1200x675 units
    P = lambda x, y: (ox + x * k, oy + y * k)
    box = lambda x0, y0, x1, y1: [*P(x0, y0), *P(x1, y1)]
    grey = (146, 162, 152)                                         # dimmed; the bloom lifts it
    for (y0, y1), c in zip(((237, 305), (312, 380), (387, 453)), ((150, 26, 2), (186, 128, 2), (20, 130, 218))):
        d.rectangle((0, P(0, y0)[1], P(453, 0)[0], P(0, y1)[1]), fill=c)
    d.rectangle(box(460, 237, 612, 453), fill=grey)                 # H
    for y0, y1 in ((237, 302), (374, 453)):
        d.rectangle(box(519, y0, 553, y1), fill=INK)
    d.rounded_rectangle(box(620, 237, 776, 345), 54 * k, fill=grey)   # B
    d.rounded_rectangle(box(620, 341, 786, 453), 56 * k, fill=grey)
    d.rectangle(box(620, 237, 690, 453), fill=grey)                 # square back on the B
    for y0, y1 in ((290, 330), (370, 406)):
        d.rectangle(box(680, y0, 714, y1), fill=INK)
    cx, cy = P(826, 345)
    for r, w in ((110, 0), (48, 0)):                                # O, outlined where it covers the B
        r *= k
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=grey, outline=INK, width=int(7 * k))


def disney(img, d):
    """After the 80s Disney Channel ident: rainbow slats behind a brushed-gold Mickey head."""
    slats = ((130, 60, 120), (110, 90, 170), (80, 110, 200), (70, 130, 190), (70, 140, 170), (70, 140, 130),
             (130, 150, 110), (150, 140, 60), (190, 110, 20), (180, 70, 20), (190, 60, 70), (170, 50, 110),
             (130, 50, 150), (60, 50, 160), (30, 40, 160))
    d.rectangle((0, 0, CW, CH), fill=(150, 146, 136))            # gaps kept grey: white ones bloom the tile out
    slats = [slats[i] for i in (0, 2, 3, 5, 7, 8, 9, 10, 12, 14)]  # ten, thick enough to survive the scan lines
    pitch = CH / len(slats)
    for i, c in enumerate(slats):
        c = tuple(min(255, int(v * 1.15)) for v in c)
        d.rectangle((0, i * pitch + 12, CW, (i + 1) * pitch - 12), fill=c)
    cx = CW // 2
    discs = ((cx - 234, 228, 152), (cx + 234, 228, 152), (cx, 501, 232))
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    for x, y, r in discs:
        md.ellipse((x - r, y - r, x + r, y + r), fill=255)
    shadow = Image.new("RGBA", img.size, (20, 12, 30, 0))
    shadow.putalpha(mask.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 0.6))
    img.alpha_composite(shadow, (16, 18))
    y, x = np.mgrid[0:CH, 0:CW]
    t = (0.5 + 0.5 * np.sin((x + y * 1.2) / 120.0)) ** 1.5                               # broad diagonal sheen
    gold = np.stack([lerp_ch(112, 206, t), lerp_ch(82, 164, t), lerp_ch(24, 70, t), np.full_like(t, 255)], -1)
    edge = np.asarray(mask.filter(ImageFilter.MinFilter(27)))
    gold[edge < 128, :3] = (78, 54, 18)                           # dark rim
    sheet = Image.fromarray(gold.astype(np.uint8), "RGBA")
    sheet.putalpha(mask)
    img.alpha_composite(sheet)


def disney_teal(img, d):
    """The flat teal variant of the Disney Channel ident: a white Mickey head cut out of teal slats."""
    white, teal = (234, 234, 226), (36, 122, 120)
    d.rectangle((0, 0, CW, CH), fill=white)
    n = 11
    pitch = CH / n
    for i in range(n):
        d.rectangle((0, i * pitch + pitch * 0.42, CW, (i + 1) * pitch), fill=teal)
    cx = CW // 2
    for x, y, r in ((cx - 251, 248, 158), (cx + 251, 248, 158), (cx, 488, 224)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=white)


MICKEY = lambda cx: ((cx - 251, 248, 158), (cx + 251, 248, 158), (cx, 488, 224))


def mickey_mask(discs, grow=0):
    m = Image.new("L", (CW, CH), 0)
    md = ImageDraw.Draw(m)
    for x, y, r in discs:
        md.ellipse((x - r - grow, y - r - grow, x + r + grow, y + r + grow), fill=255)
    return m


def cutout(img, discs, fill, rim=18, ink=12, off=14):
    """A Mickey head cut like the wordmarks: ink drop shadow, ink outline, a cream rim, then fill (colour or image)."""
    outer, inner = mickey_mask(discs, rim + ink), mickey_mask(discs, rim)
    img.paste(INK, (off, off), outer)
    img.paste(INK, (0, 0), outer)
    img.paste(CREAM, (0, 0), inner)
    img.paste(fill, (0, 0), mickey_mask(discs))


def disney_slat(img, d):
    """The slatted head, lit like a sunset: teal at the ears to red at the chin, on black."""
    discs = MICKEY(CW // 2)
    sl = Image.new("RGB", (CW, CH), (30, 14, 12))
    sd = ImageDraw.Draw(sl)
    stops, n = (TEAL, GOLD, ORANGE, RED), 12
    for i in range(n):
        t = i / (n - 1) * 3
        c = lerp(stops[int(min(t, 2.99))], stops[int(min(t, 2.99)) + 1], t - int(min(t, 2.99)))
        y = 70 + i * 58
        sd.rectangle((0, y, CW, y + 38), fill=c)
    cutout(img, discs, sl)
    word(d, CW - 190, 150, "+", CLARENDON(260), fill=YELLOW, stroke=12)


def disney_marquee(img, d):
    """Teal slats behind a cream head ringed with marquee bulbs."""
    d.rectangle((0, 0, CW, CH), fill=(8, 40, 44))
    pitch = CH / 11
    for i in range(11):
        d.rectangle((0, i * pitch + pitch * 0.45, CW, (i + 1) * pitch), fill=(30, 128, 124))
    discs = MICKEY(CW // 2)
    cutout(img, discs, CREAM, rim=0, ink=12)
    for x, y, r in discs:
        R = r - 44
        for k in range(int(2 * math.pi * R / 58)):
            a = 2 * math.pi * k / int(2 * math.pi * R / 58)
            bx, by = x + R * math.cos(a), y + R * math.sin(a)
            if all(math.hypot(bx - ox, by - oy) > orr - 30 for ox, oy, orr in discs if (ox, oy) != (x, y)):
                bulb(d, bx, by, 19, 19, YELLOW if k % 2 else ORANGE)
    word(d, CW // 2, 520, "Disney", fit(d, "Disney", CLARENDON_IT, 380, 130), fill=TEAL, stroke=10)


def disney_card(img, d):
    """The flat ident, cut like a 70s sign: cream head on teal slats, with the script name across it."""
    d.rectangle((0, 0, CW, CH), fill=(230, 222, 200))
    pitch = CH / 11
    for i in range(11):
        d.rectangle((0, i * pitch + pitch * 0.42, CW, (i + 1) * pitch), fill=(26, 118, 116))
    discs = MICKEY(CW // 2)
    cutout(img, discs, CREAM, rim=0, ink=12)
    word(d, CW // 2 - 20, 500, "Disney", fit(d, "Disney", CLARENDON_IT, 460, 170), fill=(26, 118, 116), stroke=10)
    word(d, CW // 2 + 250, 420, "+", CLARENDON(170), fill=YELLOW, stroke=10)


def lerp_ch(a, b, t):
    return a + (b - a) * t


def amc(img, d):
    grad(d, (34, 8, 34), (128, 26, 44))
    def beams(g):                                                # searchlights crossing over the marquee
        for bx, tx in ((170, -160), (430, 660), (986, 760), (1246, 1580)):
            g.polygon([(bx - 26, CH), (bx + 26, CH), (tx + 140, -20), (tx - 140, -20)], fill=(255, 236, 196, 80))
    layer(img, beams, 10)
    for k in range(14):
        bulb(d, 50 + k * 101, CH - 48, 26, 26, YELLOW if k % 2 else CREAM)
    word_plus(d, CW // 2, CH // 2 - 50, "AMC", CLARENDON(330), CLARENDON(280), GOLD, CREAM, 14, 16)


def tall_text(text, f, h, w, stroke):
    """Text rendered then squeezed into a w x h box, for the tall condensed Didone of the 70s AMC mark."""
    m = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(m).text((CW // 2, CH // 2), text, font=f, anchor="mm", fill=255, stroke_width=stroke, stroke_fill=255)
    return m.crop(m.getbbox()).resize((w, h), Image.LANCZOS)


def amc_diamond(img, d):
    """The 70s AMC diamond: brown lozenge, cream inset line and tip triangles, tall gold Didot letters breaking out of it."""
    d.rectangle((0, 0, CW, CH), fill=(22, 14, 8))
    cx, cy, rx, ry = CW // 2, CH // 2, 650, 366
    dia = lambda k: [(cx - rx * k, cy), (cx, cy - ry * k), (cx + rx * k, cy), (cx, cy + ry * k)]
    shadowed(d, dia(1), (150, 116, 60), width=12, off=14)
    d.polygon(dia(0.87), outline=(226, 214, 186), width=9)
    for sgn in (-1, 1):
        tip = cx + sgn * rx * 0.87
        d.polygon([(tip - sgn * 18, cy), (tip - sgn * 96, cy - 52), (tip - sgn * 96, cy + 52)], fill=(226, 214, 186))
    f = font("Didot.ttc", 300, 2)
    w, h = 430, 470
    x, y = cx - w // 2, cy - h // 2
    for dx, dy, colour, stroke in ((14, 14, INK, 16), (0, 0, INK, 16), (0, 0, (242, 186, 64), 5)):
        t = tall_text("AMC", f, h, w, stroke)
        img.paste(colour, (x + dx - (stroke - 5), y + dy - (stroke - 5)), t.resize((w + 2 * (stroke - 5), h + 2 * (stroke - 5))))


def aurora(img, d):
    grad(d, (8, 8, 36), (40, 54, 104))
    rng = np.random.default_rng(3)
    for _ in range(70):
        x, y, r = rng.integers(0, CW), rng.integers(0, 420), rng.integers(2, 5)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(220, 230, 255))
    wave = lambda x, base, amp, ph: base + amp * math.sin(x / 230 + ph)
    def bands(g):
        for base, amp, ph, colour in ((250, 60, 0.0, (80, 240, 160, 170)), (180, 50, 1.8, (200, 255, 120, 120)),
                                      (320, 40, 3.1, (196, 110, 255, 140))):
            xs = range(-40, CW + 60, 20)
            g.polygon([(x, wave(x, base, amp, ph) - 110) for x in xs] +
                      [(x, wave(x, base, amp, ph) + 30) for x in reversed(xs)], fill=colour)
    layer(img, bands, 26)
    layer(img, lambda g: [g.line((x, wave(x, 250, 60, 0) - 150, x, wave(x, 250, 60, 0) + 20),
                                 fill=(220, 255, 210, 50), width=6) for x in range(0, CW, 22)], 4)
    d.polygon([(0, 420), (200, 330), (380, 420), (560, 360), (760, 450), (980, 340), (1180, 430), (1416, 350),
               (CW, CH), (0, CH)], fill=(38, 34, 72))
    ridge = [(0, 440), (130, 380), (260, 470), (360, 430), (470, 520), (600, 470), (720, 540), (860, 460),
             (980, 510), (1110, 390), (1260, 480), (1416, 420)]
    d.polygon(ridge + [(CW, CH), (0, CH)], fill=(16, 14, 34))
    for px, py in ((130, 380), (1110, 390)):                     # snow caps
        d.polygon([(px, py), (px + 60, py + 34), (px + 26, py + 26), (px, py + 40), (px - 28, py + 24),
                   (px - 58, py + 34)], fill=CREAM)
    word(d, CW // 2, CH - 150, "Aurora", CLARENDON_IT(240), stroke=12)


def crunchyroll(img, d):
    d.rectangle((0, 0, CW, CH), fill=(244, 112, 28))
    rays(d, CW // 2, 280, 36, (255, 150, 52))
    cx, cy, r = CW // 2, 280, 180
    d.ellipse((cx - r + 10, cy - r + 10, cx + r + 10, cy + r + 10), fill=INK)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CREAM, outline=INK, width=14)
    d.ellipse((cx - 70, cy - 120, cx + 130, cy + 80), fill=(244, 112, 28), outline=INK, width=12)
    word(d, CW // 2, CH - 150, "Crunchyroll", fit(d, "Crunchyroll", CLARENDON, CW - 80, 200))


def protector(img, d):
    d.rectangle((0, 0, CW, CH), fill=AVOCADO)
    for i in range(-6, 30):                                      # 70s pinstripes
        x = i * 70
        d.polygon([(x, 0), (x + 24, 0), (x + 24 - 300, CH), (x - 300, CH)], fill=(98, 116, 30))
    def shield(cx, cy, w, h):
        side = [(cx + w / 2, cy - h / 2), (cx + w / 2, cy)]
        for i in range(1, 21):                                   # quadratic curve to the point
            t = i / 20
            p0, p1, p2 = (cx + w / 2, cy), (cx + w / 2, cy + h * 0.32), (cx, cy + h / 2)
            side.append(((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0],
                         (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]))
        return side + [(2 * cx - x, y) for x, y in reversed(side)]
    cx, cy, h = CW // 2, 300, 460
    shadowed(d, shield(cx, cy, 390, h), CREAM, 14, 12)
    d.polygon(shield(cx, cy + 4, 300, h * 0.8), fill=RED, outline=INK, width=8)
    bolt = [(0.10, -0.36), (-0.16, 0.04), (0.0, 0.04), (-0.08, 0.36), (0.18, -0.06), (0.03, -0.06)]
    shadowed(d, [(cx + x * h * 0.95, cy - 6 + y * h * 0.95) for x, y in bolt], YELLOW, 10, 8)
    word(d, CW // 2, CH - 125, "Protector", fit(d, "Protector", CLARENDON, CW - 160, 190))


def fandango(img, d):
    d.rectangle((0, 0, CW, CH), fill=PINK)
    for i in range(-6, 30):
        x = i * 110
        d.polygon([(x, 0), (x + 50, 0), (x + 50 + 300, CH), (x + 300, CH)], fill=(206, 38, 104))
    tw, th, pad = 1340, 470, 40
    m = Image.new("L", (tw + 2 * pad, th + 2 * pad), 0)          # ticket shape: rounded card, notched at the tear
    md = ImageDraw.Draw(m)
    md.rounded_rectangle((pad, pad, pad + tw, pad + th), 34, fill=255)
    tear = pad + int(tw * 0.8)
    for ny in (pad, pad + th):
        md.ellipse((tear - 34, ny - 34, tear + 34, ny + 34), fill=0)
    for nx in (pad, pad + tw):
        md.ellipse((nx - 40, pad + th / 2 - 40, nx + 40, pad + th / 2 + 40), fill=0)
    t = Image.new("RGBA", m.size, (0, 0, 0, 0))
    t.paste(INK, (14, 14), m)
    t.paste(INK, (0, 0), m.filter(ImageFilter.MaxFilter(25)))
    t.paste(GOLD, (0, 0), m)
    td = ImageDraw.Draw(t)
    for y in range(pad + 50, pad + th - 40, 36):
        td.rectangle((tear - 5, y, tear + 5, y + 18), fill=INK)
    sx, sy = (tear + pad + tw) / 2, pad + th / 2
    td.polygon([(x + 8, y + 8) for x, y in star(sx, sy, 100)], fill=INK)
    td.polygon(star(sx, sy, 100), fill=RED, outline=INK, width=10)
    mx = (pad + tear) / 2
    word(td, mx, sy, "FANDANGO", fit(td, "FANDANGO", CLARENDON, tear - pad - 70, 200), fill=CREAM, stroke=11, shadow=7)
    t = t.rotate(5, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(t, ((CW - t.width) // 2, (CH - t.height) // 2))


def media(img, d):
    grad(d, (246, 176, 44), (214, 104, 22))
    d.rounded_rectangle((152, 72, 1288, 744), 50, fill=INK)
    d.rounded_rectangle((140, 60, 1276, 732), 50, fill=(62, 40, 34), outline=INK, width=14)
    for sx, sy in ((186, 106), (1230, 106), (186, 686), (1230, 686)):
        d.ellipse((sx - 16, sy - 16, sx + 16, sy + 16), fill=(160, 140, 120), outline=INK, width=4)
    d.rounded_rectangle((226, 100, 1190, 566), 26, fill=CREAM, outline=INK, width=8)
    for k, colour in enumerate((RED, ORANGE, GOLD)):
        d.rectangle((230, 318 + k * 22, 1186, 336 + k * 22), fill=colour)
    d.rounded_rectangle((400, 410, 1016, 540), 64, fill=(34, 22, 20), outline=INK, width=10)
    for rx, tape in ((560, 60), (856, 42)):
        d.ellipse((rx - tape, 475 - tape, rx + tape, 475 + tape), fill=(110, 58, 32))
        d.ellipse((rx - 30, 445, rx + 30, 505), fill=CREAM, outline=INK, width=6)
        for k in range(6):
            a = k * math.pi / 3
            d.ellipse((rx + 18 * math.cos(a) - 5, 475 + 18 * math.sin(a) - 5, rx + 18 * math.cos(a) + 5,
                       475 + 18 * math.sin(a) + 5), fill=INK)
    d.polygon([(380, 732), (440, 606), (976, 606), (1036, 732)], fill=(84, 56, 46), outline=INK, width=10)
    for hx in (520, 896):
        d.ellipse((hx - 20, 650, hx + 20, 690), fill=INK)
    word(d, CW // 2, 208, "Media", fit(d, "Media", CLARENDON, 880, 210), fill=RED, stroke=10, shadow=7)


def paramount(img, d):
    """The 70s Paramount Television ident: navy disc, a ring of stars, the script name over a pale peak."""
    sky, navy, ice, white = (0, 128, 230), (0, 36, 92), (90, 190, 255), (252, 250, 240)
    d.rectangle((0, 0, CW, CH), fill=sky)
    cx, cy, r, base = CW // 2, 440, 360, 680
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=navy)
    d.rectangle((0, base, CW, CH), fill=sky)                     # the disc stops where the mountain stands
    hw = math.sqrt(r * r - (base - cy) ** 2)
    d.polygon([(cx - hw, base), (cx - 120, 500), (cx - 40, 400), (cx, 362), (cx + 36, 392), (cx + 130, 500), (cx + hw, base)], fill=ice)
    for pts in ([(cx - 20, 400), (cx - 80, 470), (cx - 66, 486), (cx - 150, 590), (cx - 60, 520), (cx - 74, 500), (cx - 30, 440)],
                [(cx + 24, 404), (cx + 100, 470), (cx + 84, 490), (cx + 200, 620), (cx + 90, 540), (cx + 104, 520), (cx + 40, 450)],
                [(cx - 170, 570), (cx - 250, 670), (cx - 190, 650), (cx - 200, 630)],
                [(cx + 230, 610), (cx + 280, 676), (cx + 236, 676)]):      # jagged ridge shadows
        d.polygon(pts, fill=navy)
    for k in range(24):
        a = math.radians(146 + k * 248 / 23)
        d.polygon(star(cx + 412 * math.cos(a), cy + 412 * math.sin(a), 26), fill=white)
    snell = lambda s: font("SnellRoundhand.ttc", s, 2)
    for text, y, w in (("Paramount", 228, 720), ("Television", 326, 640)):
        f = fit(d, text, snell, w, 200)
        d.text((cx + 8, y + 8), text, font=f, fill=(0, 30, 70), anchor="mm", stroke_width=7, stroke_fill=(0, 18, 50))
        d.text((cx, y), text, font=f, fill=white, anchor="mm", stroke_width=3, stroke_fill=white)  # fattened to survive the tube
    z = 1.15                                                     # zoom in: the ring is taller than it is wide
    img.paste(img.crop((cx - CW / z / 2, 0, cx + CW / z / 2, CH / z)).resize((CW, CH), Image.Resampling.LANCZOS))


def jellyfin(img, d):
    grad(d, (120, 40, 170), (36, 100, 210), across=True)
    cy, R = 270, 205
    tape = (78, 40, 26)
    for cx, pack in ((420, 160), (996, 100)):
        d.line((cx + (-1 if cx < 708 else 1) * pack * 0.3, cy + pack, 708 + (-1 if cx < 708 else 1) * 120, 560),
               fill=tape, width=18)
        d.ellipse((cx - R + 12, cy - R + 12, cx + R + 12, cy + R + 12), fill=INK)
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(236, 226, 212), outline=INK, width=12)
        for k in range(3):
            a = 30 + k * 120
            d.pieslice((cx - R + 26, cy - R + 26, cx + R - 26, cy + R - 26), a, a + 64, fill=(46, 22, 74))
        d.ellipse((cx - pack, cy - pack, cx + pack, cy + pack), fill=tape, outline=INK, width=6)
        d.ellipse((cx - 52, cy - 52, cx + 52, cy + 52), fill=(236, 226, 212), outline=INK, width=8)
        d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=INK)
    d.line((588, 560, 828, 560), fill=tape, width=18)
    for gx in (588, 828):
        d.ellipse((gx - 24, 536, gx + 24, 584), fill=(236, 226, 212), outline=INK, width=6)
    d.rectangle((676, 540, 740, 590), fill=GOLD, outline=INK, width=6)
    word(d, CW // 2, CH - 124, "Jellyfin", fit(d, "Jellyfin", CLARENDON, 1100, 180), fill=CREAM)


def play(img, d):
    grad(d, (110, 52, 24), (52, 22, 10))
    tl, bl, r = (110, 120), (110, 672), (600, 396)
    p = (290, 396)
    t = (tl[0] + (r[0] - tl[0]) * 0.58, tl[1] + (r[1] - tl[1]) * 0.58)
    b = (bl[0] + (r[0] - bl[0]) * 0.58, bl[1] + (r[1] - bl[1]) * 0.58)
    d.polygon([(x + 14, y + 14) for x, y in (tl, r, bl)], fill=INK)
    for pts, colour in (([tl, p, bl], TEAL), ([tl, t, p], GOLD), ([bl, p, b], RED), ([t, r, b, p], ORANGE)):
        d.polygon(pts, fill=colour, outline=INK, width=10)
    d.polygon([tl, r, bl], outline=INK, width=16)
    word(d, 1010, 300, "Play", fit(d, "Play", CLARENDON, 720, 280))
    word(d, 1010, 560, "Store", fit(d, "Store", ROUNDED, 640, 190), fill=YELLOW)


def prime(img, d):
    grad(d, (44, 116, 196), (14, 40, 104))
    for k, colour in enumerate((GOLD, ORANGE, RED)):
        d.rectangle((0, CH - 96 + k * 26, CW, CH - 80 + k * 26), fill=colour)
    word(d, CW // 2, 270, "prime video", fit(d, "prime video", ROUNDED, CW - 90, 240))
    cx, cy, rx, ry = CW // 2, 400, 520, 170
    pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(math.radians(165), math.radians(18), 50)]
    (ex, ey), (qx, qy) = pts[-1], pts[-3]
    n = math.hypot(ex - qx, ey - qy)
    ux, uy = (ex - qx) / n, (ey - qy) / n
    head = [(ex + ux * 70, ey + uy * 70), (ex - uy * 56, ey + ux * 56), (ex + uy * 56, ey - ux * 56)]
    for off, colour, wd in ((10, INK, 60), (0, INK, 60), (0, GOLD, 36)):
        d.line([(x + off, y + off) for x, y in pts], fill=colour, width=wd, joint="curve")
    shadowed(d, head, GOLD, 10, 10)


def prime_mask(k=0.8, ox=117, oy=160):
    """The blocky stencil PRIME / VIDEO, traced from the reference in its 1478x541 units. Returns the mask and the point mapper."""
    P = lambda pts: [(ox + x * k, oy + y * k) for x, y in pts]
    R = lambda x0, y0, x1, y1: P([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    C = lambda x, y, r: (ox + (x - r) * k, oy + (y - r) * k, ox + (x + r) * k, oy + (y + r) * k)
    m = Image.new("L", (CW, CH), 0)
    md = ImageDraw.Draw(m)
    for box in ((0, 0, 128, 498), (0, 0, 205, 243), (338, 0, 466, 243), (466, 0, 540, 165), (632, 0, 761, 243),
                (771, 0, 1148, 243), (1158, 0, 1467, 243), (583, 254, 773, 498), (905, 254, 1215, 498)):
        md.polygon(R(*box), fill=255)
    for circ in ((205, 121, 121), (540, 82, 82), (773, 376, 122), (1345, 376, 122)):
        md.ellipse(C(*circ), fill=255)
    for poly in ([(466, 150), (578, 156), (622, 243), (492, 243), (466, 190)],
                 [(138, 254), (264, 254), (264, 398), (316, 254), (438, 254), (351, 498), (138, 498)],
                 [(448, 254), (573, 254), (573, 348), (415, 348)], [(411, 358), (573, 358), (573, 498), (361, 498)]):
        md.polygon(P(poly), fill=255)
    for cut in ([(944, 0), (975, 0), (959, 72)], [(899, 170), (899, 243), (917, 243)], [(1020, 170), (1020, 243), (1002, 243)],
                R(1287, 83, 1467, 96), R(1287, 148, 1467, 161), R(1455, 96, 1467, 148),
                R(1034, 338, 1215, 351), R(1034, 403, 1215, 416), R(1203, 351, 1215, 403)):
        md.polygon(cut if isinstance(cut[0][0], float) else P(cut), fill=0)
    md.polygon(R(205, 0, 338, 121), fill=0)                      # keep the P bowl clear of the R
    md.ellipse(C(205, 121, 121), fill=255)
    return m, P


def prime_stripes(d, P, colours=(GOLD, ORANGE, (214, 48, 22))):
    for i, colour in enumerate(colours):                           # the arrow, as three 70s stripes
        y0 = 528 + i * 34
        d.polygon(P([(0, y0 + 12), (1454, y0 + 12), (1478, y0 + 26), (1454, y0 + 40), (0, y0 + 40)]), fill=INK)
        d.polygon(P([(0, y0), (1454, y0), (1478, y0 + 13), (1454, y0 + 26), (0, y0 + 26)]), fill=colour, outline=INK, width=4)


def prime_blocks(img, d):
    """Sky blue blocks on brown, the arrow as three stripes."""
    d.rectangle((0, 0, CW, CH), fill=(40, 18, 10))
    m, P = prime_mask()
    img.paste(INK, (14, 14), m.filter(ImageFilter.MaxFilter(15)))
    img.paste(INK, (0, 0), m.filter(ImageFilter.MaxFilter(15)))
    img.paste((92, 178, 226), (0, 0), m)
    prime_stripes(d, P)


def prime_sunset(img, d):
    """The blocks filled with sunset bands, gold at the top to red at the base, cream-rimmed on a brown sunburst."""
    d.rectangle((0, 0, CW, CH), fill=(56, 24, 10))
    rays(d, CW // 2, CH + 200, 36, (76, 34, 12))
    m, P = prime_mask(0.8, 117, 130)
    bands = Image.new("RGB", (CW, CH))
    bd = ImageDraw.Draw(bands)
    cols = (YELLOW, GOLD, ORANGE, (236, 74, 20), (200, 36, 22), (150, 24, 30))
    top, bot = 130, 130 + 498 * 0.8
    for i, c in enumerate(cols):
        bd.rectangle((0, top + (bot - top) * i / len(cols), CW, top + (bot - top) * (i + 1) / len(cols)), fill=c)
    grow = lambda n: m.filter(ImageFilter.MaxFilter(n))
    img.paste(INK, (16, 16), grow(25))
    img.paste(INK, (0, 0), grow(25))
    img.paste(CREAM, (0, 0), grow(13))
    img.paste(INK, (0, 0), grow(5))
    img.paste(bands, (0, 0), m)
    prime_stripes(d, lambda pts: [(x, y - 30) for x, y in P(pts)], ((70, 150, 210), (40, 110, 180), (24, 70, 140)))


def prime_echo(img, d):
    """Sky blue blocks with a groovy stack of gold, orange and red echoes stepping out behind them."""
    d.rectangle((0, 0, CW, CH), fill=(30, 14, 8))
    m, P = prime_mask(0.76, 114, 175)                            # mark plus its 64px echo stack, centred
    out = m.filter(ImageFilter.MaxFilter(11))
    for n, colour in ((4, (190, 36, 18)), (3, ORANGE), (2, GOLD)):
        off = (n * 16, n * 16)
        img.paste(INK, (off[0] + 6, off[1] + 6), out)
        img.paste(colour, off, m)
    img.paste(INK, (16, 16), out)
    img.paste(CREAM, (16, 16), m)
    img.paste(INK, (0, 0), out)
    img.paste((92, 178, 226), (0, 0), m)


def sources(img, d):
    """A 70s console's row of chunky input push-buttons, one pressed in and lit, centred on the tile."""
    oy = 101
    grad(d, (44, 22, 12), (16, 8, 6))
    panel = (150, 110 + oy, 1266, 440 + oy)
    d.rounded_rectangle((panel[0] + 14, panel[1] + 14, panel[2] + 14, panel[3] + 14), 30, fill=INK)
    d.rounded_rectangle(panel, 30, fill=(86, 60, 38), outline=INK, width=10)
    d.rounded_rectangle((panel[0] + 22, panel[1] + 22, panel[2] - 22, panel[3] - 22), 18, outline=(200, 170, 120), width=5)
    labels, w, gap, lit = ("1", "2", "3", "4", "TV"), 176, 26, 2
    x0 = (CW - (len(labels) * w + (len(labels) - 1) * gap)) // 2
    for i, label in enumerate(labels):
        x, down = x0 + i * (w + gap), 18 if i == lit else 0
        face, lip = ((255, 120, 30), (180, 60, 16)) if i == lit else ((226, 214, 186), (150, 128, 96))
        if i == lit:
            glow = Image.new("L", (CW, CH), 0)
            ImageDraw.Draw(glow).rounded_rectangle((x - 30, 130 + oy, x + w + 30, 430 + oy), 30, fill=200)
            img.paste((200, 80, 10), (0, 0), glow.filter(ImageFilter.GaussianBlur(30)))
        d.rounded_rectangle((x, 160 + oy + down, x + w, 400 + oy), 22, fill=lip, outline=INK, width=8)
        d.rounded_rectangle((x, 160 + oy + down, x + w, 370 + oy), 22, fill=face, outline=INK, width=8)
        d.text((x + w // 2, 265 + oy + down), label, font=CLARENDON(96 if len(label) == 1 else 76), anchor="mm", fill=INK)


def wood(box, seed=7):
    """Walnut grain filling box: wavy horizontal streaks, as an RGB image the size of box."""
    x0, y0, x1, y1 = box
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0].astype(float)
    warp = 14 * np.sin(xx / 160 + rng.uniform(0, 6)) + 6 * np.sin(xx / 47)
    g = 0.5 + 0.5 * np.sin((yy + warp) / 9 + 3 * np.sin((yy + warp) / 61))
    g = 0.75 * g + 0.25 * rng.random(g.shape[0])[:, None]
    lo, hi = np.array((70, 38, 20)), np.array((128, 76, 40))
    return Image.fromarray((lo + g[..., None] * (hi - lo)).astype(np.uint8))


def sources_wood(img, d):
    """Walnut console with a chrome strip of cream push-keys, key 3 latched down and lit amber, pilot lamp above."""
    grad(d, (30, 16, 10), (12, 6, 4))
    panel = (110, 70, 1306, 470)
    d.rounded_rectangle((panel[0] + 16, panel[1] + 16, panel[2] + 16, panel[3] + 16), 34, fill=INK)
    m = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(m).rounded_rectangle(panel, 34, fill=255)
    img.paste(wood(panel), panel[:2], m.crop(panel))
    d.rounded_rectangle(panel, 34, outline=INK, width=10)
    strip = (176, 150, 1240, 430)
    d.rounded_rectangle(strip, 20, fill=(150, 146, 136), outline=INK, width=8)
    d.rounded_rectangle((strip[0] + 14, strip[1] + 14, strip[2] - 14, strip[3] - 14), 12, fill=(40, 30, 24))
    labels, w, gap, lit = ("1", "2", "3", "4", "TV"), 170, 30, 2
    x0 = (CW - (len(labels) * w + (len(labels) - 1) * gap)) // 2
    for i, label in enumerate(labels):
        x, down = x0 + i * (w + gap), 22 if i == lit else 0
        face, lip = ((255, 150, 40), (190, 74, 18)) if i == lit else ((214, 184, 136), (140, 110, 74))
        if i == lit:
            glow = Image.new("L", (CW, CH), 0)
            ImageDraw.Draw(glow).rounded_rectangle((x - 20, 170, x + w + 20, 420), 30, fill=220)
            img.paste((230, 100, 14), (0, 0), glow.filter(ImageFilter.GaussianBlur(34)))
            bulb(d, x + w // 2, 112, 22, 22, (255, 120, 24))
        else:
            d.ellipse((x + w // 2 - 14, 98, x + w // 2 + 14, 126), fill=(60, 26, 12), outline=INK, width=5)
        d.rounded_rectangle((x, 182 + down, x + w, 404), 20, fill=lip, outline=INK, width=8)
        d.rounded_rectangle((x, 182 + down, x + w, 374), 20, fill=face, outline=INK, width=8)
        d.text((x + w // 2, 280 + down), label, font=CLARENDON(96 if len(label) == 1 else 76), anchor="mm", fill=INK)
    word(d, CW // 2, 625, "Sources", fit(d, "Sources", CLARENDON_IT, 840, 190), fill=GOLD, stroke=12)


def sources_dial(img, d):
    """A 70s TV's rotary input selector: ridged knob pointing at 3, the lit position glowing, wordmark beside it."""
    grad(d, (44, 22, 12), (16, 8, 6))
    cx, cy = 400, 430
    for i, label in enumerate(("1", "2", "3", "4", "TV")):
        a = math.radians(200 + i * 35)
        x, y = cx + 286 * math.cos(a), cy + 286 * math.sin(a)
        if i == 2:
            glow = Image.new("L", (CW, CH), 0)
            ImageDraw.Draw(glow).ellipse((x - 70, y - 70, x + 70, y + 70), fill=150)
            img.paste((230, 100, 14), (0, 0), glow.filter(ImageFilter.GaussianBlur(28)))
        d.text((x, y), label, font=CLARENDON(84 if len(label) == 1 else 66), anchor="mm",
               fill=YELLOW if i == 2 else (200, 172, 124), stroke_width=8, stroke_fill=INK)
    d.ellipse((cx - 200 + 16, cy - 200 + 16, cx + 200 + 16, cy + 200 + 16), fill=INK)
    d.ellipse((cx - 200, cy - 200, cx + 200, cy + 200), fill=(200, 176, 130), outline=INK, width=10)
    d.ellipse((cx - 166, cy - 166, cx + 166, cy + 166), fill=(58, 36, 24), outline=INK, width=8)
    for k in range(36):
        a = math.radians(k * 10)
        d.line((cx + 128 * math.cos(a), cy + 128 * math.sin(a), cx + 160 * math.cos(a), cy + 160 * math.sin(a)),
               fill=(96, 64, 42), width=8)
    d.ellipse((cx - 118, cy - 118, cx + 118, cy + 118), fill=(80, 52, 34), outline=INK, width=6)
    d.rounded_rectangle((cx - 22, cy - 160, cx + 22, cy - 34), 18, fill=CREAM, outline=INK, width=6)
    d.rounded_rectangle((cx - 12, cy - 154, cx + 12, cy - 116), 10, fill=ORANGE)
    word(d, 1060, 360, "Sources", fit(d, "Sources", CLARENDON, 600, 170), stroke=12)
    word(d, 1060, 540, "INPUT", fit(d, "INPUT", CLARENDON, 360, 110), fill=GOLD, stroke=10)


def settings(img, d):
    d.rectangle((0, 0, CW, CH), fill=(26, 116, 118))
    rays(d, CW // 2, 280, 40, (34, 130, 130))
    cx, cy, r, depth, teeth = CW // 2, 280, 176, 44, 10
    pts = [(cx + (r if i % 4 in (1, 2) else r - depth) * math.cos(2 * math.pi * (i + 0.5) / (teeth * 4)),
            cy + (r if i % 4 in (1, 2) else r - depth) * math.sin(2 * math.pi * (i + 0.5) / (teeth * 4)))
           for i in range(teeth * 4)]
    shadowed(d, pts, ORANGE, 14, 12)
    d.ellipse((cx - 104, cy - 104, cx + 104, cy + 104), fill=GOLD, outline=INK, width=10)
    d.ellipse((cx - 50, cy - 50, cx + 50, cy + 50), fill=(26, 116, 118), outline=INK, width=10)
    for k in range(24):
        a = 2 * math.pi * k / 24
        bulb(d, cx + 236 * math.cos(a), cy + 236 * math.sin(a), 18, 18, CREAM if k % 2 else YELLOW)
    word(d, CW // 2, CH - 128, "Settings", fit(d, "Settings", CLARENDON, 1160, 180))


def peacock(img, d):
    """The 1956 NBC bird: translucent leaf feathers fanned behind a white peacock, a diamond past each tip."""
    cx, cy = CW // 2, 640                                       # fan pivot, behind the bird's body
    feathers = ((80, 100, 170), (225, 75, 45), (245, 175, 115), (60, 95, 205), (120, 75, 175), (215, 75, 130),
                (230, 60, 60), (160, 40, 70), (235, 115, 45), (248, 195, 75), (60, 155, 195), (85, 125, 215),
                (225, 85, 50))
    fan = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fan)
    for i, c in enumerate(feathers):
        a = math.radians(176 + i * 188 / (len(feathers) - 1))
        L = 470 + 130 * abs(math.cos(a))
        ux, uy, px, py = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        side = [(cx + ux * L * t + px * 72 * math.sin(math.pi * t) ** 0.8,
                 cy + uy * L * t + py * 72 * math.sin(math.pi * t) ** 0.8) for t in (k / 24 for k in range(25))]
        side += [(cx + ux * L * t - px * 72 * math.sin(math.pi * t) ** 0.8,
                  cy + uy * L * t - py * 72 * math.sin(math.pi * t) ** 0.8) for t in (k / 24 for k in range(24, -1, -1))]
        leaf = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(leaf).polygon(side, fill=c + (215,))
        fan.alpha_composite(leaf)
        tx, ty, r = cx + ux * (L + 62), cy + uy * (L + 62), 26     # the diamond past the tip
        fd.polygon([(tx + ux * r * 1.3, ty + uy * r * 1.3), (tx + px * r, ty + py * r),
                    (tx - ux * r * 1.3, ty - uy * r * 1.3), (tx - px * r, ty - py * r)], fill=feathers[-1 - i])
    img.alpha_composite(fan)
    d = ImageDraw.Draw(img)
    bird = [(-5, -345), (-48, -320), (-14, -303), (-20, -250), (-30, -170), (-50, -90), (-76, -20), (-78, 30),
            (-55, 70), (-10, 88), (60, 84), (128, 120), (100, 60), (58, 0), (12, -90), (2, -160), (6, -240),
            (22, -310), (12, -342)]
    d.polygon([(cx + x, cy + y) for x, y in bird], fill=(250, 248, 240))
    d.polygon([(cx - 8, cy - 330), (cx + 10, cy - 322), (cx + 8, cy - 300), (cx - 6, cy - 306)], fill=(230, 70, 50))
    for x0, x1 in ((-22, -34), (12, 14)):                       # legs
        d.line([(cx + x0, cy + 84), (cx + x1, cy + 135)], fill=(250, 248, 240), width=9)


LOGOS = {"netflix": netflix, "netflix_bow": netflix_bow, "netflix_n": netflix_n, "netflix_lines": netflix_lines, "netflix_groovy": netflix_groovy, "netflix_stripe": netflix_stripe, "youtube": youtube, "youtube_tv": youtube_tv, "hbomax": hbomax, "disney": disney, "disney_teal": disney_teal, "disney_slat": disney_slat, "disney_marquee": disney_marquee, "disney_card": disney_card,
         "amc": amc, "amc_diamond": amc_diamond, "aurora": aurora, "crunchyroll": crunchyroll, "protector": protector, "fandango": fandango, "media": media, "paramount": paramount, "jellyfin": jellyfin, "play": play, "prime": prime, "prime_blocks": prime_blocks, "prime_sunset": prime_sunset, "prime_echo": prime_echo, "settings": settings, "sources": sources, "sources_wood": sources_wood, "sources_dial": sources_dial, "peacock": peacock}


# --- the tube -----------------------------------------------------------------------------------------------------

def crt(img):
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(1.2)), float) / 255
    a[..., 0] = np.roll(a[..., 0], 2, axis=1)                    # convergence error: red right, blue left
    a[..., 2] = np.roll(a[..., 2], -2, axis=1)
    glow = lambda r: np.asarray(img.filter(ImageFilter.GaussianBlur(r)), float) / 255
    a = 1 - (1 - a) * (1 - 0.6 * glow(8)) * (1 - 0.55 * glow(26))   # screen-blend bloom
    y, x = np.mgrid[0:H, 0:W]
    a *= (0.74 + 0.26 * np.cos(2 * np.pi * y / 4))[..., None]       # scan lines, 2 screen pixels
    a *= (0.93 + 0.07 * np.cos(2 * np.pi * x / 3))[..., None]       # aperture grille
    u, v = x / W * 2 - 1, y / H * 2 - 1
    a *= (1 - 0.38 * (u ** 2 * 0.6 + v ** 2) ** 1.4)[..., None]     # vignette
    a += np.random.default_rng(1983).normal(0, 0.012, a.shape)
    return Image.fromarray((a.clip(0, 1) * 255).astype(np.uint8))


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[2:] or LOGOS:
        img = Image.new("RGBA", (CW, CH), (6, 4, 4, 255))
        LOGOS[name](img, ImageDraw.Draw(img))
        crt(img.convert("RGB").resize((W, H), Image.Resampling.LANCZOS)).save(out / f"banner_retro_{name}.png")


if __name__ == "__main__":
    main()
