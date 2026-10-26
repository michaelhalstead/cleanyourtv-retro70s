"""70s wallpaper directions and home-screen mocks: python mock.py <tiles dir> <out dir>"""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
rng = np.random.default_rng(1975)
yy, xx = np.mgrid[0:H, 0:W].astype(float)


def finish(a):
    a = a * (0.94 + 0.06 * np.cos(2 * np.pi * yy / 4))[..., None]         # faint scan lines
    u, v = xx / W * 2 - 1, yy / H * 2 - 1
    a = a * (1 - 0.35 * (u ** 2 * 0.5 + v ** 2 * 0.8))[..., None]          # soft vignette, no frame
    a = a + rng.normal(0, 2.2, a.shape)                                    # film grain
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def vgrad(top, bot):
    t = (yy / H)[..., None]
    return np.array(top, float) * (1 - t) + np.array(bot, float) * t


def stripes():
    a = vgrad((18, 9, 6), (44, 20, 10))
    for i, c in enumerate(((150, 104, 30), (150, 70, 20), (130, 40, 18), (86, 26, 16))):
        y0 = 560 + i * 34
        band = (yy >= y0) & (yy < y0 + 24)
        a[band] = np.array(c, float) * 0.62
    return finish(a)


def wood():
    """Walnut veneer panels: long vertical streaks, a slow sideways wander, darker seams every 240px."""
    n = rng.normal(0, 1, (H // 4, W))
    streak = np.asarray(Image.fromarray(((n + 3) * 42).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur((1.6, 40))), float)
    streak = np.asarray(Image.fromarray(streak.astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
    shift = (np.sin(yy / 170 + xx / 400) * 9).astype(int)
    streak = np.take_along_axis(streak, (xx.astype(int) + shift) % W, axis=1)
    g = 0.55 + 0.75 * (streak - streak.mean())
    g = g * (0.9 + 0.1 * np.sin(xx / 61 + np.sin(yy / 300)))
    for x in range(0, W, 240):
        g[:, x:x + 3] *= 0.4
    a = np.stack([g * 78, g * 42, g * 22], -1)
    return finish(a)


def sunburst():
    a = vgrad((26, 12, 8), (52, 22, 10))
    ang = np.arctan2(yy - (H + 260), xx - W / 2)
    ray = (np.floor(ang / (math.pi / 22)) % 2 == 0)
    a[ray] *= 1.28
    glow = np.exp(-(((xx - W / 2) / 900) ** 2 + ((yy - H) / 420) ** 2))[..., None]
    a = a + glow * np.array((70, 30, 6))
    return finish(a)


def home(wall, tiles, out):
    img = wall.convert("RGB").copy()
    d = ImageDraw.Draw(img)
    av = "/System/Library/Fonts/Avenir Next.ttc"
    d.text((112, 190), "9:12", font=ImageFont.truetype(av, 104, index=5), fill=(240, 232, 214), anchor="ls")
    d.text((312, 178), "PM", font=ImageFont.truetype(av, 30, index=5), fill=(240, 232, 214), anchor="ls")
    d.line((392, 146, 392, 196), fill=(150, 140, 120), width=2)
    d.text((428, 186), "SUNDAY 25 OCTOBER", font=ImageFont.truetype(av, 30, index=5), fill=(200, 190, 170), anchor="ls")
    for x in (1660, 1764):
        d.ellipse((x - 41, 118, x + 41, 200), outline=(150, 140, 120), width=2, fill=(30, 22, 18))
    d.rounded_rectangle((1382, 118, 1598, 200), 41, outline=(150, 140, 120), width=2, fill=(30, 22, 18))
    d.text((1490, 160), "Inputs", font=ImageFont.truetype(av, 30, index=5), fill=(230, 220, 200), anchor="mm")
    mask = Image.new("L", (354, 198), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 353, 197), 24, fill=255)
    for row, y in ((0, 722), (1, 1036)):
        for i, x in enumerate((162, 576, 990, 1404)):
            t = Image.open(tiles / f"banner_retro_{tiles_order[row][i]}.png").convert("RGB").resize((354, 198), Image.LANCZOS)
            sh = Image.new("L", (W, H), 0)
            ImageDraw.Draw(sh).rounded_rectangle((x + 6, y + 12, x + 360, y + 210), 24, fill=150)
            img.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
            img.paste(t, (x, y), mask)
    d.rounded_rectangle((162 - 10, 722 - 10, 162 + 364, 722 + 208), 32, outline=(250, 244, 230), width=5)   # rim focus on Netflix
    img.save(out)


tiles_order = (("netflix_lines", "youtube_tv", "hbomax", "disney_slat"), ("amc_diamond", "aurora", "crunchyroll", "protector"))
if __name__ == "__main__":
    tiles, out = Path(sys.argv[1]), Path(sys.argv[2])
    for name, fn in (("stripes", stripes), ("wood", wood), ("sunburst", sunburst)):
        w = fn()
        w.save(out / f"wallpaper-{name}.jpg", quality=92)
        home(w, tiles, out / f"home-{name}.png")
