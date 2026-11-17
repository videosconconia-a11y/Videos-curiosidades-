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

def mailbox(t, p):
    a = colonial("night", (0, 0, 0, 1, 0, 0, 0))
    img = to_img(arr(to_img(a).filter(ImageFilter.GaussianBlur(16))) * 0.5); d = ImageDraw.Draw(img)
    d.rectangle([630, 1350, 670, 2310], fill=(30, 30, 32))                                   # poste
    d.rounded_rectangle([330, 900, 970, 1360], 120, fill=(28, 30, 34))                       # buzón
    d.rectangle([330, 1100, 970, 1360], fill=(28, 30, 34))
    d.rectangle([350, 920, 950, 1340], outline=(55, 58, 64), width=8)
    d.rectangle([975, 900, 1000, 1180], fill=(170, 25, 30)); d.rectangle([975, 900, 1080, 960], fill=(170, 25, 30))  # banderita
    out = min(1, p / 0.5)
    env = Image.new("RGBA", (520, 320), (232, 228, 214, 255)); de = ImageDraw.Draw(env)
    de.line([0, 0, 260, 170, 520, 0], fill=(190, 185, 170), width=5)
    de.text((140, 210), "657 BOULEVARD", font=F_MONO_S, fill=(30, 30, 30))
    env = env.rotate(-6, expand=True)
    img.paste(env, (390, int(1060 - 260 * out)), env)
    a = arr(img)
    a += cone(650, 300, math.pi / 2, 0.5, 1200)[..., None] * np.array([110, 95, 70])
    return grade(a)

def price(t, p):
    img = to_img(arr(to_img(colonial("day")).filter(ImageFilter.GaussianBlur(14))) * 0.45)
    d = ImageDraw.Draw(img)
    v = 1355657 * min(1, p / 0.5) ** 0.5
    s = f"{int(v):,}".replace(",", ".") + " $"
    text_c(d, 820, s, ImageFont.truetype(FONT, 150), (255, 255, 255), 6, w=BW)
    text_c(d, 1010, "JUNIO 2014 · WESTFIELD, NUEVA JERSEY", F_SM, (230, 230, 230), 3, w=BW)
    return arr(img)

def kids_room(t, p):
    a = room((70, 80, 110), (90, 70, 55), (60, 66, 90), seed=31)
    img = to_img(a); d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = BACK
    d.rectangle([560, 880, 760, 1160], fill=(20, 26, 40)); d.line([660, 880, 660, 1160], fill=(200, 200, 210), width=6)  # ventana
    d.rectangle([380, 1390, 760, 1560], fill=(200, 190, 210)); d.rectangle([380, 1330, 430, 1560], fill=(120, 90, 70))  # cama
    d.ellipse([440, 1330, 560, 1410], fill=(240, 240, 245))                                       # almohada
    d.ellipse([820, 1440, 900, 1520], fill=(150, 100, 60)); d.ellipse([835, 1400, 885, 1450], fill=(150, 100, 60))  # osito
    d.ellipse([830, 1395, 850, 1415], fill=(150, 100, 60)); d.ellipse([870, 1395, 890, 1415], fill=(150, 100, 60))
    for k, c in enumerate([(200, 60, 60), (60, 120, 200), (230, 190, 60)]):
        d.rectangle([180 + k * 70, 1900 - k * 20, 240 + k * 70, 1960 - k * 20], fill=c)            # cubos
    a = arr(img)
    L = 0.12 + radial(660, 1020, 380) * 0.8 + cone(660, 1020, math.pi / 2 + 0.2, 0.35, 900) * 0.6
    out = grade(lit(a, L[..., None] * np.array([0.75, 0.85, 1.15])))
    # silueta en la ventana, aparece a mitad del plano
    k = min(1, max(0, (p - 0.45) / 0.2))
    if k > 0:
        sil = np.zeros((BH, BW)); sil[985:1160, 615:705] = 1
        sil *= (((XX - 660) / 45) ** 2 + ((YY - 1010) / 34) ** 2 < 1) | (YY > 1040)
        out = out * (1 - sil[..., None] * 0.9 * k)
    return out

def generations(t, p):
    a = plaster(41, (95, 80, 70)) * 0.6
    img = to_img(a); d = ImageDraw.Draw(img)
    labels = ["ABUELO", "PADRE", "ÉL"]
    for k, (cx, cy) in enumerate([(350, 800), (950, 1050), (500, 1550)]):
        show = p > k * 0.25
        d.rectangle([cx - 190, cy - 240, cx + 190, cy + 240], fill=(70, 50, 30))
        tone = [(170, 150, 110), (150, 145, 130), (60, 62, 70)][k]
        d.rectangle([cx - 160, cy - 210, cx + 160, cy + 210], fill=tone)
        if show:
            d.ellipse([cx - 55, cy - 120, cx + 55, cy - 10], fill=(25, 22, 20))
            d.rounded_rectangle([cx - 110, cy - 5, cx + 110, cy + 210], 60, fill=(25, 22, 20))
            if k == 0: d.rectangle([cx - 85, cy - 140, cx + 85, cy - 110], fill=(25, 22, 20)); d.rectangle([cx - 50, cy - 190, cx + 50, cy - 120], fill=(25, 22, 20))
            if k == 2: d.polygon([(cx - 70, cy - 40), (cx, cy - 160), (cx + 70, cy - 40)], fill=(25, 22, 20))   # capucha
            text_c(d, cy + 250, labels[k], F_SM, (230, 220, 200), 3, w=cx * 2)
    a = arr(img)
    return grade(a * (0.35 + 0.9 * radial(650, 1150, 800))[..., None])

def street_cars(t, p):
    a = sky("night")
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([0, 1300, BW, BH], fill=(18, 18, 22)); d.rectangle([0, 1280, BW, 1320], fill=(40, 40, 44))
    for k in range(6): d.rectangle([k * 260, 1780, k * 260 + 140, 1800], fill=(200, 190, 120))
    for x in (200, 1100):
        d.rectangle([x - 8, 700, x + 8, 1300], fill=(30, 30, 32)); d.rectangle([x - 50, 690, x + 50, 710], fill=(30, 30, 32))
    a = arr(img)
    for x in (200, 1100): a += radial(x, 720, 60)[..., None] * 230 + cone(x, 720, math.pi / 2, 0.35, 700)[..., None] * np.array([120, 100, 60])
    for k in range(3):   # coches
        u = ((t * 0.55 + k * 0.37) % 1.4) - 0.2
        cx = -300 + u * (BW + 600); cy = 1650 + k * 140
        a += radial(cx + 200, cy, 90)[..., None] * np.array([255, 245, 210]) * 1.2
        a += cone(cx + 200, cy, 0, 0.25, 700)[..., None] * np.array([200, 190, 160]) * 0.5
        a += radial(cx - 200, cy, 40)[..., None] * np.array([255, 30, 30])
        box = np.zeros((BH, BW)); y0 = int(cy - 90); x0 = int(max(0, cx - 220)); x1 = int(min(BW, cx + 210))
        if x1 > x0: box[y0:y0 + 150, x0:x1] = 1; a = a * (1 - box[..., None] * 0.85)
    return grade(a)

def windows_watch(t, p):
    a = sky("night")
    img = to_img(a); d = ImageDraw.Draw(img)
    houses = [(0, 900, 520, 1700), (560, 1000, 1300, 1700)]
    for x0, y0, x1, y1 in houses:
        d.rectangle([x0, y0, x1, y1], fill=(26, 28, 34)); d.polygon([(x0 - 30, y0), ((x0 + x1) / 2, y0 - 260), (x1 + 30, y0)], fill=(16, 16, 20))
    wins = [(130, 1100, 1), (330, 1100, 0), (130, 1400, 1), (330, 1400, 0), (700, 1150, 0), (900, 1150, 0), (1100, 1150, 1), (750, 1420, 1), (1050, 1420, 0)]
    for wx, wy, on in wins:
        d.rectangle([wx - 60, wy - 85, wx + 60, wy + 85], fill=(230, 180, 100) if on else (10, 11, 15))
    d.rectangle([0, 1700, BW, BH], fill=(14, 20, 14))
    a = arr(img)
    for wx, wy, on in wins:
        if on: a += radial(wx, wy, 120)[..., None] * np.array([100, 70, 25])
    # silueta en una ventana oscura (1100,1150)
    k = min(1, max(0, (p - 0.3) / 0.25))
    a += (((XX - 900) / 60) ** 2 < 1)[..., None] * ((abs(YY - 1150) < 85))[..., None] * np.array([18, 22, 34]) * 2.0
    sil = ((((XX - 900) / 26) ** 2 + ((YY - 1120) / 30) ** 2) < 1) | ((abs(XX - 900) < 42) & (YY > 1145) & (YY < 1235))
    a = a * (1 - sil[..., None] * 0.95 * k)
    return grade(a)

def signature(t, p):
    pg = paper(["...", "", "Que empiece la fiesta."], 1.0, sig=None)
    d = ImageDraw.Draw(pg)
    k = min(1, p / 0.5)
    f = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMonoBoldOblique.ttf", 96) if os.path.exists("/usr/share/fonts/truetype/freefont/FreeMonoBoldOblique.ttf") else F_TYPE_B
    s = "El Vigilante"; n = int(len(s) * k)
    d.text((110, 600), s[:n], font=f, fill=(150, 15, 20))
    if p > 0.55: d.text((115, 730), "(The Watcher)", font=F_TYPE, fill=(80, 80, 80))
    return on_desk(pg, -2, 420)

def poll(t, p):
    img = to_img(arr(to_img(colonial("night", (0, 0, 0, 1, 0, 0, 0))).filter(ImageFilter.GaussianBlur(18))) * 0.35)
    d = ImageDraw.Draw(img, "RGBA")
    text_c(d, 520, "¿TE QUEDARÍAS?", ImageFont.truetype(FONT, 120), (255, 255, 255), 6, w=BW)
    for k, (num, txt, col) in enumerate([("1", "ME QUEDO", (40, 160, 90)), ("2", "ME VOY", (200, 30, 40))]):
        y = 800 + k * 300; pulse = 1 + 0.04 * math.sin(t * 6 + k * math.pi)
        w2 = 430 * pulse; h2 = 110 * pulse
        d.rounded_rectangle([650 - w2, y - h2, 650 + w2, y + h2], 60, fill=col + (235,))
        d.ellipse([650 - w2 + 30, y - 80, 650 - w2 + 190, y + 80], fill=(255, 255, 255, 255))
        tw = d.textlength(num, font=F_MED); d.text((650 - w2 + 110 - tw / 2, y - 55), num, font=F_MED, fill=col)
        d.text((650 - w2 + 240, y - 50), txt, font=F_MED, fill=(255, 255, 255))
    text_c(d, 1460, "ESCRÍBELO EN LOS COMENTARIOS", F_SM, (230, 230, 230), 3, w=BW)
    return arr(img)

def letters_pile(t, p):
    a = grad((36, 28, 22), (16, 12, 10)) * (0.8 + 0.35 * noise_tex(BW, BH, 3, 23)[..., None])
    img = to_img(a)
    r = np.random.default_rng(9)
    n = 1 + int(4 * min(1, p / 0.7))
    for k in range(n):
        env = Image.new("RGBA", (620, 380), (232 - k * 6, 228 - k * 6, 214 - k * 6, 255)); de = ImageDraw.Draw(env)
        de.line([0, 0, 310, 200, 620, 0], fill=(190, 185, 170), width=5)
        de.text((180, 280), "657 BOULEVARD", font=F_MONO_S, fill=(30, 30, 30))
        env = env.rotate(r.uniform(-25, 25), expand=True)
        img.paste(env, (int(250 + r.uniform(-120, 120)), int(800 + r.uniform(-250, 250))), env)
    return arr(img) * (0.3 + 0.85 * radial(650, 1100, 720))[..., None]

def case_file(t, p):
    a = grad((40, 32, 25), (22, 18, 14)) * (0.8 + 0.4 * noise_tex(BW, BH, 3, 25)[..., None])
    img = to_img(a)
    fo = Image.new("RGBA", (920, 1200), (200, 170, 110, 255)); d = ImageDraw.Draw(fo)
    d.rectangle([0, 0, 360, 70], fill=(185, 155, 95))
    d.text((60, 140), "POLICÍA DE WESTFIELD", font=F_SM, fill=(40, 30, 20))
    d.text((60, 210), "Fiscalía del condado de Union", font=F_XS, fill=(60, 45, 30))
    d.text((60, 330), "CASO: \"THE WATCHER\"", font=F_MONO, fill=(30, 25, 20))
    d.text((60, 400), "657 Boulevard · 2014-", font=F_MONO_S, fill=(30, 25, 20))
    d.text((60, 470), "Sospechoso: ???", font=F_MONO, fill=(30, 25, 20))
    fo = fo.rotate(-3, expand=True, resample=Image.BICUBIC); img.paste(fo, (180, 450), fo)
    if p > 0.35:
        k = min(1, (p - 0.35) / 0.08); sc = 1 + 1.2 * (1 - k)
        st = Image.new("RGBA", (860, 200), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle([8, 8, 852, 192], 20, outline=RED + (235,), width=14)
        text_c(ds, 40, "SIN RESOLVER", ImageFont.truetype(FONT, 100), RED + (235,), w=860)
        st = st.rotate(8, expand=True); st = st.resize((int(st.width * sc), int(st.height * sc)))
        img.paste(st, (650 - st.width // 2, 1350 - st.height // 2), st)
    return arr(img) * (0.35 + 0.9 * radial(650, 1100, 750))[..., None]

def sold(t, p):
    img = to_img(colonial("day", (0,) * 7, sign="SOLD"))
    d = ImageDraw.Draw(img)
    v = 400000 * min(1, p / 0.5) ** 0.5
    s = "-" + f"{int(v):,}".replace(",", ".") + " $"
    lay = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    text_c(dl, 420, s, ImageFont.truetype(FONT, 170), RED + (255,), 8, w=BW)
    text_c(dl, 630, "VENDIDA EN 2019", F_MED, (255, 255, 255, 255), 5, w=BW)
    img.paste(lay, (0, 0), lay)
    return arr(img) * 0.9

def watcher_street(t, p):
    a = colonial("night", (0, 0, 0, 0, 1, 0, 0))
    img = to_img(a); d = ImageDraw.Draw(img)
    # farola y silueta en primer plano (de espaldas, mirando la casa)
    d.rectangle([1130, 300, 1150, BH], fill=(16, 16, 18)); d.rectangle([1060, 290, 1150, 312], fill=(16, 16, 18))
    d.ellipse([170, 1350, 330, 1520], fill=(4, 4, 6))
    d.rounded_rectangle([110, 1500, 390, 2310], 120, fill=(4, 4, 6))
    a = arr(img)
    a += radial(1080, 320, 50)[..., None] * 220 + cone(1080, 320, math.pi / 2 + 0.25, 0.3, 1600)[..., None] * np.array([90, 80, 50])
    fog = noise_tex(BW, BH, 140, 5) * np.clip((YY - 1300) / 1000, 0, 1)
    a += fog[..., None] * np.array([30, 34, 44]) * (1 + 0.3 * math.sin(t))
    return a

def end_card(t, p):
    a = watcher_street(t, 1.0)
    img = to_img(a * (0.45 - 0.15 * min(1, p * 2)))
    d = ImageDraw.Draw(img)
    text_c(d, 380, "¿QUIÉN ERA", ImageFont.truetype(FONT, 140), (255, 255, 255), 8, w=BW)
    text_c(d, 540, "EL VIGILANTE?", ImageFont.truetype(FONT, 140), RED, 8, w=BW)
    return arr(img)

# ---------------------------------------------------------------- precálculo
print("fondos…", flush=True)
BG = {
    "dream_house": colonial("dusk"), "house_day": colonial("day", (0, 0, 0, 0, 0, 0, 0)),
    "wall": wall_close(9, hole=True),
    "house_empty": colonial("night", (0,) * 7, sign="FOR SALE"),
    "letter1_desk": None,
}
LETTER_C = on_desk(paper(LC, 1.0, highlight=("sangre", "paredes")), -2.5, 420)
GRAIN = [rng.standard_normal((H // 2, W // 2)) * 8 for _ in range(4)]
yy, xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1.2 - (((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2) * 0.75, 0.15, 1)[..., None]

MODES = {
    "dream_house": (1.0, 1.15, 0, 0.1), "mailbox": (1.0, 1.12, 0, 0), "letter1": (1.0, 1.08, 0, -0.2),
    "house_day": (1.05, 1.2, 0.3, 0), "price": (1.0, 1.05, 0, 0), "letter_close": (1.3, 1.6, 0, 0.5),
    "kids_room": (1.0, 1.25, 0, -0.2), "wall": (1.1, 1.8, 0, 0), "generations": (1.0, 1.15, 0, 0.3),
    "street_cars": (1.0, 1.1, 0, 0), "windows_watch": (1.0, 1.8, 0.77, 0), "signature": (1.0, 1.15, -0.3, 0),
    "poll": (1.0, 1.02, 0, 0), "letters_pile": (1.1, 1.0, 0, 0), "letter2": (1.0, 1.1, 0, -0.2),
    "house_empty": (1.15, 1.0, 0, 0), "case_file": (1.15, 1.0, 0, 0.2), "sold": (1.0, 1.1, 0, 0),
    "watcher_street": (1.0, 1.2, -0.4, 0.2), "end_card": (1.05, 1.15, 0, 0),
}

def line_progress(name, t):
    """Progreso de la voz dentro de la frase del plano (0..1), para escribir la carta a la vez que se lee."""
    for (a, b, _n, _k, shots, v0, vd, words) in SCENES:
        if name in shots and words:
            return min(1, max(0, (t - v0) / max(0.1, words[-1][1] - v0)))
    return 1.0

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    M = MODES.get(name, (1.0, 1.1, 0, 0))
    if name == "letter1": return cam(on_desk(paper(L1, line_progress(name, t)), -2.5, 420), p, M)
    if name == "letter2": return cam(on_desk(paper(L2, line_progress(name, t), highlight=("sangre",)), 2, 480), p, M)
    if name == "letter_close": return cam(LETTER_C, p, M)
    if name == "wall":
        img = to_img(BG["wall"]); d = ImageDraw.Draw(img)
        cracks(d, 77, 650, 1050, int(3 + 6 * p), length=300 + 500 * p)
        return cam(img, p, M)
    fn = {"mailbox": mailbox, "price": price, "kids_room": kids_room, "generations": generations, "street_cars": street_cars,
          "windows_watch": windows_watch, "signature": signature, "poll": poll, "letters_pile": letters_pile,
          "case_file": case_file, "sold": sold, "watcher_street": watcher_street, "end_card": end_card}.get(name)
    if fn: return cam(fn(t, p), p, M)
    if name in BG and BG[name] is not None: return cam(BG[name], p, M)
    raise KeyError(name)

SHOTS = shot_timeline()
CAPS = caption_timeline()
HITS = [0.05, scene_start("kids_room"), scene_start("wall"), scene_start("signature"), scene_start("case_file"), scene_start("end_card")]

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
