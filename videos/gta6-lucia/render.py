# "GTA 6 WEAPONS ARE GETTING CRAZY!" — 1080x1920 Short built on official Rockstar Games images.
# Camera = animated crop on the official image (zoom-to-detail); overlays = red circles, arrows, HUD weapon cards,
# freeze-frame reveal, word-by-word captions. Palette: black / red / white / yellow.
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
ANTON = lambda s: ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), s)
def MONT(s, w=800):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
RED = (255, 38, 48); YEL = (255, 212, 0); WHITE = (255, 255, 255); BLACK = (0, 0, 0); GREEN = (70, 230, 120)

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

# ---------------------------------------------------------------- captions (spelled letters merged: G T A -> GTA, E S 9 -> ES9)
def build_caps():
    caps = []
    for sd in SEGMENTS:
        ws = []; run = False
        for w in SEGT[sd["id"]]["words"]:
            txt = w["w"].strip(); core = txt.rstrip(".,?!")
            single = len(core) == 1 and core.isalpha() and core.isupper()
            if ws and run and (single or core[:1].isdigit()):
                sep = " " if ws[-1][0] == "GTA" and core[:1].isdigit() else ""
                ws[-1] = (ws[-1][0] + sep + txt.upper(), ws[-1][1], w["b"], True)
                run = not core[:1].isdigit(); continue
            run = single and core in ("G", "E", "K")
            up = txt.upper(); key = up.rstrip(".,?!")
            if key in DISPLAY: up = DISPLAY[key] + up[len(key):]
            ws.append((up, w["a"], w["b"], clean(txt) in sd["hl"]))
        for k, x in enumerate(ws):   # spelled tokens -> highlight
            if x[0].rstrip(".,?!") in ("GTA 6",): ws[k] = (x[0], x[1], x[2], True)
        g = []
        for k, x in enumerate(ws):
            g.append(x)
            if x[0][-1] in ".,?!:" or len(g) >= 3 or sum(len(q[0]) for q in g) > 14 or k == len(ws) - 1:
                caps.append(g); g = []
    out = []
    for i, g in enumerate(caps):
        a = g[0][1] - 0.05; b = caps[i + 1][0][1] - 0.05 if i + 1 < len(caps) else g[-1][2] + 0.45
        out.append((a, min(b, g[-1][2] + 0.45), g))
    return out
CAPS = build_caps()

# ---------------------------------------------------------------- helpers
def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))
def glow_paste(img, lay, r=14, k=1.0):
    g = lay.filter(ImageFilter.GaussianBlur(r))
    if k != 1: a = np.asarray(g).astype(np.float32); a[..., 3] *= k; g = to_img(a)
    img.alpha_composite(g); img.alpha_composite(lay)
def tsize(d, s, f): b = d.textbbox((0, 0), s, font=f); return b[2] - b[0], b[3] - b[1], b[0], b[1]
def text_c(d, cx, cy, s, f, fill, stroke=0, sc=(0, 0, 0, 255)):
    w, h, ox, oy = tsize(d, s, f); d.text((cx - w / 2 - ox, cy - h / 2 - oy), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sc)
def scaled(lay, s, cx, cy):
    s = max(.02, s)
    if abs(s - 1) < 1e-3: return lay
    big = lay.resize((max(1, int(W * s)), max(1, int(H * s))), Image.BICUBIC); out = rgba(); out.paste(big, (int(cx - cx * s), int(cy - cy * s)), big); return out

@lru_cache(maxsize=6)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + "*.jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2300 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im

class Cam:
    """crop of an official image: (cx, cy, zoom) with cx,cy in 0..1 image coords; zoom 1 = full image height."""
    def __init__(self, key, c0, c1): self.key, self.c0, self.c1 = key, c0, c1
    def box(self, p):
        im = load(self.key); q = ease(p) * .7 + p * .3
        cx = self.c0[0] + (self.c1[0] - self.c0[0]) * q; cy = self.c0[1] + (self.c1[1] - self.c0[1]) * q
        z = self.c0[2] * (self.c1[2] / self.c0[2]) ** q
        ch = im.height / z; cw = ch * W / H
        if cw > im.width: cw = im.width / z; ch = cw * H / W
        x = min(max(cx * im.width, cw / 2), im.width - cw / 2); y = min(max(cy * im.height, ch / 2), im.height - ch / 2)
        return (x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2)
    def render(self, p, dark=1.0, blur=0):
        im = load(self.key); b = self.box(p)
        v = im.resize((W, H), Image.BILINEAR, box=b).convert("RGBA")
        if blur: v = v.filter(ImageFilter.GaussianBlur(blur))
        if dark != 1: a = np.asarray(v).astype(np.float32); a[..., :3] *= dark; v = to_img(a)
        return v
    def pt(self, p, u, v):
        """image point (0..1) -> screen"""
        im = load(self.key); b = self.box(p)
        return (u * im.width - b[0]) / (b[2] - b[0]) * W, (v * im.height - b[1]) / (b[3] - b[1]) * H

def red_circle(img, cx, cy, rx, ry, p, col=RED, wdt=12):
    lay = rgba(); d = ImageDraw.Draw(lay); n = 64; k = int(n * 1.12 * ease(p))
    pts = [(cx + rx * (1 + .05 * math.sin(i * .8)) * math.cos(-2 + i / n * 2 * math.pi * 1.1),
            cy + ry * (1 + .05 * math.cos(i * 1.2)) * math.sin(-2 + i / n * 2 * math.pi * 1.1)) for i in range(k)]
    if len(pts) > 1: d.line(pts, fill=col + (255,), width=wdt, joint="curve")
    glow_paste(img, lay, 10, .9)
def arrow(img, x0, y0, x1, y1, p, col=YEL, wdt=14):
    p = eout(p)
    if p <= 0: return
    xe, ye = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    lay = rgba(); d = ImageDraw.Draw(lay); d.line([x0, y0, xe, ye], fill=col + (255,), width=wdt)
    a = math.atan2(ye - y0, xe - x0); hd = 46
    d.polygon([(xe + 12 * math.cos(a), ye + 12 * math.sin(a)), (xe - hd * math.cos(a - .5), ye - hd * math.sin(a - .5)), (xe - hd * math.cos(a + .5), ye - hd * math.sin(a + .5))], fill=col + (255,))
    glow_paste(img, lay, 8, .6)
def stamp(img, cx, cy, s, f, col, age, rot=-5, box=True, fill=None):
    if age < 0: return
    sc = 1 + 1.3 * (1 - eout(age / .16)) if age < .16 else 1
    lay = rgba(); d = ImageDraw.Draw(lay); w, h, _, _ = tsize(d, s, f)
    if box: d.rectangle([cx - w / 2 - 34, cy - h / 2 - 24, cx + w / 2 + 34, cy + h / 2 + 24], fill=fill, outline=col + (255,), width=10)
    text_c(d, cx, cy, s, f, (WHITE if fill else col) + (255,), 0 if fill else 8)
    glow_paste(img, scaled(lay.rotate(rot, Image.BICUBIC, center=(cx, cy)), sc, cx, cy), 12, .7)
def tag(d, x, y, s, col, tc=BLACK, f=None):
    f = f or MONT(30); tw = d.textlength(s, font=f); d.rectangle([x, y, x + tw + 28, y + 50], fill=col); d.text((x + 14, y + 8), s, font=f, fill=tc); return tw + 28
def weapon_card(img, age, num, name, sub, status="CONFIRMED", y=250, col=YEL):
    """HUD weapon card sliding in from the left"""
    if age < 0: return
    k = eout(age / .35); x0 = -700 + 760 * k
    lay = rgba(); d = ImageDraw.Draw(lay)
    d.rectangle([x0, y, x0 + 640, y + 230], fill=(0, 0, 0, 215)); d.rectangle([x0, y, x0 + 12, y + 230], fill=col + (255,))
    d.text((x0 + 36, y + 18), f"WEAPON {num:02d}", font=MONT(28), fill=col + (255,))
    f = ANTON(92)
    while d.textlength(name, font=f) > 580: f = ANTON(f.size - 4)
    d.text((x0 + 34, y + 54), name, font=f, fill=WHITE + (255,))
    d.text((x0 + 36, y + 178), sub, font=MONT(28, 700), fill=(220, 220, 220, 255))
    sw = d.textlength(status, font=MONT(24)) + 54
    d.rectangle([x0 + 640 - sw - 14, y + 18, x0 + 626, y + 56], fill=(GREEN if status == "CONFIRMED" else RED) + (255,))
    d.text((x0 + 640 - sw + 2, y + 24), status, font=MONT(24), fill=BLACK + (255,))
    if status == "CONFIRMED": d.line([(x0 + 626 - 26, y + 38), (x0 + 626 - 18, y + 47), (x0 + 626 - 6, y + 28)], fill=BLACK + (255,), width=5)
    img.alpha_composite(lay)
def brackets(d, x0, y0, x1, y1, col, L=50, w=6):
    for x, y, sx, sy in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([x, y, x + sx * L, y], fill=col, width=w); d.line([x, y, x, y + sy * L], fill=col, width=w)

# ---------------------------------------------------------------- shots
L = lambda n: f"Lucia_Caminos_{n:02d}"
CAMS = {
    "hook_face": Cam(L(13), (.30, .45, 1.6), (.26, .40, 1.15)),
    "hook_five": Cam(L(11), (.70, .45, 1.0), (.72, .42, 1.2)),
    "n1": Cam(L(1), (.65, .4, 1.1), (.65, .4, 1.25)),
    "father": Cam(L(1), (.62, .35, 1.0), (.66, .30, 1.3)),
    "punch": Cam(L(1), (.80, .50, 1.3), (.86, .52, 1.7)),
    "n2": Cam(L(5), (.60, .4, 1.1), (.60, .4, 1.25)),
    "prison": Cam(L(5), (.60, .30, 1.0), (.60, .50, 1.25)),
    "luck": Cam(L(14), (.30, .40, 1.0), (.40, .40, 1.2)),
    "n3": Cam("Vice_City_08", (.5, .5, 1.1), (.5, .5, 1.25)),
    "liberty": Cam("Vice_City_08", (.40, .5, 1.0), (.55, .45, 1.15)),
    "pool": Cam(L(2), (.55, .45, 1.0), (.55, .40, 1.2)),
    "real": Cam(L(3), (.30, .45, 1.0), (.32, .40, 1.2)),
    "n4": Cam("Jason_and_Lucia_17", (.45, .5, 1.1), (.45, .5, 1.25)),
    "duo": Cam("Jason_and_Lucia_17", (.25, .55, 1.0), (.27, .58, 1.15)),
    "worst": Cam("Jason_and_Lucia_14", (.5, .5, 1.0), (.5, .45, 1.25)),
    "plan": Cam(L(11), (.60, .45, 1.0), (.72, .40, 1.3)),
    "n5": Cam(L(13), (.3, .4, 1.3), (.3, .4, 1.4)),
    "trailer1": Cam("trailer-1", (.5, .5, 1.0), (.5, .42, 1.2)),
    "her_name": Cam(L(13), (.26, .42, 1.05), (.25, .40, 1.3)),
    "female_lead": Cam("Jason_Lucia_Rooftop_portrait", (.70, .45, 1.6), (.72, .48, 1.25)),
    "question": Cam("Jason_Lucia_Lock_And_Load_portrait", (.5, .5, 1.0), (.5, .45, 1.12)),
}
PTS = {"fist": (.88, .55), "face1": (.65, .25), "cuffs": (.58, .86), "face5": (.62, .13), "police": (.76, .50),
       "lucia17": (.25, .62), "jason17": (.66, .45), "face13": (.25, .40)}
NUMCOL = {1: YEL, 2: RED, 3: WHITE, 4: YEL, 5: RED}

def quote(img, age, text, src="— ROCKSTAR GAMES", y=300):
    if age < 0: return
    k = eout(age / .35); lay = rgba(); d = ImageDraw.Draw(lay)
    f = MONT(40, 700); words = text.split(); lines = []; cur = ""
    for w in words:
        if d.textlength(cur + " " + w, font=f) > 860: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    lines.append(cur); hgt = 70 + 54 * len(lines)
    d.rectangle([80, y, 1000, y + hgt], fill=(0, 0, 0, 205)); d.rectangle([80, y, 92, y + hgt], fill=YEL + (255,))
    d.text((112, y + 6), "\u201c", font=ANTON(80), fill=YEL + (255,))
    for i, ln in enumerate(lines): d.text((150, y + 26 + i * 54), ln, font=f, fill=WHITE + (255,))
    d.text((150, y + 30 + len(lines) * 54), src, font=MONT(28), fill=YEL + (255,))
    lay = lay.transform((W, H), Image.AFFINE, (1, 0, (1 - k) * -900, 0, 1, 0)); img.alpha_composite(lay)

def draw_shot(name, t, a, b, seg):
    p = (t - a) / max(1e-3, b - a); age = t - a
    cam = CAMS[name]
    isnum = name in ("n1", "n2", "n3", "n4", "n5")
    dark = .4 if isnum else {"liberty": .45, "question": .55, "trailer1": .9}.get(name, 1.0)
    img = cam.render(p, dark, 12 if isnum else 0); d = ImageDraw.Draw(img)
    P = lambda k: cam.pt(p, *PTS[k])
    if isnum:
        n = int(name[1]); col = NUMCOL[n]
        s_ = back(age / .35) if age < .35 else 1 + .02 * math.sin(age * 6)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        text_c(dl, W / 2, 560, "FACT", ANTON(140), WHITE + (255,), 8)
        text_c(dl, W / 2, 880, f"#{n}", ANTON(500), col + (255,), 14)
        if n == 5: text_c(dl, W / 2, 1180, "THE BIGGEST ONE", ANTON(90), WHITE + (255,), 8)
        glow_paste(img, scaled(lay, s_, W / 2, 800), 26, 1.0)
    elif name == "hook_face":
        stamp(img, W / 2, 330, "LUCIA", ANTON(240), WHITE, age - .05, rot=0, box=False)
        stamp(img, W / 2, 520, "CAMINOS", ANTON(120), YEL, age - .3, rot=0, box=False)
    elif name == "hook_five":
        stamp(img, W / 2, 400, "5 DETAILS", ANTON(170), WHITE, age - .05, rot=-4, fill=RED + (255,))
        stamp(img, W / 2, 600, "YOU MISSED", ANTON(120), YEL, age - .3, rot=0, box=False)
    elif name == "father":
        quote(img, age - .2, "Lucia's father taught her to fight as soon as she could walk.", y=260)
    elif name == "punch":
        x, y = P("fist"); red_circle(img, x, y, 230, 260, (age - .1) / .4)
        stamp(img, W / 2, 330, "TRAINED FIGHTER", ANTON(110), YEL, age - .2, rot=-4)
    elif name == "prison":
        stamp(img, W / 2, 330, "LEONIDA", ANTON(150), WHITE, age - .2, rot=0, box=False)
        stamp(img, W / 2, 490, "PENITENTIARY", ANTON(120), RED, age - .45, rot=-3, fill=RED + (255,))
        x, y = P("cuffs")
        if age > .8: red_circle(img, x, y, 170, 110, (age - .8) / .4)
    elif name == "luck":
        stamp(img, W / 2, 330, "NOT A LAWYER", ANTON(110), WHITE, age - .05, rot=0, box=False)
        stamp(img, W / 2, 500, "SHEER LUCK", ANTON(150), YEL, age - .65, rot=-5)
    elif name == "liberty":
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.rectangle([90, 420, 990, 980], fill=(0, 0, 0, 200), outline=YEL + (255,), width=6)
        text_c(dl, W / 2, 520, "WHERE IT STARTED", MONT(36), YEL + (255,))
        text_c(dl, W / 2, 660, "LIBERTY CITY", ANTON(170), WHITE + (255,), 8)
        text_c(dl, W / 2, 800, "THE CITY FROM GTA III & GTA IV", MONT(36), (230, 230, 230, 255))
        text_c(dl, W / 2, 900, "OFFICIAL · ROCKSTAR CHARACTER BIO", MONT(26), GREEN + (255,))
        img.alpha_composite(scaled(lay, back(age / .35), W / 2, 700))
    elif name == "pool":
        quote(img, age - .1, "Lucia wants the good life her mom has dreamed of since their days in Liberty City.", y=260)
    elif name == "real":
        stamp(img, W / 2, 330, "THE GOOD LIFE", ANTON(130), YEL, age - .1, rot=-3)
    elif name == "duo":
        quote(img, age - .1, "Meeting Lucia could be the best or worst thing to ever happen to him.", y=260)
        for k_, lab, col in (("lucia17", "LUCIA", YEL), ("jason17", "JASON", WHITE)):
            x, y = P(k_)
            if 0 < x < W and age > .7: tag(ImageDraw.Draw(img), x - 60, y + 220, lab, col)
    elif name == "worst":
        stamp(img, W / 2, 330, "BEST...", ANTON(140), WHITE, age - .05, rot=0, box=False)
        stamp(img, W / 2, 500, "OR WORST?", ANTON(140), RED, age - .45, rot=-4, fill=RED + (255,))
    elif name == "plan":
        stamp(img, W / 2, 330, "NO MATTER WHAT", ANTON(120), YEL, age - .2, rot=-3)
        stamp(img, W / 2, 480, "IT TAKES", ANTON(110), WHITE, age - .5, rot=0, box=False)
    elif name == "trailer1":
        tag(ImageDraw.Draw(img), 60, 250, "TRAILER 1 · DECEMBER 2023", YEL)
        stamp(img, W / 2, 1150, "THE FIRST WORDS?", ANTON(120), WHITE, age - .3, rot=0, box=False)
    elif name == "her_name":
        x, y = P("face13")
        if age > .25:
            k = eout((age - .25) / .35); r = 520 - 160 * k
            brackets(ImageDraw.Draw(img), x - r * .8, y - r, x + r * .8, y + r, RED + (255,), 80, 9)
            if age > .6: tag(ImageDraw.Draw(img), x - 150, y + r + 20, "ID MATCH · LUCIA CAMINOS", RED, WHITE)
        stamp(img, W / 2, 330, "\u201cLUCIA CAMINOS\u201d", ANTON(130), YEL, age - .5, rot=-3)
    elif name == "female_lead":
        stamp(img, W / 2, 330, "FIRST FEMALE LEAD", ANTON(115), WHITE, age - .1, rot=0, fill=RED + (255,))
        stamp(img, W / 2, 490, "OF A MODERN GTA", ANTON(100), YEL, age - .4, rot=0, box=False)
    elif name == "question":
        stamp(img, W / 2, 420, "MOST ICONIC", ANTON(150), YEL, age - .1, rot=-3)
        stamp(img, W / 2, 600, "GTA PROTAGONIST?", ANTON(120), WHITE, age - .35, rot=0, box=False)
        d = ImageDraw.Draw(img); yb = 1110 + 18 * math.sin(t * 9)
        d.polygon([(W / 2 - 60, yb), (W / 2 + 60, yb), (W / 2, yb + 80)], fill=YEL)
    return img

# ---------------------------------------------------------------- captions
def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, g = cur[0]; age = t - a
    pop = max(.3, back(age / .15, 2.0)) if age < .15 else 1.0
    f = ANTON(126); lay = rgba(W, 420); d = ImageDraw.Draw(lay)
    words = [w[0] for w in g]; sp = d.textlength(" ", font=f) * 1.5
    while sum(d.textlength(x, font=f) for x in words) + sp * (len(words) - 1) > W - 110:
        f = ANTON(f.size - 6); sp = d.textlength(" ", font=f) * 1.5
    x = (W - sum(d.textlength(x_, font=f) for x_ in words) - sp * (len(words) - 1)) / 2
    for i, (txt, wa, wb, hl) in enumerate(g):
        spoken = t >= wa - .03; nxt = g[i + 1][1] if i + 1 < len(g) else b; active = spoken and t < nxt
        col = (YEL if hl else WHITE) if spoken else (200, 200, 200); al = 255 if spoken else 140
        ww = d.textlength(txt, font=f)
        if active and hl: d.rectangle([x - 14, 70, x + ww + 14, 70 + f.size * 1.18], fill=RED + (255,)); col = WHITE
        d.text((x, 80), txt, font=f, fill=col + (al,), stroke_width=11, stroke_fill=(0, 0, 0, al)); x += ww + sp
    if pop != 1:
        nw, nh = int(W * pop), int(420 * pop); l2 = lay.resize((nw, nh), Image.BICUBIC); lay = rgba(W, 420); lay.paste(l2, ((W - nw) // 2, (420 - nh) // 2))
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(12)); shadow = rgba(W, 420); shadow.putalpha(sh.point(lambda v: int(v * .6)))
    out = rgba(W, 420); out.alpha_composite(shadow, (0, 8)); out.alpha_composite(lay); return out

# ---------------------------------------------------------------- compositing
YY, XX = np.mgrid[0:H, 0:W]
VIG = np.clip(1.18 - (((XX - W / 2) / (W * .6)) ** 2 + ((YY - H / 2) / (H * .6)) ** 2) * .55, .3, 1)[..., None].astype(np.float32)
GRAIN = [np.random.default_rng(k).standard_normal((H // 2, W // 2)).astype(np.float32) * 4 for k in range(4)]
SCAN = (np.sin(np.arange(H) * math.pi / 3) * .5 + .5).astype(np.float32)[:, None, None] * 6
def st(n): return [s[0] for s in SHOTS if s[2] == n][0]
IMPACTS = [0.0, st("hook_five"), st("n1"), st("n2"), st("n3"), st("n4"), st("n5"), st("punch"), st("prison") + .45, st("luck") + .65, st("worst") + .45, st("female_lead")]
FREEZE = st("her_name") + .45

def frame(t, fi):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); a, b, name, seg = SHOTS[i]; age = t - a
    img = draw_shot(name, t, a, b, seg)
    z = 1 + (.08 * math.exp(-age / .09) if i else 0)
    shake = 0.0
    for h in IMPACTS:
        if 0 <= t - h < .3: shake = max(shake, 22 * math.exp(-(t - h) / .07))
    z = max(z, 1 + 2.4 * shake / W)
    if z > 1.0005:
        cw, ch = W / z, H / z
        dx = max(-(W - cw) / 2, min((W - cw) / 2, shake * math.sin(fi * 2.3))); dy = max(-(H - ch) / 2, min((H - ch) / 2, shake * math.cos(fi * 3.1)))
        img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2 + dx, (H - ch) / 2 + dy, (W + cw) / 2 + dx, (H + ch) / 2 + dy))
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    if i and age < .13:
        o = int(16 * (1 - age / .13)); arr[..., 0] = np.roll(arr[..., 0], o, 1); arr[..., 2] = np.roll(arr[..., 2], -o, 1)
    # freeze-frame on the big reveal: desaturated, bright edge, scanline, "FREEZE" frame for 0.35 s
    fz = t - FREEZE
    if 0 <= fz < .35:
        gray = arr.mean(-1, keepdims=True); arr = gray * .6 + arr * .4; arr = arr * 1.15
    for h in IMPACTS:
        if 0 <= t - h < .12: arr = arr + 255 * (1 - (t - h) / .12) * .55
    arr = arr * VIG - SCAN + np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    out = to_img(arr).convert("RGBA"); d = ImageDraw.Draw(out)
    if 0 <= fz < .35:
        brackets(d, 40, 40, W - 40, H - 40, RED, 120, 10); d.text((70, 140), "FREEZE ■ 00:00:" + f"{int(fz * 100):02d}", font=MONT(30), fill=RED)
    # HUD
    brackets(d, 30, 30, W - 30, H - 30, (255, 255, 255, 130), 70, 5)
    if int(t * 2) % 2 == 0: d.ellipse([60, 66, 84, 90], fill=RED)
    d.text((98, 60), "CHARACTER FILE // LUCIA", font=MONT(26), fill=WHITE)
    d.text((W - 300, 60), f"REC {int(t // 60):02d}:{t % 60:05.2f}", font=MONT(26, 700), fill=YEL)
    d.text((60, H - 110), "IMAGES © ROCKSTAR GAMES · FAN-MADE", font=MONT(22, 700), fill=(230, 230, 230))
    d.rectangle([0, 0, W * min(1, t / TOTAL), 8], fill=RED)
    cap = caption_layer(t)
    if cap is not None: out.alpha_composite(cap, (0, 1300))
    return out.convert("RGB")

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
