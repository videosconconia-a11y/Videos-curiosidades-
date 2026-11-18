# Render del vídeo "El iceberg de GTA 6" — todo dibujado por código (Pillow + NumPy), sin material de terceros.
# Estética original "atardecer neón" (años 80); no se usan logos, arte ni capturas de Rockstar.
import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, TOTAL, caption_timeline, shot_timeline, hits

W, H, FPS = 1080, 1920, 30
BW, BH = 1300, 2310
rng = np.random.default_rng(6)

def _font(names):
    for n in names:
        if os.path.exists(n): return n
    raise FileNotFoundError(names)
FONT = _font(["/usr/share/fonts/truetype/google-fonts/Poppins-Black.ttf", "/usr/share/fonts/opentype/inter/Inter-Black.otf"])
FONT_B = _font(["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"])
F = lambda s, bold=False: ImageFont.truetype(FONT_B if bold else FONT, s)
F_CAP, F_HUGE, F_BIG, F_MED, F_SM, F_XS = F(100), F(400), F(250), F(96), F(58, True), F(44, True)

PINK = (255, 60, 170); TEAL = (0, 235, 215); SUN = (255, 196, 70); ORANGE = (255, 120, 60)
WHITE = (255, 255, 255); RED = (255, 55, 70); HL = (255, 214, 60)

# ---------------------------------------------------------------- helpers
def grad_stops(stops, w, h):
    y = np.linspace(0, 1, h)
    ch = [np.interp(y, [s[0] for s in stops], [s[1][k] for s in stops]) for k in range(3)]
    return np.broadcast_to(np.stack(ch, 1)[:, None, :], (h, w, 3)).copy()

def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def ease(p): p = min(max(p, 0.0), 1.0); return p * p * (3 - 2 * p)
def pop(p, d=0.18):   # 0→1 con pequeño rebote
    u = min(max(p / d, 0), 1); return 1 + 0.12 * math.sin(u * math.pi) if u < 1 else 1.0

def paste_glow(img, lay, r=22, k=1.0):
    g = lay.filter(ImageFilter.GaussianBlur(r))
    if k != 1.0:
        a = np.asarray(g).astype(float); a[..., 3] = np.clip(a[..., 3] * k, 0, 255); g = Image.fromarray(a.astype(np.uint8))
    img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)

def text_c(d, y, s, font, fill, stroke=0, sc=(0, 0, 0), x=None):
    w = d.textlength(s, font=font)
    d.text(((W - w) / 2 if x is None else x - w / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)

def scaled_text(img, cx, cy, s, font, fill, scale=1.0, glow=20, stroke=0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w = d.textlength(s, font=font); bb = d.textbbox((0, 0), s, font=font)
    d.text((cx - w / 2, cy - (bb[1] + bb[3]) / 2), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    if abs(scale - 1) > 1e-3:
        nw, nh = int(W * scale), int(H * scale)
        big = lay.resize((nw, nh), Image.BILINEAR)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.paste(big, (int(cx - cx * scale), int(cy - cy * scale)))
    paste_glow(img, lay, glow) if glow else img.paste(lay, (0, 0), lay)

def cam(bg, p, mode):
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0); bw, bh = bg.size
    z = z0 + (z1 - z0) * (ease(p) * 0.5 + p * 0.5)
    cw, ch = BW / z, BH / z
    cx = bw / 2 + dx * (p - 0.5) * (bw - cw); cy = bh / 2 + dy * (p - 0.5) * (bh - ch)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def palm(d, x, base, h, col, lean=0.15, seed=0):
    r = np.random.default_rng(seed)
    pts = []
    for i in range(21):
        u = i / 20; pts.append((x + lean * h * u ** 1.6, base - h * u))
    for i in range(20):
        w = 16 * (1 - i / 26) * h / 900
        d.line([pts[i], pts[i + 1]], fill=col, width=max(3, int(w * 2)))
    tx, ty = pts[-1]
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.42 + r.uniform(-.1, .1); L = h * r.uniform(0.3, 0.42)
        seg = [(tx, ty)]
        for j in range(1, 13):
            u = j / 12
            seg.append((tx + math.cos(a) * L * u * 1.0, ty + math.sin(a) * L * u + (L * 0.55) * u * u))
        for j in range(12):
            wd = int(max(2, 26 * (1 - j / 12) * h / 900))
            d.line([seg[j], seg[j + 1]], fill=col, width=wd)
            mx, my = seg[j + 1]
            for s in (-1, 1):
                d.line([seg[j + 1], (mx + s * 18 * (1 - j / 12) * h / 900, my + 30 * h / 900)], fill=col, width=max(2, wd // 2))

# ---------------------------------------------------------------- backgrounds
def bg_sunset(dark=0.0):
    a = grad_stops([(0, (18, 4, 46)), (0.32, (88, 18, 110)), (0.55, (230, 70, 130)), (0.6, (255, 140, 110)), (0.6001, (40, 8, 60)), (1, (8, 2, 22))], BW, BH)
    img = to_img(a)
    sun = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); ds = ImageDraw.Draw(sun)
    cx, cy, R = BW / 2, 1386 - 40, 420
    for y in range(int(cy - R), int(cy + 1)):
        u = (y - (cy - R)) / R
        if u > 0.45 and int((y - cy) / 16) % 2 == 0 and (cy - y) < R * 0.55 * (1 - (u - 0.45) * 0.4) * 0.9 and (int((cy - y) / 16) % 2): pass
        half = math.sqrt(max(0, R * R - (y - cy) ** 2))
        stripe = u > 0.5 and ((cy - y) % (14 + 30 * (1 - u))) < 10 * (u - 0.45) * 2.2
        if stripe: continue
        col = tuple(int(SUN[k] + (PINK[k] - SUN[k]) * u) for k in range(3))
        ds.line([cx - half, y, cx + half, y], fill=col + (255,))
    g = sun.filter(ImageFilter.GaussianBlur(60)); img.paste(g, (0, 0), g); img.paste(sun, (0, 0), sun)
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(60):                       # reflejos del sol en el agua
        y = 1400 + k ** 1.45 * 1.6; w = (420 - k * 5) * (0.6 + 0.4 * math.sin(k * 1.7))
        if w > 10: d.rectangle([BW / 2 - w, y, BW / 2 + w, y + 4 + k * 0.15], fill=(255, 120 + k, 150, max(0, 150 - k * 2)))
    lay = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    palm(dl, 120, 1500, 1050, (12, 2, 22, 255), 0.22, 1); palm(dl, 1180, 1520, 900, (12, 2, 22, 255), -0.25, 2)
    palm(dl, 1050, 1460, 620, (30, 6, 46, 255), -0.1, 3)
    dl.rectangle([0, 1490, BW, BH], fill=(0, 0, 0, 0))
    img.paste(lay, (0, 0), lay)
    if dark: img = to_img(np.asarray(img, float) * (1 - dark))
    return img

def bg_city():
    r = np.random.default_rng(9)
    a = grad_stops([(0, (8, 2, 30)), (0.45, (60, 12, 90)), (0.62, (180, 40, 120)), (0.62, (10, 2, 25)), (1, (4, 0, 14))], BW, BH)
    st = r.random((BH, BW)) > 0.9988; st[1300:] = False; a[st] = 230
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    base = 1432
    for layer, (col, hmin, hmax, wmin) in enumerate([((40, 10, 70), 300, 650, 70), ((20, 4, 40), 220, 900, 90)]):
        x = -40
        while x < BW:
            w = r.uniform(wmin, wmin * 2.2); h = r.uniform(hmin, hmax)
            d.rectangle([x, base - h, x + w, base], fill=col)
            if layer == 1:
                for wy in range(int(base - h + 30), base - 20, 34):
                    for wx in range(int(x + 12), int(x + w - 14), 26):
                        if r.random() < 0.38:
                            c = [PINK, TEAL, SUN, (255, 240, 220)][r.integers(0, 4)]
                            d.rectangle([wx, wy, wx + 12, wy + 16], fill=c + (int(r.uniform(140, 255)),))
                if r.random() < 0.35:   # cartel / perfil de neón
                    c = [PINK, TEAL][r.integers(0, 2)]
                    d.rectangle([x + 6, base - h - 4, x + w - 6, base - h + 6], fill=c + (255,))
            x += w + r.uniform(-10, 18)
    glow = img.filter(ImageFilter.GaussianBlur(14)); img = to_img(np.asarray(img, float) + np.asarray(glow, float) * 0.7)
    top = img.crop((0, base - 700, BW, base)).transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(6))
    refl = to_img(np.asarray(top, float) * 0.45 + np.array([10, 0, 20]))
    img.paste(refl, (0, base))
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(40):
        y = base + 10 + k * 22; d.line([0, y, BW, y], fill=(0, 0, 0, 60), width=3)
    lay = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    palm(dl, 80, 2310, 1500, (6, 0, 14, 255), 0.25, 4); palm(dl, 1240, 2310, 1250, (6, 0, 14, 255), -0.3, 5)
    img.paste(lay, (0, 0), lay)
    return img

IW, IH, WATER = 1300, 5300, 900
LEVEL_Y = [WATER + 520 * k for k in range(8)]
def bg_iceberg():
    sky = bg_sunset().crop((0, 1386 - WATER, BW, 1386 + 300 - 300)).resize((IW, WATER))
    a = grad_stops([(0, (0, 150, 175)), (0.12, (0, 80, 120)), (0.5, (4, 26, 64)), (1, (2, 4, 18))], IW, IH - WATER)
    img = Image.new("RGB", (IW, IH)); img.paste(sky, (0, 0)); img.paste(to_img(a), (0, WATER))
    d = ImageDraw.Draw(img, "RGBA")
    r = np.random.default_rng(12)
    # silueta del iceberg (punta pequeña arriba, masa enorme abajo)
    left, right = [], []
    for i in range(80):
        y = WATER - 330 + i / 79 * (IH - 450 - (WATER - 330))
        u = (y - WATER) / (IH - WATER)
        if y < WATER: hw = 40 + (y - (WATER - 330)) * 0.55
        else: hw = 220 + 430 * math.sin(min(1, u * 1.4) * math.pi / 2) - 60 * max(0, u - 0.8) * 5
        left.append((IW / 2 - hw - r.uniform(0, 45), y)); right.append((IW / 2 + hw + r.uniform(0, 45), y))
    poly = left + [(IW / 2, IH - 300)] + right[::-1]
    mask = Image.new("L", (IW, IH), 0); ImageDraw.Draw(mask).polygon(poly, fill=255)
    yy = np.arange(IH)[:, None]; xx = np.arange(IW)[None, :]
    depth = np.clip((yy - WATER) / (IH - WATER), 0, 1)
    shade = 0.55 + 0.45 * np.clip(1 - np.abs(xx - IW / 2 + 120) / 700, 0, 1)
    ice = np.stack([(150 + 90 * (1 - depth)) * shade, (220 + 30 * (1 - depth)) * shade, (245) * shade + depth * 0], -1)
    under = yy >= WATER
    ice = np.where(under[..., None], ice * (1 - depth[..., None] * 0.72) + np.array([0, 20, 50]) * depth[..., None], np.minimum(ice * 1.15, 255))
    # facetas: planos de luz/sombra en diagonal (aspecto de hielo tallado) + textura suave
    fac = Image.new("L", (IW, IH), 128); dfc = ImageDraw.Draw(fac)
    for k in range(60):
        x0 = r.uniform(0, IW); y0 = r.uniform(WATER - 300, IH); L = r.uniform(250, 900)
        ang = r.uniform(-0.9, 0.9) + math.pi / 2
        x1, y1 = x0 + math.cos(ang) * L, y0 + math.sin(ang) * L
        w = r.uniform(60, 220)
        dfc.polygon([(x0, y0), (x0 + w, y0 + w * 0.3), (x1 + w * 0.6, y1), (x1, y1 - w * 0.2)], fill=int(r.uniform(70, 200)))
    fac = np.asarray(fac.filter(ImageFilter.GaussianBlur(3)), float) / 255
    tex = np.asarray(Image.fromarray((r.random((IH // 90, IW // 90)) * 255).astype(np.uint8)).resize((IW, IH), Image.BICUBIC), float) / 255
    ice *= (0.72 + 0.45 * fac + 0.12 * tex)[..., None]
    edge = np.asarray(mask.filter(ImageFilter.GaussianBlur(10)), float) / 255
    rim = np.clip((1 - np.abs(edge - 0.5) * 2), 0, 1)[..., None] * (1 - depth[..., None] * 0.7)
    ice = ice + rim * np.array([90, 140, 150])
    base = np.asarray(img, float); m = (np.asarray(mask, float) / 255)[..., None]
    out = base * (1 - m) + ice * m
    img = to_img(out); d = ImageDraw.Draw(img, "RGBA")
    d.line([0, WATER, IW, WATER], fill=(220, 255, 255, 200), width=5)
    for k in range(1, 8):
        y = LEVEL_Y[k]
        for x in range(0, IW, 40): d.line([x, y, x + 22, y], fill=(255, 255, 255, 110), width=4)
    # rayos de luz bajo la superficie
    rays = Image.new("L", (IW, IH), 0); dr = ImageDraw.Draw(rays)
    for k in range(9):
        x = 80 + k * 150; dr.polygon([(x, WATER), (x + 70, WATER), (x + 260, WATER + 1500), (x + 120, WATER + 1500)], fill=60)
    rays = rays.filter(ImageFilter.GaussianBlur(30))
    img = to_img(np.asarray(img, float) + (np.asarray(rays, float) / 255)[..., None] * np.array([120, 220, 220]))
    return img

def bg_dark(c1=(14, 4, 34), c2=(40, 8, 60)):
    a = grad_stops([(0, c1), (1, c2)], BW, BH)
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, BW, 90): d.line([x, 0, x, BH], fill=(255, 60, 170, 22), width=2)
    for y in range(0, BH, 90): d.line([0, y, BW, y], fill=(255, 60, 170, 22), width=2)
    return img

# ---------------------------------------------------------------- overlays
def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    return np.clip(1.15 - r ** 2 * 0.55, 0.3, 1)[..., None]
GRAIN = [(rng.standard_normal((H // 2, W // 2)) * 6) for _ in range(4)]
BUB = rng.random((70, 4))

def bubbles(img, t, speed=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    for bx, by, bs, ph in BUB:
        y = (by * H - t * (80 + bs * 160) * speed) % (H + 60) - 30
        x = bx * W + 25 * math.sin(t * 2 + ph * 9); s = 3 + bs ** 2 * 14
        d.ellipse([x - s, y - s, x + s, y + s], outline=(200, 255, 255, int(80 + bs * 120)), width=2)

def counter(img, p, target, unit, sub, color, prefix="", y=420):
    v = target * ease(min(1, p / 0.55)) ** 0.8
    s = prefix + f"{int(round(v))}"
    scaled_text(img, W / 2, y + 150, s, F_BIG if len(s) > 2 else F_HUGE, color + (255,), pop(p - 0.5, 0.2) if p > 0.5 else 1.0, 34)
    d = ImageDraw.Draw(img, "RGBA")
    text_c(d, y + 330, unit, F_MED, WHITE, 5)
    if sub: text_c(d, y + 460, sub, F_SM, (255, 220, 240), 4)

def badge(d, cx, cy, s, font, bg, fg=WHITE, padx=40, pady=22, outline=None):
    w = d.textlength(s, font=font); bb = d.textbbox((0, 0), s, font=font); h = bb[3] - bb[1]
    d.rounded_rectangle([cx - w / 2 - padx, cy - h / 2 - pady, cx + w / 2 + padx, cy + h / 2 + pady + 8], 26, fill=bg, outline=outline, width=6)
    d.text((cx - w / 2, cy - h / 2 - bb[1] + 4), s, font=font, fill=fg)

# ---------------------------------------------------------------- build backgrounds
print("building backgrounds", flush=True)
BG = {"sunset": bg_sunset(), "city": bg_city(), "dark": bg_dark(), "dark2": bg_dark((4, 16, 34), (8, 40, 60))}
BG["sunset_blur"] = to_img(np.asarray(BG["sunset"].filter(ImageFilter.GaussianBlur(14)), float) * 0.5)
BG["city_blur"] = to_img(np.asarray(BG["city"].filter(ImageFilter.GaussianBlur(16)), float) * 0.45)
ICE = bg_iceberg()
VIG = vignette()

LEVEL_SUB = {1: "LA SUPERFICIE", 2: "EL MAPA", 3: "LOS PROTAGONISTAS", 4: "LA ESPERA", 5: "LA FILTRACIÓN", 6: "EL RÉCORD", 7: "EL FONDO"}

def ice_view(cy, z=1.0, dx=0.0):
    cw = IW / z; ch = cw * H / W
    cy = min(max(cy, ch / 2), IH - ch / 2); cx = IW / 2 + dx
    return ICE.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

# Florida-like peninsula (forma genérica, inventada) en coordenadas 0..1
MAP = [(0.05, 0.10), (0.30, 0.08), (0.55, 0.12), (0.62, 0.16), (0.68, 0.14), (0.80, 0.13), (0.84, 0.20), (0.86, 0.32),
       (0.90, 0.45), (0.93, 0.58), (0.92, 0.70), (0.88, 0.80), (0.82, 0.88), (0.76, 0.90), (0.72, 0.84), (0.66, 0.74),
       (0.60, 0.62), (0.58, 0.50), (0.52, 0.36), (0.44, 0.27), (0.34, 0.22), (0.22, 0.24), (0.10, 0.22), (0.04, 0.18)]

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    if name == "hook_13":
        img = cam(BG["sunset"], p, (1.05, 1.22, 0, 0.15))
        n = int(round(13 * ease(min(1, p / 0.45))))
        scaled_text(img, W / 2, 620, str(n), F_HUGE, SUN + (255,), 1.0 + 0.15 * (1 - ease(min(1, p / 0.45))), 40, 8)
        d = ImageDraw.Draw(img, "RGBA")
        if p > 0.3: text_c(d, 880, "AÑOS", F_MED, WHITE, 6)
        if p > 0.55: text_c(d, 1010, "2013  →  2026", F_SM, (255, 220, 240), 4)
        return img
    if name == "iceberg_reveal":
        cy = 1000 + ease(p) * 1700
        img = ice_view(cy, 1.0 + 0.15 * (1 - p)); bubbles(img, t)
        d = ImageDraw.Draw(img, "RGBA")
        text_c(d, 200, "EL ICEBERG DE", F_SM, WHITE, 5)
        scaled_text(img, W / 2, 380, "GTA 6", F(190), PINK + (255,), pop(p, 0.15), 30, 8)
        for k, (qx, qy) in enumerate([(260, 1700), (820, 1580), (540, 1820), (300, 2100), (780, 2200)]):
            yy = qy - (cy - 960) * 0.0 - ease(p) * 1700 + 900
            if 0 < yy < H: d.text((qx, yy), "?", font=F_MED, fill=(220, 255, 255, 170))
        return img
    if name.startswith("level_"):
        k = int(name[-1]); y0 = LEVEL_Y[k - 1] + (200 if k == 1 else 0); y1 = LEVEL_Y[k]
        cy = y0 + (y1 - y0) * ease(min(1, p / 0.55)) + 120
        img = ice_view(cy, 1.08, 40 * math.sin(k)); bubbles(img, t, 0.6 + k * 0.15)
        img = to_img(np.asarray(img, float) * 0.8)
        d = ImageDraw.Draw(img, "RGBA")
        sy = H / 2 + (y1 - cy) * (H / (IW / 1.08 * H / W))
        d.line([0, sy, W, sy], fill=TEAL + (230,), width=8)
        scaled_text(img, W / 2, 560, f"NIVEL {k}", F(170), (WHITE if k < 7 else PINK) + (255,), pop(p, 0.2), 28, 8)
        text_c(d, 720, LEVEL_SUB[k], F_SM, TEAL if k < 7 else HL, 4)
        # mini-indicador de profundidad
        for j in range(1, 8):
            cxj = 140 + (j - 1) * 133
            d.ellipse([cxj - 22, 900 - 22, cxj + 22, 900 + 22], fill=(PINK if j == k else (255, 255, 255, 60 if j > k else 140)))
        return img
    if name == "calendar":
        img = cam(BG["dark"], p, (1.0, 1.1, 0, 0.2)); d = ImageDraw.Draw(img, "RGBA")
        s = 0.7 + 0.3 * ease(min(1, p / 0.3))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        cx, cy, cw, ch = W / 2, 640, 640 * s, 700 * s
        dl.rounded_rectangle([cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2], 50, fill=(250, 245, 255, 255))
        dl.rounded_rectangle([cx - cw / 2, cy - ch / 2, cx + cw / 2, cy - ch / 2 + 190 * s], 50, fill=PINK + (255,))
        dl.rectangle([cx - cw / 2, cy - ch / 2 + 120 * s, cx + cw / 2, cy - ch / 2 + 190 * s], fill=PINK + (255,))
        f1 = F(int(72 * s)); text_c(dl, cy - ch / 2 + 50 * s, "NOV · 2026", f1, WHITE)
        f2 = F(int(330 * s)); text_c(dl, cy - ch / 2 + 170 * s, "19", f2, (30, 10, 50))
        f3 = F(int(56 * s), True); text_c(dl, cy + ch / 2 - 120 * s, "JUEVES", f3, (120, 60, 140))
        img.paste(lay.filter(ImageFilter.GaussianBlur(40)), (0, 0), lay.filter(ImageFilter.GaussianBlur(40)))
        img.paste(lay, (0, 0), lay)
        return img
    if name == "consoles":
        img = cam(BG["sunset_blur"], p, (1.0, 1.1, 0.2, 0)); d = ImageDraw.Draw(img, "RGBA")
        items = [("PS5", TEAL, True), ("XBOX SERIES X|S", TEAL, True), ("PC", RED, False)]
        for i, (s, c, ok) in enumerate(items):
            q = ease(min(1, max(0, (p - i * 0.18) / 0.22)))
            if q <= 0: continue
            y = 330 + i * 250; x = W / 2 + (1 - q) * 900
            d.rounded_rectangle([x - 420, y - 90, x + 420, y + 90], 36, fill=(20, 6, 40, 220), outline=c + (255,), width=7)
            d.text((x - 360, y - 52), s, font=F(78 if len(s) < 6 else 62), fill=WHITE)
            if ok:
                d.line([(x + 270, y), (x + 310, y + 45), (x + 380, y - 50)], fill=TEAL, width=18, joint="curve")
            else:
                d.text((x + 285, y - 70), "?", font=F(130), fill=RED)
                if p > 0.75: d.line([x - 380, y + 6, x + 220, y - 6], fill=RED + (255,), width=14)
        if p > 0.8: text_c(d, 1060, "SIN FECHA EN PC", F_SM, RED, 4)
        return img
    if name == "city":
        img = cam(BG["city"], p, (1.12, 1.0, 0.5, -0.2))
        f = 0.85 + 0.15 * (math.sin(t * 23) > -0.7)
        scaled_text(img, W / 2, 420, "VICE CITY", F(150), tuple(int(c * f) for c in PINK) + (255,), 1.0, 30, 0)
        d = ImageDraw.Draw(img, "RGBA"); text_c(d, 560, "VUELVE", F_SM, TEAL, 4)
        return img
    if name == "map":
        img = cam(BG["dark2"], p, (1.0, 1.08, 0, 0)); d = ImageDraw.Draw(img, "RGBA")
        ox, oy, sx, sy = 90, 160, 900, 1000
        pts = [(ox + x * sx, oy + y * sy) for x, y in MAP]
        n = max(2, int(len(pts) * ease(min(1, p / 0.6))) + 1)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        if p > 0.6: dl.polygon(pts, fill=(0, 235, 215, int(70 * ease((p - 0.6) / 0.3))))
        dl.line((pts + [pts[0]])[:n], fill=TEAL + (255,), width=9, joint="curve")
        paste_glow(img, lay, 18)
        d = ImageDraw.Draw(img, "RGBA")
        if p > 0.45: text_c(d, oy + 0.44 * sy, "LEONIDA", F(66), WHITE, 6, x=ox + 0.755 * sx)
        if p > 0.65:
            px, py = ox + 0.86 * sx, oy + 0.78 * sy - 40 * (1 - ease((p - 0.65) / 0.15))
            d.ellipse([px - 22, py - 22, px + 22, py + 22], fill=PINK); d.polygon([(px - 18, py + 8), (px + 18, py + 8), (px, py + 50)], fill=PINK)
            d.text((px - 300, py - 25), "VICE CITY", font=F_SM, fill=PINK, stroke_width=4, stroke_fill=(0, 0, 0))
        text_c(d, 1130, "ESTADO FICTICIO · INSPIRADO EN FLORIDA", F_XS, (200, 255, 250), 3)
        return img
    if name == "duo":
        img = cam(BG["sunset_blur"], p, (1.0, 1.12, 0, 0.1)); d = ImageDraw.Draw(img, "RGBA")
        q = ease(min(1, p / 0.35))
        for side, col, nm in ((-1, PINK, "LUCÍA"), (1, TEAL, "JASON")):
            cx = W / 2 + side * (230 + (1 - q) * 700); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            dl.ellipse([cx - 120, 330, cx + 120, 600], fill=col + (255,))
            dl.rounded_rectangle([cx - 210, 610, cx + 210, 1060], 150, fill=col + (255,))
            dl.rectangle([cx - 230, 980, cx + 230, 1100], fill=(0, 0, 0, 0))
            paste_glow(img, lay, 30)
            d = ImageDraw.Draw(img, "RGBA"); text_c(d, 1000, nm, F(84), WHITE, 6, x=cx)
        if p > 0.4:
            scaled_text(img, W / 2, 700, "&", F(160), HL + (255,), pop(p - 0.4, 0.15), 24, 6)
        d = ImageDraw.Draw(img, "RGBA"); text_c(d, 180, "1ª VEZ: 2 PROTAGONISTAS", F_SM, WHITE, 4)
        return img
    if name in ("timeline", "timeline_13"):
        img = cam(BG["dark"], p, (1.0, 1.08, 0, 0)); d = ImageDraw.Draw(img, "RGBA")
        rows = [("III → IV", "2001 → 2008", 7, TEAL), ("IV → V", "2008 → 2013", 5, TEAL), ("V → VI", "2013 → 2026", 13, PINK)]
        show = 2 if name == "timeline" else 3
        for i, (lab, yrs, n, col) in enumerate(rows[:show]):
            if name == "timeline_13" and i < 2: q = 1
            else: q = ease(min(1, max(0, (p - (i * 0.3 if name == "timeline" else 0.05)) / 0.4)))
            y = 300 + i * 270
            d.text((90, y - 70), lab, font=F(64), fill=WHITE); d.text((540, y - 58), yrs, font=F_XS, fill=(220, 200, 240))
            L = 62 * n * q
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            dl.rounded_rectangle([90, y + 20, 90 + max(40, L), y + 100], 40, fill=col + (255,))
            paste_glow(img, lay, 16)
            d = ImageDraw.Draw(img, "RGBA")
            if q > 0.05: d.text((110 + max(40, L), y + 8), f"{int(round(n * q))}", font=F(84), fill=col)
        if name == "timeline_13" and p > 0.55:
            text_c(d, 1080, "LA ESPERA MÁS LARGA", F_SM, HL, 4)
        return img
    if name == "leak":
        img = cam(BG["dark"], p, (1.0, 1.1, 0, 0)); d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle([290, 160, 790, 1140], 60, fill=(10, 10, 20), outline=(200, 200, 220), width=8)
        scr = to_img(np.asarray(BG["sunset"].resize((440, 880)).filter(ImageFilter.GaussianBlur(10)), float) * 0.8)
        img.paste(scr, (320, 210)); d = ImageDraw.Draw(img, "RGBA")
        d.ellipse([480, 570, 600, 690], outline=WHITE, width=8); d.polygon([(525, 600), (525, 660), (575, 630)], fill=WHITE)
        if math.sin(t * 40) > 0.3:
            for k in range(6):
                y = int(rng.uniform(220, 1080)); d.rectangle([320, y, 760, y + int(rng.uniform(4, 18))], fill=(255, 60, 170, 120))
        if p > 0.3:
            q = pop(p - 0.3, 0.15); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            badge(dl, W / 2, 640, "FILTRADO", F(120), (0, 0, 0, 0), RED + (255,), 40, 30, outline=RED + (255,))
            lay = lay.rotate(-12 + 0 * q, center=(W / 2, 640)); paste_glow(img, lay, 14)
        d = ImageDraw.Draw(img, "RGBA"); text_c(d, 1060, "DICIEMBRE 2023", F_XS, (220, 220, 240), 3)
        return img
    if name == "stat_90":
        img = cam(BG["city_blur"], p, (1.0, 1.1, 0.3, 0))
        counter(img, p, 90, "MILLONES", "VISITAS EN YOUTUBE · 24 H", HL)
        d = ImageDraw.Draw(img, "RGBA")
        if p > 0.55: badge(d, W / 2, 1060, "RÉCORD GUINNESS", F(62), PINK + (255,))
        return img
    if name == "stat_475":
        img = cam(BG["sunset_blur"], p, (1.0, 1.12, 0, 0.2))
        counter(img, p, 475, "MILLONES", "EN 24 HORAS", PINK)
        d = ImageDraw.Draw(img, "RGBA"); text_c(d, 1070, "SEGÚN ROCKSTAR", F_XS, (255, 230, 240), 3)
        return img
    if name == "stat_475b":
        img = cam(BG["dark"], p, (1.0, 1.08, 0, 0)); d = ImageDraw.Draw(img, "RGBA")
        q = ease(min(1, p / 0.6))
        for i, (lab, sub, v, col) in enumerate([("TRÁILER 1", "SOLO YOUTUBE", 90, TEAL), ("TRÁILER 2", "TODAS LAS PLATAFORMAS", 475, PINK)]):
            x = 300 + i * 480; top = 1100 - 1.6 * v * q
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            dl.rounded_rectangle([x - 130, top, x + 130, 1100], 30, fill=col + (255,)); paste_glow(img, lay, 20)
            d = ImageDraw.Draw(img, "RGBA")
            text_c(d, top - 120, f"{int(v * q)} M", F(84), WHITE, 5, x=x)
            text_c(d, 1120, lab, F(54), WHITE, 0, x=x)
        text_c(d, 150, "VISITAS EN 24 HORAS", F_SM, HL, 4)
        return img
    if name == "stat_230":
        img = ice_view(IH - 1100, 1.05); img = to_img(np.asarray(img, float) * 0.55); bubbles(img, t, 0.4)
        counter(img, p, 230, "MILLONES", "DE COPIAS DE GTA V", TEAL, prefix="+")
        return img
    if name == "boxes":
        img = cam(BG["dark"], p, (1.0, 1.1, 0, -0.2)); d = ImageDraw.Draw(img, "RGBA")
        n = int(46 * ease(min(1, p / 0.7)))
        for i in range(n):
            col = i % 7; row = i // 7
            x = 130 + col * 120; y = 1100 - row * 150
            c = [PINK, TEAL, SUN][i % 3]
            d.rounded_rectangle([x, y - 130, x + 100, y], 12, fill=(30, 10, 50), outline=c, width=6)
            d.rectangle([x + 14, y - 112, x + 86, y - 70], fill=c + (160,))
        bar = 1100 - 7 * 150 - 20
        if p > 0.6:
            d.line([80, bar, W - 80, bar], fill=HL + (255,), width=14)
            text_c(d, bar - 120, "EL LISTÓN", F(80), HL, 6)
        return img
    if name in ("end_q", "end_card"):
        img = cam(BG["sunset"], p if name == "end_q" else 1, (1.0, 1.15, 0, 0.1))
        img = to_img(np.asarray(img, float) * (0.75 if name == "end_q" else 0.45))
        d = ImageDraw.Draw(img, "RGBA")
        if name == "end_q":
            scaled_text(img, W / 2, 420, "¿DÍA 1", F(170), PINK + (255,), pop(p, 0.18), 30, 8)
            if p > 0.35: scaled_text(img, W / 2, 680, "O PC?", F(170), TEAL + (255,), pop(p - 0.35, 0.18), 30, 8)
        else:
            text_c(d, 220, "COMENTA", F_MED, WHITE, 6)
            badge(d, W / 2 - 230, 520, "DÍA 1", F(84), PINK + (255,))
            badge(d, W / 2 + 230, 520, "PC", F(84), (0, 170, 160, 255))
            cx = W / 2; yb = 700 + 18 * math.sin(t * 8)
            d.polygon([(cx - 50, yb), (cx + 50, yb), (cx, yb + 66)], fill=HL)
        return img
    raise KeyError(name)

SHOTS = shot_timeline()
CAPS = caption_timeline()
HITS = hits()

def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, s = cur[0]
    age = t - a
    sc = 0.82 + 0.18 * min(1, age / 0.11) + 0.04 * math.sin(min(1, age / 0.11) * math.pi)
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    parts, hl = [], False
    for w in s.split(" "):
        if w.startswith("*"): hl = True
        parts.append((w.replace("*", ""), hl))
        if w.rstrip("…?!,:.").endswith("*"): hl = False
    full = " ".join(p[0] for p in parts)
    font = F_CAP
    while d.textlength(full, font=font) > W - 90: font = ImageFont.truetype(FONT, font.size - 6)
    x = (W - d.textlength(full, font=font)) / 2
    for i, (wd, h) in enumerate(parts):
        txt = wd + (" " if i < len(parts) - 1 else "")
        d.text((x, 60), txt, font=font, fill=(HL if h else WHITE) + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255))
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
    XF = 0.16
    if i + 1 < len(SHOTS) and t > b - XF:
        a2, b2, n2 = SHOTS[i + 1]
        img = Image.blend(img, shot_frame(n2, t, a2, b2), (t - (b - XF)) / XF)
    arr = np.asarray(img, float) * VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.22: arr = arr + (1 - u / 0.22) * 120
    g = GRAIN[fi % 4]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    arr = (arr - 128) * 1.05 + 128
    if t > TOTAL - 0.5: arr *= max(0, (TOTAL - t) / 0.5)
    img = to_img(arr)
    cap = caption_layer(t)
    if cap is not None: img.paste(cap, (0, 1250), cap)
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
    elif sys.argv[1] == "contact":       # hoja de contactos: un fotograma en mitad de cada plano
        ims = [frame((a + b) / 2 + 0.3 * (b - a) * 0, 0).resize((270, 480)) for a, b, _ in SHOTS]
        cols = 8; rows = math.ceil(len(ims) / cols); sheet = Image.new("RGB", (cols * 270, rows * 480))
        for k, im in enumerate(ims): sheet.paste(im, ((k % cols) * 270, (k // cols) * 480))
        sheet.save(os.path.join(HERE, "still_contact.jpg"), quality=80)
    else:
        for si in [int(x) for x in sys.argv[2:]]:
            render_scene(si, os.path.join(HERE, f"scene_{si:02}.mp4")); print("scene", si, flush=True)
