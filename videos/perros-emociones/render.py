import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, TOTAL, caption_timeline, shot_timeline

W, H, FPS = 1080, 1920, 30
BW, BH = 1300, 2310          # fondos más grandes para mover la cámara
rng = np.random.default_rng(3)
FONT = os.environ.get("FONT", "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf")
FONT2 = os.environ.get("FONT2", "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf")
F_CAP = ImageFont.truetype(FONT, 100)
F_BIG = ImageFont.truetype(FONT, 300)
F_MED = ImageFont.truetype(FONT, 88)
F_SM = ImageFont.truetype(FONT2, 50)
F_XS = ImageFont.truetype(FONT2, 40)
GOLD = (255, 200, 90); TEAL = (90, 235, 215); RED = (255, 85, 75); PINK = (255, 120, 170); SKY = (120, 190, 255)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- utilidades
def grad(c1, c2, w=BW, h=BH, power=1.0):
    y = (np.linspace(0, 1, h) ** power)[:, None, None]
    a = np.array(c1, float); b = np.array(c2, float)
    return np.broadcast_to(a + (b - a) * y, (h, w, 3)).copy()

def radial(w, h, cx, cy, r, col, k=1.0):
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))
    return m[..., None] * np.array(col, float) * k

def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def noise_tex(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((h // scale + 2, w // scale + 2))
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, float) / 255

def ease(p): p = min(max(p, 0.0), 1.0); return p * p * (3 - 2 * p)

def catmull(pts, n=10, closed=True):
    P = list(pts); out = []
    m = len(P) if closed else len(P) - 1
    for i in range(m):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % len(P)], P[(i + 2) % len(P)]
        for k in range(n):
            u = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u * u
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u ** 3) for j in range(2)))
    return out

def tf(pts, x, y, s, flip=False):
    return [((-px if flip else px) * s + x, py * s + y) for px, py in pts]

def paste_glow(img, lay, r=20, k=1.0):
    g = lay.filter(ImageFilter.GaussianBlur(r))
    if k != 1.0:
        a = np.asarray(g, float); a[..., 3] *= k; g = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)

def text_c(d, y, s, font, fill, stroke=0, sc=(0, 0, 0), x=None):
    w = d.textlength(s, font=font)
    d.text(((W - w) / 2 if x is None else x - w / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)

def cam(bg, p, mode):
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * (p * p * (3 - 2 * p) * 0.5 + p * 0.5)
    cw, ch = BW / z, BH / z
    cx = BW / 2 + dx * (p - 0.5) * (BW - cw); cy = BH / 2 + dy * (p - 0.5) * (BH - ch)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def cam_pt(p, mode, x, y):
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * (p * p * (3 - 2 * p) * 0.5 + p * 0.5)
    cw, ch = BW / z, BH / z
    cx = BW / 2 + dx * (p - 0.5) * (BW - cw); cy = BH / 2 + dy * (p - 0.5) * (BH - ch)
    return (x - (cx - cw / 2)) * W / cw, (y - (cy - ch / 2)) * H / ch

# ---------------------------------------------------------------- siluetas (coordenadas 0..1000, mirando a la derecha)
DOG_HEAD = [(380, 230), (480, 200), (580, 215), (660, 290), (760, 320), (860, 340), (920, 350), (950, 385), (940, 425),
            (900, 440), (880, 480), (820, 505), (720, 510), (760, 540), (700, 570), (620, 580), (560, 600), (520, 700),
            (540, 850), (560, 1000), (180, 1000), (200, 800), (250, 560), (290, 380), (320, 280)]
DOG_HEAD_EAR = [(380, 270), (410, 150), (455, 45), (490, 40), (530, 140), (570, 240), (480, 280)]
DOG_SIT = [(845, 175), (852, 215), (815, 240), (760, 258), (715, 280), (655, 315), (640, 390), (662, 490), (668, 620),
           (672, 900), (706, 955), (702, 992), (600, 992), (606, 880), (598, 660), (560, 690), (510, 760), (500, 880),
           (530, 950), (540, 992), (380, 992), (250, 985), (215, 900), (228, 760), (275, 600), (350, 440), (425, 335),
           (470, 250), (490, 150), (560, 95), (650, 98), (710, 135), (800, 150)]
DOG_SIT_EAR = [(535, 150), (555, 80), (580, 15), (605, 20), (630, 80), (655, 140), (595, 165)]
DOG_WALK = [(905, 245), (905, 290), (860, 310), (790, 320), (745, 345), (720, 420), (705, 520), (715, 760), (735, 900),
            (760, 985), (690, 990), (650, 880), (620, 640), (560, 650), (450, 655), (360, 650), (320, 760), (295, 900),
            (310, 990), (240, 990), (220, 880), (215, 700), (190, 600), (150, 520), (90, 470), (110, 440), (190, 480),
            (230, 450), (360, 430), (520, 420), (610, 370), (650, 240), (700, 175), (770, 170), (820, 205)]
DOG_WALK_EAR = [(680, 215), (700, 140), (720, 80), (745, 85), (765, 150), (780, 215), (730, 230)]
HUMAN_STAND = [(500, 0), (560, 20), (585, 85), (575, 150), (545, 185), (545, 215), (640, 245), (690, 300), (700, 560),
               (665, 570), (650, 330), (640, 560), (620, 980), (560, 990), (535, 640), (500, 630), (465, 640), (440, 990),
               (380, 980), (360, 560), (350, 330), (335, 570), (300, 560), (310, 300), (360, 245), (455, 215), (455, 185),
               (425, 150), (415, 85), (440, 20)]
HUMAN_BUST = [(500, 80), (600, 110), (650, 230), (640, 380), (600, 470), (575, 530), (580, 600), (760, 660), (880, 760),
              (930, 1000), (70, 1000), (120, 760), (240, 660), (420, 600), (425, 530), (400, 470), (360, 380), (350, 230),
              (400, 110)]
HUMAN_SIT = [(500, 0), (560, 20), (585, 85), (575, 150), (545, 185), (545, 215), (640, 250), (680, 330), (690, 560),
             (660, 590), (780, 600), (830, 650), (830, 990), (710, 990), (710, 720), (500, 720), (330, 700), (320, 330),
             (360, 250), (455, 215), (455, 185), (425, 150), (415, 85), (440, 20)]

def silhouette(d, shape, x, y, s, fill, flip=False, ear=None, ear_fill=None):
    d.polygon(tf(catmull(shape, 8), x, y, s, flip), fill=fill)
    if ear is not None:
        d.polygon(tf(catmull(ear, 8), x, y, s, flip), fill=ear_fill or fill)

def rim_sil(img, shape, x, y, s, rim, body=(6, 6, 12), flip=False, ear=None, glow=26, off=(-6, -4)):
    """silueta oscura con luz de contorno (rim light) de color"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    silhouette(d, shape, x, y, s, rim + (255,), flip, ear)
    g = lay.filter(ImageFilter.GaussianBlur(glow))
    img.paste(g, (0, 0), g)
    img.paste(lay, (0, 0), lay)
    body_l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); db = ImageDraw.Draw(body_l)
    silhouette(db, shape, x + off[0] * (-1 if flip else 1), y + off[1], s, body + (255,), flip, ear,
               tuple(max(0, c - 4) for c in body) + (255,))
    img.paste(body_l, (0, 0), body_l)

# ---------------------------------------------------------------- partículas de olor
PART = rng.random((400, 6))
def scent(d, t, n, src, dst, col, spread=220, speed=0.45, size=1.0, curl=1.0, alpha=230):
    (sx, sy), (tx, ty) = src, dst
    for i in range(n):
        u0, v0, s0, ph, sp, w0 = PART[i]
        u = (u0 + t * speed * (0.6 + sp * 0.8)) % 1.0
        e = u ** 1.4
        off = (v0 - 0.5) * spread * (1 - e) * 2
        nx, ny = -(ty - sy), (tx - sx); L = math.hypot(nx, ny) + 1e-6; nx /= L; ny /= L
        wob = math.sin(u * 9 + ph * 6 + t * 2) * 45 * curl * (1 - e)
        x = sx + (tx - sx) * e + nx * (off + wob); y = sy + (ty - sy) * e + ny * (off + wob)
        r = (3 + s0 * 9) * size * (0.4 + 0.6 * (1 - e))
        a = int(alpha * min(1, u * 5) * min(1, (1 - u) * 6))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))

BOKEH = rng.random((40, 5))
def bokeh(img, t, col, n=26, k=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        x, y, s, sp, ph = BOKEH[i]
        cx = x * W + 40 * math.sin(t * 0.3 + ph * 6); cy = (y * H - t * (10 + sp * 25)) % H
        r = 18 + s * 70
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (int((25 + s * 45) * k),))
    lay = lay.filter(ImageFilter.GaussianBlur(10)); img.paste(lay, (0, 0), lay)

# ---------------------------------------------------------------- fondos estáticos
def bg_nose():
    yy, xx = np.mgrid[0:BH, 0:BW].astype(float)
    fur = grad((120, 78, 42), (70, 42, 22))
    tex = noise_tex(BW, BH, 3, 1) * 0.45 + noise_tex(BW, BH, 30, 2) * 0.55
    # pelo: rayas orientadas que salen del centro
    r0 = np.random.default_rng(5).random((BH // 60 + 2, BW // 4 + 2))
    strands = 0.7 + 0.3 * np.asarray(Image.fromarray((r0 * 255).astype(np.uint8)).resize((BW, BH), Image.BICUBIC), float) / 255
    fur *= (0.55 + 0.6 * tex)[..., None] * strands[..., None]
    cx, cy = 650, 1050
    # forma de la trufa: dos lóbulos
    nx, ny = (xx - cx) / 470, (yy - cy) / 330
    shape = (np.abs(nx) ** 2.2 + np.abs(ny + 0.15 * nx * nx) ** 2.0) < 1
    tile = noise_tex(BW, BH, 14, 4)
    cells = np.abs(np.sin(xx / 17 + tile * 4) * np.sin(yy / 17 + tile * 4))
    nose = np.array([28, 22, 24])[None, None, :] * (0.55 + 0.9 * cells)[..., None]
    nose += np.exp(-(((xx - cx + 120) / 190) ** 2 + ((yy - cy + 170) / 70) ** 2))[..., None] * 120
    nose += np.exp(-(((xx - cx - 160) / 120) ** 2 + ((yy - cy + 150) / 50) ** 2))[..., None] * 70
    # fosas nasales en forma de coma
    for sgn in (-1, 1):
        ex, ey = cx + sgn * 190, cy + 60
        ca, sa = math.cos(sgn * 0.5), math.sin(sgn * 0.5)
        u = ((xx - ex) * ca + (yy - ey) * sa); v = (-(xx - ex) * sa + (yy - ey) * ca)
        hole = (u / 105) ** 2 + (v / 48) ** 2 < 1
        # hendidura que baja hacia fuera
        sx, sy = ex + sgn * 120, ey + 70
        u2 = ((xx - sx) * math.cos(sgn * 0.9) + (yy - sy) * math.sin(sgn * 0.9)); v2 = (-(xx - sx) * math.sin(sgn * 0.9) + (yy - sy) * math.cos(sgn * 0.9))
        hole |= (u2 / 95) ** 2 + (v2 / 13) ** 2 < 1
        rim = (u / 125) ** 2 + (v / 66) ** 2 < 1
        nose[rim & ~hole] *= 0.6
        nose[hole] = [5, 3, 5]
    groove = np.exp(-((xx - cx) / 10) ** 2) * (yy > cy) * 0.8
    nose *= (1 - groove)[..., None]
    a = fur.copy(); a[shape] = nose[shape]
    edge = np.clip(1 - np.abs(np.abs(nx) ** 2.2 + np.abs(ny + 0.15 * nx * nx) ** 2.0 - 1) * 12, 0, 1)
    a *= (1 - 0.6 * edge)[..., None]
    a *= np.clip(1.25 - np.sqrt(((xx - cx) / 900) ** 2 + ((yy - cy) / 1100) ** 2), 0.2, 1)[..., None]
    return to_img(a)

def bg_night(c1=(6, 8, 22), c2=(28, 16, 44), glowc=(80, 40, 120), gx=650, gy=900):
    return to_img(grad(c1, c2) + radial(BW, BH, gx, gy, 700, glowc, 0.6))

def bg_sunset():
    a = grad((40, 20, 70), (255, 150, 70), power=1.6)
    a += radial(BW, BH, 650, 1450, 300, (255, 230, 150), 1.2) + radial(BW, BH, 650, 1450, 800, (255, 120, 60), 0.5)
    img = to_img(a); d = ImageDraw.Draw(img)
    d.ellipse([480, 1280, 820, 1620], fill=(255, 235, 170))
    img = img.filter(ImageFilter.GaussianBlur(2)); d = ImageDraw.Draw(img)
    pts = [(0, 1560)] + [(x, 1560 - 70 * math.sin(x * 0.004 + 1) - 25 * math.sin(x * 0.017)) for x in range(0, BW + 20, 20)] + [(BW, BH), (0, BH)]
    d.polygon(pts, fill=(60, 26, 40))
    pts = [(0, 1640)] + [(x, 1640 - 40 * math.sin(x * 0.003 + 4)) for x in range(0, BW + 20, 20)] + [(BW, BH), (0, BH)]
    d.polygon(pts, fill=(22, 10, 18))
    # silueta: persona sentada abrazando al perro
    silhouette(d, HUMAN_SIT, 330, 1100, 0.52, (18, 8, 14))
    silhouette(d, DOG_SIT, 560, 1190, 0.46, (18, 8, 14), ear=DOG_SIT_EAR)
    d.line([(560 + 250 * 0.46, 1190 + 950 * 0.46), (560 + 90 * 0.46, 1190 + 990 * 0.46), (560 + 30 * 0.46, 1190 + 940 * 0.46)], fill=(18, 8, 14), width=14)
    return img

def eye_img(kind):
    """ojo en primer plano: 'dog' (marrón) o 'human' (claro con esclerótica)"""
    w, h = 900, 900
    yy, xx = np.mgrid[0:h, 0:w].astype(float); cx, cy = 450, 450
    if kind == "dog":
        a = grad((110, 70, 38), (70, 42, 22), w, h) * (0.6 + 0.6 * noise_tex(w, h, 4, 7))[..., None]
        ang = np.arctan2(yy - cy, xx - cx)
        a *= (0.8 + 0.2 * np.sin(ang * 90 + noise_tex(w, h, 30, 8) * 8))[..., None]
        lid = ((xx - cx) / 330) ** 2 + ((yy - cy) / 250) ** 2 < 1
        a[lid] = [20, 12, 8]
        R, irisc = 230, np.array([150, 85, 30])
    else:
        a = grad((225, 170, 140), (190, 130, 105), w, h) * (0.9 + 0.15 * noise_tex(w, h, 6, 9))[..., None]
        lid = (np.abs((xx - cx) / 360) ** 1.6 + np.abs((yy - cy) / (210 * (1 - 0.35 * ((xx - cx) / 360) ** 2))) ** 2) < 1
        a[lid] = [235, 232, 228]
        a[lid] *= (1 - 0.25 * np.exp(-((yy[lid] - cy + 210) / 70) ** 2))[..., None]
        R, irisc = 165, np.array([70, 130, 160])
    d2 = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2); ang = np.arctan2(yy - cy, xx - cx)
    iris = (d2 < R) & lid
    streak = 0.6 + 0.4 * np.sin(ang * 60 + noise_tex(w, h, 25, 10) * 8) ** 2
    ic = irisc * (1.25 - d2 / R * 0.6)[..., None] * streak[..., None]
    a[iris] = ic[iris]
    pupil = (d2 < R * 0.45) & lid
    a[pupil] = [6, 5, 6]
    a += np.exp(-(((xx - cx + R * 0.4) ** 2 + (yy - cy + R * 0.42) ** 2) / (R * R * 0.012)))[..., None] * 255 * lid[..., None]
    a += np.exp(-(((xx - cx - R * 0.3) ** 2 + (yy - cy - R * 0.35) ** 2) / (R * R * 0.004)))[..., None] * 160 * lid[..., None]
    return to_img(a)

def bg_cross():
    """corte lateral de la cabeza del perro con las vías del aire (dibujado a BW x BH)"""
    img = to_img(grad((8, 14, 30), (20, 30, 55)) + radial(BW, BH, 700, 900, 650, (40, 70, 120), 0.7))
    d = ImageDraw.Draw(img, "RGBA")
    for gx in range(0, BW, 60): d.line([gx, 0, gx, BH], fill=(80, 120, 180, 22))
    for gy in range(0, BH, 60): d.line([0, gy, BW, gy], fill=(80, 120, 180, 22))
    pts = tf(catmull(DOG_HEAD, 10), -20, 380, 1.32)
    d.polygon(pts, fill=(30, 50, 85, 255), outline=(150, 200, 255, 255))
    d.line(pts + [pts[0]], fill=(150, 200, 255, 255), width=5)
    # zona olfativa (laberinto de cornetes) al fondo de la nariz
    for k in range(9):
        y0 = 720 + k * 26
        d.arc([700 - k * 6, y0 - 40, 980 - k * 4, y0 + 40], 180, 360, fill=(90, 235, 215, 160), width=6)
    return img

# ---------------------------------------------------------------- animaciones
def ecg(img, t, beats, color=(255, 90, 90), y0=900):
    d = ImageDraw.Draw(img, "RGBA")
    for gy in range(0, H, 90): d.line([0, gy, W, gy], fill=(120, 40, 50, 50))
    for gx in range(0, W, 90): d.line([gx, 0, gx, H], fill=(120, 40, 50, 50))
    pts = []; win = 3.0
    for i in range(0, W, 3):
        tt = t - win + win * i / W; v = 0
        for bt in beats:
            u = tt - bt
            if -0.2 < u < 0.5:
                v += 260 * math.exp(-(u / 0.018) ** 2) - 90 * math.exp(-((u - 0.05) / 0.025) ** 2) + 50 * math.exp(-((u - 0.25) / 0.06) ** 2)
        pts.append((i, y0 - v))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.line(pts, fill=color + (255,), width=9, joint="curve")
    paste_glow(img, lay, 14)
    last = [b for b in beats if b <= t]
    bpm = int(60 / max(0.25, (last[-1] - last[-2]))) if len(last) > 1 else 80
    text_c(d, 300, f"{bpm} LPM", F_MED, color)
    text_c(d, 410, "PULSO DEL PERRO", F_SM, (255, 200, 200))

def heart(d, cx, cy, s, fill):
    pts = []
    for k in range(60):
        u = k / 60 * 2 * math.pi
        x = 16 * math.sin(u) ** 3; y = -(13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u))
        pts.append((cx + x * s, cy + y * s))
    d.polygon(pts, fill=fill)

def counter(img, p, target, unit, sub, color, fmt="{:d}", y=330):
    v = target * min(1, (p / 0.55)) ** 0.5
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    text_c(dl, y, fmt.format(int(round(v))), F_BIG, color + (255,))
    text_c(dl, y + 350, unit, F_MED, WHITE + (255,))
    paste_glow(img, lay, 30)
    d = ImageDraw.Draw(img, "RGBA")
    if sub: text_c(d, y + 470, sub, F_SM, (225, 225, 240))

def molecule(d, cx, cy, R, rot, col, a=230, wdt=6):
    pts = [(cx + R * math.cos(rot + k * math.pi / 3), cy + R * math.sin(rot + k * math.pi / 3)) for k in range(6)]
    d.line(pts + [pts[0]], fill=col + (a,), width=wdt)
    q = pts[1]; e = (q[0] + R * 0.9 * math.cos(rot + 0.5), q[1] + R * 0.9 * math.sin(rot + 0.5))
    d.line([q, e], fill=col + (a,), width=wdt)
    for qq in pts + [e]: d.ellipse([qq[0] - wdt * 1.4, qq[1] - wdt * 1.4, qq[0] + wdt * 1.4, qq[1] + wdt * 1.4], fill=col + (255,))

def sweat_drop(d, x, y, s, col):
    pts = [(x, y - 1.6 * s)] + [(x + s * math.cos(u), y + s * math.sin(u)) for u in np.linspace(-0.35, math.pi + 0.35, 24)]
    d.polygon(pts, fill=col)

def face(d, cx, cy, R, happy, col, wdt=12):
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=col, width=wdt)
    ey = cy - R * 0.2
    for s in (-1, 1):
        ex = cx + s * R * 0.36
        d.ellipse([ex - R * 0.08, ey - R * 0.1, ex + R * 0.08, ey + R * 0.1], fill=col)
        if not happy:  # cejas fruncidas
            d.line([ex - s * R * 0.2, ey - R * 0.18, ex + s * R * 0.14, ey - R * 0.34], fill=col, width=wdt)
    if happy: d.arc([cx - R * 0.5, cy - R * 0.2, cx + R * 0.5, cy + R * 0.6], 20, 160, fill=col, width=wdt)
    else: d.arc([cx - R * 0.45, cy + R * 0.3, cx + R * 0.45, cy + R * 0.9], 200, 340, fill=col, width=wdt)

def wave_line(d, x0, x1, y, amp, t, col, freq=0.05, wdt=7, env=True):
    pts = []
    for x in range(int(x0), int(x1), 4):
        u = (x - x0) / (x1 - x0)
        e = math.sin(u * math.pi) if env else 1
        a = amp * e * (0.6 + 0.4 * math.sin(t * 7 + x * 0.013)) * (0.5 + 0.5 * abs(math.sin(t * 3.1 + x * 0.004)))
        pts.append((x, y + a * math.sin(x * freq - t * 14)))
    d.line(pts, fill=col, width=wdt, joint="curve")

# ---------------------------------------------------------------- construir fondos
print("construyendo fondos", flush=True)
BG = {
    "nose": bg_nose(),
    "night": bg_night(),
    "red": bg_night((20, 4, 8), (60, 10, 20), (150, 30, 30)),
    "warm": bg_night((40, 20, 20), (120, 60, 30), (255, 170, 80), 650, 700),
    "teal": bg_night((4, 14, 20), (8, 30, 44), (20, 110, 120)),
    "pink": bg_night((26, 6, 22), (70, 20, 50), (200, 70, 130)),
    "blue": bg_night((4, 8, 24), (14, 22, 60), (50, 80, 200)),
    "sunset": bg_sunset(),
}
EYE_DOG = eye_img("dog"); EYE_HUM = eye_img("human")
VIG = None
def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    return np.clip(1.15 - r ** 2 * 0.6, 0.25, 1)[..., None]
VIG = vignette()
GRAIN = [(rng.standard_normal((H // 2, W // 2)) * 6) for _ in range(4)]
MOL = rng.random((26, 5))
DOTS = rng.random((1500, 3))

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    if name in ("nose_macro", "scent_in"):
        sniff = 0.0
        if name == "scent_in": sniff = 0.012 * max(0, math.sin(t * 2 * math.pi * 5)) * (math.sin(t * 2.2) > 0)
        mode = (1.0, 1.12, 0, -0.2) if name == "nose_macro" else (1.18 + sniff, 1.45 + sniff, 0, 0.3)
        img = cam(BG["nose"], p, mode)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for sgn in (-1, 1):
            tx, ny = cam_pt(p, mode, 650 + sgn * 190, 1050 + 60)
            n = 70 if name == "nose_macro" else 140
            scent(d, t + sgn, n, (W / 2 + sgn * 520, -150 if sgn < 0 else H + 100), (tx, ny), TEAL, spread=420,
                  speed=0.35 if name == "nose_macro" else 0.75, size=1.2)
        paste_glow(img, lay, 12, 1.2)
        return img
    if name == "human_stress":
        img = cam(BG["red"], p, (1.0, 1.1, 0, 0))
        pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.6)
        rim_sil(img, HUMAN_BUST, 90 - 30 * p, 360, 0.9, (255, 80 + int(40 * pulse), 60), body=(14, 4, 6), glow=34 + 14 * pulse)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i in range(90):
            u0, v0, s0, ph, sp, _ = PART[i]
            u = (u0 + t * (0.25 + sp * 0.3)) % 1
            x = 540 + (v0 - 0.5) * 760 + 50 * math.sin(u * 8 + ph * 6); y = 1250 - u * 1100
            r = 4 + s0 * 10
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 140 + int(60 * s0), 70, int(220 * min(1, u * 4) * (1 - u))))
        paste_glow(img, lay, 10)
        return img
    if name == "molecules":
        img = cam(BG["red"], p, (1.1, 1.2, 0, 0.3))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i, (mx, my, ms, sp, ph) in enumerate(MOL):
            cx = mx * W + 60 * math.sin(t * 0.7 + ph * 6); cy = (my * 1300 + 50 - t * (30 + sp * 60)) % 1300 + 50
            molecule(d, cx, cy, 30 + ms * 60, t * (0.4 + sp) + ph * 6, (255, 150, 70) if i % 3 else (255, 210, 120), wdt=int(4 + ms * 5))
        paste_glow(img, lay, 18)
        return img
    if name == "dog_sniff":
        img = cam(BG["teal"], p, (1.0, 1.08, 0, 0))
        x0, s0 = -160 + 40 * ease(p), 0.92
        rim_sil(img, DOG_HEAD, x0, 260, s0, TEAL, body=(6, 14, 18), ear=DOG_HEAD_EAR, glow=30)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        nz = (x0 + 945 * s0, 260 + 395 * s0)
        scent(d, t, 120, (W + 120, 300), nz, TEAL, spread=420, speed=0.55, size=1.1)
        scent(d, t + 0.37, 40, (W + 120, 1150), nz, (255, 140, 80), spread=300, speed=0.5, size=1.2)
        paste_glow(img, lay, 10)
        return img
    if name == "stat_300":
        img = cam(BG["teal"], p, (1.0, 1.1, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        k = int(len(DOTS) * min(1, p / 0.6))
        for (x, y, s) in DOTS[:k]:
            r = 2 + s * 4
            d.ellipse([x * W - r, y * H - r, x * W + r, y * H + r], fill=TEAL + (int(60 + s * 90),))
        counter(img, p, 300, "MILLONES", "DE RECEPTORES OLFATIVOS", TEAL)
        return img
    if name == "stat_6":
        img = cam(BG["teal"], p, (1.1, 1.0, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        text_c(d, 250, "RECEPTORES OLFATIVOS", F_SM, (200, 240, 235))
        g = ease(p / 0.5)
        for i, (lab, val, col) in enumerate([("PERRO", 300, TEAL), ("HUMANO", 6, (255, 190, 120))]):
            y = 420 + i * 330
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            dl.text((110, y), lab, font=F_SM, fill=WHITE + (255,))
            wbar = max(14, int(860 * val / 300 * g))
            dl.rounded_rectangle([110, y + 80, 110 + wbar, y + 190], 30, fill=col + (255,))
            dl.text((110 + wbar + 20 if val < 100 else 140, y + 92), f"{int(round(val * g))} M", font=F_MED if val < 100 else F_MED,
                    fill=(WHITE if val < 100 else (10, 30, 30)) + (255,))
            paste_glow(img, lay, 18, 0.8)
        if p > 0.55:
            text_c(d, 1070, "×50", F_BIG.font_variant(size=200), TEAL + (int(255 * min(1, (p - 0.55) / 0.15)),))
        return img
    if name == "airflow":
        img = cam(BG["blue"], p, (1.0, 1.06, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for gx in range(0, W, 60): d.line([gx, 0, gx, H], fill=(80, 120, 180, 25))
        for gy in range(0, H, 60): d.line([0, gy, W, gy], fill=(80, 120, 180, 25))
        x0, y0, sc = -70, 260, 1.05
        pts = tf(catmull(DOG_HEAD, 10), x0, y0, sc)
        d.polygon(pts, fill=(25, 45, 85, 230))
        d.polygon(tf(catmull(DOG_HEAD_EAR, 8), x0, y0, sc), fill=(25, 45, 85, 230))
        d.line(pts + [pts[0]], fill=(150, 200, 255, 255), width=5)
        P = lambda x, y: (x0 + x * sc, y0 + y * sc)
        for k in range(8):   # cornetes de la zona olfativa
            cxk, cyk = P(560 + k * 12, 300 + k * 13)
            d.arc([cxk - 130, cyk - 30, cxk + 90, cyk + 30], 180, 360, fill=TEAL + (170,), width=6)
        UP = catmull([P(*q) for q in [(935, 400), (830, 375), (720, 350), (600, 330), (560, 330)]], 12, closed=False)
        DN = catmull([P(*q) for q in [(935, 410), (800, 445), (650, 480), (520, 600), (420, 800), (370, 1000), (360, 1010)]], 12, closed=False)
        def path(u, upper):
            L = UP if upper else DN
            return L[min(len(L) - 1, int(u * (len(L) - 1)))]
        for upper, col in ((False, SKY), (True, TEAL)):
            g = ease((p - (0.05 if not upper else 0.3)) / 0.35)
            pts = [path(u / 40 * g, upper) for u in range(41)]
            if g > 0.01: d.line(pts, fill=col + (90,), width=34, joint="curve")
            for j in range(14):
                u = ((j / 14) + t * 0.5) % 1
                if u > g: continue
                x, y = path(u, upper)
                d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=col + (255,))
        if p > 0.3: text_c(d, 380, "OLER", F_MED, TEAL + (int(255 * min(1, (p - 0.3) * 5)),), x=820)
        if p > 0.1: text_c(d, 960, "RESPIRAR", F_MED.font_variant(size=70), SKY + (int(255 * min(1, (p - 0.1) * 5)),), x=800)
        paste_glow(img, lay, 14)
        return img
    if name == "receptors":
        img = cam(BG["teal"], p, (1.0, 1.15, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i in range(26):   # cilios ondulantes
            x0 = 30 + i * 40
            pts = [(x0 + 30 * math.sin(t * 2 + i + y * 0.01), 1150 - y) for y in range(0, 700, 20)]
            d.line(pts, fill=TEAL + (150,), width=6, joint="curve")
            d.ellipse([x0 - 18, 1130, x0 + 18, 1170], fill=TEAL + (220,))
        for i, (mx, my, ms, sp, ph) in enumerate(MOL[:14]):
            u = (my + t * (0.25 + sp * 0.2)) % 1
            cx = mx * W; cy = u * 1000 - 50
            hit = u > 0.85
            molecule(d, cx, cy, 22 + ms * 22, t + ph * 6, GOLD if hit else (255, 150, 80), a=255, wdt=5)
            if hit: d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], outline=GOLD + (200,), width=5)
        paste_glow(img, lay, 16)
        dd = ImageDraw.Draw(img); text_c(dd, 1230 - 1000, "ZONA OLFATIVA", F_SM, (200, 245, 240))
        return img
    if name == "lab_vials":
        img = cam(BG["blue"], p, (1.0, 1.1, 0, -0.2))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        text_c(d, 230, "BELFAST", F_MED, WHITE + (255,)); text_c(d, 340, "QUEEN'S UNIVERSITY · 2022", F_XS, (190, 210, 255, 255))
        for k, (lab, col) in enumerate([("ANTES", SKY), ("DESPUÉS", RED)]):
            x = 250 + k * 420; top = 560
            reveal = ease((p - 0.15 * k) / 0.3)
            d.rounded_rectangle([x - 110, top, x + 110, top + 520], 40, outline=(220, 235, 255, 255), width=8)
            d.rectangle([x - 130, top - 60, x + 130, top], fill=(230, 235, 245, 255))
            lvl = min(top + 470, top + 520 - int(380 * reveal))
            d.rounded_rectangle([x - 96, lvl, x + 96, top + 506], 34, fill=col + (150,))
            for j in range(5):
                u = (t * 0.6 + j / 5 + k * 0.3) % 1
                yy = top - 80 - u * 260
                d.ellipse([x - 12 + 30 * math.sin(u * 7 + j), yy - 12, x + 12 + 30 * math.sin(u * 7 + j), yy + 12], fill=col + (int(220 * (1 - u)),))
            text_c(d, top + 560, lab, F_SM, col + (255,), x=x)
        paste_glow(img, lay, 18, 0.8)
        return img
    if name == "dog_lineup":
        img = cam(BG["blue"], p, (1.05, 1.15, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        sel = int(p * 4.5) % 4
        for k in range(4):
            x = 20 + k * 260; y = 560
            on = (k == sel)
            col = GOLD if on else (90, 120, 200)
            rim_sil(img, DOG_SIT, x, y, 0.3, col, body=(10, 12, 26), ear=DOG_SIT_EAR, glow=22 if on else 12)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        for k in range(4):   # cada perro frente a 3 muestras, una roja
            x = 70 + k * 260
            for j in range(3):
                c = RED if (j == (k + 1) % 3) else (150, 170, 220)
                dl.rounded_rectangle([x + j * 60, 960, x + j * 60 + 42, 1050], 12, fill=c + (230,))
        paste_glow(img, lay, 12)
        dd = ImageDraw.Draw(img); text_c(dd, 330, "4 PERROS · 3 MUESTRAS", F_SM, (220, 230, 255))
        return img
    if name == "stat_94":
        img = cam(BG["blue"], p, (1.0, 1.1, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        ang = 360 * 0.9375 * ease(p / 0.55)
        d.arc([190, 250, 890, 950], -90, 270, fill=(255, 255, 255, 40), width=34)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.arc([190, 250, 890, 950], -90, -90 + ang, fill=GOLD + (255,), width=34)
        paste_glow(img, lay, 20)
        v = 94 * min(1, (p / 0.55)) ** 0.5
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        text_c(dl, 430, f"{int(round(v))}%", F_BIG.font_variant(size=240), WHITE + (255,))
        paste_glow(img, lay, 24, 0.6)
        text_c(d, 1010, "DE ACIERTOS (675 DE 720)", F_SM, (230, 230, 245))
        return img
    if name == "fear_sweat":
        img = cam(BG["red"], p, (1.2, 1.0, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i in range(14):
            u0, v0, s0, ph, sp, _ = PART[i + 50]
            y = ((u0 * H) + t * (500 + sp * 600)) % (H + 300) - 150
            sweat_drop(d, 80 + v0 * 920, y, 30 + s0 * 50, (255, 120 + int(60 * s0), 110, 200))
        paste_glow(img, lay, 14)
        dd = ImageDraw.Draw(img); text_c(dd, 300, "ITALIA", F_MED, WHITE, 6); text_c(dd, 410, "SUDOR DE MIEDO", F_SM, (255, 190, 190), 4)
        return img
    if name == "heart_fast":
        img = to_img(np.zeros((H, W, 3)) + np.array([14, 3, 6]))
        beats = []; bt = a - 3; iv = 0.75
        while bt < b + 1:
            beats.append(bt); u = ease((bt - a) / (b - a)); iv = 0.75 - 0.37 * u; bt += iv
        ecg(img, t, beats)
        d = ImageDraw.Draw(img, "RGBA")
        last = max([x for x in beats if x <= t] or [a])
        s = 6 + 1.5 * math.exp(-(t - last) * 9)
        heart(d, W / 2, 1100, s, RED + (255,))
        return img
    if name == "dog_owner":
        img = cam(BG["warm"], p, (1.0, 1.08, 0, 0))
        rim_sil(img, HUMAN_STAND, 360, 220, 1.0, GOLD, body=(30, 14, 10))
        rim_sil(img, DOG_SIT, 30 + 40 * ease(p), 720, 0.5, GOLD, body=(30, 14, 10), ear=DOG_SIT_EAR)
        return img
    if name == "happy_stranger":
        img = cam(BG["warm"], p, (1.0, 1.1, 0.3, 0))
        bokeh(img, t, (255, 220, 140), k=1.4)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        scent(d, t, 70, (1000, 520), (220 + 160 * ease(p) + 400 * 0.45, 620), (255, 230, 120), spread=260, speed=0.5, size=1.2)
        paste_glow(img, lay, 10)
        rim_sil(img, HUMAN_STAND, 600, 260, 0.98, (255, 230, 150), body=(40, 20, 12), flip=False)
        dx = 50 + 230 * ease(p)
        bob = 10 * abs(math.sin(t * 6))
        rim_sil(img, DOG_WALK, dx, 760 - bob, 0.5, (255, 230, 150), body=(40, 20, 12), ear=DOG_WALK_EAR)
        d = ImageDraw.Draw(img, "RGBA")
        text_c(d, 240, "OLOR DE FELICIDAD", F_SM, (255, 240, 200), 4, (60, 30, 10))
        return img
    if name == "brain_voice":
        img = cam(BG["night"], p, (1.0, 1.1, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        cx, cy = 600, 760
        brain = [(cx + 330 * math.cos(u) * (1 + 0.08 * math.sin(5 * u)) - 40 * math.sin(u) ** 2,
                  cy + 210 * math.sin(u) * (1 + 0.07 * math.cos(7 * u))) for u in np.linspace(0, 2 * math.pi, 120)]
        d.polygon(brain, fill=(60, 40, 90, 200), outline=(200, 170, 255, 255))
        d.line(brain + [brain[0]], fill=(200, 170, 255, 255), width=6)
        for k in range(6):   # circunvoluciones
            pts = [(cx - 260 + k * 90 + 25 * math.sin(v * 3 + k), cy - 150 + v * 60) for v in range(6)]
            d.line(pts, fill=(170, 140, 230, 160), width=5, joint="curve")
        d.polygon([(cx + 230, cy + 120), (cx + 330, cy + 170), (cx + 290, cy + 240), (cx + 200, cy + 200)], fill=(80, 55, 110, 220))
        pulse = 0.5 + 0.5 * math.sin(t * 9)
        lit = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dlit = ImageDraw.Draw(lit)
        dlit.ellipse([cx - 210, cy + 10, cx - 30, cy + 150], fill=GOLD + (int(150 + 100 * pulse),))
        lit = lit.filter(ImageFilter.GaussianBlur(25)); lay.alpha_composite(lit)
        wave_line(d, 60, 1020, 1120, 90, t, GOLD + (255,))
        for k in range(3):
            r = ((t * 1.2 + k / 3) % 1) * 300
            d.arc([cx - 120 - r, cy + 80 - r, cx - 120 + r, cy + 80 + r], 0, 360, fill=GOLD + (int(160 * (1 - r / 300)),), width=5)
        paste_glow(img, lay, 18)
        dd = ImageDraw.Draw(img); text_c(dd, 300, "ÁREAS DE LA VOZ", F_SM, (230, 220, 255))
        return img
    if name == "faces":
        img = cam(BG["night"], p, (1.05, 1.0, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        sel = ease((p - 0.25) / 0.3)
        for k, happy in enumerate((True, False)):
            x = 290 + k * 500
            col = tuple(int(c1 + (c2 - c1) * (sel if happy else 0)) for c1, c2 in zip((200, 200, 220), GOLD)) if happy else (200 - int(80 * sel), 200 - int(80 * sel), 220 - int(80 * sel))
            face(d, x, 640, 190 + (30 * sel if happy else 0), happy, col + (255,))
        # voz alegre
        wave_line(d, 160, 920, 1080, 70, t, (255, 220, 150, 255), freq=0.06)
        # barra de tiempo mirando cada cara
        for k, frac in enumerate((0.85, 0.35)):
            x = 290 + k * 500
            d.rounded_rectangle([x - 150, 880, x + 150, 910], 15, outline=(255, 255, 255, 120), width=3)
            d.rounded_rectangle([x - 150, 880, x - 150 + int(300 * frac * ease(p / 0.8)), 910], 15, fill=(GOLD if k == 0 else (150, 150, 180)) + (255,))
        paste_glow(img, lay, 16, 0.8)
        dd = ImageDraw.Draw(img); text_c(dd, 260, "VOZ ALEGRE → CARA ALEGRE", F_SM, (240, 230, 200))
        return img
    if name == "gaze":
        img = cam(BG["pink"], p, (1.0, 1.06, 0, 0))
        z = 1 + 0.08 * p
        e1 = EYE_DOG.resize((int(560 * z), int(560 * z)))
        e2 = EYE_HUM.resize((int(560 * z), int(560 * z)))
        m = Image.new("L", e1.size, 0); ImageDraw.Draw(m).ellipse([10, 10, e1.size[0] - 10, e1.size[1] - 10], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(12))
        img.paste(e1, (int(270 - e1.size[0] / 2), int(560 - e1.size[1] / 2)), m)
        img.paste(e2, (int(810 - e2.size[0] / 2), int(1030 - e2.size[1] / 2)), m)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for j in range(8):
            u = (t * 0.6 + j / 8) % 1
            x = 400 + (680 - 400) * u; y = 680 + (910 - 680) * u
            heart(d, x, y, 2.2 + 1.2 * math.sin(u * math.pi), PINK + (int(255 * math.sin(u * math.pi)),))
        paste_glow(img, lay, 14)
        return img
    if name == "oxytocin":
        img = cam(BG["pink"], p, (1.0, 1.12, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i, (mx, my, ms, sp, ph) in enumerate(MOL):
            cx = mx * W + 50 * math.sin(t * 0.7 + ph * 6); cy = (my * 1400 - t * (40 + sp * 80)) % 1400 + 100
            molecule(d, cx, cy, 24 + ms * 40, t * (0.4 + sp) + ph * 6, PINK, a=150, wdt=4)
        beat = math.exp(-((t * 1.3) % 1) * 7)
        for k, x in enumerate((330, 750)):
            heart(d, x, 760, 9 + 2.2 * beat, PINK + (255,))
        d.arc([300, 470, 780, 1050], 200, 340, fill=(255, 200, 225, 220), width=10)
        d.arc([300, 470, 780, 1050], 20, 160, fill=(255, 200, 225, 220), width=10)
        d.polygon([(760, 600), (790, 650), (735, 650)], fill=(255, 200, 225, 255))
        d.polygon([(320, 920), (290, 870), (345, 870)], fill=(255, 200, 225, 255))
        paste_glow(img, lay, 20)
        dd = ImageDraw.Draw(img)
        text_c(dd, 300, "OXITOCINA", F_MED, WHITE, 6, (90, 20, 60))
        text_c(dd, 955, "PERRO", F_SM, (255, 220, 235), x=330); text_c(dd, 955, "TÚ", F_SM, (255, 220, 235), x=750)
        return img
    if name == "hair_cortisol":
        img = cam(BG["night"], p, (1.0, 1.08, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        lvl = ease(p / 0.6) * (0.68 + 0.05 * math.sin(t * 2))
        for k, (lab, col) in enumerate([("PERRO", (200, 140, 70)), ("DUEÑO", (110, 80, 60))]):
            x = 330 + k * 420
            pts = [(x + 26 * math.sin(y * 0.012 + k), y) for y in range(300, 1130, 10)]
            d.line(pts, fill=col + (255,), width=46, joint="curve")
            for y in range(320, 1120, 46):
                xx = x + 26 * math.sin(y * 0.012 + k)
                d.line([(xx - 22, y), (xx + 22, y - 18)], fill=tuple(min(255, c + 40) for c in col) + (200,), width=4)
            # medidor de cortisol
            mx = x + 110
            d.rounded_rectangle([mx, 420, mx + 42, 1060], 21, outline=(255, 255, 255, 180), width=4)
            d.rounded_rectangle([mx + 6, 1054 - int(628 * (lvl + (0.03 if k else 0))), mx + 36, 1054], 16, fill=(255, 170, 70, 255))
            text_c(d, 1150 - 1150 + 210, lab, F_SM, WHITE + (255,), x=x + 40)
        paste_glow(img, lay, 14, 0.7)
        dd = ImageDraw.Draw(img)
        text_c(dd, 120, "SUECIA · CORTISOL EN EL PELO", F_XS, (255, 210, 160))
        return img
    if name in ("sunset_pair", "end_card"):
        if name == "sunset_pair":
            img = cam(BG["sunset"], p, (1.25, 1.05, 0, 0.3))
            bokeh(img, t, (255, 220, 160), k=0.8)
            return img
        img = cam(BG["sunset"], 1.0, (1.25, 1.05 + 0.08 * p, 0, 0.3))
        img = to_img(np.asarray(img, float) * (1 - 0.35 * ease(p / 0.3)))
        d = ImageDraw.Draw(img, "RGBA")
        if p > 0.12:
            al = int(255 * min(1, (p - 0.12) / 0.1))
            text_c(d, 250, "COMENTA", F_MED, WHITE + (al,), 6)
            text_c(d, 360, "TU HISTORIA", F_MED, GOLD + (al,), 6)
            cx = W / 2; yb = 500 + 18 * math.sin(t * 8)
            d.polygon([(cx - 45, yb), (cx + 45, yb), (cx, yb + 60)], fill=GOLD + (al,))
        return img
    raise KeyError(name)

SHOTS = shot_timeline()
CAPS = caption_timeline()
# destellos en las revelaciones (inicio de los planos clave)
HITS = [0.05] + [s[0] for s in SHOTS if s[2] in ("stat_300", "stat_94", "fear_sweat", "gaze", "sunset_pair")]

def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, s = cur[-1]
    age = t - a
    sc = 0.82 + 0.18 * min(1, age / 0.11) + 0.04 * math.sin(min(1, age / 0.11) * math.pi)
    words = s.split(" ")
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    parts, hl = [], False
    for w in words:
        if w.startswith("*") or w.startswith("¿*"): hl = True
        clean = w.replace("*", "")
        parts.append((clean, hl))
        if w.rstrip("…?,.").endswith("*"): hl = False
    full = " ".join(p[0] for p in parts)
    font = F_CAP
    while d.textlength(full, font=font) > W - 90: font = font.font_variant(size=font.size - 6)
    x = (W - d.textlength(full, font=font)) / 2
    for i, (wd, h) in enumerate(parts):
        txt = wd + (" " if i < len(parts) - 1 else "")
        d.text((x, 60), txt, font=font, fill=(GOLD if h else WHITE) + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255))
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
    if i + 1 < len(SHOTS) and t > b - XF:      # fundido rápido al siguiente plano
        a2, b2, n2 = SHOTS[i + 1]
        img = Image.blend(img, shot_frame(n2, t, a2, b2), (t - (b - XF)) / XF)
    arr = np.asarray(img, float) * VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.25: arr = arr + (1 - u / 0.25) * 110
    g = GRAIN[fi % 4]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    arr = (arr - 128) * 1.05 + 128
    if t < 0.2: arr *= t / 0.2
    if t > TOTAL - 0.7: arr *= max(0, (TOTAL - t) / 0.7)
    img = to_img(arr)
    cap = caption_layer(t)
    if cap is not None and t < TOTAL - 0.3:
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
            frame(tt, 0).resize((540, 960)).save(os.path.join(HERE, "stills", f"still_{tt:05.1f}.jpg"), quality=85)
    elif sys.argv[1] == "shots":   # un fotograma a mitad de cada plano
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for (a, b, n) in SHOTS:
            frame((a + b) / 2, 0).resize((360, 640)).save(os.path.join(HERE, "stills", f"{a:05.1f}_{n}.jpg"), quality=80)
    else:
        for si in [int(x) for x in sys.argv[2:]]:
            render_scene(si, os.path.join(HERE, f"scene_{si:02}.mp4")); print("escena", si, flush=True)
