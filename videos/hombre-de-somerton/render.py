import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, TOTAL, caption_timeline, shot_timeline, hits, caption_start

W, H, FPS = 1080, 1920, 30
BW, BH = 1300, 2310
rng = np.random.default_rng(48)
FD = "/usr/share/fonts/"
FONT = FD + "opentype/inter/Inter-Black.otf"
SERIF_I = FD + "truetype/liberation/LiberationSerif-Italic.ttf"
SERIF_B = FD + "truetype/liberation/LiberationSerif-Bold.ttf"
MONO = FD + "truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_CAP = ImageFont.truetype(FONT, 100)
F_BIG = ImageFont.truetype(FONT, 330)
F_MED = ImageFont.truetype(FONT, 88)
F_SM = ImageFont.truetype(FONT, 50)
F_TY = ImageFont.truetype(MONO, 48)
F_PEN = ImageFont.truetype(SERIF_I, 92)
RED = (232, 36, 36); AMBER = (255, 190, 90); PAPER = ((222, 210, 180), (190, 172, 135))

# ---------------------------------------------------------------- utilidades
def grad(c1, c2, w=BW, h=BH, power=1.0):
    y = (np.linspace(0, 1, h) ** power)[:, None, None]
    a = np.array(c1, float); b = np.array(c2, float)
    return np.broadcast_to(a + (b - a) * y, (h, w, 3)).copy()
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def noise_tex(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((h // scale + 2, w // scale + 2))
    return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), float) / 255
def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def text_c(d, y, s, font, fill, stroke=0, sc=(0, 0, 0), x=None):
    w = d.textlength(s, font=font)
    d.text(((W - w) / 2 if x is None else x - w / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)
def paste_glow(img, lay, r=22):
    g = lay.filter(ImageFilter.GaussianBlur(r)); img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
def cam(bg, p, mode):
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * (ease(p) * 0.5 + p * 0.5)
    cw, ch = bg.width / z * (W / BW) * (BW / W), bg.height / z
    cw = bg.width / z; ch = bg.height / z
    cx = bg.width / 2 + dx * (p - 0.5) * (bg.width - cw); cy = bg.height / 2 + dy * (p - 0.5) * (bg.height - ch)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
def light(arr, x, y, rx, ry, col, k=1.0):
    yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]
    l = np.exp(-(((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2)) * k
    return arr * (1 + 0.8 * l[..., None]) + l[..., None] * np.array(col, float)
def paper_tex(w, h, seed, c=PAPER):
    a = grad(c[0], c[1], w, h)
    a *= (0.9 + 0.16 * noise_tex(w, h, 4, seed) + 0.12 * noise_tex(w, h, 90, seed + 1))[..., None]
    return a

# ---------------------------------------------------------------- playa de Somerton
def bg_beach(fog=False):
    a = grad((4, 10, 18), (40, 52, 60), power=1.3)
    a[:1200] = grad((4, 10, 18), (60, 58, 62), BW, 1200, 1.6)
    st = rng.random((BH, BW)) > 0.9992; st[1150:] = False; a[st] = 210
    img = to_img(a); d = ImageDraw.Draw(img)
    # mar
    d.rectangle([0, 1150, BW, 1500], fill=(16, 26, 34))
    for k in range(60):
        y = 1160 + (k ** 1.4) * 1.6; x = rng.uniform(-100, BW)
        d.line([x, y, x + rng.uniform(60, 260), y], fill=(70, 90, 105), width=2)
    # arena
    sand = to_img(grad((96, 86, 72), (60, 52, 44), BW, BH - 1500) * (0.85 + 0.25 * noise_tex(BW, BH - 1500, 3, 4))[..., None])
    img.paste(sand, (0, 1500))
    d = ImageDraw.Draw(img)
    for k in range(7):  # orilla
        y = 1495 + k * 6; d.line([0, y + 20 * math.sin(k), BW, y], fill=(150, 160, 160), width=2)
    # malecón de piedra a la derecha
    d.polygon([(860, 1180), (BW, 1150), (BW, 2310), (1040, 2310)], fill=(58, 56, 54))
    for r in range(18):
        y = 1200 + r * 62
        for c in range(4):
            x = 880 + (y - 1180) * 0.16 + c * 110 + (r % 2) * 55
            d.rectangle([x, y, x + 100, y + 56], outline=(38, 36, 34), width=4)
    # farola
    d.line([1200, 1150, 1200, 520], fill=(20, 20, 22), width=14); d.line([1200, 530, 1110, 530], fill=(20, 20, 22), width=10)
    d.ellipse([1085, 520, 1135, 560], fill=(255, 220, 150))
    arr = light(np.asarray(img, float), 1110, 900, 380, 700, (60, 45, 20), 0.9)
    if fog:
        arr = arr * 0.85 + np.array([20, 24, 28])
    return to_img(arr)

def man_lying(d, x, y, s, col=(14, 14, 18)):
    """Silueta de hombre recostado contra el muro, piernas estiradas y cruzadas."""
    d.ellipse([x - 0.13 * s, y - 0.72 * s, x + 0.13 * s, y - 0.44 * s], fill=col)                # cabeza
    d.polygon([(x - 0.2 * s, y - 0.46 * s), (x + 0.22 * s, y - 0.46 * s), (x + 0.15 * s, y), (x - 0.35 * s, y + 0.02 * s)], fill=col)  # torso
    d.polygon([(x - 0.35 * s, y - 0.05 * s), (x + 0.1 * s, y - 0.05 * s), (x - 1.3 * s, y + 0.12 * s), (x - 1.3 * s, y + 0.03 * s)], fill=col)
    d.polygon([(x - 0.3 * s, y + 0.02 * s), (x + 0.12 * s, y), (x - 1.25 * s, y + 0.2 * s), (x - 1.28 * s, y + 0.1 * s)], fill=col)
    d.ellipse([x - 1.42 * s, y + 0.04 * s, x - 1.24 * s, y + 0.2 * s], fill=col)                # zapatos
    d.line([x + 0.05 * s, y - 0.42 * s, x - 0.3 * s, y - 0.12 * s], fill=(40, 40, 46), width=int(s * 0.05))  # brazo

# ---------------------------------------------------------------- telas, etiqueta, bolsillo
def bg_wool(seed=1, base=((44, 42, 48), (30, 28, 34))):
    a = grad(*base)
    yy, xx = np.mgrid[0:BH, 0:BW]
    a += ((np.sin((xx + yy) * 0.7) * np.sin((xx - yy) * 0.7)) * 7)[..., None]
    a *= (0.85 + 0.3 * noise_tex(BW, BH, 40, seed))[..., None]
    return to_img(a)
def label_frame(t, p):
    img = cam(BG["wool"], p, (1.0, 1.1, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.line([0, 760, W, 700], fill=(70, 66, 72), width=10)       # costura del cuello
    pull = ease((p - 0.25) / 0.45)
    # agujeritos de las puntadas que quedan
    for k in range(18):
        x = 300 + k * 27
        d.ellipse([x - 4, 836, x + 4, 844], fill=(10, 10, 12)); d.ellipse([x - 4, 1086, x + 4, 1094], fill=(10, 10, 12))
    lab = Image.new("RGBA", (520, 280), (0, 0, 0, 0)); dl = ImageDraw.Draw(lab)
    dl.rectangle([0, 0, 519, 279], fill=(232, 226, 210, 255))
    dl.rectangle([14, 14, 505, 265], outline=(150, 40, 40, 255), width=6)
    f1 = ImageFont.truetype(SERIF_B, 64); f2 = ImageFont.truetype(SERIF_I, 44)
    dl.text((260 - dl.textlength("TAILORED", font=f1) / 2, 60), "TAILORED", font=f1, fill=(120, 30, 30, 255))
    dl.text((260 - dl.textlength("in Australia", font=f2) / 2, 150), "in Australia", font=f2, fill=(80, 40, 40, 255))
    lab = lab.rotate(-pull * 40, expand=True, resample=Image.BICUBIC)
    lx = 290 + pull * 700; ly = 830 - pull * 900
    if pull < 1: img.paste(lab, (int(lx), int(ly)), lab)
    if 0.25 < p < 0.75:   # pellizco de dedos
        d.ellipse([lx + 380 - 60, ly + 60, lx + 380 + 60, ly + 200], fill=(200, 160, 130, 255))
    if pull > 0.95:
        text_c(d, 1600, "SIN ETIQUETAS", F_SM, RED, 5)
    return img

def bg_trousers(): return bg_wool(3, ((54, 50, 44), (36, 33, 30)))
def pocket_frame(t, p):
    img = cam(BG["trousers"], p, (1.05, 1.2, 0, -0.2))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([230, 520, 850, 600], 30, fill=(12, 11, 10))            # abertura del bolsillo
    d.line([230, 600, 850, 600], fill=(90, 84, 74), width=6)
    up = ease(p / 0.35); unroll = ease((p - 0.3) / 0.35)
    # papelito: primero enrollado saliendo, luego desplegado
    w = 120 + unroll * 640; h = 120 if unroll < 0.05 else 120 + unroll * 140
    cx = 540; cy = 560 - up * 200 + unroll * 420
    pa = to_img(paper_tex(int(w), int(h), 7, ((236, 228, 205), (215, 205, 178)))).convert("RGBA")
    dp = ImageDraw.Draw(pa)
    if unroll > 0.6:
        f = ImageFont.truetype(SERIF_I, 100)
        a = int(255 * min(1, (unroll - 0.6) / 0.3))
        dp.text((w / 2 - dp.textlength("Tamám Shud", font=f) / 2, h / 2 - 62), "Tamám Shud", font=f, fill=(25, 20, 18, a))
    else:
        for k in range(6): dp.line([0, k * h / 6, w, k * h / 6 + 3], fill=(170, 160, 135), width=3)
    pa = pa.rotate(-4 + 4 * unroll, expand=True, resample=Image.BICUBIC)
    img.paste(pa, (int(cx - pa.width / 2), int(cy - pa.height / 2)), pa)
    return img

# ---------------------------------------------------------------- figura de traje
def suit_frame(t, p):
    a = grad((8, 8, 12), (20, 18, 22), W, H)
    a = light(a, W / 2, 700, 420, 900, (60, 50, 35), 1.0)
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    cx = W / 2; s = 1.0 + 0.08 * ease(p)
    col = (16, 16, 20)
    d.ellipse([cx - 120 * s, 420 - 300 * (s - 1), cx + 120 * s, 700], fill=(22, 20, 24))        # cabeza
    d.polygon([(cx - 60, 690), (cx + 60, 690), (cx + 70, 780), (cx - 70, 780)], fill=(22, 20, 24))  # cuello
    d.polygon([(cx - 380, 1900), (cx - 330, 880), (cx - 90, 760), (cx + 90, 760), (cx + 330, 880), (cx + 380, 1900)], fill=col)
    d.polygon([(cx - 70, 770), (cx + 70, 770), (cx, 1050)], fill=(225, 220, 210))                 # camisa
    d.polygon([(cx - 22, 790), (cx + 22, 790), (cx + 34, 1060), (cx, 1110), (cx - 34, 1060)], fill=(120, 24, 28))  # corbata
    d.polygon([(cx - 90, 760), (cx - 10, 1150), (cx - 150, 980)], fill=(30, 30, 36)); d.polygon([(cx + 90, 760), (cx + 10, 1150), (cx + 150, 980)], fill=(30, 30, 36))
    for k in range(2): d.ellipse([cx - 12, 1200 + k * 130, cx + 12, 1224 + k * 130], fill=(60, 60, 66))
    if p > 0.25:
        al = int(255 * min(1, (p - 0.25) / 0.2))
        text_c(d, 470, "?", ImageFont.truetype(FONT, 220), (232, 36, 36, al))
    return img

# ---------------------------------------------------------------- veneno e informe
def poison_frame(t, p):
    a = grad((10, 14, 12), (24, 30, 26), W, H); a = light(a, W / 2, 900, 400, 600, (30, 50, 30))
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    cx = W / 2
    d.rounded_rectangle([cx - 210, 620, cx + 210, 1300], 60, fill=(40, 70, 60, 230), outline=(140, 190, 170), width=6)
    d.rectangle([cx - 70, 460, cx + 70, 640], fill=(40, 70, 60, 230), outline=(140, 190, 170), width=6)
    d.rectangle([cx - 85, 400, cx + 85, 470], fill=(70, 50, 40))
    lvl = 820 + 40 * math.sin(t * 3)
    d.rounded_rectangle([cx - 196, lvl, cx + 196, 1286], 50, fill=(90, 200, 120, 160))
    d.rectangle([cx - 170, 860, cx + 170, 1120], fill=(225, 215, 190))
    text_c(d, 870, "☠", ImageFont.truetype(FD + "truetype/dejavu/DejaVuSans-Bold.ttf", 170), (20, 20, 20))
    text_c(d, 380, "?", ImageFont.truetype(FONT, 200), RED + (int(255 * ease(p / 0.4)),), 8)
    return img
def autopsy_frame(t, p):
    img = cam(BG["report"], p, (1.05, 1.15, 0, 0))
    d = ImageDraw.Draw(img)
    lines = ["INFORME FORENSE · 1948", "", "ESTÓMAGO .......... ?", "SANGRE ............ ?", "HÍGADO ............ ?", "",
             "VENENO:"]
    n = int(sum(len(l) for l in lines) * min(1, p / 0.55)); y = 330
    for l in lines:
        d.text((110, y), l[:max(0, n)], font=F_TY, fill=(30, 26, 22)); n -= len(l); y += 78
    if p > 0.62:
        st = Image.new("RGBA", (860, 200), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle([8, 8, 852, 192], 16, outline=(190, 25, 25, 230), width=12)
        fz = ImageFont.truetype(FONT, 104); ds.text((430 - ds.textlength("NO DETECTADO", font=fz) / 2, 38), "NO DETECTADO", font=fz, fill=(190, 25, 25, 220))
        sc = 1 + 1.2 * max(0, 1 - (p - 0.62) / 0.06)
        st = st.resize((int(860 * sc), int(200 * sc))).rotate(-8, expand=True)
        img.paste(st, (int(W / 2 - st.width / 2), int(1000 - st.height / 2)), st)
    return to_img(np.asarray(img, float) * 0.85)

# ---------------------------------------------------------------- libro y coche
def bg_book():
    a = grad((6, 6, 8), (18, 16, 16)); img = to_img(light(a, 650, 1150, 600, 800, (50, 40, 25)))
    d = ImageDraw.Draw(img)
    d.rectangle([300, 520, 1020, 1640], fill=(30, 58, 42)); d.rectangle([300, 520, 340, 1640], fill=(22, 44, 32))
    d.rectangle([370, 580, 980, 1580], outline=(196, 160, 80), width=6)
    f1 = ImageFont.truetype(SERIF_B, 86); f2 = ImageFont.truetype(SERIF_I, 60)
    for s, y, f in [("THE", 760, f2), ("RUBAIYAT", 840, f1), ("of", 960, f2), ("OMAR", 1040, f1), ("KHAYYAM", 1140, f1)]:
        d.text((660 - d.textlength(s, font=f) / 2, y), s, font=f, fill=(210, 175, 95))
    d.polygon([(1020, 1640), (900, 1640), (1020, 1520)], fill=(6, 6, 8))   # esquina arrancada
    return img
def car_frame(t, p):
    a = grad((4, 6, 12), (22, 22, 30), W, H)
    a = light(a, 860, 760, 360, 700, (70, 55, 25), 1.0)
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 1450, W, H], fill=(18, 18, 22))
    d.line([900, 1450, 900, 360], fill=(14, 14, 16), width=14); d.ellipse([870, 340, 930, 400], fill=(255, 220, 150))
    ox = 60 + p * 40; col = (10, 10, 14)
    body = [(ox, 1380), (ox + 40, 1250), (ox + 230, 1220), (ox + 330, 1080), (ox + 640, 1070), (ox + 760, 1200), (ox + 930, 1230),
            (ox + 960, 1380)]
    d.polygon(body, fill=col)
    d.polygon([(ox + 350, 1100), (ox + 470, 1095), (ox + 470, 1200), (ox + 300, 1205)], fill=(40, 46, 60))
    d.polygon([(ox + 490, 1095), (ox + 625, 1095), (ox + 720, 1200), (ox + 490, 1200)], fill=(40, 46, 60))
    for wx in (ox + 210, ox + 760):
        d.ellipse([wx - 95, 1290, wx + 95, 1480], fill=(6, 6, 8)); d.ellipse([wx - 40, 1345, wx + 40, 1425], fill=(70, 70, 76))
    # el libro en el asiento trasero, iluminado
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(g)
    pulse = 0.6 + 0.4 * math.sin(t * 5)
    dg.rectangle([ox + 380, 1160, ox + 450, 1200], fill=(196, 160, 80, int(255 * pulse)))
    paste_glow(img, g, 18)
    draw_rain(img, t)
    return img

# ---------------------------------------------------------------- teléfono y casa
def phone_frame(t, p):
    a = grad((14, 10, 8), (30, 22, 18), W, H); a = light(a, W / 2, 900, 500, 500, (40, 30, 20))
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    cx, cy, R = W / 2, 900, 380
    d.ellipse([cx - R - 30, cy - R - 30, cx + R + 30, cy + R + 30], fill=(14, 14, 16))
    rot = 0
    for k, (s, e) in enumerate([(0.05, 0.25), (0.3, 0.5), (0.55, 0.8)]):
        if s < p < e: rot = math.sin((p - s) / (e - s) * math.pi) * 150
    f = ImageFont.truetype(FONT, 60)
    for k in range(10):
        ang = math.radians(-60 - k * 28)
        hx = cx + R * 0.72 * math.cos(ang); hy = cy + R * 0.72 * math.sin(ang)
        d.text((hx - 18, hy - 34), str((k + 1) % 10), font=f, fill=(230, 225, 215))
    disk = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0)); dd = ImageDraw.Draw(disk)
    dd.ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=(28, 28, 32, 255))
    for k in range(10):
        ang = math.radians(-60 - k * 28)
        hx = R + R * 0.72 * math.cos(ang); hy = R + R * 0.72 * math.sin(ang)
        dd.ellipse([hx - 52, hy - 52, hx + 52, hy + 52], fill=(0, 0, 0, 0))
    dd.ellipse([R - 120, R - 120, R + 120, R + 120], fill=(225, 215, 190, 255))
    dd.text((R - dd.textlength("GLENELG", font=F_SM) / 2, R - 30), "GLENELG", font=F_SM, fill=(40, 30, 25, 255))
    disk = disk.rotate(-rot, resample=Image.BICUBIC)
    img.paste(disk, (int(cx - R), int(cy - R)), disk)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([cx + R * 0.9, cy + R * 0.2, cx + R * 1.05, cy + R * 0.45], fill=(200, 200, 205), width=14)   # tope
    return img
def bg_house():
    a = grad((4, 6, 14), (16, 20, 30)); img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([0, 1560, BW, BH], fill=(10, 12, 14))
    d.polygon([(220, 900), (650, 560), (1080, 900)], fill=(16, 16, 22))
    d.rectangle([260, 900, 1040, 1560], fill=(26, 26, 32))
    d.rectangle([340, 1020, 560, 1290], fill=(255, 196, 110))                    # ventana encendida
    d.rectangle([740, 1020, 960, 1290], fill=(14, 14, 18))
    d.rectangle([600, 1250, 700, 1560], fill=(14, 12, 12))
    for x in range(0, BW, 70): d.rectangle([x, 1440, x + 22, 1600], fill=(20, 20, 24))   # valla
    d.rectangle([0, 1470, BW, 1490], fill=(20, 20, 24))
    return img
def house_frame(t, p):
    img = cam(BG["house"], p, (1.05, 1.25, -0.3, 0.1))
    z = 1.05 + 0.2 * (ease(p) * 0.5 + p * 0.5); k = W / (BW / z)
    cx = BW / 2 - 0.3 * (p - 0.5) * (BW - BW / z); cy = BH / 2 + 0.1 * (p - 0.5) * (BH - BH / z)
    wx = (450 - cx) * k + W / 2; wy = (1155 - cy) * k + H / 2
    d = ImageDraw.Draw(img, "RGBA")
    if not (0.55 < p < 0.6):   # la cortina se mueve; una silueta
        sx = wx + 30 * math.sin(t * 1.5)
        d.ellipse([sx - 28 * k, wy - 80 * k, sx + 28 * k, wy - 25 * k], fill=(40, 25, 15, 200))
        d.polygon([(sx - 60 * k, wy + 135 * k), (sx + 60 * k, wy + 135 * k), (sx + 30 * k, wy - 25 * k), (sx - 30 * k, wy - 25 * k)], fill=(40, 25, 15, 200))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(g)
    dg.rectangle([wx - 110 * k, wy - 135 * k, wx + 110 * k, wy + 135 * k], fill=(255, 190, 100, 90))
    g = g.filter(ImageFilter.GaussianBlur(60)); img.paste(g, (0, 0), g)
    if p > 0.2:
        a = int(255 * min(1, (p - 0.2) / 0.2))
        text_c(d, 260, "A 400 M", F_MED, (255, 255, 255, a), 6); text_c(d, 370, "DE LA PLAYA", F_SM, RED + (a,), 5)
    draw_rain(img, t, 0.5)
    return img

# ---------------------------------------------------------------- el código
CODE = ["WRGOABABD", "MLIAOI", "WTBIMPANETP", "MLIABOAIAQC", "ITTMTSAMSTGAB"]
def bg_page():
    a = paper_tex(BW, BH, 21, ((214, 204, 176), (186, 170, 136)))
    yy, xx = np.mgrid[0:BH, 0:BW]
    a *= (1 - 0.35 * np.clip((np.abs(xx - BW / 2) / (BW / 2)) ** 4, 0, 1))[..., None]
    return to_img(a)
def code_lines(d, x0, y0, n, font, col, jitter_seed=3, step=150, strike_col=None):
    r = np.random.default_rng(jitter_seed)
    for li, line in enumerate(CODE):
        x = x0; y = y0 + li * step
        for ch in line:
            if n <= 0: return
            d.text((x + r.normal(0, 2), y + r.normal(0, 3)), ch, font=font, fill=col)
            x += d.textlength(ch, font=font) * 0.98; n -= 1
        if li == 1:   # la segunda línea está tachada en el original
            d.line([x0 - 10, y + 60, x + 10, y + 52], fill=strike_col or col, width=6)
def code_frame(t, p):
    img = cam(BG["page"], p, (1.0, 1.12, 0, -0.1))
    d = ImageDraw.Draw(img, "RGBA")
    n = int(sum(map(len, CODE)) * min(1, p / 0.8))
    code_lines(d, 90, 330, n, F_PEN, (70, 66, 64, 235))
    return img
def code_zoom_frame(t, p):
    img = cam(BG["page"], 0.5, (1.6, 1.8, 0, 0)).filter(ImageFilter.GaussianBlur(2))
    img = to_img(np.asarray(img, float) * 0.6)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(SERIF_I, 150)
    line = CODE[4]; r = np.random.default_rng(int(t * 12))
    solved = int(len(line) * 0.0)
    for row, ln in enumerate([CODE[0], CODE[2], CODE[4]]):
        s = "".join(ch if r.random() > 0.4 * max(0, 1 - p / 0.6) else chr(65 + r.integers(26)) for ch in ln)
        sc = min(1, (W - 80) / d.textlength(s, font=f))
        ff = ImageFont.truetype(SERIF_I, int(150 * sc))
        text_c(d, 380 + row * 230, s, ff, (40, 30, 30, 255) if row != 1 else RED + (255,))
    paste_glow(img, lay, 8)
    return img
def code_glow_frame(t, p):
    img = to_img(np.zeros((H, W, 3)) + 6)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fl = 0.7 + 0.3 * math.sin(t * 31) * math.sin(t * 13)
    code_lines(d, 90, 300 - p * 60, 999, F_PEN, (int(232 * fl), 36, 36, 255), strike_col=(120, 20, 20, 255))
    paste_glow(img, lay, 26); paste_glow(img, lay, 6)
    return img

# ---------------------------------------------------------------- ADN y nombre
def dna_frame(t, p):
    img = to_img(grad((2, 8, 18), (6, 20, 36), W, H))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(46):
        y = 120 + k * 40; ph = k * 0.38 + t * 2.2
        x1 = W / 2 + 260 * math.sin(ph); x2 = W / 2 - 260 * math.sin(ph); dep = math.cos(ph)
        d.line([x1, y, x2, y], fill=(120, 180, 255, 110), width=6)
        for x, dd in ((x1, dep), (x2, -dep)):
            r = 18 + 8 * dd; c = (90, 210, 255) if dd > 0 else (60, 120, 200)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (255,))
    paste_glow(img, lay, 18)
    return img
def name_frame(t, p):
    img = cam(BG["report"], p, (1.15, 1.25, 0, 0))
    d = ImageDraw.Draw(img)
    s = "CARL «CHARLES» WEBB"; n = int(len(s) * min(1, p / 0.35))
    d.text((110, 420), "IDENTIFICACIÓN (ADN):", font=F_TY, fill=(30, 26, 22))
    f = ImageFont.truetype(MONO, 70); d.text((110, 520), s[:n], font=f, fill=(20, 18, 16))
    d.text((110, 640), "Ingeniero · Melbourne · 1905", font=F_TY, fill=(60, 52, 44)) if p > 0.35 else None
    if p > 0.5:
        st = Image.new("RGBA", (900, 200), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle([8, 8, 892, 192], 16, outline=(190, 25, 25, 230), width=12)
        fz = ImageFont.truetype(FONT, 100); ds.text((450 - ds.textlength("SIN CONFIRMAR", font=fz) / 2, 40), "SIN CONFIRMAR", font=fz, fill=(190, 25, 25, 220))
        sc = 1 + 1.2 * max(0, 1 - (p - 0.5) / 0.06)
        st = st.resize((int(900 * sc), int(200 * sc))).rotate(10, expand=True)
        img.paste(st, (int(W / 2 - st.width / 2), int(900 - st.height / 2)), st)
    return to_img(np.asarray(img, float) * 0.85)

# ---------------------------------------------------------------- busto
def bust_frame(t, p):
    a = grad((4, 4, 6), (10, 10, 12), W, H); img = to_img(a)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx = W / 2; c = (150, 146, 136, 255); sh = (90, 86, 80, 255)
    d.polygon([(cx - 380, 1700), (cx - 300, 1250), (cx - 110, 1130), (cx + 110, 1130), (cx + 300, 1250), (cx + 380, 1700)], fill=c)
    d.rectangle([cx - 95, 960, cx + 95, 1160], fill=sh)
    d.ellipse([cx - 190, 470, cx + 190, 1010], fill=c)
    d.ellipse([cx + 160, 700, cx + 230, 840], fill=sh)                                     # oreja
    d.ellipse([cx - 120, 700, cx - 40, 730], fill=(70, 66, 60, 255)); d.ellipse([cx + 40, 700, cx + 120, 730], fill=(70, 66, 60, 255))  # ojos cerrados
    d.polygon([(cx, 720), (cx - 30, 850), (cx + 25, 860)], fill=sh)
    d.line([cx - 60, 920, cx + 60, 920], fill=(80, 76, 70, 255), width=8)
    img.paste(lay, (0, 0), lay)
    arr = np.asarray(img, float)
    lx = W / 2 - 300 + 600 * p
    arr = light(arr, lx, 650, 330, 600, (20, 20, 20), 1.0) * (0.55 + 0.45 * math.exp(-((p - 0.5) / 0.45) ** 2))
    return to_img(arr)

def end_frame(t, p):
    img = cam(BG["beach_fog"], 0.9, (1.3, 1.35, 0.2, 0.2))
    img = to_img(np.asarray(img, float) * (1 - 0.6 * min(1, p * 2))); fog(img, t, 1.4)
    d = ImageDraw.Draw(img, "RGBA")
    if p > 0.08:
        text_c(d, 250, "TAMÁM SHUD", F_MED, (255, 255, 255), 6)
        text_c(d, 360, "¿QUIÉN ERA?", F_MED, RED, 6)
        cx = W / 2; yb = 520 + 18 * math.sin(t * 8)
        d.polygon([(cx - 45, yb), (cx + 45, yb), (cx, yb + 60)], fill=RED)
    return img


# ---------------------------------------------------------------- testigos: el brazo que se levanta
def arm_frame(t, p, wide=False):
    z = (1.0 + 0.12 * ease(p)) if wide else (1.35 + 0.25 * ease(p)); cw, ch = BW / z, BH / z
    cx, cy = (650, 1155) if wide else (820, 1560)
    cx = min(max(cx, cw / 2), BW - cw / 2); cy = min(max(cy, ch / 2), BH - ch / 2)
    img = BG["beach"].resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    img = to_img(np.asarray(img, float) * np.array([1.1, 0.85, 0.75]) * 0.9)     # luz de atardecer
    d = ImageDraw.Draw(img); k = W / cw
    mx, my, s = (960 - cx) * k + W / 2, (1500 - cy) * k + H / 2, 280 * k
    man_lying(d, mx, my, s)
    up = 0 if wide else math.sin(min(1, max(0, (p - 0.15) / 0.55)) * math.pi)                      # sube… y cae
    ang = math.radians(200 - 110 * up) if p < 0.7 else math.radians(200)
    sx, sy = mx + 0.02 * s, my - 0.4 * s
    d.line([sx, sy, sx + 0.55 * s * math.cos(ang), sy + 0.55 * s * math.sin(ang)], fill=(14, 14, 18), width=int(s * 0.07))
    # pareja de testigos a lo lejos
    for j, x in enumerate((180, 240)):
        hh = (150 + j * 10) * k; y0 = (1180 - cy) * k + H / 2; x = (x + 60 - cx) * k + W / 2
        d.ellipse([x - 14 * k, y0 - hh, x + 14 * k, y0 - hh + 30 * k], fill=(10, 10, 12)); d.rectangle([x - 18 * k, y0 - hh + 28 * k, x + 18 * k, y0], fill=(10, 10, 12))
    if wide and p > 0.3:
        dd = ImageDraw.Draw(img, "RGBA"); a = int(255 * min(1, (p - 0.3) / 0.2))
        text_c(dd, 330, "30 NOV · 19:00", F_MED, (255, 255, 255, a), 6); text_c(dd, 440, "LA NOCHE ANTERIOR", F_SM, RED + (a,), 5)
    return img

# ---------------------------------------------------------------- la maleta y el nombre
def suitcase_frame(t, p):
    a = grad((10, 9, 8), (26, 22, 18), W, H); a = light(a, W / 2, 800, 500, 600, (50, 38, 22))
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 1400, W, H], fill=(20, 17, 14))
    op = ease((p - 0.2) / 0.4)
    # tapa (se abre hacia arriba)
    lid_h = 520 * (1 - op) + 120 * op
    d.rounded_rectangle([150, 880, 930, 1400], 30, fill=(96, 62, 36), outline=(50, 30, 18), width=8)
    d.rounded_rectangle([150, 880 - lid_h, 930, 900], 30, fill=(110, 72, 42), outline=(50, 30, 18), width=8)
    d.rounded_rectangle([450, 830 - lid_h * (1 - op), 630, 880 - lid_h * (1 - op)], 20, outline=(40, 26, 16), width=14)
    if op > 0.3:   # ropa doblada sin etiquetas
        for k, c in enumerate([(200, 196, 186), (60, 64, 80), (150, 40, 40), (210, 206, 196)]):
            d.rectangle([200 + k * 12, 940 + k * 90, 880 - k * 12, 1020 + k * 90], fill=c)
            d.rectangle([500, 950 + k * 90, 580, 990 + k * 90], fill=(0, 0, 0, 0), outline=(30, 30, 30), width=3)
    for x in (200, 860): d.rectangle([x - 20, 1110, x + 20, 1170], fill=(170, 150, 90))
    if p > 0.65:
        a2 = int(255 * min(1, (p - 0.65) / 0.15))
        text_c(d, 360, "ESTACIÓN DE ADELAIDA", F_SM, (255, 255, 255, a2), 5)
    return img
def keane_frame(t, p):
    img = cam(BG["wool"], p, (1.2, 1.35, 0, 0))
    img = to_img(np.asarray(img, float) * np.array([0.7, 0.75, 1.0]))
    lab = Image.new("RGBA", (700, 240), (0, 0, 0, 0)); dl = ImageDraw.Draw(lab)
    dl.rectangle([0, 0, 699, 239], fill=(236, 232, 220, 255))
    n = int(len("T. KEANE") * min(1, p / 0.35))
    f = ImageFont.truetype(MONO, 120); dl.text((350 - dl.textlength("T. KEANE", font=f) / 2, 50), "T. KEANE"[:n], font=f, fill=(25, 25, 40, 255))
    lab = lab.rotate(4, expand=True, resample=Image.BICUBIC)
    img.paste(lab, (int(W / 2 - lab.width / 2), 700), lab)
    d = ImageDraw.Draw(img, "RGBA")
    if p > 0.5:
        a = int(255 * min(1, (p - 0.5) / 0.15))
        text_c(d, 380, "¿QUIÉN ES?", F_MED, RED + (a,), 6)
    return img

# ---------------------------------------------------------------- el militar y el libro intacto
def soldier_frame(t, p):
    a = grad((20, 24, 18), (40, 44, 32), W, H); a = light(a, W / 2, 700, 420, 800, (50, 50, 30))
    img = to_img(a); d = ImageDraw.Draw(img, "RGBA")
    cx = W / 2; col = (20, 22, 16)
    d.ellipse([cx - 115, 470, cx + 115, 730], fill=col)
    d.polygon([(cx - 210, 520), (cx + 210, 520), (cx + 150, 430), (cx - 150, 430)], fill=(30, 34, 22))     # gorra
    d.rectangle([cx - 230, 515, cx + 230, 545], fill=(24, 26, 18))
    d.polygon([(cx - 400, 1900), (cx - 340, 860), (cx - 80, 760), (cx + 80, 760), (cx + 340, 860), (cx + 400, 1900)], fill=col)
    for k in range(4): d.ellipse([cx - 12, 900 + k * 120, cx + 12, 924 + k * 120], fill=(150, 130, 70))
    d.rectangle([cx + 120, 900, cx + 260, 950], fill=(150, 30, 30)); d.rectangle([cx + 120, 950, cx + 260, 975], fill=(40, 80, 140))
    text_c(d, 1080, "ALF BOXALL", F_SM, (220, 210, 180), 5)
    if t > caption_start("¿ES EL MUERTO"):
        text_c(d, 240, "¿ES EL MUERTO?", F_MED, RED, 6)
    return img
T_VIVO, T_INTACTO = None, None
def book_intact_frame(t, p):
    img = to_img(paper_tex(W, H, 33, ((230, 222, 198), (205, 194, 166))))
    d = ImageDraw.Draw(img, "RGBA")
    d.line([0, 0, 60, H], fill=(150, 140, 120), width=4)
    fi = ImageFont.truetype(SERIF_I, 52)
    r = np.random.default_rng(2)
    for k in range(9):
        y = 300 + k * 82; w = r.uniform(500, 820)
        d.line([140, y, 140 + w, y], fill=(120, 110, 95), width=10)
    f = ImageFont.truetype(SERIF_I, 120)
    text_c(d, 1080, "Tamám Shud", f, (25, 20, 18))
    if t >= T_VIVO:   # sello: Boxall está vivo
        sc = 1 + 1.2 * max(0, 1 - (t - T_VIVO) / 0.2)
        st = Image.new("RGBA", (760, 200), (0, 0, 0, 0)); ds = ImageDraw.Draw(st)
        ds.rounded_rectangle([8, 8, 752, 192], 16, outline=(30, 140, 60, 235), width=12)
        fz = ImageFont.truetype(FONT, 110); ds.text((380 - ds.textlength("¡VIVO!", font=fz) / 2, 34), "¡VIVO!", font=fz, fill=(30, 140, 60, 235))
        st = st.resize((int(760 * sc), int(200 * sc))).rotate(-8, expand=True)
        img.paste(st, (int(W / 2 - st.width / 2), int(560 - st.height / 2)), st)
    if t >= T_INTACTO:   # círculo rojo alrededor: la página sigue ahí
        a = min(1, (t - T_INTACTO) / 0.8)
        d.arc([180, 1030, 900, 1260], 0, int(360 * a), fill=RED, width=10)
        if a >= 1: text_c(d, 1600, "PÁGINA ENTERA", F_SM, RED, 4)
    return img

# ---------------------------------------------------------------- partículas
DROPS = rng.random((220, 4))
def draw_rain(img, t, k=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    for x, y, s, ph in DROPS[:int(len(DROPS) * k)]:
        yy = (y * H + t * (1400 + s * 900)) % (H + 100) - 50; xx = (x * W - t * 120) % W
        d.line([xx, yy, xx - 8, yy + 30 + 30 * s], fill=(180, 190, 210, int(40 + 70 * s)), width=2)
def fog(img, t, k=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for j in range(16):
        x = (j * 197 + t * (30 + j * 4)) % (W + 600) - 300; y = 900 + (j % 5) * 180 + 50 * math.sin(t * 0.5 + j)
        d.ellipse([x - 360, y - 110, x + 360, y + 110], fill=(150, 160, 170, int(40 * k)))
    lay = lay.filter(ImageFilter.GaussianBlur(50)); img.paste(lay, (0, 0), lay)
DUST = rng.random((80, 4))
def draw_dust(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    for x, y, s, ph in DUST:
        xx = (x * W + 20 * math.sin(t * 0.4 + ph * 6)) % W; yy = (y * H - t * 15 * (0.5 + s)) % H; r = 1 + s * 3
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 235, 200, int(40 + s * 80)))

# ---------------------------------------------------------------- fondos
T_VIVO, T_INTACTO = caption_start("VIVO"), caption_start("CON SU LIBRO")
print("generando fondos", flush=True)
BG = {"beach": bg_beach(), "beach_fog": bg_beach(True), "wool": bg_wool(), "trousers": bg_trousers(), "book": bg_book(),
      "house": bg_house(), "page": bg_page(), "report": to_img(paper_tex(BW, BH, 5))}
yy, xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1.2 - (((xx - W / 2) / (W * 0.55)) ** 2 + ((yy - H / 2) / (H * 0.58)) ** 2) * 0.75, 0.12, 1)[..., None]
GRAIN = [(rng.standard_normal((H // 2, W // 2)) * 11) for _ in range(4)]
SCRATCH = rng.random((400, 3))

def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    F = {"label_tear": label_frame, "pocket": pocket_frame, "suit": suit_frame, "poison": poison_frame, "autopsy": autopsy_frame,
         "car": car_frame, "phone": phone_frame, "house": house_frame, "code": code_frame, "code_zoom": code_zoom_frame,
         "code_glow": code_glow_frame, "arm": arm_frame, "arm_wide": lambda t, p: arm_frame(t, p, True), "suitcase": suitcase_frame, "keane": keane_frame,
         "soldier": soldier_frame, "book_intact": book_intact_frame, "dna": dna_frame, "name": name_frame, "bust": bust_frame, "end_card": end_frame}
    if name in F:
        img = F[name](t, p)
        if name in ("suit", "bust", "book", "autopsy", "name", "code"): draw_dust(img, t)
        return img
    if name in ("beach_body", "beach_fog"):
        if name == "beach_body":
            z = 1.15 + 0.35 * (ease(p) * 0.5 + p * 0.5); cw, ch = BW / z, BH / z
            cx = min(max(700 + 80 * p, cw / 2), BW - cw / 2); cy = min(max(1620, ch / 2), BH - ch / 2)
            img = BG["beach"].resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
            d = ImageDraw.Draw(img); k = W / cw
            man_lying(d, (960 - cx) * k + W / 2, (1500 - cy) * k + H / 2, 280 * k)
        else:
            img = cam(BG["beach_fog"], p, (1.2, 1.0, 0, 0)); fog(img, t, 1.6)
        return img
    if name == "title_1948":
        img = cam(BG["beach"], p, (1.3, 1.45, 0, 0)).filter(ImageFilter.GaussianBlur(6))
        img = to_img(np.asarray(img, float) * 0.45); fog(img, t)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        yr = 1900 + int(48 * ease(min(1, p / 0.45)))
        text_c(d, 380, str(yr), F_BIG, (240, 236, 228, 255), x=W / 2 + ((7 * math.sin(t * 50)) if p < 0.45 else 0))
        if p > 0.4: text_c(d, 760, "SOMERTON · ADELAIDA · AUSTRALIA", F_SM, RED + (255,))
        paste_glow(img, lay, 26)
        return img
    if name == "meaning":
        img = to_img(np.zeros((H, W, 3)) + 8)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        f = ImageFont.truetype(SERIF_I, 170)
        swap = p > 0.5
        gl = (0.45 < p < 0.55)
        txt = "Se acabó." if swap else "Tamám Shud"
        jx = 25 * math.sin(t * 90) if gl else 0
        text_c(d, 560, txt, f, (RED if swap else (235, 228, 210)) + (255,), x=W / 2 + jx)
        if gl: text_c(d, 560, txt, f, (60, 200, 255, 120), x=W / 2 - jx)
        if not swap: text_c(d, 820, "(persa)", F_SM, (160, 150, 140, 255))
        paste_glow(img, lay, 24)
        return img
    if name == "book":
        img = cam(BG["book"], p, (1.0, 1.25, 0.4, 0.4)); return img
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
    parts, hl, cur, chl = [], False, "", False
    for ch in s + " ":
        if ch == "*": hl = not hl; continue
        if ch == " ":
            if cur: parts.append((cur, chl))
            cur, chl = "", False; continue
        cur += ch; chl = chl or (hl and ch.isalnum())
    full = " ".join(q[0] for q in parts)
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
    XF = 0.14
    if i + 1 < len(SHOTS) and t > b - XF:
        a2, b2, n2 = SHOTS[i + 1]
        img = Image.blend(img, shot_frame(n2, t, a2, b2).convert("RGB"), (t - (b - XF)) / XF)
    arr = np.asarray(img, float)
    lum = arr.mean(2, keepdims=True); arr = lum + (arr - lum) * 0.75
    arr = arr * np.array([1.04, 1.0, 0.94])                       # tono de película antigua
    arr = arr * VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.22: arr = arr + (1 - u / 0.22) * np.array([150, 120, 110])
    if (fi * 7919) % 97 < 3: arr *= 0.85
    g = GRAIN[fi % 4]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    sx, _s, _p = SCRATCH[fi % 400]                                   # rayas de película
    if _p > 0.6: arr[:, int(sx * W):int(sx * W) + 2] += 50
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
