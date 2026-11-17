# Motion-graphics renderer for "5 GTA 6 Secrets" (1080x1920, 30 fps).
# All visuals are original, procedurally drawn (no Rockstar footage/logos) — neon Vice-City-style look.
# Usage: python3 render.py still <t> [<t> ...]   -> still_<t>.jpg
#        python3 render.py video <worker> <nworkers> -> part_<worker>.mp4
import sys, os, math, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS = 1080, 1920, 30
BW, BH = 1350, 2400
FD = os.path.join(HERE, "fonts")
def font(name, size):
    f = ImageFont.truetype(os.path.join(FD, name), size)
    return f
ANTON = lambda s: font("Anton-Regular.ttf", s)
BEBAS = lambda s: font("BebasNeue-Regular.ttf", s)
def MONT(s, wght=800):
    f = font("Montserrat-VF.ttf", s)
    try: f.set_variation_by_axes([wght])
    except Exception: pass
    return f

PINK = (255, 45, 149); CYAN = (34, 228, 255); GOLD = (255, 205, 60); ORANGE = (255, 140, 50)
GREEN = (60, 255, 140); RED = (255, 50, 60); WHITE = (255, 255, 255); PURPLE = (120, 50, 200)
rng = np.random.default_rng(6)

# ------------------------------------------------------------------ timing
TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]
SEGT = {s["id"]: s for s in TM["segments"]}

def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")

def word_time(seg_id, word, nth=0):
    k = 0
    for w in SEGT[seg_id]["words"]:
        if clean(w["w"]) == word:
            if k == nth: return w["a"]
            k += 1
    raise KeyError((seg_id, word))

def build_shots():
    out = []
    segs = TM["segments"]
    for i, (sd, st) in enumerate(zip(SEGMENTS, segs)):
        seg_start = 0.0 if i == 0 else st["a"] - 0.06
        seg_end = segs[i + 1]["a"] - 0.06 if i + 1 < len(segs) else TOTAL
        starts = []
        for name, cue in sd["shots"]:
            starts.append((seg_start if cue is None else word_time(sd["id"], cue) - 0.08, name))
        for j, (a, name) in enumerate(starts):
            b = starts[j + 1][0] if j + 1 < len(starts) else seg_end
            out.append((a, b, name, sd["id"]))
    return out
SHOTS = build_shots()

def build_captions():
    caps = []  # (a, b, [ (text, a, b, hl) ... ])
    for sd in SEGMENTS:
        st = SEGT[sd["id"]]; ws = []
        for w in st["words"]:
            txt = w["w"].strip()
            prev = ws[-1][0] if ws else ""
            if ws and ((txt.upper() in ("T", "A") and prev in ("G", "GT")) or (txt == "S" and prev == "P") or (txt.startswith("5") and prev == "PS")):
                ws[-1] = (prev + txt.upper(), ws[-1][1], w["b"], True); continue
            ws.append((txt.upper(), w["a"], w["b"], clean(txt) in sd["hl"] or clean(txt).strip("-") in sd["hl"]))
        group = []
        for k, wd in enumerate(ws):
            group.append(wd)
            brk = wd[0][-1] in ".,?!…" or len(group) >= 3 or sum(len(g[0]) for g in group) > 13
            if brk or k == len(ws) - 1:
                caps.append(group); group = []
    out = []
    for i, g in enumerate(caps):
        a = g[0][1] - 0.05
        b = caps[i + 1][0][1] - 0.05 if i + 1 < len(caps) else g[-1][2] + 0.4
        b = min(b, g[-1][2] + 0.45)
        out.append((a, b, g))
    return out
CAPS = build_captions()

# ------------------------------------------------------------------ helpers
def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7):
    p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def grad(c1, c2, w=BW, h=BH, power=1.0):
    y = (np.linspace(0, 1, h) ** power)[:, None, None]
    a = np.array(c1, float); b = np.array(c2, float)
    return np.broadcast_to(a + (b - a) * y, (h, w, 3)).copy()
def grad3(stops, w=BW, h=BH):
    ys = np.linspace(0, 1, h)
    cols = np.stack([np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops]) for c in range(3)], 1)
    return np.broadcast_to(cols[:, None, :], (h, w, 3)).copy()

def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))

def glow_paste(img, lay, r=22, k=1.0, core=True):
    g = lay.filter(ImageFilter.GaussianBlur(r))
    if k != 1.0:
        a = np.asarray(g).astype(float); a[..., 3] *= k; g = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img.alpha_composite(g) if img.mode == "RGBA" else img.paste(g, (0, 0), g)
    if core:
        img.alpha_composite(lay) if img.mode == "RGBA" else img.paste(lay, (0, 0), lay)

def tsize(d, s, f):
    x0, y0, x1, y1 = d.textbbox((0, 0), s, font=f); return x1 - x0, y1 - y0, x0, y0

def text_c(d, cx, cy, s, f, fill, stroke=0, sc=(0, 0, 0)):
    w, h, ox, oy = tsize(d, s, f)
    d.text((cx - w / 2 - ox, cy - h / 2 - oy), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sc)

def neon_text(img, cx, cy, s, f, col, r=24, scale=1.0, rot=0, stroke=0):
    lay = rgba(); d = ImageDraw.Draw(lay)
    text_c(d, cx, cy, s, f, col + (255,), stroke, (20, 0, 30, 255))
    if scale != 1.0 or rot:
        lay = lay.resize((int(W * scale), int(H * scale)), Image.BICUBIC)
        lay = lay.crop(((lay.width - W) // 2, (lay.height - H) // 2, (lay.width - W) // 2 + W, (lay.height - H) // 2 + H)) if scale >= 1 else _pad(lay)
        if rot: lay = lay.rotate(rot, Image.BICUBIC, center=(cx, cy))
    glow_paste(img, lay, r, 1.3)
    hot = rgba(); dh = ImageDraw.Draw(hot)
    return img

def _pad(lay):
    out = rgba(); out.paste(lay, ((W - lay.width) // 2, (H - lay.height) // 2)); return out

def scaled_layer(lay, s, cx=W / 2, cy=H / 2):
    """scale an RGBA full-frame layer about (cx, cy)"""
    if abs(s - 1) < 1e-3: return lay
    nw, nh = max(1, int(W * s)), max(1, int(H * s))
    big = lay.resize((nw, nh), Image.BICUBIC)
    out = rgba(); out.paste(big, (int(cx - cx * s), int(cy - cy * s)), big); return out

def stamp(img, cx, cy, s, f, col, age, rot=-8, box=True):
    """slam-in stamp: big -> 1.0 with overshoot"""
    if age < 0: return
    sc = 1 + 1.6 * (1 - eout(age / 0.18)) if age < 0.18 else 1 + 0.05 * math.sin(min(1, (age - 0.18) / 0.2) * math.pi)
    lay = rgba(); d = ImageDraw.Draw(lay)
    w, h, ox, oy = tsize(d, s, f)
    if box:
        d.rounded_rectangle([cx - w / 2 - 40, cy - h / 2 - 30, cx + w / 2 + 40, cy + h / 2 + 30], 18, outline=col + (255,), width=12)
    text_c(d, cx, cy, s, f, col + (255,))
    lay = lay.rotate(rot, Image.BICUBIC, center=(cx, cy))
    lay = scaled_layer(lay, sc, cx, cy)
    a = min(1, age / 0.08)
    if a < 1:
        arr = np.asarray(lay).copy(); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); lay = Image.fromarray(arr)
    glow_paste(img, lay, 18, 0.9)

def arrow(d, x0, y0, x1, y1, col, wdt=16, head=50):
    d.line([x0, y0, x1, y1], fill=col, width=wdt)
    ang = math.atan2(y1 - y0, x1 - x0)
    pts = [(x1 + head * 0.3 * math.cos(ang), y1 + head * 0.3 * math.sin(ang)),
           (x1 - head * math.cos(ang - 0.5), y1 - head * math.sin(ang - 0.5)),
           (x1 - head * math.cos(ang + 0.5), y1 - head * math.sin(ang + 0.5))]
    d.polygon(pts, fill=col)

def circle_draw(img, cx, cy, rx, ry, p, col=RED, wdt=14):
    """hand-drawn circle that draws on over p"""
    lay = rgba(); d = ImageDraw.Draw(lay)
    n = 60; k = int(n * 1.15 * ease(p))
    pts = [(cx + rx * (1 + 0.04 * math.sin(i * 0.9)) * math.cos(-1.9 + i / n * 2 * math.pi * 1.08),
            cy + ry * (1 + 0.04 * math.cos(i * 1.3)) * math.sin(-1.9 + i / n * 2 * math.pi * 1.08)) for i in range(k)]
    if len(pts) > 1: d.line(pts, fill=col + (255,), width=wdt, joint="curve")
    glow_paste(img, lay, 12, 0.8)

def cam(bg, p, z0, z1, dx=0.0, dy=0.0):
    p = min(max(p, 0), 1)
    z = z0 + (z1 - z0) * (0.5 * ease(p) + 0.5 * p)
    cw = bg.size[0] / z; ch = cw * H / W
    bw_, bh_ = bg.size
    cw = min(cw, bw_); ch = min(ch, bh_)
    cx = bw_ / 2 + dx * (p - 0.5) * (bw_ - cw); cy = bh_ / 2 + dy * (p - 0.5) * (bh_ - ch)
    cx = min(max(cx, cw / 2), bw_ - cw / 2); cy = min(max(cy, ch / 2), bh_ - ch / 2)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

# ------------------------------------------------------------------ backgrounds
def palm(d, x, base, h, col, lean=0.15, r=None):
    r = r or np.random.default_rng(int(x))
    pts = []
    for i in range(30):
        u = i / 29; pts.append((x + lean * h * u * u, base - h * u))
    for i in range(len(pts) - 1):
        wd = int(h * 0.03 * (1 - i / 40))
        d.line([pts[i], pts[i + 1]], fill=col, width=max(4, wd))
    tx, ty = pts[-1]
    for k in range(9):
        ang = -math.pi / 2 + (k - 4) * 0.42 + r.uniform(-.1, .1)
        L = h * r.uniform(0.32, 0.45)
        fr = [(tx + L * u * math.cos(ang), ty + L * u * math.sin(ang) + L * 0.55 * u * u * (0.6 + abs(math.cos(ang)))) for u in np.linspace(0, 1, 14)]
        for j in range(len(fr) - 1):
            d.line([fr[j], fr[j + 1]], fill=col, width=max(3, int(h * 0.028 * (1 - j / 14))))
            nx, ny = fr[j]
            for s in (-1, 1):
                d.line([nx, ny, nx + s * 18 * (1 - j / 14) + 6, ny + 26 * (1 - j / 14)], fill=col, width=4)

def skyline(d, base, col, seed, hmin, hmax, wmin=50, wmax=140, win=None):
    r = np.random.default_rng(seed); x = -40
    while x < BW + 40:
        w = r.uniform(wmin, wmax); h = r.uniform(hmin, hmax)
        d.rectangle([x, base - h, x + w, base], fill=col)
        if r.random() < 0.3: d.rectangle([x + w * 0.4, base - h - 60, x + w * 0.45, base - h], fill=col)
        if win:
            for wy in np.arange(base - h + 20, base - 20, 26):
                for wx in np.arange(x + 10, x + w - 14, 22):
                    if r.random() < 0.28:
                        c = win[int(r.integers(len(win)))]
                        d.rectangle([wx, wy, wx + 9, wy + 12], fill=c)
        x += w + r.uniform(-10, 14)

def bg_sunset(night=False):
    stops = [(0, (20, 6, 50)), (0.25, (70, 15, 110)), (0.45, (200, 40, 130)), (0.6, (255, 120, 80)), (0.66, (255, 180, 90)), (1, (30, 10, 50))]
    if night: stops = [(0, (5, 2, 20)), (0.35, (30, 8, 70)), (0.6, (110, 20, 120)), (0.66, (160, 40, 120)), (1, (10, 4, 25))]
    a = grad3(stops)
    img = to_img(a); d = ImageDraw.Draw(img)
    # stars
    for _ in range(260):
        x, y = rng.uniform(0, BW), rng.uniform(0, BH * 0.4); s = rng.uniform(1, 3)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 230, 255))
    # synthwave sun
    sun = rgba(BW, BH); ds = ImageDraw.Draw(sun)
    cx, cy, R = BW / 2, BH * 0.56, 420
    for y in range(int(cy - R), int(cy + R)):
        u = (y - (cy - R)) / (2 * R)
        hw = math.sqrt(max(0, R * R - (y - cy) ** 2))
        col = (int(255), int(230 - 160 * u), int(90 + 60 * u), 255)
        if u > 0.45 and (y // 8) % (2 + int((1 - u) * 6)) == 0: continue
        ds.line([cx - hw, y, cx + hw, y], fill=col)
    img.paste(sun.filter(ImageFilter.GaussianBlur(60)), (0, 0), sun.filter(ImageFilter.GaussianBlur(60)))
    img.paste(sun, (0, 0), sun)
    base = int(BH * 0.66)
    skyline(d, base, (40, 10, 60), 3, 200, 520, win=[(255, 200, 120), (255, 90, 180), (120, 220, 255)])
    skyline(d, base + 10, (22, 5, 38), 8, 120, 330, 80, 180, win=[(255, 120, 200), (100, 230, 255)])
    # water with reflections
    wa = np.asarray(img).astype(float)
    refl = wa[base - 1::-1][: BH - base]
    yy = np.arange(BH - base)[:, None, None]
    ripple = (np.sin(yy * 0.35 + np.arange(BW)[None, :, None] * 0.02) * 0.5 + 0.5)
    wa[base:] = refl[: BH - base] * (0.35 + 0.2 * ripple) + np.array([10, 5, 30]) * 0.8
    img = to_img(wa); d = ImageDraw.Draw(img)
    for x, h, ln in [(90, 1100, 0.18), (250, 900, 0.25), (1200, 1150, -0.2), (1050, 850, -0.12)]:
        palm(d, x, BH * 0.8, h, (12, 2, 20), ln)
    return img

def bg_grid(c1=(10, 2, 30), c2=(60, 10, 90), line=PINK):
    return to_img(grad(c1, c2, W, H))

def draw_grid(img, t, col=PINK, horizon=1050, speed=1.0, alpha=200):
    lay = rgba(); d = ImageDraw.Draw(lay)
    for i in range(-14, 15):
        d.line([W / 2 + i * 40, horizon, W / 2 + i * 260, H + 40], fill=col + (alpha,), width=3)
    off = (t * speed) % 1
    for k in range(18):
        z = (k + 1 - off)
        y = horizon + 1400 / (z * 1.3 + 1) - 70
        y = horizon + (H - horizon) * (1 / (1 + (18 - k - off) * 0.35)) ** 1.2
        d.line([0, y, W, y], fill=col + (alpha,), width=3)
    glow_paste(img, lay, 10, 1.0)

print("building backgrounds", flush=True)
BG_SUN = bg_sunset()
BG_NIGHT = bg_sunset(night=True)
BG_SUN_BLUR = BG_SUN.filter(ImageFilter.GaussianBlur(14))
BG_NIGHT_BLUR = BG_NIGHT.filter(ImageFilter.GaussianBlur(18))

def dark_bg(c1, c2):
    return to_img(grad(c1, c2, W, H))
BG_RED = dark_bg((40, 0, 10), (8, 0, 4))
BG_PURPLE = dark_bg((22, 4, 50), (6, 2, 18))
BG_TEAL = dark_bg((0, 30, 40), (2, 6, 18))
BG_GREEN = dark_bg((0, 18, 8), (0, 4, 2))
BG_GOLD = dark_bg((50, 30, 0), (10, 4, 0))

def yy_xx():
    return np.mgrid[0:H, 0:W]
YY, XX = yy_xx()
def rays_layer(t, col, n=16, cx=W / 2, cy=H * 0.42, alpha=60):
    ang = np.arctan2(YY - cy, XX - cx) + t * 0.6
    m = (np.sin(ang * n) > 0.3).astype(float)
    r = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)
    m *= np.clip(1.3 - r / 1500, 0, 1)
    arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = col; arr[..., 3] = (m * alpha).astype(np.uint8)
    return Image.fromarray(arr)

# ------------------------------------------------------------------ official Rockstar images (assets/official, see fetch_official.sh)
OFFDIR = os.path.join(HERE, "assets", "official")
FOCAL = {}
for ln in open(os.path.join(HERE, "official_images.txt")):
    if ln.strip() and not ln.startswith("#"):
        k_, _, fx = ln.split()[:3]; FOCAL[k_] = float(fx)
def _load(k):
    f = os.path.join(OFFDIR, k + ".jpg")
    if not os.path.exists(f): return None
    im = Image.open(f).convert("RGB"); sc = max(2300 / im.height, 1300 / im.width)
    return im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
OFF = {k: _load(k) for k in FOCAL}
HAVE_OFF = all(v is not None for v in OFF.values())
def photo(key, p, z0=1.0, z1=1.15, dx=0.0, dy=0.0, dark=1.0, blur=0, focal=None, size=(W, H)):
    """Ken-Burns crop of an official image to `size` (default full 9:16 frame)."""
    im = OFF.get(key); w_, h_ = size
    if im is None: return Image.new("RGBA", size, (20, 10, 30, 255))
    p = min(max(p, 0), 1); z = z0 + (z1 - z0) * (ease(p) * .5 + p * .5)
    ch = im.height / z; cw = ch * w_ / h_
    if cw > im.width: cw = im.width / z; ch = cw * h_ / w_
    fx = FOCAL.get(key, .5) if focal is None else focal
    cx = im.width * fx + dx * (p - .5) * cw * 0.3; cy = im.height / 2 + dy * (p - .5) * (im.height - ch)
    cx = min(max(cx, cw / 2), im.width - cw / 2); cy = min(max(cy, ch / 2), im.height - ch / 2)
    v = im.resize(size, Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)).convert("RGBA")
    if blur: v = v.filter(ImageFilter.GaussianBlur(blur))
    if dark != 1.0:
        a_ = np.asarray(v).astype(np.float32); a_[..., :3] *= dark; v = to_img(a_)
    return v
def framed(img, key, x, y, w, h, p, age, rot=0, label=None, border=WHITE):
    """photo card that slides/scales in"""
    if age < 0: return
    e = back(age / 0.3)
    card = photo(key, p, 1.0, 1.12, 0.5, 0, size=(w, h))
    lay = rgba(); lay.paste(card, (int(x), int(y))); dl = ImageDraw.Draw(lay)
    dl.rectangle([x, y, x + w, y + h], outline=border + (255,), width=8)
    if label:
        tw = dl.textlength(label, font=MONT(28, 800))
        dl.rectangle([x, y + h - 48, x + tw + 26, y + h], fill=(0, 0, 0, 220)); dl.text((x + 13, y + h - 42), label, font=MONT(28, 800), fill=WHITE + (255,))
    if rot: lay = lay.rotate(rot, Image.BICUBIC, center=(x + w / 2, y + h / 2))
    glow_paste(img, scaled_layer(lay, max(.01, e), x + w / 2, y + h / 2), 20, 0.5)
# thumbnails for the "90 clips" grid: random crops of every official image
_rt = np.random.default_rng(31); TILES = []
_keys = [k for k in FOCAL if OFF.get(k) is not None]
for i_ in range(90):
    k_ = _keys[i_ % len(_keys)] if _keys else None
    if k_ is None: TILES.append(Image.new("RGB", (108, 62), (40, 20, 50))); continue
    im_ = OFF[k_]; cw_ = im_.width * _rt.uniform(.25, .5); ch_ = cw_ * 62 / 108
    x_ = _rt.uniform(0, im_.width - cw_); y_ = _rt.uniform(0, im_.height - ch_)
    TILES.append(im_.resize((108, 62), Image.BILINEAR, box=(x_, y_, x_ + cw_, y_ + ch_)))

# ------------------------------------------------------------------ shots
GRAIN = [(np.random.default_rng(k).standard_normal((H // 2, W // 2)) * 6) for k in range(4)]
VIG = np.clip(1.18 - (((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H / 2) / (H * 0.62)) ** 2) * 0.55, 0.3, 1)[..., None].astype(np.float32)
CODE_LINES = ["$ ssh rsg-dev@internal", "> auth token... OK", "> slack.channel(#vi-dev)", "> fetch /builds/vi/*.mp4",
              "  clip_001.mp4 ... 100%", "  clip_014.mp4 ... 100%", "  clip_037.mp4 ... 100%", "  clip_062.mp4 ... 100%",
              "  clip_090.mp4 ... 100%", "> upload --forum", "!! ACCESS FLAGGED", "> 90 FILES SENT"]
FEED = np.random.default_rng(9).random((12, 4))
BILLS = np.random.default_rng(12).random((40, 4))
CONF = np.random.default_rng(13).random((90, 5))

NUM_BG = {5: "trailer2", 4: "trailer1", 3: "gr_gator", 2: "cover", 1: "vc_night"}
def num_card(img, t, age, n, col):
    img.paste(photo(NUM_BG[n], min(1, age / 1.5), 1.05, 1.25, dark=0.5, blur=4))
    img.alpha_composite(rays_layer(t, col, 14, alpha=70))
    s = back(age / 0.35) if age < 0.35 else 1 + 0.02 * math.sin(age * 6)
    lay = rgba(); d = ImageDraw.Draw(lay)
    text_c(d, W / 2, 560, "SECRET", ANTON(140), WHITE + (255,))
    text_c(d, W / 2, 900, f"#{n}", ANTON(520), col + (255,), 14, (25, 0, 40, 255))
    lay = scaled_layer(lay, max(0.01, s), W / 2, 800)
    glow_paste(img, lay, 30, 1.2)
    # chromatic split shortly after slam
    return img

def phone_frame(d, x0, y0, x1, y1):
    d.rounded_rectangle([x0, y0, x1, y1], 70, fill=(10, 10, 16, 255), outline=(200, 200, 230, 255), width=10)
    d.rounded_rectangle([x0 + 22, y0 + 22, x1 - 22, y1 - 22], 52, fill=(24, 20, 36, 255))
    d.rounded_rectangle([(x0 + x1) / 2 - 80, y0 + 34, (x0 + x1) / 2 + 80, y0 + 70], 18, fill=(0, 0, 0, 255))

def draw_shot(name, t, a, b, seg):
    p = (t - a) / max(1e-3, b - a); age = t - a
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    def bgcam(bg, z0, z1, dx=0, dy=0): img.paste(cam(bg, p, z0, z1, dx, dy).convert("RGBA"))

    if name == "hook_city":
        img.paste(photo("rooftop", p, 1.0, 1.18, 0, 0.6))
        g_ = rgba(); dg_ = ImageDraw.Draw(g_)
        for y_ in range(0, 900, 12): dg_.rectangle([0, y_, W, y_ + 12], fill=(10, 0, 30, int(150 * (1 - y_ / 900))))
        img.alpha_composite(g_)
        s = back(age / 0.4) if age < 0.4 else 1 + 0.03 * age
        lay = rgba(); d = ImageDraw.Draw(lay)
        text_c(d, W / 2, 470, "GTA 6", ANTON(330), WHITE + (255,), 16, (60, 0, 80, 255))
        lay = scaled_layer(lay, s, W / 2, 470)
        glow_paste(img, lay, 34, 1.2)
        d = ImageDraw.Draw(img)
        if age > 0.35:
            text_c(d, W / 2, 720, "SECRETS", ANTON(130), PINK + (255,), 10, (30, 0, 40, 255))
    elif name == "hook_five":
        img.paste(photo("hero", p, 1.0, 1.15, 0.5, 0, dark=0.55))
        d = ImageDraw.Draw(img)
        for k in range(5):
            ak = age - k * 0.1
            if ak < 0: continue
            e = back(ak / 0.3)
            x = W / 2 + (k - 2) * 190; y = 640 + abs(k - 2) * 40
            lay = rgba(); dl = ImageDraw.Draw(lay)
            th_ = photo(["trailer2", "trailer1", "gr_gator", "cover", "masked"][k], 0.5, 1.0, 1.0, dark=0.55, size=(170, 260))
            lay.paste(th_, (int(x - 85), int(y - 130)))
            dl.rounded_rectangle([x - 85, y - 130, x + 85, y + 130], 22, outline=[CYAN, PINK, GOLD, GREEN, ORANGE][k] + (255,), width=8)
            text_c(dl, x, y - 10, "?" if age < 1.2 + k * 0.05 else str(5 - k), ANTON(150), WHITE + (255,), 8, (0, 0, 0, 255))
            lay = lay.rotate((k - 2) * -7, Image.BICUBIC, center=(x, y + 200))
            lay = scaled_layer(lay, max(0.01, e), x, y)
            glow_paste(img, lay, 18, 0.9)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 330, "YOU DIDN'T KNOW", ANTON(110), GOLD + (255,), 8, (30, 0, 40, 255))
    elif name.startswith("num"):
        n = int(name[3:]); col = {5: CYAN, 4: GREEN, 3: ORANGE, 2: PINK, 1: GOLD}[n]
        num_card(img, t, age, n, col)
    elif name == "film_strip":
        img.paste(photo("trailer2", p, 1.0, 1.15, 0, 0.3, dark=0.75))
        lay = rgba(); d = ImageDraw.Draw(lay)
        y0 = 360; hh = 560; off = -(age * 420) % 520
        d.rectangle([-10, y0, W + 10, y0 + hh], fill=(12, 10, 14, 255))
        for k in range(-1, 4):
            x = k * 520 + off - 260
            fr = photo(["vc_marina", "jason_action", "gr_airboat", "keys", "lucia_gun"][k + 1], 0.5, 1.0, 1.0, size=(460, 440))
            lay.paste(fr.convert("RGBA"), (int(x + 30), y0 + 60))
            for hy in (y0 + 15, y0 + hh - 45):
                for hx in range(0, 520, 70):
                    d.rounded_rectangle([x + hx + 10, hy, x + hx + 45, hy + 30], 6, fill=(230, 230, 230, 255))
        lay = lay.rotate(-4, Image.BICUBIC, center=(W / 2, y0 + hh / 2))
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 280, "TRAILER 2", ANTON(150), WHITE + (255,), 10, (0, 0, 0, 255))
        stamp(img, W / 2, 1060, "100% IN-GAME", ANTON(120), GREEN, age - 0.9, rot=-6)
    elif name == "console":
        img.paste(photo("jason_drive", p, 1.0, 1.15, -0.5, 0, dark=0.55))
        s = eout(age / 0.4) * 0.15 + 0.85 + 0.04 * p
        lay = rgba(); d = ImageDraw.Draw(lay)
        # generic gamepad silhouette
        cx, cy = W / 2, 700
        d.rounded_rectangle([cx - 330, cy - 150, cx + 330, cy + 120], 120, fill=(235, 240, 250, 255))
        d.ellipse([cx - 380, cy - 60, cx - 140, cy + 270], fill=(235, 240, 250, 255))
        d.ellipse([cx + 140, cy - 60, cx + 380, cy + 270], fill=(235, 240, 250, 255))
        d.rounded_rectangle([cx - 270, cy - 70, cx - 220, cy + 40], 8, fill=(40, 44, 60, 255))
        d.rounded_rectangle([cx - 300, cy - 40, cx - 190, cy + 10], 8, fill=(40, 44, 60, 255))
        for dx, dy, c in [(250, -70, GREEN), (300, -20, RED), (200, -20, PINK), (250, 30, CYAN)]:
            d.ellipse([cx + dx - 22, cy + dy - 22, cx + dx + 22, cy + dy + 22], fill=c + (255,))
        for dx in (-110, 110):
            d.ellipse([cx + dx - 48, cy + 40, cx + dx + 48, cy + 136], fill=(30, 34, 50, 255))
        d.rounded_rectangle([cx - 90, cy - 120, cx + 90, cy - 40], 20, fill=(60, 64, 90, 255))
        lay = scaled_layer(lay, s, cx, cy)
        glow_paste(img, lay, 30, 0.6)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 300, "CAPTURED ON", ANTON(110), WHITE + (255,), 8, (0, 0, 0, 255))
        if age > 0.2:
            neon_text(img, W / 2, 1060, "PS5", ANTON(230), CYAN, 30, 1.0)
    elif name == "split_half":
        d = ImageDraw.Draw(img)
        prog = eout(age / 0.35)
        left = photo("jason_action", p, 1.0, 1.12, 0.3, 0)
        right = photo("vc_incar", p, 1.05, 1.15, -0.3, 0)
        mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
        xm = W / 2
        dm.polygon([(0, 0), (xm + 140, 0), (xm - 140, H), (0, H)], fill=255)
        img.paste(right); img.paste(left, (0, 0), mask)
        d = ImageDraw.Draw(img)
        # HUD on the gameplay half: minimap + health
        d.ellipse([60, 1050, 300, 1290], fill=(10, 20, 30, 220), outline=(255, 255, 255, 255), width=6)
        d.polygon([(180, 1140), (165, 1185), (195, 1185)], fill=WHITE)
        d.rectangle([60, 1305, 300, 1320], fill=GREEN)
        # letterbox on cutscene half
        d.rectangle([W / 2 + 60, 0, W, 170], fill=(0, 0, 0)); d.rectangle([W / 2 - 80, H - 170, W, H], fill=(0, 0, 0))
        d.line([(xm + 140, 0), (xm - 140, H)], fill=WHITE, width=10)
        for cx, lab, col, dlt in [(270, "GAMEPLAY", CYAN, 0.0), (820, "CUTSCENES", PINK, 0.25)]:
            if age > dlt:
                e = back((age - dlt) / 0.3)
                lay = rgba(); dl = ImageDraw.Draw(lay)
                text_c(dl, cx, 420, "50%", ANTON(200), col + (255,), 10, (0, 0, 0, 255))
                text_c(dl, cx, 590, lab, ANTON(90), WHITE + (255,), 8, (0, 0, 0, 255))
                glow_paste(img, scaled_layer(lay, max(.01, e), cx, 480), 16, 0.8)
    elif name == "leak_alert":
        img.paste(photo("trailer1", p, 1.2, 1.3, dark=0.35, blur=12))
        img.alpha_composite(Image.new("RGBA", (W, H), (120, 0, 10, 90)))
        fr = photo("trailer1", p, 1.0, 1.08, size=(820, 1100))
        img.paste(fr, (130, 260))
        d = ImageDraw.Draw(img)
        d.rectangle([130, 260, 950, 1360], outline=RED, width=10)
        if int(t * 4) % 2 == 0:
            d.ellipse([170, 300, 210, 340], fill=RED); text_c(d, 290, 320, "REC", ANTON(50), WHITE)
        stamp(img, W / 2, 700, "LEAKED", ANTON(230), RED, age - 0.15, rot=-10)
        if age > 1.0:
            e = eout((age - 1.0) / 0.35)
            lay = rgba(); dl = ImageDraw.Draw(lay)
            dl.rounded_rectangle([200, 1000, 880, 1160], 30, fill=GOLD + (255,))
            text_c(dl, W / 2, 1080, "RELEASED EARLY", ANTON(100), (20, 0, 0, 255))
            lay = lay.transform((W, H), Image.AFFINE, (1, 0, -(1 - e) * 900, 0, 1, 0))
            img.alpha_composite(lay)
    elif name == "views_counter":
        img.paste(photo("jl_club", p, 1.0, 1.15, 0.4, 0, dark=0.4))
        d = ImageDraw.Draw(img)
        v = 90_000_000 * eout(min(1, age / 1.6))
        lay = rgba(); dl = ImageDraw.Draw(lay)
        # generic play badge
        dl.rounded_rectangle([W / 2 - 110, 210, W / 2 + 110, 360], 40, fill=WHITE + (255,))
        dl.polygon([(W / 2 - 30, 245), (W / 2 - 30, 325), (W / 2 + 45, 285)], fill=PINK + (255,))
        text_c(dl, W / 2, 560, f"{int(v):,}", ANTON(170), WHITE + (255,), 10, (40, 0, 60, 255))
        text_c(dl, W / 2, 730, "VIEWS", ANTON(110), GOLD + (255,))
        glow_paste(img, lay, 20, 0.8)
        # rising graph
        lay = rgba(); dl = ImageDraw.Draw(lay)
        k = int(60 * min(1, age / 1.6))
        pts = [(140 + i * 13.3, 1120 - 260 * (1 - math.exp(-i / 18)) - 8 * math.sin(i)) for i in range(k + 1)]
        if len(pts) > 1: dl.line(pts, fill=CYAN + (255,), width=12, joint="curve")
        glow_paste(img, lay, 14, 1.0)
        if age > 0.6:
            stamp(img, W / 2, 900, "IN 24 HOURS", ANTON(110), CYAN, age - 0.6, rot=0, box=False)
    elif name == "trophy":
        img.paste(photo("vc_sign", p, 1.0, 1.15, 0.6, 0, dark=0.6))
        img.alpha_composite(rays_layer(t, GOLD, 18, cy=640, alpha=45))
        e = back(age / 0.4)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        cx, cy = W / 2, 640
        dl.pieslice([cx - 230, cy - 330, cx + 230, cy + 130], 0, 180, fill=GOLD + (255,))
        dl.rectangle([cx - 230, cy - 330, cx + 230, cy - 100], fill=GOLD + (255,))
        for s in (-1, 1):
            dl.arc([cx + s * 230 - 110, cy - 290, cx + s * 230 + 110, cy - 50], 0, 360, fill=GOLD + (255,), width=26)
        dl.rectangle([cx - 40, cy + 120, cx + 40, cy + 230], fill=(220, 160, 30, 255))
        dl.rounded_rectangle([cx - 190, cy + 220, cx + 190, cy + 300], 16, fill=(120, 70, 20, 255))
        text_c(dl, cx, cy - 170, "#1", ANTON(170), (140, 80, 0, 255))
        dl.ellipse([cx - 160, cy - 300, cx - 110, cy - 160], fill=(255, 250, 200, 200))
        glow_paste(img, scaled_layer(lay, max(.01, e), cx, cy), 30, 0.7)
        d = ImageDraw.Draw(img)
        for (cx_, cy_, s_, sp, ph) in CONF:
            y = (cy_ * 400 + age * (300 + sp * 500)) - 300
            if y > H: continue
            x = cx_ * W + 40 * math.sin(age * 3 + ph * 9)
            c = [GOLD, PINK, CYAN, WHITE, GREEN][int(ph * 5)]
            d.rectangle([x, y, x + 10 + s_ * 16, y + 18], fill=c)
        if age > 0.35:
            text_c(d, W / 2, 1080, "WORLD RECORD", ANTON(140), WHITE + (255,), 10, (60, 30, 0, 255))
    elif name == "florida_map":
        img.paste(photo("gr_gator", p, 1.0, 1.15, -0.4, 0, dark=0.8))
        P_SCALE = 0.42
        # stylised Florida-like peninsula (Leonida is Rockstar's fictional Florida)
        P = [(220, 300), (700, 300), (720, 340), (770, 360), (800, 420), (820, 520), (850, 620), (880, 720), (900, 820), (905, 920),
             (880, 1010), (840, 1060), (800, 1080), (770, 1050), (730, 980), (690, 900), (660, 820), (620, 740), (590, 660),
             (560, 590), (520, 520), (470, 470), (400, 430), (330, 410), (260, 400), (220, 380)]
        tf = lambda x, y: (560 + (x - 220) * 0.6, 400 + (y - 300) * 0.6)
        P = [tf(*q) for q in P]
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([520, 360, 1040, 900], 30, fill=(0, 0, 0, 150), outline=(255, 255, 255, 160), width=3)
        k = max(2, int(len(P) * eout(age / 0.7)))
        dl.polygon(P, fill=(255, 45, 149, int(60 * min(1, age / 0.7))))
        dl.line(P[:k] + ([P[0]] if k == len(P) else []), fill=PINK + (255,), width=10, joint="curve")
        glow_paste(img, lay, 18, 1.1)
        d = ImageDraw.Draw(img)
        for i, (px, py) in enumerate([tf(*q) for q in [(820, 900), (760, 520), (420, 420), (650, 760), (860, 1040)]]):
            ak = age - 0.5 - i * 0.18
            if ak < 0: continue
            e = back(ak / 0.25)
            lay = rgba(); dl = ImageDraw.Draw(lay)
            dl.ellipse([px - 20, py - 60, px + 20, py - 20], fill=GOLD + (255,)); dl.polygon([(px - 17, py - 33), (px + 17, py - 33), (px, py)], fill=GOLD + (255,))
            dl.ellipse([px - 8, py - 48, px + 8, py - 32], fill=(40, 10, 0, 255))
            glow_paste(img, scaled_layer(lay, max(.01, e), px, py), 10, 0.8)
        text_c(d, W / 2, 1230, "FLORIDA MAN ENERGY", ANTON(105), WHITE + (255,), 8, (0, 0, 0, 255))
        text_c(d, W / 2, 260, "TRAILER 1", ANTON(110), GOLD + (255,), 8, (0, 0, 0, 255))
        tg_ = "OFFICIAL SCREENSHOT · GRASSRIVERS"; d.rectangle([40, 1080, 60 + d.textlength(tg_, font=MONT(28, 800)), 1128], fill=(0, 0, 0, 200)); d.text((50, 1088), tg_, font=MONT(28, 800), fill=WHITE)
    elif name == "phone_feed":
        img.paste(photo("vc_beach", p, 1.1, 1.2, dark=0.4, blur=10))
        lay = rgba(); d = ImageDraw.Draw(lay)
        x0, y0, x1, y1 = 240, 170, 840, 1340
        phone_frame(d, x0, y0, x1, y1)
        scr = rgba(x1 - x0 - 44, y1 - y0 - 44); ds = ImageDraw.Draw(scr)
        off = (age * 380) % 330
        for k in range(6):
            yy = k * 330 - off + 100
            fx, fy, fs, fc = FEED[k]
            col = tuple(int(c) for c in np.array([PINK, CYAN, ORANGE, GREEN][k % 4]) * 0.6)
            fk_ = ["gr_gator2", "pg_bbq", "amb_bikers", "jl_bar", "vc_beach", "gr_gator"][k]
            ph_ = photo(fk_, 0.5, 1.0, 1.0, size=(scr.width - 48, 300))
            mk_ = Image.new("L", ph_.size, 0); ImageDraw.Draw(mk_).rounded_rectangle([0, 0, ph_.width, 300], 26, fill=255)
            scr.paste(ph_, (24, int(yy)), mk_)
            ds.polygon([(scr.width / 2 - 30, yy + 110), (scr.width / 2 - 30, yy + 190), (scr.width / 2 + 40, yy + 150)], fill=(255, 255, 255, 230))
            ds.text((44, yy + 240), f"{int(1 + fx * 40)}.{int(fs * 9)}M views", font=MONT(34), fill=(255, 255, 255, 255))
        m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width, scr.height], 52, fill=255)
        lay.paste(scr, (x0 + 22, y0 + 22), m)
        tilt = 6 * math.sin(age * 1.5)
        lay = lay.rotate(tilt, Image.BICUBIC, center=(540, 760))
        glow_paste(img, lay, 26, 0.5)
        d = ImageDraw.Draw(img)
        for k in range(5):
            hy = (age * 520 + k * 260) % 1100
            x = 880 + 30 * math.sin(age * 4 + k)
            hx, hyy, r_ = x, 1300 - hy, 26
            d.ellipse([hx - r_ * 2, hyy - r_, hx, hyy + r_], fill=PINK); d.ellipse([hx, hyy - r_, hx + r_ * 2, hyy + r_], fill=PINK)
            d.polygon([(hx - r_ * 2 + 3, hyy + 8), (hx + r_ * 2 - 3, hyy + 8), (hx, hyy + r_ * 2.6)], fill=PINK)
        stamp(img, W / 2, 1180, "MATCHED TO REAL CLIPS", ANTON(90), GOLD, age - 0.7, rot=-5)
    elif name == "hammers":
        img.paste(photo("redcar", p, 1.0, 1.15, 0.3, 0, dark=0.85))
        lay = rgba(); d = ImageDraw.Draw(lay)
        # car silhouette
        cx, cy = W / 2, 980
        # cracks after hits
        hits = [0.35, 0.75, 1.15, 1.55]
        nh = sum(1 for hh in hits if age > hh)
        rr = np.random.default_rng(4)
        for k in range(nh):
            hx, hy = [(cx - 80, cy - 140), (cx + 110, cy - 130), (cx - 140, cy - 100), (cx + 70, cy - 160)][k]
            for j in range(9):
                ang = rr.uniform(0, 2 * math.pi); L = rr.uniform(40, 120)
                d.line([hx, hy, hx + L * math.cos(ang), hy + L * math.sin(ang)], fill=(255, 255, 255, 255), width=4)
        img.alpha_composite(lay)
        # two hammers swinging alternately
        for side, ph in ((-1, 0.0), (1, 0.4)):
            cyc = ((age + ph) % 0.8) / 0.8
            ang = -70 + 110 * (cyc / 0.5 if cyc < 0.5 else (1 - (cyc - 0.5) / 0.5))
            hl = rgba(); dh = ImageDraw.Draw(hl)
            px, py = cx + side * 260, 560
            dh.rounded_rectangle([px - 14, py - 300, px + 14, py], 8, fill=(150, 90, 40, 255))
            dh.rounded_rectangle([px - 90, py - 360, px + 90, py - 280], 14, fill=(200, 205, 215, 255))
            hl = hl.rotate(side * ang, Image.BICUBIC, center=(px, py))
            img.alpha_composite(hl)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 300, "x2 HAMMERS", ANTON(140), GOLD + (255,), 10, (0, 0, 0, 255))
        text_c(d, W / 2, 1220, "PARODY OF A REAL 2020 VIRAL VIDEO", MONT(42), WHITE + (255,), 4, (0, 0, 0, 255))
    elif name in ("game_box", "box_open"):
        img.paste(photo("preload", p, 1.1, 1.2, dark=0.45, blur=8))
        img.alpha_composite(rays_layer(t, PINK, 12, cy=760, alpha=25))
        lay = rgba(); d = ImageDraw.Draw(lay)
        cx, cy = W / 2, 760
        if name == "game_box":
            sw = abs(math.cos((1 - eout(age / 0.7)) * math.pi * 1.5)) * 0.25 + 0.75 if age < 0.7 else 1
            bw, bh = int(560 * sw), 760
            art = photo("lockload", 0.5, 1.0, 1.0, size=(bw - 40, bh - 150))
            d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 20, fill=(20, 40, 160, 255))
            d.rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy - bh / 2 + 90], fill=(10, 30, 120, 255))
            lay.paste(art.convert("RGBA"), (int(cx - bw / 2 + 20), int(cy - bh / 2 + 110)))
            text_c(d, cx, cy - bh / 2 + 45, "PHYSICAL EDITION", ANTON(int(54 * sw)), WHITE + (255,))
            text_c(d, cx, cy + 250, "GTA 6", ANTON(int(120 * sw)), WHITE + (255,), 8, (60, 0, 80, 255))
            glow_paste(img, scaled_layer(lay, 0.9 + 0.1 * eout(age / 0.5), cx, cy), 30, 0.5)
        else:
            # open case: left inside cover, right empty disc hub
            d.rounded_rectangle([90, cy - 380, 540, cy + 380], 20, fill=(20, 40, 160, 255))
            d.rounded_rectangle([110, cy - 360, 520, cy + 360], 14, fill=(230, 235, 245, 255))
            lay.paste(photo("trailer2", 0.5, 1.0, 1.0, size=(410, 720)), (110, int(cy - 360)))
            d.rounded_rectangle([540, cy - 380, 990, cy + 380], 20, fill=(20, 40, 160, 255))
            d.rounded_rectangle([560, cy - 360, 970, cy + 360], 14, fill=(10, 20, 80, 255))
            d.ellipse([765 - 180, cy - 180, 765 + 180, cy + 180], outline=(60, 80, 160, 255), width=6)
            d.ellipse([765 - 50, cy - 50, 765 + 50, cy + 50], fill=(40, 50, 120, 255), outline=(120, 140, 220, 255), width=6)
            d.rounded_rectangle([170, cy - 120, 460, cy + 60], 14, fill=(255, 255, 255, 255), outline=(30, 30, 30, 255), width=4)
            text_c(d, 315, cy - 75, "DOWNLOAD", MONT(36), (20, 20, 20, 255)); text_c(d, 315, cy - 20, "CODE", MONT(36), (20, 20, 20, 255))
            img.alpha_composite(lay)
            circle_draw(img, 765, cy, 250, 250, (age - 0.2) / 0.5, RED, 14)
            if age > 0.45:
                d2 = ImageDraw.Draw(img)
                k = min(1, (age - 0.45) / 0.2)
                d2.line([765 - 170 * k, cy - 170 * k, 765 + 170 * k, cy + 170 * k], fill=RED, width=26)
                d2.line([765 + 170 * k, cy - 170 * k, 765 - 170 * k, cy + 170 * k], fill=RED, width=26)
            stamp(img, W / 2, 1270, "NO DISC", ANTON(170), RED, age - 0.7, rot=-6)
    elif name == "code_card":
        img.paste(photo("cover", p, 1.0, 1.1, dark=0.8))
        lay = rgba(); d = ImageDraw.Draw(lay)
        e = back(age / 0.35)
        d.rounded_rectangle([120, 560, 960, 1080], 40, fill=(250, 250, 255, 255))
        d.rectangle([120, 640, 960, 700], fill=(30, 30, 40, 255))
        code = "XKQ7-9VLP-2RT4-M8ZD"; k = int(len(code) * min(1, age / 1.0))
        text_c(d, W / 2, 840, code[:k] + ("_" if int(t * 6) % 2 else " ") * (k < len(code)), font("Montserrat-VF.ttf", 70), (20, 20, 30, 255))
        text_c(d, W / 2, 980, "REDEEM ON YOUR CONSOLE STORE", MONT(34), (90, 90, 110, 255))
        glow_paste(img, scaled_layer(lay, max(.01, e), W / 2, 740), 30, 0.5)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 470, "JUST A CODE", ANTON(150), GOLD + (255,), 10, (0, 0, 0, 255))
        if age > 1.0:
            stamp(img, W / 2, 1200, "ROCKSTAR CONFIRMED", ANTON(110), GREEN, age - 1.0, rot=-4, box=True)
    elif name == "hacker_terminal":
        ph_ = np.asarray(photo("masked", p, 1.0, 1.15, 0.3, 0)).astype(np.float32)
        ph_[..., 0] *= 0.45; ph_[..., 2] *= 0.5; ph_[..., 1] *= 0.85
        img.paste(to_img(ph_))
        d = ImageDraw.Draw(img)
        d.rectangle([40, 950, W - 40, 1460], fill=(0, 10, 4, 200))
        mf = MONT(40, 600)
        n = int(age * 9)
        lines = CODE_LINES[: min(len(CODE_LINES), n)]
        for i, ln in enumerate(lines[-9:]):
            c = RED if ln.startswith("!!") else GREEN
            d.text((70, 980 + i * 52), ln, font=mf, fill=c)
        # hooded silhouette with screen glow
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 290, "2022", ANTON(170), GREEN + (255,), 8, (0, 0, 0, 255))
        stamp(img, W / 2, 860, "TEEN HACKER", ANTON(110), RED, age - 0.9, rot=-5)
    elif name == "clips_grid":
        img.paste(photo("vc_night", p, 1.1, 1.2, dark=0.3, blur=6))
        img.alpha_composite(Image.new("RGBA", (W, H), (120, 0, 10, 80)))
        d = ImageDraw.Draw(img)
        n = int(90 * eout(min(1, age / 1.4)))
        cols, cw, ch = 9, 108, 62
        for i in range(n):
            r_, c_ = divmod(i, cols)
            x = 54 + c_ * (cw + 6); y = 370 + r_ * (ch + 6)
            tile = TILES[i]
            img.paste(tile.convert("RGBA"), (int(x), int(y)))
            d.polygon([(x + 44, y + 17), (x + 44, y + 45), (x + 68, y + 31)], fill=(255, 255, 255, 200))
        lay = rgba(); dl = ImageDraw.Draw(lay)
        text_c(dl, W / 2, 1150, f"{n} CLIPS LEAKED", ANTON(130), WHITE + (255,), 12, (60, 0, 0, 255))
        glow_paste(img, lay, 20, 0.8)
        text_c(d, W / 2, 280, "EARLY DEV FOOTAGE", ANTON(100), GOLD + (255,), 8, (0, 0, 0, 255))
    elif name == "hotel_tv":
        img.paste(photo("hotel", p, 1.0, 1.12, 0, 0, dark=0.7))
        d = ImageDraw.Draw(img)
        z = 1 + 0.12 * ease(p)
        tvx0, tvy0, tvx1, tvy1 = 120, 640, 960, 1110
        d.rectangle([tvx0 - 14, tvy0 - 14, tvx1 + 14, tvy1 + 14], fill=(10, 10, 12))
        d.rectangle([tvx0, tvy0, tvx1, tvy1], fill=(4, 20, 8))
        mf = MONT(30, 600)
        for i in range(10):
            ln = CODE_LINES[(i + int(age * 6)) % len(CODE_LINES)]
            d.text((tvx0 + 20, tvy0 + 15 + i * 40), ln, font=mf, fill=GREEN)
        # TV glow
        g = rgba(); ImageDraw.Draw(g).rectangle([tvx0, tvy0, tvx1, tvy1], fill=GREEN + (90,))
        glow_paste(img, g, 80, 1.0, core=False)
        d = ImageDraw.Draw(img)

        img2 = img.resize((int(W * z), int(H * z)), Image.BILINEAR).crop((int((W * z - W) / 2), int((H * z - H) * 0.3), int((W * z - W) / 2) + W, int((H * z - H) * 0.3) + H))
        img.paste(img2)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 290, "HOTEL ROOM", ANTON(140), WHITE + (255,), 10, (0, 0, 0, 255))
        stamp(img, 800, 1180, "ON BAIL", ANTON(100), GOLD, age - 0.8, rot=8)
    elif name == "firestick":
        img.paste(photo("raul_screens", p, 1.0, 1.12, dark=0.42))
        img.alpha_composite(rays_layer(t, ORANGE, 12, cy=760, alpha=30))
        s = 0.7 + 0.35 * eout(age / 0.5) + 0.05 * p
        lay = rgba(); d = ImageDraw.Draw(lay)
        cx, cy = W / 2, 760
        # streaming stick plugged into a port (generic dongle)
        d.rounded_rectangle([cx - 340, cy - 70, cx + 200, cy + 70], 30, fill=(25, 25, 30, 255), outline=(80, 80, 95, 255), width=4)
        d.rectangle([cx + 200, cy - 40, cx + 330, cy + 40], fill=(190, 190, 200, 255))
        d.rectangle([cx + 330, cy - 90, cx + 420, cy + 90], fill=(50, 50, 60, 255))
        d.ellipse([cx - 290, cy - 15, cx - 260, cy + 15], fill=(255, 140, 50, 255))
        glow_paste(img, scaled_layer(lay, s, cx, cy), 20, 0.6)
        if age > 0.5:
            circle_draw(img, cx - 60, cy, 380, 180, (age - 0.5) / 0.45, ORANGE, 14)
        if age > 0.9:
            lay = rgba(); dl = ImageDraw.Draw(lay)
            arrow(dl, 300, 1250, 420, 920, WHITE + (255,), 16, 60)
            img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 300, "A FIRE STICK", ANTON(150), ORANGE + (255,), 10, (0, 0, 0, 255))
        text_c(d, W / 2, 440, "+ THE HOTEL TV", ANTON(100), WHITE + (255,), 8, (0, 0, 0, 255))
    elif name == "money":
        img.paste(photo("vc_money", p, 1.0, 1.18, 0.4, 0, dark=0.8))
        d = ImageDraw.Draw(img)
        for (bx, by, bs, br) in BILLS[:16]:
            y = (by * 600 + age * (400 + bs * 500)) % (H + 300) - 200
            x = bx * W
            bill = rgba(220, 110); db = ImageDraw.Draw(bill)
            db.rounded_rectangle([0, 0, 219, 109], 10, fill=(70, 160, 80, 255), outline=(20, 70, 30, 255), width=5)
            db.ellipse([80, 25, 140, 85], outline=(20, 70, 30, 255), width=4); text_c(db, 110, 55, "$", ANTON(40), (20, 70, 30, 255))
            bill = bill.rotate(br * 360 + age * 90 * (bs - .5), Image.BICUBIC, expand=True)
            img.alpha_composite(bill, (int(x - bill.width / 2), int(y)))
        v = 5_000_000 * eout(min(1, age / 1.3))
        lay = rgba(); dl = ImageDraw.Draw(lay)
        text_c(dl, W / 2, 680, f"${int(v):,}", ANTON(190), GREEN + (255,), 12, (0, 30, 10, 255))
        text_c(dl, W / 2, 870, "COST TO ROCKSTAR", ANTON(100), WHITE + (255,), 8, (0, 0, 0, 255))
        glow_paste(img, lay, 26, 1.0)
    elif name == "gavel":
        img.paste(photo("lucia_prison", p, 1.0, 1.15, 0.3, 0, dark=0.7))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([200, 1020, 880, 1090], 20, fill=(110, 60, 30))
        d.ellipse([380, 960, 700, 1040], fill=(140, 80, 40))
        slam = 0.45
        ang = 55 * (1 - ease(age / slam)) if age < slam else 4 * math.exp(-(age - slam) * 8) * math.sin((age - slam) * 40)
        g = rgba(); dg = ImageDraw.Draw(g)
        px, py = 860, 900
        dg.rounded_rectangle([px - 520, py - 22, px, py + 22], 12, fill=(150, 85, 40, 255))
        dg.rounded_rectangle([px - 640, py - 120, px - 440, py + 120], 30, fill=(120, 65, 30, 255))
        dg.rectangle([px - 640, py - 30, px - 440, py + 30], fill=(200, 160, 60, 255))
        g = g.rotate(-ang, Image.BICUBIC, center=(px, py))
        img.alpha_composite(g)
        text_c(d, W / 2, 310, "THIS WEEK", ANTON(140), WHITE + (255,), 10, (0, 0, 0, 255))
        try:
            gt = word_time("f1", "guilty") - a
        except KeyError:
            gt = 1.2
        stamp(img, W / 2, 620, "GUILTY", ANTON(250), RED, age - gt + 0.1, rot=-8)
        if age > gt + 0.3:
            text_c(d, W / 2, 1240, "LONDON · NOV 16, 2026", MONT(50), GOLD + (255,), 4, (0, 0, 0, 255))
    elif name == "release_date":
        img.paste(photo("jl_sunset", p, 1.15, 1.0, -0.4, 0))
        e = back(age / 0.4)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        cx, cy = W / 2, 620
        dl.rounded_rectangle([cx - 280, cy - 300, cx + 280, cy + 300], 40, fill=(255, 255, 255, 255))
        dl.rounded_rectangle([cx - 280, cy - 300, cx + 280, cy - 140], 40, fill=PINK + (255,))
        dl.rectangle([cx - 280, cy - 180, cx + 280, cy - 140], fill=PINK + (255,))
        text_c(dl, cx, cy - 220, "NOVEMBER", ANTON(100), WHITE + (255,))
        text_c(dl, cx, cy + 70, "19", ANTON(330), (30, 10, 50, 255))
        for rx in (-160, 160): dl.rounded_rectangle([cx + rx - 18, cy - 340, cx + rx + 18, cy - 260], 12, fill=(60, 60, 70, 255))
        glow_paste(img, scaled_layer(lay, max(.01, e), cx, cy), 30, 0.6)
        d = ImageDraw.Draw(img)
        if age > 0.3:
            text_c(d, W / 2, 1040, "PS5 · XBOX SERIES X|S", MONT(54), WHITE + (255,), 5, (0, 0, 0, 255))
    elif name == "comments":
        img.paste(photo("preload", p, 1.0, 1.12, 0.5, 0, dark=0.45))
        d = ImageDraw.Draw(img)
        opts = [("#5", "IN-GAME TRAILER", CYAN), ("#4", "RECORD LEAK", GREEN), ("#3", "FLORIDA CLIPS", ORANGE), ("#2", "NO DISC", PINK), ("#1", "FIRE STICK HACK", GOLD)]
        for i, (n, lab, col) in enumerate(opts):
            ak = age - i * 0.12
            if ak < 0: continue
            e = eout(ak / 0.3)
            lay = rgba(); dl = ImageDraw.Draw(lay)
            y = 260 + i * 175
            dl.rounded_rectangle([110, y, 970, y + 140], 70, fill=(255, 255, 255, 235))
            dl.ellipse([125, y + 15, 235, y + 125], fill=col + (255,))
            text_c(dl, 180, y + 70, n, ANTON(64), (20, 10, 30, 255))
            dl.text((270, y + 34), lab, font=ANTON(70), fill=(20, 10, 30, 255))
            lay = lay.transform((W, H), Image.AFFINE, (1, 0, (1 - e) * (700 if i % 2 else -700), 0, 1, 0))
            img.alpha_composite(lay)
        yb = 1170 + 22 * math.sin(t * 9)
        d.polygon([(W / 2 - 70, yb), (W / 2 + 70, yb), (W / 2, yb + 90)], fill=GOLD)
    else:
        raise KeyError(name)
    return img

# ------------------------------------------------------------------ captions
def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None, 0
    a, b, g = cur[0]
    age = t - a
    pop = max(0.3, back(age / 0.16, 2.2)) if age < 0.16 else 1.0
    f = ANTON(132)
    lay = rgba(W, 420); d = ImageDraw.Draw(lay)
    words = [wd[0] for wd in g]
    full = " ".join(words)
    while d.textlength(full, font=f) + (len(words) - 1) * 0.6 * d.textlength(" ", font=f) > W - 130: f = ANTON(f.size - 6)
    sp = d.textlength(" ", font=f) * 1.6
    x = (W - sum(d.textlength(w_, font=f) for w_ in words) - sp * (len(words) - 1)) / 2
    hl_cols = [GOLD, GREEN, CYAN, PINK]
    for i, (txt, wa, wb, hl) in enumerate(g):
        active = wa - 0.03 <= t < (g[i + 1][1] if i + 1 < len(g) else b)
        spoken = t >= wa - 0.03
        col = (hl_cols[hash(txt) % 2] if hl else WHITE) if spoken else (255, 255, 255)
        alpha = 255 if spoken else 150
        ww = d.textlength(txt, font=f)
        if active:
            wl = rgba(int(ww + 80), 300); dw = ImageDraw.Draw(wl)
            if hl:
                dw.rounded_rectangle([10, 70, ww + 70, 250], 26, fill=(0, 0, 0, 0))
            dw.text((40, 60), txt, font=f, fill=col + (255,), stroke_width=12, stroke_fill=(0, 0, 0, 255))
            ka = min(1, (t - wa + 0.03) / 0.1)
            s = 1.0 + 0.08 * math.sin(ka * math.pi / 2) if hl else 1.0 + 0.04 * ka
            wl = wl.resize((int(wl.width * s), int(wl.height * s)), Image.BICUBIC)
            ch_ = f.size * 0.55
            lay.alpha_composite(wl, (int(x + ww / 2 - (40 + ww / 2) * s), int(90 + ch_ - (60 + ch_) * s)))
        else:
            d.text((x, 80 + 10), txt, font=f, fill=col + (alpha,), stroke_width=12, stroke_fill=(0, 0, 0, alpha))
        x += ww + sp
    if pop != 1:
        nw, nh = int(W * pop), int(420 * pop)
        l2 = lay.resize((nw, nh), Image.BICUBIC); out = rgba(W, 420); out.paste(l2, ((W - nw) // 2, (420 - nh) // 2)); lay = out
    # drop shadow
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(14))
    shadow = Image.new("RGBA", lay.size, (0, 0, 0, 0)); shadow.putalpha(sh.point(lambda v: int(v * 0.6)))
    out = rgba(W, 420); out.alpha_composite(shadow, (0, 10)); out.alpha_composite(lay)
    return out, 1

# ------------------------------------------------------------------ compositing / transitions
CUTS = [s[0] for s in SHOTS[1:]]
NUM_STARTS = [s[0] for s in SHOTS if s[2].startswith("num")]

def frame(t, fi):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0)
    a, b, name, seg = SHOTS[i]
    img = draw_shot(name, t, a, b, seg)
    age = t - a
    # punch-in zoom on every cut + slow drift
    z = 1 + 0.10 * math.exp(-age / 0.09) * (1 if i else 0) + 0.015 * math.sin(t * 0.8)
    if name.startswith("num"): z += 0.0
    # camera shake on impacts
    shake = 0
    for hit in NUM_STARTS:
        if 0 <= t - hit < 0.35: shake = 26 * math.exp(-(t - hit) / 0.08)
    if name == "gavel":
        try:
            gt = word_time("f1", "guilty")
            if 0 <= t - gt < 0.4: shake = max(shake, 30 * math.exp(-(t - gt) / 0.1))
        except KeyError: pass
    if name == "hammers" and (age % 0.4) < 0.08: shake = max(shake, 10)
    if z != 1 or shake:
        z = max(z, 1 + 2.4 * shake / W)
        cw, ch = W / z, H / z
        dx = max(-(W - cw) / 2, min((W - cw) / 2, shake * math.sin(fi * 2.3)))
        dy = max(-(H - ch) / 2, min((H - ch) / 2, shake * math.cos(fi * 3.1)))
        img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2 + dx, (H - ch) / 2 + dy, (W + cw) / 2 + dx, (H + ch) / 2 + dy))
    rgb = img.convert("RGB")
    # whip-blur at cut start
    if i and age < 0.1:
        k = int(60 * (1 - age / 0.1))
        if k > 2:
            arr = np.asarray(rgb).astype(np.float32)
            acc = np.zeros_like(arr)
            for s in range(0, k, max(1, k // 6)): acc += np.roll(arr, s - k // 2, axis=0 if i % 2 else 1)
            rgb = to_img(acc / len(range(0, k, max(1, k // 6))))
    arr = np.asarray(rgb).astype(np.float32)
    # RGB split glitch around cuts
    if i and age < 0.16:
        o = int(22 * (1 - age / 0.16))
        arr = arr.copy(); arr[..., 0] = np.roll(arr[..., 0], o, 1); arr[..., 2] = np.roll(arr[..., 2], -o, 1)
    if name in ("leak_alert", "hacker_terminal") and (int(t * 12) % 9 == 0):
        y0 = int((t * 997) % (H - 200)); arr[y0:y0 + 120] = np.roll(arr[y0:y0 + 120], 60, 1)
    # flash on number cards
    for hit in NUM_STARTS:
        if 0 <= t - hit < 0.18: arr = arr + 255 * (1 - (t - hit) / 0.18) * 0.85
    arr = arr * VIG
    g = GRAIN[fi % 4]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    out = to_img(arr).convert("RGBA")
    cap, _ = caption_layer(t)
    if cap is not None: out.alpha_composite(cap, (0, 1290))
    # secret counter badge + progress bar
    d = ImageDraw.Draw(out)
    cur_n = None
    for sd in SEGMENTS:
        if sd["id"].startswith("n") and t >= SEGT[sd["id"]]["a"] - 0.06: cur_n = sd["id"][1]
    if cur_n and not name.startswith("num") and name not in ("release_date", "comments"):
        d.rounded_rectangle([40, 70, 270, 160], 45, fill=(0, 0, 0, 170), outline=GOLD + (255,), width=4)
        text_c(d, 155, 115, f"SECRET #{cur_n}", ANTON(52), GOLD + (255,))
        tag = "FAN DISCOVERY" if seg == "f3" else "CONFIRMED" if seg.startswith("f") else None
        if tag:
            tw = d.textlength(tag, font=MONT(30))
            ex = 40 if "CONF" in tag else 0
            d.rounded_rectangle([W - 70 - tw - ex, 85, W - 40, 145], 30, fill=(GREEN if "CONF" in tag else ORANGE) + (230,))
            d.text((W - 55 - tw, 96), tag, font=MONT(30), fill=(10, 10, 10, 255))
            if ex: d.line([(W - 92 - tw, 115), (W - 82 - tw, 127), (W - 64 - tw, 102)], fill=(10, 10, 10, 255), width=6)
    if HAVE_OFF:
        d.text((40, H - 70), "IMAGES © ROCKSTAR GAMES · FAN-MADE, NOT AFFILIATED", font=MONT(24, 700), fill=(230, 230, 230, 220))
    pw = W * min(1, t / TOTAL)
    d.rectangle([0, 0, pw, 10], fill=PINK + (255,))
    return out.convert("RGB")

def frame_at(t): return frame(t, int(t * FPS))

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for s in sys.argv[2:]:
            frame_at(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3])
        nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        out = os.path.join(HERE, f"part_{wk}.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
