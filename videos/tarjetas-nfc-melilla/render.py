# Render del anuncio "El gadget que Melilla no sabía que necesitaba" (9:16, 1080x1920, 30 fps)
# Uso:  python3 render.py stills 1.0 4.2 ...    |    python3 render.py video 0 1 2 ...   (índices de SHOTS)
import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import SHOTS, TITLES, TOTAL

W, H, FPS = 1080, 1920, 30
BW, BH = 1300, 2310
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
_fc = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

CYAN = (60, 235, 255); BLUE = (40, 110, 255); WHITE = (255, 255, 255); GOLD = (255, 205, 70); MAG = (190, 80, 255)
rng = np.random.default_rng(5)

def clamp01(x): return min(1.0, max(0.0, x))
def ease(x): x = clamp01(x); return x * x * (3 - 2 * x)
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp01(x); return x ** 3
def back_out(x):
    x = clamp01(x); c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def arr(img): return np.asarray(img.convert("RGB"), np.float32)

# ------------------------------------------------------------------ photos
PHOTO_DIR = os.path.join(HERE, "assets", "photos")
_ph = {}
def photo(key):
    if key in _ph: return _ph[key]
    p = os.path.join(PHOTO_DIR, key + ".jpg")
    if os.path.exists(p):
        src = Image.open(p).convert("RGB")
        s = max(BW / src.width, BH / src.height)
        im = src.resize((int(src.width * s + 1), int(src.height * s + 1)), Image.LANCZOS)
        fx = PHOTO_FOCUS.get(key, 0.5)
        x0 = int((im.width - BW) * fx); y0 = (im.height - BH) // 2
        im = im.crop((x0, y0, x0 + BW, y0 + BH))
        if src.width > src.height * 1.05:
            # foto horizontal: fondo desenfocado + foto completa nítida en el centro (formato vertical)
            im = to_img(arr(im.filter(ImageFilter.GaussianBlur(40))) * 0.45)
            fw = int(BW * 1.25); fh = int(src.height * fw / src.width)
            fg = src.resize((fw, fh), Image.LANCZOS)
            im.paste(fg, ((BW - fw) // 2, (BH - fh) // 2 + 40))
        # grade: contraste, teal & orange suave
        a = arr(im)
        a = (a - 128) * 1.12 + 128
        lum = a.mean(2, keepdims=True) / 255
        a = a + (1 - lum) * np.array([-8, 4, 14]) + lum * np.array([12, 4, -10])
        im = to_img(a)
    else:
        im = to_img(np.zeros((BH, BW, 3)) + np.linspace(30, 90, BH)[:, None, None])
    _ph[key] = im; return im
PHOTO_FOCUS = {}  # desplazamiento horizontal del recorte por foto (0 izq – 1 der), se rellena en assets/photos/focus.txt
fp = os.path.join(PHOTO_DIR, "focus.txt")
if os.path.exists(fp):
    for ln in open(fp):
        if ln.strip() and not ln.startswith("#"):
            k, v = ln.split(); PHOTO_FOCUS[k] = float(v)

def cam(bg, p, z0, z1, dx=0.0, dy=0.0, rot=0.0):
    z = z0 + (z1 - z0) * p
    cw, ch = BW / z, BH / z
    cx = BW / 2 + dx * (p - 0.5) * (BW - cw); cy = BH / 2 + dy * (p - 0.5) * (BH - ch)
    if rot:
        bg = bg.rotate(rot, Image.BILINEAR, center=(cx, cy))
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

# ------------------------------------------------------------------ 3D helpers
def persp_coeffs(dst, src):
    # devuelve coeficientes para Image.transform(PERSPECTIVE): mapea puntos de salida (dst) a entrada (src)
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def project(pts3, rx, ry, rz, dist, cx, cy, f=1400):
    out = []
    cxr, sxr = math.cos(rx), math.sin(rx); cyr, syr = math.cos(ry), math.sin(ry); czr, szr = math.cos(rz), math.sin(rz)
    for x, y, z in pts3:
        x, y = x * czr - y * szr, x * szr + y * czr
        y, z = y * cxr - z * sxr, y * sxr + z * cxr
        x, z = x * cyr + z * syr, -x * syr + z * cyr
        s = f / (f + z + dist)
        out.append((cx + x * s, cy + y * s))
    return out

def place(tex, quad, canvas=(W, H)):
    # proyecta una textura RGBA sobre un cuadrilátero (tl, tr, br, bl) del lienzo
    tw, th = tex.size
    c = persp_coeffs(quad, [(0, 0), (tw, 0), (tw, th), (0, th)])
    return tex.transform(canvas, Image.PERSPECTIVE, c, Image.BICUBIC)

def rrect_mask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); return m

def glow_add(base, layer, r=30, k=1.0):
    g = layer.filter(ImageFilter.GaussianBlur(r))
    a = arr(base) + np.asarray(g, np.float32)[..., :3] * (np.asarray(g, np.float32)[..., 3:4] / 255) * k
    return to_img(a)

def over(base, layer):
    b = base.convert("RGBA"); b.alpha_composite(layer); return b.convert("RGB")

# ------------------------------------------------------------------ the product: NFC card
CW, CH = 760, 790  # tarjeta NFC real del cliente (foto enderezada en assets/tarjeta_nfc.png)
def nfc_icon(d, cx, cy, s, col, width=None):
    width = width or max(3, int(s * 0.09))
    for k in range(3):
        r = s * (0.35 + 0.3 * k)
        d.arc([cx - r, cy - r, cx + r, cy + r], -50, 50, fill=col, width=width)
    d.ellipse([cx - s * 0.12, cy - s * 0.12, cx + s * 0.12, cy + s * 0.12], fill=col)

def star(d, cx, cy, r, fill, outline=None, w=0):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline, width=w)

def make_card():
    src = Image.open(os.path.join(HERE, "assets", "tarjeta_nfc.png")).convert("RGB")
    src = src.crop((6, 6, src.width - 6, src.height - 14)).resize((CW, CH), Image.LANCZOS)
    img = src.convert("RGBA")
    img.putalpha(rrect_mask(CW, CH, 34))
    return img
CARD = make_card()

def card_tex(sheen):
    # brillo especular que recorre la tarjeta (sheen: -0.3 .. 1.3)
    t = CARD.copy()
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    u = (xx / CW + yy / CH * 0.45) / 1.45
    band = np.exp(-((u - sheen) / 0.07) ** 2) * 70 + np.exp(-((u - sheen + 0.12) / 0.03) ** 2) * 35
    rgb = np.asarray(t, np.float32)
    rgb[..., :3] += band[..., None]
    out = to_img(rgb[..., :3]).convert("RGBA"); out.putalpha(t.getchannel("A"))
    d = ImageDraw.Draw(out); d.rounded_rectangle([1, 1, CW - 2, CH - 2], 34, outline=(255, 255, 255, 200), width=3)
    return out

def draw_card(img, cx, cy, scale, rx, ry, rz, sheen=0.5, glow=0.6, shadow=True, reflect=False):
    w, h = CW * scale, CH * scale
    pts = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
    q = project(pts, rx, ry, rz, 0, cx, cy)
    tex = card_tex(sheen)
    lay = place(tex, q)
    if reflect:
        q2 = [(x, 2 * max(p[1] for p in q) - y + 20) for (x, y) in q]
        r = place(tex.transpose(Image.FLIP_TOP_BOTTOM), [q2[3], q2[2], q2[1], q2[0]])
        a = np.asarray(r, np.float32); a[..., 3] *= 0.22
        img = over(img, to_img(a) if False else Image.fromarray(a.astype(np.uint8), "RGBA"))
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon([(x + 30, y + 60) for x, y in q], fill=(0, 0, 0, 170))
        img = over(img, sh.filter(ImageFilter.GaussianBlur(40)))
    if glow > 0:
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).polygon(q, fill=CYAN + (255,))
        img = glow_add(img, gl, 60, glow * 0.55)
    return over(img, lay), q

# ------------------------------------------------------------------ phone + hand
PW, PH = 520, 1060
def phone_screen(state, p, t):
    # state: "home" | "banner" | "review"
    s = Image.new("RGB", (PW - 36, PH - 36)); d = ImageDraw.Draw(s)
    sw, sh = s.size
    if state == "home":
        a = np.zeros((sh, sw, 3), np.float32) + np.linspace(0, 1, sh)[:, None, None] * np.array([40, 30, 90]) + np.array([10, 14, 40])
        s = to_img(a); d = ImageDraw.Draw(s)
        d.text((sw / 2, 210), "10:41", font=font(F_BOLD, 120), fill=WHITE, anchor="mm")
    if state in ("banner", "review"):
        a = np.zeros((sh, sw, 3), np.float32) + 245
        s = to_img(a); d = ImageDraw.Draw(s)
        # página de reseña (maqueta genérica, sin logotipos)
        d.rectangle([0, 0, sw, 150], fill=(255, 255, 255))
        d.text((32, 92), "Tu negocio · Melilla", font=font(F_BOLD, 34), fill=(30, 30, 40), anchor="lm")
        d.ellipse([sw / 2 - 70, 210, sw / 2 + 70, 350], fill=(30, 40, 70))
        nfc_icon(d, sw / 2 - 10, 280, 60, CYAN)
        d.text((sw / 2, 400), "Valora tu experiencia", font=font(F_BOLD, 36), fill=(30, 30, 40), anchor="mm")
        fill = ease((p - 0.25) / 0.5) * 5 if state == "review" else 0
        for k in range(5):
            on = fill > k + 0.5
            star(d, sw / 2 - 168 + k * 84, 490, 36, GOLD if on else (210, 210, 220))
        for k in range(3):
            d.rounded_rectangle([40, 580 + k * 70, sw - 40 - k * 60, 610 + k * 70], 12, fill=(225, 225, 232))
        d.rounded_rectangle([60, sh - 200, sw - 60, sh - 110], 45, fill=(40, 110, 255))
        d.text((sw / 2, sh - 155), "Publicar reseña", font=font(F_BOLD, 34), fill=WHITE, anchor="mm")
    if state == "banner" or (state == "review" and p < 0.2):
        bp = ease_out(p / 0.25) if state == "banner" else 1 - ease(p / 0.2)
        if state == "banner":
            # antes de abrir: fondo de inicio y la notificación de etiqueta NFC
            a = np.zeros((sh, sw, 3), np.float32) + np.linspace(0, 1, sh)[:, None, None] * np.array([40, 30, 90]) + np.array([10, 14, 40])
            s = to_img(a); d = ImageDraw.Draw(s)
            d.text((sw / 2, 210), "10:41", font=font(F_BOLD, 120), fill=WHITE, anchor="mm")
        y = -150 + 230 * bp
        d.rounded_rectangle([18, y, sw - 18, y + 140], 34, fill=(250, 250, 252))
        nfc_icon(d, 80, y + 70, 40, BLUE)
        d.text((130, y + 48), "Etiqueta NFC", font=font(F_BOLD, 28), fill=(20, 20, 30), anchor="lm")
        d.text((130, y + 92), "Abrir enlace de reseñas", font=font(F_BOLD, 26), fill=(90, 90, 100), anchor="lm")
    return s

def draw_phone(img, cx, cy, scale, rz, state, p, t, hand=True):
    ph = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(ph)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], 80, fill=(28, 30, 36, 255))
    d.rounded_rectangle([4, 4, PW - 5, PH - 5], 76, outline=(120, 125, 140, 255), width=3)
    scr = phone_screen(state, p, t).convert("RGBA"); scr.putalpha(rrect_mask(*scr.size, 62))
    ph.alpha_composite(scr, (18, 18))
    d.rounded_rectangle([PW / 2 - 80, 34, PW / 2 + 80, 74], 20, fill=(0, 0, 0, 255))
    if hand:
        big = Image.new("RGBA", (PW + 400, PH + 500), (0, 0, 0, 0)); dh = ImageDraw.Draw(big)
        skin = (176, 122, 92, 255); skin2 = (150, 100, 74, 255)
        ox, oy = 200, 150
        dh.rounded_rectangle([ox - 110, oy + 560, ox + PW + 120, oy + PH + 520], 260, fill=skin2)      # palma
        for k in range(4):                                                                         # dedos por la derecha
            dh.rounded_rectangle([ox + PW - 40, oy + 300 + k * 150, ox + PW + 95, oy + 420 + k * 150], 60, fill=skin)
        dh.rounded_rectangle([ox - 105, oy + 520, ox + 35, oy + 900], 70, fill=skin)                  # pulgar
        big.alpha_composite(ph, (ox, oy))
        dh2 = ImageDraw.Draw(big)
        dh2.rounded_rectangle([ox - 105, oy + 600, ox + 30, oy + 900], 70, fill=skin)
        ph = big
    sz = (int(ph.width * scale), int(ph.height * scale))
    ph = ph.resize(sz, Image.LANCZOS).rotate(rz, Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = ph.getchannel("A").point(lambda v: v * 0.6)
    blk = Image.new("RGBA", ph.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (int(cx - ph.width / 2 + 40), int(cy - ph.height / 2 + 70)))
    img = over(img, sh.filter(ImageFilter.GaussianBlur(35)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.alpha_composite(ph, (int(cx - ph.width / 2), int(cy - ph.height / 2)))
    return over(img, lay)

# ------------------------------------------------------------------ FX
yy0, xx0 = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.15 - (((xx0 - W / 2) / (W * 0.65)) ** 2 + ((yy0 - H / 2) / (H * 0.62)) ** 2) * 0.55, 0.3, 1)[..., None]
GRAIN = [rng.standard_normal((H // 2, W // 2)).astype(np.float32) * 5 for _ in range(4)]
PART = rng.random((140, 4))

def studio_bg(t, hue=(10, 18, 40), spot=True):
    a = np.zeros((H, W, 3), np.float32) + np.array(hue, np.float32) * (0.5 + 0.5 * (1 - yy0 / H))[..., None]
    if spot:
        cone = np.exp(-((xx0 - W / 2) / (120 + yy0 * 0.35)) ** 2) * np.clip(1 - yy0 / H * 0.6, 0, 1)
        a += cone[..., None] * np.array([40, 70, 110])
    floor = np.clip((yy0 - 1400) / 520, 0, 1)
    a = a * (1 - floor[..., None] * 0.5)
    return to_img(a)

def particles(img, t, n=90, col=CYAN, speed=40, size=4):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, y, s, ph in PART[:n]:
        px = (x * W + 30 * math.sin(t * 0.8 + ph * 9)) % W
        py = (y * H - t * speed * (0.5 + s)) % H
        r = 1 + s * size
        al = int(80 + 150 * (0.5 + 0.5 * math.sin(t * 3 + ph * 20)))
        d.ellipse([px - r, py - r, px + r, py + r], fill=col + (al,))
    return glow_add(over(img, lay), lay, 8, 1.2)

def hud(img, t, label=None, sub=None, grid=False, scan=True, col=CYAN):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    m, L = 60, 90
    for (x, y, sx, sy) in [(m, m + 120, 1, 1), (W - m, m + 120, -1, 1), (m, H - m - 120, 1, -1), (W - m, H - m - 120, -1, -1)]:
        d.line([x, y, x + sx * L, y], fill=col + (220,), width=5); d.line([x, y, x, y + sy * L], fill=col + (220,), width=5)
    if scan:
        sy = (t * 700) % (H + 400) - 200
        for k in range(40):
            d.line([0, sy - k * 3, W, sy - k * 3], fill=col + (int(60 * (1 - k / 40)),), width=3)
    if grid:
        hz = 1280
        for k in range(-12, 13):
            d.line([W / 2 + k * 30, hz, W / 2 + k * 260, H], fill=col + (110,), width=3)
        for k in range(12):
            z = ((k + (t * 2.2) % 1) / 12) ** 2.2
            y = hz + (H - hz) * z
            d.line([0, y, W, y], fill=col + (int(40 + 120 * z),), width=3)
    if label:
        f = font(F_MONO, 34)
        tw = d.textlength(label, font=f)
        x, y = 80, H - 250
        d.rectangle([x - 20, y - 12, x + tw + 70, y + 56], fill=(0, 0, 0, 150))
        d.polygon([(x, y + 6), (x + 30, y + 6), (x + 15, y + 40)], fill=col + (255,))
        d.ellipse([x + 3, y - 4, x + 27, y + 20], fill=col + (255,))
        d.text((x + 50, y + 22), label, font=f, fill=WHITE + (255,), anchor="lm")
        if sub: d.text((x, y + 90), sub, font=font(F_MONO, 26), fill=col + (230,), anchor="lm")
    return glow_add(over(img, lay), lay, 10, 0.8)

def rgb_split(img, amt):
    if amt < 0.5: return img
    r, g, b = img.split(); a = int(amt)
    return Image.merge("RGB", (ImageChops.offset(r, a, 0), g, ImageChops.offset(b, -a, 0)))

def glitch(img, t, k):
    if k <= 0: return img
    a = np.asarray(img).copy(); r = np.random.default_rng(int(t * 1000))
    for _ in range(int(6 + 20 * k)):
        y = r.integers(0, H - 80); hgt = r.integers(8, 80); sh = int(r.integers(-120, 120) * k)
        a[y:y + hgt] = np.roll(a[y:y + hgt], sh, axis=1)
    return rgb_split(Image.fromarray(a), 18 * k)

def ripple(img, cx, cy, p, col=CYAN, n=3):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(n):
        q = (p - k * 0.18)
        if 0 < q < 1:
            r = 40 + q * 420; al = int(255 * (1 - q))
            d.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55], outline=col + (al,), width=8)
    return glow_add(over(img, lay), lay, 16, 1.4)

# ------------------------------------------------------------------ business scenes (ilustración neón)
def neon(d, shape, *a, col=CYAN, w=10, **k):
    getattr(d, shape)(*a, outline=col + (255,), width=w, **k) if shape in ("rectangle", "ellipse", "rounded_rectangle") else getattr(d, shape)(*a, fill=col + (255,), width=w, **k)

def biz_scene(kind, t, p):
    hue = {"barber": (40, 12, 30), "food": (40, 20, 8), "shop": (8, 22, 40), "any": (10, 10, 30)}[kind]
    img = studio_bg(t, hue, spot=True)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    zoom = 1 + 0.06 * p
    def S(x, y): return (W / 2 + (x - W / 2) * zoom, 900 + (y - 900) * zoom)
    if kind == "barber":
        # poste de barbero con franjas en movimiento + tijeras
        x0, x1, y0, y1 = 170, 290, 520, 1140
        d.rounded_rectangle([*S(x0, y0), *S(x1, y1)], 50, outline=WHITE + (255,), width=10)
        for k in range(-3, 9):
            yy = y0 + ((k * 90 + t * 160) % 720) - 90
            for col, off in ((255, 60, 60), 0), ((60, 120, 255), 45):
                a0 = S(x0 + 10, yy + off); a1 = S(x1 - 10, yy + off - 80)
                if y0 + 30 < yy + off - 80 and yy + off < y1 - 30: d.line([a0, a1], fill=col + (255,), width=14)
        cx, cy = 760, 640
        for s in (-1, 1):
            ang = s * (0.25 + 0.15 * math.sin(t * 9))
            d.line([S(cx, cy), S(cx + 300 * math.cos(-math.pi / 2 + ang), cy + 300 * math.sin(-math.pi / 2 + ang))], fill=CYAN + (255,), width=12)
            ex, ey = cx - 150 * math.cos(-math.pi / 2 + ang), cy - 150 * math.sin(-math.pi / 2 + ang) + 60
            d.ellipse([*S(ex - 55, ey - 55), *S(ex + 55, ey + 55)], outline=CYAN + (255,), width=12)
        col = (255, 90, 120)
        d.rounded_rectangle([*S(420, 900), *S(980, 1000)], 30, outline=col + (255,), width=10)   # mostrador
    elif kind == "food":
        cx, cy = 560, 640
        d.ellipse([*S(cx - 240, cy - 240), *S(cx + 240, cy + 240)], outline=GOLD + (255,), width=12)
        d.ellipse([*S(cx - 160, cy - 160), *S(cx + 160, cy + 160)], outline=GOLD + (160,), width=6)
        d.line([S(cx - 330, cy - 200), S(cx - 330, cy + 240)], fill=WHITE + (255,), width=12)
        for k in (-30, 0, 30): d.line([S(cx - 330 + k, cy - 200), S(cx - 330 + k, cy - 110)], fill=WHITE + (255,), width=8)
        d.line([S(cx + 330, cy - 200), S(cx + 330, cy + 240)], fill=WHITE + (255,), width=12)
        d.ellipse([*S(cx + 300, cy - 220), *S(cx + 360, cy - 60)], outline=WHITE + (255,), width=10)
        for k in range(3):   # vapor
            pts = [S(cx - 60 + k * 60 + 18 * math.sin(t * 4 + j * 0.6 + k), cy - 290 - j * 18) for j in range(10)]
            d.line(pts, fill=(255, 255, 255, 150), width=7)
        d.rounded_rectangle([*S(100, 900), *S(980, 1000)], 30, outline=GOLD + (255,), width=10)
    elif kind == "shop":
        x0, y0 = 250, 380
        d.polygon([S(x0, y0 + 160), S(x0 + 580, y0 + 160), S(x0 + 530, y0 + 600), S(x0 + 50, y0 + 600)], outline=CYAN + (255,), width=12)
        d.arc([*S(x0 + 170, y0), *S(x0 + 410, y0 + 300)], 180, 360, fill=CYAN + (255,), width=12)
        nfc_icon(d, *S(x0 + 290, y0 + 380), 90, MAG + (255,))
        for k in range(5):  # tiras de toldo
            col = (MAG if k % 2 else WHITE) + (255,)
            d.rectangle([*S(60 + k * 192, 170), *S(60 + k * 192 + 180, 250)], outline=col, width=8)
        d.rounded_rectangle([*S(100, 1040), *S(980, 1060)], 10, outline=CYAN + (255,), width=8)
    else:
        icons = ["✂", "☕", "🍽", "🛍"]
        labels = ["PELUQUERÍA", "CAFETERÍA", "TALLER", "CLÍNICA", "GIMNASIO", "HOTEL", "INMOBILIARIA", "FLORISTERÍA", "ÓPTICA"]
        for i, lb in enumerate(labels):
            r_, c_ = divmod(i, 3)
            x, y = 90 + c_ * 310, 330 + r_ * 230
            on = p * 9 * 1.4 > i
            col = (CYAN if on else (70, 80, 110))
            d.rounded_rectangle([x, y, x + 280, y + 190], 30, outline=col + (255,), width=6, fill=(col + (40,)) if on else None)
            nfc_icon(d, x + 140, y + 72, 44, col + (255,), 6)
            d.text((x + 140, y + 150), lb, font=font(F_MONO, 26), fill=WHITE + (255 if on else 120,), anchor="mm")
    img = glow_add(over(img, lay), lay, 22, 1.3)
    img = particles(img, t, 50, CYAN, 30, 3)
    if kind != "any":
        # tarjeta sobre el mostrador + móvil que toca
        img, q = draw_card(img, 640 if kind != "food" else 640, 1300, 0.62, 0.95, 0.0, -0.05, sheen=-0.2 + p * 1.4, glow=0.5)
        tap = ease((p - 0.15) / 0.35) - ease((p - 0.85) / 0.15)
        img = draw_phone(img, 700, 1700 - 250 * tap, 0.55, 8, "review" if p > 0.5 else "home", (p - 0.5) * 2, t, hand=True)
        if p > 0.45: img = ripple(img, 640, 1300, (p - 0.45) / 0.5)
    return img

# ------------------------------------------------------------------ titles
def title_layer(t):
    cur = [x for x in TITLES if x[0] <= t < x[1]]
    if not cur: return None
    a, b, lines, style = cur[0][:4]
    age = t - a; out_p = clamp01((t - (b - 0.12)) / 0.12)
    size = {"hook": 150, "mid": 112, "big": 230, "cta": 120}[style]
    y_c = {"hook": 820, "mid": 360, "big": 330, "cta": 1380}[style]
    if len(cur[0]) > 4: y_c = cur[0][4]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sizes = []
    for ln in lines:
        s = size; f = font(F_BLACK, s)
        while d.textlength(ln.replace("*", ""), font=f) > W - 110: s -= 4; f = font(F_BLACK, s)
        sizes.append(s)
    lh = [s * 1.02 for s in sizes]; tot = sum(lh); y = y_c - tot / 2
    for i, (ln, s) in enumerate(zip(lines, sizes)):
        li = clamp01((age - i * 0.11) / 0.18)
        if li <= 0: y += lh[i]; continue
        sc = 0.6 + 0.4 * back_out(li)
        f = font(F_BLACK, max(8, int(s * sc)))
        hl = ln.startswith("*")
        txt = ln.replace("*", "")
        tw = d.textlength(txt, font=f)
        x = (W - tw) / 2; yy = y + (s - s * sc) / 2
        if hl and style != "big":
            pad = 18
            d.rounded_rectangle([x - pad, yy + s * 0.08, x + tw + pad, yy + s * sc * 1.0], 18, fill=CYAN + (int(255 * li),))
            d.text((x, yy), txt, font=f, fill=(5, 10, 25, int(255 * li)))
        else:
            fill = (CYAN if hl else WHITE) + (int(255 * li),)
            d.text((x, yy), txt, font=f, fill=fill, stroke_width=max(4, int(s * 0.05)), stroke_fill=(0, 0, 0, int(220 * li)))
        y += lh[i]
    if out_p > 0:
        al = np.asarray(lay.getchannel("A"), np.float32) * (1 - out_p); lay.putalpha(Image.fromarray(al.astype(np.uint8)))
    return lay

# ------------------------------------------------------------------ shots
def photo_shot(key, p, t, z0, z1, dx=0, dy=0, label=None):
    img = cam(photo(key), ease(p) * 0.6 + p * 0.4, z0, z1, dx, dy)
    return img

def shot_frame(name, t, a, b):
    p = clamp01((t - a) / (b - a))
    if name == "faro_hook":
        img = cam(photo("faro_hook"), ease_in(p) * 0.5 + p * 0.5, 1.0, 1.45, 0.0, -0.2)
        img = to_img(arr(img) * 0.72)
        img = hud(img, t, "FARO DE MELILLA", "SEÑAL DETECTADA ▮▮▮▯", scan=True)
        # notificación tecnológica que cae desde arriba
        bp = back_out((t - 0.05) / 0.35)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        y = -200 + 290 * bp
        d.rounded_rectangle([60, y, W - 60, y + 160], 44, fill=(250, 250, 255, 235))
        d.rounded_rectangle([90, y + 30, 190, y + 130], 26, fill=(15, 20, 40, 255))
        nfc_icon(d, 132, y + 80, 44, CYAN + (255,), 7)
        d.text((220, y + 58), "NUEVO GADGET DETECTADO", font=font(F_BOLD, 36), fill=(15, 15, 25, 255), anchor="lm")
        d.text((220, y + 108), "Toca para descubrirlo · ahora", font=font(F_BOLD, 30), fill=(100, 100, 115, 255), anchor="lm")
        return over(img, lay)
    if name in ("box_closed", "box_open"):
        img = studio_bg(t, (8, 12, 26))
        img = particles(img, t, 70, (150, 200, 255), 20, 3)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        open_p = 0 if name == "box_closed" else ease_out(p / 0.55)
        shake = (math.sin(t * 60) * 6 * clamp01((p - 0.5) / 0.5)) if name == "box_closed" else 0
        bx, by, bw, bh, dep = W / 2 + shake, 1240, 700, 330, 210
        # mesa
        d.polygon([(0, 1330), (W, 1330), (W, H), (0, H)], fill=(18, 20, 30, 255))
        d.line([0, 1330, W, 1330], fill=(70, 80, 110, 255), width=3)
        # caja: frente, lateral superior
        fx0, fx1 = bx - bw / 2, bx + bw / 2
        d.polygon([(fx0, by - bh), (fx1, by - bh), (fx1, by), (fx0, by)], fill=(16, 16, 20, 255))
        d.polygon([(fx0, by - bh), (fx0 + dep * 0.5, by - bh - dep * 0.45), (fx1 + dep * 0.5, by - bh - dep * 0.45), (fx1, by - bh)], fill=(40, 40, 50, 255))
        d.polygon([(fx1, by - bh), (fx1 + dep * 0.5, by - bh - dep * 0.45), (fx1 + dep * 0.5, by - dep * 0.45), (fx1, by)], fill=(10, 10, 14, 255))
        d.text((bx, by - bh / 2), "?", font=font(F_BLACK, 220), fill=CYAN + (255,), anchor="mm")
        d.line([fx0, by - bh + 40, fx1, by - bh + 40], fill=(60, 60, 70, 255), width=3)
        if open_p > 0:
            # luz desde dentro + tapa que sale volando
            rays = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(rays)
            topy = by - bh - dep * 0.2
            for k in range(9):
                ang = -math.pi / 2 + (k - 4) * 0.16
                L = 1400 * open_p
                dr.polygon([(bx - 60 + k * 15, topy), (bx + L * math.cos(ang - 0.05), topy + L * math.sin(ang - 0.05)), (bx + L * math.cos(ang + 0.05), topy + L * math.sin(ang + 0.05))], fill=(200, 240, 255, 90))
            lay = Image.alpha_composite(rays.filter(ImageFilter.GaussianBlur(14)), lay)
            d = ImageDraw.Draw(lay)
            ly = by - bh - 30 - 700 * open_p; lr = 25 * open_p
            lid = Image.new("RGBA", (bw + 80, 90), (0, 0, 0, 0)); ImageDraw.Draw(lid).rounded_rectangle([0, 0, bw + 79, 89], 14, fill=(30, 30, 38, 255))
            lid = lid.rotate(lr, expand=True)
            lay.alpha_composite(lid, (int(bx - lid.width / 2 + 200 * open_p), int(ly)))
        img = glow_add(over(img, lay), lay, 25, 0.35)
        if name == "box_closed":
            # tapa: ligera vibración y brillo en la rendija
            d2 = ImageDraw.Draw(img)
            d2.rounded_rectangle([fx0 - 40, by - bh - 40, fx1 + 40, by - bh + 30], 14, fill=(30, 30, 38))
            gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).line([fx0, by - bh + 34, fx1, by - bh + 34], fill=CYAN + (255,), width=6)
            img = glow_add(over(img, gl), gl, 18, 1.5 * ease(p))
            img = cam(img.resize((BW, BH)), p, 1.0, 1.12)
        else:
            rise = ease_out((p - 0.15) / 0.75)
            img, _ = draw_card(img, W / 2, by - bh - 40 - 560 * rise, 0.25 + 0.55 * rise, 0.9 * (1 - rise) + 0.12, -0.5 * (1 - rise) + 0.15 * math.sin(t * 2), 0.06,
                               sheen=-0.2 + 1.4 * p, glow=0.4 + 0.6 * rise)
        return img
    if name in ("tap_approach", "tap_result"):
        img = studio_bg(t, (6, 14, 34))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        d.polygon([(0, 1100), (W, 1100), (W, H), (0, H)], fill=(22, 24, 32, 255))
        img = over(img, lay)
        if name == "tap_approach":
            img, q = draw_card(img, W / 2, 1180, 0.95, 1.0, 0.0, -0.08, sheen=-0.2 + p * 1.3, glow=0.6)
            ap = ease(p / 0.9)
            img = draw_phone(img, W / 2 + 60, 1950 - 820 * ap, 0.95, 12 - 8 * ap, "home", 0, t)
            if p > 0.85: img = ripple(img, W / 2, 1180, (p - 0.85) / 0.4)
            img = cam(img.resize((BW, BH)), p, 1.0, 1.15, 0, 0.2)
        else:
            img, q = draw_card(img, W / 2, 1320, 0.8, 1.05, 0.0, -0.08, sheen=0.8, glow=0.9)
            img = ripple(img, W / 2, 1320, 0.2 + p * 1.6, n=4)
            img = draw_phone(img, W / 2 + 40, 980 - 60 * ease(p), 1.05, 3, "banner" if p < 0.4 else "review", (p if p < 0.4 else (p - 0.4) / 0.6), t)
            if p < 0.12:
                img = to_img(arr(img) + (1 - p / 0.12) * 120)
        return img
    if name == "portal":
        img = studio_bg(t, (4, 8, 24), spot=False)
        img = hud(img, t, None, grid=True, scan=False)
        fly = ease_in(p)
        img, q = draw_card(img, W / 2, 900, 0.7 + 3.5 * fly, 0.3 * (1 - fly), 0.6 * math.sin(p * 3), 0.6 * fly, sheen=p * 1.2, glow=1.0)
        if p > 0.6:
            mur = cam(photo("murallas_game"), 0, 1.6, 1.6)
            k = ease((p - 0.6) / 0.4)
            img = Image.blend(img, mur, k)
        return glitch(img, t, max(0, (p - 0.45) * 1.6) * (1 - max(0, (p - 0.9) * 10)))
    if name == "murallas_game":
        img = cam(photo("murallas_game"), ease_out(p), 1.6, 1.12, 0.2, 0.0)
        img = to_img(arr(img) * np.array([0.85, 0.95, 1.1]))
        img = hud(img, t, "MURALLAS REALES", "NIVEL 01 · MODO FUTURO ACTIVADO", grid=True, scan=True)
        return glitch(img, t, max(0, 0.6 - p * 3))
    if name.startswith("biz_"):
        return biz_scene(name[4:], t, p)
    if name in ("hernandez_float", "noray_float"):
        key = name.replace("_float", "")
        img = cam(photo(key), p, 1.05, 1.25, 0.4 if key == "noray" else -0.3, -0.1)
        img = to_img(arr(img) * 0.8)
        img = particles(img, t, 80, CYAN, 50, 4)
        bob = math.sin(t * 2.4) * 30
        img, q = draw_card(img, W / 2, 1150 + bob, 0.72, 0.35 + 0.15 * math.sin(t * 1.3), 0.5 * math.sin(t * 1.1 + (1 if key == "noray" else 0)), 0.1 * math.sin(t),
                           sheen=(p * 1.5 - 0.2), glow=1.0, shadow=False)
        img = hud(img, t, "PARQUE HERNÁNDEZ" if key == "hernandez" else "PUERTO NORAY", None, scan=False)
        return img
    if name.startswith("m_"):
        key = name
        lbl = {"m_faro": "FARO DE MELILLA", "m_sanlorenzo": "PLAYAS DE MELILLA", "m_murallas": "MELILLA LA VIEJA",
               "m_hernandez": "PARQUE HERNÁNDEZ", "m_calle1": "CENTRO MODERNISTA", "m_calle2": "CALLES CON VIDA"}[name]
        dirs = {"m_faro": (0, -0.4), "m_sanlorenzo": (0.6, 0), "m_murallas": (-0.6, 0), "m_hernandez": (0, 0.4), "m_calle1": (0.5, 0.2), "m_calle2": (-0.5, -0.2)}[name]
        img = cam(photo(key), ease_out(p), 1.32, 1.05, *dirs)
        img = hud(img, t, lbl, None, scan=False)
        return rgb_split(img, 14 * max(0, 1 - p / 0.15))
    if name == "hero_card":
        img = studio_bg(t, (6, 10, 30))
        img = particles(img, t, 120, (180, 220, 255), 25, 3)
        ry = -0.55 + 1.1 * ease(p)
        img, q = draw_card(img, W / 2, 1200, 0.92, 0.18, ry, -0.04, sheen=-0.3 + 1.6 * p, glow=1.1, reflect=True)
        return img
    if name == "cta":
        img = studio_bg(t, (4, 10, 30))
        img = particles(img, t, 100, CYAN, 35, 3)
        img, q = draw_card(img, W / 2, 690, 0.8, 0.12, 0.25 * math.sin(t * 1.5), 0.0, sheen=(p * 2) % 1.4 - 0.2, glow=1.2)
        img = ripple(img, W / 2, 690, (p * 1.5) % 1, n=3)
        # botón de mensaje privado
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        pulse = 1 + 0.04 * math.sin(t * 8)
        bw, bh = 720 * pulse, 130 * pulse
        y0 = 1720
        d.rounded_rectangle([W / 2 - bw / 2, y0 - bh / 2, W / 2 + bw / 2, y0 + bh / 2], 60, fill=CYAN + (255,))
        # icono de mensaje
        d.rounded_rectangle([W / 2 - bw / 2 + 40, y0 - 30, W / 2 - bw / 2 + 110, y0 + 22], 14, fill=(5, 10, 25, 255))
        d.polygon([(W / 2 - bw / 2 + 55, y0 + 18), (W / 2 - bw / 2 + 52, y0 + 42), (W / 2 - bw / 2 + 80, y0 + 20)], fill=(5, 10, 25, 255))
        d.text((W / 2 + 40, y0), "MENSAJE PRIVADO", font=font(F_BLACK, 52), fill=(5, 10, 25, 255), anchor="mm")
        return glow_add(over(img, lay), lay, 30, 0.6)
    raise KeyError(name)

FLASH = [0.0, 3.0, 4.5, 8.0, 11.4, 14.0, 19.0, 24.0, 30.0, 33.0]
def frame(t, fi):
    idx = [i for i, s in enumerate(SHOTS) if s[0] <= t < s[1]]
    i = idx[0] if idx else len(SHOTS) - 1
    a, b, name = SHOTS[i]
    img = shot_frame(name, t, a, b)
    # transición: zoom-whip (desenfoque radial aproximado) en los 0,12 s finales del plano
    if i + 1 < len(SHOTS) and t > b - 0.12 and SHOTS[i + 1][2] not in ("murallas_game",):
        k = (t - (b - 0.12)) / 0.12
        z = 1 + 0.25 * k
        img = img.resize((int(W * z), int(H * z)), Image.BILINEAR).crop(((int(W * z) - W) // 2, (int(H * z) - H) // 2, (int(W * z) - W) // 2 + W, (int(H * z) - H) // 2 + H))
        img = Image.blend(img, img.filter(ImageFilter.GaussianBlur(14)), k)
    x = arr(img) * VIG
    for h in FLASH:
        u = t - h
        if 0 <= u < 0.16: x = x + (1 - u / 0.16) * 110
    g = GRAIN[fi % 4]; x += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    if t < 0.12: x *= t / 0.12
    img = to_img(x)
    tl = title_layer(t)
    if tl is not None: img = over(img, tl)
    if t > TOTAL - 0.35: img = to_img(arr(img) * max(0, (TOTAL - t) / 0.35))
    return img

def render_shot(si, path):
    a, b, _ = SHOTS[si]
    f0, f1 = int(round(a * FPS)), int(round(b * FPS))
    tmp = path.replace(".mp4", ".part.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, path)

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]]:
            frame(tt, 0).save(os.path.join(HERE, "stills", f"still_{tt:05.2f}.jpg"), quality=85)
    else:
        for si in [int(x) for x in sys.argv[2:]]:
            render_shot(si, os.path.join(HERE, f"shot_{si:02}.mp4")); print("shot", si, flush=True)
