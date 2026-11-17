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

# ---------------------------------------------------------------- planos (albedo + luz)
def sky_night():
    a = grad((4, 7, 16), (22, 30, 44), power=1.4)
    st = rng.random((BH, BW)) > 0.9992; a[st] = 200
    m = radial(1000, 360, 90) * 1.0 + radial(1000, 360, 300) * 0.25
    a += m[..., None] * np.array([190, 200, 215])
    return a

def house_albedo():
    a = sky_night()
    img = to_img(a); d = ImageDraw.Draw(img)
    # postes y cables
    for x in (120, 1180):
        d.rectangle([x - 10, 500, x + 10, 1900], fill=(8, 9, 12))
        d.rectangle([x - 70, 560, x + 70, 575], fill=(8, 9, 12))
    for k in range(3):
        pts = [(x, 590 + k * 25 + 80 * math.sin(math.pi * (x - 120) / 1060)) for x in range(120, 1181, 20)]
        d.line(pts, fill=(10, 11, 14), width=3)
    # casa japonesa de dos plantas
    body = (26, 28, 34)
    d.rectangle([230, 1050, 1070, 1850], fill=body)
    d.polygon([(170, 1060), (650, 820), (1130, 1060)], fill=(16, 17, 22))            # tejado
    d.polygon([(190, 1440), (1110, 1440), (1070, 1380), (230, 1380)], fill=(16, 17, 22))  # alero
    for wx, wy in [(330, 1150), (780, 1150), (330, 1530)]:
        d.rectangle([wx, wy, wx + 190, wy + 170], fill=(12, 13, 16))
        d.line([wx + 95, wy, wx + 95, wy + 170], fill=(30, 32, 38), width=6)
    d.rectangle([760, 1520, 960, 1850], fill=(14, 15, 19))  # puerta
    d.rectangle([0, 1850, BW, BH], fill=(12, 12, 14))       # calle
    d.rectangle([150, 1700, 230, 1860], fill=(20, 20, 24))  # muro bajo
    return arr(img)

def house(lightwin=True, police=None):
    a = house_albedo()
    if lightwin:
        win = np.zeros((BH, BW)); win[1530:1700, 330:520] = 1
        a += win[..., None] * np.array([200, 150, 80])
        a += radial(425, 1615, 160)[..., None] * np.array([90, 60, 25]) * 0.5
    fog = noise_tex(BW, BH, 120, 3) * np.clip((YY - 1300) / 900, 0, 1)
    a += fog[..., None] * np.array([40, 46, 56])
    if police is not None:
        r, b = police
        a += radial(300, 1900, 700)[..., None] * np.array([255, 20, 30]) * r * 0.9
        a += radial(1000, 1900, 700)[..., None] * np.array([20, 70, 255]) * b * 0.9
    return a

def man_table():
    a = room((70, 66, 58), (60, 44, 30), (40, 38, 34), seed=2, tatami=True)
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([380, 1600, 920, 1660], fill=(50, 32, 20))            # mesa baja
    d.rectangle([410, 1660, 440, 1760], fill=(40, 26, 16)); d.rectangle([860, 1660, 890, 1760], fill=(40, 26, 16))
    d.ellipse([600, 1570, 700, 1610], fill=(220, 215, 200))           # cuenco
    # silueta de espaldas
    d.ellipse([560, 1180, 760, 1400], fill=(6, 6, 8))
    d.rounded_rectangle([440, 1370, 880, 2000], 150, fill=(6, 6, 8))
    d.line([650, 0, 650, 900], fill=(20, 20, 20), width=4)           # cable de la lámpara
    d.polygon([(560, 900), (740, 900), (690, 830), (610, 830)], fill=(40, 34, 26))
    a = arr(img)
    L = 0.06 + radial(650, 960, 380) * 1.3 + cone(650, 900, math.pi / 2, 0.6, 900) * 0.9
    out = lit(a, L)
    out += radial(650, 905, 40)[..., None] * 255
    return out

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

def fridge_shelf():
    a = grad((210, 222, 228), (170, 185, 195))
    img = to_img(a); d = ImageDraw.Draw(img)
    for yy in (700, 1300, 1900):
        d.rectangle([0, yy, BW, yy + 26], fill=(150, 170, 180))
    r = np.random.default_rng(8)
    for row, base in enumerate((700, 1300, 1900)):
        x = 60
        while x < BW - 150:
            w_ = r.uniform(130, 230); h_ = r.uniform(200, 420)
            if r.random() < 0.28:   # hueco: falta algo
                d.rectangle([x, base - h_, x + w_, base], outline=(120, 135, 145), width=5)
            else:
                c = tuple(int(v) for v in r.choice([(200, 60, 50), (240, 230, 200), (60, 120, 70), (230, 200, 90), (90, 60, 160), (220, 220, 230)]))
                d.rounded_rectangle([x, base - h_, x + w_, base], 20, fill=c)
            x += w_ + r.uniform(30, 70)
    a = arr(img)
    return a * (0.55 + 0.6 * radial(650, 1100, 800))[..., None]

def camera_wall():
    a = grad((48, 46, 44), (30, 29, 28)) * (0.85 + 0.3 * noise_tex(BW, BH, 4, 7)[..., None])
    img = to_img(a); d = ImageDraw.Draw(img)
    d.line([0, 700, BW, 640], fill=(20, 20, 20), width=6)           # esquina techo
    d.rectangle([600, 760, 700, 900], fill=(200, 200, 200))         # soporte
    d.polygon([(540, 880), (900, 980), (880, 1180), (520, 1060)], fill=(225, 225, 222))  # cuerpo
    d.polygon([(880, 980), (960, 1010), (950, 1190), (880, 1180)], fill=(160, 160, 158))
    d.ellipse([835, 1020, 985, 1170], fill=(20, 20, 24)); d.ellipse([870, 1055, 950, 1135], fill=(40, 60, 90))
    d.ellipse([893, 1070, 913, 1090], fill=(200, 220, 255))
    return arr(img)

def phone(screen_fn, t, p):
    a = grad((8, 9, 14), (3, 3, 6))
    a += radial(650, 1150, 500)[..., None] * np.array([20, 30, 50])
    img = to_img(a); d = ImageDraw.Draw(img)
    px0, py0, px1, py1 = 290, 520, 1010, 1920
    d.rounded_rectangle([px0 - 18, py0 - 18, px1 + 18, py1 + 18], 90, fill=(25, 25, 28))
    d.rounded_rectangle([px0, py0, px1, py1], 75, fill=(6, 8, 12))
    screen_fn(d, img, (px0, py0, px1, py1), t, p)
    # mano (silueta)
    d.rounded_rectangle([180, 1500, 420, 2310], 120, fill=(14, 11, 10))
    d.rounded_rectangle([900, 1300, 1080, 1420], 60, fill=(14, 11, 10))
    d.rounded_rectangle([920, 1450, 1110, 1570], 60, fill=(14, 11, 10))
    out = arr(img)
    glow = np.zeros((BH, BW)); glow[py0:py1, px0:px1] = 1
    g = arr(to_img(glow[..., None] * np.array([60, 80, 110])).filter(ImageFilter.GaussianBlur(90)))
    return out + g * 0.8

def screen_idle(d, img, box, t, p):
    x0, y0, x1, y1 = box
    sub = to_img(grad((20, 30, 60), (60, 30, 70), w=x1 - x0, h=y1 - y0))
    img.paste(sub, (x0, y0), rounded_mask(x1 - x0, y1 - y0, 75))
    tc = "13:58"
    w = d.textlength(tc, font=F_BIG)
    d.text(((x0 + x1 - w) / 2 * 1 + 0, y0 + 160), tc, font=ImageFont.truetype(FONT, 200), fill=(240, 240, 250))
    # icono app cámara
    d.rounded_rectangle([x0 + 70, y1 - 360, x0 + 230, y1 - 200], 40, fill=(30, 30, 34))
    d.ellipse([x0 + 115, y1 - 315, x0 + 185, y1 - 245], fill=(80, 140, 230))
    d.text((x0 + 70, y1 - 180), "CÁMARA", font=F_XS, fill=(230, 230, 235))

def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); return m

def screen_alert(d, img, box, t, p):
    screen_idle(d, img, box, t, p)
    x0, y0, x1, y1 = box
    k = min(1, p / 0.15); yoff = int(-200 * (1 - k))
    d.rounded_rectangle([x0 + 40, y0 + 470 + yoff, x1 - 40, y0 + 980 + yoff], 40, fill=(245, 245, 248))
    d.text((x0 + 80, y0 + 500 + yoff), "CÁMARA SALÓN · ahora", font=F_XS, fill=(110, 110, 120))
    d.text((x0 + 80, y0 + 550 + yoff), "Movimiento detectado", font=ImageFont.truetype(FONT, 50), fill=(15, 15, 20))
    th = cctv_frame(t, figure=True, size=(x1 - x0 - 160, 300), plain=True)
    img.paste(th, (x0 + 80, y0 + 640 + yoff))

def cctv_frame(t, figure=True, size=(W, H), plain=False, zoom=1.0):
    base = CCTV_BASE
    if figure:
        base = base.copy(); d = ImageDraw.Draw(base, "RGBA")
        u = ((t - scene_start("phone_alert")) * 0.09) % 1.0
        fx = 520 + 260 * u; fy = 1180
        sil = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); ds = ImageDraw.Draw(sil)
        ds.ellipse([fx - 45, fy - 330, fx + 45, fy - 220], fill=(5, 5, 5, 235))
        ds.rounded_rectangle([fx - 80, fy - 230, fx + 80, fy + 90], 60, fill=(5, 5, 5, 235))
        ds.rectangle([fx - 60, fy + 60, fx - 15, fy + 320], fill=(5, 5, 5, 235))
        ds.rectangle([fx + 15, fy + 60, fx + 60, fy + 320], fill=(5, 5, 5, 235))
        sil = sil.filter(ImageFilter.GaussianBlur(6))
        base.paste(sil, (0, 0), sil)
    if zoom != 1.0:
        cw, ch = BW / zoom, BH / zoom; cx = min(max(690, cw / 2), BW - cw / 2); cy = min(max(1050, ch / 2), BH - ch / 2)
        base = base.resize(size, Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    else:
        base = base.resize(size, Image.BILINEAR)
    a = arr(base)
    sw, shh = size
    a += np.random.default_rng(int(t * 30)).standard_normal((shh, sw, 1)) * 18
    a[::4] *= 0.8
    img = to_img(a)
    if not plain:
        d = ImageDraw.Draw(img)
        d.text((60, 290), "CAM 01  SALÓN", font=F_MONO, fill=(230, 230, 230))
        secs = 14 * 3600 + 32 * 60 + int(t * 1) % 60
        d.text((60, 1600), f"2008-05-XX  {secs // 3600:02}:{secs // 60 % 60:02}:{secs % 60:02}", font=F_MONO, fill=(230, 230, 230))
        if int(t * 2) % 2 == 0:
            d.ellipse([880, 295, 920, 335], fill=RED)
        d.text((935, 290), "REC", font=F_MONO, fill=(230, 230, 230))
    return img

def build_cctv_base():
    a = room((150, 150, 145), (110, 100, 90), (120, 120, 118), seed=9, tatami=True)
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([420, 860, 620, 1460], fill=(170, 165, 150))                 # fusuma
    d.rectangle([620, 860, 820, 1460], fill=(160, 155, 140))
    d.line([420, 1160, 820, 1160], fill=(90, 85, 75), width=6)
    d.rectangle([940, 1500, 1200, 1700], fill=(60, 50, 40))                  # mueble
    d.rectangle([150, 1650, 420, 1720], fill=(70, 55, 40))                   # mesa
    a = arr(img)
    lum = a.mean(2, keepdims=True)
    a = np.repeat(lum, 3, 2) * np.array([0.85, 1.0, 0.9]) * (0.55 + 0.5 * radial(650, 1100, 900))[..., None]
    return to_img(a)

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

def oshiire(open_=0.0, top=False):
    """Armario japonés (oshiire) con puertas correderas; open_ 0..1."""
    a = grad((60, 52, 44), (38, 33, 28)) * (0.85 + 0.3 * noise_tex(BW, BH, 5, 12)[..., None])
    img = to_img(a); d = ImageDraw.Draw(img)
    X0, Y0, X1, Y1 = 150, 330, 1150, 2050; MID = 1150
    d.rectangle([X0 - 30, Y0 - 30, X1 + 30, Y1 + 30], fill=(40, 28, 18))
    d.rectangle([X0, Y0, X1, Y1], fill=(4, 4, 5))                         # interior oscuro
    if top or open_ > 0:
        # balda y futón en el hueco superior
        d.rectangle([X0, MID - 20, X1, MID + 30], fill=(70, 50, 32))
        d.rounded_rectangle([X0 + 60, MID - 230, X1 - 120, MID - 20], 60, fill=(150, 140, 125))
        d.rounded_rectangle([X0 + 80, MID - 300, X0 + 330, MID - 200], 40, fill=(170, 165, 150))  # almohada
        for k in range(4):
            bx = X1 - 110 - k * 55
            d.rounded_rectangle([bx, MID - 200, bx + 40, MID - 20], 12, fill=(110, 140, 150))  # botellas
        # silueta acurrucada al fondo, casi invisible
        d.ellipse([X0 + 420, MID - 360, X0 + 640, MID - 160], fill=(10, 10, 12))
    # puertas correderas (fusuma) — la derecha se desliza a la izquierda
    pw = (X1 - X0) / 2
    slide = open_ * pw * 0.95
    for k, xoff in enumerate((0, pw - slide)):
        x = X0 + xoff
        d.rectangle([x, Y0, x + pw, Y1], fill=(200, 190, 165) if k == 0 else (190, 180, 155), outline=(60, 40, 25), width=10)
        d.line([x, MID, x + pw, MID], fill=(150, 140, 120), width=4)
        d.ellipse([x + (pw - 70 if k == 0 else 30), (Y0 + Y1) / 2 - 30, x + (pw - 10 if k == 0 else 90), (Y0 + Y1) / 2 + 30], fill=(80, 60, 40))
    if open_ == 0 and not top:      # rendija oscura
        d.rectangle([X0 + pw - 6, Y0 + 10, X0 + pw + 22, Y1 - 10], fill=(2, 2, 3))
    a = arr(img)
    tex = noise_tex(BW, BH, 3, 13) * 0.15 + 0.92
    return a * tex[..., None]

def closet_light(a, t, mode):
    if mode == "gap":
        L = 0.08 + radial(650, 1000, 700) * 0.55
    elif mode == "flash":
        L = 0.05 + radial(860 + 70 * math.sin(t * 1.7), 960, 300) * 1.3 + radial(650, 1100, 900) * 0.15
    else:
        L = 0.05 + radial(650, 1000, 420) * 1.3
    return grade(lit(a, L), (6, 14, 30))

def futon_close(t):
    a = grad((25, 22, 20), (8, 7, 7))
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rounded_rectangle([-100, 1300, 1400, 2000], 120, fill=(160, 150, 135))
    for k in range(9):
        d.line([0, 1360 + k * 70, BW, 1340 + k * 72], fill=(135, 125, 110), width=5)
    d.rounded_rectangle([90, 1150, 560, 1400], 80, fill=(185, 180, 165))
    for k in range(3):
        bx = 780 + k * 150
        d.rounded_rectangle([bx, 950, bx + 100, 1360], 30, fill=(120, 150, 160))
        d.rectangle([bx + 30, 900, bx + 70, 960], fill=(40, 90, 160))
    d.rectangle([0, 700, BW, 740], fill=(60, 45, 30))
    a = arr(img)
    L = 0.04 + radial(560 + 120 * math.sin(t * 0.9), 1300, 420) * 1.6
    return grade(lit(a, L))

def door_frame(gap):
    a = grad((30, 26, 22), (18, 15, 13))
    img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([300, 300, 1000, 2000], fill=(50, 38, 28))
    d.rectangle([340, 340, 960, 2000], fill=(0, 0, 0))
    gw = int(560 * gap)
    d.rectangle([340, 340, 960 - gw, 2000], fill=(75, 58, 42))
    d.ellipse([880 - gw - 60, 1160, 920 - gw - 60, 1200], fill=(170, 150, 90))
    d.rectangle([0, 2000, BW, BH], fill=(60, 50, 40))
    a = arr(img)
    out = grade(a * 0.7)
    if gw > 0:
        light = np.zeros((BH, BW)); light[340:2000, 960 - gw:960] = 1
        out += light[..., None] * np.array([220, 200, 160])
        out += cone(960 - gw / 2, 1200, math.pi / 2 + 0.6, 0.35, 900)[..., None] * np.array([120, 100, 70]) * min(1, gap * 8)
    return out

def case_file(t, p):
    a = grad((40, 32, 25), (22, 18, 14)) * (0.8 + 0.4 * noise_tex(BW, BH, 3, 21)[..., None])
    img = to_img(a)
    pap = Image.new("RGBA", (900, 1250), (232, 225, 205, 255)); d = ImageDraw.Draw(pap)
    d.text((60, 60), "INFORME POLICIAL", font=F_MED, fill=(20, 20, 20))
    d.text((60, 170), "Prefectura de Fukuoka · Mayo 2008", font=F_XS, fill=(60, 60, 60))
    r = np.random.default_rng(5)
    for k in range(13):
        y = 280 + k * 62; w_ = r.uniform(380, 760)
        d.rectangle([60, y, 60 + w_, y + 22], fill=(110, 105, 95) if k % 4 else (15, 15, 15))
    d.text((60, 1100), "Mujer, 58 años · sin domicilio", font=F_XS, fill=(40, 40, 40))
    pap = pap.rotate(-4, expand=True, resample=Image.BICUBIC)
    img.paste(pap, (180, 450), pap)
    if p > 0.3:
        k = min(1, (p - 0.3) / 0.08); sc = 1 + 1.5 * (1 - k)
        st = Image.new("RGBA", (900, 260), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle([10, 10, 890, 250], 20, outline=RED + (230,), width=14)
        f = ImageFont.truetype(FONT, 54)
        for i, s in enumerate(["DETENIDA POR", "ALLANAMIENTO DE MORADA"]):
            w_ = ds.textlength(s, font=f); ds.text(((900 - w_) / 2, 40 + i * 95), s, font=f, fill=RED + (230,))
        st = st.rotate(9, expand=True).resize((int(st.width * sc * 1.0), int(st.height * sc * 1.0)))
        img.paste(st, (650 - st.width // 2, 1020 - st.height // 2), st)
    a = arr(img)
    return a * (0.35 + 0.9 * radial(650, 1150, 750))[..., None]

def counter(img, p, target, unit, sub, color=BONE, prefix=""):
    d = ImageDraw.Draw(img, "RGBA")
    v = target * min(1, p / 0.5) ** 0.5
    s = prefix + str(int(round(v)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    tw = dl.textlength(s, font=F_BIG); dl.text(((W - tw) / 2, 300), s, font=F_BIG, fill=color + (255,))
    tw = dl.textlength(unit, font=F_MED); dl.text(((W - tw) / 2, 650), unit, font=F_MED, fill=(255, 255, 255, 255))
    g = lay.filter(ImageFilter.GaussianBlur(30))
    img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
    tw = d.textlength(sub, font=F_SM); d.text(((W - tw) / 2, 780), sub, font=F_SM, fill=(200, 200, 205))

# ---------------------------------------------------------------- precálculo
print("fondos…", flush=True)
CCTV_BASE = build_cctv_base()
BG = {
    "house_ext": house(), "man_table": man_table(), "fridge": fridge(), "fridge_shelf": fridge_shelf(),
    "camera": camera_wall(),
    "closet_gap": closet_light(oshiire(0), 0, "gap"),
    "closet_closed": closet_light(oshiire(0), 0, "gap"),
    "futon_base": None,
}
HOUSE_DARK = house(lightwin=True)
OSH_TOP = oshiire(1.0, True)
BLUR_CLOSET = to_img(BG["closet_gap"]).filter(ImageFilter.GaussianBlur(14))
GRAIN = [rng.standard_normal((H // 2, W // 2)) * 9 for _ in range(4)]
yy, xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1.2 - (((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2) * 0.75, 0.15, 1)[..., None]

MODES = {  # zoom inicio, zoom fin, paneo x, paneo y
    "house_ext": (1.0, 1.18, 0.3, 0.2), "man_table": (1.05, 1.25, 0, -0.2), "fridge": (1.0, 1.22, 0, 0),
    "fridge_shelf": (1.15, 1.0, -0.6, 0), "camera": (1.1, 1.35, 0.4, 0.1), "closet_gap": (1.0, 1.3, 0, 0),
    "closet_closed": (1.0, 1.12, 0, 0), "police": (1.0, 1.1, -0.2, 0), "hallway": (1.0, 1.35, 0, -0.2),
    "closet_open": (1.0, 1.08, 0, 0), "closet_top": (1.25, 1.45, 0, -0.5), "futon": (1.0, 1.2, 0.4, 0),
    "door": (1.0, 1.2, 0.3, 0), "door_close": (1.1, 1.25, 0.3, 0), "case_file": (1.15, 1.0, 0, 0.2),
    "phone_idle": (1.0, 1.08, 0, 0), "phone_alert": (1.0, 1.15, 0, -0.2), "end_card": (1.1, 1.5, 0, 0),
}

def cam(bg, p, mode):
    if not isinstance(bg, Image.Image): bg = to_img(bg)
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * (p * p * (3 - 2 * p) * 0.5 + p * 0.5)
    cw, ch = BW / z, BH / z
    cx = BW / 2 + dx * (p - 0.5) * (BW - cw); cy = BH / 2 + dy * (p - 0.5) * (BH - ch)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    M = MODES.get(name, (1.0, 1.1, 0, 0))
    if name == "cctv_hook":
        img = cctv_frame(t + 3, figure=False)
        if 0.35 < p < 0.6:   # una sombra cruza durante un instante
            d = ImageDraw.Draw(img, "RGBA"); x = 300 + (p - 0.35) / 0.25 * 600
            d.rounded_rectangle([x - 60, 820, x + 60, 1300], 50, fill=(0, 0, 0, 150))
        return img
    if name in ("cctv_figure", "cctv_zoom"):
        return cctv_frame(t, True, zoom=1.0 if name == "cctv_figure" else 1.0 + 0.9 * p)
    if name in ("phone_idle", "phone_alert"):
        return cam(phone(screen_idle if name == "phone_idle" else screen_alert, t, p), p, M)
    if name == "police":
        r = 0.5 + 0.5 * math.sin(t * 9); bl = 0.5 + 0.5 * math.sin(t * 9 + math.pi)
        return cam(house(True, (r, bl)), p, M)
    if name == "hallway": return cam(hallway(t, p), p, M)
    if name == "closet_open":
        o = min(1, p / 0.7) ** 0.7
        return cam(closet_light(oshiire(o, True), t, "flash"), p, M)
    if name == "closet_top": return cam(closet_light(OSH_TOP, t, "flash"), p, M)
    if name == "futon": return cam(futon_close(t), p, M)
    if name in ("door", "door_close"):
        g = 0.25 if name == "door" else 0.25 * max(0, 1 - p / 0.7)
        return cam(door_frame(g), p, M)
    if name == "case_file": return cam(case_file(t, p), p, M)
    if name == "stat_58":
        img = to_img(arr(cam(BLUR_CLOSET, p, (1.2, 1.3, 0, 0))) * 0.6)
        counter(img, p, 58, "AÑOS", "ENCONTRADA EN EL ARMARIO"); return img
    if name == "stat_year":
        img = to_img(arr(cam(to_img(futon_close(t)).filter(ImageFilter.GaussianBlur(14)), p, (1.1, 1.2, 0, 0))) * 0.55)
        counter(img, p, 12, "MESES", "CERCA DE UN AÑO ESCONDIDA", BONE, "~")
        d = ImageDraw.Draw(img, "RGBA")
        ang = 360 * min(1, p / 0.5) * 0.97
        d.arc([290, 1000, 790, 1500], -90, -90 + ang, fill=RED + (255,), width=24)
        d.arc([290, 1000, 790, 1500], -90 + ang, 270, fill=(255, 255, 255, 40), width=24)
        return img
    if name == "end_card":
        img = cam(BG["closet_gap"], p, M)
        img = to_img(arr(img) * (1 - 0.55 * min(1, p * 2)))
        d = ImageDraw.Draw(img, "RGBA")
        if p > 0.12:
            for i, (s, c) in enumerate([("¿Y TÚ?", RED), ("COMENTA LO MÁS", (255, 255, 255)), ("RARO QUE TE HA", (255, 255, 255)), ("PASADO EN CASA", (255, 255, 255))]):
                f = F_MED if i else ImageFont.truetype(FONT, 130)
                tw = d.textlength(s, font=f); d.text(((W - tw) / 2, 260 + (i and 140 + (i - 1) * 100)), s, font=f, fill=c, stroke_width=6, stroke_fill=(0, 0, 0))
        return img
    if name in BG and BG[name] is not None: return cam(BG[name], p, M)
    raise KeyError(name)

SHOTS = shot_timeline()
CAPS = caption_timeline()
HITS = [0.05, scene_start("phone_alert") + 0.1, scene_start("closet_closed") + 2.45, scene_start("stat_58"), scene_start("case_file") + 0.75]

def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, s = cur[0]
    age = t - a
    sc = 0.8 + 0.2 * min(1, age / 0.1) + 0.05 * math.sin(min(1, age / 0.1) * math.pi)
    parts = []
    for k, seg in enumerate(s.split("*")):
        for w in seg.split():
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
