import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, TOTAL, caption_timeline, shot_timeline, hits

W, H, FPS = 1080, 1920, 30
BW, BH = 1300, 2310          # fondos más grandes para mover la cámara
rng = np.random.default_rng(13)
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_CY = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"      # cirílico
FONT_TY = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"  # máquina de escribir
F_CAP = ImageFont.truetype(FONT, 100)
F_BIG = ImageFont.truetype(FONT, 340)
F_MED = ImageFont.truetype(FONT, 88)
F_SM = ImageFont.truetype(FONT, 50)
F_CY = ImageFont.truetype(FONT_CY, 64)
F_TY = ImageFont.truetype(FONT_TY, 50)
RED = (235, 38, 38); COLD = (170, 205, 235); WARM = (255, 150, 60)

# ---------------------------------------------------------------- utilidades
def grad(c1, c2, w=BW, h=BH, power=1.0):
    y = (np.linspace(0, 1, h) ** power)[:, None, None]
    a = np.array(c1, float); b = np.array(c2, float)
    return np.broadcast_to(a + (b - a) * y, (h, w, 3)).copy()

def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def noise_tex(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((h // scale + 2, w // scale + 2))
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, float) / 255

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)

def text_c(d, y, s, font, fill, stroke=0, sc=(0, 0, 0), x=None):
    w = d.textlength(s, font=font)
    d.text(((W - w) / 2 if x is None else x - w / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)

def paste_glow(img, lay, r=22, k=1):
    g = lay.filter(ImageFilter.GaussianBlur(r))
    for _ in range(k): img.paste(g, (0, 0), g)
    img.paste(lay, (0, 0), lay)

def cam(bg, p, mode):
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * (ease(p) * 0.5 + p * 0.5)
    cw, ch = BW / z, BH / z
    cx = BW / 2 + dx * (p - 0.5) * (BW - cw); cy = BH / 2 + dy * (p - 0.5) * (BH - ch)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

# ---------------------------------------------------------------- escenario: ladera nevada
def cam_at(bg, p, cx, cy, z0, z1, dx=0, dy=0):
    """Encuadre centrado en (cx, cy) del fondo, con zoom z0->z1 y una leve deriva."""
    z = z0 + (z1 - z0) * (ease(p) * 0.5 + p * 0.5)
    cw, ch = BW / z, BH / z
    cx = min(max(cx + dx * (p - 0.5), cw / 2), BW - cw / 2); cy = min(max(cy + dy * (p - 0.5), ch / 2), BH - ch / 2)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def ridge_y(x, base=1080, seed=0):
    return base - 260 * abs(math.sin(x * 0.0031 + seed)) - 90 * abs(math.sin(x * 0.011 + seed * 2)) - 30 * math.sin(x * 0.04 + seed)

def snow_tex(shape, seed, c1=(150, 165, 188), c2=(70, 82, 104)):
    h, w = shape
    a = grad(c1, c2, w, h)
    n = noise_tex(w, h, 6, seed) * 0.5 + noise_tex(w, h, 50, seed + 1) * 0.5
    return a * (0.78 + 0.35 * n)[..., None]

def bg_slope(seed=1, sky=((3, 5, 12), (32, 40, 58)), peak=False):
    a = grad(*sky, power=1.4)
    st = rng.random((BH, BW)) > 0.9988
    a[st] = [200, 210, 230]
    img = to_img(a); d = ImageDraw.Draw(img)
    # luna velada
    m = Image.new("RGB", (BW, BH)); dm = ImageDraw.Draw(m)
    dm.ellipse([200, 260, 360, 420], fill=(190, 200, 215))
    img = to_img(np.asarray(img, float) + np.asarray(m.filter(ImageFilter.GaussianBlur(90)), float) * 0.7
                 + np.asarray(m.filter(ImageFilter.GaussianBlur(6)), float) * 0.45)
    d = ImageDraw.Draw(img)
    # montañas del fondo
    if peak:
        pts = [(0, 1250), (300, 1000), (520, 760), (650, 560), (760, 720), (980, 950), (BW, 1150), (BW, BH), (0, BH)]
        d.polygon(pts, fill=(48, 56, 74))
        d.polygon([(520, 760), (650, 560), (760, 720), (700, 690), (650, 740), (590, 700)], fill=(150, 160, 180))
    pts = [(0, BH)] + [(x, ridge_y(x, 1150, seed)) for x in range(0, BW + 20, 20)] + [(BW, BH)]
    d.polygon(pts, fill=(36, 42, 58))
    # ladera principal (nieve con textura)
    mask = Image.new("L", (BW, BH)); dmk = ImageDraw.Draw(mask)
    dmk.polygon([(0, 1500), (BW, 1260), (BW, BH), (0, BH)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(4))
    snow = to_img(snow_tex((BH, BW), seed + 5) * grad((0.75,) * 3, (1.0,) * 3))
    img.paste(snow, (0, 0), mask)
    return img

def tent(d, cx, cy, s, glow=0.0, collapsed=False, slit=False):
    top = cy - (0.42 if collapsed else 0.8) * s
    A, B, C = (cx - 0.6 * s, cy), (cx + 0.6 * s, cy), (cx + (0.1 * s if collapsed else 0), top)
    v = (-1.9 * s, -0.28 * s)
    roof = [C, (C[0] + v[0], C[1] + v[1] + (0.25 * s if collapsed else 0)), (A[0] + v[0], A[1] + v[1]), A]
    d.polygon(roof, fill=(52, 58, 52) if not glow else (int(70 + 150 * glow), int(50 + 80 * glow), int(30 + 20 * glow)))
    d.polygon([A, B, C], fill=(70, 76, 66) if not glow else (int(90 + 165 * glow), int(60 + 110 * glow), int(30 + 30 * glow)))
    if slit:
        sx = C[0] + v[0] * 0.55; sy = C[1] + v[1] * 0.55
        d.line([(sx, sy + 0.08 * s), (sx - 0.12 * s, sy + 0.62 * s)], fill=(5, 5, 8), width=max(4, int(s * 0.05)))
    if collapsed:   # nieve encima
        d.polygon([C, (C[0] + v[0], C[1] + v[1] + 0.25 * s), (C[0] + v[0] - 0.1 * s, C[1] + v[1] + 0.33 * s), (C[0] + 0.05 * s, top + 0.12 * s)],
                  fill=(175, 185, 205))
    d.line([C, (C[0], C[1] - 0.12 * s)], fill=(30, 30, 30), width=5)

def bg_tent(glow=0.0, collapsed=False, slit=False, seed=1):
    img = bg_slope(seed)
    lay = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    tent(d, 780, 1560, 300, glow, collapsed, slit)
    if glow:
        g = lay.filter(ImageFilter.GaussianBlur(70))
        img.paste(g, (0, 0), g)
    img.paste(lay, (0, 0), lay)
    if glow:   # luz cálida sobre la nieve
        ar = np.asarray(img, float); yy, xx = np.mgrid[0:BH, 0:BW]
        l = np.exp(-(((xx - 720) / 520) ** 2 + ((yy - 1620) / 260) ** 2)) * glow
        ar += l[..., None] * np.array([150, 80, 25]); img = to_img(ar)
    return img

# ---------------------------------------------------------------- primer plano: lona rajada
def bg_canvas():
    a = grad((62, 70, 58), (40, 46, 38))
    yy, xx = np.mgrid[0:BH, 0:BW]
    weave = (np.sin(xx * 0.9) * np.sin(yy * 0.9)) * 6
    folds = np.sin(xx * 0.006 + np.sin(yy * 0.003) * 2) * 18
    a += (weave + folds)[..., None] + (noise_tex(BW, BH, 30, 3)[..., None] - 0.5) * 30
    return to_img(a)
CANVAS = None
OUTSIDE = None
def slash_frame(t, p):
    img = cam(CANVAS, p, (1.0, 1.12, 0.1, -0.1)).convert("RGB")
    cut = ease(min(1, p / 0.55))
    if cut > 0:
        x0, y0, x1, y1 = 640, 260, 420, 1700
        xe, ye = x0 + (x1 - x0) * cut, y0 + (y1 - y0) * cut
        n = 40
        pts_l, pts_r = [], []
        for i in range(n + 1):
            u = i / n * cut
            x = x0 + (x1 - x0) * u / max(cut, 1e-3) * cut; y = y0 + (y1 - y0) * u / max(cut, 1e-3) * cut
            x = x0 + (x1 - x0) * (i / n) * cut; y = y0 + (y1 - y0) * (i / n) * cut
            open_w = 70 * math.sin(math.pi * (i / n)) * min(1, cut * 1.4) * (0.6 + 0.4 * ease(p * 1.5))
            j = 8 * math.sin(i * 2.7)
            pts_l.append((x - open_w + j, y)); pts_r.append((x + open_w + j, y))
        hole = Image.new("L", (W, H)); dh = ImageDraw.Draw(hole)
        dh.polygon(pts_l + pts_r[::-1], fill=255)
        out = OUTSIDE.copy(); draw_snow(out, t, 1.0, big=True)
        img.paste(out, (0, 0), hole)
        d = ImageDraw.Draw(img)
        d.line(pts_l, fill=(110, 118, 100), width=6); d.line(pts_r, fill=(110, 118, 100), width=6)
        # filo del cuchillo en la punta
        if cut < 1:
            d.polygon([(xe - 14, ye - 120), (xe + 14, ye - 120), (xe + 3, ye + 10), (xe - 3, ye + 10)], fill=(215, 220, 230))
            d.rectangle([xe - 22, ye - 330, xe + 22, ye - 120], fill=(25, 18, 14))
    return img

# ---------------------------------------------------------------- huellas en la nieve
def footprint(d, x, y, ang, s, col):
    ca, sa = math.cos(ang), math.sin(ang)
    def P(u, v): return (x + u * ca - v * sa, y + u * sa + v * ca)
    pts = [P(s * 0.55 * math.cos(k / 20 * 2 * math.pi) * (1 - 0.25 * math.sin(k / 20 * 2 * math.pi)), s * 0.24 * math.sin(k / 20 * 2 * math.pi)) for k in range(20)]
    d.polygon(pts, fill=col)
    for k in range(5):
        tx, ty = P(-s * 0.72, (k - 2) * s * 0.11)
        r = s * (0.07 if k else 0.09)
        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=col)

def bg_snowfield(seed):
    return to_img(snow_tex((3800, BW), seed, (190, 200, 218), (150, 162, 185)))
def make_prints(seed, n=26, start=(560, -100), step=(0, 115), wander=60):
    r = np.random.default_rng(seed); out = []
    x, y = start
    for i in range(n * 3):
        side = 1 if i % 2 else -1
        out.append((x + side * 58 + r.normal(0, 6), y, math.pi / 2 + r.normal(0, 0.12), 92))
        x += step[0] + r.normal(0, wander * 0.15); y += step[1]
    return out
PRINTS = {}
def footprints_frame(t, p, key, dim=0.45):
    bg = BG[key]; prints = PRINTS[key]
    yc = 400 + p * 1000                           # la cámara sigue el rastro
    img = bg.crop((110, int(yc), 110 + W, int(yc) + H))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    head = yc + 300 + p * 1300
    for (x, y, a, s) in prints:
        if y > head: break
        sy = y - yc
        if -100 < sy < H + 100:
            footprint(d, x - 110, sy + 6, a, s, (70, 85, 110, 170))
            footprint(d, x - 110, sy, a, s * 0.92, (115, 130, 158, 255))
    img = img.convert("RGBA"); img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2.2)))
    ar = np.asarray(img.convert("RGB"), float) * dim * np.array([0.8, 0.9, 1.15])
    yy, xx = np.mgrid[0:H, 0:W]                    # haz de linterna
    lx = W / 2 + 120 * math.sin(t * 1.3); ly = H * 0.55 + 140 * math.sin(t * 0.9)
    l = np.exp(-(((xx - lx) / 420) ** 2 + ((yy - ly) / 520) ** 2))
    ar = ar * (1 + 1.4 * l[..., None])
    img = to_img(ar); draw_snow(img, t, 0.7)
    return img

# ---------------------------------------------------------------- figuras
def hiker(d, x, y, s, phase, col, facing=1):
    hb = y - s
    d.ellipse([x - s * 0.11, hb - s * 0.02, x + s * 0.11, hb + s * 0.2], fill=col)            # cabeza
    d.rounded_rectangle([x - s * 0.13, hb + s * 0.2, x + s * 0.13, y - s * 0.42], int(s * 0.06), fill=col)
    bx0, bx1 = sorted([x - facing * s * 0.33, x - facing * s * 0.08])
    d.rounded_rectangle([bx0, hb + s * 0.18, bx1, y - s * 0.5], int(s * 0.05), fill=col)  # mochila
    sw = math.sin(phase) * s * 0.18
    d.line([(x, y - s * 0.44), (x + sw, y)], fill=col, width=max(3, int(s * 0.09)))
    d.line([(x, y - s * 0.44), (x - sw, y)], fill=col, width=max(3, int(s * 0.09)))
    d.line([(x + facing * s * 0.1, hb + s * 0.3), (x + facing * s * 0.32 + sw * 0.3, y)], fill=col, width=max(2, int(s * 0.03)))  # bastón

def bg_dusk(seed=2):
    a = grad((22, 26, 48), (120, 80, 90), power=1.6)
    img = to_img(a); d = ImageDraw.Draw(img)
    pts = [(0, BH)] + [(x, ridge_y(x, 1050, seed + 3) - 120) for x in range(0, BW + 20, 20)] + [(BW, BH)]
    d.polygon(pts, fill=(60, 58, 80))
    pts = [(0, BH)] + [(x, 1450 - 120 * math.sin(x * 0.0024 + 1)) for x in range(0, BW + 20, 20)] + [(BW, BH)]
    d.polygon(pts, fill=(14, 14, 24))
    return img
def ground_y(x): return 1450 - 120 * math.sin(x * 0.0024 + 1)

def hikers_frame(t, p, survivor=False):
    img = cam(BG["dusk"], p, (1.08, 1.16, 0.3 if not survivor else -0.3, 0)).convert("RGB")
    d = ImageDraw.Draw(img)
    for k in range(10):
        if survivor:
            if k == 0:
                x = 470 - p * 300; ph = t * 5
                hiker(d, x, 1260, 210, ph, (8, 8, 12), facing=-1)
            else:
                x = 620 + k * 48 + p * 120; hiker(d, x, 1150 - k * 4, 70, t * 6 + k, (10, 10, 16), facing=1)
        else:
            x = 120 + k * 92 + p * 160
            hiker(d, x, 1235 - 70 * math.sin((x / W) * 2.6 + 0.6), 105, t * 6 + k * 0.8, (8, 8, 14))
    draw_snow(img, t, 0.7)
    if survivor and p > 0.25:
        dd = ImageDraw.Draw(img, "RGBA")
        a = int(255 * min(1, (p - 0.25) / 0.2))
        text_c(dd, 300, "YURI YUDIN", F_MED, (255, 255, 255, a), 6)
        text_c(dd, 410, "EL ÚNICO SUPERVIVIENTE", F_SM, RED + (a,), 5)
    if not survivor:
        dd = ImageDraw.Draw(img, "RGBA")
        for k in range(10):
            x = 120 + k * 92 + p * 160
            if p > 0.15 + k * 0.05:
                text_c(dd, 1000 - 70 * math.sin((x / W) * 2.6 + 0.6), str(k + 1), F_SM, (255, 255, 255, 200), 4, x=x)
    return img

# ---------------------------------------------------------------- cedro y hoguera
def bg_cedar():
    img = bg_slope(7, sky=((2, 4, 10), (20, 26, 40)))
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(4)
    for x in np.sort(r.uniform(-100, BW + 100, 9)):   # bosque al fondo
        b = 1350 + r.uniform(-40, 40); hh = r.uniform(400, 650)
        for i in range(7):
            y0 = b - hh * i / 7; ww = hh * 0.4 * (1 - i / 8)
            d.polygon([(x - ww / 2, y0), (x + ww / 2, y0), (x, y0 - hh * 0.28)], fill=(14, 20, 26))
    col = (6, 7, 10)
    d.polygon([(560, 1800), (740, 1800), (690, 300), (620, 300)], fill=col)          # tronco
    def br(x, y, ang, L, dep, w):
        if dep == 0:
            d.ellipse([x - 70, y - 30, x + 70, y + 30], fill=col); return
        x2, y2 = x + L * math.cos(ang), y + L * math.sin(ang)
        d.line([x, y, x2, y2], fill=col, width=int(w))
        br(x2, y2, ang + r.uniform(-0.5, -0.1), L * 0.65, dep - 1, w * 0.6)
        br(x2, y2, ang + r.uniform(0.1, 0.5), L * 0.65, dep - 1, w * 0.6)
    for k in range(9):
        y = 420 + k * 120
        if k in (6, 7, 8):   # ramas bajas partidas
            for s in (-1, 1):
                x0 = 655 + s * 40; d.line([x0, y, x0 + s * 120, y + 40], fill=col, width=18)
            continue
        for s in (-1, 1):
            br(655, y, (math.pi if s < 0 else 0) + s * -0.35, 230 - k * 8, 3, 22)
    return img

def cedar_frame(t, p):
    img = cam(BG["cedar"], p, (1.0, 1.14, 0, 0.3))
    ar = np.asarray(img, float); yy, xx = np.mgrid[0:H, 0:W]
    fl = 0.75 + 0.25 * math.sin(t * 23) * math.sin(t * 7.3)
    l = np.exp(-(((xx - 540) / 380) ** 2 + ((yy - 1560) / 300) ** 2)) * fl
    ar += l[..., None] * np.array([190, 85, 20])
    img = to_img(ar)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(18):   # pavesas
        ph = (t * 0.6 + k * 0.137) % 1
        x = 540 + 120 * math.sin(k * 3.1 + t * 2) * ph; y = 1600 - ph * 700
        r = 6 * (1 - ph) + 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 170, 60, int(255 * (1 - ph))))
    for k in range(7):    # brasas
        x = 470 + k * 22; y = 1600 + 8 * math.sin(k)
        d.ellipse([x - 14, y - 8, x + 14, y + 8], fill=(255, int(90 + 60 * math.sin(t * 9 + k)), 30, 255))
    paste_glow(img, lay, 14)
    draw_snow(img, t, 0.6)
    return img

# ---------------------------------------------------------------- barranco
def bg_ravine():
    a = snow_tex((BH, BW), 31, (120, 135, 160), (40, 48, 64))
    img = to_img(a); d = ImageDraw.Draw(img)
    l = [(0, 0), (520, 0)] + [(470 - 260 * (y / BH) + 40 * math.sin(y * 0.01), y) for y in range(0, BH, 40)] + [(0, BH)]
    rr = [(BW, 0), (780, 0)] + [(830 + 260 * (y / BH) + 40 * math.sin(y * 0.013 + 2), y) for y in range(0, BH, 40)] + [(BW, BH)]
    d.polygon(l, fill=(16, 18, 26)); d.polygon(rr, fill=(12, 14, 22))
    # arroyo bajo la nieve
    pts = [(650 + 60 * math.sin(y * 0.006), y) for y in range(900, BH, 30)]
    d.line(pts, fill=(20, 30, 45), width=60)
    return to_img(np.asarray(img, float) * 0.75)

# ---------------------------------------------------------------- rayos X
def xray_frame(t, p):
    img = to_img(grad((0, 6, 14), (4, 16, 30), W, H))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx = W / 2; flick = 0.85 + 0.15 * math.sin(t * 40)
    colb = (180, 220, 255, int(230 * flick))
    for k in range(14):
        y = 380 + k * 52; d.rounded_rectangle([cx - 26, y, cx + 26, y + 40], 10, fill=colb)
    ribs = []
    for i in range(10):
        yi = 430 + i * 72
        for s in (-1, 1):
            pts = [(cx + s * (40 + (300 - abs(i - 4) * 14) * math.sin(u * math.pi * 0.85)), yi + 170 * u * u - 40 * math.sin(u * math.pi))
                   for u in np.linspace(0, 1, 32)]
            d.line(pts, fill=colb, width=20, joint="curve"); ribs.append((i, s, pts))
    d.line([(cx - 120, 360), (cx - 380, 330)], fill=colb, width=24); d.line([(cx + 120, 360), (cx + 380, 330)], fill=colb, width=24)
    paste_glow(img, lay, 20)
    if p > 0.35:
        dd = ImageDraw.Draw(img)
        r = np.random.default_rng(5)
        for (i, s, pts) in ribs:
            if i in (2, 3, 4, 5) and (s == -1 or i in (3, 4)):
                k = 12 + i
                x, y = pts[k]
                z = [(x + r.uniform(-14, 14), y - 26 + j * 13) for j in range(5)]
                dd.line(z, fill=RED, width=7)
        a = min(1, (p - 0.35) / 0.15)
        text_c(dd, 1080, "FRACTURAS", F_MED, tuple(int(c * a) for c in RED), 5)
    return img

# ---------------------------------------------------------------- contador Geiger
def geiger_frame(t, p):
    img = cam(BG["ravine"], 0.5, (1.4, 1.4, 0, 0)).filter(ImageFilter.GaussianBlur(10))
    img = to_img(np.asarray(img, float) * 0.35)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([170, 380, 910, 1160], 50, fill=(196, 170, 52), outline=(40, 36, 20), width=10)
    d.rounded_rectangle([230, 440, 850, 860], 30, fill=(235, 228, 205), outline=(30, 30, 30), width=6)
    cx, cy, R = 540, 820, 300
    for k in range(11):
        a = math.radians(200 + k * 14)
        d.line([cx + R * math.cos(a), cy + R * math.sin(a), cx + (R - 40) * math.cos(a), cy + (R - 40) * math.sin(a)],
               fill=(20, 20, 20) if k < 8 else RED, width=6)
    d.arc([cx - R + 20, cy - R + 20, cx + R - 20, cy + R - 20], 312, 340, fill=RED, width=16)
    jit = math.sin(t * 37) * 3 + math.sin(t * 61) * 2
    val = 200 + 14 * (1 + 6.5 * ease(p / 0.7)) + jit
    a = math.radians(val)
    d.line([cx, cy, cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a)], fill=(15, 15, 15), width=9)
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(15, 15, 15))
    text_c(d, 885, "☢", ImageFont.truetype(FONT_CY, 150), (25, 25, 25))
    d.text((240, 1060), "ДП-5", font=F_CY, fill=(30, 30, 20))
    blink = int(t * 8) % 2 == 0
    d.ellipse([780, 1050, 840, 1110], fill=RED if blink else (80, 20, 20))
    return img

# ---------------------------------------------------------------- expediente
def bg_paper():
    a = grad((214, 200, 165), (188, 170, 128))
    a *= (0.9 + 0.18 * noise_tex(BW, BH, 4, 8) + 0.1 * noise_tex(BW, BH, 80, 9))[..., None]
    yy, xx = np.mgrid[0:BH, 0:BW]
    st = np.exp(-(((xx - 980) / 170) ** 2 + ((yy - 1700) / 140) ** 2))
    a *= (1 - 0.18 * st)[..., None]
    img = to_img(a); d = ImageDraw.Draw(img)
    d.text((150, 260), "УГОЛОВНОЕ ДЕЛО", font=F_CY, fill=(40, 34, 26))
    d.text((150, 350), "Свердловск · 1959", font=ImageFont.truetype(FONT_CY, 44), fill=(60, 52, 40))
    r = np.random.default_rng(3)
    for k in range(26):
        y = 520 + k * 58
        if 840 < y < 1060: continue
        x = 150
        while x < 1120:
            w = r.uniform(30, 150)
            if x + w > 1150: break
            d.rectangle([x, y, x + w, y + 14], fill=(70, 62, 50)); x += w + 18
    return img

def file_frame(t, p):
    img = cam(BG["paper"], p, (1.05, 1.18, 0.1, -0.2)).convert("RGB")
    d = ImageDraw.Draw(img)
    q = "«FUERZA NATURAL"; q2 = "IRRESISTIBLE»"
    n = int(len(q + q2) * min(1, max(0, (p - 0.45) / 0.4)))
    d.text((120, 860), q[:n], font=F_TY, fill=(25, 22, 18))
    d.text((120, 930), q2[:max(0, n - len(q))], font=F_TY, fill=(25, 22, 18))
    sp = (p - 0.3)
    if sp > 0:   # el sello cae
        sc = 1 + 1.5 * max(0, 1 - sp / 0.06)
        st = Image.new("RGBA", (900, 260), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle([10, 10, 890, 250], 20, outline=(190, 25, 25, 230), width=14)
        fz = ImageFont.truetype(FONT_CY, 130)
        ds.text((450 - ds.textlength("ЗАКРЫТО", font=fz) / 2, 45), "ЗАКРЫТО", font=fz, fill=(190, 25, 25, 220))
        grit = (noise_tex(900, 260, 3, 12) > 0.35).astype(np.uint8)
        al = np.asarray(st)[..., 3] * grit
        st.putalpha(Image.fromarray(al.astype(np.uint8)))
        st = st.resize((int(900 * sc), int(260 * sc))).rotate(-12, expand=True)
        img.paste(st, (int(W / 2 - st.width / 2), int(560 - st.height / 2)), st)
        d = ImageDraw.Draw(img)
        if sp > 0.06: text_c(d, 690, "(CASO CERRADO)", F_SM, (150, 25, 25))
    return to_img(np.asarray(img, float) * 0.82)

# ---------------------------------------------------------------- alud
def avalanche_frame(t, p):
    sh = 18 * max(0, 1 - p) if p > 0.05 else 0
    img = cam_at(BG["tent"], p, 600, 1300, 1.1, 1.2)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    front = -400 + ease(p / 0.8) * 1900
    pts = [(-50, -50), (W + 50, -50), (W + 50, front - 500)]
    for x in range(W + 50, -60, -30):
        pts.append((x, front - 500 * (x / W) + 50 * math.sin(x * 0.03 + t * 5) + 30 * math.sin(x * 0.11)))
    d.polygon(pts, fill=(205, 215, 230, 245))
    lay2 = lay.filter(ImageFilter.GaussianBlur(10))
    img.paste(lay2, (0, 0), lay2)
    draw_snow(img, t, 1.0, big=True)
    if sh: img = img.transform(img.size, Image.AFFINE, (1, 0, sh * math.sin(t * 60), 0, 1, sh * math.cos(t * 47)))
    return img

# ---------------------------------------------------------------- niebla y final
FOG = None
def fog(img, t, k=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for j in range(16):
        x = (j * 197 + t * (30 + j * 4)) % (W + 600) - 300; y = 900 + (j % 5) * 180 + 50 * math.sin(t * 0.5 + j)
        d.ellipse([x - 360, y - 110, x + 360, y + 110], fill=(160, 170, 190, int(38 * k)))
    lay = lay.filter(ImageFilter.GaussianBlur(50)); img.paste(lay, (0, 0), lay)

def tent_glow_frame(t, p):
    on = 1.0 if not (0.62 < p < 0.66 or 0.72 < p < 0.75 or p > 0.86) else 0.0   # parpadeo y apagón
    img = cam_at(BG["tent_glow"] if on else BG["tent"], p, 560, 1430, 1.25, 1.7)
    if on:
        d = ImageDraw.Draw(img, "RGBA")
        z = 1.25 + 0.45 * (ease(p) * 0.5 + p * 0.5)
        sx = 760 + 30 * math.sin(t * 2)        # sombra de alguien dentro
        k = W / (BW / z)
        hx = W / 2 + (sx - 560) * k; hy = H / 2 + (1390 - 1430) * k
        u = k * 0.5
        d.ellipse([hx - 30 * u, hy - 30 * u, hx + 30 * u, hy + 30 * u], fill=(40, 20, 10, 170))
        d.polygon([(hx - 60 * u, hy + 150 * u), (hx + 60 * u, hy + 150 * u), (hx + 30 * u, hy + 30 * u), (hx - 30 * u, hy + 30 * u)], fill=(40, 20, 10, 170))
    draw_snow(img, t, 0.8)
    return img

def end_frame(t, p):
    img = cam_at(BG["tent"], p, 560, 1430, 1.7, 1.9)
    img = to_img(np.asarray(img, float) * (1 - 0.55 * min(1, p * 2)))
    fog(img, t, 1.2)
    d = ImageDraw.Draw(img, "RGBA")
    if p > 0.08:
        text_c(d, 250, "¿QUÉ LOS", F_MED, (255, 255, 255), 6)
        text_c(d, 360, "HIZO *HUIR*?".replace("*", ""), F_MED, RED, 6)
        cx = W / 2; yb = 520 + 18 * math.sin(t * 8)
        d.polygon([(cx - 45, yb), (cx + 45, yb), (cx, yb + 60)], fill=RED)
    return img

# ---------------------------------------------------------------- nieve
FLAKES = rng.random((300, 5))
def draw_snow(img, t, density=1.0, big=False):
    d = ImageDraw.Draw(img, "RGBA")
    for fx, fy, fs, sp, ph in FLAKES[:int(len(FLAKES) * density)]:
        s = (2 + fs ** 3 * 12) * (2.0 if big else 1)
        y = (fy * H + t * (90 + sp * 260) * (1 + fs)) % (H + 40) - 20
        x = (fx * W + t * 160 * (0.5 + fs) + 50 * math.sin(t * (0.5 + ph) + ph * 6)) % W   # viento lateral
        d.ellipse([x - s, y - s, x + s, y + s], fill=(225, 232, 245, int(80 + fs * 140)))

# ---------------------------------------------------------------- fondos
print("generando fondos", flush=True)
BG = {"tent": bg_tent(), "tent_glow": bg_tent(1.0), "tent_empty": bg_tent(0, True, True), "mountain": bg_slope(3, peak=True),
      "dusk": bg_dusk(), "cedar": bg_cedar(), "ravine": bg_ravine(), "paper": bg_paper(),
      "snow1": bg_snowfield(1), "snow2": bg_snowfield(2)}
CANVAS = bg_canvas()
OUTSIDE = to_img(np.asarray(cam(BG["tent"], 0.5, (1.6, 1.6, 0, 0)).filter(ImageFilter.GaussianBlur(6)), float) * 0.6)
PRINTS["snow1"] = make_prints(1); PRINTS["snow2"] = make_prints(2, wander=140)
yy, xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1.2 - (((xx - W / 2) / (W * 0.55)) ** 2 + ((yy - H / 2) / (H * 0.58)) ** 2) * 0.75, 0.12, 1)[..., None]
GRAIN = [(rng.standard_normal((H // 2, W // 2)) * 10) for _ in range(4)]

MODES = {"mountain": (1.0, 1.2, 0, -0.3), "tent_night": (1.0, 1.3, 0.3, 0.3), "searchers": (1.1, 1.25, -0.3, 0.2),
         "tent_empty": (1.3, 1.6, 0.3, 0.35), "ravine": (1.0, 1.2, 0, 0.6), "mountain_fog": (1.2, 1.0, 0, -0.2)}
CENTER = {"tent_night": (600, 1300, 1.05, 1.4, 0, 60), "searchers": (620, 1250, 1.0, 1.15, -80, 0),
          "tent_empty": (560, 1450, 1.5, 1.9, 60, 0)}
SRC = {"tent_night": "tent", "searchers": "tent", "mountain_fog": "mountain"}

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    if name == "tent_slash": return slash_frame(t, p)
    if name == "footprints": return footprints_frame(t, p, "snow1")
    if name == "footprints_down": return footprints_frame(t, p, "snow2", 0.38)
    if name == "hikers": return hikers_frame(t, p)
    if name == "survivor": return hikers_frame(t, p, True)
    if name == "cedar": return cedar_frame(t, p)
    if name == "xray": return xray_frame(t, p)
    if name == "geiger": return geiger_frame(t, p)
    if name == "file": return file_frame(t, p)
    if name == "avalanche": return avalanche_frame(t, p)
    if name == "tent_glow": return tent_glow_frame(t, p)
    if name == "end_card": return end_frame(t, p)
    if name == "title_1959":
        img = cam(BG["mountain"], p, (1.3, 1.45, 0, 0)).filter(ImageFilter.GaussianBlur(5))
        img = to_img(np.asarray(img, float) * 0.5); fog(img, t)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        yr = 1900 + int(59 * ease(min(1, p / 0.45)))
        jx = (8 * math.sin(t * 50)) if p < 0.45 else 0
        text_c(d, 380, str(yr), F_BIG, (240, 240, 245, 255), x=W / 2 + jx)
        if p > 0.4: text_c(d, 770, "URSS · MONTES URALES", F_SM, RED + (255,))
        paste_glow(img, lay, 26); draw_snow(img, t, 0.8)
        return img
    if name in MODES:
        if name in CENTER: img = cam_at(BG[SRC.get(name, name)], p, *CENTER[name])
        else: img = cam(BG[SRC.get(name, name)], p, MODES[name])
        if name == "searchers":
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            for k, (ox, sp) in enumerate([(150, 0.9), (950, 1.3), (520, 0.7)]):
                ang = math.pi * 1.5 + 0.5 * math.sin(t * sp + k * 2)
                tip = (ox + 1400 * math.cos(ang - 0.9), H + 1400 * math.sin(ang - 0.9))
                d.polygon([(ox, H + 40), (tip[0] - 160, tip[1]), (tip[0] + 160, tip[1])], fill=(255, 245, 210, 55))
            lay = lay.filter(ImageFilter.GaussianBlur(30)); img.paste(lay, (0, 0), lay)
        if name == "mountain_fog":
            fog(img, t, 1.6)
            if p > 0.35:
                d = ImageDraw.Draw(img); text_c(d, 330, "¿RESUELTO?", F_MED, RED, 6)
        if name == "mountain" and p > 0.3:
            d = ImageDraw.Draw(img, "RGBA"); a = int(255 * min(1, (p - 0.3) / 0.2))
            text_c(d, 300, "KHOLAT SYAKHL", F_MED, (255, 255, 255, a), 6)
            text_c(d, 410, "«MONTAÑA MUERTA» EN MANSI", F_SM, RED + (a,), 4)
        if name == "tent_night": fog(img, t, 0.7)
        draw_snow(img, t, 1.0 if name != "ravine" else 0.5, big=name == "tent_night")
        return img
    raise KeyError(name)

SHOTS = shot_timeline()
CAPS = caption_timeline()
HITS = hits()

def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, s = cur[-1]
    age = t - a
    sc = 0.82 + 0.18 * min(1, age / 0.11) + 0.04 * math.sin(min(1, age / 0.11) * math.pi)
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    parts, hl = [], False
    for w in s.split(" "):
        if w.startswith("*") or w.startswith("¿*"): hl = True
        parts.append((w.replace("*", ""), hl))
        if "*" in w[1:] and not (w.startswith("*") and w.count("*") == 1): hl = False
    full = " ".join(p[0] for p in parts)
    font = F_CAP
    while d.textlength(full, font=font) > W - 90: font = ImageFont.truetype(FONT, font.size - 6)
    x = (W - d.textlength(full, font=font)) / 2
    for i, (wd, h) in enumerate(parts):
        txt = wd + (" " if i < len(parts) - 1 else "")
        d.text((x, 60), txt, font=font, fill=(RED if h else (255, 255, 255)) + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255))
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
    img = shot_frame(name, t, a, b).convert("RGB")
    XF = 0.16
    if i + 1 < len(SHOTS) and t > b - XF:
        a2, b2, n2 = SHOTS[i + 1]
        img = Image.blend(img, shot_frame(n2, t, a2, b2).convert("RGB"), (t - (b - XF)) / XF)
    arr = np.asarray(img, float)
    lum = arr.mean(2, keepdims=True); arr = lum + (arr - lum) * 0.72      # desaturado frío
    arr = arr * VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.22: arr = arr + (1 - u / 0.22) * np.array([150, 120, 120])
    if (fi * 7919) % 97 < 3: arr *= 0.86                                   # parpadeo de película
    g = GRAIN[fi % 4]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    arr = (arr - 128) * 1.08 + 128
    if t < 0.2: arr *= t / 0.2
    if t > TOTAL - 0.6: arr *= max(0, (TOTAL - t) / 0.6)
    img = to_img(arr)
    cap = caption_layer(t)
    if cap is not None and t < TOTAL - 0.25:
        img.paste(cap, (0, 1250), cap)
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
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]]:
            frame(tt, 0).save(os.path.join(HERE, "stills", f"still_{tt:05.1f}.jpg"), quality=85)
    else:
        for si in [int(x) for x in sys.argv[2:]]:
            render_scene(si, os.path.join(HERE, f"scene_{si:02}.mp4")); print("scene", si, flush=True)
