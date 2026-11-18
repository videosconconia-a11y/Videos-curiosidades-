# "GTA 6 Pre-Orders Hit $1.5 BILLION?!" — BREAKING NEWS / LIVE BROADCAST identity.
# Palette: red #D7141A, navy #0B1F3A, white, yellow #F5C400. Official Rockstar key art as broadcast backgrounds,
# original broadcast graphics: LIVE bug, BREAKING banner, chyron lower-third, ticker, counters, donut chart, bar race.
# Usage: python3 render.py still <t>... | python3 render.py video <worker> <nworkers>
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS = 1080, 1920, 30
FD = os.path.join(HERE, "fonts")
def VF(name, s, w):
    f = ImageFont.truetype(os.path.join(FD, name), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
OSW = lambda s, w=700: VF("Oswald-VF.ttf", s, w)
RC = lambda s, w=700: VF("RobotoCondensed-VF.ttf", s, w)
RED = (215, 20, 26); NAVY = (11, 31, 58); WHITE = (255, 255, 255); YEL = (245, 196, 0); DARK = (6, 14, 28); GREEN = (40, 200, 110)

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
        s0 = 0.0 if i == 0 else st["a"] - 0.06
        s1 = segs[i + 1]["a"] - 0.06 if i + 1 < len(segs) else TOTAL
        starts = [(s0 if c is None else word_time(sd["id"], c) - 0.08, n) for n, c in sd["shots"]]
        for j, (a, n) in enumerate(starts):
            out.append((a, starts[j + 1][0] if j + 1 < len(starts) else s1, n, sd["id"]))
    return out
SHOTS = build_shots()
def st(n): return [s[0] for s in SHOTS if s[2] == n][0]

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))
def tw_(d, s, f): return d.textlength(s, font=f)
def text_c(d, cx, y, s, f, fill, stroke=0, sc=(0, 0, 0)):
    d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sc)

@lru_cache(maxsize=8)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + "*.jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2300 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im
def bg(key, p, cx=.5, cy=.5, z0=1.0, z1=1.15, dark=.55, tint=True):
    im = load(key); z = z0 + (z1 - z0) * (ease(p) * .6 + p * .4)
    ch = im.height / z; cw = ch * W / H
    if cw > im.width: cw = im.width / z; ch = cw * H / W
    x = min(max(cx * im.width, cw / 2), im.width - cw / 2); y = min(max(cy * im.height, ch / 2), im.height - ch / 2)
    a = np.asarray(im.resize((W, H), Image.BILINEAR, box=(x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2)), np.float32) * dark
    if tint: a = a * .8 + np.array(NAVY, np.float32) * .35
    return to_img(a).convert("RGBA")

# broadcast "studio" background: navy gradient + moving light streaks + world-grid
YY, XX = np.mgrid[0:H, 0:W]
STUDIO = (np.array(NAVY, np.float32) * (1.1 - .6 * (YY / H))[..., None] + np.array([0, 10, 30], np.float32) * np.exp(-((XX - W / 2) ** 2 + (YY - 800) ** 2) / 4e5)[..., None])
def studio(t):
    a = STUDIO.copy()
    for k in range(3):
        x0 = ((t * 260 + k * 420) % (W + 900)) - 450
        a += (np.exp(-((XX - x0 - (YY - 900) * .45) / 60) ** 2) * 18)[..., None] * np.array([1, 1.3, 2.0])
    img = to_img(a).convert("RGBA"); d = ImageDraw.Draw(img)
    for x in range(0, W, 90): d.line([x, 0, x, H], fill=(255, 255, 255, 12))
    for y in range(0, H, 90): d.line([0, y, W, y], fill=(255, 255, 255, 12))
    return img

def stamp(img, cx, cy, s, f, col, age, rot=-6, fill=None):
    if age < 0: return
    sc = 1 + 1.2 * (1 - eout(age / .16)) if age < .16 else 1
    lay = rgba(); d = ImageDraw.Draw(lay); w = tw_(d, s, f); h = f.size
    d.rectangle([cx - w / 2 - 34, cy - h * .62, cx + w / 2 + 34, cy + h * .7], fill=fill, outline=col + (255,), width=10)
    text_c(d, cx, cy - h * .6, s, f, (WHITE if fill else col) + (255,))
    lay = lay.rotate(rot, Image.BICUBIC, center=(cx, cy))
    if sc != 1:
        big = lay.resize((int(W * sc), int(H * sc)), Image.BICUBIC); lay = rgba(); lay.paste(big, (int(cx - cx * sc), int(cy - cy * sc)), big)
    img.alpha_composite(lay)

def counter(img, y, value, age, dur, prefix="", suffix="", f=None, col=WHITE, fmt="{:,.0f}"):
    v = value * eout(min(1, max(0, age) / dur))
    d = ImageDraw.Draw(img); f = f or OSW(170, 700)
    s = prefix + fmt.format(v) + suffix; text_c(d, W / 2, y, s, f, col, 6, (0, 0, 0))

def source_tag(d, y, s="SOURCE: SENSOR TOWER ESTIMATE · NOV 17"):
    f = RC(30, 700); w = tw_(d, s, f); d.rectangle([(W - w) / 2 - 20, y, (W + w) / 2 + 20, y + 48], fill=YEL); text_c(d, W / 2, y + 6, s, f, NAVY)

# ---------------------------------------------------------------- shots
def draw_shot(name, t, a, b):
    p = (t - a) / max(1e-3, b - a); age = t - a
    if name == "hook":
        img = bg("Jason_Lucia_Rooftop_portrait", p, .5, .42, 1.25, 1.0, .75, tint=False)
        lay = rgba(); d = ImageDraw.Draw(lay)
        k = eout(age / .25); y = 250
        d.rectangle([0, y, W * k, y + 190], fill=RED + (255,)); d.rectangle([0, y + 190, W * k, y + 204], fill=YEL + (255,))
        if age > .15: text_c(d, W / 2, y + 12, "BREAKING NEWS", OSW(150, 700), WHITE + (255,))
        img.alpha_composite(lay)
        if age > .9:
            k2 = eout((age - .9) / .3); lay = rgba(); d = ImageDraw.Draw(lay)
            d.rectangle([60, 520, 60 + 960 * k2, 700], fill=NAVY + (235,))
            if k2 > .9: text_c(d, W / 2, 545, "NOT EVEN OUT YET", OSW(110, 700), WHITE + (255,))
            img.alpha_composite(lay)
    elif name == "hook2":
        img = bg("hero", p, .55, .5, 1.0, 1.12, .45)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 380, "ALREADY A", OSW(110, 600), WHITE)
        counter(img, 500, 1_000_000_000, age, 1.2, "$", "+", OSW(150, 700), YEL)
        text_c(d, W / 2, 700, "GAME", OSW(110, 600), WHITE)
    elif name == "source":
        img = studio(t); d = ImageDraw.Draw(img)
        lay = rgba(); dl = ImageDraw.Draw(lay); k = eout(age / .4)
        dl.rectangle([80, 330, 1000, 900], fill=(255, 255, 255, 18), outline=(255, 255, 255, 80), width=3)
        # mini line chart drawing on
        pts = [(140 + i * 26, 820 - 380 * (1 - math.exp(-i / 12)) - 15 * math.sin(i * .9)) for i in range(int(32 * k) + 1)]
        if len(pts) > 1: dl.line(pts, fill=YEL + (255,), width=8, joint="curve")
        img.alpha_composite(lay)
        text_c(d, W / 2, 360, "MARKET TRACKER", RC(44, 700), (190, 205, 230))
        text_c(d, W / 2, 410, "SENSOR TOWER", OSW(120, 700), WHITE)
        source_tag(d, 940, "ESTIMATE · NOT OFFICIAL DATA")
    elif name == "preorders":
        img = studio(t); d = ImageDraw.Draw(img)
        counter(img, 400, 15_880_000, age, 1.8, "", "", OSW(170, 700), WHITE)
        text_c(d, W / 2, 610, "DIGITAL PRE-ORDERS", OSW(90, 600), YEL)
        text_c(d, W / 2, 730, "PLAYSTATION + XBOX", RC(48, 700), (200, 210, 230))
        source_tag(d, 830)
    elif name == "dollars":
        img = bg("Vice_City_18", p, .3, .5, 1.05, 1.2, .35)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 330, "ESTIMATED VALUE", RC(50, 700), (210, 220, 235))
        counter(img, 420, 1_540_000_000, age, 1.6, "$", "", OSW(150, 700), YEL)
        if age > 1.6: stamp(img, W / 2, 760, "$1.5 BILLION", OSW(120, 700), YEL, age - 1.6, rot=-4)
        source_tag(d, 900)
    elif name == "nobody":
        img = bg("GTAVI_Pre_Load", p, .45, .5, 1.0, 1.15, .45)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 340, "MISSIONS PLAYED:", OSW(100, 600), WHITE)
        k = back(age / .35)
        lay = rgba(); dl = ImageDraw.Draw(lay); text_c(dl, W / 2, 480, "0", OSW(380, 700), RED + (255,), 8, (0, 0, 0, 255))
        if k > 0:
            big = lay.resize((int(W * k), int(H * k)), Image.BICUBIC); l2 = rgba(); l2.paste(big, (int(W / 2 - W / 2 * k), int(680 - 680 * k)), big); img.alpha_composite(l2)
    elif name == "ps5":
        img = studio(t); d = ImageDraw.Draw(img)
        cx, cy, R = W / 2, 620, 300; k = eout(age / 1.0)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.pieslice([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * .75 * k, fill=(30, 110, 255, 255))
        dl.pieslice([cx - R, cy - R, cx + R, cy + R], -90 + 270 * k, -90 + 270 * k + 90 * k, fill=(16, 160, 80, 255))
        dl.ellipse([cx - R * .55, cy - R * .55, cx + R * .55, cy + R * .55], fill=NAVY + (255,))
        img.alpha_composite(lay); d = ImageDraw.Draw(img)
        text_c(d, cx, cy - 80, f"{int(75 * k)}%", OSW(130, 700), WHITE); text_c(d, cx, cy + 60, "PS5", OSW(60, 600), (120, 180, 255))
        if age > .9:
            d.rectangle([110, 990, 150, 1030], fill=(30, 110, 255)); d.text((170, 984), "PS5  ~75%", font=OSW(54, 600), fill=WHITE)
            d.rectangle([590, 990, 630, 1030], fill=(16, 160, 80)); d.text((650, 984), "XBOX  ~25%", font=OSW(54, 600), fill=WHITE)
        text_c(d, W / 2, 260, "WHERE PRE-ORDERS WENT", OSW(70, 600), YEL)
    elif name == "unconfirmed":
        img = bg("Vice_City_08", p, .5, .5, 1.0, 1.1, .35)
        stamp(img, W / 2, 620, "UNCONFIRMED", OSW(150, 700), RED, age - .1, rot=-7)
        stamp(img, W / 2, 800, "ESTIMATE", OSW(110, 700), WHITE, age - .45, rot=-7, fill=RED + (255,))
    elif name == "taketwo":
        img = studio(t); d = ImageDraw.Draw(img)
        lay = rgba(); dl = ImageDraw.Draw(lay); k = eout(age / .35)
        dl.rectangle([70, 360, 1010, 860], fill=(255, 255, 255, 235)); dl.rectangle([70, 360, 1010, 440], fill=NAVY + (255,))
        dl.text((110, 372), "OFFICIAL STATEMENT · TAKE-TWO", font=RC(40, 700), fill=YEL + (255,))
        for i, ln in enumerate(["Pre-orders are tracking", "well above expectations."]):
            dl.text((110, 500 + i * 90), ln, font=OSW(74, 500), fill=NAVY + (255,))
        dl.text((110, 700), "(as reported) · no official numbers released", font=RC(34, 500), fill=(90, 100, 120, 255))
        lay = lay.transform((W, H), Image.AFFINE, (1, 0, (1 - k) * -900, 0, 1, 0)); img.alpha_composite(lay)
    elif name == "question":
        img = bg("trailer-2", p, .5, .45, 1.0, 1.12, .4)
        stamp(img, W / 2, 560, "THE REAL", OSW(130, 700), WHITE, age - .05, rot=0)
        stamp(img, W / 2, 760, "QUESTION", OSW(150, 700), YEL, age - .3, rot=-3, fill=RED + (255,))
    elif name in ("gta5", "record"):
        img = studio(t); d = ImageDraw.Draw(img)
        text_c(d, W / 2, 230, "DAY-ONE SALES", OSW(90, 700), YEL)
        base = 1080; maxh = 620
        k5 = eout(age / .9) if name == "gta5" else 1
        # GTA V bar
        h5 = maxh * .62 * k5
        d.rectangle([180, base - h5, 460, base], fill=(150, 160, 175)); text_c(d, 320, base + 20, "GTA V · 2013", RC(42, 700), WHITE)
        text_c(d, 320, base - h5 - 90, "$800M+", OSW(80, 700), WHITE)
        # GTA 6 bar (unknown)
        if name == "record":
            k6 = (math.sin(age * 5) * .5 + .5) * .35 + .5 * eout(age / .6)
            h6 = maxh * k6
            d.rectangle([620, base - h6, 900, base], fill=RED); text_c(d, 760, base + 20, "GTA 6 · 2026", RC(42, 700), WHITE)
            text_c(d, 760, base - h6 - 110, "?", OSW(110, 700), YEL)
            if age > .6: stamp(img, W / 2, 470, "RECORD?", OSW(110, 700), YEL, age - .6, rot=-4)
        else:
            d.rectangle([620, base - 8, 900, base], fill=RED); text_c(d, 760, base + 20, "GTA 6 · 2026", RC(42, 700), WHITE)
            text_c(d, W / 2, 1180, "OFFICIAL · TAKE-TWO, 2013", RC(34, 600), (180, 190, 210))
    elif name == "outro":
        img = bg("Jason_Lucia_Lock_And_Load_portrait", p, .5, .45, 1.0, 1.1, .5)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.rectangle([70, 300, 1010, 900], fill=NAVY + (230,), outline=YEL + (255,), width=6)
        text_c(dl, W / 2, 330, "LIVE POLL", RC(44, 700), YEL + (255,))
        text_c(dl, W / 2, 400, "GTA 6 DAY ONE?", OSW(110, 700), WHITE + (255,))
        for i, (lab, col) in enumerate([("A · UNDER $800M", (150, 160, 175)), ("B · $800M – $1.5B", YEL), ("C · OVER $1.5B", RED)]):
            if age > .3 + i * .15:
                y = 560 + i * 105; dl.rectangle([120, y, 960, y + 84], fill=col + (255,))
                dl.text((150, y + 8), lab, font=OSW(58, 600), fill=(NAVY if col == YEL else WHITE) + (255,))
        img.alpha_composite(lay)
    return img

# ---------------------------------------------------------------- captions (news-style white plates, yellow keywords)
def build_caps():
    caps = []
    for sd in SEGMENTS:
        ws = []; run = False
        for w in SEGT[sd["id"]]["words"]:
            txt = w["w"].strip(); core = txt.rstrip(".,?!")
            single = len(core) == 1 and core.isalpha() and core.isupper()
            if ws and run and (single or core[:1].isdigit()):
                sep = " " if ws[-1][0] == "GTA" and core[:1].isdigit() else ""
                ws[-1] = (ws[-1][0] + sep + txt.upper(), ws[-1][1], w["b"], True); run = not core[:1].isdigit(); continue
            run = single and core == "G"
            if ws and ws[-1][0] == "GTA" and core.lower() in ("six", "five"):
                ws[-1] = ("GTA " + {"six": "6", "five": "5"}[core.lower()] + txt[len(core):].upper(), ws[-1][1], w["b"], True); continue
            ws.append((txt.upper(), w["a"], w["b"], clean(txt) in sd["hl"]))
        g = []
        for k, x in enumerate(ws):
            g.append(x)
            if x[0][-1] in ".,?!" or len(g) >= 3 or sum(len(q[0]) for q in g) > 15 or k == len(ws) - 1: caps.append(g); g = []
    out = []
    for i, g in enumerate(caps):
        a = g[0][1] - .05; b = caps[i + 1][0][1] - .05 if i + 1 < len(caps) else g[-1][2] + .45
        out.append((a, min(b, g[-1][2] + .45), g))
    return out
CAPS = build_caps()
def caption(img, t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return
    a, b, g = cur[0]; age = t - a; d = ImageDraw.Draw(img)
    f = OSW(96, 700); sp = 24
    words = [w[0] for w in g]
    while sum(tw_(d, x, f) for x in words) + sp * (len(words) - 1) > W - 120: f = OSW(f.size - 4, 700)
    total = sum(tw_(d, x, f) for x in words) + sp * (len(words) - 1); x = (W - total) / 2; y = 1250
    lay = rgba(); dl = ImageDraw.Draw(lay); k = eout(age / .12)
    for i, (txt, wa, wb, hl) in enumerate(g):
        spoken = t >= wa - .03; nxt = g[i + 1][1] if i + 1 < len(g) else b; active = spoken and t < nxt
        ww = tw_(dl, txt, f)
        if spoken:
            plate = YEL if hl else WHITE
            dl.rectangle([x - 10, y - 4 + (1 - k) * 20, x + ww + 10, y + f.size * 1.32 + (1 - k) * 20], fill=plate + (255,))
            dl.text((x, y + (1 - k) * 20), txt, font=f, fill=NAVY + (255,))
            if active: dl.rectangle([x - 10, y + f.size * 1.32, x + ww + 10, y + f.size * 1.32 + 10], fill=RED + (255,))
        else:
            dl.text((x, y), txt, font=f, fill=(255, 255, 255, 110))
        x += ww + sp
    img.alpha_composite(lay)

# ---------------------------------------------------------------- broadcast chrome
CHYRON = {"hook": "GTA 6 · BILLION-DOLLAR GAME BEFORE LAUNCH", "s1": "~15.88M DIGITAL PRE-ORDERS (ESTIMATE)", "s2": "~$1.54B IN PRE-ORDERS (ESTIMATE)",
          "s3": "PS5 ACCOUNTS FOR ~75% OF PRE-ORDERS", "s4": "ROCKSTAR / TAKE-TWO: NO OFFICIAL FIGURES", "s5": "CAN GTA 6 BEAT GTA V'S $800M DAY ONE?", "outro": "COMMENT YOUR DAY-ONE GUESS"}
TICKER = "   ///   GTA 6 LAUNCHES NOV 19 AT MIDNIGHT LOCAL TIME   ///   PRE-ORDER FIGURES ARE SENSOR TOWER ESTIMATES, NOT OFFICIAL   ///   GTA V: $800M+ ON DAY ONE (2013)   ///   PS5 & XBOX SERIES X|S   ///   COMMENT YOUR DAY-ONE GUESS  "
def chrome(img, t, seg):
    d = ImageDraw.Draw(img)
    # top bar
    d.rectangle([0, 0, W, 150], fill=DARK + (235,))
    on = int(t * 2) % 2 == 0
    d.rectangle([50, 60, 190, 112], fill=RED if on else (150, 12, 16)); d.text((72, 62), "LIVE", font=OSW(40, 700), fill=WHITE)
    d.text((215, 60), "GTA6 SECRETS", font=OSW(40, 700), fill=WHITE); d.text((470, 66), "NEWS", font=OSW(34, 500), fill=YEL)
    d.text((W - 240, 66), f"{int(18 + t // 60) % 24:02d}:{int(t) % 60:02d} ET", font=RC(34, 600), fill=(200, 210, 230))
    d.rectangle([0, 146, W * min(1, t / TOTAL), 150], fill=YEL)
    # chyron (lower third)
    y = 1440; label = CHYRON.get(seg, "")
    fb = OSW(44, 700); bw = tw_(d, "BREAKING", fb) + 44
    d.rectangle([0, y, bw, y + 86], fill=RED); d.text((22, y + 16), "BREAKING", font=fb, fill=WHITE)
    d.rectangle([bw, y, W, y + 86], fill=WHITE + (245,))
    f = RC(40, 800)
    while tw_(d, label, f) > W - bw - 40: f = RC(f.size - 2, 800)
    d.text((bw + 20, y + 20), label, font=f, fill=NAVY)
    # ticker
    yt = y + 86; d.rectangle([0, yt, W, yt + 60], fill=NAVY); d.rectangle([0, yt, 150, yt + 60], fill=YEL); d.text((22, yt + 10), "TICKER", font=OSW(34, 700), fill=NAVY)
    ft = RC(34, 700); tl = tw_(d, TICKER, ft); off = (t * 170) % tl
    tick = rgba(W - 150, 60); dt = ImageDraw.Draw(tick)
    for k in range(3): dt.text((-off + k * tl, 10), TICKER, font=ft, fill=WHITE + (255,))
    img.alpha_composite(tick, (150, yt))
    d.text((40, H - 330), "IMAGES © ROCKSTAR GAMES · FAN NEWS, NOT AFFILIATED", font=RC(22, 600), fill=(170, 180, 200))

def frame(t, fi):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); a, b, name, seg = SHOTS[i]; age = t - a
    img = draw_shot(name, t, a, b)
    # broadcast "wipe": a red + yellow bar sweeping on each cut
    if i and age < .22:
        k = eout(age / .22); lay = rgba(); dl = ImageDraw.Draw(lay); x = -300 + (W + 600) * k
        dl.rectangle([x - 220, 0, x, H], fill=RED + (255,)); dl.rectangle([x, 0, x + 30, H], fill=YEL + (255,))
        img.alpha_composite(lay)
    caption(img, t); chrome(img, t, seg)
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    for h in (0.0, st("hook2"), st("dollars") + 1.6, st("unconfirmed") + .1, st("record") + .6):
        if 0 <= t - h < .1: arr += 255 * (1 - (t - h) / .1) * .5
    if t < .2: arr *= ease(t / .2)
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
