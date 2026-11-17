# Render del vídeo "GTA 6: haz esto YA" — 1080x1920, 30 fps.
# Todo se dibuja por código (Pillow + NumPy) con estética neón tipo Miami: skyline, palmeras,
# playa al atardecer, deportivo, billetes... Sin logos ni marcas registradas.
# Uso:  python3 render.py frame <t> [<t> ...]   -> previews/frame_<t>.png
#       python3 render.py video                -> video_only.mp4
import sys, os, math, subprocess
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import load_timing, caption_groups, shot_timeline, is_keyword, norm

W, H, FPS = 1080, 1920, 30
BW, BH = 1320, 2346                    # fondos más grandes para mover la cámara
FONT = os.path.join(HERE, "fonts", "Anton-Regular.ttf")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YEL = (255, 222, 0); PINK = (255, 46, 170); CYAN = (0, 234, 255); PURP = (140, 60, 255)
RED = (255, 30, 40); GREEN = (40, 230, 110)
_fonts = {}
def font(sz):
    sz = int(sz)
    if sz not in _fonts: _fonts[sz] = ImageFont.truetype(FONT, sz)
    return _fonts[sz]

TM = load_timing()
TOTAL = TM["total"]
SHOTS = shot_timeline(TM)
CAPS = caption_groups(TM)
KEY_TIMES = [w[0] for w in TM["words"] if is_keyword(w[2])]

# ------------------------------------------------------------------ utilidades
def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_io(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

def grad(stops, w=BW, h=BH):
    ys = np.linspace(0, 1, h)
    pos = [s[0] for s in stops]
    out = np.zeros((h, 3))
    for c in range(3):
        out[:, c] = np.interp(ys, pos, [s[1][c] for s in stops])
    return np.broadcast_to(out[:, None, :], (h, w, 3)).copy()

def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def arr(im): return np.asarray(im, dtype=np.float32)

def add_glow(base, layer, r=(6, 22, 60), k=(1.0, 0.9, 0.6)):
    """Suma una capa luminosa con varios radios de desenfoque (efecto neón)."""
    a = arr(base)[..., :3] + arr(layer)[..., :3]
    for rr, kk in zip(r, k):
        a += arr(layer.filter(ImageFilter.GaussianBlur(rr)))[..., :3] * kk
    return to_img(a)

def text_size(txt, f):
    b = f.getbbox(txt); return b[2] - b[0], b[3] - b[1], b

def draw_text_center(img, txt, cx, cy, size, fill, stroke=10, stroke_fill=(0, 0, 0), glow=None, scale=1.0, alpha=1.0, rot=0):
    """Texto centrado con borde; opcional brillo neón, escala y rotación."""
    f = font(size * scale)
    tw, th, b = text_size(txt, f)
    pad = stroke + 40
    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((pad - b[0], pad - b[1]), txt, font=f, fill=fill + (255,), stroke_width=int(stroke * scale), stroke_fill=stroke_fill + (255,))
    if glow:
        g = Image.new("RGBA", layer.size, (0, 0, 0, 0)); dg = ImageDraw.Draw(g)
        dg.text((pad - b[0], pad - b[1]), txt, font=f, fill=glow + (255,), stroke_width=int(stroke * scale) + 6, stroke_fill=glow + (255,))
        g = g.filter(ImageFilter.GaussianBlur(18))
        layer = Image.alpha_composite(g, layer)
    if rot: layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        al = layer.split()[3].point(lambda v: int(v * alpha)); layer.putalpha(al)
    safe_ac(img, layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
    return tw

def emoji_img(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((int(im.width * size / 109), int(im.height * size / 109)), Image.LANCZOS)

def safe_ac(dst, src, pos):
    """alpha_composite que admite posiciones negativas o fuera de la imagen."""
    x, y = int(pos[0]), int(pos[1])
    l, t = max(0, -x), max(0, -y)
    r, b = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if r <= l or b <= t: return
    dst.alpha_composite(src.crop((l, t, r, b)), (x + l, y + t))

# ------------------------------------------------------------------ elementos
def palm(d, x, base, h, lean, col, rng, fronds=9, width=1.0):
    pts = []
    for i in range(25):
        s = i / 24
        pts.append((x + lean * h * s ** 1.6, base - h * s))
    for i in range(len(pts) - 1):
        wdt = (26 - 14 * i / 24) * width * h / 900
        d.line([pts[i], pts[i + 1]], fill=col, width=max(3, int(wdt)))
    tx, ty = pts[-1]
    for k in range(fronds):
        ang = -math.pi / 2 + (k - fronds / 2 + 0.5) * (math.pi * 1.25 / fronds) + rng.uniform(-0.15, 0.15)
        L = h * rng.uniform(0.42, 0.55)
        poly_top, poly_bot = [], []
        for j in range(18):
            s = j / 17
            ax = tx + math.cos(ang) * L * s
            ay = ty + math.sin(ang) * L * s + (L * 0.55) * s * s * (0.6 + 0.4 * abs(math.cos(ang)))
            wv = L * 0.07 * math.sin(math.pi * s) * width
            poly_top.append((ax - math.sin(ang) * wv, ay + math.cos(ang) * wv))
            poly_bot.append((ax + math.sin(ang) * wv, ay - math.cos(ang) * wv))
        d.polygon(poly_top + poly_bot[::-1], fill=col)
    d.ellipse([tx - h * 0.025, ty - h * 0.02, tx + h * 0.025, ty + h * 0.03], fill=col)

def skyline(w, h, base, rng, neon_cols=(PINK, CYAN, PURP), dense=1.0, tall=1.0, night=1.0):
    """Edificios con ventanas encendidas y perfiles de neón. Devuelve (capa RGBA, capa de neón RGB)."""
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    neon = Image.new("RGB", (w, h)); dn = ImageDraw.Draw(neon)
    x = -40
    while x < w + 40:
        bw = int(rng.uniform(70, 190) / dense)
        bh = int(rng.uniform(180, 760) * tall * (1.6 if rng.random() < 0.15 else 1))
        top = base - bh
        col = tuple(int(v) for v in (np.array([18, 10, 40]) + rng.uniform(0, 14)))
        kind = rng.random()
        if kind < 0.3:  # art déco escalonado
            d.rectangle([x, top, x + bw, base], fill=col)
            d.rectangle([x + bw * 0.15, top - bh * 0.08, x + bw * 0.85, top], fill=col)
            d.rectangle([x + bw * 0.35, top - bh * 0.16, x + bw * 0.65, top - bh * 0.08], fill=col)
            d.line([x + bw / 2, top - bh * 0.16, x + bw / 2, top - bh * 0.25], fill=col, width=4)
        elif kind < 0.45:  # torre redondeada
            d.rectangle([x, top, x + bw, base], fill=col)
            d.pieslice([x, top - bw / 2, x + bw, top + bw / 2], 180, 360, fill=col)
        else:
            d.rectangle([x, top, x + bw, base], fill=col)
        # ventanas
        wc = rng.choice([0, 1, 2])
        wincol = [(255, 214, 140), (120, 230, 255), (255, 120, 200)][wc]
        for wy in range(int(top + 20), int(base - 10), 22):
            for wx in range(int(x + 10), int(x + bw - 14), 18):
                if rng.random() < 0.33 * night:
                    b = rng.uniform(0.5, 1.0)
                    d.rectangle([wx, wy, wx + 8, wy + 11], fill=tuple(int(c * b) for c in wincol) + (255,))
        if rng.random() < 0.45:
            nc = neon_cols[rng.integers(len(neon_cols))]
            if rng.random() < 0.5:
                dn.line([x, top, x + bw, top], fill=nc, width=5)
                dn.line([x, top, x, base], fill=nc, width=3)
            else:
                yy = top + rng.uniform(0.1, 0.4) * bh
                dn.rectangle([x + 10, yy, x + bw - 10, yy + 26], outline=nc, width=5)
        x += bw + rng.integers(-10, 12)
    return lay, neon

def stars(a, n, rng, ymax):
    for _ in range(n):
        x, y = rng.integers(0, a.shape[1]), rng.integers(0, ymax)
        a[y, x] = np.minimum(255, a[y, x] + rng.uniform(80, 255))
    return a

def reflect(img, y0, darken=0.45, seed=0):
    """Reflejo en el agua desde la línea y0 con ondulación."""
    a = arr(img)
    top = a[:y0]
    hh = a.shape[0] - y0
    refl = top[::-1][:hh].copy()
    if refl.shape[0] < hh:
        refl = np.concatenate([refl, np.zeros((hh - refl.shape[0],) + refl.shape[1:], np.float32)])
    r = np.random.default_rng(seed)
    for yy in range(hh):
        sh = int(8 * math.sin(yy * 0.35 + r.uniform(0, 0.4)) * (1 + yy / 300))
        refl[yy] = np.roll(refl[yy], sh, axis=0)
    fade = np.linspace(1, 0.25, hh)[:, None, None]
    a[y0:] = refl * darken * fade + a[y0:] * 0.25
    return to_img(a)

CAR_BODY = [(0.00, 0.10), (0.015, 0.165), (0.12, 0.205), (0.30, 0.235), (0.42, 0.27), (0.52, 0.355), (0.67, 0.36),
            (0.80, 0.30), (0.95, 0.275), (1.00, 0.24), (1.00, 0.12), (0.97, 0.09)]
CAR_WIN = [(0.45, 0.265), (0.535, 0.338), (0.655, 0.342), (0.75, 0.285)]

def car_sprite(L=700, body=(255, 40, 120), glow_col=CYAN, wheel_rot=0.0):
    """Deportivo de perfil (mira a la izquierda). Devuelve RGBA y capa de brillo."""
    Hh = int(L * 0.48)
    im = Image.new("RGBA", (L + 40, Hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    gl = Image.new("RGB", im.size); dg = ImageDraw.Draw(gl)
    gy = Hh - 12
    P = lambda p: (20 + p[0] * L, gy - p[1] * L)
    # cuerpo con degradado vertical
    mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).polygon([P(p) for p in CAR_BODY], fill=255)
    g = grad([(0, tuple(min(255, c + 90) for c in body)), (0.45, body), (1, tuple(int(c * 0.35) for c in body))], im.width, im.height)
    im.paste(to_img(g), (0, 0), mask)
    d.polygon([P(p) for p in CAR_WIN], fill=(20, 24, 40, 255))
    d.line([P((0.47, 0.27)), P((0.55, 0.33))], fill=(150, 200, 255, 255), width=4)
    # línea de carácter y entrada de aire
    d.line([P((0.06, 0.16)), P((0.45, 0.2)), P((0.78, 0.24)), P((0.97, 0.22))], fill=(255, 255, 255, 120), width=3)
    d.polygon([P((0.56, 0.2)), P((0.68, 0.24)), P((0.68, 0.18))], fill=(15, 15, 25, 255))
    # faros
    dg.polygon([P((0.01, 0.15)), P((0.07, 0.18)), P((0.08, 0.165))], fill=(220, 250, 255))
    dg.line([P((0.975, 0.23)), P((1.0, 0.215))], fill=(255, 30, 40), width=8)
    # ruedas
    for wx in (0.2, 0.8):
        cx, cy = P((wx, 0.085)); r = 0.088 * L
        d.ellipse([cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6], fill=(5, 5, 10, 255))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(18, 18, 22, 255))
        rr = r * 0.62
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(150, 150, 165, 255))
        for k in range(5):
            a = wheel_rot + k * 2 * math.pi / 5
            d.line([cx, cy, cx + math.cos(a) * rr, cy + math.sin(a) * rr], fill=(40, 40, 50, 255), width=int(r * 0.18))
        d.ellipse([cx - r * 0.15, cy - r * 0.15, cx + r * 0.15, cy + r * 0.15], fill=(230, 230, 240, 255))
    # luz de bajos
    dg.line([P((0.18, 0.0)), P((0.85, 0.0))], fill=glow_col, width=10)
    return im, gl

def bill_sprite():
    w, h = 170, 78
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 6, fill=(70, 160, 90, 255), outline=(30, 90, 50, 255), width=4)
    d.rounded_rectangle([10, 9, w - 11, h - 10], 4, outline=(170, 230, 170, 255), width=2)
    d.ellipse([w / 2 - 24, h / 2 - 24, w / 2 + 24, h / 2 + 24], fill=(120, 200, 130, 255), outline=(30, 90, 50, 255), width=3)
    f = font(40); tw, th, b = text_size("$", f)
    d.text((w / 2 - tw / 2 - b[0], h / 2 - th / 2 - b[1]), "$", font=f, fill=(20, 70, 35, 255))
    for cx in (24, w - 24):
        d.text((cx - 9, 14), "1", font=font(20), fill=(30, 90, 50, 255))
    return im
BILL = None

# ------------------------------------------------------------------ fondos estáticos (cacheados)
_BG = {}
def bg(name):
    if name not in _BG: _BG[name] = BGS[name]()
    return _BG[name]

def bg_city_night():
    rng = np.random.default_rng(11)
    a = grad([(0, (8, 2, 28)), (0.35, (40, 6, 70)), (0.55, (160, 30, 120)), (0.62, (255, 110, 120)), (1, (20, 4, 40))])
    a = stars(a, 500, rng, 900)
    img = to_img(a).convert("RGBA")
    moon = Image.new("RGB", (BW, BH)); dm = ImageDraw.Draw(moon); dm.ellipse([860, 380, 1080, 600], fill=(255, 190, 230))
    img = add_glow(img, moon, (4, 60, 160), (0.4, 0.5, 0.4)).convert("RGBA")
    base = 1460
    for li, (dense, tall, k) in enumerate([(1.6, 0.8, 0.6), (1.0, 1.25, 1.0)]):
        lay, neon = skyline(BW, BH, base, rng, dense=dense, tall=tall)
        if li == 0:
            lay = Image.fromarray((arr(lay) * np.array([0.6, 0.6, 0.8, 1])).astype(np.uint8), "RGBA")
        img.alpha_composite(lay)
        img = add_glow(img, neon, (3, 14, 40), (0.8 * k, 0.7 * k, 0.4 * k)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, base, BW, BH], fill=(10, 4, 26, 255))
    img = reflect(img.convert("RGB"), base, 0.55, 3).convert("RGBA")
    # paseo y palmeras en primer plano
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1820, BW, BH], fill=(6, 2, 14, 255))
    hl = Image.new("RGB", (BW, BH)); ImageDraw.Draw(hl).line([0, 1822, BW, 1822], fill=PINK, width=6)
    img = add_glow(img, hl).convert("RGBA")
    d = ImageDraw.Draw(img)
    for x, h, ln in [(60, 1250, 0.18), (1240, 1350, -0.2), (330, 900, 0.1)]:
        palm(d, x, 1840, h, ln, (4, 0, 10, 255), rng)
    return img.convert("RGB")

def bg_street():
    rng = np.random.default_rng(5)
    a = grad([(0, (10, 0, 30)), (0.4, (60, 10, 90)), (0.52, (255, 70, 140)), (1, (5, 0, 15))])
    img = to_img(a).convert("RGBA")
    hz = 1000
    lay, neon = skyline(BW, BH, hz, rng, dense=1.4, tall=0.9)
    img.alpha_composite(lay); img = add_glow(img, neon).convert("RGBA")
    d = ImageDraw.Draw(img)
    vx = BW / 2
    d.polygon([(vx - 30, hz), (vx + 30, hz), (BW + 900, BH), (-900, BH)], fill=(16, 8, 30, 255))
    d.rectangle([0, hz, BW, hz + 6], fill=(30, 10, 50, 255))
    ln = Image.new("RGB", (BW, BH)); dl = ImageDraw.Draw(ln)
    for side in (-1, 1):
        dl.line([(vx + side * 30, hz), (vx + side * (BW / 2 + 900), BH)], fill=CYAN if side < 0 else PINK, width=8)
    for k in range(10):
        s0 = (k / 10) ** 2; s1 = ((k + 0.45) / 10) ** 2
        y0 = hz + (BH - hz) * s0; y1 = hz + (BH - hz) * s1
        dl.polygon([(vx - 3 - 20 * s0, y0), (vx + 3 + 20 * s0, y0), (vx + 3 + 20 * s1, y1), (vx - 3 - 20 * s1, y1)], fill=(255, 220, 120))
    img = add_glow(img, ln, (4, 18, 50), (0.7, 0.6, 0.3)).convert("RGBA")
    d = ImageDraw.Draw(img)
    for x, h, l in [(-60, 1500, 0.15), (BW + 40, 1600, -0.15), (160, 1000, 0.08), (BW - 150, 1050, -0.1)]:
        palm(d, x, BH - 80, h, l, (3, 0, 8, 255), rng)
    return img.convert("RGB")

def bg_sunset():
    rng = np.random.default_rng(21)
    hz = 1240
    a = grad([(0, (30, 0, 60)), (0.3, (140, 20, 120)), (0.5, (255, 90, 90)), (hz / BH, (255, 180, 90)), (hz / BH + 0.001, (60, 20, 90)), (1, (10, 0, 30))])
    img = to_img(a)
    # sol a franjas
    sun = Image.new("RGB", (BW, BH)); ds = ImageDraw.Draw(sun)
    cx, cy, r = BW / 2, hz - 120, 330
    ds.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 220, 90))
    sa = arr(sun)
    yy = np.arange(BH)[:, None]
    g = np.clip((yy - (cy - r)) / (2 * r), 0, 1)
    col = np.array([255, 230, 100]) * (1 - g[..., None]) + np.array([255, 40, 140]) * g[..., None]
    m = (sa[..., 0] > 0)[..., None]
    stripes = ((yy - cy) > 0) & ((((yy - cy) // 18) % 3) == 0) & (yy < hz)
    sa = np.where(m & ~stripes[..., None], col, 0)
    sun = to_img(sa)
    img = add_glow(img, sun, (2, 50, 150), (0.3, 0.5, 0.45))
    img = img.convert("RGBA"); d = ImageDraw.Draw(img)
    # islas / ciudad lejana
    lay, neon = skyline(BW, BH, hz, rng, dense=2.4, tall=0.35, night=0.4)
    lay = Image.fromarray((arr(lay) * np.array([0.8, 0.5, 0.9, 1])).astype(np.uint8), "RGBA")
    img.alpha_composite(lay)
    img = reflect(img.convert("RGB"), hz, 0.7, 9).convert("RGBA")
    # destellos en el agua
    d = ImageDraw.Draw(img)
    for _ in range(260):
        y = rng.uniform(hz + 10, hz + 520); x = BW / 2 + rng.normal(0, 90 + (y - hz) * 0.5)
        l = rng.uniform(10, 50) * (1 + (y - hz) / 300)
        d.line([x - l, y, x + l, y], fill=(255, 210, 150, 200), width=2)
    return img.convert("RGB")

def bg_alarm():
    a = grad([(0, (40, 0, 4)), (0.5, (110, 0, 10)), (1, (30, 0, 2))])
    img = to_img(a)
    # ciudad en silueta roja
    rng = np.random.default_rng(2)
    lay, neon = skyline(BW, BH, 2000, rng, neon_cols=(RED,), dense=1.2, tall=1.2, night=0.4)
    lay = Image.fromarray((arr(lay) * np.array([1.6, 0.3, 0.3, 1])).astype(np.uint8), "RGBA")
    img = img.convert("RGBA"); img.alpha_composite(lay)
    # líneas de escaneo
    a = arr(img.convert("RGB")); a[::4] *= 0.7
    return to_img(a)

def bg_vault():
    a = grad([(0, (2, 20, 10)), (0.5, (10, 60, 30)), (1, (0, 10, 5))])
    rng = np.random.default_rng(4)
    img = to_img(a).convert("RGBA"); d = ImageDraw.Draw(img)
    f = font(150)
    for i in range(70):
        x, y = rng.uniform(0, BW), rng.uniform(0, BH)
        d.text((x, y), "$", font=f, fill=(40, 140, 70, int(rng.uniform(30, 80))))
    rays = Image.new("RGB", (BW, BH)); dr = ImageDraw.Draw(rays)
    for k in range(16):
        ang = k * math.pi / 8
        dr.polygon([(BW / 2, BH / 2), (BW / 2 + math.cos(ang) * 3000, BH / 2 + math.sin(ang) * 3000),
                    (BW / 2 + math.cos(ang + 0.12) * 3000, BH / 2 + math.sin(ang + 0.12) * 3000)], fill=(40, 120, 40))
    return add_glow(img, rays.filter(ImageFilter.GaussianBlur(30)), (40,), (0.6,))

def bg_showroom():
    a = grad([(0, (6, 2, 20)), (0.55, (30, 10, 60)), (0.62, (60, 20, 90)), (1, (10, 4, 22))])
    img = to_img(a)
    sp = Image.new("RGB", (BW, BH)); d = ImageDraw.Draw(sp)
    for x0, c in [(BW * 0.25, PINK), (BW * 0.75, CYAN), (BW * 0.5, (255, 255, 255))]:
        d.polygon([(x0 - 40, 0), (x0 + 40, 0), (BW / 2 + 420, 1500), (BW / 2 - 420, 1500)], fill=tuple(int(v * 0.35) for v in c))
    img = add_glow(img, sp.filter(ImageFilter.GaussianBlur(40)), (60,), (0.5,))
    # suelo reflectante con rejilla neón
    gl = Image.new("RGB", (BW, BH)); dg = ImageDraw.Draw(gl)
    hz = 1240
    for k in range(-14, 15):
        dg.line([(BW / 2 + k * 40, hz), (BW / 2 + k * 260, BH)], fill=(110, 30, 160), width=2)
    for k in range(12):
        y = hz + (BH - hz) * (k / 12) ** 1.8
        dg.line([(0, y), (BW, y)], fill=(110, 30, 160), width=2)
    return add_glow(img, gl, (3, 12), (0.6, 0.4))

def bg_panorama():
    """Panorámica ancha de la ciudad para el paneo final."""
    rng = np.random.default_rng(31)
    w = 2600
    a = grad([(0, (12, 0, 40)), (0.35, (90, 10, 120)), (0.5, (255, 80, 130)), (0.58, (255, 170, 110)), (0.62, (30, 6, 60)), (1, (8, 0, 20))], w, BH)
    a = stars(a, 600, rng, 800)
    img = to_img(a).convert("RGBA")
    base = 1440
    for dense, tall in [(1.8, 0.7), (1.1, 1.3)]:
        lay, neon = skyline(w, BH, base, rng, dense=dense, tall=tall)
        img.alpha_composite(lay); img = add_glow(img, neon, (3, 14, 40), (0.8, 0.7, 0.4)).convert("RGBA")
    img = reflect(img.convert("RGB"), base, 0.55, 7).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1900, w, BH], fill=(5, 0, 12, 255))
    for x in range(-50, w + 100, 330):
        palm(d, x + rng.uniform(-60, 60), 1930, rng.uniform(900, 1300), rng.uniform(-0.2, 0.2), (3, 0, 9, 255), rng)
    return img.convert("RGB")

BGS = dict(city=bg_city_night, street=bg_street, sunset=bg_sunset, alarm=bg_alarm, vault=bg_vault,
           showroom=bg_showroom, pano=bg_panorama)

# ------------------------------------------------------------------ cámara
def camera(img, zoom, cx=0.5, cy=0.5, shake=0.0, t=0.0, rot=0.0):
    """Recorta una ventana del fondo grande (zoom >= 1 respecto a 1080x1920 sobre BW x BH)."""
    iw, ih = img.size
    s = min(iw / W, ih / H)
    cw, ch = W * s / zoom, H * s / zoom
    x = cx * iw - cw / 2 + shake * 30 * math.sin(t * 61.0)
    y = cy * ih - ch / 2 + shake * 30 * math.cos(t * 47.0)
    x = min(max(x, 0), iw - cw); y = min(max(y, 0), ih - ch)
    out = img.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((W, H), Image.BILINEAR)
    if rot:
        out = out.rotate(rot, resample=Image.BILINEAR, expand=False).resize((W, H))
    return out

# ------------------------------------------------------------------ planos (t local, d duración, T global)
def cars_streaks(img, t, y0, y1, n=10, seed=0, speed=2600):
    """Coches pasando a toda velocidad: faros blancos y pilotos rojos con estela."""
    gl = Image.new("RGB", img.size); d = ImageDraw.Draw(gl)
    r = np.random.default_rng(seed)
    for k in range(n):
        lane = r.uniform(y0, y1); dirn = 1 if k % 2 else -1
        off = r.uniform(0, 4000); v = speed * r.uniform(0.8, 1.3)
        x = ((off + v * t) % 4200) - 1400
        if dirn < 0: x = img.width - x
        col = (255, 245, 220) if dirn > 0 else (255, 40, 50)
        L = r.uniform(250, 600)
        d.line([x, lane, x - dirn * L, lane], fill=col, width=int(r.uniform(5, 10)))
        d.line([x, lane + 14, x - dirn * L * 0.8, lane + 14], fill=col, width=4)
    return add_glow(img, gl, (3, 12, 30), (0.9, 0.7, 0.4))

def shot_alarm(t, d, T, variant=0):
    img = bg("alarm").copy()
    pulse = 0.5 + 0.5 * math.sin(T * 2 * math.pi * 2.2)
    a = arr(img); yy, xx = np.ogrid[:BH, :BW]
    vig = ((xx - BW / 2) ** 2 / (BW * 0.55) ** 2 + (yy - BH / 2) ** 2 / (BH * 0.5) ** 2)
    a = a * (0.75 + 0.45 * pulse) + (np.clip(vig - 0.4, 0, 1) * 160 * pulse)[..., None] * np.array([1, 0.05, 0.05])
    img = to_img(a)
    z = 1.05 + 0.10 * ease_io(t / max(d, 0.1)) + (0.12 if variant == 1 else 0)
    out = camera(img, z, shake=0.25 + 0.35 * pulse, t=T).convert("RGBA")
    # contador bajando
    # cuenta atrás; al final del vídeo llega justo a 59,99 para que el bucle empalme
    secs = 59.99 - T * 4.5 if T < 14 else 59.99 + (TOTAL - T) * 4.5
    secs = max(secs, 0.0)
    s_txt = f"{int(secs // 60):02d}:{int(secs % 60):02d}:{int((secs % 1) * 100):02d}"
    draw_text_center(out, s_txt, W / 2, 470, 175, (255, 255, 255), 8, (60, 0, 0), glow=RED, scale=1 + 0.04 * pulse)
    warn = emoji_img("⚠️", 150)
    tri_y = 760
    sc = 1 + 0.08 * pulse
    wi = warn.resize((int(warn.width * sc), int(warn.height * sc)))
    safe_ac(out, wi, (int(W / 2 - wi.width / 2), int(tri_y - wi.height / 2)))
    draw_text_center(out, "LO VAN A QUITAR", W / 2, 950, 128, (255, 255, 255), 10, (0, 0, 0), glow=RED, scale=1 + 0.05 * pulse)
    # barras de alerta
    dd = ImageDraw.Draw(out)
    for yb in (40, H - 70):
        for k in range(-2, 16):
            x0 = k * 120 + (T * 300) % 120
            dd.polygon([(x0, yb), (x0 + 60, yb), (x0 + 30, yb + 30), (x0 - 30, yb + 30)], fill=(255, 210, 0, 230))
    return out

def shot_city(t, d, T):
    img = cars_streaks(bg("city").copy(), T, 1760, 1810, 8, 1)
    return camera(img, 1.08 + 0.18 * ease_io(t / d), 0.5 + 0.06 * (t / d), 0.5)

def shot_street(t, d, T):
    img = bg("street").copy()
    gl = Image.new("RGB", img.size); dd = ImageDraw.Draw(gl)
    hz = 1000; vx = BW / 2
    for k in range(6):
        s = ((T * 0.9 + k / 6) % 1.0) ** 2.2
        y = hz + (BH - hz) * s
        for side, col in ((-1, (255, 250, 230)), (1, (255, 40, 50))):
            x = vx + side * (60 + 560 * s)
            r = 6 + 60 * s
            dd.ellipse([x - r * 1.6, y - r * 0.6, x - r * 0.4, y + r * 0.6], fill=col)
            dd.ellipse([x + r * 0.4, y - r * 0.6, x + r * 1.6, y + r * 0.6], fill=col)
            dd.line([x, y, vx + side * 40, hz], fill=tuple(int(c * 0.35) for c in col), width=max(2, int(r * 0.5)))
    img = add_glow(img, gl, (4, 16, 40), (1.0, 0.8, 0.4))
    return camera(img, 1.25 - 0.15 * ease_out(t / d), 0.5, 0.5, shake=0.15, t=T)

def shot_palms(t, d, T):
    img = cars_streaks(bg("city").copy(), T * 1.2, 1760, 1810, 8, 4)
    return camera(img, 1.55 - 0.2 * ease_io(t / d), 0.2 + 0.25 * (t / d), 0.68)

def title_card(out, t, l1, l2, col, glow):
    s = 1 + 0.6 * math.exp(-t * 10)
    draw_text_center(out, l1, W / 2, 470, 140, (255, 255, 255), 10, (0, 0, 0), scale=s, rot=-4)
    draw_text_center(out, l2, W / 2, 660, 170, col, 12, (0, 0, 0), glow=glow, scale=s * (1 + 0.03 * math.sin(t * 20)), rot=-4)

def shot_title_money(t, d, T):
    img = bg("vault").rotate(t * 25, resample=Image.BILINEAR)
    out = camera(img, 1.25 + 0.15 * t / d, shake=0.1, t=T).convert("RGBA")
    rain(out, T, 14, 7, scale=0.8)
    title_card(out, t, "TRUCO 1:", "DINERO INFINITO", YEL, GREEN)
    return out

def rain(out, T, n, seed, scale=1.0, speed=900):
    global BILL
    if BILL is None: BILL = bill_sprite()
    r = np.random.default_rng(seed)
    for k in range(n):
        x0 = r.uniform(-80, W + 80); ph = r.uniform(0, 1); sp = speed * r.uniform(0.7, 1.3)
        y = ((ph * (H + 300) + sp * T) % (H + 300)) - 150
        x = x0 + 60 * math.sin(T * r.uniform(1, 3) + k)
        ang = (T * r.uniform(60, 200) + k * 40) % 360
        sc = scale * r.uniform(0.7, 1.4)
        bimg = BILL.resize((int(BILL.width * sc), int(BILL.height * sc * abs(math.cos(T * 3 + k)) + 4)))
        bimg = bimg.rotate(ang, expand=True, resample=Image.BILINEAR)
        safe_ac(out, bimg, (int(x - bimg.width / 2), int(y - bimg.height / 2)))

def person(d, cx, base, h, col):
    """Silueta de personaje con gafas de sol y dos maletines."""
    hr = h * 0.065
    d.ellipse([cx - hr, base - h, cx + hr, base - h + hr * 2.3], fill=col)
    d.polygon([(cx - h * 0.04, base - h + hr * 2.1), (cx + h * 0.04, base - h + hr * 2.1), (cx + h * 0.045, base - h * 0.8), (cx - h * 0.045, base - h * 0.8)], fill=col)
    d.polygon([(cx - h * 0.15, base - h * 0.80), (cx + h * 0.15, base - h * 0.80), (cx + h * 0.12, base - h * 0.42), (cx - h * 0.12, base - h * 0.42)], fill=col)
    d.polygon([(cx - h * 0.12, base - h * 0.43), (cx + h * 0.12, base - h * 0.43), (cx + h * 0.10, base), (cx + h * 0.02, base), (cx, base - h * 0.3),
               (cx - h * 0.02, base), (cx - h * 0.10, base)], fill=col)
    for s in (-1, 1):
        d.line([(cx + s * h * 0.14, base - h * 0.78), (cx + s * h * 0.2, base - h * 0.5), (cx + s * h * 0.22, base - h * 0.36)], fill=col, width=int(h * 0.05))
    d.rectangle([cx - hr * 0.9, base - h + hr * 0.9, cx + hr * 0.9, base - h + hr * 1.25], fill=(255, 40, 160, 255))

def briefcase(out, cx, cy, w, open_=True):
    d = ImageDraw.Draw(out)
    h = w * 0.62
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 12, fill=(25, 20, 30, 255), outline=(200, 170, 80, 255), width=5)
    d.rectangle([cx - w * 0.15, cy - h / 2 - 22, cx + w * 0.15, cy - h / 2], outline=(200, 170, 80, 255), width=6)
    if open_:
        for r_ in range(4):
            for c_ in range(3):
                bx = cx - w / 2 + 18 + c_ * (w - 36) / 3; by = cy - h / 2 + 14 + r_ * (h - 28) / 4
                d.rectangle([bx, by, bx + (w - 36) / 3 - 8, by + (h - 28) / 4 - 6], fill=(80, 170, 95, 255), outline=(30, 90, 50, 255), width=2)
                d.rectangle([bx + (w - 36) / 6 - 10, by, bx + (w - 36) / 6 + 2, by + (h - 28) / 4 - 6], fill=(235, 220, 160, 255))

def shot_money_bags(t, d, T):
    img = bg("city")
    out = camera(img, 1.15 + 0.12 * t / d, 0.55, 0.42).convert("RGBA")
    a = arr(out); a[..., :3] *= 0.55; out = Image.fromarray(a.astype(np.uint8), "RGBA")
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(rim)
    person(dr, W / 2, 1720, 1300, (255, 60, 180, 255))
    rim = rim.filter(ImageFilter.GaussianBlur(14))
    out.alpha_composite(rim); out.alpha_composite(rim)
    dp = ImageDraw.Draw(out)
    person(dp, W / 2, 1720, 1290, (6, 2, 12, 255))
    bob = 8 * math.sin(T * 6)
    briefcase(out, W / 2 - 300, 1250 + bob, 320)
    briefcase(out, W / 2 + 300, 1250 - bob, 320)
    rain(out, T, 10, 3, scale=0.9, speed=700)
    draw_text_center(out, "$$$", W / 2, 420, 200, YEL, 10, (0, 0, 0), glow=GREEN, scale=1 + 0.08 * math.sin(T * 12))
    return out

def shot_cash_rain(t, d, T, close=False):
    img = bg("vault")
    out = camera(img, (1.4 if close else 1.1) + 0.1 * t / d, 0.5, 0.5, shake=0.1, t=T).convert("RGBA")
    rain(out, T, 26 if not close else 18, 11 if not close else 5, scale=1.0 if not close else 1.8, speed=1100)
    if close:
        draw_text_center(out, "+ $1.000.000", W / 2, 520, 150, YEL, 10, (0, 0, 0), glow=GREEN, scale=1 + 0.5 * math.exp(-t * 9))
    return out

def shot_counter(t, d, T):
    img = bg("vault")
    out = camera(img, 1.2 - 0.1 * t / d).convert("RGBA")
    rain(out, T, 10, 9, 0.8)
    val = int(99_999_999 * ease_out(t / d) ** 1.4)
    txt = "$" + f"{val:,}".replace(",", ".")
    draw_text_center(out, "TU CUENTA", W / 2, 470, 110, (255, 255, 255), 8, (0, 0, 0))
    draw_text_center(out, txt, W / 2, 660, 150, GREEN, 10, (0, 0, 0), glow=GREEN, scale=1 + 0.03 * math.sin(T * 40))
    a = Image.new("RGBA", (W, H), (0, 0, 0, 0)); da = ImageDraw.Draw(a)
    da.polygon([(W / 2, 800), (W / 2 - 60, 880), (W / 2 + 60, 880)], fill=GREEN + (255,))
    out.alpha_composite(a)
    return out

def shot_title_car(t, d, T):
    img = bg("showroom")
    out = camera(img, 1.3 + 0.1 * t / d, shake=0.1, t=T).convert("RGBA")
    car, gl = car_sprite(820, (255, 210, 0))
    out = draw_car(out, car, gl, W / 2, 1760, 1.0)
    title_card(out, t, "TRUCO 2:", "COCHE GRATIS", YEL, PINK)
    return out

def draw_car(out, car, gl, cx, base, sx, flip=False, sy=1.0):
    if flip:
        car = car.transpose(Image.FLIP_LEFT_RIGHT); gl = gl.transpose(Image.FLIP_LEFT_RIGHT)
    nw = max(4, int(car.width * abs(sx))); nh = int(car.height * sy)
    car = car.resize((nw, nh), Image.BILINEAR); gl = gl.resize((nw, nh), Image.BILINEAR)
    x, y = int(cx - nw / 2), int(base - nh)
    # reflejo
    refl = car.transpose(Image.FLIP_TOP_BOTTOM); al = refl.split()[3].point(lambda v: int(v * 0.3)); refl.putalpha(al)
    safe_ac(out, refl, (x, base))
    safe_ac(out, car, (x, y))
    big = Image.new("RGB", out.size); big.paste(gl, (x, y))
    return add_glow(out.convert("RGB"), big, (3, 14, 40), (1.0, 0.8, 0.5)).convert("RGBA")

def flares(out, T, pts, seed=0):
    gl = Image.new("RGB", out.size); d = ImageDraw.Draw(gl)
    for k, (x, y) in enumerate(pts):
        s = max(0, math.sin(T * 7 + k * 1.7)) ** 6
        if s < 0.05: continue
        L = 160 * s
        d.line([x - L, y, x + L, y], fill=(255, 255, 255), width=3)
        d.line([x, y - L * 0.6, x, y + L * 0.6], fill=(255, 255, 255), width=3)
        d.ellipse([x - 8 * s, y - 8 * s, x + 8 * s, y + 8 * s], fill=(255, 255, 255))
    return add_glow(out.convert("RGB"), gl, (2, 10, 30), (1, 0.8, 0.5)).convert("RGBA")

def shot_car_spin(t, d, T, close=False):
    img = bg("showroom")
    out = camera(img, (1.5 if close else 1.15) + 0.1 * t / d, 0.5, 0.55 if close else 0.5).convert("RGBA")
    dd = ImageDraw.Draw(out)
    base = 1150 if not close else 1180
    # plataforma giratoria
    ang = T * 3.2
    pr = 500 if not close else 600
    dd.ellipse([W / 2 - pr, base - pr * 0.16, W / 2 + pr, base + pr * 0.16], fill=(20, 10, 40, 255), outline=CYAN + (255,), width=6)
    for k in range(12):
        a = ang + k * math.pi / 6
        x = W / 2 + math.cos(a) * pr * 0.92; y = base + math.sin(a) * pr * 0.15
        dd.ellipse([x - 7, y - 4, x + 7, y + 4], fill=PINK + (255,))
    c = math.cos(ang)
    car, gl = car_sprite(860 if not close else 1020, (255, 210, 0), PINK)
    sx = 0.28 + 0.72 * abs(c)
    out = draw_car(out, car, gl, W / 2, base, sx, flip=c < 0)
    pts = [(W / 2 - 300 * sx, base - 180), (W / 2 + 280 * sx, base - 240), (W / 2, base - 330)]
    return flares(out, T, pts)

def shot_coast(t, d, T, close=False):
    img = bg("sunset").copy()
    dd = ImageDraw.Draw(img)
    r = np.random.default_rng(8)
    # carretera de la costa
    ry = 1700
    dd.rectangle([0, ry, BW, BH], fill=(14, 6, 26))
    dd.rectangle([0, ry, BW, ry + 10], fill=(255, 120, 160))
    for k in range(12):
        x = ((k * 260 - T * 2400) % (BW + 300)) - 150
        dd.rectangle([x, ry + 170, x + 130, ry + 184], fill=(255, 220, 140))
    # palmeras pasando (paralaje)
    for k in range(5):
        x = ((k * 420 + 200 - T * 1700) % (BW + 900)) - 450
        palm(dd, x, ry + 40, 1100 + 120 * (k % 2), 0.12, (8, 0, 14), np.random.default_rng(k))
    car, gl = car_sprite(1000 if not close else 1000, (255, 40, 120), CYAN, wheel_rot=-T * 30)
    bob = 3 * math.sin(T * 30)
    img = img.convert("RGBA")
    img = draw_car(img, car, gl, BW / 2 + (60 if close else 0), ry + 300 + bob, 1.0)
    # líneas de velocidad
    sp = Image.new("RGB", img.size); ds = ImageDraw.Draw(sp)
    for k in range(18):
        y = r.uniform(ry - 500, ry + 400); x = ((r.uniform(0, 3000) - T * 3500) % 3000) - 400; L = r.uniform(150, 400)
        ds.line([x, y, x + L, y], fill=(255, 220, 200), width=2)
    img = add_glow(img.convert("RGB"), sp, (2,), (0.4,))
    if close:
        return camera(img, 1.12 + 0.12 * t / d, 0.53, 0.66, shake=0.08, t=T)
    return camera(img, 1.05 + 0.1 * t / d, 0.5, 0.55, shake=0.05, t=T)

def clock_txt(T):
    s = max(0, 23 * 3600 + 59 * 60 + 59 - T * 37)
    return f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d}"

def shot_limited(t, d, T, zoom=False):
    img = bg("city")
    out = camera(img, (1.35 if zoom else 1.12) + 0.12 * t / d, 0.4, 0.45)
    a = arr(out); a *= 0.55; a[..., 0] += 35; out = to_img(a).convert("RGBA")
    on = (int(T * 5) % 2) == 0
    draw_text_center(out, "SOLO POR", W / 2, 430, 130, (255, 255, 255) if on else YEL, 10, (0, 0, 0), glow=RED if on else None)
    draw_text_center(out, "TIEMPO LIMITADO", W / 2, 590, 128, YEL if on else (255, 255, 255), 10, (0, 0, 0), glow=RED if on else None,
                     scale=1.05 if on else 1.0)
    draw_text_center(out, clock_txt(T), W / 2, 820, 150, (255, 255, 255), 8, (60, 0, 0), glow=RED)
    return out

def hourglass(out, cx, cy, h, frac, T):
    d = ImageDraw.Draw(out)
    w = h * 0.55
    glass = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + 30, cy), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2), (cx - 30, cy)]
    d.polygon(glass, fill=(255, 255, 255, 40), outline=(255, 255, 255, 220))
    sand = (255, 200, 60, 255)
    # arena arriba
    ht = (h / 2 - 20) * (1 - frac)
    yt = cy - ht
    wt = 30 + (w / 2 - 30) * (ht / (h / 2))
    d.polygon([(cx - wt, yt), (cx + wt, yt), (cx + 26, cy - 4), (cx - 26, cy - 4)], fill=sand)
    # arena abajo
    hb = (h / 2 - 20) * frac
    d.polygon([(cx - w / 2 + 10, cy + h / 2 - 6), (cx + w / 2 - 10, cy + h / 2 - 6), (cx, cy + h / 2 - 6 - hb * 1.3)], fill=sand)
    d.line([cx, cy, cx, cy + h / 2 - 8], fill=sand, width=6)
    for k in range(8):
        yy = cy + ((T * 900 + k * 40) % (h / 2))
        d.ellipse([cx - 4, yy - 4, cx + 4, yy + 4], fill=(255, 230, 120, 255))
    for yb in (cy - h / 2, cy + h / 2):
        d.rounded_rectangle([cx - w / 2 - 40, yb - 16, cx + w / 2 + 40, yb + 16], 8, fill=(120, 60, 30, 255), outline=(255, 200, 80, 255), width=4)

def shot_hourglass(t, d, T):
    img = bg("city")
    out = camera(img, 1.25 + 0.1 * t / d, 0.6, 0.45)
    a = arr(out); a *= 0.5; out = to_img(a).convert("RGBA")
    hourglass(out, W / 2, 760, 820, 0.35 + 0.6 * t / d, T)
    draw_text_center(out, clock_txt(T), W / 2, 260, 120, (255, 255, 255), 8, (60, 0, 0), glow=RED)
    return out

def shot_follow(t, d, T, close=False):
    img = bg("pano")
    s = BH / H
    cw = W * s
    span = img.width - cw
    if close:
        out = camera(img, 1.25 + 0.12 * t / d, 0.62, 0.5)
    else:
        p = ease_io(t / d)
        x = span * (0.05 + 0.5 * p)
        out = img.crop((int(x), 0, int(x + cw), BH)).resize((W, H), Image.BILINEAR)
    out = cars_streaks(out.resize((W, H)), T, 1780, 1820, 6, 2).convert("RGBA")
    s1 = 1 + 0.35 * math.exp(-max(0, T - SHOT_START["follow_pan"]) * 8)
    draw_text_center(out, "SÍGUEME", W / 2, 470, 190, (255, 255, 255), 12, (0, 0, 0), glow=PINK, scale=s1 * (1 + 0.04 * math.sin(T * 9)))
    tw = draw_text_center(out, "PARA MÁS", W / 2 - 60, 680, 140, YEL, 10, (0, 0, 0), scale=s1)
    fire = emoji_img("🔥", int(140 * s1))
    safe_ac(out, fire, (int(W / 2 - 60 + tw / 2 + 25), int(680 - fire.height / 2 - 10)))
    return out

SHOT_FUNCS = {
    "alarm": lambda t, d, T: shot_alarm(t, d, T, 0),
    "alarm_zoom": lambda t, d, T: shot_alarm(t, d, T, 1),
    "alarm_tease": lambda t, d, T: shot_alarm(t, d, T, 1),
    "city_night": shot_city, "street_cars": shot_street, "palms_neon": shot_palms,
    "title_money": shot_title_money, "money_bags": shot_money_bags,
    "cash_rain": lambda t, d, T: shot_cash_rain(t, d, T, False),
    "cash_rain_close": lambda t, d, T: shot_cash_rain(t, d, T, True),
    "money_counter": shot_counter,
    "title_car": shot_title_car,
    "car_spin": lambda t, d, T: shot_car_spin(t, d, T, False),
    "car_spin_close": lambda t, d, T: shot_car_spin(t, d, T, True),
    "coast_drive": lambda t, d, T: shot_coast(t, d, T, False),
    "coast_drive_close": lambda t, d, T: shot_coast(t, d, T, True),
    "limited": lambda t, d, T: shot_limited(t, d, T, False),
    "limited_zoom": lambda t, d, T: shot_limited(t, d, T, True),
    "hourglass": shot_hourglass,
    "follow_pan": lambda t, d, T: shot_follow(t, d, T, False),
    "follow_close": lambda t, d, T: shot_follow(t, d, T, True),
}
SHOT_START = {}
for a, b, n, si in SHOTS:
    SHOT_START.setdefault(n, a)

# ------------------------------------------------------------------ subtítulos
CAP_Y = 1330
CAP_SIZE = 124
def draw_captions(out, T):
    grp = None
    for a, b, g in CAPS:
        if a <= T < b: grp = g; break
    if not grp: return
    items = []
    for (wa, wb, w, si) in grp:
        if T < wa - 0.02: continue
        key = is_keyword(w)
        txt = w.upper()
        size = CAP_SIZE * (1.28 if key else 1.0)
        pop = 1 + 0.18 * math.exp(-(T - wa) * 22)
        items.append((txt, size, pop, key, wa <= T < wb + 0.05))
    if not items: return
    gap = 34
    widths = [text_size(it[0], font(it[1] * it[2]))[0] for it in items]
    # salto de línea si no cabe
    lines = [[]]; lw = 0
    for it, wdt in zip(items, widths):
        if lw + wdt > W - 120 and lines[-1]:
            lines.append([]); lw = 0
        lines[-1].append((it, wdt)); lw += wdt + gap
    y = CAP_Y - (len(lines) - 1) * 75
    for ln in lines:
        tot = sum(w for _, w in ln) + gap * (len(ln) - 1)
        x = W / 2 - tot / 2
        for (txt, size, pop, key, active), wdt in ln:
            col = YEL if key else (255, 255, 255)
            draw_text_center(out, txt, x + wdt / 2, y, size, col, 13, (0, 0, 0), scale=pop,
                             glow=(255, 160, 0) if key else None)
            x += wdt + gap
        y += 150

# ------------------------------------------------------------------ fotograma completo
def frame(T):
    idx = 0
    for i, (a, b, n, si) in enumerate(SHOTS):
        if a <= T < b: idx = i; break
    else:
        idx = len(SHOTS) - 1
    a, b, name, si = SHOTS[idx]
    t = T - a; d = b - a
    out = SHOT_FUNCS[name](t, d, T)
    if out.mode != "RGBA": out = out.convert("RGBA")
    # zoom brusco en cada corte + en palabras clave
    pz = 0.22 * math.exp(-t / 0.09)
    for kt in KEY_TIMES:
        if 0 <= T - kt < 0.4: pz = max(pz, 0.10 * math.exp(-(T - kt) / 0.08))
    if pz > 0.003:
        z = 1 + pz
        cw, ch = W / z, H / z
        out = out.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.BILINEAR)
    # destello blanco y aberración cromática en el corte
    if t < 0.12:
        k = 1 - t / 0.12
        a_ = arr(out)
        a_[..., 0] = np.roll(a_[..., 0], int(18 * k), axis=1)
        a_[..., 2] = np.roll(a_[..., 2], -int(18 * k), axis=1)
        a_[..., :3] = a_[..., :3] + 120 * k ** 2
        out = Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8), "RGBA")
    draw_captions(out, T)
    # viñeta suave
    return out.convert("RGB")

_VIG = None
def finish(img):
    global _VIG
    if _VIG is None:
        yy, xx = np.ogrid[:H, :W]
        v = 1 - 0.45 * np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2, 0, 1)
        _VIG = v[..., None].astype(np.float32)
    return to_img(arr(img) * _VIG)

def render_chunk(args):
    i0, i1, path = args
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(finish(frame(i / FPS)).tobytes())
    p.stdin.close(); p.wait()
    return path

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "frame":
        os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
        for s in sys.argv[2:]:
            finish(frame(float(s))).save(os.path.join(HERE, "previews", f"frame_{float(s):05.2f}.png"))
    elif mode == "video":
        n = int(round(TOTAL * FPS)); k = os.cpu_count() or 2
        bounds = [round(n * j / k) for j in range(k + 1)]
        jobs = [(bounds[j], bounds[j + 1], os.path.join(HERE, f"chunk_{j:02d}.mp4")) for j in range(k)]
        with Pool(k) as pool:
            paths = pool.map(render_chunk, jobs)
        with open(os.path.join(HERE, "chunks.txt"), "w") as f:
            for pth in paths: f.write(f"file '{pth}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(HERE, "chunks.txt"),
                        "-c", "copy", os.path.join(HERE, "video_only.mp4")], check=True)
        for pth in paths: os.remove(pth)
        os.remove(os.path.join(HERE, "chunks.txt"))
