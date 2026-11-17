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


# ================================================================ planos de "El Vigilante"
TYPE = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
if not os.path.exists(TYPE): TYPE = MONO
F_TYPE = ImageFont.truetype(TYPE, 50)
F_TYPE_B = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 54) if os.path.exists("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf") else F_TYPE

def sky(mode):
    if mode == "dusk":
        a = grad((40, 50, 95), (235, 140, 90), power=0.9)
        a += radial(250, 1500, 380)[..., None] * np.array([120, 70, 30])
    elif mode == "day":
        a = grad((90, 140, 200), (200, 220, 235), power=1.0)
    else:
        a = grad((4, 7, 16), (24, 30, 46), power=1.4)
        a += radial(1050, 380, 80)[..., None] * 190 + radial(1050, 380, 280)[..., None] * 35
    return a

def colonial(mode="dusk", lights=(1, 1, 0, 1, 0, 1, 1), sign=None):
    """Casa colonial americana de 1905: tejado holandés (gambrel), porche con columnas, jardín."""
    a = sky(mode)
    img = to_img(a); d = ImageDraw.Draw(img)
    night = mode == "night"
    tree = (14, 22, 16) if night else ((35, 55, 35) if mode == "day" else (30, 30, 34))
    for cx, cy, r in [(80, 1150, 260), (1230, 1050, 300), (1150, 1300, 220), (150, 1400, 200)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tree)
    wall = (30, 32, 38) if night else ((235, 232, 222) if mode == "day" else (150, 140, 140))
    roof = (12, 12, 16) if night else ((70, 70, 78) if mode == "day" else (45, 42, 48))
    d.polygon([(250, 1050), (330, 820), (650, 700), (970, 820), (1050, 1050)], fill=roof)     # gambrel
    d.rectangle([280, 1040, 1020, 1760], fill=wall)
    for k in range(30): d.line([280, 1040 + k * 24, 1020, 1040 + k * 24], fill=tuple(int(c * 0.85) for c in wall), width=2)
    for dx in (430, 650, 870):                                                                  # buhardillas
        d.rectangle([dx - 60, 820, dx + 60, 960], fill=wall); d.polygon([(dx - 75, 830), (dx, 770), (dx + 75, 830)], fill=roof)
    d.rectangle([250, 1420, 1050, 1450], fill=roof)                                             # tejadillo del porche
    for cx in (290, 470, 650, 830, 1010): d.rectangle([cx - 10, 1450, cx + 10, 1760], fill=(225, 222, 212) if not night else (40, 42, 48))
    wins = [(430, 890), (650, 890), (870, 890), (370, 1130), (560, 1130), (740, 1130), (930, 1130)]
    sizes = [(70, 90)] * 3 + [(110, 170)] * 4
    lit_col = (255, 205, 120)
    for (wx, wy), (ww, wh), on in zip(wins, sizes, lights):
        d.rectangle([wx - ww // 2, wy - wh // 2, wx + ww // 2, wy + wh // 2], fill=lit_col if on else (14, 16, 22))
        d.line([wx, wy - wh // 2, wx, wy + wh // 2], fill=(60, 50, 40), width=5)
        if wh > 100:
            d.rectangle([wx - ww // 2 - 22, wy - wh // 2, wx - ww // 2 - 6, wy + wh // 2], fill=(20, 40, 30))   # contraventanas
            d.rectangle([wx + ww // 2 + 6, wy - wh // 2, wx + ww // 2 + 22, wy + wh // 2], fill=(20, 40, 30))
    d.rectangle([600, 1520, 700, 1760], fill=(60, 30, 25))                                      # puerta
    lawn = (20, 34, 20) if night else ((70, 120, 60) if mode == "day" else (40, 60, 40))
    d.rectangle([0, 1760, BW, BH], fill=lawn)
    d.polygon([(600, 1760), (700, 1760), (760, BH), (540, BH)], fill=(140, 135, 125) if not night else (40, 40, 44))  # camino
    if sign:
        d.rectangle([1000, 1830, 1014, 2080], fill=(240, 240, 240)); d.rectangle([900, 1850, 1180, 1990], fill=(250, 250, 250))
        f = ImageFont.truetype(FONT, 64 if len(sign) < 6 else 46)
        tw = d.textlength(sign, font=f); d.text((1040 - tw / 2, 1880), sign, font=f, fill=(190, 20, 30))
    a = arr(img)
    for (wx, wy), (ww, wh), on in zip(wins, sizes, lights):
        if on: a += radial(wx, wy, 120)[..., None] * np.array([120, 80, 30]) * (0.9 if mode != "day" else 0.15)
    if night: a = grade(a * 0.9, (6, 10, 24))
    return a

def paper(lines, reveal=1.0, w=1000, h=1350, highlight=(), sig=None):
    pg = Image.new("RGBA", (w, h), (236, 232, 220, 255)); d = ImageDraw.Draw(pg)
    tot = sum(len(l) for l in lines); n = int(tot * reveal); y = 110
    for l in lines:
        k = max(0, min(len(l), n)); n -= len(l)
        if k:
            col = (150, 15, 20) if any(hh in l for hh in highlight) else (25, 25, 28)
            d.text((80, y), l[:k], font=F_TYPE, fill=col)
            if 0 < k < len(l) or (n <= 0 and k == len(l) and reveal < 1):
                cx = 80 + d.textlength(l[:k], font=F_TYPE); d.rectangle([cx + 4, y + 8, cx + 30, y + 54], fill=(25, 25, 28))
        y += 72
    if sig:
        d.text((80, h - 230), sig, font=F_TYPE_B, fill=(15, 15, 18))
    return pg

def on_desk(pg, rot=-2.5, y=420):
    a = grad((36, 28, 22), (16, 12, 10)) * (0.8 + 0.35 * noise_tex(BW, BH, 3, 21)[..., None])
    img = to_img(a)
    pg = pg.rotate(rot, expand=True, resample=Image.BICUBIC)
    img.paste(pg, ((BW - pg.width) // 2, y), pg)
    return arr(img) * (0.3 + 0.85 * radial(650, 1100, 720))[..., None]

L1 = ["Querido nuevo vecino", "del 657 de Boulevard:", "", "Permíteme darte la", "bienvenida al barrio."]
LC = L1 + ["", "¿Habéis traído la", "sangre joven que pedí?", "", "¿Sabéis lo que hay", "dentro de las paredes?"]
L2 = ["Pedí a los antiguos", "dueños que me trajeran", "sangre joven.", "", "Y parece que me han", "hecho caso."]


# ================================================================ planos de "Hinterkaifeck"
def winter_sky(night=False):
    if night:
        a = grad((3, 5, 12), (22, 28, 40), power=1.3)
        a += radial(1020, 330, 70)[..., None] * 190 + radial(1020, 330, 260)[..., None] * 30
    else:
        a = grad((120, 128, 140), (205, 208, 212), power=1.0)
    return a

def forest_line(d, y, col, seed=3, h=(260, 520)):
    r = np.random.default_rng(seed)
    for x in np.sort(r.uniform(-80, BW + 80, 34)):
        hh = r.uniform(*h); w = hh * 0.32
        d.polygon([(x - w / 2, y), (x + w / 2, y), (x, y - hh)], fill=col)

def farm_shape(d, x0, y0, sc, night, lit=(), smoke=False):
    """Granja bávara: casa alargada con tejado a dos aguas y establo adosado."""
    P = lambda x, y: (x0 + x * sc, y0 + y * sc)
    wall = (40, 38, 40) if night else (175, 168, 155)
    barn = (32, 28, 26) if night else (110, 90, 70)
    roof = (14, 14, 18) if night else (70, 60, 55)
    d.polygon([P(0, 0), P(380, 0), P(380, 230), P(0, 230)], fill=wall)                  # vivienda
    d.polygon([P(380, 20), P(900, 20), P(900, 230), P(380, 230)], fill=barn)            # establo
    d.polygon([P(-30, 10), P(190, -170), P(410, 10)], fill=roof)
    d.polygon([P(370, 30), P(380, -130), P(920, -130), P(930, 30)], fill=roof)
    d.polygon([P(-30, 10), P(190, -170), P(410, 10), P(390, 10), P(190, -150), P(-10, 10)], fill=(225, 230, 238))   # nieve
    d.rectangle([*P(380, -135), *P(920, -110)], fill=(225, 230, 238))
    d.rectangle([*P(250, -150), *P(285, -60)], fill=roof)                                # chimenea
    wins = [(60, 70), (160, 70), (270, 70), (60, 150), (270, 150)]
    for k, (wx, wy) in enumerate(wins):
        d.rectangle([*P(wx, wy), *P(wx + 50, wy + 55)], fill=(255, 190, 100) if k in lit else (12, 12, 16))
    d.rectangle([*P(150, 140), *P(210, 230)], fill=(50, 34, 24))                         # puerta
    d.rectangle([*P(560, 90), *P(700, 230)], fill=(28, 20, 16))                          # portón del establo
    return P, wins

def farm(night=False, lit=(), sc=1.0, tracks=False):
    a = winter_sky(night)
    img = to_img(a); d = ImageDraw.Draw(img)
    forest_line(d, 1250, (12, 16, 18) if night else (55, 65, 62), 3)
    forest_line(d, 1330, (8, 10, 12) if night else (40, 48, 46), 5, (200, 380))
    d.rectangle([0, 1320, BW, BH], fill=(150, 158, 175) if night else (232, 234, 238))
    x0 = 650 - 450 * sc; y0 = 1300 - 230 * sc
    P, wins = farm_shape(d, x0, y0, sc, night, lit)
    if tracks:   # huellas desde el bosque hasta el establo
        for k in range(26):
            u = k / 25; x = 120 + (P(620, 230)[0] - 120) * u + 30 * math.sin(u * 7); y = 1360 + (BH - 1360) * (1 - u) ** 1.6
            s = 6 + 16 * (1 - u)
            off = s * 0.9 * (1 if k % 2 else -1)
            d.ellipse([x + off - s, y - s * 0.6, x + off + s, y + s * 0.6], fill=(120, 128, 145) if not night else (80, 88, 110))
    a = arr(img)
    for k in lit:
        wx, wy = wins[k]; cx, cy = P(wx + 25, wy + 27)
        a += radial(cx, cy, 90 * sc)[..., None] * np.array([150, 90, 30])
    if night: a = grade(a, (6, 10, 24))
    return a, P

def tracks_close(t, p):
    a = np.zeros((BH, BW, 3)) + np.array([228, 232, 240], float)
    a *= (0.88 + 0.16 * noise_tex(BW, BH, 4, 61))[..., None]
    img = to_img(a); d = ImageDraw.Draw(img)
    for k in range(9):           # huellas de bota en perspectiva, todas hacia arriba (hacia la casa)
        y = BH - 140 - k * 230; s = 1.0 - k * 0.07; x = 650 + (90 if k % 2 else -90) * s
        d.rounded_rectangle([x - 55 * s, y - 120 * s, x + 55 * s, y + 40 * s], int(45 * s), fill=(150, 158, 175))
        d.rounded_rectangle([x - 45 * s, y + 50 * s, x + 45 * s, y + 120 * s], int(35 * s), fill=(150, 158, 175))
    a = arr(img)
    lay = to_img(a * (0.45 + 0.6 * radial(650, 1000, 900))[..., None]); d = ImageDraw.Draw(lay, "RGBA")
    if p > 0.35:   # flecha "de vuelta" tachada
        k = min(1, (p - 0.35) / 0.2)
        d.line([1080, 600, 1080, 600 + 700 * k], fill=RED + (230,), width=16)
        if k == 1:
            d.polygon([(1040, 1300), (1120, 1300), (1080, 1380)], fill=RED + (230,))
            d.line([960, 900, 1200, 1100], fill=RED + (255,), width=20); d.line([1200, 900, 960, 1100], fill=RED + (255,), width=20)
    return arr(lay)

def family_lamp(t, p):
    a = room((90, 70, 50), (70, 50, 34), (50, 40, 30), seed=71)
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([340, 1350, 960, 1420], fill=(60, 40, 25))                        # mesa
    d.ellipse([600, 1270, 700, 1350], fill=(255, 200, 110))                       # quinqué
    for k, (x, hh) in enumerate([(380, 1.0), (520, 0.95), (780, 0.9), (900, 0.62), (690, 0.5)]):
        top = 1350 - 330 * hh
        d.ellipse([x - 45 * hh, top - 90 * hh, x + 45 * hh, top], fill=(14, 10, 8))
        d.rounded_rectangle([x - 70 * hh, top - 10, x + 70 * hh, 1420], int(40 * hh), fill=(14, 10, 8))
    a = arr(img)
    fl = 0.9 + 0.1 * math.sin(t * 9) * math.sin(t * 5.3)
    L = 0.05 + radial(650, 1310, 520) * 1.3 * fl
    return grade(lit(a, L[..., None] * np.array([1.1, 0.85, 0.6])))

def lantern_tracks(t, p):
    a, P = farm(False, (), 1.0, tracks=True)
    a = a * 0.75
    img = to_img(a); d = ImageDraw.Draw(img)
    # el abuelo (silueta) con farol mirando las huellas
    x = 950; y = 1900
    d.ellipse([x - 40, y - 380, x + 40, y - 300], fill=(16, 14, 14)); d.rectangle([x - 60, y - 300, x + 60, y], fill=(16, 14, 14))
    d.line([x - 60, y - 220, x - 130, y - 120], fill=(16, 14, 14), width=22)
    a = arr(img)
    a += radial(x - 140, y - 100, 60)[..., None] * np.array([255, 190, 90]) * 1.2
    return a

def attic(t, p, lantern=False):
    a = np.zeros((BH, BW, 3)) + 8
    img = to_img(a); d = ImageDraw.Draw(img)
    for k in range(7):        # vigas en perspectiva
        x = -200 + k * 290
        pass
    d.polygon([(0, 0), (BW, 0), (650, 1050)], fill=(62, 46, 32))                               # pared del fondo (hastial)
    d.polygon([(0, 1700), (650, 1050), (BW, 1700)], fill=(110, 84, 58))                         # suelo hacia el fondo
    for k in range(9): d.line([650, 1050, -300 + k * 237, 1700], fill=(80, 60, 40), width=4)
    d.polygon([(0, 0), (650, 1050), (0, 1700)], fill=(105, 80, 55)); d.polygon([(BW, 0), (650, 1050), (BW, 1700)], fill=(92, 70, 48))
    for k in range(7):
        x = -200 + k * 290
        d.line([x, 0, 650 + (x - 650) * 0.25, 1050], fill=(55, 40, 26), width=30)
    d.polygon([(0, 1700), (BW, 1700), (BW, BH), (0, BH)], fill=(120, 92, 62))
    for k in range(10): d.line([0, 1700 + k * 70, BW, 1700 + k * 70], fill=(38, 28, 20), width=4)
    d.rectangle([590, 960, 710, 1060], fill=(30, 40, 60))                         # ventanuco
    for (bx, by, bw, bh) in [(150, 1580, 220, 160), (900, 1550, 260, 200), (1000, 1430, 140, 120)]:
        d.rectangle([bx, by, bx + bw, by + bh], fill=(60, 45, 30))                # cajas
    a = arr(img)
    if lantern:
        cx = 650 + 300 * math.sin(t * 0.9); L = 0.12 + radial(cx, 1500, 520) * 1.6
        out = lit(a, L[..., None] * np.array([1.15, 0.9, 0.6]))
        out += radial(cx, 2100, 70)[..., None] * np.array([255, 200, 110])
    else:
        L = 0.22 + radial(650, 1010, 380) * 0.9
        out = lit(a, L[..., None] * np.array([0.7, 0.8, 1.1]))
        for k, ph in enumerate((0.2, 0.55)):  # "pasos": ondas de polvo sobre las tablas
            u = (p * 2 + ph) % 1
            out += radial(400 + k * 420, 1900 - 200 * k, 40 + 140 * u)[..., None] * 30 * (1 - u)
    return grade(out)

def newspaper_munich(t, p):
    pg = Image.new("RGBA", (980, 1300), (222, 214, 190, 255)); d = ImageDraw.Draw(pg)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 92)
    text_c(d, 40, "MÜNCHNER", f, (20, 20, 20), w=980)
    text_c(d, 150, "ZEITUNG", f, (20, 20, 20), w=980)
    d.line([40, 270, 940, 270], fill=(30, 30, 30), width=5)
    d.text((40, 285), "München · März 1922", font=F_TYPE, fill=(50, 50, 50))
    d.line([40, 350, 940, 350], fill=(30, 30, 30), width=3)
    r = np.random.default_rng(4)
    for col in range(3):
        for k in range(26):
            y = 390 + k * 34
            d.rectangle([40 + col * 310, y, 40 + col * 310 + r.uniform(200, 280), y + 12], fill=(120, 112, 95))
    on = on_desk(pg, -4, 420)
    return on

def maid_leaving(t, p):
    a, P = farm(False, (), 0.7)
    a = a * 0.8
    img = to_img(a); d = ImageDraw.Draw(img)
    x = 650 + 120 * p; y = 1850 + 250 * p; s = 1.0 - 0.15 * p
    d.ellipse([x - 38 * s, y - 360 * s, x + 38 * s, y - 280 * s], fill=(18, 16, 16))
    d.polygon([(x - 50 * s, y - 280 * s), (x + 50 * s, y - 280 * s), (x + 95 * s, y), (x - 95 * s, y)], fill=(18, 16, 16))
    d.rectangle([x + 70 * s, y - 150 * s, x + 150 * s, y - 70 * s], fill=(70, 45, 30))     # maleta
    return arr(img)

def poll(t, p):
    a, _P = farm(True, (0,), 1.0)
    img = to_img(arr(to_img(a).filter(ImageFilter.GaussianBlur(16))) * 0.4)
    d = ImageDraw.Draw(img, "RGBA")
    text_c(d, 470, "¿DORMIRÍAS", ImageFont.truetype(FONT, 120), (255, 255, 255), 6, w=BW)
    text_c(d, 610, "UNA NOCHE AQUÍ?", ImageFont.truetype(FONT, 100), (255, 255, 255), 6, w=BW)
    for k, (num, txt, col) in enumerate([("1", "ME QUEDO", (40, 160, 90)), ("2", "ME VOY", (200, 30, 40))]):
        y = 900 + k * 300; pulse = 1 + 0.04 * math.sin(t * 6 + k * math.pi)
        w2 = 430 * pulse; h2 = 110 * pulse
        d.rounded_rectangle([650 - w2, y - h2, 650 + w2, y + h2], 60, fill=col + (235,))
        d.ellipse([650 - w2 + 30, y - 80, 650 - w2 + 190, y + 80], fill=(255, 255, 255, 255))
        tw = d.textlength(num, font=F_MED); d.text((650 - w2 + 110 - tw / 2, y - 55), num, font=F_MED, fill=col)
        d.text((650 - w2 + 240, y - 50), txt, font=F_MED, fill=(255, 255, 255))
    text_c(d, 1560, "ESCRÍBELO EN LOS COMENTARIOS", F_SM, (230, 230, 230), 3, w=BW)
    return arr(img)

def new_maid(t, p):
    a, P = farm(False, (), 1.6)
    a = a * 0.85
    img = to_img(a); d = ImageDraw.Draw(img)
    x = 520 - 60 * p; y = 2000 - 120 * p
    d.ellipse([x - 45, y - 420, x + 45, y - 330], fill=(20, 18, 18))
    d.polygon([(x - 60, y - 330), (x + 60, y - 330), (x + 110, y), (x - 110, y)], fill=(20, 18, 18))
    d.rectangle([x + 80, y - 170, x + 170, y - 80], fill=(80, 55, 35))
    lay = to_img(arr(img)); d = ImageDraw.Draw(lay)
    text_c(d, 380, "31 DE MARZO DE 1922", F_SM, (255, 255, 255), 4, w=BW)
    return arr(lay)

def barn_door(t, p):
    a = np.zeros((BH, BW, 3)) + np.array([40, 30, 24], float)
    a *= (0.75 + 0.4 * noise_tex(BW, BH, 2, 81) * noise_tex(BW, BH, 40, 82))[..., None]
    for k in range(10): a[:, k * 130:k * 130 + 6] *= 0.5
    img = to_img(a); d = ImageDraw.Draw(img)
    gap = int(40 + 60 * p)
    d.rectangle([650 - gap // 2, 300, 650 + gap // 2, 2100], fill=(0, 0, 0))
    d.line([150, 700, 1150, 1700], fill=(30, 22, 16), width=40); d.line([1150, 700, 150, 1700], fill=(30, 22, 16), width=40)
    d.rectangle([0, 2100, BW, BH], fill=(215, 220, 230))
    a = arr(img)
    L = 0.3 + radial(650, 1200, 700) * 0.8
    return grade(lit(a, L[..., None] * np.array([0.8, 0.85, 1.05])), (4, 6, 16))

def window_dark(t, p):
    a = plaster(91, (60, 58, 56)) * 0.5
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([330, 650, 970, 1550], fill=(50, 36, 24)); d.rectangle([370, 690, 930, 1510], fill=(6, 8, 14))
    d.line([650, 690, 650, 1510], fill=(50, 36, 24), width=24); d.line([370, 1100, 930, 1100], fill=(50, 36, 24), width=24)
    k = min(1, max(0, (p - 0.4) / 0.3))
    d.ellipse([760 - 40, 1150, 760 + 40, 1240], fill=(2, 2, 3) if k else (6, 8, 14))
    a = arr(img)
    a[690:1510, 370:930] += np.array([10, 14, 26]) * (1 - k * 0.5)
    return grade(a)

def chimney(t, p):
    a, P = farm(False, (), 1.9)
    img = to_img(a * 0.8)
    lay = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = P(267, -150)
    for k in range(14):
        u = ((t * 0.35 + k / 14) % 1)
        r_ = 30 + 120 * u
        d.ellipse([cx - r_ + 160 * u + 20 * math.sin(k + t), cy - 900 * u - r_, cx + r_ + 160 * u, cy - 900 * u + r_], fill=(200, 200, 205, int(150 * (1 - u))))
    lay = lay.filter(ImageFilter.GaussianBlur(18)); img.paste(lay, (0, 0), lay)
    return arr(img)

def stable(t, p):
    a = room((70, 55, 40), (80, 65, 40), (40, 32, 24), seed=101)
    img = to_img(a); d = ImageDraw.Draw(img)
    for k, x in enumerate((380, 760)):
        d.rounded_rectangle([x - 200, 1250, x + 200, 1550], 80, fill=(30, 24, 20))               # vaca (silueta)
        d.ellipse([x + 150, 1180, x + 290, 1330], fill=(30, 24, 20))
        for lx in (x - 150, x - 90, x + 90, x + 150): d.rectangle([lx, 1530, lx + 30, 1700], fill=(30, 24, 20))
    r = np.random.default_rng(3)
    for k in range(300):                                                                         # heno recién echado
        x = r.uniform(200, 1100); y = r.uniform(1700, 1900)
        d.line([x, y, x + r.uniform(-40, 40), y + r.uniform(-15, 15)], fill=(200, 170, 90), width=3)
    a = arr(img)
    L = 0.08 + radial(650, 1500, 600) * 0.9
    return grade(lit(a, L[..., None] * np.array([1.1, 0.95, 0.75])))

def kitchen_killer(t, p):
    a = room((80, 66, 50), (60, 46, 32), (45, 38, 30), seed=111)
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([380, 1400, 920, 1460], fill=(55, 38, 24))
    d.rectangle([880, 1000, 1080, 1460], fill=(30, 26, 24)); d.rectangle([910, 1300, 1050, 1400], fill=(255, 120, 40))  # cocina de leña
    d.ellipse([500, 1060, 640, 1200], fill=(5, 5, 6)); d.rounded_rectangle([450, 1190, 690, 1500], 70, fill=(5, 5, 6))  # silueta sentada
    d.ellipse([700, 1340, 780, 1400], fill=(200, 190, 170))                                                             # plato
    a = arr(img)
    fl = 0.85 + 0.15 * math.sin(t * 11) * math.sin(t * 7)
    L = 0.05 + radial(980, 1350, 520) * 1.2 * fl
    out = grade(lit(a, L[..., None] * np.array([1.2, 0.8, 0.5])))
    out += radial(980, 1350, 80)[..., None] * np.array([255, 120, 40]) * fl
    return out

def neighbors(t, p):
    a, P = farm(False, (), 1.2)
    img = to_img(a * 0.85); d = ImageDraw.Draw(img)
    for k, x in enumerate((260, 420, 1000)):
        y = 2050 - 60 * p - (k % 2) * 40
        d.ellipse([x - 38, y - 380, x + 38, y - 300], fill=(18, 16, 16))
        d.rectangle([x - 55, y - 300, x + 55, y], fill=(18, 16, 16))
    return arr(img)

def case_file(t, p):
    a = grad((40, 32, 25), (22, 18, 14)) * (0.8 + 0.4 * noise_tex(BW, BH, 3, 25)[..., None])
    img = to_img(a)
    fo = Image.new("RGBA", (920, 1200), (200, 170, 110, 255)); d = ImageDraw.Draw(fo)
    d.rectangle([0, 0, 360, 70], fill=(185, 155, 95))
    d.text((60, 140), "POLIZEI · BAYERN", font=F_SM, fill=(40, 30, 20))
    d.text((60, 330), "HINTERKAIFECK", font=F_MONO, fill=(30, 25, 20))
    d.text((60, 400), "31.03.1922 · 6 víctimas", font=F_MONO_S, fill=(30, 25, 20))
    d.text((60, 470), "Culpable: ???", font=F_MONO, fill=(30, 25, 20))
    fo = fo.rotate(-3, expand=True, resample=Image.BICUBIC); img.paste(fo, (180, 450), fo)
    if p > 0.4:
        k = min(1, (p - 0.4) / 0.08); sc = 1 + 1.2 * (1 - k)
        st = Image.new("RGBA", (860, 200), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle([8, 8, 852, 192], 20, outline=RED + (235,), width=14)
        text_c(ds, 40, "SIN RESOLVER", ImageFont.truetype(FONT, 100), RED + (235,), w=860)
        st = st.rotate(8, expand=True); st = st.resize((int(st.width * sc), int(st.height * sc)))
        img.paste(st, (650 - st.width // 2, 1350 - st.height // 2), st)
    return arr(img) * (0.35 + 0.9 * radial(650, 1100, 750))[..., None]

def field(t, p, stone=False):
    a = winter_sky(False)
    img = to_img(a); d = ImageDraw.Draw(img)
    forest_line(d, 1250, (55, 65, 62), 3); forest_line(d, 1330, (40, 48, 46), 5, (200, 380))
    d.rectangle([0, 1320, BW, BH], fill=(232, 234, 238))
    if stone:
        d.rectangle([600, 1500, 700, 1720], fill=(130, 130, 128)); d.rectangle([560, 1460, 740, 1520], fill=(120, 120, 118))
        d.rectangle([640, 1340, 660, 1460], fill=(60, 60, 60)); d.rectangle([600, 1370, 700, 1390], fill=(60, 60, 60))
    else:
        for x in (250, 500, 820, 1000): d.rectangle([x, 1420, x + 60, 1440], fill=(150, 140, 130))   # restos
    a = arr(img)
    lay = to_img(a); d = ImageDraw.Draw(lay)
    if not stone: text_c(d, 600, "DERRIBADA", ImageFont.truetype(FONT, 140), (255, 255, 255), 6, w=BW)
    else: text_c(d, 600, "HOY", ImageFont.truetype(FONT, 150), (255, 255, 255), 6, w=BW)
    return arr(lay)

def end_card(t, p):
    a = attic(t, 0.5) * 0.6
    img = to_img(a); d = ImageDraw.Draw(img)
    d.ellipse([620, 990, 680, 1040], fill=(0, 0, 0))                                   # alguien en el ventanuco
    text_c(d, 360, "¿QUÉ OYÓ", ImageFont.truetype(FONT, 140), (255, 255, 255), 8, w=BW)
    text_c(d, 520, "LA CRIADA?", ImageFont.truetype(FONT, 140), RED, 8, w=BW)
    return arr(img)

# ---------------------------------------------------------------- precálculo
print("fondos…", flush=True)
BG = {"tracks_farm": farm(False, (), 1.0, tracks=True)[0], "farm_wide": farm(False, (0, 3), 0.8)[0],
      "farm_night": farm(True, (3,), 1.0)[0]}
GRAIN = [rng.standard_normal((H // 2, W // 2)) * 8 for _ in range(4)]
yy, xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1.2 - (((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2) * 0.75, 0.15, 1)[..., None]

MODES = {
    "tracks_farm": (1.0, 1.25, -0.3, 0.4), "tracks_close": (1.0, 1.15, 0, -0.5), "farm_wide": (1.1, 1.0, 0, 0),
    "family_lamp": (1.0, 1.2, 0, 0.2), "lantern_tracks": (1.0, 1.2, 0.4, 0.5), "attic": (1.0, 1.25, 0, 0),
    "attic_lantern": (1.1, 1.3, 0, 0.3), "newspaper": (1.1, 1.0, 0, -0.2), "maid_leaving": (1.0, 1.15, 0, 0.4), "maid_leaving2": (1.2, 1.35, 0.2, 0.5), "new_maid2": (1.15, 1.3, -0.3, 0.4),
    "poll": (1.0, 1.02, 0, 0), "farm_night": (1.0, 1.2, 0, 0), "new_maid": (1.0, 1.1, -0.2, 0.3),
    "barn_door": (1.0, 1.3, 0, 0), "window_dark": (1.0, 1.4, 0.3, 0.1), "chimney": (1.0, 1.15, 0, -0.3),
    "stable": (1.0, 1.2, 0, 0), "kitchen_killer": (1.0, 1.25, -0.2, 0), "neighbors": (1.0, 1.15, 0, 0.3),
    "case_file": (1.15, 1.0, 0, 0.2), "field": (1.0, 1.1, 0, 0), "memorial": (1.0, 1.2, 0, 0.2), "end_card": (1.0, 1.08, 0, 0),
}

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    M = MODES.get(name, (1.0, 1.1, 0, 0))
    snowy = name in ("maid_leaving2", "new_maid2", "tracks_farm", "farm_wide", "lantern_tracks", "maid_leaving", "farm_night", "new_maid", "chimney", "neighbors", "field", "memorial")
    fn = {"tracks_close": tracks_close, "family_lamp": family_lamp, "lantern_tracks": lantern_tracks, "attic": attic,
          "attic_lantern": lambda t, p: attic(t, p, True), "newspaper": newspaper_munich, "maid_leaving": maid_leaving, "maid_leaving2": maid_leaving, "new_maid2": new_maid,
          "poll": poll, "new_maid": new_maid, "barn_door": barn_door, "window_dark": window_dark, "chimney": chimney,
          "stable": stable, "kitchen_killer": kitchen_killer, "neighbors": neighbors, "case_file": case_file,
          "field": field, "memorial": lambda t, p: field(t, p, True), "end_card": end_card}.get(name)
    img = cam(fn(t, p) if fn else BG[name], p, M)
    if snowy: snow_layer(img, t, 160)
    return img

SHOTS = shot_timeline()
CAPS = caption_timeline()
HITS = [0.05, scene_start("tracks_close") + 0.3, scene_start("attic"), scene_start("barn_door"), scene_start("kitchen_killer"), scene_start("end_card")]

def caption_layer(t):
    """Subtítulo karaoke: palabras ya dichas en blanco (claves en rojo), las que faltan, apagadas."""
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, ws = cur[0]
    age = t - a
    sc = 0.82 + 0.18 * min(1, age / 0.1) + 0.05 * math.sin(min(1, age / 0.1) * math.pi)
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    full = " ".join(w for w, _, _ in ws)
    font = F_CAP
    while d.textlength(full, font=font) > W - 100: font = ImageFont.truetype(FONT, font.size - 6)
    x = (W - d.textlength(full, font=font)) / 2
    for i, (wd, t0, key) in enumerate(ws):
        said = t >= t0 - 0.03
        col = (RED if key else (255, 255, 255)) if said else (255, 255, 255)
        alpha = 255 if said else 110
        txt = wd + (" " if i < len(ws) - 1 else "")
        d.text((x, 60), txt, font=font, fill=col + (alpha,), stroke_width=9, stroke_fill=(0, 0, 0, alpha))
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
    XF = 0.12
    if i + 1 < len(SHOTS) and t > b - XF:
        a2, b2, n2 = SHOTS[i + 1]
        img = Image.blend(img, shot_frame(n2, t, a2, b2), (t - (b - XF)) / XF)
    x = arr(img) * VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.2: x = x + (1 - u / 0.2) * 110
    x *= 0.97 + 0.03 * math.sin(fi * 2.3) * math.sin(fi * 0.71)
    x += np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    x = (x - 128) * 1.06 + 128
    if t < 0.15: x *= t / 0.15
    if t > TOTAL - 0.6: x *= max(0, (TOTAL - t) / 0.6)
    img = to_img(x)
    cap = caption_layer(t)
    if cap is not None and t < TOTAL - 0.2 and not any(s[2] in ("poll", "end_card") and s[0] <= t < s[1] for s in SHOTS):
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
