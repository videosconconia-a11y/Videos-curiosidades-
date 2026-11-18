# "The 'Before GTA 6' Era Is OVER" — MEMORY TAPE identity: nostalgic end-of-an-era tribute.
# Faded sepia memories (polaroids, typewriter dates, camcorder date stamp, film grain, light leaks) that burst into
# full colour on "it's finally here". Captions in the trending bold-white Shorts style with yellow keyword plates.
# Official Rockstar images only (assets/official, not in git). Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS = 1080, 1920, 30
FD = os.path.join(HERE, "fonts")
@lru_cache(maxsize=64)
def MS(s, w=800):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
@lru_cache(maxsize=16)
def SERIF(s, italic=True): return ImageFont.truetype(os.path.join(FD, "DMSerifDisplay-Italic.ttf" if italic else "DMSerifDisplay-Regular.ttf"), s)
@lru_cache(maxsize=16)
def ANTON(s): return ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), s)
YEL = (255, 214, 0); RED = (230, 40, 40); CREAM = (245, 236, 215); GREEN = (60, 210, 110); ORANGE = (255, 150, 40)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word, nth=0):
    hits = [w["a"] for w in SEGT[seg]["words"] if clean(w["w"]) == word]
    return hits[nth]
def build_shots():
    out = []; segs = TM["segments"]
    for i, (sd, st_) in enumerate(zip(SEGMENTS, segs)):
        s0 = 0.0 if i == 0 else st_["a"] - 0.1
        s1 = segs[i + 1]["a"] - 0.1 if i + 1 < len(segs) else TOTAL
        starts = [(s0 if c is None else word_time(sd["id"], c) - 0.08, n) for n, c in sd["shots"]]
        for j, (a, n) in enumerate(starts):
            out.append((a, starts[j + 1][0] if j + 1 < len(starts) else s1, n, sd["id"]))
    return out
SHOTS = build_shots()
def st(n): return [s[0] for s in SHOTS if s[2] == n][0]
COLOR_AT = st("here")

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))
def text_c(d, cx, y, s, f, fill, **kw): d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill, **kw)

@lru_cache(maxsize=12)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + ".*jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2200 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im
def crop(key, w, h, p, cx=.5, cy=.5, z0=1.0, z1=1.1):
    im = load(key); z = z0 + (z1 - z0) * (ease(p) * .6 + p * .4)
    ch = im.height / z; cw = ch * w / h
    if cw > im.width: cw = im.width / z; ch = cw * h / w
    x = min(max(cx * im.width, cw / 2), im.width - cw / 2); y = min(max(cy * im.height, ch / 2), im.height - ch / 2)
    return im.resize((w, h), Image.BILINEAR, box=(x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2))
def full(key, p, cx=.5, cy=.5, z0=1.0, z1=1.12): return crop(key, W, H, p, cx, cy, z0, z1).convert("RGBA")

# dark paper background for "memory" cards
_rng = np.random.default_rng(3)
_paper = np.full((H // 4, W // 4, 3), (24, 20, 17), np.float32) + _rng.normal(0, 4, (H // 4, W // 4, 1))
PAPER = to_img(_paper).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2)).convert("RGBA")

def polaroid(img, key, cx, cy, w, h, rot, p, k=1.0, cxf=.5, label=None, gray=False):
    """white-bordered photo with shadow; k = drop-in progress"""
    if k <= 0: return
    ph = crop(key, w, h, p, cxf, .5, 1.0, 1.08)
    if gray: ph = Image.fromarray(np.repeat(np.asarray(ph.convert("L"))[..., None], 3, 2))
    b, bb = int(w * .05), int(w * .2 if label else w * .05)
    card = Image.new("RGBA", (w + 2 * b, h + b + bb), (246, 242, 232, 255)); card.paste(ph, (b, b))
    if label:
        d = ImageDraw.Draw(card); f = SERIF(int(w * .1)); text_c(d, card.width / 2, h + b + bb * .18, label, f, (40, 36, 34))
    s = 1.25 - .25 * eout(k)
    card = card.resize((int(card.width * s), int(card.height * s)), Image.BILINEAR).rotate(rot + (1 - eout(k)) * 12, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); sh.putalpha(card.getchannel("A").point(lambda v: int(v * .55)))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    a = min(1, k * 3)
    if a < 1: card.putalpha(card.getchannel("A").point(lambda v: int(v * a))); sh.putalpha(sh.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(sh, (int(cx - card.width / 2 + 14), int(cy - card.height / 2 + 22)))
    img.alpha_composite(card, (int(cx - card.width / 2), int(cy - card.height / 2)))

def strike(img, x0, y0, x1, y1, k, col=RED, width=18):
    if k <= 0: return
    lay = rgba(); d = ImageDraw.Draw(lay); e = eout(k)
    d.line([(x0, y0), (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)], fill=col + (255,), width=width)
    img.alpha_composite(lay)

def typewriter(d, cx, y, s, f, age, cps=18, fill=CREAM):
    n = max(0, min(len(s), int(age * cps))); sub = s[:n]
    x = cx - d.textlength(s, font=f) / 2; d.text((x, y), sub, font=f, fill=fill)
    if n < len(s) and int(age * 4) % 2 == 0: d.rectangle([x + d.textlength(sub, font=f) + 6, y + 10, x + d.textlength(sub, font=f) + 14, y + f.size], fill=fill)
    return n

def counter(v, age, dur): return v * eout(age / dur)

# ---------------------------------------------------------------- shots
def draw_shot(name, t, a, b):
    age = t - a; p = (t - a) / max(b - a, 1e-3)
    if name == "hook":
        img = full("Jason_Lucia_Rooftop_portrait", p, .5, .45, 1.15, 1.0); d = ImageDraw.Draw(img)
        f = ANTON(170); y = 330
        lay = rgba(); dl = ImageDraw.Draw(lay)
        text_c(dl, W / 2, y, "\"BEFORE", f, (255, 255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0, 255))
        text_c(dl, W / 2, y + 190, "GTA 6\"", f, (255, 255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0, 255))
        img.alpha_composite(lay)
        sw = word_time("hook", "officially") - a
        strike(img, 150, y + 300, W - 150, y + 90, (age - sw) / .3, width=26)
        if age > sw + .35:
            k = back(min(1, (age - sw - .35) / .25)); f2 = ANTON(int(120 * k) + 1)
            lay = rgba(); dl = ImageDraw.Draw(lay)
            text_c(dl, W / 2, 900, "ERA: OVER", f2, RED + (255,), stroke_width=6, stroke_fill=(0, 0, 0, 255))
            img.alpha_composite(lay.rotate(-5, center=(W / 2, 960), resample=Image.BICUBIC))
        return img
    if name == "date2013":
        img = PAPER.copy(); d = ImageDraw.Draw(img)
        text_c(d, W / 2, 330, "2013", ANTON(420), (60, 52, 46))
        typewriter(d, W / 2, 800, "September 17, 2013", SERIF(104), age, 16)
        if age > 1.6:
            k = eout((age - 1.6) / .4); text_c(d, W / 2, 960 + (1 - k) * 30, "GTA V RELEASES", MS(54, 800), (255, 255, 255, int(255 * k)))
        return img
    if name == "waiting":
        img = PAPER.copy(); d = ImageDraw.Draw(img)
        yr = 2013 + min(8, int(age / max(b - a, .1) * 9.5))
        text_c(d, W / 2, 230, str(yr), ANTON(300), (255, 255, 255))
        text_c(d, W / 2, 610, "STILL WAITING…", MS(44, 800), (200, 190, 175))
        polaroid(img, "Vice_City_15", W / 2, 1150, 620, 620, -4, p, age / .4, .55, gray=True)
        return img
    if name == "confirm":
        img = PAPER.copy(); d = ImageDraw.Draw(img)
        polaroid(img, "GTAVI_Official_Cover_Art_Landscape", W / 2, 640, 760, 560, 3, p, age / .4, .5, label="Feb 4, 2022")
        if age > .9:
            k = back(min(1, (age - .9) / .25)); lay = rgba(); dl = ImageDraw.Draw(lay); f = ANTON(int(110 * k) + 1)
            bw = dl.textlength("CONFIRMED", font=f) + 60
            dl.rounded_rectangle([W / 2 - bw / 2, 1040, W / 2 + bw / 2, 1040 + 150 * k], 14, outline=GREEN + (255,), width=10)
            text_c(dl, W / 2, 1050, "CONFIRMED", f, GREEN + (255,))
            img.alpha_composite(lay.rotate(4, center=(W / 2, 1110), resample=Image.BICUBIC))
        return img
    if name == "trailer":
        img = PAPER.copy(); d = ImageDraw.Draw(img)
        polaroid(img, "trailer-1", W / 2, 600, 820, 560, -2, p, age / .4, .5, label="Trailer 1 · Dec 2023")
        lay = rgba(); dl = ImageDraw.Draw(lay); cx, cy = W / 2, 560
        dl.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=(0, 0, 0, 150)); dl.polygon([(cx - 22, cy - 38), (cx - 22, cy + 38), (cx + 40, cy)], fill=(255, 255, 255, 230))
        img.alpha_composite(lay)
        sv = word_time("s3", "ninety") - a
        if age > sv - .2:
            v = counter(90421491, age - sv + .2, 1.4); d = ImageDraw.Draw(img)
            text_c(d, W / 2, 1010, f"{v:,.0f}", ANTON(150), (255, 255, 255))
            text_c(d, W / 2, 1180, "VIEWS IN 24 HOURS", MS(48, 800), YEL)
        return img
    if name == "record":
        img = full("trailer-1", p, .5, .5, 1.25, 1.35)
        img = Image.fromarray(np.uint8(np.asarray(img, np.float32) * np.array([.45, .45, .45, 1])), "RGBA")
        k = back(min(1, age / .3)); r = int(250 * k)
        lay = rgba(); dl = ImageDraw.Draw(lay); cx, cy = W / 2, 620
        if r > 2:
            dl.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(212, 170, 60, 255), outline=(255, 230, 140, 255), width=12)
            dl.ellipse([cx - r * .82, cy - r * .82, cx + r * .82, cy + r * .82], outline=(140, 100, 20, 255), width=6)
            if k > .7:
                text_c(dl, cx, cy - 130, "WORLD", ANTON(110), (40, 26, 0, 255)); text_c(dl, cx, cy - 10, "RECORD", ANTON(110), (40, 26, 0, 255))
        img.alpha_composite(lay)
        if age > .4:
            d = ImageDraw.Draw(img); text_c(d, W / 2, 920, "Most viewed non-music video in 24h", MS(40, 700), (255, 255, 255))
            text_c(d, W / 2, 975, "Guinness World Records · Dec 2023", MS(32, 600), (210, 200, 180))
        return img
    if name == "delays":
        img = PAPER.copy()
        t1, t2, t3 = word_time("s4", "fall") - a, word_time("s4", "may") - a, word_time("s4", "november") - a
        polaroid(img, "Leonida_Keys_01", 330, 520, 440, 380, -7, p, (age - t1 + .2) / .35, .5, label="Fall 2025", gray=True)
        polaroid(img, "Vice_City_01", 760, 690, 440, 380, 6, p, (age - t2 + .2) / .35, .5, label="May 26, 2026", gray=True)
        polaroid(img, "Grassrivers_04", W / 2, 1180, 520, 420, -2, p, (age - t3 + .15) / .35, .5, label="Nov 19, 2026")
        strike(img, 120, 380, 560, 720, (age - t1 - .35) / .25); strike(img, 560, 560, 990, 860, (age - t2 - .35) / .25)
        if age > t3 + .5:
            lay = rgba(); dl = ImageDraw.Draw(lay); k = eout((age - t3 - .5) / .4)
            dl.arc([W / 2 - 360, 1340, W / 2 + 360, 1560], 200, 200 + 340 * k, fill=GREEN + (255,), width=12)
            img.alpha_composite(lay)
        if age < t1 + .4:
            k = back(min(1, age / .25)) * (1 - ease((age - t1) / .4)); lay = rgba(); dl = ImageDraw.Draw(lay); f = ANTON(int(190 * max(k, .01)) + 1)
            bw = dl.textlength("DELAYED", font=f) + 60
            dl.rounded_rectangle([W / 2 - bw / 2, 620, W / 2 + bw / 2, 640 + f.size * 1.25], 16, outline=RED + (255,), width=12)
            text_c(dl, W / 2, 640, "DELAYED", f, RED + (255,))
            img.alpha_composite(lay.rotate(-8, center=(W / 2, 760), resample=Image.BICUBIC))
        return img
    if name == "wall":
        img = PAPER.copy(); keys = ["Vice_City_08", "Mount_Kalaga_National_Park_04", "Vice_City_02", "Port_Gellhorn_07", "Leonida_Keys_05",
                                    "trailer-2", "Jason_and_Lucia_16", "Vice_City_15", "Grassrivers_04", "Leonida_Keys_01"]
        rng = np.random.default_rng(11)
        for i, k_ in enumerate(keys):
            x, y = rng.uniform(170, W - 170), rng.uniform(260, H - 360); rot = rng.uniform(-14, 14)
            polaroid(img, k_, x, y, 330, 280, rot, p, (age - i * .22) / .3, .5, gray=True)
        lay = rgba(); dl = ImageDraw.Draw(lay); dl.rectangle([0, 700, W, 1130], fill=(0, 0, 0, 215)); img.alpha_composite(lay)
        d = ImageDraw.Draw(img); v = counter(4811, age, 2.6)
        text_c(d, W / 2, 700, f"{v:,.0f}", ANTON(300), (255, 255, 255))
        text_c(d, W / 2, 1040, "DAYS OF \"BEFORE GTA 6\"", MS(54, 900), YEL)
        return img
    if name == "here":
        return full("GTAVI_Launch_Trailer_poster", p, .5, .5, 1.0, 1.1)
    if name == "outro":
        img = full("Jason_and_Lucia_16", p, .55, .5, 1.05, 1.15); d = ImageDraw.Draw(img)
        if age > .2:
            k = eout((age - .2) / .5); text_c(d, W / 2, 330 + (1 - k) * 30, "WHERE WERE YOU", ANTON(130), (255, 255, 255, int(255 * k)), stroke_width=6, stroke_fill=(0, 0, 0, 200))
            text_c(d, W / 2, 480 + (1 - k) * 30, "IN 2013?", ANTON(170), YEL + (int(255 * k),), stroke_width=6, stroke_fill=(0, 0, 0, 200))
        return img
    raise ValueError(name)

# ---------------------------------------------------------------- grading + overlays
YY, XX = np.mgrid[0:H:4, 0:W:4]
VIG = np.asarray(to_img(np.clip(1.15 - (((XX - W / 2) / (W * .65)) ** 2 + ((YY - H / 2) / (H * .62)) ** 2) * .5, .35, 1) * 255).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
GRAIN = [np.random.default_rng(k).normal(0, 9, (H // 2, W // 2)).astype(np.float32) for k in range(6)]
def sepia(a, amt):
    l = a @ np.array([.299, .587, .114], np.float32)
    s = np.stack([l * 1.07 + 8, l * .95 + 2, l * .78 - 6], -1)
    return a * (1 - amt) + s * amt
def grade(arr, t):
    if t < COLOR_AT:
        arr = sepia(arr, .8); arr = (arr - 128) * .92 + 124
    else:
        k = ease((t - COLOR_AT) / .5)
        arr = sepia(arr, .8 * (1 - k)); sat = arr.mean(-1, keepdims=True); arr = sat + (arr - sat) * (1 + .18 * k)
        if t - COLOR_AT < .35: arr = arr + 255 * (1 - (t - COLOR_AT) / .35) * .7
    g = GRAIN[int(t * FPS) % 6]; g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    amt = 1.0 if t < COLOR_AT else .45
    arr = arr + g * amt
    # warm light leak drifting
    lk = math.sin(t * .9) * .5 + .5
    arr[..., 0] += 30 * lk * np.exp(-((np.arange(W) - W * (.15 + .7 * lk)) / 420) ** 2)[None, :]
    arr[..., 1] += 12 * lk * np.exp(-((np.arange(W) - W * (.15 + .7 * lk)) / 420) ** 2)[None, :]
    return arr * VIG

def camcorder(img, t):
    """camcorder-style date stamp that follows the story"""
    i, (a, b, name, seg) = shot_at(t)
    stamp = {"hook": "NOV 19 2026", "s1": "SEP 17 2013", "s2": "FEB 04 2022", "s3": "DEC 04 2023", "s4": "NOV 06 2025", "s5": "", "s6": "NOV 19 2026", "outro": "NOV 19 2026"}[seg]
    d = ImageDraw.Draw(img)
    if int(t * 2) % 2 == 0 and t < COLOR_AT: d.ellipse([60, 92, 92, 124], fill=(230, 30, 30))
    if t < COLOR_AT: d.text((108, 86), "PLAY", font=MS(40, 800), fill=(255, 255, 255))
    if stamp: d.text((W - 60 - d.textlength(stamp, font=MS(40, 800)), 86), stamp, font=MS(40, 800), fill=ORANGE, stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((60, 150), "IMAGES © ROCKSTAR GAMES · FAN-MADE", font=MS(22, 600), fill=(230, 225, 215))

def build_caps():
    groups = []
    for seg in TM["segments"]:
        hl = [s for s in SEGMENTS if s["id"] == seg["id"]][0]["hl"]; cur = []
        for i, w in enumerate(seg["words"]):
            cur.append(dict(w, hl=clean(w["w"]) in hl))
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(seg["words"]) - 1:
                groups.append((cur, seg["id"])); cur = []
    return groups
CAPS = build_caps()
NUM = {"seventeenth": "17TH", "thirteen.": "2013.", "twenty-two.": "2022.", "twenty-three.": "2023.", "twenty-five.": "2025.", "twenty-six.": "2026.",
       "ninety": "90", "twenty-four": "24", "six": "6", "six.": "6.", "five": "5", "four": "4,811", "five.": "5."}
def disp(w, prev):
    lw = w.lower()
    if lw in ("twenty",) : return ""
    if lw in ("thousand", "eight", "hundred", "and", "eleven") and prev == "4,811": return None
    return NUM.get(lw, w).upper()
def caption(img, t):
    g = None
    for ws, sid in CAPS:
        if ws[0]["a"] - .05 <= t: g = (ws, sid)
    if g is None: return
    ws, sid = g
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if t > ws[-1]["b"] + .5 or (nxt and t >= nxt[0] - .12): return
    toks = []; prev = None
    for w in ws:
        s = disp(w["w"], prev)
        if s is None: continue
        if s == "": continue
        toks.append((w, s)); prev = s
    if not toks: return
    y = 1330
    f = MS(84, 900); d = ImageDraw.Draw(img)
    widths = [d.textlength(s, font=f) for _, s in toks]; sp = 26
    while sum(widths) + sp * (len(toks) - 1) > W - 100:
        f = MS(f.size - 4, 900); widths = [d.textlength(s, font=f) for _, s in toks]
    x = (W - sum(widths) - sp * (len(toks) - 1)) / 2
    age = t - ws[0]["a"]; pop = back(min(1, age / .15)) if age > 0 else 0
    lay = rgba(); dl = ImageDraw.Draw(lay)
    for (w, s_), wd in zip(toks, widths):
        on = w["a"] - .03 <= t; yy = y + (1 - pop) * 26
        if w["hl"] and on:
            dl.rounded_rectangle([x - 12, yy - 2, x + wd + 12, yy + f.size + 16], 14, fill=YEL + (255,)); dl.text((x, yy), s_, font=f, fill=(0, 0, 0))
        else:
            dl.text((x, yy), s_, font=f, fill=(255, 255, 255, 255 if on else 120), stroke_width=8, stroke_fill=(0, 0, 0, 255 if on else 100))
        x += wd + sp
    img.alpha_composite(lay)

def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); return i, SHOTS[i]
def frame(t, fi=None):
    i, (a, b, name, seg) = shot_at(t)
    img = draw_shot(name, t, a, b); age = t - a
    if i and age < .25 and name != "here":                     # film-burn dissolve between memories
        pa, pb, pn, _ = SHOTS[i - 1]; prev = draw_shot(pn, a - 1e-3, pa, pb); img = Image.blend(prev, img, ease(age / .25))
    arr = grade(np.asarray(img.convert("RGB"), np.float32), t)
    if t < .25: arr *= ease(t / .25)
    if TOTAL - t < .4: arr *= ease((TOTAL - t) / .4)
    out = to_img(arr).convert("RGBA")
    camcorder(out, t); caption(out, t)
    return out.convert("RGB")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
