import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, TOTAL, caption_timeline, shot_timeline

W, H, FPS = 1080, 1920, 30
BW, BH = 1300, 2310          # backgrounds drawn larger for camera moves
rng = np.random.default_rng(3)
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
F_CAP = ImageFont.truetype(FONT, 104)
F_BIG = ImageFont.truetype(FONT, 330)
F_MED = ImageFont.truetype(FONT, 92)
F_SM = ImageFont.truetype(FONT, 54)
ICE = (127, 227, 255); GOLD = (255, 214, 77)

# ---------------------------------------------------------------- helpers
def grad(c1, c2, w=BW, h=BH, power=1.0):
    y = (np.linspace(0, 1, h) ** power)[:, None, None]
    a = np.array(c1, float); b = np.array(c2, float)
    return np.broadcast_to(a + (b - a) * y, (h, w, 3)).copy()

def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def glow(img, r=25, k=1.0):
    g = np.asarray(img.filter(ImageFilter.GaussianBlur(r)), float)
    return to_img(np.asarray(img, float) + g * k)

def noise_tex(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((h // scale + 2, w // scale + 2))
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, float) / 255

def pine(d, x, base, h, col):
    w = h * 0.42
    for i in range(7):
        y0 = base - h * (i / 7); ww = w * (1 - i / 8)
        d.polygon([(x - ww / 2, y0), (x + ww / 2, y0), (x, y0 - h * 0.28)], fill=col)
    d.rectangle([x - h * 0.02, base, x + h * 0.02, base + h * 0.06], fill=col)

def forest(sky1, sky2, layers, ground, moon=True, seed=1):
    r = np.random.default_rng(seed)
    a = grad(sky1, sky2, power=1.3)
    img = to_img(a)
    if moon:
        m = Image.new("RGB", (BW, BH)); dm = ImageDraw.Draw(m)
        dm.ellipse([820, 300, 1020, 500], fill=(235, 245, 255))
        img = to_img(np.asarray(img, float) + np.asarray(m.filter(ImageFilter.GaussianBlur(70)), float) * 0.9
                     + np.asarray(m.filter(ImageFilter.GaussianBlur(3)), float) * 0.8)
    for li, col in enumerate(layers):
        lay = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        base = 1350 + li * 260
        for x in np.sort(r.uniform(-100, BW + 100, 7 + li * 2)):
            pine(d, x, base + r.uniform(-60, 60), r.uniform(380, 620) * (1 + li * 0.3), col + (255,))
        d.rectangle([0, base + 40, BW, BH], fill=col + (255,))
        if li < len(layers) - 1:
            lay = lay.filter(ImageFilter.GaussianBlur(3 - li))
        img.paste(lay, (0, 0), lay)
    d = ImageDraw.Draw(img)
    d.ellipse([-400, 2000, BW + 400, 2900], fill=ground)
    return img

# ---------------------------------------------------------------- static backgrounds
def bg_forest_night(): return forest((6, 12, 30), (70, 105, 140), [(28, 48, 70), (16, 30, 46), (6, 12, 20)], (200, 220, 235))
def bg_forest_spring():
    img = forest((90, 140, 120), (210, 200, 140), [(70, 100, 70), (40, 70, 45), (18, 36, 22)], (70, 90, 40), moon=False, seed=5)
    rays = Image.new("RGB", (BW, BH)); d = ImageDraw.Draw(rays)
    for i in range(7):
        x = 200 + i * 160
        d.polygon([(1100, -100), (x - 60, BH), (x + 60, BH)], fill=(255, 230, 160))
    return to_img(np.asarray(img, float) * 0.85 + np.asarray(rays.filter(ImageFilter.GaussianBlur(40)), float) * 0.18)

def bg_aurora():
    a = grad((2, 4, 14), (10, 30, 45), power=0.8)
    yy, xx = np.mgrid[0:BH, 0:BW]
    for k, (col, y0, amp, fr) in enumerate([((40, 255, 160), 700, 180, 0.004), ((60, 200, 255), 950, 140, 0.006), ((150, 90, 255), 520, 120, 0.003)]):
        c = y0 + amp * np.sin(xx * fr + k * 2) + 60 * np.sin(xx * fr * 3.1 + k)
        dist = (yy - c)
        band = np.exp(-np.clip(dist, 0, None) / 260) * np.exp(-np.clip(-dist, 0, None) / 25)
        band *= 0.55 + 0.45 * np.sin(xx * 0.03 + k) ** 2
        a += band[..., None] * np.array(col, float) * 0.7
    st = rng.random((BH, BW)) > 0.9985
    a[st] = 255
    img = to_img(a)
    d = ImageDraw.Draw(img)
    pts = [(0, 1650)] + [(x, 1650 - 380 * abs(math.sin(x * 0.004 + 1)) - 140 * abs(math.sin(x * 0.013))) for x in range(0, BW + 20, 20)] + [(BW, BH), (0, BH)]
    d.polygon(pts, fill=(8, 14, 24))
    pts = [(0, 1900)] + [(x, 1900 - 250 * abs(math.sin(x * 0.006 + 3))) for x in range(0, BW + 20, 20)] + [(BW, BH), (0, BH)]
    d.polygon(pts, fill=(205, 222, 236))
    return img

def bg_leaves():
    r = np.random.default_rng(11)
    img = to_img(grad((50, 32, 20), (25, 15, 10)))
    for i in range(900):
        lay = Image.new("RGBA", (180, 180), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        c = tuple(int(v) for v in r.choice([(120, 70, 35), (150, 95, 45), (90, 55, 30), (170, 120, 60), (70, 45, 25)]) * r.uniform(0.7, 1.1))
        L = r.uniform(80, 170)
        d.ellipse([90 - L / 2, 90 - L / 5, 90 + L / 2, 90 + L / 5], fill=c + (255,))
        d.line([90 - L / 2, 90, 90 + L / 2, 90], fill=(40, 25, 15, 255), width=2)
        lay = lay.rotate(r.uniform(0, 360))
        img.paste(lay, (int(r.uniform(-90, BW)), int(r.uniform(-90, BH))), lay)
    a = np.asarray(img, float)
    frost = noise_tex(BW, BH, 3, 4) ** 6 * 1.6 + (noise_tex(BW, BH, 60, 2) ** 2) * 0.6
    a = a * (1 - np.clip(frost, 0, 1)[..., None] * 0.8) + np.clip(frost, 0, 1)[..., None] * np.array([225, 238, 250]) * 0.8
    return to_img(a * 0.9)

def frog_eye(frost=True, warm=False):
    a = grad((95, 62, 38), (70, 45, 28)) if not warm else grad((125, 85, 45), (90, 60, 30))
    tex = noise_tex(BW, BH, 9, 1) * 0.5 + noise_tex(BW, BH, 40, 2) * 0.5
    a *= (0.65 + 0.6 * tex)[..., None]
    yy, xx = np.mgrid[0:BH, 0:BW]
    cx, cy, R = 650, 1080, 360
    # dark "mask" band through the eye — signature of the wood frog
    band = np.exp(-((yy - (cy + (xx - cx) * 0.18)) / 260) ** 2)
    a *= (1 - 0.75 * band)[..., None]
    d2 = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    ang = np.arctan2(yy - cy, xx - cx)
    iris = (d2 < R)
    streak = 0.6 + 0.4 * np.sin(ang * 70 + noise_tex(BW, BH, 30, 9) * 8) ** 2
    ic = np.array([200, 150, 60]) * (1.1 - d2 / R * 0.5)[..., None] * streak[..., None]
    a[iris] = ic[iris]
    pupil = ((xx - cx) / 240) ** 2 + ((yy - cy) / 120) ** 2 < 1
    a[pupil] = [5, 4, 3]
    rim = (np.abs(d2 - R) < 14)
    a[rim] = a[rim] * 0.3
    hl = np.exp(-(((xx - cx + 140) ** 2 + (yy - cy + 150) ** 2) / 3000))
    a += hl[..., None] * 255
    if frost:
        f = np.clip(noise_tex(BW, BH, 2, 5) ** 8 * 2.5 + noise_tex(BW, BH, 25, 6) ** 3 * 0.5, 0, 1)
        f[iris] *= 0.5
        a = a * (1 - f[..., None] * 0.85) + f[..., None] * np.array([220, 240, 255]) * 0.9
        a = a * 0.75 + np.array([0, 15, 40])
    return to_img(a)

# Ice crystal growth: final image + distance map from seeds (revealed by radius)
def make_ice():
    r = np.random.default_rng(21)
    img = Image.new("RGB", (BW, BH)); d = ImageDraw.Draw(img)
    seeds = [(650, 1150), (250, 500), (1100, 1900), (300, 1900), (1050, 450)]
    def branch(x, y, ang, L, depth, wdt):
        if depth == 0 or L < 8: return
        x2, y2 = x + L * math.cos(ang), y + L * math.sin(ang)
        d.line([x, y, x2, y2], fill=(170, 225, 255), width=max(1, int(wdt)))
        for k in range(1, 5):
            px, py = x + (x2 - x) * k / 5, y + (y2 - y) * k / 5
            for s in (-1, 1):
                branch(px, py, ang + s * math.pi / 3, L * 0.33 * r.uniform(0.7, 1.1), depth - 1, wdt * 0.6)
        branch(x2, y2, ang + r.normal(0, 0.1), L * 0.6, depth - 1, wdt * 0.8)
    for sx, sy in seeds:
        for k in range(6):
            branch(sx, sy, k * math.pi / 3 + r.uniform(-.1, .1), r.uniform(260, 420), 4, 5)
    img = glow(img.filter(ImageFilter.GaussianBlur(0.8)), 14, 1.4)
    base = grad((4, 14, 34), (10, 40, 70))
    a = base + np.asarray(img, float)
    yy, xx = np.mgrid[0:BH, 0:BW]
    dist = np.min([np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2) for sx, sy in seeds], axis=0)
    return a, base, dist

def bg_dark(c1=(4, 10, 24), c2=(14, 34, 60)): return to_img(grad(c1, c2))

# ---------------------------------------------------------------- overlays
VIG = None
def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    return np.clip(1.15 - r ** 2 * 0.6, 0.25, 1)[..., None]
GRAIN = [(rng.standard_normal((H // 2, W // 2)) * 7) for _ in range(4)]

FLAKES = rng.random((260, 5))   # x, y, size, speed, phase
def draw_snow(img, t, density=1.0, warm=False, big=False):
    d = ImageDraw.Draw(img, "RGBA")
    n = int(len(FLAKES) * density)
    for fx, fy, fs, sp, ph in FLAKES[:n]:
        s = (2 + fs ** 3 * 14) * (2.2 if big else 1)
        y = (fy * H + t * (60 + sp * 200) * (1 + fs)) % (H + 40) - 20
        x = (fx * W + 40 * math.sin(t * (0.5 + ph) + ph * 6)) % W
        col = (255, 235, 170, int(90 + fs * 120)) if warm else (235, 245, 255, int(110 + fs * 140))
        d.ellipse([x - s, y - s, x + s, y + s], fill=col)

def cam(bg, p, mode):
    # p in 0..1 across the shot; returns W x H crop with a slow push/pan
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * (p * p * (3 - 2 * p) * 0.5 + p * 0.5)
    cw, ch = BW / z, BH / z
    cx = BW / 2 + dx * (p - 0.5) * (BW - cw); cy = BH / 2 + dy * (p - 0.5) * (BH - ch)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return bg.resize((W, H), Image.BILINEAR, box=box)

def text_c(d, y, s, font, fill, stroke=0, sc=(0, 0, 0)):
    w = d.textlength(s, font=font)
    d.text(((W - w) / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)

def ecg(img, t, beats, flat_after=None, color=(60, 255, 120)):
    d = ImageDraw.Draw(img, "RGBA")
    for gy in range(0, H, 90): d.line([0, gy, W, gy], fill=(30, 80, 50, 60))
    for gx in range(0, W, 90): d.line([gx, 0, gx, H], fill=(30, 80, 50, 60))
    pts = []
    win = 3.0
    for i in range(0, W, 3):
        tt = t - win + win * i / W
        v = 0
        for b in beats:
            u = tt - b
            v += 260 * math.exp(-(u / 0.018) ** 2) - 90 * math.exp(-((u - 0.05) / 0.025) ** 2) + 50 * math.exp(-((u - 0.25) / 0.06) ** 2)
        pts.append((i, 960 - v))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.line(pts, fill=color + (255,), width=9, joint="curve")
    img.paste(lay.filter(ImageFilter.GaussianBlur(14)), (0, 0), lay.filter(ImageFilter.GaussianBlur(14)))
    img.paste(lay, (0, 0), lay)
    last = [b for b in beats if b <= t]
    bpm = 0 if (flat_after and t > flat_after) or not last else (int(60 / max(0.3, (last[-1] - last[-2]))) if len(last) > 1 else 72)
    c = (255, 70, 70) if bpm == 0 else color
    text_c(d, 260, f"{bpm} LPM", F_MED, c)

def counter(img, p, target, unit, sub, color, fmt="{:d}"):
    d = ImageDraw.Draw(img, "RGBA")
    v = target * min(1, (p / 0.6)) ** 0.5 if target > 0 else -abs(target) * min(1, p / 0.6) ** 0.5
    s = fmt.format(int(round(v)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    text_c(dl, 330, s, F_BIG, color + (255,))
    text_c(dl, 700, unit, F_MED, (255, 255, 255, 255))
    g = lay.filter(ImageFilter.GaussianBlur(30))
    img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
    text_c(d, 830, sub, F_SM, (200, 225, 240))

# ---------------------------------------------------------------- build backgrounds
print("building backgrounds", flush=True)
BG = {
    "forest_night": bg_forest_night(), "forest_spring": bg_forest_spring(), "aurora": bg_aurora(),
    "leaves_snow": bg_leaves(), "eye_frost": frog_eye(True), "eye_open": frog_eye(False, True),
}
BG["snowfall_close"] = BG["forest_night"].filter(ImageFilter.GaussianBlur(18))
ICE_FULL, ICE_BASE, ICE_DIST = make_ice()
BG["dark"] = bg_dark()
BG["lab"] = bg_dark((6, 16, 30), (20, 50, 70))
BG["green"] = bg_dark((2, 12, 6), (4, 30, 14))
VIG = vignette()
MOL = rng.random((26, 5))
CELLS = rng.random((14, 3))

MODES = {  # zoom start, zoom end, pan x, pan y
    "eye_frost": (1.0, 1.25, 0.2, -0.1), "ice_grow": (1.05, 1.2, -0.3, 0.2), "forest_night": (1.0, 1.18, 0.6, 0),
    "aurora": (1.15, 1.0, -0.5, -0.2), "leaves_snow": (1.25, 1.05, 0, 0.6), "snowfall_close": (1.0, 1.1, 0, 0),
    "eye_open": (1.3, 1.05, -0.2, 0.1), "forest_spring": (1.0, 1.2, -0.4, 0.2), "thaw": (1.0, 1.15, 0.2, 0.2),
}

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    if name in ("ice_grow", "thaw"):
        r = (200 + p * 1700) if name == "ice_grow" else (1900 - p * 1900)
        m = np.clip((r - ICE_DIST) / 120, 0, 1)[..., None]
        arr = ICE_BASE + (ICE_FULL - ICE_BASE) * m
        if name == "thaw":
            warmth = np.array([1.0 + p * 0.9, 1.0 + p * 0.5, 1.0 - p * 0.3])
            arr = arr * warmth + p * np.array([60, 35, 5])
        img = cam(to_img(arr), p, MODES[name])
        if name == "thaw":
            d = ImageDraw.Draw(img, "RGBA")
            for k in range(14):
                x = (k * 137) % W; y = ((t * 900 + k * 333) % (H + 200)) - 100
                d.ellipse([x - 9, y - 14, x + 9, y + 14], fill=(200, 230, 255, 170))
        else:
            draw_snow(img, t, 0.5)
        return img
    if name in BG and name in MODES:
        img = cam(BG[name], p, MODES[name])
        if name == "snowfall_close": draw_snow(img, t, 1.0, big=True)
        elif name == "forest_spring": draw_snow(img, t, 0.35, warm=True)
        elif name == "eye_open":
            lid = max(0, 1 - p / 0.35)
            if lid > 0:
                d = ImageDraw.Draw(img); d.rectangle([0, 0, W, int(H / 2 * lid)], fill=(25, 15, 8)); d.rectangle([0, H - int(H / 2 * lid), W, H], fill=(25, 15, 8))
        elif name not in ("eye_frost",): draw_snow(img, t, 0.8)
        else: draw_snow(img, t, 0.3)
        return img
    if name == "stat_65":
        img = cam(to_img(ICE_BASE + (ICE_FULL - ICE_BASE) * 0.35), p, (1.1, 1.2, 0, 0))
        counter(img, p, 65, "%", "DEL AGUA DE SU CUERPO", ICE, "{:d}")
        d = ImageDraw.Draw(img, "RGBA")
        fill = min(1, p / 0.6) * 0.65
        d.rounded_rectangle([140, 1000, 940, 1060], 30, outline=(200, 240, 255, 255), width=5)
        d.rounded_rectangle([146, 1006, 146 + int(788 * fill), 1054], 26, fill=ICE + (255,))
        draw_snow(img, t, 0.4); return img
    if name == "stat_193":
        img = cam(BG["aurora"], 0.5 + p * 0.3, (1.3, 1.4, 0.3, 0)).filter(ImageFilter.GaussianBlur(6))
        img = to_img(np.asarray(img, float) * 0.55)
        counter(img, p, 193, "DÍAS", "SEGUIDOS CONGELADA · ALASKA", ICE)
        d = ImageDraw.Draw(img, "RGBA")
        ang = 360 * min(1, p / 0.6) * (193 / 365)
        d.arc([240, 1000, 840, 1600], -90, -90 + ang, fill=ICE + (255,), width=26)
        d.arc([240, 1000, 840, 1600], -90 + ang, 270, fill=(255, 255, 255, 50), width=26)
        text_c(d, 1250, "> 6 MESES", F_SM, (255, 255, 255)); draw_snow(img, t, 0.6); return img
    if name == "stat_18":
        img = cam(BG["forest_night"], p, (1.2, 1.3, -0.2, 0)).filter(ImageFilter.GaussianBlur(8))
        img = to_img(np.asarray(img, float) * 0.5 + np.array([0, 10, 30]))
        counter(img, p, -18, "°C", "TEMPERATURA MÍNIMA REGISTRADA", ICE, "{:d}")
        d = ImageDraw.Draw(img, "RGBA")
        lvl = 1 - min(1, p / 0.6) * 0.85
        d.rounded_rectangle([500, 950, 580, 1550], 40, outline=(255, 255, 255, 230), width=6)
        d.ellipse([460, 1500, 620, 1660], fill=ICE + (255,))
        d.rounded_rectangle([515, 950 + int(560 * (1 - lvl)), 565, 1540], 25, fill=ICE + (255,))
        draw_snow(img, t, 1.0, big=True); return img
    if name in ("heartbeat", "heartbeat_back"):
        img = to_img(np.zeros((H, W, 3)) + np.array([2, 8, 5]))
        if name == "heartbeat": ecg(img, t, [22.2, 23.0, 23.95, 25.1], flat_after=25.45)
        else: ecg(img, t, [46.9, 47.9, 48.75, 49.5, 50.2])
        return img
    if name in ("glucose", "cells"):
        img = cam(BG["dark"] if name == "glucose" else BG["lab"], p, (1.0, 1.1, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        if name == "glucose":
            for i, (mx, my, ms, sp, ph) in enumerate(MOL):
                cx = mx * W + 60 * math.sin(t * 0.7 + ph * 6); cy = (my * H - t * (40 + sp * 80) * (0.5 + ms)) % H
                R = 30 + ms * 70; rot = t * (0.5 + sp) + ph * 6
                pts = [(cx + R * math.cos(rot + k * math.pi / 3), cy + R * math.sin(rot + k * math.pi / 3)) for k in range(6)]
                col = GOLD if i % 3 else ICE
                d.line(pts + [pts[0]], fill=col + (230,), width=int(4 + ms * 6))
                for q in pts: d.ellipse([q[0] - 7, q[1] - 7, q[0] + 7, q[1] + 7], fill=col + (255,))
            text_c(d, 250, "C₆H₁₂O₆".replace("₆", "6").replace("₁₂", "12"), F_MED, GOLD + (255,))
        else:
            for (cxr, cyr, cr) in CELLS:
                cx = cxr * W; cy = cyr * H + 20 * math.sin(t + cxr * 9); R = 90 + cr * 110
                d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(255, 190, 70, 70), outline=(255, 220, 120, 255), width=6)
                d.ellipse([cx - R * 0.3, cy - R * 0.3, cx + R * 0.3, cy + R * 0.3], fill=(255, 160, 60, 180))
            ice_rgba = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            m = cam(to_img(ICE_FULL - ICE_BASE), p, (1.0, 1.1, 0, 0))
            ice_rgba.paste(m, (0, 0), m.convert("L"))
            lay = Image.alpha_composite(ice_rgba, lay)
        g = lay.filter(ImageFilter.GaussianBlur(18))
        img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
        return img
    if name == "lab":
        img = cam(BG["lab"], p, (1.0, 1.15, 0, -0.3))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for k in range(5):
            x = 140 + k * 200; top = 700 + (k % 2) * 60
            d.rounded_rectangle([x, top, x + 120, top + 620], 50, outline=(210, 240, 255, 255), width=7)
            lvl = top + 260 + 30 * math.sin(t * 2 + k)
            d.rounded_rectangle([x + 10, lvl, x + 110, top + 610], 45, fill=(90, 200, 255, 170))
            d.rectangle([x - 10, top - 50, x + 130, top], fill=(240, 240, 250, 255))
        g = lay.filter(ImageFilter.GaussianBlur(22)); img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
        fog = Image.new("RGBA", (W, H), (0, 0, 0, 0)); df = ImageDraw.Draw(fog)
        for k in range(12):
            x = (k * 211 + t * 40) % (W + 300) - 150; y = 1350 + 60 * math.sin(k + t)
            df.ellipse([x - 220, y - 90, x + 220, y + 90], fill=(220, 240, 255, 40))
        fog = fog.filter(ImageFilter.GaussianBlur(40)); img.paste(fog, (0, 0), fog)
        return img
    if name == "end_card":
        img = cam(BG["eye_open"], p, (1.05, 1.35, 0, 0))
        img = to_img(np.asarray(img, float) * (1 - 0.45 * min(1, p * 2)))
        d = ImageDraw.Draw(img, "RGBA")
        if p > 0.15:
            text_c(d, 230, "COMENTA", F_MED, (255, 255, 255), 6)
            text_c(d, 340, "SÍ  o  NO", F_MED, GOLD, 6)
            cx = W / 2; yb = 470 + 18 * math.sin(t * 8)
            d.polygon([(cx - 45, yb), (cx + 45, yb), (cx, yb + 60)], fill=GOLD)
        return img
    raise KeyError(name)

SHOTS = shot_timeline()
CAPS = caption_timeline()
HITS = [0.05, 17.0, 28.6, 39.4, 44.5, 54.6]

def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, s = cur[0]
    age = t - a
    sc = 0.82 + 0.18 * min(1, age / 0.11) + 0.04 * math.sin(min(1, age / 0.11) * math.pi)
    words = s.split(" ")
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    parts, hl = [], False
    for w in words:
        if w.startswith("*"): hl = True
        clean = w.replace("*", "")
        parts.append((clean, hl))
        if w.endswith("*") or w.endswith("*…") or w.endswith("*?"): hl = False
    full = " ".join(p[0] for p in parts)
    font = F_CAP
    while d.textlength(full, font=font) > W - 90: font = ImageFont.truetype(FONT, font.size - 6)
    x = (W - d.textlength(full, font=font)) / 2
    for i, (wd, h) in enumerate(parts):
        txt = wd + (" " if i < len(parts) - 1 else "")
        d.text((x, 60), txt, font=font, fill=(GOLD if h else (255, 255, 255)) + (255,), stroke_width=9, stroke_fill=(0, 0, 0, 255))
        x += d.textlength(txt, font=font)
    if sc != 1:
        nw, nh = int(W * sc), int(260 * sc)
        lay2 = lay.resize((nw, nh), Image.BILINEAR); out = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        out.paste(lay2, ((W - nw) // 2, (260 - nh) // 2)); lay = out
    return lay

def frame(t, fi):
    idx = [i for i, s in enumerate(SHOTS) if s[0] <= t < s[1]]
    i = idx[0] if idx else len(SHOTS) - 1
    a, b, name = SHOTS[i]
    img = shot_frame(name, t, a, b)
    XF = 0.18
    if i + 1 < len(SHOTS) and t > b - XF:      # quick crossfade into next shot
        a2, b2, n2 = SHOTS[i + 1]
        nxt = shot_frame(n2, t, a2, b2)
        img = Image.blend(img, nxt, (t - (b - XF)) / XF)
    arr = np.asarray(img, float)
    arr = arr * VIG
    for h in HITS:                              # flash on reveals
        u = t - h
        if 0 <= u < 0.25: arr = arr + (1 - u / 0.25) * 140
    g = GRAIN[fi % 4]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    arr = (arr - 128) * 1.06 + 128               # a touch of contrast
    if t < 0.25: arr *= t / 0.25
    if t > TOTAL - 0.6: arr *= max(0, (TOTAL - t) / 0.6)
    img = to_img(arr)
    cap = caption_layer(t)
    if cap is not None and t < TOTAL - 0.2:
        img.paste(cap, (0, 1240), cap)
    return img

def render_scene(si, path):
    a, b = SCENES[si][0], SCENES[si][1]
    f0, f1 = int(round(a * FPS)), int(round(b * FPS))
    tmp = path.replace(".mp4", ".part.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, path)

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        for tt in [float(x) for x in sys.argv[2:]]:
            frame(tt, 0).save(os.path.join(HERE, f"still_{tt:05.1f}.jpg"), quality=85)
    else:
        for si in [int(x) for x in sys.argv[2:]]:
            render_scene(si, os.path.join(HERE, f"scene_{si:02}.mp4")); print("scene", si, flush=True)
