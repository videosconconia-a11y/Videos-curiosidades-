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
            if x[0].rstrip(".,?!") in ("GTA 6", "ES9", "K17"): ws[k] = (x[0], x[1], x[2], True)
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
V = "ULTIMATE_EDITION_WEAPON_VARIANTS_01"; R = "ULTIMATE_EDITION_HAWK_AND_LITTLE_MORGAN_REVOLVERS_02"
PAT = "VINTAGE_VICE_CITY_WEAPON_PATTERN_01"; LOOK = "VINTAGE_VICE_CITY_PACK_EXCLUSIVE_LOOKS_03"
CAMS = {
    "hook_sparks": Cam("Jason_Duval_16", (.45, .5, 1.0), (.42, .48, 1.25)),
    "hook_names": Cam(V, (.30, .55, 1.0), (.30, .55, 1.12)),
    "pistols_wide": Cam(V, (.30, .55, 1.15), (.30, .55, 1.0)),
    "es9": Cam(V, (.30, .45, 1.0), (.33, .40, 1.35)),
    "k17": Cam(V, (.38, .66, 1.0), (.34, .68, 1.4)),
    "engraved": Cam(V, (.30, .58, 1.0), (.29, .62, 1.12)),
    "smg_car": Cam(PAT, (.62, .55, 1.0), (.70, .57, 1.3)),
    "smg_jason": Cam(LOOK, (.32, .40, 1.0), (.26, .33, 1.3)),
    "smg_pack": Cam("VINTAGE_VICE_CITY_PACK_01", (.45, .5, 1.0), (.45, .5, 1.15)),
    "night_rifle": Cam("Jason_Duval_05", (.38, .55, 1.0), (.33, .58, 1.3)),
    "trailer_rifle": Cam("Jason_Duval_17", (.40, .40, 1.0), (.45, .42, 1.2)),
    "lucia_pistol": Cam("Lucia_Caminos_13", (.55, .5, 1.0), (.74, .48, 1.25)),
    "shotgun": Cam("Jason_Lucia_Rooftop_portrait", (.55, .55, 1.0), (.72, .62, 1.6)),
    "tease": Cam(R, (.62, .5, 1.3), (.62, .5, 1.45)),
    "rev_reveal": Cam(R, (.62, .5, 1.5), (.55, .5, 1.0)),
    "rev_grips": Cam(R, (.68, .68, 1.3), (.70, .76, 1.75)),
    "rev_engraved": Cam(R, (.62, .48, 1.2), (.65, .52, 1.45)),
    "rev_scope": Cam(R, (.50, .26, 1.3), (.50, .18, 1.7)),
    "vercetti": Cam(R, (.6, .5, 1.05), (.6, .5, 1.2)),
    "tommy": Cam("Vice_City_01", (.5, .45, 1.0), (.5, .4, 1.2)),
    "question": Cam("Jason_Lucia_Lock_And_Load_portrait", (.5, .5, 1.0), (.5, .45, 1.12)),
}
PTS = {  # detail points (image 0..1 coords), measured on the official images
    "es9": (.38, .35), "k17": (.33, .66), "rose": (.28, .73), "smg_car": (.72, .56), "smg_jason": (.25, .30),
    "rifle17": (.47, .43), "heli1": (.08, .17), "heli2": (.55, .10), "lucia_gun": (.72, .47), "shotgun": (.80, .65),
    "grip": (.70, .77), "jduval": (.72, .385), "lcaminos": (.585, .65), "scope": (.50, .17),
}

def draw_shot(name, t, a, b, seg):
    p = (t - a) / max(1e-3, b - a); age = t - a
    cam = CAMS[name]
    dark = {"tease": .25, "vercetti": .45, "question": .55, "hook_names": .45, "smg_pack": .75}.get(name, 1.0)
    blur = {"tease": 6, "hook_names": 10}.get(name, 0)
    img = cam.render(p, dark, blur); d = ImageDraw.Draw(img)
    P = lambda k: cam.pt(p, *PTS[k])

    if name == "hook_sparks":
        stamp(img, W / 2, 360, "GTA 6", ANTON(220), WHITE, age - .05, rot=0, box=False)
        stamp(img, W / 2, 560, "WEAPONS", ANTON(170), RED, age - .35, rot=-4, fill=RED + (255,))
    elif name == "hook_names":
        for i, (s, col) in enumerate([("GIRARDI ES9", YEL), ("KLOSE K17", YEL), ("HAWK & LITTLE", RED)]):
            stamp(img, W / 2, 520 + i * 200, s, ANTON(120), col, age - .15 - i * .25, rot=(-1) ** i * 3, box=False)
        tag(ImageDraw.Draw(img), W / 2 - 170, 330, "OFFICIAL ROCKSTAR NAMES", GREEN)
    elif name == "pistols_wide":
        stamp(img, W / 2, 330, "THE PISTOLS", ANTON(150), WHITE, age - .1, rot=0, box=False)
    elif name in ("es9", "k17"):
        x, y = P(name); red_circle(img, x, y, 250, 150, (age - .15) / .45)
        if name == "es9": weapon_card(img, age - .3, 1, "GIRARDI ES9", "JASON'S PISTOL · 'J. DUVAL'", y=1000)
        else: weapon_card(img, age - .3, 2, "KLOSE K17", "LUCIA'S PISTOL · 'LUCIA'", y=300)
    elif name == "engraved":
        weapon_card(img, age - .05, 3, "ENGRAVED VARIANTS", "ULTIMATE EDITION EXTRA", y=250)
        rx_, ry_ = P("rose"); arrow(img, rx_ + 330, ry_ + 260, rx_ + 60, ry_ + 40, (age - .4) / .35)
    elif name == "smg_car":
        x, y = P("smg_car"); red_circle(img, x, y, 230, 330, (age - .3) / .5)
        weapon_card(img, age - .5, 4, "TROPICAL SMG", "SUBMACHINE GUN · VICE CITY PATTERN")
    elif name == "smg_jason":
        x, y = P("smg_jason"); arrow(img, x + 380, y + 420, x + 90, y + 120, (age - .2) / .35, YEL)
        stamp(img, W / 2, 1150, "STRAIGHT OUT OF THE 80s", ANTON(80), YEL, age - .3, rot=-3, box=False)
    elif name == "smg_pack":
        tag(ImageDraw.Draw(img), 60, 250, "PRE-ORDER BONUS", YEL)
        stamp(img, W / 2, 470, "VINTAGE VICE CITY PACK", ANTON(84), WHITE, age - .15, rot=0, fill=RED + (255,))
    elif name == "night_rifle":
        stamp(img, W / 2, 330, "OFFICIAL SCREENSHOTS", ANTON(100), WHITE, age - .1, rot=0, box=False)
    elif name == "trailer_rifle":
        x, y = P("rifle17"); red_circle(img, x, y, 330, 200, (age - .1) / .45)
        for k in ("heli1", "heli2"):
            hx, hy = P(k)
            if 100 < hx < W - 100 and 100 < hy: d = ImageDraw.Draw(img); brackets(d, hx - 110, hy - 80, hx + 110, hy + 80, YEL, 30, 5)
        weapon_card(img, age - .3, 5, "ASSAULT RIFLE", "JASON · POLICE CHOPPERS ABOVE", y=1000)
    elif name == "lucia_pistol":
        x, y = P("lucia_gun"); red_circle(img, x, y, 250, 220, (age - .15) / .45)
        weapon_card(img, age - .3, 6, "PISTOL", "LUCIA · POINT BLANK", y=300)
    elif name == "shotgun":
        x, y = P("shotgun"); red_circle(img, x, y, 200, 330, (age - .25) / .45)
        weapon_card(img, age - .45, 7, "SHOTGUN", "OFFICIAL KEY ART", y=300)
    elif name == "tease":
        stamp(img, W / 2, 700, "THE CRAZIEST ONE?", ANTON(130), YEL, age - .2, rot=0, box=False)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        for i in range(3):
            k = (age * 1.4 + i / 3) % 1; r = 80 + 420 * k
            dl.ellipse([W / 2 - r, 1050 - r, W / 2 + r, 1050 + r], outline=RED + (int(200 * (1 - k)),), width=6)
        img.alpha_composite(lay)
    elif name == "rev_reveal":
        weapon_card(img, age - .35, 8, "HAWK & LITTLE MORGAN", "REVOLVERS · HIS AND HERS", y=250, col=RED)
        tag(ImageDraw.Draw(img), 60, 500, "ULTIMATE EDITION", YEL)
    elif name in ("rev_grips", "rev_scope"):
        k_ = "grip" if name == "rev_grips" else "scope"
        x, y = P(k_); rx, ry = (230, 250) if k_ == "grip" else (420, 170)
        red_circle(img, x, y, rx, ry, (age - .1) / .4)
        lab = "PALM TREE GRIPS" if k_ == "grip" else "HIGH-PERFORMANCE SCOPE"
        stamp(img, W / 2, 330 if y > 800 else 1150, lab, ANTON(96), YEL, age - .2, rot=-3)
    elif name == "rev_engraved":
        for j, k_ in enumerate(("jduval", "lcaminos")):
            x, y = P(k_); red_circle(img, x, y, 170, 90, (age - .1 - j * .35) / .35)
        stamp(img, W / 2, 330, "\u201cJ. DUVAL\u201d + \u201cL. CAMINOS\u201d", ANTON(90), YEL, age - .2, rot=-3)
    elif name == "vercetti":
        stamp(img, W / 2, 620, "SOURCED FROM THE", ANTON(90), WHITE, age - .1, rot=0, box=False)
        stamp(img, W / 2, 800, "VERCETTI ESTATE", ANTON(150), RED, age - .45, rot=-4, fill=RED + (255,))
        d = ImageDraw.Draw(img); q = "“classic Vice City stylings sourced from the Vercetti Estate”"
        if age > .9:
            f = MONT(32, 600); text_c(d, W / 2, 1020, q, f, (240, 240, 240, 255)); text_c(d, W / 2, 1070, "— ROCKSTAR GAMES", MONT(28), YEL + (255,))
    elif name == "tommy":
        stamp(img, W / 2, 330, "TOMMY VERCETTI'S MANSION", ANTON(86), YEL, age - .1, rot=0, box=False)
        stamp(img, W / 2, 470, "GTA VICE CITY · 2002", ANTON(80), WHITE, age - .5, rot=0, fill=RED + (255,))
    elif name == "question":
        opts = [("GIRARDI ES9", YEL), ("KLOSE K17", YEL), ("TROPICAL SMG", WHITE), ("ASSAULT RIFLE", WHITE), ("HAWK & LITTLE MORGAN", RED)]
        for i, (lab, col) in enumerate(opts):
            ak = age - i * .1
            if ak < 0: continue
            e = eout(ak / .3); y = 300 + i * 150
            lay = rgba(); dl = ImageDraw.Draw(lay)
            dl.rectangle([110, y, 970, y + 118], fill=(0, 0, 0, 220), outline=col + (255,), width=4)
            dl.text((150, y + 14), f"{i + 1}", font=ANTON(80), fill=col + (255,)); dl.text((240, y + 18), lab, font=ANTON(72), fill=WHITE + (255,))
            img.alpha_composite(lay.transform((W, H), Image.AFFINE, (1, 0, (1 - e) * (800 if i % 2 else -800), 0, 1, 0)))
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
IMPACTS = [0.0, st("hook_names"), st("es9"), st("k17"), st("smg_car") + .5, st("trailer_rifle"), st("rev_reveal"), st("vercetti") + .45, st("tommy")]
FREEZE = st("rev_reveal")

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
    d.text((98, 60), "LEONIDA ARMORY // INTEL", font=MONT(26), fill=WHITE)
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
