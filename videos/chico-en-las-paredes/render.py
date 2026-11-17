import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, TOTAL, caption_timeline, shot_timeline, scene_start

W, H, FPS = 1080, 1920, 30
BW, BH = 1300, 2310                     # fondos más grandes para mover la cámara
rng = np.random.default_rng(13)
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
if not os.path.exists(MONO): MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_CAP = ImageFont.truetype(FONT, 100)
F_BIG = ImageFont.truetype(FONT, 300)
F_MED = ImageFont.truetype(FONT, 84)
F_SM = ImageFont.truetype(FONT, 50)
F_XS = ImageFont.truetype(FONT, 34)
F_MONO = ImageFont.truetype(MONO, 44)
F_MONO_S = ImageFont.truetype(MONO, 32)
RED = (230, 30, 40); BONE = (235, 228, 210); COLD = (150, 200, 230)

# ---------------------------------------------------------------- utilidades
def grad(c1, c2, w=BW, h=BH, power=1.0):
    y = (np.linspace(0, 1, h) ** power)[:, None, None]
    a = np.array(c1, float); b = np.array(c2, float)
    return np.broadcast_to(a + (b - a) * y, (h, w, 3)).copy()

def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def arr(img): return np.asarray(img, float)

def noise_tex(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((h // scale + 2, w // scale + 2))
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, float) / 255

YY, XX = np.mgrid[0:BH, 0:BW]
def radial(cx, cy, r, w=BW, h=BH):
    yy, xx = (YY, XX) if (w, h) == (BW, BH) else np.mgrid[0:h, 0:w]
    return np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))

def cone(x0, y0, ang, spread, length):
    a = np.arctan2(YY - y0, XX - x0); d = np.sqrt((XX - x0) ** 2 + (YY - y0) ** 2)
    da = np.angle(np.exp(1j * (a - ang)))
    return np.exp(-(da / spread) ** 2) * np.exp(-d / length)

def lit(albedo, light):            # albedo (H,W,3) 0..255, light (H,W) o (H,W,3)
    if light.ndim == 2: light = light[..., None]
    return albedo * light

def grade(a, shadows=(10, 18, 30), k=1.0):   # sombras frías
    lum = a.mean(2, keepdims=True) / 255
    return a + (1 - lum) ** 3 * np.array(shadows) * k

# ---------------------------------------------------------------- habitación en perspectiva
BACK = (380, 780, 920, 1500)   # pared del fondo (x0,y0,x1,y1)
def room(wall=(120, 110, 95), floor=(80, 58, 40), ceil=(90, 85, 75), back=None, seed=1, tatami=False):
    img = Image.new("RGB", (BW, BH)); d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = BACK
    sh = lambda c, k: tuple(int(v * k) for v in c)
    d.polygon([(0, 0), (BW, 0), (x1, y0), (x0, y0)], fill=ceil)
    d.polygon([(0, BH), (BW, BH), (x1, y1), (x0, y1)], fill=floor)
    d.polygon([(0, 0), (x0, y0), (x0, y1), (0, BH)], fill=sh(wall, 0.8))
    d.polygon([(BW, 0), (x1, y0), (x1, y1), (BW, BH)], fill=sh(wall, 0.7))
    d.rectangle([x0, y0, x1, y1], fill=back or wall)
    # tablas o tatami en el suelo (líneas que convergen)
    vx = (x0 + x1) / 2
    n = 9 if not tatami else 5
    for k in range(n + 1):
        xb = -200 + (BW + 400) * k / n; xt = x0 + (x1 - x0) * k / n
        d.line([xt, y1, xb, BH], fill=sh(floor, 0.6), width=3)
    if tatami:
        for k in range(1, 4):
            yk = y1 + (BH - y1) * (k / 4) ** 1.8
            d.line([0, yk, BW, yk], fill=sh(floor, 0.6), width=4)
    # rodapié
    d.line([(x0, y1), (x1, y1)], fill=sh(wall, 0.4), width=6)
    a = arr(img) * (0.85 + 0.3 * noise_tex(BW, BH, 6, seed)[..., None])
    return a


def fridge(open_=True):
    a = room((60, 70, 75), (55, 55, 58), (35, 38, 42), seed=4)
    img = to_img(a); d = ImageDraw.Draw(img)
    fx0, fy0, fx1, fy1 = 470, 760, 830, 1520
    d.rectangle([fx0, fy0, fx1, fy1], fill=(200, 205, 205))
    d.rectangle([fx0 + 20, fy0 + 20, fx1 - 20, fy1 - 20], fill=(235, 240, 240))
    for k, yy in enumerate([980, 1160, 1330]):
        d.line([fx0 + 20, yy, fx1 - 20, yy], fill=(170, 190, 200), width=8)
    items = [(510, 900, 70, 80, (200, 60, 50)), (600, 920, 60, 60, (240, 230, 200)), (720, 880, 50, 100, (60, 120, 70)),
             (520, 1080, 90, 80, (230, 200, 90)), (760, 1100, 40, 60, (90, 60, 160)), (530, 1260, 60, 70, (220, 220, 230)),
             (640, 1240, 110, 90, (190, 120, 60))]
    for x, y, w_, h_, c in items: d.rectangle([x, y, x + w_, y + h_], fill=c)
    # puerta abierta en perspectiva (izquierda)
    d.polygon([(fx0, fy0), (fx0 - 260, fy0 - 120), (fx0 - 260, fy1 + 160), (fx0, fy1)], fill=(170, 175, 178))
    d.polygon([(fx0 - 20, fy0 + 60), (fx0 - 230, fy0 - 20), (fx0 - 230, fy1 + 90), (fx0 - 20, fy1 - 40)], fill=(210, 215, 215))
    a = arr(img)
    inside = np.zeros((BH, BW)); inside[fy0:fy1, fx0:fx1] = 1
    L = 0.05 + inside * 1.0 + cone(650, 1140, math.pi / 2, 0.5, 900) * 1.1 + radial(650, 1140, 500) * 0.4
    out = lit(a, np.stack([L * 0.9, L * 1.0, L * 1.08], 2))
    return out


def hallway(t, p):
    a = room((110, 100, 85), (90, 66, 45), (80, 75, 66), seed=11)
    img = to_img(a); d = ImageDraw.Draw(img)
    for x in (120, 1050):   # puertas laterales
        d.polygon([(x, 900), (x + (130 if x < 600 else 130), 940), (x + 130, 1500), (x, 1620)], fill=(60, 45, 30))
    a = arr(img)
    ang = math.pi / 2 - 0.35 + 0.7 * (0.5 + 0.5 * math.sin(t * 1.3))
    L = 0.03 + cone(650, 2300, -ang, 0.18, 2200) * 1.8
    beam = arr(to_img(np.zeros((BH, BW, 3)))) + cone(650, 2300, -ang, 0.18, 2200)[..., None] * 25
    return lit(a, L) + beam


def cam(bg, p, mode):
    if not isinstance(bg, Image.Image): bg = to_img(bg)
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * (p * p * (3 - 2 * p) * 0.5 + p * 0.5)
    cw, ch = BW / z, BH / z
    cx = BW / 2 + dx * (p - 0.5) * (BW - cw); cy = BH / 2 + dy * (p - 0.5) * (BH - ch)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))


# ================================================================ planos de este vídeo
def text_c(d, y, s, font, fill, stroke=0, sc=(0, 0, 0), w=W):
    tw = d.textlength(s, font=font)
    d.text(((w - tw) / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)

def plaster(seed=1, base=(150, 135, 112)):
    a = np.zeros((BH, BW, 3)) + np.array(base, float)
    tex = noise_tex(BW, BH, 3, seed) * 0.35 + noise_tex(BW, BH, 40, seed + 1) * 0.65
    return a * (0.7 + 0.45 * tex)[..., None]

def cracks(d, seed, x, y, n=5, col=(30, 24, 18), length=500):
    r = np.random.default_rng(seed)
    for _ in range(n):
        px, py, ang = x, y, r.uniform(0, 2 * math.pi)
        for _k in range(int(length / 25)):
            ang += r.normal(0, 0.45); nx, ny = px + 25 * math.cos(ang), py + 25 * math.sin(ang)
            d.line([px, py, nx, ny], fill=col, width=int(r.uniform(2, 6))); px, py = nx, ny

def wall_close(seed=3, hole=False):
    a = plaster(seed)
    img = to_img(a); d = ImageDraw.Draw(img)
    cracks(d, seed, 650, 1050, 6)
    if hole:
        d.polygon([(600, 980), (720, 990), (735, 1060), (690, 1110), (590, 1090), (575, 1030)], fill=(4, 3, 3))
    a = arr(img)
    L = 0.12 + radial(300, 700, 900) * 0.9
    return grade(lit(a, L[..., None] * np.array([1.0, 0.92, 0.8])[None, None]))

def eye_layer(open_=1.0, cx=655, cy=1045, s=1.0):
    lay = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    h = 26 * s * open_
    if h > 1:
        d.ellipse([cx - 55 * s, cy - h, cx + 55 * s, cy + h], fill=(200, 190, 175, 255))
        d.ellipse([cx - 22 * s, cy - min(h, 22 * s), cx + 22 * s, cy + min(h, 22 * s)], fill=(40, 30, 20, 255))
        d.ellipse([cx - 9 * s, cy - min(h, 9 * s), cx + 9 * s, cy + min(h, 9 * s)], fill=(0, 0, 0, 255))
        d.ellipse([cx - 14 * s, cy - 14 * s, cx - 6 * s, cy - 6 * s], fill=(255, 255, 255, 255))
    return lay

def sky_snow():
    a = grad((8, 12, 22), (40, 48, 62), power=1.3)
    a += radial(1050, 380, 80)[..., None] * 200 + radial(1050, 380, 280)[..., None] * 40
    return a

def ne_house(close=False, windows_on=(1, 0, 1, 0, 1)):
    """Casa de madera de Nueva Inglaterra, de noche, con nieve."""
    a = sky_snow()
    img = to_img(a); d = ImageDraw.Draw(img)
    r = np.random.default_rng(4)
    for tx in (90, 1180, 1240):   # árboles sin hojas
        d.line([tx, 1900, tx, 700], fill=(10, 10, 14), width=18)
        for k in range(14):
            y = 760 + k * 70; L_ = r.uniform(80, 220); s = 1 if k % 2 else -1
            d.line([tx, y, tx + s * L_, y - L_ * 0.7], fill=(10, 10, 14), width=6)
    sc = 1.45 if close else 1.0; ox, oy = (650, 1200)
    P = lambda x, y: (ox + (x - 650) * sc, oy + (y - 1200) * sc)
    body = [P(330, 1000), P(970, 1000), P(970, 1800), P(330, 1800)]
    d.polygon(body, fill=(52, 54, 60))
    for k in range(32):                                   # tablas horizontales
        y = 1000 + k * 25
        d.line([P(330, y), P(970, y)], fill=(38, 40, 46), width=3)
    d.polygon([P(290, 1010), P(650, 700), P(1010, 1010)], fill=(22, 22, 26))   # tejado a dos aguas
    d.rectangle([*P(820, 700), *P(880, 880)], fill=(30, 26, 26))                 # chimenea
    d.polygon([P(290, 1010), P(650, 700), P(1010, 1010), P(980, 1010), P(650, 735), P(320, 1010)], fill=(225, 230, 240))  # nieve en el tejado
    wins = [(400, 1100), (590, 1100), (780, 1100), (400, 1450), (780, 1450)]
    for (wx, wy), on in zip(wins, windows_on):
        d.rectangle([*P(wx, wy), *P(wx + 120, wy + 190)], fill=(210, 160, 80) if on else (14, 15, 20))
        d.line([P(wx + 60, wy), P(wx + 60, wy + 190)], fill=(40, 30, 20), width=int(6 * sc))
        d.line([P(wx, wy + 95), P(wx + 120, wy + 95)], fill=(40, 30, 20), width=int(6 * sc))
    d.rectangle([*P(590, 1520), *P(710, 1800)], fill=(70, 30, 26))                # puerta
    d.rectangle([0, 1800 * (1 if not close else 1) + (0 if not close else 290), BW, BH], fill=(215, 222, 235))
    a = arr(img)
    glow = np.zeros((BH, BW))
    for (wx, wy), on in zip(wins, windows_on):
        if on:
            x0, y0 = P(wx, wy); x1, y1 = P(wx + 120, wy + 190)
            glow += radial((x0 + x1) / 2, (y0 + y1) / 2, 160 * sc) * 0.6
    a += glow[..., None] * np.array([150, 100, 40])
    return a, P

def snow_layer(img, t, n=220, big=False, seed=0):
    d = ImageDraw.Draw(img, "RGBA"); r = np.random.default_rng(seed); F = r.random((n, 4))
    for fx, fy, fs, ph in F:
        s = (2 + fs ** 3 * 9) * (2 if big else 1)
        y = (fy * H + t * (70 + fs * 160)) % (H + 40) - 20
        x = (fx * W + 30 * math.sin(t * (0.6 + ph) + ph * 6)) % W
        d.ellipse([x - s, y - s, x + s, y + s], fill=(240, 245, 255, int(100 + fs * 140)))

def family_window():
    a, P = ne_house(True, (0, 0, 0, 1, 0))
    img = to_img(a); d = ImageDraw.Draw(img)
    x0, y0 = P(400, 1450); x1, y1 = P(520, 1640)
    for k, (fx, hh) in enumerate([(0.2, 1.0), (0.45, 0.75), (0.65, 0.7), (0.85, 0.62)]):
        cx = x0 + (x1 - x0) * fx; top = y1 - (y1 - y0) * 0.55 * hh
        d.ellipse([cx - 16, top - 16, cx + 16, top + 16], fill=(20, 14, 10))
        d.rounded_rectangle([cx - 24, top + 12, cx + 24, y1], 14, fill=(20, 14, 10))
    return arr(img)

def living_dark():
    a = room((95, 85, 70), (70, 52, 38), (60, 56, 50), seed=6)
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rounded_rectangle([420, 1300, 900, 1520], 40, fill=(70, 40, 35))           # sofá
    d.rounded_rectangle([400, 1220, 920, 1330], 40, fill=(80, 46, 40))
    d.rectangle([1020, 1300, 1200, 1460], fill=(30, 30, 32)); d.rectangle([1040, 1320, 1180, 1430], fill=(90, 110, 130))  # tele
    d.line([250, 1600, 250, 1150], fill=(40, 34, 28), width=10); d.polygon([(190, 1150), (310, 1150), (280, 1060), (220, 1060)], fill=(200, 180, 140))
    a = arr(img)
    L = (0.06 + radial(250, 1100, 300) * 0.9)[..., None] + radial(1110, 1375, 260)[..., None] * 0.7 * np.array([0.6, 0.8, 1.2])
    return grade(lit(a, L))

def objects_moved(p):
    a = grad((70, 46, 30), (50, 32, 20)) * (0.8 + 0.4 * noise_tex(BW, BH, 2, 31)[..., None] * noise_tex(BW, BH, 60, 32)[..., None] ** 0.3)
    for k in range(9):
        a[:, int(k * 150):int(k * 150) + 3] *= 0.7
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    objs = [((380, 800), (700, 1000), "cup"), ((850, 1250), (520, 1500), "keys"), ((400, 1500), (900, 820), "frame")]
    k = min(1, max(0, (p - 0.25) / 0.5)); k = k * k * (3 - 2 * k)
    for (a0, a1, kind) in objs:
        # contorno de donde estaba
        x, y = a0
        if kind == "cup": d.ellipse([x - 90, y - 90, x + 90, y + 90], outline=(220, 220, 220, 120), width=4)
        if kind == "keys": d.rectangle([x - 70, y - 40, x + 70, y + 40], outline=(220, 220, 220, 120), width=4)
        if kind == "frame": d.rectangle([x - 130, y - 170, x + 130, y + 170], outline=(220, 220, 220, 120), width=4)
        x = a0[0] + (a1[0] - a0[0]) * k; y = a0[1] + (a1[1] - a0[1]) * k
        if kind == "cup":
            d.ellipse([x - 90, y - 90, x + 90, y + 90], fill=(230, 228, 220)); d.ellipse([x - 65, y - 65, x + 65, y + 65], fill=(60, 35, 20))
            d.rounded_rectangle([x + 80, y - 25, x + 140, y + 25], 20, outline=(230, 228, 220), width=14)
        if kind == "keys":
            d.ellipse([x - 70, y - 40, x - 10, y + 20], outline=(200, 190, 120), width=10)
            d.rectangle([x - 15, y - 15, x + 80, y], fill=(200, 190, 120)); d.rectangle([x + 50, y, x + 60, y + 20], fill=(200, 190, 120))
        if kind == "frame":
            d.rectangle([x - 130, y - 170, x + 130, y + 170], fill=(40, 30, 22)); d.rectangle([x - 105, y - 145, x + 105, y + 145], fill=(150, 150, 160))
    a = arr(img)
    return grade(a * (0.25 + 0.95 * radial(650, 1100, 650))[..., None])

def basement_wall():
    a = np.zeros((BH, BW, 3)) + np.array([105, 104, 100], float)
    a *= (0.75 + 0.4 * noise_tex(BW, BH, 2, 41) * 0.5 + 0.2 * noise_tex(BW, BH, 30, 42))[..., None]
    for row, y in enumerate(range(0, BH, 170)):   # bloques de hormigón
        a[y:y + 8] *= 0.55
        off = 0 if row % 2 else 200
        for x in range(off, BW, 400): a[y:y + 170, x:x + 8] *= 0.55
    return a

def scrawl_paths(seed=51):
    r = np.random.default_rng(seed); paths = []
    for line in range(5):
        y0 = 820 + line * 190; x = 180 + r.uniform(0, 80)
        while x < 1100 - 60:
            pts = []
            for k in range(int(r.integers(5, 10))):
                pts.append((x + k * 14, y0 + r.normal(0, 40) + (k % 2) * r.uniform(-50, 50)))
            paths.append(pts); x += r.uniform(110, 200)
    return paths
SCRAWL = scrawl_paths()

def basement(p):
    a = basement_wall()
    img = to_img(a); d = ImageDraw.Draw(img)
    n = int(len(SCRAWL) * min(1, p / 0.7))
    for pts in SCRAWL[:n]:
        d.line(pts, fill=(120, 8, 10), width=16, joint="curve")
        bx, by = pts[-1]
        d.line([bx, by, bx + 2, by + 60 + (hash(int(bx)) % 120)], fill=(110, 6, 8), width=7)  # goteo
    d.line([650, 0, 650, 350], fill=(20, 20, 20), width=4); d.ellipse([625, 340, 675, 410], fill=(255, 230, 170))
    a = arr(img)
    L = 0.05 + radial(650, 380, 650) * 1.2
    out = grade(lit(a, L[..., None] * np.array([1.05, 0.95, 0.8])[None, None]), (4, 8, 16))
    out += radial(650, 375, 60)[..., None] * 200
    return out

def cutaway(found=False, t=0.0):
    """Corte de la casa: hueco estrecho entre dos paredes (centro) con alguien dentro; dormitorio a la derecha."""
    a = grad((14, 15, 18), (8, 8, 10))
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([720, 400, 1300, 1900], fill=(90, 80, 66))                     # dormitorio
    d.rectangle([980, 1560, 1300, 1900], fill=(70, 50, 40))                    # cama
    for fx in (1060, 1190): d.ellipse([fx - 40, 1490, fx + 40, 1570], fill=(30, 24, 20))
    d.rectangle([620, 400, 680, 1960], fill=(96, 80, 60))                      # interior del hueco
    d.rectangle([575, 400, 620, 1960], fill=(175, 165, 145))                   # pared exterior
    d.rectangle([680, 400, 725, 1960], fill=(175, 165, 145))                   # pared interior
    for y in range(420, 1940, 180): d.rectangle([620, y, 680, y + 16], fill=(120, 88, 55))
    d.rectangle([0, 1960, BW, BH], fill=(40, 34, 28))
    a = arr(img)
    L = 0.32 + (XX > 720) * (0.3 + radial(1050, 800, 600) * 0.6)
    out = lit(a, L)
    if found:
        out += cone(1300, 1180, math.pi, 0.16, 1500)[..., None] * np.array([255, 245, 220]) * 0.8
    lay = to_img(out); d = ImageDraw.Draw(lay)
    d.ellipse([624, 1060, 676, 1115], fill=(3, 3, 4))                          # alguien encogido dentro
    d.rounded_rectangle([622, 1105, 678, 1420], 22, fill=(3, 3, 4))
    if found:
        for ex in (640, 660): d.ellipse([ex - 4, 1080, ex + 4, 1088], fill=(230, 225, 210))
    if not found: d.line([600, 1000, 330, 780], fill=(230, 30, 40), width=6)
    if not found: d.text((170, 700), "HUECO", font=F_SM, fill=(230, 30, 40), stroke_width=3, stroke_fill=(0, 0, 0))
    return arr(lay)

def date_card(p):
    a = grad((30, 26, 22), (14, 12, 10))
    img = to_img(a)
    pg = Image.new("RGBA", (820, 1000), (238, 234, 222, 255)); d = ImageDraw.Draw(pg)
    d.rectangle([0, 0, 820, 200], fill=(150, 20, 25))
    text_c(d, 50, "DICIEMBRE 1986", ImageFont.truetype(FONT, 80), (255, 255, 255), w=820)
    for k, s in enumerate("LMXJVSD"): d.text((60 + k * 105, 230), s, font=F_XS, fill=(80, 80, 80))
    day = 1
    for row in range(5):
        for col in range(7):
            if row == 0 and col < 0: continue
            if day > 31: break
            x, y = 60 + col * 105, 300 + row * 130
            d.text((x, y), str(day), font=F_SM, fill=(30, 30, 30))
            if day == 8 and p > 0.35:
                k = min(1, (p - 0.35) / 0.25)
                d.arc([x - 30, y - 22, x + 95, y + 85], -90, -90 + 360 * k, fill=(220, 20, 30), width=10)
            day += 1
    pg = pg.rotate(3, expand=True, resample=Image.BICUBIC)
    img.paste(pg, (230, 560), pg)
    return arr(img) * (0.35 + 0.9 * radial(650, 1100, 700))[..., None]

def front_door(p):
    a = sky_snow()
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([0, 300, BW, 1900], fill=(52, 54, 60))
    for k in range(64): d.line([0, 300 + k * 25, BW, 300 + k * 25], fill=(38, 40, 46), width=3)
    d.rectangle([380, 700, 920, 1900], fill=(240, 235, 225))
    d.rectangle([420, 740, 880, 1900], fill=(0, 0, 0))
    open_ = 0.15 + 0.35 * min(1, p / 0.6)
    gw = int(460 * open_)
    d.rectangle([420, 740, 880 - gw, 1900], fill=(90, 32, 28))
    d.ellipse([820 - gw, 1300, 850 - gw, 1330], fill=(200, 170, 90))
    d.rectangle([0, 1900, BW, BH], fill=(215, 222, 235))
    a = arr(img)
    a[740:1900, 880 - gw:880] = np.array([25, 22, 20]) + radial(880 - gw / 2, 1300, 250)[740:1900, 880 - gw:880, None] * np.array([60, 45, 30])
    return grade(a * 0.85)

def closet_us(open_=0.0):
    a = plaster(61, (120, 112, 98))
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([330, 380, 970, 2000], fill=(230, 225, 210))                   # marco
    d.rectangle([360, 410, 940, 2000], fill=(0, 0, 0))
    gw = int(580 * open_)
    d.rectangle([360, 410, 940 - gw, 2000], fill=(185, 175, 155))
    for yy in (520, 1250): d.rectangle([400, yy, 900 - gw, yy + 600], outline=(150, 140, 120), width=6)
    d.ellipse([870 - gw, 1150, 905 - gw, 1185], fill=(190, 170, 100))
    d.rectangle([0, 2000, BW, BH], fill=(70, 52, 38))
    return arr(img), gw

def closet_door(t, p):
    a, gw = closet_us(0.04 + 0.12 * min(1, p / 0.8))
    L = 0.04 + radial(560 + 60 * math.sin(t * 1.5), 1150, 380) * 1.2
    return grade(lit(a, L), (6, 10, 22))

def closet_hatchet(t, p):
    a = np.zeros((BH, BW, 3)) + 6
    img = to_img(a); d = ImageDraw.Draw(img)
    for x in range(300, 1000, 90): d.line([x, 300, x - 20, 700], fill=(26, 24, 22), width=26)  # ropa colgada
    d.ellipse([520, 760, 780, 1060], fill=(16, 14, 13))                           # cabeza
    d.rounded_rectangle([420, 1030, 880, 2200], 140, fill=(14, 12, 11))
    for k in range(3):                                                            # pintura facial (rayas)
        d.line([560, 860 + k * 50, 740, 880 + k * 50], fill=(150, 25, 25), width=14)
    for ex in (600, 700):
        d.ellipse([ex - 22, 880, ex + 22, 908], fill=(210, 200, 185)); d.ellipse([ex - 9, 884, ex + 9, 904], fill=(5, 5, 5))
    d.rounded_rectangle([900, 700, 935, 1350], 12, fill=(60, 42, 28))             # mango del hacha
    d.polygon([(860, 700), (1010, 650), (1040, 830), (900, 820)], fill=(150, 155, 160))  # hoja
    d.rounded_rectangle([860, 1250, 960, 1350], 40, fill=(14, 12, 11))            # mano
    a = arr(img)
    L = 0.25 + radial(650 + 50 * math.sin(t * 2.1), 950, 340) * 1.6
    out = lit(a, L)
    out += radial(950, 740, 90)[..., None] * np.array([90, 90, 100]) * (0.5 + 0.5 * math.sin(t * 6))   # brillo del filo
    return out

def chase(t, p):
    a = room((95, 80, 65), (70, 50, 34), (60, 54, 46), seed=71)
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([560, 900, 740, 1480], fill=(40, 30, 20))                         # puerta del dormitorio al fondo
    d.rectangle([575, 915, 725, 1480], fill=(200, 170, 120))
    # sombra alargada con el hacha en la pared izquierda
    sx = 80 + 220 * p
    d.polygon([(sx, 600), (sx + 120, 640), (sx + 160, 1600), (sx + 20, 1700)], fill=(0, 0, 0, 200))
    d.ellipse([sx + 10, 470, sx + 130, 610], fill=(0, 0, 0, 200))
    d.line([sx + 130, 760, sx + 300, 480], fill=(0, 0, 0, 200), width=26)
    d.polygon([(sx + 270, 430), (sx + 380, 470), (sx + 330, 560)], fill=(0, 0, 0, 200))
    a = arr(img)
    L = 0.08 + radial(650, 1200, 400) * 1.0 + radial(200, 900, 500) * 0.4
    out = lit(a, L) * np.array([1.15, 0.85, 0.8])
    return arr(to_img(out).filter(ImageFilter.BoxBlur(int(3 + 4 * abs(math.sin(t * 7))))))

def window_escape(t, p):
    a = plaster(81, (70, 72, 82))
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([300, 500, 1000, 1500], fill=(230, 228, 220))
    d.rectangle([330, 530, 970, 1470], fill=(6, 8, 14))
    # hoja de guillotina subida
    d.rectangle([330, 530, 970, 900], fill=(200, 198, 190)); d.rectangle([350, 550, 950, 880], fill=(30, 36, 50))
    # cortina movida por el viento
    sway = 60 * math.sin(t * 2.5)
    d.polygon([(330, 530), (520, 530), (480 + sway, 1100), (400 + sway * 1.4, 1470), (330, 1470)], fill=(170, 150, 120))
    d.rectangle([0, 1500, BW, BH], fill=(60, 50, 40))
    a = arr(img)
    a[900:1470, 520:970] += radial(750, 1300, 300)[900:1470, 520:970, None] * np.array([20, 30, 50])
    return grade(a * (0.35 + 0.8 * radial(650, 1000, 650))[..., None])

def police_house(t):
    a, P = ne_house(False, (0, 0, 0, 0, 0))
    r = 0.5 + 0.5 * math.sin(t * 9); b = 1 - r
    a += radial(250, 1950, 700)[..., None] * np.array([255, 20, 30]) * r * 0.85
    a += radial(1050, 1950, 700)[..., None] * np.array([20, 70, 255]) * b * 0.85
    return a

def name_card(t, p):
    a = np.zeros((BH, BW, 3)) + np.array([228, 222, 205], float)
    a *= (0.88 + 0.2 * noise_tex(BW, BH, 2, 91))[..., None]
    img = to_img(a); d = ImageDraw.Draw(img)
    d.text((170, 650), "EXPEDIENTE", font=F_MONO, fill=(60, 60, 60))
    name = "DANIEL LAPLANTE"; n = int(len(name) * min(1, p / 0.55))
    d.text((170, 900), name[:n] + ("_" if int(t * 4) % 2 else ""), font=ImageFont.truetype(MONO, 92), fill=(20, 20, 20))
    if p > 0.55:
        d.text((170, 1060), "16 AÑOS · PEPPERELL, 1986", font=F_MONO, fill=(60, 60, 60))
    a = arr(img)
    return a * (0.3 + 0.85 * radial(650, 1000, 650))[..., None]

def bars(t, p):
    a = grad((30, 34, 40), (12, 14, 18)) * (0.8 + 0.3 * noise_tex(BW, BH, 3, 101)[..., None])
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([780, 900, 1000, 1150], fill=(90, 100, 120))      # ventanuco
    for x in range(0, BW, 130): d.rectangle([x, 0, x + 34, BH], fill=(25, 25, 28)); d.line([x + 8, 0, x + 8, BH], fill=(80, 80, 85), width=4)
    d.rectangle([0, 500, BW, 540], fill=(25, 25, 28)); d.rectangle([0, 1700, BW, 1740], fill=(25, 25, 28))
    a = arr(img)
    a += radial(890, 1025, 300)[..., None] * np.array([40, 50, 70])
    out = grade(a)
    lay = to_img(out); d = ImageDraw.Draw(lay)
    text_c(d, 1950, "CENTRO DE MENORES", F_SM, (230, 230, 230), 4, w=BW)
    return arr(lay)

def bail(t, p):
    a, gw = closet_us(0.0)
    a = np.zeros((BH, BW, 3)) + 10
    img = to_img(a); d = ImageDraw.Draw(img)
    gw = int(580 * min(1, p / 0.6) * 0.8)
    d.rectangle([330, 380, 970, 2000], fill=(70, 70, 75)); d.rectangle([360, 410, 940, 2000], fill=(255, 250, 235))
    d.rectangle([360, 410, 940 - gw, 2000], fill=(60, 62, 66))
    a = arr(img)
    a += cone(650, 2000, math.pi / 2, 0.6, 800)[..., None] * np.array([120, 110, 90]) * (gw / 460)
    lay = to_img(a * (0.4 + 0.8 * radial(650, 1200, 800))[..., None]); d = ImageDraw.Draw(lay, "RGBA")
    st = Image.new("RGBA", (800, 220), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
    ds.rounded_rectangle([8, 8, 792, 212], 18, outline=(220, 30, 40, 235), width=12)
    text_c(ds, 30, "BAJO FIANZA", ImageFont.truetype(FONT, 70), (220, 30, 40, 235), w=800)
    text_c(ds, 125, "OCTUBRE 1987", F_SM, (220, 30, 40, 235), w=800)
    if p > 0.45:
        st = st.rotate(-8, expand=True); lay.paste(st, (250, 1700), st)
    return arr(lay)

def newspaper(t, p):
    a = grad((20, 18, 16), (8, 8, 8))
    img = to_img(a)
    pg = Image.new("RGBA", (980, 1350), (226, 220, 200, 255)); d = ImageDraw.Draw(pg)
    text_c(d, 30, "EDICIÓN LOCAL · 2 DIC 1987", F_XS, (60, 60, 60), w=980)
    d.line([40, 90, 940, 90], fill=(30, 30, 30), width=4)
    f = ImageFont.truetype(FONT, 104)
    for i, s in enumerate(["TRIPLE CRIMEN", "EN TOWNSEND"]): text_c(d, 120 + i * 120, s, f, (15, 15, 15), w=980)
    text_c(d, 380, "Una madre y sus dos hijos, asesinados", F_SM, (50, 50, 50), w=980)
    d.rectangle([40, 470, 560, 900], fill=(90, 90, 90))
    r = np.random.default_rng(3)
    for k in range(22):
        y = 470 + k * 36
        x0 = 600 if y < 920 else 40
        d.rectangle([x0, y, 940 - r.uniform(0, 80), y + 14], fill=(140, 135, 120))
    pg = pg.rotate(-3, expand=True, resample=Image.BICUBIC)
    img.paste(pg, (150, 400), pg)
    return arr(img) * (0.35 + 0.8 * radial(650, 1000, 700))[..., None]

def candles(t, p):
    a = grad((6, 8, 14), (30, 34, 44))
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([0, 1500, BW, BH], fill=(150, 156, 170))
    pos = [(380, 1600), (560, 1660), (740, 1610), (920, 1680), (480, 1780), (820, 1800)]
    for x, y in pos:
        d.rounded_rectangle([x - 35, y - 150, x + 35, y], 10, fill=(230, 225, 210))
    a = arr(img)
    for k, (x, y) in enumerate(pos):
        fl = 0.85 + 0.15 * math.sin(t * 11 + k * 2) * math.sin(t * 7.3 + k)
        a += radial(x, y - 190, 26)[..., None] * np.array([255, 200, 120]) * 1.2 * fl
        a += radial(x, y - 170, 220)[..., None] * np.array([120, 70, 25]) * 0.6 * fl
    return grade(a)

def prison(t, p):
    a = room((120, 125, 125), (80, 82, 84), (100, 104, 106), seed=111)
    img = to_img(a); d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = BACK
    for k in range(7):    # rejas de celdas en las paredes laterales
        fx = k / 7
        xl = fx * x0; xr = BW - fx * (BW - x1)
        yt = fx * y0; yb = BH - fx * (BH - y1)
        d.line([xl, yt + 40, xl, yb - 40], fill=(30, 32, 34), width=int(20 * (1 - fx) + 4))
        d.line([xr, yt + 40, xr, yb - 40], fill=(30, 32, 34), width=int(20 * (1 - fx) + 4))
    for k in range(4): d.rectangle([600, 300 + k * 0, 700, 330], fill=(230, 240, 255))
    a = arr(img)
    L = 0.12 + radial(650, 600, 700) * 0.9
    out = grade(lit(a, L[..., None] * np.array([0.85, 0.95, 1.1])[None, None]))
    lay = to_img(out); d = ImageDraw.Draw(lay)
    text_c(d, 1900, "CADENA PERPETUA", F_MED, (230, 230, 230), 5, w=BW)
    return arr(lay)

# ---------------------------------------------------------------- precálculo
print("fondos…", flush=True)
BG = {
    "wall_noise": wall_close(3), "eye_gap": wall_close(5, hole=True), "ghost": None,
    "house_ne": ne_house()[0], "family_window": family_window(), "living_dark": living_dark(), "fridge": fridge(),
    "cutaway": cutaway(False), "cutaway_found": cutaway(True), "wall_end": wall_close(7, hole=True),
}
GHOST_ROOM = room((90, 85, 78), (60, 50, 40), (55, 52, 48), seed=12)
GHOST_ROOM = grade(lit(GHOST_ROOM, 0.12 + radial(650, 1100, 600) * 0.5))
GRAIN = [rng.standard_normal((H // 2, W // 2)) * 9 for _ in range(4)]
yy, xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1.2 - (((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2) * 0.75, 0.15, 1)[..., None]

MODES = {  # zoom inicio, zoom fin, paneo x, paneo y
    "wall_noise": (1.0, 1.25, 0.2, 0), "ghost": (1.0, 1.2, 0, 0), "eye_gap": (1.1, 1.9, 0, 0),
    "house_ne": (1.0, 1.15, 0.3, 0.2), "family_window": (1.05, 1.5, -0.5, 0.45), "living_dark": (1.0, 1.15, -0.3, 0),
    "fridge": (1.0, 1.2, 0, 0), "objects_moved": (1.1, 1.0, 0, 0), "basement_msg": (1.05, 1.2, 0, -0.2),
    "cutaway": (1.0, 1.25, 0, 0), "cutaway_found": (1.4, 1.8, 0, 0), "date_card": (1.1, 1.25, 0, 0),
    "front_door": (1.0, 1.15, 0, 0), "hallway": (1.0, 1.35, 0, -0.2), "closet_door": (1.0, 1.12, 0, 0),
    "closet_hatchet": (1.0, 1.25, 0, -0.3), "chase": (1.0, 1.35, 0, 0), "window_escape": (1.05, 1.2, 0, 0),
    "police": (1.0, 1.1, -0.2, 0), "name_card": (1.0, 1.1, 0, 0), "bars": (1.0, 1.1, 0.3, 0),
    "bail": (1.0, 1.15, 0, 0), "newspaper": (1.2, 1.0, 0, -0.3), "candles": (1.0, 1.2, 0, 0.3),
    "prison": (1.0, 1.4, 0, 0), "wall_end": (1.2, 2.2, 0, 0), "end_card": (2.2, 2.4, 0, 0),
}

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    M = MODES.get(name, (1.0, 1.1, 0, 0))
    if name == "wall_noise":
        img = to_img(BG[name]); d = ImageDraw.Draw(img, "RGBA")
        for k in range(4):                      # ondas de sonido saliendo de la pared
            r_ = ((t * 260 + k * 160) % 640)
            d.ellipse([650 - r_, 1050 - r_, 650 + r_, 1050 + r_], outline=(255, 255, 255, int(90 * (1 - r_ / 640))), width=5)
        img = cam(img, p, M); img = img.transform(img.size, Image.AFFINE, (1, 0, 3 * math.sin(t * 40), 0, 1, 2 * math.sin(t * 33)))
        return img
    if name == "ghost":
        img = to_img(GHOST_ROOM); lay = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        al = int(70 + 60 * abs(math.sin(t * 5)) * (0.5 + 0.5 * math.sin(t * 13)))
        d.ellipse([600, 950, 700, 1060], fill=(220, 225, 235, al)); d.rounded_rectangle([570, 1050, 730, 1480], 70, fill=(220, 225, 235, al))
        lay = lay.filter(ImageFilter.GaussianBlur(14)); img.paste(lay, (0, 0), lay)
        return cam(img, p, M)
    if name in ("eye_gap", "wall_end"):
        img = to_img(BG[name])
        op = 1.0 if name == "eye_gap" else min(1, max(0, (p - 0.45) / 0.15))
        blink = 1 - max(0, 1 - abs((t - a) - 1.8) / 0.12) if name == "eye_gap" else 1
        if op * blink > 0:
            e = eye_layer(op * blink, s=0.8); img.paste(e, (0, 0), e)
        return cam(img, p, M)
    if name == "house_ne":
        img = cam(BG[name], p, M); snow_layer(img, t)
        return img
    if name == "family_window":
        img = cam(BG[name], p, M); snow_layer(img, t, 120); return img
    if name == "objects_moved": return cam(objects_moved(p), p, M)
    if name == "basement_msg": return cam(basement(p), p, M)
    if name == "date_card": return cam(date_card(p), p, M)
    if name == "front_door":
        img = cam(front_door(p), p, M); snow_layer(img, t, 160); return img
    if name == "hallway": return cam(hallway(t, p), p, M)
    if name == "closet_door": return cam(closet_door(t, p), p, M)
    if name == "closet_hatchet": return cam(closet_hatchet(t, p), p, M)
    if name == "chase": return cam(chase(t, p), p, M)
    if name == "window_escape":
        img = cam(window_escape(t, p), p, M); snow_layer(img, t, 90, big=True); return img
    if name == "police":
        img = cam(police_house(t), p, M); snow_layer(img, t, 150); return img
    if name == "name_card": return cam(name_card(t, p), p, M)
    if name == "bars": return cam(bars(t, p), p, M)
    if name == "bail": return cam(bail(t, p), p, M)
    if name == "newspaper": return cam(newspaper(t, p), p, M)
    if name == "candles":
        img = cam(candles(t, p), p, M); snow_layer(img, t, 80); return img
    if name == "prison": return cam(prison(t, p), p, M)
    if name == "end_card":
        img = to_img(BG["wall_end"]); e = eye_layer(1, s=0.8); img.paste(e, (0, 0), e)
        img = cam(img, p, M); img = to_img(arr(img) * (1 - 0.6 * min(1, p * 3)))
        d = ImageDraw.Draw(img)
        if p > 0.08:
            text_c(d, 300, "¿SEGURO QUE", ImageFont.truetype(FONT, 110), (255, 255, 255), 7)
            text_c(d, 430, "ES LA CASA?", ImageFont.truetype(FONT, 110), RED, 7)
            text_c(d, 1560, "SÍGUEME PARA MÁS", F_SM, (255, 255, 255), 4)
            text_c(d, 1625, "CASOS REALES", F_SM, (255, 255, 255), 4)
        return img
    if name in BG and BG[name] is not None: return cam(BG[name], p, M)
    raise KeyError(name)

SHOTS = shot_timeline()
CAPS = caption_timeline()
HITS = [0.05, scene_start("eye_gap") + 0.05, scene_start("closet_hatchet"), scene_start("cutaway_found"), scene_start("name_card"), scene_start("newspaper")]

def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, s = cur[0]
    age = t - a
    sc = 0.8 + 0.2 * min(1, age / 0.1) + 0.05 * math.sin(min(1, age / 0.1) * math.pi)
    parts = []
    for k, seg in enumerate(s.split("*")):
        for w in seg.split():
            if parts and all(ch in "…?!.,¿¡" for ch in w) and not w.startswith(("¿", "¡")):
                parts[-1] = (parts[-1][0] + w, parts[-1][1])
            else:
                parts.append((w, k % 2 == 1))
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    full = " ".join(p_[0] for p_ in parts)
    font = F_CAP
    while d.textlength(full, font=font) > W - 100: font = ImageFont.truetype(FONT, font.size - 6)
    x = (W - d.textlength(full, font=font)) / 2
    for i, (wd, h) in enumerate(parts):
        txt = wd + (" " if i < len(parts) - 1 else "")
        d.text((x, 60), txt, font=font, fill=(RED if h else (255, 255, 255)) + (255,), stroke_width=9, stroke_fill=(0, 0, 0, 255))
        x += d.textlength(txt, font=font)
    if sc != 1:
        nw, nh = int(W * sc), int(260 * sc)
        lay2 = lay.resize((nw, nh), Image.BILINEAR); out = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        out.paste(lay2, ((W - nw) // 2, (260 - nh) // 2)); lay = out
    return lay

TAG = Image.new("RGBA", (W, 80), (0, 0, 0, 0))
_d = ImageDraw.Draw(TAG); _s = "HISTORIA REAL · RECREACIÓN"
_d.text(((W - _d.textlength(_s, font=F_XS)) / 2, 20), _s, font=F_XS, fill=(255, 255, 255, 150))

def frame(t, fi):
    idx = [i for i, s in enumerate(SHOTS) if s[0] <= t < s[1]]
    i = idx[0] if idx else len(SHOTS) - 1
    a, b, name = SHOTS[i]
    img = shot_frame(name, t, a, b)
    XF = 0.15
    if i + 1 < len(SHOTS) and t > b - XF:
        a2, b2, n2 = SHOTS[i + 1]
        img = Image.blend(img, shot_frame(n2, t, a2, b2), (t - (b - XF)) / XF)
    x = arr(img) * VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.2: x = x + (1 - u / 0.2) * 120
    # leve parpadeo de película y grano
    x *= 0.97 + 0.03 * math.sin(fi * 2.3) * math.sin(fi * 0.71)
    x += np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    x = (x - 128) * 1.08 + 128
    if t < 0.2: x *= t / 0.2
    if t > TOTAL - 0.6: x *= max(0, (TOTAL - t) / 0.6)
    img = to_img(x)
    img.paste(TAG, (0, 175), TAG)
    cap = caption_layer(t)
    if cap is not None and t < TOTAL - 0.2:
        img.paste(cap, (0, 1180), cap)
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
            render_scene(si, os.path.join(HERE, f"scene_{si:02}.mp4")); print("escena", si, flush=True)

