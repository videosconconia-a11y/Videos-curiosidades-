# "Be Honest… You Did All 5 in GTA 6" — POV PHONE UI identity (original UI design, not Rockstar's).
# Palette: tick green #34C759, iOS blue #0A84FF, light #F2F2F7, dark #1C1C1E. Font: Montserrat (UI).
# Official Rockstar images as the "camera" behind a phone interface: lock screen + notifications, story-style
# progress bar, a status-bar clock that runs 12:00 -> 12:05, a checklist card that ticks each item, chat bubbles.
# Usage: python3 render.py still <t>... | python3 render.py video <worker> <nworkers>
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS, ITEMS

W, H, FPS = 1080, 1920, 30
FD = os.path.join(HERE, "fonts")
@lru_cache(maxsize=64)
def MS(s, w=700):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
GREEN = (52, 199, 89); BLUE = (10, 132, 255); LIGHT = (242, 242, 247); DARK = (28, 28, 30); WHITE = (255, 255, 255)
RED = (255, 59, 48); PINK = (255, 45, 140); ORANGE = (255, 149, 0)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word):
    for w in SEGT[seg]["words"]:
        if clean(w["w"]) == word: return w["a"]
    raise KeyError((seg, word))
def build_shots():
    out = []; segs = TM["segments"]
    for i, (sd, st_) in enumerate(zip(SEGMENTS, segs)):
        s0 = 0.0 if i == 0 else st_["a"] - 0.12
        s1 = segs[i + 1]["a"] - 0.12 if i + 1 < len(segs) else TOTAL
        starts = [(s0 if c is None else word_time(sd["id"], c) - 0.08, n) for n, c in sd["shots"]]
        for j, (a, n) in enumerate(starts):
            out.append((a, starts[j + 1][0] if j + 1 < len(starts) else s1, n, sd["id"]))
    return out
SHOTS = build_shots()
def st(n): return [s[0] for s in SHOTS if s[2] == n][0]
ITEM_SEG = ["i1", "i2", "i3", "i4", "i5"]
TICK = [SEGT[s]["words"][-1]["a"] + 0.1 for s in ITEM_SEG]          # tick lands on the item's last word
ITEM_START = [SEGT[s]["a"] - 0.12 for s in ITEM_SEG]
LOOP = TOTAL - 0.75                                                 # back to the lock screen for a seamless loop

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))
def text_c(d, cx, y, s, f, fill, **kw): d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill, **kw)

@lru_cache(maxsize=6)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + ".*jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2400 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im
def photo(key, p, cx=.5, cy=.5, z0=1.0, z1=1.12, dark=1.0):
    im = load(key); z = z0 + (z1 - z0) * (ease(p) * .6 + p * .4)
    ch = im.height / z; cw = ch * W / H
    if cw > im.width: cw = im.width / z; ch = cw * H / W
    x = min(max(cx * im.width, cw / 2), im.width - cw / 2); y = min(max(cy * im.height, ch / 2), im.height - ch / 2)
    v = im.resize((W, H), Image.BILINEAR, box=(x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2))
    if dark != 1.0: v = to_img(np.asarray(v, np.float32) * dark)
    return v.convert("RGBA")
@lru_cache(maxsize=4)
def blurred(key, cx=.5, r=38, dark=.62):
    return photo(key, 0, cx, z0=1.05, z1=1.05, dark=dark).filter(ImageFilter.GaussianBlur(r))

# shading for legibility: top + bottom gradients
_g = np.linspace(0, 1, H)[:, None]
_al = np.clip(np.clip(1 - _g / .12, 0, 1) * 140 + np.clip((_g - .5) / .5, 0, 1) ** 1.5 * 190, 0, 255)
SHADE = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), np.repeat(_al, W, 1).astype(np.uint8)]), "RGBA")

def glass(img, box, r=44, fill=(28, 28, 30, 190), blur=22, outline=(255, 255, 255, 40)):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1c <= x0c or y1c <= y0c: return
    reg = img.crop((x0c, y0c, x1c, y1c)).filter(ImageFilter.GaussianBlur(blur))
    m = Image.new("L", (x1 - x0, y1 - y0), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], r, fill=255)
    m = m.crop((x0c - x0, y0c - y0, x0c - x0 + x1c - x0c, y0c - y0 + y1c - y0c))
    img.paste(reg, (x0c, y0c), m)
    lay = rgba(); ImageDraw.Draw(lay).rounded_rectangle([x0, y0, x1, y1], r, fill=fill, outline=outline, width=2)
    img.alpha_composite(lay)

def app_icon(img, x, y, s=96):
    """original 'game library' icon: pink→orange gradient squircle with a drawn gamepad"""
    g = np.zeros((s, s, 4), np.float32); yy, xx = np.mgrid[0:s, 0:s] / s; k = (xx + yy) / 2
    g[..., :3] = np.array(PINK) * (1 - k[..., None]) + np.array(ORANGE) * k[..., None]; g[..., 3] = 255
    ic = Image.fromarray(g.astype(np.uint8), "RGBA"); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, s - 1, s - 1], s * .23, fill=255)
    ic.putalpha(m); d = ImageDraw.Draw(ic); u = s / 96
    d.rounded_rectangle([18 * u, 34 * u, 78 * u, 64 * u], 15 * u, fill=WHITE)
    d.rectangle([29 * u, 45 * u, 41 * u, 49 * u], fill=PINK); d.rectangle([33 * u, 41 * u, 37 * u, 53 * u], fill=PINK)
    d.ellipse([58 * u, 40 * u, 64 * u, 46 * u], fill=ORANGE); d.ellipse([64 * u, 47 * u, 70 * u, 53 * u], fill=ORANGE)
    img.alpha_composite(ic, (int(x), int(y)))
def chat_icon(img, x, y, s=96):
    ic = rgba(s, s); d = ImageDraw.Draw(ic); d.rounded_rectangle([0, 0, s - 1, s - 1], s * .23, fill=GREEN)
    d.ellipse([18, 22, 78, 66], fill=WHITE); d.polygon([(30, 58), (24, 78), (46, 64)], fill=WHITE)
    img.alpha_composite(ic, (int(x), int(y)))

def notification(img, y, icon, app, when, title, body, alpha=1.0):
    x0, x1 = 40, W - 40
    glass(img, (x0, y, x1, y + 210), r=46, fill=(245, 245, 250, int(200 * alpha)), outline=(255, 255, 255, int(90 * alpha)))
    icon(img, x0 + 32, y + 40, 96)
    d = ImageDraw.Draw(img)
    d.text((x0 + 152, y + 34), app, font=MS(30, 600), fill=(60, 60, 67))
    d.text((x1 - 32 - d.textlength(when, font=MS(28, 500)), y + 36), when, font=MS(28, 500), fill=(110, 110, 118))
    d.text((x0 + 152, y + 78), title, font=MS(40, 800), fill=(0, 0, 0))
    d.text((x0 + 152, y + 132), body, font=MS(33, 500), fill=(40, 40, 46))

def checkbox(img, cx, cy, r, k, col=GREEN):
    """k: 0 empty, >0 ticking (spring)"""
    lay = rgba(); d = ImageDraw.Draw(lay)
    if k <= 0:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 200), width=6)
    else:
        s = back(min(k * 2.2, 1)) * r
        d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=col + (255,))
        p = min(1, max(0, (k - .15) / .45)); pts = [(cx - .45 * r, cy + .02 * r), (cx - .12 * r, cy + .34 * r), (cx + .5 * r, cy - .32 * r)]
        if p > 0:
            q = min(1, p * 2); a = pts[0]; b = (pts[0][0] + (pts[1][0] - pts[0][0]) * q, pts[0][1] + (pts[1][1] - pts[0][1]) * q)
            d.line([a, b], fill=WHITE, width=int(r * .2))
            if p > .5:
                q2 = (p - .5) * 2; c = (pts[1][0] + (pts[2][0] - pts[1][0]) * q2, pts[1][1] + (pts[2][1] - pts[1][1]) * q2)
                d.line([pts[1], c], fill=WHITE, width=int(r * .2)); d.ellipse([pts[1][0] - r * .1, pts[1][1] - r * .1, pts[1][0] + r * .1, pts[1][1] + r * .1], fill=WHITE)
    img.alpha_composite(lay)

def bubble(img, x, y, s, age, side="left", name=None, col=(58, 58, 60)):
    if age < 0: return
    k = back(min(1, age / .28)); f = MS(40, 600); d0 = ImageDraw.Draw(img)
    tw = d0.textlength(s, font=f); w = tw + 64; h = 88 + (40 if name else 0)
    lay = rgba(int(w) + 20, int(h) + 20); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, w, h], 40, fill=col + (240,))
    yy = 20
    if name: d.text((32, 16), name, font=MS(26, 700), fill=(255, 214, 10)); yy = 52
    d.text((32, yy), s, font=f, fill=WHITE)
    lay = lay.resize((max(1, int(lay.width * k)), max(1, int(lay.height * k))), Image.BILINEAR)
    ox = x if side == "left" else x - lay.width
    img.alpha_composite(lay, (int(ox), int(y + (1 - k) * 40)))

# ---------------------------------------------------------------- shots
def lock_screen(t, age, loop=False):
    img = blurred("GTAVI_Pre_Load", .5, 30, .7).copy()
    d = ImageDraw.Draw(img)
    text_c(d, W / 2, 210, "Thursday, November 19", MS(44, 600), WHITE)
    text_c(d, W / 2, 255, "12:00", MS(250, 300), WHITE)
    notes = [(0.25, app_icon, "GAME LIBRARY", "now", "GTA 6 is ready to play", "Pre-load complete. Press start."),
             (1.25, chat_icon, "THE BOYS (4)", "now", "Marcus", "bro are you on yet??"),
             (2.35, chat_icon, "MOM", "now", "Mom", "dinner is ready")]
    if loop: notes = notes[:1]
    ys = []
    for i, n in enumerate(notes):
        a = age - n[0]
        if a < 0: continue
        ys.append((i, n, a))
    # newest on top, older pushed down
    for rank, (i, n, a) in enumerate(reversed(ys)):
        y = 640 + rank * 236; drop = eout(a / .35); yy = -260 + (y + 260) * drop
        if i == 2 and age > 3.25:                                   # swipe mom away
            k = ease((age - 3.25) / .3); lay = rgba(); notification(lay, yy, n[1], n[2], n[3], n[4], n[5])
            img.alpha_composite(lay.transform(lay.size, Image.AFFINE, (1, 0, k * 1200, 0, 1, 0)))
            continue
        notification(img, yy, n[1], n[2], n[3], n[4], n[5])
    return img

def settings_shot(t, age, p):
    img = blurred("Vice_City_08", .5, 26, .55).copy()
    x0, x1, y0 = 70, W - 70, 220
    glass(img, (x0, y0, x1, y0 + 590), r=50, fill=(28, 28, 30, 215))
    d = ImageDraw.Draw(img)
    d.text((x0 + 44, y0 + 36), "Settings", font=MS(58, 800), fill=WHITE)
    rows = [("Brightness", "slider", .2, .85, 0.0), ("Camera FOV", "slider", .5, .25, .5), ("Subtitles", "toggle", 0, 1, 1.0),
            ("Vibration", "toggle", 1, 0, 1.6), ("Radio volume", "slider", .8, .4, 2.0)]
    for i, (lab, kind, v0, v1, at) in enumerate(rows):
        y = y0 + 130 + i * 90
        d.line([x0 + 44, y - 18, x1 - 44, y - 18], fill=(255, 255, 255, 30), width=2)
        d.text((x0 + 44, y + 6), lab, font=MS(38, 600), fill=LIGHT)
        k = ease((age - at) / .6) if age > at else 0
        if kind == "slider":
            # fiddling back and forth
            v = v0 + (v1 - v0) * k + (.08 * math.sin(age * 5 + i) if k > 0 and k < 1 else 0)
            sx0, sx1 = x1 - 440, x1 - 50; yy = y + 30
            d.rounded_rectangle([sx0, yy - 5, sx1, yy + 5], 5, fill=(90, 90, 96)); d.rounded_rectangle([sx0, yy - 5, sx0 + (sx1 - sx0) * v, yy + 5], 5, fill=BLUE)
            cx = sx0 + (sx1 - sx0) * v; d.ellipse([cx - 22, yy - 22, cx + 22, yy + 22], fill=WHITE)
        else:
            v = v0 + (v1 - v0) * k; tx = x1 - 170; yy = y + 6
            d.rounded_rectangle([tx, yy, tx + 116, yy + 64], 32, fill=tuple(int(a + (b - a) * v) for a, b in zip((90, 90, 96), GREEN)))
            cx = tx + 32 + 52 * v; d.ellipse([cx - 27, yy + 5, cx + 27, yy + 59], fill=WHITE)
    # time-in-settings counter
    secs = min(600, int(ease(p) * 598 + 2)); s = f"{secs // 60:02d}:{secs % 60:02d}"
    glass(img, (W / 2 - 280, 1010, W / 2 + 280, 1110), r=50, fill=(255, 59, 48, 210), outline=None)
    text_c(d, W / 2, 1030, f"TIME IN MENU  {s}", MS(44, 800), WHITE)
    return img

def car_shot(key, t, age, p, cx, z0, z1):
    return photo(key, p, cx, .5, z0, z1)

def heat(img, n, y=1010):
    """original 'heat' meter: n of 5 filled triangles"""
    lay = rgba(); d = ImageDraw.Draw(lay)
    glass(img, (W / 2 - 250, y - 10, W / 2 + 250, y + 90), r=50, fill=(0, 0, 0, 150))
    for i in range(5):
        cx = W / 2 - 180 + i * 90; on = i < n; s = 34
        d.polygon([(cx, y + 12), (cx + s, y + 72), (cx - s, y + 72)], fill=(RED + (255,)) if on else (255, 255, 255, 70))
    img.alpha_composite(lay)

def draw_shot(name, t, a, b):
    age = t - a; p = (t - a) / max(b - a, 1e-3)
    if name == "lock": return lock_screen(t, age)
    if name == "settings": return settings_shot(t, age, p)
    if name == "car":
        img = photo("ULTIMATE_EDITION_GROTTI_CHEETAH_04", p, .52, .5, 1.25, 1.05)
        return img
    if name == "car2":
        img = photo("Vice_City_24", p, .33, .5, 1.0, 1.14)
        bubble(img, 60, 420, "bro that's not your car", age - .25, "left", "MARCUS")
        return img
    if name == "cops":
        img = photo("Vice_City_06", p, .42, .5, 1.0, 1.16)
        k = .5 + .5 * math.sin(age * 18); arr = np.asarray(img, np.float32)
        edge = np.clip(np.abs(np.linspace(-1, 1, W))[None, :] ** 3, 0, 1)[..., None]
        col = np.array(RED if k > .5 else BLUE, np.float32)
        arr[..., :3] = arr[..., :3] * (1 - edge * .55) + col * edge * .55 * (0.6 + .4 * k)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
        heat(img, min(5, 1 + int(age / .25)))
        return img
    if name == "fail":
        img = photo("Vice_City_17", p, .5, .5, 1.12, 1.0)
        g = np.asarray(img, np.float32); l = g[..., :3].mean(-1, keepdims=True); g[..., :3] = l * .85 + g[..., :3] * .15
        img = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGBA")
        if age > .25:
            k = back(min(1, (age - .25) / .25)); s = int(170 * (2.2 - 1.2 * k))
            lay = rgba(); d = ImageDraw.Draw(lay); f = MS(s, 900); txt = "FAILED"
            text_c(d, W / 2, 470 - s / 2 + 60, txt, f, RED + (255,), stroke_width=6, stroke_fill=(0, 0, 0, 255))
            img.alpha_composite(lay.rotate(-6, center=(W / 2, 500), resample=Image.BICUBIC))
        if age > .7:
            dd = ImageDraw.Draw(img); glass(img, (W / 2 - 250, 1010, W / 2 + 250, 1110), r=50, fill=(0, 0, 0, 170))
            text_c(dd, W / 2, 1032, "SURVIVED  0:07", MS(46, 800), WHITE)
        return img
    if name in ("water", "water2"):
        img = photo("Leonida_Keys_04" if name == "water" else "Leonida_Keys_07", p, .5 if name == "water" else .55, .5, 1.02, 1.15)
        lay = rgba(); d = ImageDraw.Draw(lay); rng = np.random.default_rng(7)
        for i in range(26):
            x = rng.uniform(0, W); sp = rng.uniform(250, 520); r = rng.uniform(6, 22); y = (rng.uniform(0, H) - t * sp) % (H + 100) - 50
            d.ellipse([x - r + 14 * math.sin(t * 3 + i), y - r, x + r + 14 * math.sin(t * 3 + i), y + r], outline=(255, 255, 255, 150), width=3)
        img.alpha_composite(lay)
        if name == "water":
            if age < .25: img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - age / .25)))))  # splash
        depth = 2 + (t - st("water")) * 6
        dd = ImageDraw.Draw(img); glass(img, (W / 2 - 220, 1010, W / 2 + 220, 1110), r=50, fill=(0, 60, 110, 170))
        text_c(dd, W / 2, 1032, f"DEPTH  {depth:4.1f} m", MS(46, 800), WHITE)
        return img
    if name == "map":
        z = 3.2 - 2.2 * ease(min(1, age / 2.4))
        img = photo("Vice_City_26", 0, .5, .5, z, z)
        d = ImageDraw.Draw(img)
        # pin
        pc = (W / 2, 560); lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.ellipse([pc[0] - 40, pc[1] - 110, pc[0] + 40, pc[1] - 30], fill=RED + (255,)); dl.polygon([(pc[0] - 34, pc[1] - 58), (pc[0] + 34, pc[1] - 58), pc], fill=RED + (255,))
        dl.ellipse([pc[0] - 15, pc[1] - 85, pc[0] + 15, pc[1] - 55], fill=WHITE + (255,))
        # pinch gesture
        if age < 2.4:
            g = ease(min(1, age / 2.4)); sp = 260 - 200 * g
            for sgn in (-1, 1):
                cx, cy = W / 2 + sgn * sp * .7, 760 + sgn * sp * .5
                dl.ellipse([cx - 46, cy - 46, cx + 46, cy + 46], fill=(255, 255, 255, 110), outline=(255, 255, 255, 220), width=4)
        img.alpha_composite(lay)
        # zoom rail + scale
        glass(img, (W - 150, 330, W - 50, 760), r=50, fill=(28, 28, 30, 170)); d = ImageDraw.Draw(img)
        text_c(d, W - 100, 345, "+", MS(64, 600), WHITE); text_c(d, W - 100, 670, "−", MS(64, 600), WHITE)
        zz = (z - 1) / 2.2; ky = 450 + (1 - zz) * 180; d.ellipse([W - 122, ky - 22, W - 78, ky + 22], fill=WHITE)
        km = 0.1 * 2 ** ((3.2 - z) / 2.2 * 4.3)
        glass(img, (W / 2 - 230, 1010, W / 2 + 230, 1110), r=50, fill=(28, 28, 30, 190))
        text_c(d, W / 2, 1032, f"SCALE  {km:.1f} km" if km >= 1 else f"SCALE  {int(km * 1000)} m", MS(46, 800), WHITE)
        return img
    if name == "outro":
        img = photo("Jason_Lucia_Rooftop_portrait", p, .5, .42, 1.0, 1.08)
        return img
    raise ValueError(name)

# ---------------------------------------------------------------- persistent chrome
def status_bar(img, t):
    d = ImageDraw.Draw(img); m = min(5, int(t / TOTAL * 5.999)) if t < LOOP else 0
    d.text((70, 34), f"12:0{m}", font=MS(40, 700), fill=WHITE)
    x = W - 250
    for i in range(4): d.rounded_rectangle([x + i * 16, 64 - (i + 1) * 8, x + i * 16 + 10, 66], 3, fill=WHITE)
    d.text((x + 76, 34), "5G", font=MS(36, 700), fill=WHITE)
    d.rounded_rectangle([W - 140, 38, W - 70, 70], 9, outline=WHITE, width=3); d.rounded_rectangle([W - 134, 44, W - 134 + 52 * (1 - .4 * t / TOTAL), 64], 5, fill=WHITE)
    d.rectangle([W - 68, 48, W - 63, 60], fill=WHITE)

def stories_bar(img, t):
    d = ImageDraw.Draw(img); x0, gap = 40, 12; w = (W - 80 - gap * 4) / 5
    for i in range(5):
        a, b = ITEM_START[i], TICK[i]; k = min(1, max(0, (t - a) / (b - a)))
        xa = x0 + i * (w + gap)
        d.rounded_rectangle([xa, 104, xa + w, 112], 4, fill=(255, 255, 255, 90))
        if k > 0: d.rounded_rectangle([xa, 104, xa + w * k, 112], 4, fill=WHITE)
    d.text((40, 130), "IMAGES © ROCKSTAR GAMES · FAN-MADE", font=MS(22, 600), fill=(230, 230, 235))

def item_card(img, t):
    i = max([k for k in range(5) if t >= ITEM_START[k]], default=-1)
    if i < 0 or t >= st("outro"): return
    age = t - ITEM_START[i]; k = eout(age / .3)
    y0 = 1180 + (1 - k) * 120; x0, x1 = 40, W - 150
    glass(img, (x0, y0, x1, y0 + 170), r=46, fill=(28, 28, 30, 200))
    d = ImageDraw.Draw(img)
    d.text((x0 + 36, y0 + 22), f"FIRST 5 MINUTES  ·  {i + 1}/5", font=MS(26, 700), fill=(160, 160, 168))
    f = MS(50, 800); s = ITEMS[i]
    while d.textlength(s, font=f) > (x1 - x0 - 190): f = MS(f.size - 2, 800)
    d.text((x0 + 36, y0 + 72), s, font=f, fill=WHITE)
    checkbox(img, x1 - 80, y0 + 85, 46, (t - TICK[i]) / .5 if t >= TICK[i] else 0)

def checklist(img, t):
    a = st("outro"); age = t - a
    if age < 0 or t >= LOOP: return
    x0, x1, y0 = 60, W - 60, 820
    k = eout(age / .35); y0 += (1 - k) * 200
    glass(img, (x0, y0, x1, y0 + 640), r=50, fill=(28, 28, 30, 215))
    d = ImageDraw.Draw(img)
    d.text((x0 + 44, y0 + 34), "FIRST 5 MINUTES", font=MS(34, 800), fill=(160, 160, 168))
    d.text((x1 - 44 - d.textlength("5/5", font=MS(34, 800)), y0 + 34), "5/5", font=MS(34, 800), fill=GREEN)
    for i, s in enumerate(ITEMS):
        y = y0 + 110 + i * 100
        checkbox(img, x0 + 80, y + 30, 32, 1.0)
        d.text((x0 + 140, y + 6), s, font=MS(42, 700), fill=WHITE)
    # answer chips 0..5
    for j in range(6):
        ka = age - 1.0 - j * .09
        if ka < 0: continue
        s = back(min(1, ka / .25)); cx = W / 2 - 375 + j * 150; cy = y0 + 740; r = 58 * s
        lay = rgba(); dl = ImageDraw.Draw(lay); dl.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(BLUE if j < 5 else GREEN) + (255,))
        img.alpha_composite(lay); f = MS(int(60 * s) + 1, 800); text_c(ImageDraw.Draw(img), cx, cy - 38 * s, str(j), f, WHITE)

def build_caps():
    groups = []
    for seg in TM["segments"]:
        hl = [s for s in SEGMENTS if s["id"] == seg["id"]][0]["hl"]; cur = []
        for i, w in enumerate(seg["words"]):
            cur.append(w)
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(seg["words"]) - 1:
                groups.append(([dict(w, hl=clean(x["w"]) in hl) for x in cur for w in [x]], seg["id"])); cur = []
    return groups
CAPS = build_caps()
def disp(w):
    s = w.replace("six.", "6.").replace("six", "6")
    return s.upper()
def caption(img, t):
    if t >= LOOP: return
    g = None
    for ws, sid in CAPS:
        if ws[0]["a"] - .05 <= t: g = (ws, sid)
    if g is None: return
    ws, sid = g
    if t > ws[-1]["b"] + .6: return
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if nxt and t >= nxt[0] - .14: return
    if sid == "outro" and t > st("outro") + .2: y = 600
    elif sid in ("hook",): y = 1400
    else: y = 860
    f = MS(76, 900); d = ImageDraw.Draw(img)
    toks = [disp(w["w"]) for w in ws]; widths = [d.textlength(s, font=f) for s in toks]; sp = 24
    x = (W - sum(widths) - sp * (len(toks) - 1)) / 2
    age = t - ws[0]["a"]; pop = back(min(1, age / .16)) if age > 0 else 0
    lay = rgba(); dl = ImageDraw.Draw(lay)
    for w, s_, wd in zip(ws, toks, widths):
        on = w["a"] - .03 <= t; act = on and t < w["b"] + .05
        yy = y + (1 - pop) * 30
        if w["hl"] and on:
            dl.rounded_rectangle([x - 14, yy - 4, x + wd + 14, yy + 92], 22, fill=GREEN + (255,))
            dl.text((x, yy), s_, font=f, fill=WHITE)
        else:
            dl.text((x, yy), s_, font=f, fill=(255, 255, 255, 255 if on else 110), stroke_width=7, stroke_fill=(0, 0, 0, 230 if on else 90))
        if act: dl.rounded_rectangle([x, yy + 100, x + wd, yy + 108], 4, fill=BLUE + (255,))
        x += wd + sp
    img.alpha_composite(lay)

def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); return i, SHOTS[i]
def base(t):
    if t >= LOOP: return lock_screen(t, 0.45 + (t - LOOP) * .3, loop=True)
    i, (a, b, name, seg) = shot_at(t)
    img = draw_shot(name, t, a, b)
    age = t - a
    if i and age < .2:                                     # swipe-up app-switch transition
        pa, pb, pn, _ = SHOTS[i - 1]; prev = draw_shot(pn, a - 1e-3, pa, pb); k = eout(age / .2)
        canvas = rgba(); canvas.alpha_composite(prev, (0, int(-H * .35 * k)))
        lay = img.copy(); canvas.alpha_composite(lay, (0, int(H * (1 - k))))
        img = canvas
    return img

def frame(t, fi=None):
    img = base(t)
    if t < LOOP:
        img.alpha_composite(SHADE)
    else:
        k = ease((t - LOOP) / .25)
        if k < 1:
            prev = base(LOOP - 1e-3); prev.alpha_composite(SHADE); img = Image.blend(prev, img, k)
    status_bar(img, t)
    if t >= ITEM_START[0] and t < LOOP: stories_bar(img, t)
    item_card(img, t) if t < LOOP else None
    checklist(img, t)
    caption(img, t)
    d = ImageDraw.Draw(img); d.rounded_rectangle([W / 2 - 140, H - 30, W / 2 + 140, H - 20], 5, fill=(255, 255, 255, 200))  # home bar
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    for tk in TICK:
        if 0 <= t - tk < .12: arr += 40 * (1 - (t - tk) / .12)
    return to_img(arr)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
