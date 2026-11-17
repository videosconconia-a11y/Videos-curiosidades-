# Renderer for "THE GTA 6 MAP IS HIDING SOMETHING HUGE!" (1080x1920, 30 fps)
# Map-investigation look: dark satellite-style map, GPS / radar HUD, red circles, yellow markers.
# The base map is an ILLUSTRATION (Florida-shaped, as Leonida is Rockstar's fictional Florida) and is
# labelled as not official. Official Rockstar images, if placed in assets/official/, are used automatically
# (see README) with an on-screen credit.
# Usage: python3 render.py still <t> ... | python3 render.py video <worker> <nworkers>
import sys, os, math, json, subprocess, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS = 1080, 1920, 30
FD = os.path.join(HERE, "fonts")
ANTON = lambda s: ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), s)
def MONT(s, wght=700):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), s)
    try: f.set_variation_by_axes([wght])
    except Exception: pass
    return f
RED = (255, 40, 50); YEL = (255, 214, 0); WHITE = (255, 255, 255); BLACK = (0, 0, 0)
GREY = (150, 155, 165); GREEN = (70, 230, 120); BLUE = (80, 170, 255)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg_id, word):
    for w in SEGT[seg_id]["words"]:
        if clean(w["w"]) == word: return w["a"]
    raise KeyError((seg_id, word))

def build_shots():
    out = []; segs = TM["segments"]
    for i, (sd, st) in enumerate(zip(SEGMENTS, segs)):
        s0 = 0.0 if i == 0 else st["a"] - 0.06
        s1 = segs[i + 1]["a"] - 0.06 if i + 1 < len(segs) else TOTAL
        starts = [(s0 if cue is None else word_time(sd["id"], cue) - 0.08, name) for name, cue in sd["shots"]]
        for j, (a, name) in enumerate(starts):
            out.append((a, starts[j + 1][0] if j + 1 < len(starts) else s1, name, sd["id"]))
    return out
SHOTS = build_shots()

def build_captions():
    caps = []
    for sd in SEGMENTS:
        ws = []; spelled = False
        for w in SEGT[sd["id"]]["words"]:
            txt = w["w"].strip(); core = txt.rstrip(".,?!")
            single = len(core) == 1 and core.isalpha() and core.isupper() and core not in ("I",)
            if ws and single and spelled:          # G T A -> GTA, U S -> US
                ws[-1] = (ws[-1][0] + core + txt[len(core):], ws[-1][1], w["b"], True); continue
            if ws and ws[-1][0] == "GTA" and txt[:1].isdigit():
                ws[-1] = ("GTA " + txt.upper(), ws[-1][1], w["b"], True); spelled = False; continue
            spelled = single and core != "A" or (single and core == "A" and False)
            if single and core in ("G", "U"): spelled = True
            ws.append((txt.upper(), w["a"], w["b"], clean(txt) in sd["hl"]))
        group = []
        for k, wd in enumerate(ws):
            group.append(wd)
            if wd[0][-1] in ".,?!:" or len(group) >= 3 or sum(len(g[0]) for g in group) > 13 or k == len(ws) - 1:
                caps.append(group); group = []
    out = []
    for i, g in enumerate(caps):
        a = g[0][1] - 0.05
        b = caps[i + 1][0][1] - 0.05 if i + 1 < len(caps) else g[-1][2] + 0.4
        out.append((a, min(b, g[-1][2] + 0.45), g))
    return out
CAPS = build_captions()

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))
def glow_paste(img, lay, r=16, k=1.0, core=True):
    g = lay.filter(ImageFilter.GaussianBlur(r))
    if k != 1.0:
        a = np.asarray(g).astype(np.float32); a[..., 3] *= k; g = to_img(a)
    img.alpha_composite(g)
    if core: img.alpha_composite(lay)
def tsize(d, s, f):
    x0, y0, x1, y1 = d.textbbox((0, 0), s, font=f); return x1 - x0, y1 - y0, x0, y0
def text_c(d, cx, cy, s, f, fill, stroke=0, sc=(0, 0, 0, 255)):
    w, h, ox, oy = tsize(d, s, f); d.text((cx - w / 2 - ox, cy - h / 2 - oy), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sc)
def scaled(lay, s, cx, cy):
    s = max(0.02, s)
    if abs(s - 1) < 1e-3: return lay
    big = lay.resize((max(1, int(W * s)), max(1, int(H * s))), Image.BICUBIC)
    out = rgba(); out.paste(big, (int(cx - cx * s), int(cy - cy * s)), big); return out
def stamp(img, cx, cy, s, f, col, age, rot=-6, box=True, fill=None):
    if age < 0: return
    sc = 1 + 1.4 * (1 - eout(age / 0.16)) if age < 0.16 else 1.0
    lay = rgba(); d = ImageDraw.Draw(lay); w, h, _, _ = tsize(d, s, f)
    if box: d.rectangle([cx - w / 2 - 34, cy - h / 2 - 26, cx + w / 2 + 34, cy + h / 2 + 26], fill=fill, outline=col + (255,), width=10)
    text_c(d, cx, cy, s, f, col + (255,) if not fill else WHITE + (255,))
    lay = scaled(lay.rotate(rot, Image.BICUBIC, center=(cx, cy)), sc, cx, cy)
    glow_paste(img, lay, 14, 0.7)
def red_circle(img, cx, cy, rx, ry, p, col=RED, wdt=12):
    lay = rgba(); d = ImageDraw.Draw(lay); n = 64; k = int(n * 1.12 * ease(p))
    pts = [(cx + rx * (1 + .05 * math.sin(i * .8)) * math.cos(-2 + i / n * 2 * math.pi * 1.1),
            cy + ry * (1 + .05 * math.cos(i * 1.2)) * math.sin(-2 + i / n * 2 * math.pi * 1.1)) for i in range(k)]
    if len(pts) > 1: d.line(pts, fill=col + (255,), width=wdt, joint="curve")
    glow_paste(img, lay, 10, 0.8)
def arrow(img, x0, y0, x1, y1, p, col=YEL, wdt=14):
    p = eout(p)
    if p <= 0: return
    xe, ye = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    lay = rgba(); d = ImageDraw.Draw(lay); d.line([x0, y0, xe, ye], fill=col + (255,), width=wdt)
    ang = math.atan2(ye - y0, xe - x0); hd = 46
    d.polygon([(xe + 12 * math.cos(ang), ye + 12 * math.sin(ang)), (xe - hd * math.cos(ang - .5), ye - hd * math.sin(ang - .5)),
               (xe - hd * math.cos(ang + .5), ye - hd * math.sin(ang + .5))], fill=col + (255,))
    glow_paste(img, lay, 8, 0.6)

# ------------------------------------------------------------------ illustrative Leonida (Florida-shaped) map
FL = [(-87.63, 30.85), (-87.6, 31.0), (-85.0, 31.0), (-84.86, 30.71), (-83.5, 30.64), (-82.2, 30.57), (-82.04, 30.36), (-81.95, 30.82),
      (-81.45, 30.71), (-81.3, 30.0), (-81.0, 29.3), (-80.6, 28.6), (-80.55, 28.0), (-80.35, 27.4), (-80.05, 26.7), (-80.1, 26.0),
      (-80.2, 25.6), (-80.4, 25.25), (-80.9, 25.15), (-81.15, 25.4), (-81.35, 25.8), (-81.8, 26.1), (-82.1, 26.6), (-82.6, 27.3),
      (-82.8, 27.9), (-82.65, 28.6), (-82.75, 29.0), (-83.1, 29.3), (-83.65, 29.9), (-84.0, 30.1), (-84.4, 29.9), (-85.0, 29.6),
      (-85.35, 29.7), (-85.6, 30.1), (-86.2, 30.4), (-87.0, 30.35), (-87.5, 30.3)]
KEYS = [(-80.45 - k * 0.11, 25.05 - k * 0.042 - 0.012 * k * k / 6) for k in range(13)]
LAKE = (-80.83, 26.95)
MW, MH = 3200, 3700
LON0, LON1, LAT0, LAT1 = -90.5, -78.5, 22.4, 33.8
def proj(lon, lat):
    k = math.cos(math.radians(27.5))
    x = (lon - LON0) / (LON1 - LON0) * MW
    y = (LAT1 - lat) / (LAT1 - LAT0) * MH * (1 / k) * ((LON1 - LON0) / (LAT1 - LAT0)) * (LAT1 - LAT0) / (LON1 - LON0) * k / k
    return x, y
def proj(lon, lat):  # equirectangular, x scaled by cos(lat)
    sx = MW / ((LON1 - LON0) * math.cos(math.radians(27.5)))
    x = (lon - LON0) * math.cos(math.radians(27.5)) * sx
    y = (LAT1 - lat) * sx
    return x, y
PLACES = {  # real-world analogues used as approximate positions on the illustration
    "vice": (-80.25, 25.85), "keys": (-81.0, 24.85), "grass": (-80.95, 25.75), "ambrosia": (-80.95, 26.75),
    "kalaga": (-82.4, 30.25), "britton": (-86.28, 30.99), "lake": LAKE, "north": (-83.2, 30.4),
}
def noise(w, h, scale, seed):
    r = np.random.default_rng(seed); s = r.random((h // scale + 2, w // scale + 2))
    return np.asarray(Image.fromarray((s * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255

def build_map():
    print("building map", flush=True)
    mask = Image.new("L", (MW, MH), 0); dm = ImageDraw.Draw(mask)
    dm.polygon([proj(*p) for p in FL], fill=255)
    for (lo, la) in KEYS:
        x, y = proj(lo, la); dm.ellipse([x - 26, y - 9, x + 26, y + 9], fill=255)
    lx, ly = proj(*LAKE); lake = Image.new("L", (MW, MH), 0); ImageDraw.Draw(lake).ellipse([lx - 70, ly - 80, lx + 70, ly + 75], fill=255)
    # out-of-bounds land north of the state line (not part of Leonida)
    oob = Image.new("L", (MW, MH), 0); do = ImageDraw.Draw(oob)
    do.polygon([proj(-90.5, 30.3), proj(-87.5, 30.3), proj(-87.6, 31.0), proj(-85.0, 31.0), proj(-84.86, 30.71), proj(-83.5, 30.64),
                proj(-82.2, 30.57), proj(-82.04, 30.36), proj(-81.95, 30.82), proj(-81.45, 30.71), proj(-81.1, 31.8), proj(-80.6, 33.8), proj(-90.5, 33.8)], fill=255)
    ob = np.asarray(oob, np.float32) / 255
    m = np.asarray(mask, np.float32) / 255; lk = np.asarray(lake, np.float32) / 255
    n1 = noise(MW, MH, 6, 1); n2 = noise(MW, MH, 40, 2); n3 = noise(MW, MH, 140, 3)
    ocean = np.stack([6 + 10 * n2, 12 + 16 * n2, 22 + 24 * n2], -1)
    # shallow water glow near coast
    coast = np.asarray(mask.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255
    ocean += (coast * (1 - m))[..., None] * np.array([10, 60, 70])
    land = np.stack([40 + 30 * n3 + 18 * n1, 48 + 34 * n3 + 18 * n1, 36 + 18 * n3 + 12 * n1], -1)
    # wetlands in the south (greener/darker), north forests (darker green)
    yy = np.arange(MH)[:, None] / MH
    land *= (0.8 + 0.3 * n2)[..., None]
    _, ys = proj(-81, 26.3)
    wet = np.clip((np.arange(MH)[:, None] - ys) / 300, 0, 1) * np.ones((1, MW))
    land = land * (1 - wet[..., None] * 0.3) + wet[..., None] * np.array([20, 50, 35]) * 0.3
    a = ocean * (1 - m[..., None]) + land * m[..., None]
    a = a * (1 - lk[..., None]) + lk[..., None] * np.array([14, 34, 50])
    gray = np.stack([48 + 18 * n3, 48 + 18 * n3, 54 + 18 * n3], -1)
    a = a * (1 - ob[..., None]) + gray * ob[..., None]
    img = to_img(a)
    dh = ImageDraw.Draw(img)
    for k in range(-MH, MW, 40): dh.line([k, 0, k + MH, MH], fill=(70, 70, 76), width=3)
    img = Image.composite(img, to_img(a), oob)
    d = ImageDraw.Draw(img)
    # roads (thin light lines between analogue cities)
    for path in [[(-80.2, 25.8), (-80.1, 26.6), (-80.5, 27.6), (-81.0, 28.9), (-81.5, 30.3)], [(-82.4, 27.95), (-81.4, 28.5), (-80.6, 28.1)],
                 [(-80.2, 25.8), (-81.0, 26.2), (-81.8, 26.2)], [(-87.2, 30.5), (-84.3, 30.45), (-82.0, 30.35)], [(-80.4, 25.25), (-81.75, 24.56)]]:
        d.line([proj(*p) for p in path], fill=(120, 125, 120), width=3)
    # lat/lon grid
    for lo in np.arange(-88, -79, 1.0):
        x, _ = proj(lo, 30); d.line([x, 0, x, MH], fill=(255, 255, 255, 30), width=1)
    for la in np.arange(24, 32, 1.0):
        _, y = proj(-85, la); d.line([0, y, MW, y], fill=(255, 255, 255, 30), width=1)
    # coastline glow
    edge = mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
    e = np.asarray(edge, np.float32)[..., None] / 255
    ab = np.asarray(img, np.float32)
    eg = np.asarray(edge.filter(ImageFilter.GaussianBlur(8)), np.float32)[..., None] / 255
    ab = ab + eg * 120 + e * 160
    # city lights in SE (Vice City analogue)
    r = np.random.default_rng(4)
    for _ in range(1600):
        lo, la = r.normal(-80.25, 0.12), r.normal(25.95, 0.28)
        x, y = proj(lo, la)
        if 0 < x < MW and 0 < y < MH and m[int(y), int(x)] > 0.5:
            ab[int(y) - 1:int(y) + 2, int(x) - 1:int(x) + 2] += np.array([255, 200, 120]) * r.uniform(.3, .9)
    return to_img(ab)
MAP = build_map()
MAP_BLUR = MAP.filter(ImageFilter.GaussianBlur(10))

def map_view(lon, lat, zoom, rot=0.0, src=None):
    """W x H view centered at (lon, lat); zoom=1 shows ~1080 map px wide"""
    src = src or MAP
    cx, cy = proj(lon, lat)
    cw = W / zoom; ch = H / zoom
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    pad = Image.new("RGB", (int(cw) + 2, int(ch) + 2), (6, 12, 22))
    crop = src.crop(tuple(int(v) for v in box))
    pad.paste(crop, (0, 0))
    v = pad.resize((W, H), Image.BILINEAR)
    if rot: v = v.rotate(rot, Image.BILINEAR, fillcolor=(6, 12, 22))
    return v.convert("RGBA")
def to_screen(lon, lat, clon, clat, zoom):
    x, y = proj(lon, lat); cx, cy = proj(clon, clat)
    return W / 2 + (x - cx) * zoom, H / 2 + (y - cy) * zoom
def lerp(a, b, p): return a + (b - a) * p
def camlerp(c0, c1, p):
    p = ease(p); return (lerp(c0[0], c1[0], p), lerp(c0[1], c1[1], p), c0[2] * (c1[2] / c0[2]) ** p)

# ------------------------------------------------------------------ "photo" plates: official image if provided, else illustration
def load_official(key):
    fs = sorted(glob.glob(os.path.join(HERE, "assets", "official", key + ".*")))
    if not fs: return None
    im = Image.open(fs[0]).convert("RGB"); s = max(1350 / im.width, 2400 / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
def plate_mountains():
    w, h = 1350, 2400
    sky = np.linspace(0, 1, h)[:, None, None]
    a = np.array([255, 170, 90]) * (1 - sky) * 0.0 + np.array([30, 60, 110]) * (1 - sky) + np.array([255, 160, 90]) * sky
    a = np.broadcast_to(a, (h, w, 3)).copy()
    img = to_img(a); d = ImageDraw.Draw(img)
    r = np.random.default_rng(5)
    for li, (base, amp, col) in enumerate([(1050, 480, (70, 80, 110)), (1250, 380, (45, 60, 70)), (1450, 300, (25, 45, 40)), (1650, 200, (14, 30, 22))]):
        xs = np.arange(0, w + 10, 10)
        prof = base - amp * (0.55 + 0.45 * np.sin(xs * 0.004 + li * 1.7)) * (0.7 + 0.3 * np.sin(xs * 0.013 + li)) - r.normal(0, 8, len(xs)).cumsum() * 0.2
        d.polygon([(0, h)] + list(zip(xs, prof)) + [(w, h)], fill=col)
        if li >= 2:
            for x in range(0, w, 18):
                yb = np.interp(x, xs, prof) + 4; th = r.uniform(30, 70)
                d.polygon([(x - 12, yb + th * .3), (x + 12, yb + th * .3), (x, yb - th)], fill=tuple(int(c * .8) for c in col))
    d.line([(600, h), (650, 2000), (760, 1850), (700, 1720)], fill=(140, 180, 210), width=40)
    return img.filter(ImageFilter.GaussianBlur(1.2))
def plate_city():
    w, h = 1350, 2400
    sky = np.linspace(0, 1, h)[:, None, None]
    a = np.broadcast_to(np.array([40, 20, 70]) * (1 - sky) + np.array([255, 120, 90]) * sky, (h, w, 3)).copy()
    img = to_img(a); d = ImageDraw.Draw(img); r = np.random.default_rng(8); x = -20
    while x < w:
        bw = r.uniform(60, 150); bh = r.uniform(300, 900)
        d.rectangle([x, 1600 - bh, x + bw, 1600], fill=(20, 12, 30))
        for wy in range(int(1600 - bh) + 20, 1580, 28):
            for wx in range(int(x) + 10, int(x + bw) - 12, 22):
                if r.random() < .3: d.rectangle([wx, wy, wx + 9, wy + 12], fill=(255, 210, 140))
        x += bw + 6
    d.rectangle([0, 1600, w, h], fill=(20, 40, 70))
    return img
# ---- official Rockstar screenshots (assets/official, fetched by fetch_official.sh) — © Rockstar Games
FOCAL = {"hero": 0.45, "vice_sign": 0.5, "vice_night": 0.55, "keys": 0.55, "keys_boats": 0.4, "grass": 0.5, "grass_town": 0.5,
         "ambrosia": 0.5, "ambrosia_sunset": 0.42, "kalaga_heli": 0.38, "kalaga_canyon": 0.5, "kalaga_forest": 0.36,
         "kalaga_river": 0.48, "kalaga_trails": 0.5, "gellhorn": 0.32}
def _load(key):
    fs = sorted(glob.glob(os.path.join(HERE, "assets", "official", key + ".jpg")))
    if not fs: return None
    im = Image.open(fs[0]).convert("RGB"); s_ = 2300 / im.height
    return im.resize((int(im.width * s_), 2300), Image.LANCZOS)
OFF = {k: _load(k) for k in FOCAL}
HAVE_OFF = all(v is not None for v in OFF.values())
def off_view(key, p, z0=1.0, z1=1.12, dx=0.0, dy=0.0, dark=1.0, blur=0, focal=None):
    im = OFF.get(key)
    if im is None:   # fallback: illustration
        v = plate_view("kalaga" if "kalaga" in key else "vice", p, z0, z1)
    else:
        z = lerp(z0, z1, ease(p) * .5 + p * .5)
        ch = im.height / z; cw = ch * W / H
        cx = im.width * (focal if focal is not None else FOCAL[key]) + dx * (p - .5) * cw * 0.25; cy = im.height / 2 + dy * (p - .5) * (im.height - ch)
        cx = min(max(cx, cw / 2), im.width - cw / 2); cy = min(max(cy, ch / 2), im.height - ch / 2)
        v = im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)).convert("RGBA")
    if blur: v = v.filter(ImageFilter.GaussianBlur(blur))
    if dark != 1.0:
        a = np.asarray(v).astype(np.float32); a[..., :3] *= dark; v = to_img(a)
    return v
def off_inset(img, key, x, y, w, p, age, label="© ROCKSTAR GAMES"):
    im = OFF.get(key)
    if im is None or age < 0: return
    k = eout(age / 0.3); h = int(w * 9 / 16)
    z = 1.0 + 0.08 * p; cw = im.width / z; ch = cw * 9 / 16
    box = (im.width / 2 - cw / 2, im.height / 2 - ch / 2, im.width / 2 + cw / 2, im.height / 2 + ch / 2)
    ins = im.resize((w, h), Image.BILINEAR, box=box).convert("RGBA")
    xo = int(x + (1 - k) * 700)
    lay = rgba(); lay.paste(ins, (xo, y)); dl = ImageDraw.Draw(lay)
    dl.rectangle([xo, y, xo + w, y + h], outline=WHITE + (255,), width=6)
    img.alpha_composite(lay)
    tag(ImageDraw.Draw(img), xo, y + h - 46, label, WHITE)
LENS = (70, 560, 1010, 1270)
LENS_MASK = Image.new("L", (W, H), 0); ImageDraw.Draw(LENS_MASK).rounded_rectangle(LENS, 36, fill=255)
MAP_BG = {"hook_scan": "hero", "hook_map": "hero", "leonida_reveal": "keys", "florida_overlay": "keys", "pin_vice": "hero",
          "pin_keys": "keys", "pin_grass": "grass", "pin_ambrosia": "ambrosia_sunset", "scan_north": "ambrosia_sunset",
          "edge": "kalaga_heli", "kalaga_lock": "kalaga_heli", "britton": "vice_night", "hiding": "gellhorn"}
PLATES = {"hero": load_official("hero"), "vice": load_official("vice"), "kalaga": load_official("kalaga"),
          "keys": load_official("keys"), "grass": load_official("grass")}
OFFICIAL_ANY = any(v is not None for v in PLATES.values())
FALLBACK = {"kalaga": plate_mountains(), "vice": plate_city()}
def plate(key):
    return PLATES.get(key) or PLATES.get("hero") or FALLBACK.get(key) or FALLBACK["vice"]
def plate_is_official(key): return PLATES.get(key) is not None or PLATES.get("hero") is not None
def plate_view(key, p, z0=1.0, z1=1.15, dx=0.0, dy=0.0):
    im = plate(key); z = lerp(z0, z1, ease(p) * .5 + p * .5)
    cw = im.width / z; ch = cw * H / W
    if ch > im.height: ch = im.height / 1.0; cw = ch * W / H
    cx = im.width / 2 + dx * (p - .5) * (im.width - cw); cy = im.height / 2 + dy * (p - .5) * (im.height - ch)
    cx = min(max(cx, cw / 2), im.width - cw / 2); cy = min(max(cy, ch / 2), im.height - ch / 2)
    return im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)).convert("RGBA")

# ------------------------------------------------------------------ HUD elements
YY, XX = np.mgrid[0:H, 0:W]
VIG = np.clip(1.2 - (((XX - W / 2) / (W * .6)) ** 2 + ((YY - H / 2) / (H * .6)) ** 2) * .6, .25, 1)[..., None].astype(np.float32)
GRAIN = [np.random.default_rng(k).standard_normal((H // 2, W // 2)).astype(np.float32) * 5 for k in range(4)]
SCAN = (np.sin(np.arange(H) * math.pi / 3) * 0.5 + 0.5).astype(np.float32)[:, None, None] * 8

def radar_sweep(img, t, cx, cy, R, col=RED, alpha=110):
    ang = np.arctan2(YY - cy, XX - cx); a0 = (t * 2.2) % (2 * math.pi) - math.pi
    dlt = (ang - a0) % (2 * math.pi)
    r = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)
    m = np.exp(-dlt / 0.5) * (r < R)
    arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = col; arr[..., 3] = np.clip(m * alpha, 0, 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(arr))
    d = ImageDraw.Draw(img)
    for k in (0.33, 0.66, 1.0): d.ellipse([cx - R * k, cy - R * k, cx + R * k, cy + R * k], outline=col + (90,), width=3)
    d.line([cx - R, cy, cx + R, cy], fill=col + (60,), width=2); d.line([cx, cy - R, cx, cy + R], fill=col + (60,), width=2)

def marker(img, x, y, age, col=YEL, label=None, sub=None, side=1, official=False):
    if age < 0: return
    e = back(age / 0.3); lay = rgba(); d = ImageDraw.Draw(lay)
    # pulse rings
    for k in range(2):
        ph = ((age * 1.3) + k * .5) % 1
        rr = 20 + 90 * ph
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=col + (int(220 * (1 - ph)),), width=5)
    d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=col + (255,), outline=BLACK + (255,), width=4)
    # pin
    d.polygon([(x - 30, y - 70), (x + 30, y - 70), (x, y - 20)], fill=col + (255,))
    d.ellipse([x - 34, y - 120, x + 34, y - 52], fill=col + (255,)); d.ellipse([x - 13, y - 99, x + 13, y - 73], fill=BLACK + (255,))
    lay = scaled(lay, e, x, y)
    glow_paste(img, lay, 12, 0.7)
    if label and age > 0.2:
        ka = eout((age - 0.2) / 0.3)
        f = ANTON(66); d = ImageDraw.Draw(img)
        tw = d.textlength(label, font=f); sw = d.textlength(sub, font=MONT(34)) if sub else 0
        bw = max(tw, sw) + 50
        bx = x + side * 70 if side > 0 else x - 70 - bw
        bx = min(max(bx, 40), W - 40 - bw)
        by = y - 150
        bwk = bw * ka
        box = rgba(); db = ImageDraw.Draw(box)
        db.rectangle([bx, by, bx + bwk, by + (130 if sub else 90)], fill=(0, 0, 0, 215))
        db.rectangle([bx, by, bx + 8, by + (130 if sub else 90)], fill=col + (255,))
        db.line([x + side * 30, y - 60, bx if side > 0 else bx + bw, by + 45], fill=col + (255,), width=4)
        img.alpha_composite(box)
        if ka > 0.95:
            d.text((bx + 28, by + 6), label, font=f, fill=WHITE)
            if sub: d.text((bx + 30, by + 86), sub, font=MONT(34), fill=col)

def tag(d, x, y, s, col, txtcol=BLACK, f=None):
    f = f or MONT(30, 800); tw = d.textlength(s, font=f)
    d.rectangle([x, y, x + tw + 28, y + 50], fill=col); d.text((x + 14, y + 8), s, font=f, fill=txtcol)
    return tw + 28

def corner_brackets(d, x0, y0, x1, y1, col, L=60, w=7):
    for (x, y, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([x, y, x + sx * L, y], fill=col, width=w); d.line([x, y, x, y + sy * L], fill=col, width=w)

def coords_text(lon, lat):
    return f"{abs(lat):06.3f}°N  {abs(lon):07.3f}°W"

# ------------------------------------------------------------------ shots
CAM = {}  # name -> (start view, end view)  view=(lon, lat, zoom)
FULL = (-83.4, 27.6, 0.40)
CAM.update({
    "hook_scan": ((-82.5, 28.8, 0.55), (-82.6, 29.6, 0.75)),
    "hook_map": ((-83.4, 27.6, 0.50), (-83.4, 27.6, 0.40)),
    "leonida_reveal": ((-83.4, 27.4, 0.36), (-83.3, 27.6, 0.42)),
    "florida_overlay": ((-83.3, 27.6, 0.42), (-83.3, 27.6, 0.44)),
    "pin_vice": ((-81.0, 26.5, 0.6), (-80.45, 25.95, 1.6)),
    "pin_keys": ((-80.6, 25.6, 1.4), (-80.95, 25.05, 1.5)),
    "pin_grass": ((-80.95, 25.3, 1.4), (-80.9, 25.8, 1.3)),
    "scan_north": ((-80.9, 25.9, 1.1), (-81.5, 28.8, 0.6)),
    "pin_ambrosia": ((-81.0, 26.4, 1.0), (-80.9, 26.9, 1.25)),
    "edge": ((-81.6, 28.5, 0.65), (-82.6, 30.0, 0.85)),
    "kalaga_lock": ((-82.5, 30.0, 0.9), (-82.4, 30.2, 1.5)),
    "britton": ((-85.5, 30.4, 0.8), (-86.2, 30.8, 1.4)),
    "punch": ((-82.8, 29.4, 0.5), (-82.5, 29.9, 0.62)),
    "hiding": ((-83.4, 27.6, 0.46), (-83.4, 27.6, 0.40)),
})

def map_frame(name, p, t, blur=False):
    c0, c1 = CAM[name]; lon, lat, z = camlerp(c0, c1, p)
    return map_view(lon, lat, z, src=MAP_BLUR if blur else MAP), (lon, lat, z)

def draw_shot(name, t, a, b, seg):
    p = (t - a) / max(1e-3, b - a); age = t - a
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    view = None
    if name in CAM and name != "punch":
        mapimg, view = map_frame(name, p, t)
        img.paste(off_view(MAP_BG.get(name, "hero"), p, 1.05, 1.18, 0.4, 0.2, dark=0.62))
        lk = 1.0
        if name == "hook_scan": lk = eout((age - 0.9) / 0.35)
        if lk > 0:
            m = LENS_MASK if lk >= 1 else scaled(Image.merge("RGBA", [LENS_MASK] * 4), lk, W / 2, 915).split()[3]
            mm = np.asarray(m).astype(np.float32) * 0.94
            img.paste(mapimg, (0, 0), to_img(mm).convert("L"))
            dd = ImageDraw.Draw(img)
            if lk >= 1:
                dd.rounded_rectangle(LENS, 36, outline=(255, 255, 255, 200), width=4)
                corner_brackets(dd, LENS[0] - 12, LENS[1] - 12, LENS[2] + 12, LENS[3] + 12, YEL, 50, 6)
        d = ImageDraw.Draw(img)
    elif name == "punch":
        view = None
    S = lambda key: to_screen(*PLACES[key], *view)

    if name == "hook_scan":
        radar_sweep(img, t, W / 2, 915, 520)
        d = ImageDraw.Draw(img)
        if age > 1.1:
            x, y = S("kalaga"); red_circle(img, x, y, 170, 130, (age - 1.1) / 0.5)
        text_c(d, W / 2, 330, "GTA 6", ANTON(260), WHITE + (255,), 12)
        tag(d, 330, 470, "MAP INTEL // CLASSIFIED", RED, WHITE)
    elif name == "hook_map":
        x, y = S("kalaga")
        red_circle(img, x, y, 150, 120, 1.0)
        arrow(img, x + 300, y - 280, x + 120, y - 100, age / 0.35, YEL)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        text_c(dl, x, y - 10, "?", ANTON(200), RED + (255,), 10)
        glow_paste(img, scaled(lay, back(age / .3), x, y), 16, 1)
        stamp(img, W / 2, 330, "LOOK CLOSER", ANTON(140), YEL, age - 0.2, rot=-3, box=False)
    elif name == "leonida_reveal":
        if plate_is_official("hero") and p < 0.0: pass
        d = ImageDraw.Draw(img)
        s = "STATE OF LEONIDA"; k = int(len(s) * min(1, age / 0.7))
        text_c(d, W / 2, 300, s[:k], ANTON(120), WHITE + (255,), 8)
        tag(d, W / 2 - 150, 390, "ROCKSTAR'S FICTIONAL STATE", YEL)
        for i, key in enumerate(["vice", "grass", "keys", "lake", "ambrosia", "kalaga"]):
            x, y = S(key); ak = age - 0.3 - i * 0.12
            if ak > 0:
                rr = 14 * back(ak / .25); d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=YEL + (255,), outline=BLACK + (255,), width=3)
    elif name == "florida_overlay":
        lay = rgba(); dl = ImageDraw.Draw(lay)
        k = ease(age / 0.7); off = (1 - k) * 260; rot = (1 - k) * 14
        pts = [to_screen(*pp, *view) for pp in FL] + [to_screen(*FL[0], *view)]
        pts = [(x + off, y - off * .5) for x, y in pts]
        for i in range(0, len(pts) - 1):
            if i % 2 == 0: dl.line([pts[i], pts[i + 1]], fill=WHITE + (255,), width=7)
        lay = lay.rotate(rot, Image.BICUBIC, center=(W / 2, H / 2))
        glow_paste(img, lay, 10, 1)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 300, "LEONIDA", ANTON(120), YEL + (255,), 8)
        text_c(d, W / 2, 420, "= FLORIDA", ANTON(120), WHITE + (255,), 8)
    elif name in ("pin_vice", "pin_keys", "pin_grass", "pin_ambrosia"):
        key = name[4:]
        lab = {"vice": ("VICE CITY", "REAL-WORLD MATCH: MIAMI"), "keys": ("LEONIDA KEYS", "REAL-WORLD MATCH: FLORIDA KEYS"),
               "grass": ("GRASSRIVERS", "WETLANDS · LIKE THE EVERGLADES"), "ambrosia": ("AMBROSIA", "SUGAR REFINERY · LAKE LEONIDA")}[key]
        x, y = S(key)
        if key == "ambrosia":
            lx, ly = S("lake"); red_circle(img, lx, ly, 110, 110, (age - 0.4) / 0.5, RED, 7)
        marker(img, x, y, age - 0.05, YEL, lab[0], lab[1], side=1 if x < W / 2 else -1)
        ins = {"vice": "vice_sign", "keys": "keys_boats", "grass": "grass_town", "ambrosia": "ambrosia"}[key]
        off_inset(img, ins, 250, 175, 620, p, age - 0.25)
        d = ImageDraw.Draw(img)
        tag(d, 40, 110, "OFFICIAL LOCATION", GREEN)
    elif name == "river_grass":
        img.paste(off_view("grass", p, 1.1, 1.25, -0.4, 0, dark=0.5)); d = ImageDraw.Draw(img)
        e = back(age / 0.35); lay = rgba(); dl = ImageDraw.Draw(lay)
        cx, cy = W / 2, 760
        dl.rectangle([cx - 300, cy - 420, cx + 300, cy + 420], fill=(232, 222, 196, 255), outline=(60, 50, 40, 255), width=6)
        dl.rectangle([cx - 300, cy - 420, cx + 300, cy - 240], fill=(60, 110, 70, 255))
        text_c(dl, cx, cy - 330, "THE EVERGLADES", ANTON(80), WHITE + (255,))
        text_c(dl, cx, cy - 60, "RIVER", ANTON(170), (40, 70, 40, 255))
        text_c(dl, cx, cy + 110, "OF GRASS", ANTON(140), (40, 70, 40, 255))
        text_c(dl, cx, cy + 300, "MARJORY STONEMAN DOUGLAS · 1947", MONT(30), (60, 50, 40, 255))
        for gx in range(int(cx - 280), int(cx + 280), 14):
            hgt = 40 + 30 * math.sin(gx * .3)
            dl.line([gx, cy + 400, gx + 6 * math.sin(t * 3 + gx), cy + 400 - hgt], fill=(80, 130, 70, 255), width=4)
        glow_paste(img, scaled(lay, e, cx, cy), 20, .5)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 230, "GRASS + RIVERS", ANTON(110), YEL + (255,), 8)
        if age > 0.6: stamp(img, W / 2, 1190, "FAN THEORY", ANTON(90), YEL, age - 0.6, rot=-4)
    elif name == "scan_north":
        # GPS route drawn north from Vice City
        route = [(-80.25, 25.85), (-80.15, 26.6), (-80.6, 27.5), (-81.2, 28.4), (-81.9, 29.3), (-82.4, 30.1)]
        k = ease(p * 1.1)
        pts = [to_screen(*r, *view) for r in route]
        n = max(2, int(len(pts) * k) + 1); seg_pts = pts[:n]
        lay = rgba(); dl = ImageDraw.Draw(lay); dl.line(seg_pts, fill=YEL + (255,), width=12, joint="curve")
        glow_paste(img, lay, 10, 1)
        d = ImageDraw.Draw(img)
        hx, hy = seg_pts[-1]; d.polygon([(hx, hy - 34), (hx - 24, hy + 22), (hx, hy + 8), (hx + 24, hy + 22)], fill=WHITE)
        text_c(d, W / 2, 300, "HEADING NORTH", ANTON(130), WHITE + (255,), 8)
        arrow(img, W / 2, 560, W / 2, 420, (age % 0.8) / 0.4, YEL)
    elif name == "edge":
        x, y = S("north")
        _, ye = to_screen(-83, 31.0, *view)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        for xx in range(0, W, 40): dl.line([xx, ye, xx + 22, ye], fill=RED + (255,), width=6)
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
        corner_brackets(d, 140, ye + 40, W - 140, ye + 520, YEL)
        text_c(d, W / 2, 300, "NORTHERN FRINGES", ANTON(120), YEL + (255,), 8)
        tag(d, W / 2 - 140, ye - 70, "STATE BORDER", RED, WHITE)
    elif name == "kalaga_lock":
        x, y = S("kalaga")
        k = eout(age / 0.5); R = 380 - 220 * k
        d.ellipse([x - R, y - R, x + R, y + R], outline=RED, width=8)
        for ang in range(0, 360, 90):
            a_ = math.radians(ang + 45 * (1 - k))
            d.line([x + (R + 10) * math.cos(a_), y + (R + 10) * math.sin(a_), x + (R + 70) * math.cos(a_), y + (R + 70) * math.sin(a_)], fill=RED, width=8)
        if age > 0.5:
            marker(img, x, y, age - 0.5, RED)
            d = ImageDraw.Draw(img)
            stamp(img, W / 2, 330, "MOUNT KALAGA", ANTON(150), WHITE, age - 0.6, rot=0, box=False)
            if age > 0.9: text_c(d, W / 2, 450, "NATIONAL PARK", ANTON(90), YEL + (255,), 6)
            if age > 1.0: tag(d, W / 2 - 160, 520, "OFFICIAL ROCKSTAR LOCATION", GREEN)
        d.text((60, H - 520), "TARGET LOCKED", font=MONT(36, 800), fill=RED)
    elif name == "kalaga_features":
        try:
            ts = [word_time("kalaga", w) for w in ("forests", "rivers", "trails")]
        except KeyError:
            ts = [a, a + .6, a + 1.2]
        cur = "kalaga_forest"; ca = a
        for k_, key_ in zip(ts, ("kalaga_forest", "kalaga_river", "kalaga_trails")):
            if t >= k_ - 0.08: cur, ca = key_, k_ - 0.08
        img.paste(off_view(cur, min(1, (t - ca) / 1.2), 1.0, 1.15, 0.5, 0.1, dark=0.85)); d = ImageDraw.Draw(img)
        if 0 <= t - ca < 0.1 and cur != "kalaga_forest":
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(160 * (1 - (t - ca) / 0.1))))); d = ImageDraw.Draw(img)
        tag(d, 40, 110, "OFFICIAL SCREENSHOT · MOUNT KALAGA", WHITE)
        for i, (lab, col) in enumerate([("FORESTS", GREEN), ("RIVERS", BLUE), ("TRAILS", YEL)]):
            ak = t - ts[i]
            if ak < 0: continue
            e = eout(ak / .25); y = 420 + i * 170
            lay = rgba(); dl = ImageDraw.Draw(lay)
            dl.rectangle([80, y, 620, y + 130], fill=(0, 0, 0, 200)); dl.rectangle([80, y, 96, y + 130], fill=col + (255,))
            dl.text((130, y + 14), lab, font=ANTON(90), fill=WHITE + (255,))
            dl.line([(560, y + 70), (580, y + 92), (612, y + 40)], fill=col + (255,), width=10)
            lay = lay.transform((W, H), Image.AFFINE, (1, 0, (1 - e) * 700, 0, 1, 0))
            img.alpha_composite(lay)
    elif name == "mountain_rise":
        img.paste(off_view("kalaga_heli", p, 1.0, 1.2, 0, 0, dark=0.45)); d = ImageDraw.Draw(img)
        for gx in range(0, W, 60): d.line([gx, 0, gx, H], fill=(255, 255, 255, 18))
        for gy in range(0, H, 60): d.line([0, gy, W, gy], fill=(255, 255, 255, 18))
        k = eout(age / 0.7)
        xs = np.arange(0, W + 1, 6)
        prof = 1150 - k * (620 * np.exp(-((xs - 540) / 210) ** 2) + 260 * np.exp(-((xs - 300) / 140) ** 2) + 200 * np.exp(-((xs - 800) / 160) ** 2))
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.polygon([(0, 1250)] + list(zip(xs, prof)) + [(W, 1250)], fill=(40, 60, 50, 150))
        for r_ in range(8):
            dl.line(list(zip(xs, prof + r_ * 14)), fill=(120, 160, 130, 120 - r_ * 14), width=2)
        dl.line(list(zip(xs, prof)), fill=YEL + (255,), width=8)
        glow_paste(img, lay, 14, 0.8)
        d = ImageDraw.Draw(img)
        if age > 0.4: stamp(img, W / 2, 330, "A MOUNTAIN", ANTON(170), RED, age - 0.4, rot=-4)
        d.text((60, 1180), "ELEVATION PROFILE", font=MONT(32, 800), fill=GREY)
    elif name == "problem":
        bgp = np.asarray(off_view("kalaga_heli", p, 1.2, 1.3, dark=1.0).convert("L")).astype(np.float32)
        red = np.stack([bgp * 0.75 + 30, bgp * 0.08, bgp * 0.1, np.full_like(bgp, 255)], -1)
        img.paste(to_img(red)); d = ImageDraw.Draw(img)
        on = int(t * 6) % 2 == 0
        for y_ in range(0, H, 120): d.rectangle([0, y_, W, y_ + 60], fill=(60, 0, 8, 90))
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.polygon([(W / 2, 470), (W / 2 - 260, 920), (W / 2 + 260, 920)], fill=(RED if on else (200, 20, 30)) + (255,))
        text_c(dl, W / 2, 760, "!", ANTON(300), BLACK + (255,))
        glow_paste(img, scaled(lay, back(age / .3), W / 2, 700), 30, 1)
        stamp(img, W / 2, 1100, "PROBLEM", ANTON(170), WHITE, age - 0.15, rot=0, fill=RED + (255,))
    elif name == "britton":
        x, y = S("britton")
        marker(img, x, y, age, RED, "BRITTON HILL", "FLORIDA'S HIGHEST POINT", side=1 if x < W / 2 else -1)
        tag(ImageDraw.Draw(img), 40, 200, "REAL-WORLD FACT", WHITE)
    elif name == "compare":
        img.paste(off_view("ambrosia_sunset", p, 1.1, 1.15, dark=0.22, blur=8)); d = ImageDraw.Draw(img)
        base = 1180; scale_ = 1.45  # px per ft
        k = eout(age / 0.8)
        v = int(345 * k)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.line([60, base, W - 60, base], fill=WHITE + (255,), width=4)
        # Britton Hill (gentle bump)
        xs = np.arange(80, 620, 6); hh = 345 * scale_ * k * np.exp(-((xs - 350) / 150) ** 2)
        dl.polygon([(80, base)] + list(zip(xs, base - hh)) + [(620, base)], fill=(60, 110, 70, 255))
        dl.line(list(zip(xs, base - hh)), fill=YEL + (255,), width=6)
        # Statue of Liberty silhouette (305 ft incl. pedestal)
        sh = 305 * scale_ * min(1, age / 0.8); sx = 820
        dl.rectangle([sx - 60, base - sh * .5, sx + 60, base], fill=(150, 160, 170, 255))
        dl.rectangle([sx - 22, base - sh * .92, sx + 22, base - sh * .5], fill=(110, 180, 160, 255))
        dl.ellipse([sx - 20, base - sh * .98, sx + 20, base - sh * .9], fill=(110, 180, 160, 255))
        dl.line([sx + 18, base - sh * .88, sx + 40, base - sh], fill=(110, 180, 160, 255), width=10)
        img.alpha_composite(lay); d = ImageDraw.Draw(img)
        text_c(d, 350, base - 345 * scale_ * k - 80, f"{v} FT", ANTON(130), YEL + (255,), 8)
        text_c(d, 350, base + 70, "BRITTON HILL", ANTON(60), WHITE + (255,))
        text_c(d, sx, base + 70, "STATUE OF LIBERTY", ANTON(46), GREY + (255,))
        text_c(d, sx, base + 125, "305 FT (WITH PEDESTAL)", MONT(28), GREY + (255,))
        text_c(d, W / 2, 230, "THAT'S IT.", ANTON(140), WHITE + (255,), 8)
    elif name == "state_rank":
        img.paste(off_view("vice_night", p, 1.1, 1.15, dark=0.2, blur=8)); d = ImageDraw.Draw(img)
        rows = [("1", "ALASKA · DENALI", 20310, WHITE), ("2", "CALIFORNIA · WHITNEY", 14505, WHITE), ("49", "DELAWARE", 448, WHITE), ("50", "FLORIDA · BRITTON HILL", 345, RED)]
        for i, (rk, lab, ft, col) in enumerate(rows):
            ak = age - i * 0.15
            if ak < 0: continue
            y = 360 + i * 200 + (60 if i >= 2 else 0)
            bw = 900 * (ft / 20310) * eout(ak / .4)
            d.text((60, y), f"#{rk}", font=ANTON(80), fill=col)
            d.text((230, y + 6), lab, font=ANTON(56), fill=col)
            d.rectangle([230, y + 90, 230 + max(6, bw * 0.78), y + 130], fill=col)
            d.text((240 + max(6, bw * .78), y + 84), f"{ft:,} FT", font=MONT(34, 800), fill=col)
        for k_ in range(3): d.ellipse([120 - 7, 735 + k_ * 22, 120 + 7, 749 + k_ * 22], fill=GREY)
        text_c(d, W / 2, 230, "US STATE HIGH POINTS", ANTON(100), YEL + (255,), 6)
        if age > 0.8: red_circle(img, 520, 360 + 3 * 200 + 60 + 70, 470, 120, (age - .8) / .5)
        if age > 1.0: stamp(img, W / 2, 1180, "DEAD LAST", ANTON(120), RED, age - 1.0, rot=-5)
    elif name == "punch":
        img.paste(off_view("kalaga_canyon", p, 1.0, 1.22, 0.3, 0.0, dark=0.95, focal=0.62)); d = ImageDraw.Draw(img)
        g = rgba(); dg = ImageDraw.Draw(g)
        for y_ in range(0, 700, 10): dg.rectangle([0, y_, W, y_ + 10], fill=(0, 0, 0, int(170 * (1 - y_ / 700))))
        img.alpha_composite(g)
        stamp(img, W / 2, 300, "A MOUNTAIN", ANTON(170), WHITE, age - 0.15, rot=0, box=False)
        stamp(img, W / 2, 460, "FLORIDA NEVER HAD", ANTON(120), YEL, age - 0.45, rot=0, box=False)
        if age > 0.8: red_circle(img, 640, 900, 360, 260, (age - .8) / .5)
        if age > 1.2: arrow(img, 160, 620, 330, 800, (age - 1.2) / .3, YEL)
        tag(ImageDraw.Draw(img), 40, 110, "OFFICIAL SCREENSHOT · MOUNT KALAGA", WHITE)
    elif name == "official_map":
        img.paste(off_view("vice_sign", p, 1.0, 1.12, 0.6, 0, dark=0.5)); d = ImageDraw.Draw(img)
        e = back(age / .4); lay = rgba(); dl = ImageDraw.Draw(lay)
        cx, cy = W / 2, 720
        dl.rectangle([cx - 290, cy - 300, cx + 290, cy + 300], fill=WHITE + (255,))
        dl.rectangle([cx - 290, cy - 300, cx + 290, cy - 150], fill=RED + (255,))
        text_c(dl, cx, cy - 225, "NOVEMBER", ANTON(100), WHITE + (255,))
        text_c(dl, cx, cy + 70, "19", ANTON(320), BLACK + (255,))
        glow_paste(img, scaled(lay, e, cx, cy), 24, .6)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 260, "OFFICIAL MAP DROP", ANTON(120), YEL + (255,), 8)
    elif name == "hiding":
        radar_sweep(img, t, W / 2, 900, 560, RED, 90)
        d = ImageDraw.Draw(img)
        rr = np.random.default_rng(3)
        for i in range(14):
            lo, la = rr.uniform(-87, -80.3), rr.uniform(25.3, 30.7)
            x, y = to_screen(lo, la, *view); ak = age - i * 0.09
            if ak < 0 or not (0 < x < W and 0 < y < H): continue
            e = back(ak / .25)
            lay = rgba(); dl = ImageDraw.Draw(lay)
            text_c(dl, x, y, "?", ANTON(90), RED + (255,), 6)
            glow_paste(img, scaled(lay, e, x, y), 10, 1)
        d = ImageDraw.Draw(img)
        text_c(d, W / 2, 300, "WHAT ELSE", ANTON(130), WHITE + (255,), 8)
        text_c(d, W / 2, 430, "IS HIDDEN?", ANTON(130), RED + (255,), 8)
    elif name == "comments":
        img.paste(off_view("keys", p, 1.0, 1.12, -0.5, 0, dark=0.4)); d = ImageDraw.Draw(img)
        opts = [("VICE CITY", YEL), ("LEONIDA KEYS", WHITE), ("GRASSRIVERS", WHITE), ("AMBROSIA", WHITE), ("PORT GELLHORN", WHITE), ("MOUNT KALAGA", RED)]
        for i, (lab, col) in enumerate(opts):
            ak = age - i * .1
            if ak < 0: continue
            e = eout(ak / .3); y = 250 + i * 150
            lay = rgba(); dl = ImageDraw.Draw(lay)
            dl.rectangle([120, y, 960, y + 120], fill=(0, 0, 0, 220), outline=col + (255,), width=4)
            dl.ellipse([150, y + 35, 200, y + 85], fill=col + (255,))
            dl.text((240, y + 18), lab, font=ANTON(76), fill=WHITE + (255,))
            img.alpha_composite(lay.transform((W, H), Image.AFFINE, (1, 0, (1 - e) * (800 if i % 2 else -800), 0, 1, 0)))
        d = ImageDraw.Draw(img)
        yb = 1170 + 20 * math.sin(t * 9)
        d.polygon([(W / 2 - 60, yb), (W / 2 + 60, yb), (W / 2, yb + 80)], fill=YEL)
    else:
        raise KeyError(name)
    return img, view

# ------------------------------------------------------------------ captions
def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, g = cur[0]; age = t - a
    pop = max(0.3, back(age / 0.15, 2.0)) if age < 0.15 else 1.0
    f = ANTON(128); lay = rgba(W, 420); d = ImageDraw.Draw(lay)
    words = [w[0] for w in g]; sp = d.textlength(" ", font=f) * 1.5
    while sum(d.textlength(w_, font=f) for w_ in words) + sp * (len(words) - 1) > W - 120:
        f = ANTON(f.size - 6); sp = d.textlength(" ", font=f) * 1.5
    x = (W - sum(d.textlength(w_, font=f) for w_ in words) - sp * (len(words) - 1)) / 2
    for i, (txt, wa, wb, hl) in enumerate(g):
        spoken = t >= wa - 0.03
        nxt = g[i + 1][1] if i + 1 < len(g) else b
        active = spoken and t < nxt
        col = (YEL if hl else WHITE) if spoken else (200, 200, 200)
        alpha = 255 if spoken else 140
        ww = d.textlength(txt, font=f)
        if active and hl:
            d.rectangle([x - 14, 70, x + ww + 14, 70 + f.size * 1.18], fill=RED + (255,))
            col = WHITE
        d.text((x, 80), txt, font=f, fill=col + (alpha,), stroke_width=11, stroke_fill=(0, 0, 0, alpha))
        x += ww + sp
    if pop != 1:
        nw, nh = int(W * pop), int(420 * pop); l2 = lay.resize((nw, nh), Image.BICUBIC)
        lay = rgba(W, 420); lay.paste(l2, ((W - nw) // 2, (420 - nh) // 2))
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(12))
    shadow = Image.new("RGBA", lay.size, (0, 0, 0, 0)); shadow.putalpha(sh.point(lambda v: int(v * 0.6)))
    out = rgba(W, 420); out.alpha_composite(shadow, (0, 8)); out.alpha_composite(lay); return out

# ------------------------------------------------------------------ compositing
IMPACTS = []
for nm in ("problem", "punch", "kalaga_lock", "mountain_rise"):
    for s in SHOTS:
        if s[2] == nm: IMPACTS.append(s[0] + (0.5 if nm == "kalaga_lock" else 0.0))
MAP_SHOTS = set(CAM) | {"river_grass", "official_map", "comments"}

def frame(t, fi):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0)
    a, b, name, seg = SHOTS[i]; age = t - a
    img, view = draw_shot(name, t, a, b, seg)
    z = 1 + (0.09 * math.exp(-age / 0.09) if i else 0) + 0.012 * math.sin(t * 0.9)
    shake = 0.0
    for h in IMPACTS:
        if 0 <= t - h < 0.35: shake = max(shake, 24 * math.exp(-(t - h) / 0.08))
    z = max(z, 1 + 2.4 * shake / W)
    cw, ch = W / z, H / z
    dx = max(-(W - cw) / 2, min((W - cw) / 2, shake * math.sin(fi * 2.3)))
    dy = max(-(H - ch) / 2, min((H - ch) / 2, shake * math.cos(fi * 3.1)))
    img = img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2 + dx, (H - ch) / 2 + dy, (W + cw) / 2 + dx, (H + ch) / 2 + dy))
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    if i and age < 0.08:  # whip blur
        k = int(50 * (1 - age / 0.08))
        if k > 2:
            acc = np.zeros_like(arr); n = 0
            for s in range(0, k, max(1, k // 6)): acc += np.roll(arr, s - k // 2, axis=0); n += 1
            arr = acc / n
    if i and age < 0.14:
        o = int(18 * (1 - age / 0.14)); arr[..., 0] = np.roll(arr[..., 0], o, 1); arr[..., 2] = np.roll(arr[..., 2], -o, 1)
    for h in IMPACTS:
        if 0 <= t - h < 0.15: arr += 255 * (1 - (t - h) / 0.15) * 0.6
    if name == "problem" and int(t * 12) % 7 == 0:
        y0 = int((t * 991) % (H - 200)); arr[y0:y0 + 100] = np.roll(arr[y0:y0 + 100], 50, 1)
    arr = arr * VIG - SCAN + np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    out = to_img(arr).convert("RGBA"); d = ImageDraw.Draw(out)
    # ---- persistent HUD
    corner_brackets(d, 30, 30, W - 30, H - 30, (255, 255, 255, 140), 70, 5)
    if int(t * 2) % 2 == 0: d.ellipse([60, 64, 84, 88], fill=RED)
    d.text((98, 58), "LEONIDA // MAP INTEL", font=MONT(28, 800), fill=WHITE)
    if view:
        d.text((W - 400, 58), coords_text(view[0], view[1]), font=MONT(26, 700), fill=YEL)
        if name not in ("river_grass", "official_map", "comments", "punch"):
            d.text((60, H - 150), "MAP: ILLUSTRATION · NOT OFFICIAL · POSITIONS APPROXIMATE", font=MONT(24, 700), fill=(220, 220, 220))
    if HAVE_OFF: d.text((60, H - 115), "IMAGES © ROCKSTAR GAMES · FAN-MADE, NOT AFFILIATED", font=MONT(24, 700), fill=(220, 220, 220))
    else:
        d.text((W - 400, 58), "SIGNAL // " + f"{int(t * 1000) % 100000:05d}", font=MONT(26, 700), fill=YEL)
    pw = W * min(1, t / TOTAL); d.rectangle([0, 0, pw, 8], fill=RED)
    cap = caption_layer(t)
    if cap is not None: out.alpha_composite(cap, (0, 1290))
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
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                              os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
