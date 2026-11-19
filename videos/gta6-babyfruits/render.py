# "Baby Fruits Sneak Out to Play GTA 6 at Midnight" — two ORIGINAL baby-fruit characters with pseudo-3D shading
# (per-pixel lambert + specular + rim light, fruit textures: blueberry bloom / peach fuzz, glossy eyes) in a dark kitchen
# with a glossy counter reflection and ceiling-light bokeh — inspired by the "baby fruit" AI-video trend, but drawn by code.
# Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, json, subprocess
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
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), int(s))
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
@lru_cache(maxsize=32)
def ANTON(s): return ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), int(s))
INK = (20, 14, 18); WHITE = (255, 255, 255); YEL = (255, 214, 0)
TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word, nth=0): return [w["a"] for w in SEGT[seg]["words"] if clean(w["w"]) == clean(word)][nth]
def build_shots():
    out = []; segs = TM["segments"]
    for i, (sd, st_) in enumerate(zip(SEGMENTS, segs)):
        s0 = 0.0 if i == 0 else st_["a"] - 0.08
        s1 = segs[i + 1]["a"] - 0.08 if i + 1 < len(segs) else TOTAL
        out.append((s0, s1, sd["shots"][0][0], sd["id"]))
    return out
SHOTS = build_shots()
def st(n): return [s[0] for s in SHOTS if s[2] == n][0]
def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
WHO = {s["id"]: s["who"] for s in SEGMENTS}
def talking(t, who):
    for sd, sg in zip(SEGMENTS, TM["segments"]):
        if sd["who"] != who: continue
        for w in sg["words"]:
            if w["a"] <= t <= w["b"] + .02: return True
    return False

# ======================================================= pseudo-3D character sprites
SW, SH = 600, 820
LIGHT = np.array([-.45, -.6, .66]); LIGHT /= np.linalg.norm(LIGHT)
_YY, _XX = np.mgrid[0:SH, 0:SW].astype(np.float32)
def shade_ellipse(rgba, cx, cy, rx, ry, base, tex=None, spec=.55, rim=(255, 230, 220)):
    dx = (_XX - cx) / rx; dy = (_YY - cy) / ry; r2 = dx * dx + dy * dy; m = r2 < 1
    if not m.any(): return
    nz = np.sqrt(np.clip(1 - r2, 0, 1)); nx, ny = dx, dy
    lam = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    hv = LIGHT + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
    sp = np.clip(nx * hv[0] + ny * hv[1] + nz * hv[2], 0, 1) ** 40
    rimk = np.clip(1 - nz, 0, 1) ** 3
    col = np.array(base, np.float32)[None, None, :] * (.28 + .85 * lam)[..., None]
    if tex is not None: col = col * tex[..., None]
    col = col + spec * 255 * sp[..., None] + rimk[..., None] * np.array(rim, np.float32) * .25
    a = np.clip((1 - r2) * 60, 0, 1)                         # anti-aliased edge
    rgba[..., :3] = np.where(m[..., None], rgba[..., :3] * (1 - a[..., None]) + np.clip(col, 0, 255) * a[..., None], rgba[..., :3])
    rgba[..., 3] = np.maximum(rgba[..., 3], np.where(m, a * 255, 0))

@lru_cache(maxsize=4)
def body_sprite(kind):
    rng = np.random.default_rng(1 if kind == "blu" else 2)
    rgba = np.zeros((SH, SW, 4), np.float32)
    if kind == "blu":
        base = (70, 80, 170); n = rng.random((SH, SW)).astype(np.float32)
        tex = .9 + .25 * (np.asarray(Image.fromarray((n * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255)   # dusty bloom
    else:
        n = rng.random((SH, SW)).astype(np.float32)
        tex = .95 + .08 * n                                                           # peach fuzz
        base = (255, 160, 110)
    # legs, arms behind body, body, head
    for lx in (240, 360): shade_ellipse(rgba, lx, 770, 52, 48, base, tex, .3)
    for sgn in (-1, 1): shade_ellipse(rgba, 300 + sgn * 150, 560, 48, 78, base, tex, .3)
    shade_ellipse(rgba, 300, 590, 150, 175, base, tex)
    shade_ellipse(rgba, 300, 285, 200, 190, base, tex)
    img = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA"); d = ImageDraw.Draw(img)
    if kind == "peach":                                       # pink blush gradient on head + crease
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.ellipse([150, 120, 470, 430], fill=(255, 70, 110, 70)); ov = ov.filter(ImageFilter.GaussianBlur(40))
        img = Image.alpha_composite(img, Image.composite(ov, Image.new("RGBA", img.size, (0, 0, 0, 0)), img.getchannel("A")))
        d = ImageDraw.Draw(img); d.arc([290, 95, 420, 480], 200, 250, fill=(200, 90, 80, 160), width=6)
    # belly cross-section
    if kind == "blu":
        d.ellipse([215, 500, 385, 690], fill=(200, 215, 160, 255))
        for k in range(10):
            a = k / 10 * 2 * math.pi; d.line([300, 595, 300 + math.cos(a) * 70, 595 + math.sin(a) * 80], fill=(160, 175, 120, 255), width=4)
        d.ellipse([280, 575, 320, 615], fill=(150, 165, 110, 255))
    else:
        d.ellipse([215, 500, 385, 690], fill=(255, 200, 80, 255)); d.ellipse([240, 525, 360, 665], fill=(255, 180, 60, 255))
        d.ellipse([268, 548, 332, 642], fill=(150, 70, 45, 255))
        for k in range(6): d.line([272 + k * 10, 555, 275 + k * 9, 635], fill=(120, 55, 35, 255), width=3)
    belly = Image.new("L", img.size, 0); ImageDraw.Draw(belly).ellipse([215, 500, 385, 690], fill=255)
    gl = Image.new("RGBA", img.size, (255, 255, 255, 0)); ImageDraw.Draw(gl).ellipse([235, 515, 300, 560], fill=(255, 255, 255, 90))
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(8)))
    # crown / stem
    if kind == "blu":
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5; r = 52 if k % 2 == 0 else 24
            pts.append((300 + math.cos(a) * r, 108 + math.sin(a) * r * .55))
        d.polygon(pts, fill=(40, 40, 90, 255)); d.ellipse([285, 98, 315, 118], fill=(25, 25, 60, 255))
    else:
        d.rounded_rectangle([292, 60, 308, 110], 6, fill=(110, 75, 40, 255))
        d.polygon([(306, 78), (400, 40), (440, 70), (390, 100), (306, 92)], fill=(70, 160, 70, 255)); d.line([(306, 85), (420, 62)], fill=(40, 110, 50, 255), width=4)
    return img

def face(img, kind, expr, talk, t, look=0):
    d = ImageDraw.Draw(img); cy = 300; ex = 82; er = 50
    blink = (t % 3.4) < .12
    for sgn in (-1, 1):
        x = 300 + sgn * ex
        if expr == "sleep" or blink:
            d.arc([x - er, cy - 20, x + er, cy + 40], 200, 340, fill=INK, width=9)
            continue
        big = 1.18 if expr == "shock" else 1.0; rx, ry = er * .9 * big, er * big
        d.ellipse([x - rx, cy - ry, x + rx, cy + ry], fill=(18, 14, 22, 255))
        d.ellipse([x - rx * .65 + look * 8, cy - ry * .75, x - rx * .05 + look * 8, cy - ry * .15], fill=(255, 255, 255, 235))
        d.ellipse([x + rx * .2 + look * 8, cy + ry * .25, x + rx * .45 + look * 8, cy + ry * .5], fill=(255, 255, 255, 180))
        if expr == "angry": d.line([x - sgn * 55, cy - 80, x + sgn * 45, cy - 55], fill=INK, width=12)
        if expr == "worried": d.line([x - sgn * 45, cy - 62, x + sgn * 50, cy - 85], fill=INK, width=10)
    ck = Image.new("RGBA", img.size, (0, 0, 0, 0)); cd = ImageDraw.Draw(ck)
    for sgn in (-1, 1): cd.ellipse([300 + sgn * 150 - 45, cy + 50, 300 + sgn * 150 + 45, cy + 105], fill=(255, 80, 120, 120))
    img.alpha_composite(ck.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img); my = cy + 110
    if expr == "shock":
        d.ellipse([270, my - 15, 330, my + 65], fill=(110, 20, 40, 255)); d.ellipse([285, my + 30, 315, my + 60], fill=(240, 110, 130, 255))
    elif talk and int(t * 13) % 2 == 0:
        d.chord([255, my - 30, 345, my + 50], 0, 180, fill=(110, 20, 40, 255)); d.ellipse([280, my + 15, 320, my + 45], fill=(240, 110, 130, 255))
    elif expr in ("sleep",):
        d.ellipse([290, my, 310, my + 18], fill=(110, 20, 40, 255))
    elif expr in ("angry", "worried"):
        d.arc([265, my, 335, my + 40], 200, 340, fill=(110, 20, 40, 255), width=8)
    elif expr == "natural":
        d.line([270, my + 12, 330, my + 12], fill=(110, 20, 40, 255), width=8)
    else:
        d.chord([260, my - 25, 340, my + 40], 0, 180, fill=(110, 20, 40, 255)); d.ellipse([285, my + 8, 315, my + 34], fill=(240, 110, 130, 255))

def character(kind, expr, talk, t, scale=1.0, squash=0.0, look=0, arms_up=False, ctrl=False):
    img = body_sprite(kind).copy(); face(img, kind, expr, talk, t, look)
    d = ImageDraw.Draw(img)
    if arms_up:                                            # little raised arms (overdraw small shaded blobs)
        col = (70, 80, 170) if kind == "blu" else (255, 160, 110)
        for sgn in (-1, 1): d.ellipse([300 + sgn * 190 - 35, 330 - 40, 300 + sgn * 190 + 35, 330 + 40], fill=col + (255,))
    if ctrl:
        d.rounded_rectangle([200, 600, 400, 680], 36, fill=(35, 35, 45, 255), outline=(10, 10, 15, 255), width=4)
        d.ellipse([345, 620, 370, 645], fill=(230, 60, 60, 255)); d.ellipse([230, 620, 255, 645], fill=(80, 170, 255, 255))
    sx = scale * (1 + squash * .12); sy = scale * (1 - squash * .12)
    return img.resize((max(1, int(SW * sx)), max(1, int(SH * sy))), Image.LANCZOS)

# ======================================================= sets (soft-focus backgrounds)
def gradient(c1, c2):
    g = np.linspace(0, 1, H)[:, None, None]; return (np.array(c1) * (1 - g) + np.array(c2) * g).repeat(W, 1).astype(np.float32)
@lru_cache(maxsize=8)
def set_bg(kind):
    if kind == "kitchen":
        a = gradient((38, 26, 22), (14, 10, 10)); img = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(img)
        for x in range(0, W, 270): d.rectangle([x + 12, 300, x + 258, 820], fill=(70, 45, 32)); d.rectangle([x + 30, 320, x + 240, 800], outline=(95, 62, 44), width=6)
        d.rectangle([380, 560, 720, 900], fill=(20, 40, 80)); d.rectangle([380, 560, 720, 900], outline=(60, 40, 30), width=14)
        for (x, y) in ((200, 120), (540, 100), (880, 120)): d.ellipse([x - 30, y - 12, x + 30, y + 12], fill=(255, 230, 180))
        img = img.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(img)
        for (x, y) in ((200, 120), (540, 100), (880, 120)):
            glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([x - 160, y - 90, x + 160, y + 240], fill=(255, 200, 140, 70))
            img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(60))).convert("RGB")
        cnt = gradient((40, 34, 36), (8, 6, 8))[1100:]; rng = np.random.default_rng(4)
        cnt += rng.normal(0, 7, cnt.shape[:2])[..., None]
        arr = np.asarray(img, np.float32).copy(); arr[1100:] = cnt; arr[1100:1106] = 90
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if kind == "living":
        a = gradient((20, 16, 30), (8, 6, 12)); img = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(img)
        d.rounded_rectangle([-40, 1050, W + 40, 1500], 70, fill=(80, 50, 70)); d.rounded_rectangle([-40, 900, W + 40, 1150], 70, fill=(95, 60, 82))
        return img.filter(ImageFilter.GaussianBlur(4))
    if kind == "morning":
        a = gradient((255, 220, 170), (200, 150, 110)); img = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(img)
        for x in range(0, W, 270): d.rectangle([x + 12, 300, x + 258, 820], fill=(215, 170, 120))
        d.rectangle([380, 560, 720, 900], fill=(170, 220, 255))
        img = img.filter(ImageFilter.GaussianBlur(10)); arr = np.asarray(img, np.float32).copy()
        arr[1100:] = gradient((150, 130, 125), (90, 75, 70))[1100:]; arr[1100:1106] = 230
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def tv(img, t, mode, age, x0=140, y0=330, x1=940, y1=820):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0 - 20, y0 - 20, x1 + 20, y1 + 20], 24, fill=(15, 15, 18, 255))
    if mode in ("start", "dl", "done"):
        for i in range(0, y1 - y0, 6):
            k = i / (y1 - y0); d.rectangle([x0, y0 + i, x1, y0 + i + 6], fill=(int(255 - 30 * k), int(70 + 60 * k), int(150 - 90 * k), 255))
        cx = (x0 + x1) / 2
        if mode == "start":
            f = ANTON(170); d.text((cx - d.textlength("GTA 6", font=f) / 2, y0 + 70), "GTA 6", font=f, fill=WHITE, stroke_width=6, stroke_fill=INK)
            if int(t * 2.5) % 2 == 0: d.text((cx - d.textlength("PRESS START", font=MS(54, 900)) / 2, y0 + 330), "PRESS START", font=MS(54, 900), fill=WHITE)
        else:
            k = .99 if mode == "dl" else 1.0; lab = "99%" if mode == "dl" else "DOWNLOAD COMPLETE"
            d.text((cx - d.textlength("DOWNLOADING…" if mode == "dl" else "READY", font=MS(50, 900)) / 2, y0 + 80), "DOWNLOADING…" if mode == "dl" else "READY", font=MS(50, 900), fill=WHITE)
            d.rounded_rectangle([x0 + 70, y0 + 200, x1 - 70, y0 + 270], 34, fill=(40, 40, 50, 255), outline=WHITE, width=5)
            d.rounded_rectangle([x0 + 78, y0 + 208, x0 + 78 + (x1 - x0 - 156) * k, y0 + 262], 28, fill=(60, 220, 120, 255))
            f = ANTON(100 if mode == "dl" else 70); d.text((cx - d.textlength(lab, font=f) / 2, y0 + 300), lab, font=f, fill=YEL, stroke_width=5, stroke_fill=INK)
    elif mode == "crash":
        d.rectangle([x0, y0, x1, y1], fill=(60, 90, 140, 255)); d.rectangle([x0, y0 + 300, x1, y1], fill=(60, 60, 66, 255))
        d.rectangle([x0 + 520, y0 + 60, x0 + 545, y0 + 330], fill=(30, 30, 30, 255)); d.rectangle([x0 + 470, y0 + 50, x0 + 600, y0 + 75], fill=(30, 30, 30, 255))
        shake = math.sin(t * 50) * 6 if age < .6 else 0
        d.rounded_rectangle([x0 + 330 + shake, y0 + 250, x0 + 520 + shake, y0 + 340], 20, fill=(230, 60, 60, 255))
        f = ANTON(110); d.text(((x0 + x1) / 2 - d.textlength("CRASHED", font=f) / 2, y0 + 40), "CRASHED", font=f, fill=(255, 60, 60, 255), stroke_width=6, stroke_fill=INK)
    img.alpha_composite(lay)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([x0 - 200, y0 - 100, x1 + 200, y1 + 600], fill=(255, 90, 160, 60))
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(90)))

def bowl(img, front=True):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if not front:
        for (x, y, r, c) in ((330, 1110, 90, (220, 40, 40)), (750, 1100, 95, (255, 150, 30)), (540, 1080, 80, (120, 190, 60))):
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (255,)); d.ellipse([x - r * .5, y - r * .7, x - r * .1, y - r * .3], fill=(255, 255, 255, 110))
    else:
        d.chord([140, 920, 940, 1420], 0, 180, fill=(235, 235, 240, 255)); d.ellipse([140, 1130, 940, 1210], fill=(205, 205, 215, 255))
        d.arc([170, 940, 910, 1380], 30, 150, fill=(255, 255, 255, 200), width=10)
    img.alpha_composite(lay)

def comp(img, src, x, y):
    x, y = int(x), int(y); l, t_ = max(0, -x), max(0, -y)
    r, b_ = min(src.width, W - x), min(src.height, H - y)
    if r <= l or b_ <= t_: return
    img.alpha_composite(src.crop((l, t_, r, b_)), (x + l, y + t_))
def place(img, spr, cx, base, reflect=True):
    base = int(base); x, y = int(cx - spr.width / 2), int(base - spr.height)
    if reflect:                                                   # glossy counter reflection
        r = spr.transpose(Image.FLIP_TOP_BOTTOM); a = np.asarray(r.getchannel("A"), np.float32)
        a *= np.linspace(.35, 0, r.height)[:, None]; r.putalpha(Image.fromarray(a.astype(np.uint8)))
        comp(img, r.filter(ImageFilter.GaussianBlur(3)), x, base)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([cx - spr.width * .4, base - 18, cx + spr.width * .4, base + 18], fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); comp(img, spr, x, y)

def step_card(img, s, age):
    if age < 0: return
    k = back(min(1, age / .25)); f = ANTON(int(120 * k) + 1); d = ImageDraw.Draw(img); w = d.textlength(s, font=f)
    d.rounded_rectangle([W / 2 - w / 2 - 34, 170, W / 2 + w / 2 + 34, 170 + f.size * 1.25], 26, fill=(255, 214, 0), outline=INK, width=8)
    d.text((W / 2 - w / 2, 172), s, font=f, fill=INK)

def big_text(img, s, y, size, col, age, shake=False):
    if age < 0: return
    k = back(min(1, age / .2)); f = ANTON(int(size * k) + 1); d = ImageDraw.Draw(img); w = d.textlength(s, font=f)
    dx = math.sin(age * 60) * 10 if shake else 0
    d.text((W / 2 - w / 2 + dx, y), s, font=f, fill=col, stroke_width=10, stroke_fill=INK)

# ======================================================= shots
def draw_shot(name, t, a, b):
    age = t - a; bt, pt = talking(t, "b"), talking(t, "p")
    hop = lambda ph: abs(math.sin(t * 7 + ph)) * 30
    if name in ("sleep", "wake", "argue", "argue2", "hide", "hide2", "hide3"):
        img = set_bg("kitchen").convert("RGBA")
        bowl(img, front=False)
        hide = name.startswith("hide"); peek = hide and name != "hide"
        eb = "sleep" if name == "sleep" else ("natural" if hide else ("happy" if name in ("wake", "argue2") else "worried"))
        ep = "sleep" if name in ("sleep", "wake") else ("natural" if hide else ("angry" if name == "argue" else "worried"))
        sink = 0 if not hide else 270 * eout(age / .3) if name == "hide" else 270
        chars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        place(chars, character("blu", eb, bt, t, .8, look=1 if name.startswith("wake") else 0), 370, 1330 + sink, reflect=False)
        place(chars, character("peach", ep, pt, t + .7, .8, look=-1), 720, 1330 + sink, reflect=False)
        a_ = np.asarray(chars.getchannel("A")).copy(); a_[1300:] = 0; chars.putalpha(Image.fromarray(a_))
        img.alpha_composite(chars)
        bowl(img, front=True)
        if name == "sleep":
            d = ImageDraw.Draw(img)
            for k in range(3):
                ph = (t * .8 + k / 3) % 1; d.text((760 + ph * 80, 700 - ph * 220), "z", font=ANTON(int(50 + 40 * ph)), fill=(255, 255, 255, int(255 * (1 - ph))))
            big_text(img, "12:00 AM", 190, 140, WHITE, age)
        if name == "hide": step_card(img, "STEP 4: HIDE", age)
        return img
    if name in ("sneak", "sneak2"):
        img = set_bg("kitchen").convert("RGBA")
        p = (t - st("sneak")) / max(st("ctrl") - st("sneak"), .1)
        x0 = -150 + 1100 * p
        place(img, character("blu", "worried", bt, t, .62, squash=math.sin(t * 14) * .5), x0 + 200, 1450 - hop(0))
        place(img, character("peach", "worried", pt, t + .5, .62, squash=math.sin(t * 14 + 1.5) * .5), x0 - 200, 1450 - hop(1.5))
        if name == "sneak": step_card(img, "STEP 1: SNEAK", age)
        else: big_text(img, "SHHH!", 420, 200, YEL, age)
        return img
    if name in ("ctrl", "ctrl2", "fight", "fight2"):
        img = set_bg("living").convert("RGBA"); d = ImageDraw.Draw(img)
        big = name.startswith("ctrl")
        if big:                                                      # giant controller on the couch
            wob = math.sin(t * 9) * 6 if name == "ctrl2" else 0
            d.rounded_rectangle([170, 1130 + wob, 910, 1400 + wob], 130, fill=(35, 35, 45), outline=(10, 10, 15), width=10)
            for (x, c) in ((780, (230, 60, 60)), (700, (60, 200, 110)), (300, (80, 170, 255))): d.ellipse([x - 40, 1210 + wob, x + 40, 1290 + wob], fill=c)
            place(img, character("blu", "worried" if name == "ctrl2" else "happy", bt, t, .55, squash=math.sin(t * 10) * .8 if name == "ctrl2" else 0, arms_up=name == "ctrl2"), 540, 1170 + wob, reflect=False)
            if name == "ctrl": step_card(img, "STEP 2: CONTROLLER", age)
        else:
            tug = math.sin(t * 9) * 25
            place(img, character("blu", "angry" if name == "fight" else "happy", bt, t, .7, ctrl=name == "fight2"), 300 + tug, 1500, reflect=False)
            place(img, character("peach", "angry" if name == "fight" else "happy", pt, t + .5, .7, ctrl=name == "fight"), 790 + tug, 1500, reflect=False)
            if name == "fight": big_text(img, "I'M LUCIA!", 300, 140, (255, 140, 120), age)
            else: big_text(img, "I'M JASON.", 300, 140, (120, 160, 255), age)
        return img
    if name in ("tv", "pct", "pct2", "done", "done2", "crash", "crash2", "crash3", "mom"):
        img = set_bg("living").convert("RGBA")
        mode = {"tv": "dl", "pct": "dl", "pct2": "dl", "mom": "dl", "done": "done", "done2": "done", "crash": "crash", "crash2": "crash", "crash3": "crash"}[name]
        tv(img, t, mode, age)
        shock = name in ("pct", "pct2", "mom", "crash2")
        cheer = name in ("done", "done2")
        eb = "shock" if shock else ("happy" if cheer else ("worried" if name == "crash3" else "happy"))
        ep = "shock" if name in ("pct2", "mom") else ("angry" if name == "crash2" else ("happy" if cheer else "happy"))
        zoom = .62 + (.12 * eout(age / .3) if name in ("pct", "pct2", "mom") else 0)
        jump = abs(math.sin(t * 9)) * 60 if cheer else 0
        place(img, character("blu", eb, bt, t, zoom, arms_up=cheer, ctrl=not cheer), 300, 1560 - jump, reflect=False)
        place(img, character("peach", ep, pt, t + .5, zoom, arms_up=cheer), 790, 1560 - abs(math.sin(t * 9 + 1)) * 60 if cheer else 1560, reflect=False)
        if name == "tv": step_card(img, "STEP 3: DOWNLOAD", age)
        if name == "mom":
            fl = Image.new("RGBA", (W, H), (255, 240, 200, int(160 * max(0, 1 - age / .3)))); img.alpha_composite(fl)
            big_text(img, "WHO'S UP?!", 880, 170, (255, 70, 70), age, shake=True)
        if name == "crash": big_text(img, "10 SECONDS LATER…", 880, 100, WHITE, age)
        return img
    if name in ("morning", "morning2"):
        img = set_bg("morning").convert("RGBA"); bowl(img, front=True)
        if name == "morning": big_text(img, "6:00 AM", 190, 160, INK, age)
        else: big_text(img, "EMPTY?!", 700, 200, (255, 80, 80), age, shake=True)
        return img
    if name in ("asleep", "outro"):
        img = set_bg("living").convert("RGBA"); tv(img, t, "done", 9)
        dim = Image.new("RGBA", (W, H), (0, 0, 0, 90)); img.alpha_composite(dim)
        place(img, character("blu", "sleep", False, t, .62, ctrl=True), 310, 1560, reflect=False)
        place(img, character("peach", "sleep", False, t + 1, .62), 780, 1570, reflect=False)
        d = ImageDraw.Draw(img)
        for k in range(3):
            ph = (t * .8 + k / 3) % 1; d.text((760 + ph * 80, 900 - ph * 200), "z", font=ANTON(int(50 + 40 * ph)), fill=(255, 255, 255, int(255 * (1 - ph))))
        if name == "outro":
            big_text(img, "TAG A NIGHT OWL", 190, 110, YEL, age)
            tf = word_time("n7", "follow") - a
            if age > tf - .1:
                k = back(min(1, (age - tf + .1) / .3)); bw = 600 * k
                d.rounded_rectangle([540 - bw / 2, 360, 540 + bw / 2, 500], 60, fill=(235, 50, 50), outline=INK, width=8)
                if k > .7: d.text((540 - d.textlength("FOLLOW", font=ANTON(100)) / 2, 368), "FOLLOW", font=ANTON(100), fill=WHITE)
        return img
    raise ValueError(name)

# ======================================================= captions by speaker
PLATE = {"b": (90, 110, 230), "p": (255, 150, 110), "m": (170, 90, 200), "n": None}
LABEL = {"b": "BLU", "p": "PEACH", "m": "MOM"}
def build_caps():
    groups = []
    for sd, seg in zip(SEGMENTS, TM["segments"]):
        hl = {clean(x) for x in sd["hl"]}; cur = []
        for i, w in enumerate(seg["words"]):
            cur.append(dict(w, hl=clean(w["w"]) in hl))
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(seg["words"]) - 1:
                groups.append((cur, seg["id"])); cur = []
    return groups
CAPS = build_caps()
NUM = {"six.": "6.", "six": "6", "ninety-nine": "99", "percent?!": "%?!", "ten": "10", "one.": "1.", "two.": "2.", "three.": "3.", "four.": "4."}
def caption(img, t):
    g = None
    for ws, sid in CAPS:
        if ws[0]["a"] - .05 <= t: g = (ws, sid)
    if g is None: return
    ws, sid = g
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if t > ws[-1]["b"] + .45 or (nxt and t >= nxt[0] - .1): return
    toks = []
    for w in ws:
        s_ = NUM.get(w["w"].lower(), w["w"]).upper()
        if s_.startswith("%") and toks: toks[-1] = (toks[-1][0], toks[-1][1] + s_); continue
        toks.append((w, s_))
    who = WHO[sid]; d = ImageDraw.Draw(img); f = ANTON(92)
    widths = [d.textlength(s, font=f) for _, s in toks]; sp = 20
    while sum(widths) + sp * (len(toks) - 1) > W - 120:
        f = ANTON(f.size - 4); widths = [d.textlength(s, font=f) for _, s in toks]
    tot = sum(widths) + sp * (len(toks) - 1); x = (W - tot) / 2; y = 1610
    age = t - ws[0]["a"]; pop = back(min(1, age / .1)) if age > 0 else 0; yy0 = y + (1 - pop) * 22
    pl = PLATE[who]
    if pl:
        d.rounded_rectangle([x - 26, yy0 - 10, x + tot + 26, yy0 + f.size + 22], 26, fill=pl, outline=INK, width=6)
        lab = LABEL[who]; lf = MS(32, 900)
        d.rounded_rectangle([x - 26, yy0 - 60, x - 26 + d.textlength(lab, font=lf) + 30, yy0 - 12], 14, fill=INK); d.text((x - 11, yy0 - 57), lab, font=lf, fill=WHITE)
    for (w, s_), wd in zip(toks, widths):
        on = w["a"] - .03 <= t
        if pl: d.text((x, yy0), s_, font=f, fill=WHITE if on else (230, 230, 230), stroke_width=5, stroke_fill=INK)
        else: d.text((x, yy0), s_, font=f, fill=(YEL if w["hl"] and on else (WHITE if on else (215, 215, 215))), stroke_width=9, stroke_fill=INK)
        x += wd + sp

def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); return i, SHOTS[i]
def frame(t, fi=None):
    i, (a, b, name, seg) = shot_at(t)
    img = draw_shot(name, t, a, b); age = t - a
    if i and age < .1:                                           # quick punch-in on every cut (fast pacing)
        z = 1 + .06 * (1 - age / .1); cw, ch = W / z, H / z
        img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    caption(img, t)
    d = ImageDraw.Draw(img); d.text((30, 30), "ORIGINAL CHARACTERS · FAN-MADE", font=MS(22, 700), fill=WHITE, stroke_width=2, stroke_fill=INK)
    out = img.convert("RGB")
    if t < .1: out = Image.fromarray((np.asarray(out, np.float32) * ease(t / .1)).astype(np.uint8))
    return out

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
