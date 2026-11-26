# Utilidades compartidas: tarjeta NFC 3D, móvil, fotos, efectos (derivado del anuncio tarjetas-nfc-melilla)
# Uso:  python3 render.py stills 1.0 4.2 ...    |    python3 render.py video 0 1 2 ...   (índices de SHOTS)
import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

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

