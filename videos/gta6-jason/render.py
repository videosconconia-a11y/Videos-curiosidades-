# "5 THINGS YOU DIDN'T KNOW ABOUT JASON DUVAL" — editorial documentary look (new visual identity).
# Charcoal page + cream + electric-lime accents, DM Serif Display headlines, giant outlined numbers 01–05,
# layered photo panels (official Rockstar images), split screens, Keys map, timeline, diagonal wipes, fine grain.
# Usage: python3 render.py still <t>... | python3 render.py video <worker> <nworkers>
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS, DISPLAY

W, H, FPS = 1080, 1920, 30
FD = os.path.join(HERE, "fonts")
def F(name, s): return ImageFont.truetype(os.path.join(FD, name), s)
SERIF = lambda s: F("DMSerifDisplay-Regular.ttf", s)
SERIFI = lambda s: F("DMSerifDisplay-Italic.ttf", s)
BEBAS = lambda s: F("BebasNeue-Regular.ttf", s)
def MONT(s, w=600):
    f = F("Montserrat-VF.ttf", s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
BG = (16, 16, 18); CREAM = (242, 236, 224); LIME = (204, 255, 64); ORANGE = (255, 112, 64); GREY = (128, 128, 128)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word):
    for w in SEGT[seg]["words"]:
        if clean(w["w"]) == word: return w["a"]
    raise KeyError((seg, word))
def build_shots():
    out = []; segs = TM["segments"]
    for i, (sd, st) in enumerate(zip(SEGMENTS, segs)):
        s0 = 0.0 if i == 0 else st["a"] - 0.08
        s1 = segs[i + 1]["a"] - 0.08 if i + 1 < len(segs) else TOTAL
        starts = [(s0 if c is None else word_time(sd["id"], c) - 0.1, n) for n, c in sd["shots"]]
        for j, (a, n) in enumerate(starts):
            out.append((a, starts[j + 1][0] if j + 1 < len(starts) else s1, n, sd["id"]))
    return out
SHOTS = build_shots()

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def eio(p): p = min(max(p, 0), 1); return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))

# ---------------------------------------------------------------- page background (static, precomputed)
def make_page():
    a = np.zeros((H, W, 3), np.float32) + np.array(BG, np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    a += (np.exp(-(((xx - W * .2) / 700) ** 2 + ((yy - H * .25) / 900) ** 2)) * 10)[..., None]
    n = np.random.default_rng(3).standard_normal((H // 3, W // 3)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) - 128
    a += n[..., None] * .12
    img = to_img(a).convert("RGBA"); d = ImageDraw.Draw(img)
    for x in range(60, W, 120): d.line([x, 0, x, H], fill=(255, 255, 255, 10))
    for y in range(60, H, 120): d.line([0, y, W, y], fill=(255, 255, 255, 10))
    return img
PAGE = make_page()
GRAIN = [np.random.default_rng(k).standard_normal((H // 2, W // 2)).astype(np.float32) * 5 for k in range(4)]

@lru_cache(maxsize=8)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + "*.jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2200 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im

def crop(key, w, h, cx, cy, z):
    """crop of image `key` (centre cx,cy in 0..1, zoom z: 1 = largest crop of that aspect) resized to w x h"""
    im = load(key); ar = w / h
    cw, ch = (im.height * ar, im.height) if im.width / im.height > ar else (im.width, im.width / ar)
    cw /= z; ch /= z
    x = min(max(cx * im.width, cw / 2), im.width - cw / 2); y = min(max(cy * im.height, ch / 2), im.height - ch / 2)
    return im.resize((int(w), int(h)), Image.BILINEAR, box=(x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2)), (x - cw / 2, y - ch / 2, cw, ch, im.width, im.height)

def panel(img, key, rect, p, c0, c1, age, enter=.45, dirn=(0, 1), border=CREAM, shadow=True, label=None, dark=1.0):
    """photo panel: rect=(x,y,w,h); Ken Burns from c0=(cx,cy,z) to c1; slides in + wipe reveal"""
    if age < 0: return None
    x, y, w, h = rect; k = eout(age / enter)
    q = ease(p) * .6 + p * .4
    cx = c0[0] + (c1[0] - c0[0]) * q; cy = c0[1] + (c1[1] - c0[1]) * q; z = c0[2] * (c1[2] / c0[2]) ** q
    ph, info = crop(key, w, h, cx, cy, z)
    if dark != 1: ph = to_img(np.asarray(ph, np.float32) * dark)
    ox, oy = (1 - k) * dirn[0] * 160, (1 - k) * dirn[1] * 160
    if shadow:
        sh = rgba(); ImageDraw.Draw(sh).rectangle([x + 18 + ox, y + 26 + oy, x + w + 18 + ox, y + h + 26 + oy], fill=(0, 0, 0, int(150 * k)))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    m = Image.new("L", (int(w), int(h)), 0); md = ImageDraw.Draw(m)
    reveal = int(w * k) if dirn[0] else int(h * k)
    if dirn[0] >= 0 and dirn[0]: md.rectangle([0, 0, reveal, h], fill=255)
    elif dirn[0] < 0: md.rectangle([w - reveal, 0, w, h], fill=255)
    elif dirn[1] >= 0: md.rectangle([0, 0, w, reveal], fill=255)
    else: md.rectangle([0, h - reveal, w, h], fill=255)
    img.paste(ph.convert("RGBA"), (int(x + ox), int(y + oy)), m)
    d = ImageDraw.Draw(img)
    if border and k > .9: d.rectangle([x + ox, y + oy, x + w + ox, y + h + oy], outline=border + (255,), width=4)
    if label and age > enter * .8: lab(d, x + ox + 24, y + oy + h - 64, label)
    # image point mapper
    bx, by, cw, ch, iw, ih = info
    return lambda u, v: (x + ox + (u * iw - bx) / cw * w, y + oy + (v * ih - by) / ch * h)

def lab(d, x, y, s, bg=LIME, fg=BG, f=None):
    f = f or MONT(28, 800); tw = d.textlength(s, font=f)
    d.rectangle([x, y, x + tw + 30, y + 46], fill=bg); d.text((x + 15, y + 7), s, font=f, fill=fg); return tw + 30

def frame_draw(img, x0, y0, x1, y1, p, col=LIME, wdt=5):
    """lime rectangle that draws its perimeter (p 0..1) with corner ticks"""
    lay = rgba(); d = ImageDraw.Draw(lay)
    per = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    L = sum(math.dist(per[i], per[i + 1]) for i in range(4)); target = L * eio(p); acc = 0; pts = [per[0]]
    for i in range(4):
        sl = math.dist(per[i], per[i + 1])
        if acc + sl <= target: pts.append(per[i + 1]); acc += sl
        else:
            r = (target - acc) / sl; pts.append((per[i][0] + (per[i + 1][0] - per[i][0]) * r, per[i][1] + (per[i + 1][1] - per[i][1]) * r)); break
    if len(pts) > 1: d.line(pts, fill=col + (255,), width=wdt)
    for (cx, cy) in per[:4]: d.rectangle([cx - 9, cy - 9, cx + 9, cy + 9], fill=col + (int(255 * min(1, p * 3)),))
    img.alpha_composite(lay)

def big_number(img, n, age, y=180, x=None):
    """giant outlined number sliding up"""
    k = eout(age / .5); f = BEBAS(760)
    lay = rgba(); d = ImageDraw.Draw(lay); s = f"{n:02d}"
    tw = d.textlength(s, font=f); x = (W - tw) / 2 if x is None else x
    d.text((x, y + (1 - k) * 220), s, font=f, fill=(0, 0, 0, 0), stroke_width=6, stroke_fill=LIME + (int(255 * k),))
    img.alpha_composite(lay)

def headline(img, text, age, y, size=118, col=CREAM, italic_words=(), width=940, dly=.07):
    """serif headline, word-by-word rise; returns bottom y"""
    d = ImageDraw.Draw(img); words = text.split(); lines = [[]]; f = SERIF(size); fi = SERIFI(size)
    for w_ in words:
        fw = fi if w_.strip(".,…").lower() in italic_words else f
        cur = sum(d.textlength(x[0] + " ", font=x[1]) for x in lines[-1])
        if cur + d.textlength(w_, font=fw) > width and lines[-1]: lines.append([])
        lines[-1].append((w_, fw))
    idx = 0; lh = size * 1.08
    for li, ln in enumerate(lines):
        tw = sum(d.textlength(x[0] + " ", font=x[1]) for x in ln) - d.textlength(" ", font=f); xx = (W - tw) / 2
        for (w_, fw) in ln:
            k = eout((age - idx * dly) / .35)
            if k > 0:
                lay = rgba(); dl = ImageDraw.Draw(lay)
                c = LIME if fw is fi else col
                dl.text((xx, y + li * lh + (1 - k) * 40), w_, font=fw, fill=c + (int(255 * k),))
                img.alpha_composite(lay)
            xx += d.textlength(w_ + " ", font=fw); idx += 1
    return y + len(lines) * lh

def kicker(d, text, y, col=LIME):
    f = MONT(30, 700); s = "  ".join(text.upper()); tw = d.textlength(s, font=f)
    d.text(((W - tw) / 2, y), s, font=f, fill=col)

TIMELINE = ["CROOKS", "ARMY", "KEYS", "NOW", "LUCIA"]
def timeline(img, cur, age, y=1270):
    d = ImageDraw.Draw(img); x0, x1 = 120, 960; n = len(TIMELINE)
    d.line([x0, y, x1, y], fill=(255, 255, 255, 70), width=3)
    k = eout(age / .8); xc = x0 + (x1 - x0) * ((cur - 1) + k * 0) / (n - 1)
    d.line([x0, y, x0 + (x1 - x0) * ((cur - 1) / (n - 1)) * min(1, .3 + k), y], fill=LIME, width=5)
    for i, lb in enumerate(TIMELINE):
        x = x0 + (x1 - x0) * i / (n - 1); on = i < cur
        r = 13 if i == cur - 1 else 8
        d.ellipse([x - r, y - r, x + r, y + r], fill=LIME if on else BG, outline=LIME if on else GREY, width=3)
        f = MONT(24, 700 if i == cur - 1 else 500); tw = d.textlength(lb, font=f)
        d.text((x - tw / 2, y + 26), lb, font=f, fill=LIME if i == cur - 1 else (170, 170, 170))

# ---------------------------------------------------------------- shots
ROOF = "Jason_Lucia_Rooftop_portrait"
def draw_shot(name, t, a, b):
    p = (t - a) / max(1e-3, b - a); age = t - a
    img = PAGE.copy(); d = ImageDraw.Draw(img)
    if name == "hook":
        ph, _ = crop("Jason_Duval_19", W, H, .66 - .04 * p, .45, 1.15 + .15 * p)
        a_ = np.asarray(ph, np.float32); gx = np.linspace(0, 1, W)[None, :, None]; gy = np.linspace(0, 1, H)[:, None, None]
        a_ = a_ * (.35 + .65 * np.clip(gx * 1.6 - .2, 0, 1)) * (1 - .55 * np.clip((gy - .55) * 2.2, 0, 1))
        img.paste(to_img(a_).convert("RGBA")); d = ImageDraw.Draw(img)
        kicker(d, "case file · vol. vi", 230)
        headline(img, "You don't really know", age - .05, 300, 132, width=900, dly=.08)
        k = eout((age - .55) / .4)
        if k > 0:
            lay = rgba(); dl = ImageDraw.Draw(lay); f = SERIFI(250); s = "Jason…"; tw = dl.textlength(s, font=f)
            dl.text(((W - tw) / 2, 590 + (1 - k) * 60), s, font=f, fill=LIME + (int(255 * k),)); img.alpha_composite(lay)
    elif name == "hook2":
        P = panel(img, "Jason_Duval_01", (140, 300, 800, 1060), p, (.70, .45, 1.0), (.72, .40, 1.15), age, dirn=(0, 1))
        frame_draw(img, 110, 270, 970, 1390, (age - .2) / .7)
        d = ImageDraw.Draw(img); f = BEBAS(150); s = "NOT YET."; tw = d.textlength(s, font=f)
        if age > .35: d.text(((W - tw) / 2, 1420), s, font=f, fill=CREAM)
    elif name.endswith("_title"):
        n = int(name[1]); big_number(img, n, age, y=150)
        heads = {1: ("Raised around crooks", ("crooks",)), 2: ("The Army years", ("army",)), 3: ("Back in the Keys", ("keys",)),
                 4: ("The easy life?", ("easy",)), 5: ("Meeting Lucia", ("lucia",))}[n]
        kicker(d, f"fact {n:02d} / 05", 1000)
        headline(img, heads[0], age - .15, 1060, 120, italic_words=heads[1])
        timeline(img, n, age)
    elif name == "f1_crooks":
        panel(img, "Jason_Duval_14", (80, 210, 920, 900), p, (.52, .45, 1.0), (.55, .40, 1.12), age, dirn=(1, 0), label="OFFICIAL SCREENSHOT")
        headline(img, "“Jason grew up around grifters and crooks.”", age - .4, 1170, 76, italic_words=("grifters", "crooks."), width=900, dly=.05)
        d = ImageDraw.Draw(img); d.text((W / 2 - 150, 1400), "— ROCKSTAR GAMES", font=MONT(28, 700), fill=GREY)
    elif name == "f1_world":
        panel(img, "Cal_Hampton_02", (60, 230, 640, 760), p, (.40, .45, 1.0), (.45, .45, 1.15), age, dirn=(-1, 0), label="GRIFTERS")
        panel(img, "Jason_Duval_14", (380, 720, 640, 640), p, (.25, .45, 1.2), (.20, .45, 1.35), age - .25, dirn=(1, 0), label="CROOKS")
        d = ImageDraw.Draw(img); d.text((70, 1420), "No strangers.", font=SERIFI(96), fill=LIME)
    elif name == "f2_army":
        panel(img, "Jason_Duval_15", (100, 220, 880, 1100), p, (.50, .40, 1.0), (.50, .35, 1.15), age, dirn=(0, -1))
        frame_draw(img, 70, 190, 1010, 1350, (age - .25) / .7)
        if age > .5: lab(ImageDraw.Draw(img), 100, 1390, "A STINT IN THE ARMY")
        if age > .8: ImageDraw.Draw(img).text((100, 1460), "to shake off his troubled teens", font=SERIFI(58), fill=CREAM)
    elif name == "f2_shirt":
        # zoom from the full key art into the U.S. ARMY shirt
        z = 1.0 + 1.6 * eio(min(1, age / 1.2))
        P = panel(img, ROOF, (120, 200, 840, 1260), p, (.36, .47, z), (.33, .46, z), 1.0, border=CREAM)
        sx, sy = P(.33, .46)
        if age > 1.0: frame_draw(img, sx - 260, sy - 170, sx + 260, sy + 130, (age - 1.0) / .5)
        if age > 1.3: lab(ImageDraw.Draw(img), 120, 1500, "“U.S. ARMY” · OFFICIAL KEY ART")
    elif name == "f3_back":
        panel(img, "Jason_Duval_12", (100, 220, 880, 1000), p, (.70, .40, 1.0), (.72, .36, 1.12), age, dirn=(0, 1))
        frame_draw(img, 70, 190, 1010, 1250, (age - .2) / .6)
        headline(img, "What he knows best.", age - .4, 1300, 104, italic_words=("best",), width=900)
    elif name == "f3_map":
        panel(img, "Leonida_Keys_01", (60, 200, 960, 700), p, (.55, .45, 1.0), (.58, .45, 1.15), age, dirn=(1, 0), label="LEONIDA KEYS")
        # stylised Keys chain map
        lay = rgba(); dl = ImageDraw.Draw(lay); n = 16
        pts = [(170 + i * 48, 1080 + 90 * math.sin(i / n * 2.2) + i * 9) for i in range(n)]
        shown = int(n * eout((age - .3) / 1.2))
        for i in range(shown):
            x, y = pts[i]; r = 16 - i * .5; dl.ellipse([x - r * 1.8, y - r, x + r * 1.8, y + r], fill=CREAM + (220,))
        if shown > 1: dl.line(pts[:shown], fill=LIME + (255,), width=4)
        if shown >= n:
            x, y = pts[-1]; dl.ellipse([x - 18, y - 18, x + 18, y + 18], outline=LIME + (255,), width=5)
        img.alpha_composite(lay); d = ImageDraw.Draw(img)
        d.text((150, 960), "VICE CITY", font=MONT(26, 700), fill=GREY); d.text((700, 1300), "THE KEYS", font=BEBAS(110), fill=LIME)
        d.text((150, 1440), "working for local drug runners", font=SERIFI(60), fill=CREAM)
    elif name == "f3_brian":
        P = panel(img, "Brian_Heder_04", (60, 220, 960, 1080), p, (.45, .40, 1.0), (.48, .38, 1.1), age, dirn=(0, 1))
        d = ImageDraw.Draw(img)
        for (u, v, s, dl_, bgc) in ((.40, .62, "BRIAN · DRUG RUNNER", .4, LIME), (.80, .70, "JASON", .7, CREAM), (.12, .72, "LORI · BRIAN'S 3RD WIFE", 1.0, ORANGE)):
            x, y = P(u, v)
            if age > dl_ and 60 < x < W - 60: lab(d, max(70, min(x - 120, W - 420)), y, s, bg=bgc)
        if age > .4: d.text((70, 1350), "The boss.", font=SERIFI(100), fill=LIME)
    elif name == "f3_house":
        panel(img, "ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_01", (60, 220, 960, 760), p, (.42, .40, 1.0), (.42, .38, 1.15), age, dirn=(-1, 0), label="JASON'S SAFEHOUSE")
        d = ImageDraw.Draw(img); f = BEBAS(190); k = eout((age - .2) / .4)
        if k > 0: d.text((70, 1020 + (1 - k) * 40), "RENT FREE*", font=f, fill=CREAM)
        if age > .9: d.text((76, 1250), "*if he helps with the shakedowns", font=SERIFI(58), fill=LIME)
    elif name == "f4_split":
        panel(img, "Jason_Duval_03", (60, 200, 960, 560), p, (.30, .40, 1.0), (.28, .40, 1.1), age, dirn=(-1, 0), label="THE PLAN: AN EASY LIFE")
        panel(img, "Jason_Duval_18", (60, 800, 960, 560), p, (.55, .40, 1.0), (.55, .40, 1.12), age - .9, dirn=(1, 0), label="THE REALITY", )
        d = ImageDraw.Draw(img); d.line([60, 780, 1020, 780], fill=LIME, width=4)
    elif name == "f4_harder":
        ph, _ = crop("Jason_Duval_17", W, H, .45, .45, 1.0 + .15 * p)
        a_ = np.asarray(ph, np.float32) * .55; img.paste(to_img(a_).convert("RGBA")); d = ImageDraw.Draw(img)
        kicker(d, "in rockstar's words", 520)
        headline(img, "things just keep getting", age - .1, 580, 112, width=900, dly=.08)
        k = eout((age - .8) / .4)
        if k > 0:
            lay = rgba(); dl = ImageDraw.Draw(lay); f = BEBAS(330); s = "HARDER."; tw = dl.textlength(s, font=f)
            dl.text(((W - tw) / 2, 820 + (1 - k) * 80), s, font=f, fill=LIME + (int(255 * k),)); img.alpha_composite(lay)
    elif name == "f5_duo":
        panel(img, "Jason_and_Lucia_17", (60, 220, 960, 1060), p, (.45, .5, 1.0), (.42, .5, 1.12), age, dirn=(0, 1))
        frame_draw(img, 40, 200, 1040, 1300, (age - .3) / .6)
        d = ImageDraw.Draw(img); d.text((70, 1350), "Jason + Lucia", font=SERIFI(100), fill=CREAM)
    elif name == "f5_split":
        panel(img, "Jason_and_Lucia_14", (60, 200, 960, 560), p, (.5, .45, 1.0), (.5, .42, 1.1), age, dirn=(-1, 0))
        panel(img, "Jason_Duval_16", (60, 800, 960, 560), p, (.45, .45, 1.0), (.45, .45, 1.1), age - .45, dirn=(1, 0))
        d = ImageDraw.Draw(img)
        if age > .2: d.text((90, 640), "BEST", font=BEBAS(140), fill=LIME, stroke_width=4, stroke_fill=BG)
        if age > .75: d.text((90, 1240), "WORST?", font=BEBAS(140), fill=ORANGE, stroke_width=4, stroke_fill=BG)
        d.line([60, 780, 1020, 780], fill=LIME, width=4)
    elif name == "f5_tell":
        P = panel(img, "Jason_Duval_19", (100, 260, 880, 1000), p, (.68, .45, 1.2), (.68, .43, 1.45), age, dirn=(0, -1), dark=.85)
        lay = rgba(); dl = ImageDraw.Draw(lay); f = BEBAS(700); k = eout((age - .3) / .5)
        dl.text((560, 300 + (1 - k) * 100), "?", font=f, fill=(0, 0, 0, 0), stroke_width=6, stroke_fill=LIME + (int(255 * k),)); img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
        if age > .5: d.text((100, 1300), "Even Jason can't tell.", font=SERIFI(82), fill=CREAM)
    elif name == "outro":
        ph, _ = crop("Jason_and_Lucia_16", W, H, .5, .5, 1.05 + .1 * p)
        a_ = np.asarray(ph, np.float32); gy = np.linspace(0, 1, H)[:, None, None]; a_ = a_ * (1 - .65 * np.clip(1 - gy * 2.2, 0, 1))
        img.paste(to_img(a_).convert("RGBA")); d = ImageDraw.Draw(img)
        kicker(d, "end of file", 230)
        headline(img, "How much did you know?", age - .1, 290, 140, italic_words=("know?",), width=900)
        if age > 1.0:
            s = "COMMENT YOUR SCORE  0 – 5"; f = MONT(32, 800); tw = d.textlength(s, font=f)
            lab(d, (W - tw - 30) / 2, 760, s)
    return img

# ---------------------------------------------------------------- captions (clean editorial: cream sans, lime underline, keywords serif italic)
def build_caps():
    caps = []
    for sd in SEGMENTS:
        ws = [(w["w"].strip(), w["a"], w["b"], clean(w["w"]) in sd["hl"]) for w in SEGT[sd["id"]]["words"]]
        g = []
        for k, x in enumerate(ws):
            g.append(x)
            if x[0][-1] in ".,?!…" or len(g) >= 4 or sum(len(q[0]) for q in g) > 20 or k == len(ws) - 1: caps.append(g); g = []
    out = []
    for i, g in enumerate(caps):
        a = g[0][1] - .05; b = caps[i + 1][0][1] - .05 if i + 1 < len(caps) else g[-1][2] + .5
        out.append((a, min(b, g[-1][2] + .5), g))
    return out
CAPS = build_caps()
def caption(img, t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return
    a, b, g = cur[0]; d = ImageDraw.Draw(img)
    fs, fh = MONT(62, 700), SERIFI(72)
    parts = [(w[0], fh if w[3] else fs, w) for w in g]; sp = 18
    tw = sum(d.textlength(x[0], font=x[1]) for x in parts) + sp * (len(parts) - 1)
    while tw > W - 140:
        fs, fh = MONT(fs.size - 4, 700), SERIFI(fh.size - 4); parts = [(w[0], fh if w[3] else fs, w) for w in g]
        tw = sum(d.textlength(x[0], font=x[1]) for x in parts) + sp * (len(parts) - 1)
    x = (W - tw) / 2; y = 1610
    lay = rgba(); dl = ImageDraw.Draw(lay)
    dl.rectangle([x - 30, y - 18, x + tw + 30, y + 96], fill=(10, 10, 12, 190))
    for i, (s, f, w) in enumerate(parts):
        spoken = t >= w[1] - .03; nxt = g[i + 1][1] if i + 1 < len(g) else b; active = spoken and t < nxt
        k = eout((t - w[1] + .03) / .12) if spoken else 0
        col = (LIME if w[3] else CREAM) if spoken else (150, 150, 150)
        yy = y + (1 - k) * 10 + (6 if f is fs else -4)
        dl.text((x, yy), s, font=f, fill=col + (255 if spoken else 120,))
        ww = dl.textlength(s, font=f)
        if active: dl.rectangle([x, y + 84, x + ww * eout((t - w[1]) / .2), y + 90], fill=LIME + (255,))
        x += ww + sp
    img.alpha_composite(lay)

# ---------------------------------------------------------------- compositing: diagonal wipe transitions, chrome, grain
def frame(t, fi):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); a, b, name, seg = SHOTS[i]; age = t - a
    img = draw_shot(name, t, a, b)
    # diagonal lime/charcoal wipe over the first 0.28 s of each shot
    if i and age < .28:
        k = eio(age / .28); lay = rgba(); dl = ImageDraw.Draw(lay)
        off = -1400 + 3600 * k
        dl.polygon([(off, 0), (off + 600, 0), (off + 600 - 900, H), (off - 900, H)], fill=BG + (255,))
        dl.polygon([(off + 600, 0), (off + 640, 0), (off + 640 - 900, H), (off + 600 - 900, H)], fill=LIME + (255,))
        img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    # editorial chrome
    d.text((60, 70), "JASON DUVAL — CASE FILE", font=MONT(24, 700), fill=CREAM)
    d.text((W - 230, 70), "GTA VI · LEONIDA", font=MONT(24, 500), fill=GREY)
    d.line([60, 112, W - 60, 112], fill=(255, 255, 255, 60), width=2)
    d.rectangle([60, 112, 60 + (W - 120) * min(1, t / TOTAL), 116], fill=LIME)
    n = 0
    for sd in SEGMENTS:
        if sd["id"].startswith("f") and t >= SEGT[sd["id"]]["a"] - .08: n = int(sd["id"][1])
    if n: d.text((W - 190, H - 360), f"{n:02d} / 05", font=MONT(26, 700), fill=LIME)
    d.text((60, H - 360), "IMAGES © ROCKSTAR GAMES", font=MONT(20, 600), fill=(150, 150, 150))
    caption(img, t)
    arr = np.asarray(img.convert("RGB")).astype(np.float32) + np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    if t < .25: arr *= ease(t / .25)
    return to_img(arr)

def frame_at(t): return frame(t, int(t * FPS))

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for s in sys.argv[2:]: frame_at(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
