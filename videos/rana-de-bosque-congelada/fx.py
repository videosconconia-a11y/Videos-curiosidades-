"""Efectos y gráficos procedurales: cámara, escarcha, grietas, nieve, ECG, corazón, mapa, células, tejido."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
_fonts = {}
def font(size, kind="black"):
    k = (size, kind)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype({"black": FONT_BLACK, "bold": FONT_BOLD, "semi": FONT_SEMI}[kind], size)
    return _fonts[k]

ICE = (150, 225, 255); GOLD = (255, 205, 60); YELLOW = (255, 221, 0); RED = (255, 60, 70); GREEN = (80, 255, 160)

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def ease_out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def ease_in(x): x = min(1, max(0, x)); return x ** 3
def clamp01(x): return min(1.0, max(0.0, x))

def arr(im): return np.asarray(im, dtype=np.float32)
def img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# ------------------------------------------------------------------ imágenes
_cache = {}
def load(name, scale=1.25):
    """Carga assets/<name>.jpg reescalada para cubrir W*scale x H*scale (margen para la cámara)."""
    k = (name, scale)
    if k not in _cache:
        im = Image.open(os.path.join(HERE, "assets", name + ".jpg")).convert("RGB")
        tw, th = int(W * scale), int(H * scale)
        r = max(tw / im.width, th / im.height)
        im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        l = (im.width - tw) // 2; t = (im.height - th) // 2
        im = im.crop((l, t, l + tw, t + th)).filter(ImageFilter.UnsharpMask(2, 60, 2))
        _cache[k] = im
    return _cache[k]

def cam(im, zoom=1.0, cx=0.5, cy=0.5, rot=0.0):
    """Encuadre W x H dentro de im: zoom>=1 relativo a la imagen completa, (cx,cy) centro normalizado."""
    sw, sh = im.size
    base = min(sw / W, sh / H)
    cw, ch = W * base / zoom, H * base / zoom
    x0 = min(max(cx * sw - cw / 2, 0), sw - cw); y0 = min(max(cy * sh - ch / 2, 0), sh - ch)
    out = im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    if rot: out = out.rotate(rot, Image.BILINEAR, expand=False)
    return out

def grade(im, temp=0.0, sat=1.0, bright=1.0, contrast=1.0):
    """temp<0 frío (azul), temp>0 cálido."""
    a = arr(im)
    if sat != 1.0:
        g = a.mean(2, keepdims=True); a = g + (a - g) * sat
    if temp:
        a = a * np.array([1 + 0.18 * temp, 1 + 0.03 * temp, 1 - 0.20 * temp], np.float32)
    if contrast != 1.0: a = (a - 128) * contrast + 128
    return img(a * bright)

# ------------------------------------------------------------------ texturas de crecimiento (escarcha / deshielo)
import functools
@functools.lru_cache(maxsize=32)
def fbm(w, h, seed, octaves=5, base=6):
    r = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        sm = r.random((n + 1, int(n * w / h) + 2)).astype(np.float32)
        layer = np.asarray(Image.fromarray((sm * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        out += layer * amp; tot += amp; amp *= 0.5
    return out / tot

_growth = {}
def growth_map(seed=1, origin=(0.5, 1.1)):
    """Mapa 0..1 del momento en que cada píxel se congela (avanza desde 'origin' con bordes fractales)."""
    k = (seed, origin)
    if k not in _growth:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx / W - origin[0]) * 0.75, yy / H - origin[1])
        d = (d - d.min()) / (d.max() - d.min())
        n = fbm(W, H, seed)
        g = d * 0.65 + n * 0.45
        _growth[k] = (g - g.min()) / (g.max() - g.min())
    return _growth[k]

_frost_tex = {}
def frost_texture(seed=3):
    """Textura blanca-azulada de cristales de hielo (dendritas) a tamaño W x H, canal alfa incluido."""
    if seed not in _frost_tex:
        r = np.random.default_rng(seed)
        lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
        def branch(x, y, ang, ln, wdt, depth):
            if depth == 0 or ln < 6: return
            x2 = x + math.cos(ang) * ln; y2 = y + math.sin(ang) * ln
            d.line([(x, y), (x2, y2)], fill=int(120 + 100 * r.random()), width=max(1, int(wdt)))
            for k in range(1, 4):
                t = k / 4; bx = x + (x2 - x) * t; by = y + (y2 - y) * t
                for s in (-1, 1):
                    if r.random() < 0.8:
                        branch(bx, by, ang + s * math.radians(60), ln * 0.35, wdt * 0.6, depth - 1)
            branch(x2, y2, ang + r.normal(0, 0.15), ln * 0.7, wdt * 0.8, depth - 1)
        for _ in range(140):
            x, y = r.uniform(0, W), r.uniform(0, H)
            for k in range(6):
                branch(x, y, k * math.pi / 3 + r.uniform(0, 1), r.uniform(25, 90), 3, 3)
        sharp = lay.filter(ImageFilter.GaussianBlur(0.7))
        glow = lay.filter(ImageFilter.GaussianBlur(6))
        a = np.clip(arr(sharp) * 1.0 + arr(glow) * 0.8, 0, 255) / 255
        speck = (r.random((H, W)) > 0.9985).astype(np.float32)
        speck = arr(img(speck * 255).filter(ImageFilter.GaussianBlur(1.2))) / 255 * 3
        _frost_tex[seed] = np.clip(a + speck, 0, 1)
    return _frost_tex[seed]

def freeze_mix(alive, frozen, p, seed=1, origin=(0.5, 1.1), edge_col=ICE, warm=False):
    """Transición alive→frozen según p (0..1) con frente de hielo brillante. warm=True para deshielo."""
    g = growth_map(seed, origin)
    m = np.clip((p * 1.15 - g) / 0.06, 0, 1)[..., None]
    a = arr(alive) * (1 - m) + arr(frozen) * m
    front = np.exp(-((g - p * 1.15 + 0.03) / 0.025) ** 2)[..., None]
    col = np.array((255, 190, 120) if warm else edge_col, np.float32)
    a = a + front * col * (0.55 if warm else 0.8)
    if not warm:
        ft = frost_texture()[..., None]
        a = a + ft * m * 60 * (0.5 + 0.5 * front)
    return img(a)

def frost_overlay(im, amount, seed=3, sparkle_t=0.0):
    ft = frost_texture(seed)[..., None]
    a = arr(im) + ft * 255 * 0.45 * amount
    if sparkle_t:
        r = np.random.default_rng(int(sparkle_t * 10))
        a = add_sparkles(a, r, n=int(40 * amount))
    return img(a)

def add_sparkles(a, r, n=40, size=26):
    for _ in range(n):
        x, y = int(r.uniform(0, W)), int(r.uniform(0, H)); s = r.uniform(0.3, 1.0)
        L = int(size * s)
        x0, x1 = max(0, x - L), min(W, x + L); y0, y1 = max(0, y - L), min(H, y + L)
        if x1 <= x0 or y1 <= y0: continue
        xx = np.arange(x0, x1) - x; yy = np.arange(y0, y1) - y
        X, Y = np.meshgrid(xx, yy)
        st = (np.exp(-(Y / 1.6) ** 2) * np.exp(-np.abs(X) / (L / 3)) + np.exp(-(X / 1.6) ** 2) * np.exp(-np.abs(Y) / (L / 3)))
        a[y0:y1, x0:x1] += st[..., None] * 255 * s
    return a

# ------------------------------------------------------------------ grietas de hielo
def cracks(p, seed=5, center=(0.5, 0.45), n=9):
    """Capa RGBA con grietas que crecen desde el centro (p 0..1)."""
    r = np.random.default_rng(seed)
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    cx, cy = center[0] * W, center[1] * H
    for k in range(n):
        ang = k * 2 * math.pi / n + r.uniform(-0.3, 0.3)
        pts = [(cx, cy)]; x, y = cx, cy; L = r.uniform(500, 1100) * p
        steps = 18
        for s in range(steps):
            ang += r.normal(0, 0.25); x += math.cos(ang) * L / steps; y += math.sin(ang) * L / steps; pts.append((x, y))
            if r.random() < 0.18 and p > 0.3:
                a2 = ang + r.choice([-1, 1]) * r.uniform(0.5, 1.1); bx, by = x, y; bp = [(bx, by)]
                for _ in range(6):
                    a2 += r.normal(0, 0.3); bx += math.cos(a2) * L / 30; by += math.sin(a2) * L / 30; bp.append((bx, by))
                d.line(bp, fill=170, width=2)
        d.line(pts, fill=255, width=3)
    glow = lay.filter(ImageFilter.GaussianBlur(8))
    a = np.clip(arr(lay) + arr(glow) * 1.2, 0, 255)
    return a / 255

def apply_layer(im, alpha, col=(235, 250, 255), k=1.0):
    a = arr(im); m = (alpha * k)[..., None]
    return img(a * (1 - m) + np.array(col, np.float32) * m)

# ------------------------------------------------------------------ partículas
def snow(im, t, density=1.0, seed=7, wind=40, warm=False):
    r = np.random.default_rng(seed)
    n = int(260 * density)
    x0 = r.uniform(0, W, n); y0 = r.uniform(0, H, n); z = r.uniform(0.2, 1.0, n); ph = r.uniform(0, 6.28, n)
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    for i in range(n):
        y = (y0[i] + t * 160 * z[i]) % (H + 40) - 20
        x = (x0[i] + t * wind * z[i] + 18 * math.sin(t * 1.3 + ph[i])) % W
        s = 2 + 7 * z[i] ** 2
        d.ellipse([x - s, y - s, x + s, y + s], fill=int(140 + 115 * z[i]))
    lay = lay.filter(ImageFilter.GaussianBlur(1.5))
    return apply_layer(im, arr(lay) / 255, (255, 240, 220) if warm else (240, 248, 255), 0.85)

def drips(im, t, seed=9, n=26):
    """Gotas de agua que caen (deshielo)."""
    r = np.random.default_rng(seed); lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    for i in range(n):
        x = r.uniform(40, W - 40); start = r.uniform(0, 2.5); v = r.uniform(500, 900); y0 = r.uniform(-100, H * 0.5)
        tt = (t - start) % 2.5
        y = y0 + 0.5 * v * tt * tt * 2
        if y > H: continue
        d.ellipse([x - 6, y - 14, x + 6, y + 6], fill=200)
        d.line([(x, y - 40), (x, y - 12)], fill=60, width=3)
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    return apply_layer(im, arr(lay) / 255, (230, 245, 255), 0.7)

def light_rays(im, t, col=(255, 210, 140), k=0.35, origin=(0.85, -0.05)):
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    ox, oy = origin[0] * W, origin[1] * H
    for i in range(9):
        a = math.radians(100 + i * 9 + 3 * math.sin(t * 0.6 + i))
        L = 2600; w = math.radians(2.2 + (i % 3))
        d.polygon([(ox, oy), (ox + L * math.cos(a - w), oy + L * math.sin(a - w)), (ox + L * math.cos(a + w), oy + L * math.sin(a + w))], fill=90 + (i % 3) * 40)
    lay = lay.filter(ImageFilter.GaussianBlur(40))
    a = arr(im) + (arr(lay) / 255)[..., None] * np.array(col, np.float32) * k
    return img(a)

def glow_bloom(im, k=0.35, r=30, thr=170):
    a = arr(im); hi = np.clip(a - thr, 0, 255) * (255 / (255 - thr))
    b = arr(img(hi).filter(ImageFilter.GaussianBlur(r)))
    return img(a + b * k)

# ------------------------------------------------------------------ texto
def text_layer(lines, size=96, y=300, col=(255, 255, 255), kind="black", stroke=7, align_x=None, shadow=True, alpha=1.0, spacing=1.08):
    """Dibuja texto centrado. lines: lista de [(texto, color)] por línea o strings."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = font(size, kind)
    yy = y
    for ln in lines:
        segs = ln if isinstance(ln, list) else [(ln, col)]
        widths = [d.textlength(s, font=f) for s, _ in segs]; sp = d.textlength(" ", font=f)
        tw = sum(widths) + sp * (len(segs) - 1)
        x = (W - tw) / 2 if align_x is None else align_x
        for (s, c), w in zip(segs, widths):
            d.text((x, yy), s, font=f, fill=c + (255,), stroke_width=stroke, stroke_fill=(0, 0, 0, 255)); x += w + sp
        yy += size * spacing
    if shadow:
        sh = lay.split()[3].filter(ImageFilter.GaussianBlur(14))
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base.putalpha(sh.point(lambda v: int(v * 0.75)))
        lay = Image.alpha_composite(base, lay)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    return lay

def over(im, lay):
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")

def glow_text(im, s, size, y, col, alpha=1.0, kind="black", glow=1.0, x=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = font(size, kind)
    tw = d.textlength(s, font=f); xx = (W - tw) / 2 if x is None else x
    d.text((xx, y), s, font=f, fill=col + (255,))
    a = lay.split()[3]
    g = arr(a.filter(ImageFilter.GaussianBlur(22))) / 255 * glow
    base = arr(im) + g[..., None] * np.array(col, np.float32) * 0.9 * alpha
    m = arr(a)[..., None] / 255 * alpha
    out = base * (1 - m) + np.array(col, np.float32) * m
    # contorno oscuro sutil para legibilidad
    return img(out)

# ------------------------------------------------------------------ ECG / corazón
def ecg_wave(x):
    """Forma P-QRS-T normalizada, x en [0,1)."""
    return (0.12 * np.exp(-((x - 0.18) / 0.03) ** 2) - 0.15 * np.exp(-((x - 0.30) / 0.008) ** 2)
            + 1.0 * np.exp(-((x - 0.33) / 0.012) ** 2) - 0.3 * np.exp(-((x - 0.36) / 0.01) ** 2)
            + 0.25 * np.exp(-((x - 0.55) / 0.05) ** 2))

def ecg(im, t, beats, y=1050, amp=230, col=GREEN, speed=520, label=None):
    """Monitor ECG: 'beats' = lista de tiempos (locales) de latido. Línea plana sin latidos."""
    a = arr(im) * 0.55
    xs = np.arange(W); head = (t * speed) % (W + 200)
    tx = t - (head - xs) / speed               # tiempo al que corresponde cada x en el trazo
    yv = np.zeros(W)
    for b in beats:
        yv += ecg_wave(np.clip((tx - b) / 0.9, -1, 2)) * ((tx >= b - 0.3) & (tx < b + 0.9))
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    pts = [(x, y - amp * yv[x]) for x in range(0, W) if 0 <= head - x < W - 60]
    if len(pts) > 2: d.line(pts, fill=255, width=6)
    hx = int(head) if head < W else None
    if hx is not None: d.ellipse([hx - 10, y - amp * yv[min(hx, W - 1)] - 10, hx + 10, y - amp * yv[min(hx, W - 1)] + 10], fill=255)
    fade = np.clip(1 - ((head - xs) % (W + 200)) / W, 0, 1)
    L = arr(lay) / 255 * fade[None, :]
    G = arr(lay.filter(ImageFilter.GaussianBlur(10))) / 255 * fade[None, :]
    c = np.array(col, np.float32)
    a = a + (L[..., None] * 1.0 + G[..., None] * 1.4) * c
    # rejilla de monitor
    grid = np.zeros((H, W), np.float32); grid[::60, :] = 1; grid[:, ::60] = 1
    a = a + grid[..., None] * c * 0.06
    out = img(a)
    if label: out = over(out, text_layer([label], 60, y=y + 260, col=col, stroke=4))
    return out

def heart_shape(scale=1.0, cx=W / 2, cy=900):
    tt = np.linspace(0, 2 * np.pi, 200)
    x = 16 * np.sin(tt) ** 3; y = -(13 * np.cos(tt) - 5 * np.cos(2 * tt) - 2 * np.cos(3 * tt) - np.cos(4 * tt))
    return [(cx + 17 * scale * xi, cy + 17 * scale * yi) for xi, yi in zip(x, y)]

def heart(im, beat, frozen=0.0, cx=W / 2, cy=860, scale=1.0, dim=0.45):
    """Corazón brillante; beat 0..1 (pulso), frozen 0..1 (azul escarchado)."""
    a = arr(im) * dim; s = scale * (1 + 0.12 * beat)
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay); d.polygon(heart_shape(s, cx, cy), fill=255)
    m = arr(lay.filter(ImageFilter.GaussianBlur(3))) / 255
    yy, xx = np.mgrid[0:H, 0:W]
    shade = np.clip(1.25 - np.hypot(xx - cx + 90 * s, yy - cy + 120 * s) / (380 * s), 0.25, 1.25)
    warm = np.array((235, 40, 55), np.float32); cold = np.array((150, 200, 240), np.float32)
    col = warm * (1 - frozen) + cold * frozen
    body = shade[..., None] * col
    g = arr(lay.filter(ImageFilter.GaussianBlur(60))) / 255 * (0.6 + 0.8 * beat) * (1 - 0.6 * frozen)
    a = a + g[..., None] * col * 0.9
    a = a * (1 - m[..., None]) + body * m[..., None]
    if frozen > 0:
        ft = frost_texture(11)
        a = a + (ft * m)[..., None] * 255 * 0.6 * frozen
    return img(a)

# ------------------------------------------------------------------ mapa de Norteamérica
_map = {}
RANGE = [(-163, 60), (-166, 64.5), (-162, 67.5), (-152, 68.6), (-141, 69.2), (-135, 68.9), (-128, 68.5),
         (-118, 67.0), (-108, 64.2), (-100, 62.0), (-95, 59.5), (-92, 57.5), (-87, 56.0), (-82, 55.0),
         (-79, 56.5), (-77, 59.5), (-72, 58.8), (-67, 58.2), (-62, 56.5), (-58, 53.5), (-60, 50.0),
         (-62, 46.0), (-66, 44.8), (-70, 43.0), (-71.5, 41.5), (-74, 40.2), (-76.5, 38.8), (-79, 37.3),
         (-82.5, 35.3), (-84.3, 34.7), (-85.0, 35.8), (-84.0, 38.2), (-85.5, 40.5), (-88.5, 41.6),
         (-91.0, 42.6), (-94.5, 44.2), (-97.5, 46.5), (-99.5, 49.0), (-106, 52.0), (-114, 53.5),
         (-118, 55.5), (-123, 57.5), (-128, 59.0), (-135, 59.8), (-141, 60.5), (-149, 60.2),
         (-155, 58.8), (-160, 58.6)]

def proj(lon, lat, lon0=-100, lat0=55, R=1050, cx=W / 2, cy=980):
    lon, lat = np.radians(lon), np.radians(lat); l0, p0 = math.radians(lon0), math.radians(lat0)
    x = np.cos(lat) * np.sin(lon - l0)
    y = math.cos(p0) * np.sin(lat) - math.sin(p0) * np.cos(lat) * np.cos(lon - l0)
    return cx + R * x, cy - R * y

def _map_base():
    if "base" in _map: return _map
    import shapefile
    shp = os.path.join(HERE, "datos", "naturalearth_lowres.shp")
    rd = shapefile.Reader(shp)
    land = Image.new("L", (W, H), 0); dl = ImageDraw.Draw(land)
    bord = Image.new("L", (W, H), 0); db = ImageDraw.Draw(bord)
    for sr, rec in zip(rd.shapes(), rd.records()):
        if rec[1] not in ("North America",) and rec[2] not in ("Greenland", "Russia"): continue
        pts = sr.points; parts = list(sr.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            ring = np.array(pts[a:b])
            if rec[2] == "Russia" and ring[:, 0].max() < 100: continue
            lon = ring[:, 0].copy(); lon[lon > 0] -= 360
            x, y = proj(lon, ring[:, 1])
            poly = list(zip(x, y))
            if len(poly) > 2:
                dl.polygon(poly, fill=255); db.line(poly + [poly[0]], fill=255, width=2)
    rx, ry = proj(np.array([p[0] for p in RANGE]), np.array([p[1] for p in RANGE]))
    rng_m = Image.new("L", (W, H), 0); ImageDraw.Draw(rng_m).polygon(list(zip(rx, ry)), fill=255)
    rng_m = ImageChops.multiply(rng_m, land)
    lon = np.linspace(-200, -20, 400); ax, ay = proj(lon, np.full_like(lon, 66.56))
    _map.update(base=True, land=arr(land.filter(ImageFilter.GaussianBlur(1))) / 255,
                bord=arr(bord) / 255, range=arr(rng_m.filter(ImageFilter.GaussianBlur(2))) / 255,
                arctic=list(zip(ax, ay)))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # orden de "pintado" del área: del sureste (Apalaches) al noroeste (Alaska)
    o = (xx / W) * -0.6 + (yy / H) * 1.0
    _map["order"] = (o - o.min()) / (o.max() - o.min())
    _map["order"] = 1 - _map["order"]
    return _map

def na_map(t, p_range, p_arctic, bg=None):
    m = _map_base()
    a = np.zeros((H, W, 3), np.float32) + np.array((6, 14, 26), np.float32)
    if bg is not None: a = a * 0.3 + arr(bg) * 0.7 * 0.35
    land = m["land"][..., None]
    a = a * (1 - land) + land * np.array((34, 52, 66), np.float32)
    a += m["bord"][..., None] * np.array((90, 130, 150), np.float32) * 0.6
    # área de distribución, aparece en barrido
    rv = np.clip((p_range * 1.2 - m["order"]) / 0.12, 0, 1) * m["range"]
    pulse = 0.85 + 0.15 * math.sin(t * 4)
    a = a * (1 - rv[..., None] * 0.75) + rv[..., None] * np.array((60, 200, 120), np.float32) * pulse
    edge = np.clip(arr(img(rv * 255).filter(ImageFilter.FIND_EDGES)) / 255 * 3, 0, 1)
    a += edge[..., None] * np.array((140, 255, 190), np.float32)
    out = img(a)
    if p_arctic > 0:
        lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
        pts = m["arctic"]; n = int(len(pts) * ease(p_arctic))
        for k in range(0, max(0, n - 1), 6): d.line(pts[k:k + 4], fill=255, width=5)
        g = arr(lay.filter(ImageFilter.GaussianBlur(8))) / 255
        out = img(arr(out) + (arr(lay) / 255 + g * 1.3)[..., None] * np.array(ICE, np.float32))
    return out

# ------------------------------------------------------------------ células (recreación)
def _cells(seed=4, n=26):
    r = np.random.default_rng(seed)
    pts = np.c_[r.uniform(-150, W + 150, n * 2), r.uniform(150, H - 150, n * 2)]
    # relajación de Lloyd aproximada para que queden regulares
    yy, xx = np.mgrid[0:H:8, 0:W:8]
    for _ in range(6):
        d = (xx[..., None] - pts[:, 0]) ** 2 + (yy[..., None] - pts[:, 1]) ** 2
        lab = d.argmin(-1)
        for k in range(len(pts)):
            sel = lab == k
            if sel.any(): pts[k] = (xx[sel].mean(), yy[sel].mean())
    return pts

_cell_cache = {}
def cell_field():
    if "f" not in _cell_cache:
        pts = _cells()
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.stack([np.hypot(xx - px, yy - py) for px, py in pts], -1)
        ds = np.sort(d, -1)
        lab = d.argmin(-1)
        gap = ds[..., 1] - ds[..., 0]               # distancia a la frontera entre células
        cen = pts[lab]
        _cell_cache.update(f=True, gap=gap, lab=lab, d0=ds[..., 0], pts=pts, cx=cen[..., 0], cy=cen[..., 1])
    return _cell_cache

def cells(t, ice=0.0, shrink=0.0, glucose=0.0, survive=0.0):
    """Recreación: células (rosadas) con glucosa (dorada), hielo creciendo en el espacio entre ellas."""
    c = cell_field(); gap = c["gap"]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # radio efectivo: la célula ocupa donde gap > umbral; al encogerse, el umbral crece
    thr = 14 + 70 * shrink
    wob = 4 * np.sin(xx / 37 + t * 1.5) * np.sin(yy / 41 - t)
    inside = np.clip((gap - thr + wob) / 6, 0, 1)
    memb = np.exp(-((gap - thr + wob - 3) / 4) ** 2)
    a = np.zeros((H, W, 3), np.float32) + np.array((8, 18, 40), np.float32)
    # espacio extracelular → hielo
    out_mask = 1 - inside
    g = growth_map(21, (0.5, -0.1))
    icem = np.clip((ice * 1.2 - g) / 0.08, 0, 1) * out_mask
    ft = frost_texture(13)
    a = a + icem[..., None] * (np.array((120, 190, 235), np.float32) + ft[..., None] * 140)
    # interior celular
    shade = np.clip(0.75 + gap / 260, 0, 1.2)
    a = a * (1 - inside[..., None]) + inside[..., None] * shade[..., None] * np.array((190, 80, 105), np.float32)
    a += memb[..., None] * np.array((255, 160, 180), np.float32) * 0.9
    # núcleo
    dn = np.hypot(xx - c["cx"], yy - c["cy"])
    nuc = np.clip((40 - dn) / 4, 0, 1) * inside
    a = a * (1 - nuc[..., None] * 0.6) + nuc[..., None] * np.array((120, 40, 90), np.float32) * 0.6
    out = img(a)
    if glucose > 0:
        r = np.random.default_rng(2); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for (px, py) in c["pts"]:
            for k in range(int(7 * glucose)):
                ang = r.uniform(0, 6.28) + t * r.uniform(-0.6, 0.6); rad = r.uniform(30, 110) * (1 - 0.4 * shrink)
                x, y = px + rad * math.cos(ang), py + rad * math.sin(ang); s = 10
                hexp = [(x + s * math.cos(j * math.pi / 3), y + s * math.sin(j * math.pi / 3)) for j in range(6)]
                d.polygon(hexp, outline=GOLD + (255,), fill=(255, 210, 90, 150))
        gl = lay.filter(ImageFilter.GaussianBlur(5))
        out = Image.alpha_composite(Image.alpha_composite(out.convert("RGBA"), gl), lay).convert("RGB")
    return out

# ------------------------------------------------------------------ corte de tejido (piel / músculo)
def tissue(t, ice):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.zeros((H, W, 3), np.float32)
    skin_y = 520 + 12 * np.sin(xx / 90)
    skin = (yy < skin_y).astype(np.float32)
    n = fbm(W, H, 31, 4, 10)
    a += skin[..., None] * (np.array((120, 90, 60), np.float32) * (0.7 + 0.5 * n[..., None]))
    # fibras musculares: haces ondulados de grosor variable con estrías
    n2 = fbm(W, H, 37, 3, 3)
    yd = yy - skin_y + 120 * (n2 - 0.5) + 25 * np.sin(xx / 210)
    band = (yd // 125).astype(int)
    vpos = (yd % 125) / 125
    thick = 0.75 + 0.25 * np.sin(band * 1.7 + xx / 300)
    fiber = np.clip((np.sin(vpos * np.pi) - (1 - thick)) * 2.2, 0, 1) * (yy > skin_y + 20)
    stri = 0.82 + 0.18 * np.sin(xx / 5.5 + band * 2 + 8 * n2)
    a += fiber[..., None] * stri[..., None] * np.array((175, 60, 70), np.float32) * (0.75 + 0.35 * n[..., None])
    gapm = (1 - fiber) * (yy > skin_y + 10)
    a += gapm[..., None] * np.array((30, 22, 40), np.float32)
    # hielo: nace bajo la piel y baja por los espacios entre fibras
    under = np.clip(1 - np.abs(yy - skin_y - 15) / 22, 0, 1)
    depth = np.clip((yy - skin_y) / 1300, 0, 1)
    g = depth * 0.9 + fbm(W, H, 33, 4, 8) * 0.35
    icemask = np.clip((ice * 1.25 - g) / 0.05, 0, 1) * np.clip(gapm + under, 0, 1)
    ft = frost_texture(17)
    a = a * (1 - icemask[..., None] * 0.8) + icemask[..., None] * (np.array((150, 215, 250), np.float32) + ft[..., None] * 120)
    front = np.exp(-((g - ice * 1.25) / 0.03) ** 2) * np.clip(gapm + under, 0, 1)
    a += front[..., None] * np.array(ICE, np.float32) * 0.7
    return img(a)

# ------------------------------------------------------------------ acabado global
_grain = None
def finish(im, t, vign=0.55, grain=7.0):
    global _grain
    if _grain is None:
        r = np.random.default_rng(0); _grain = r.normal(0, 1, (H + 64, W + 64)).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        globals()["_vig"] = 1 - np.clip((np.hypot((xx - W / 2) / W, (yy - H / 2) / H) - 0.28) * 1.5, 0, 1) ** 1.6
    a = arr(im)
    v = _vig[..., None]; a = a * (1 - vign + vign * v)
    ox, oy = int(t * 997) % 64, int(t * 613) % 64
    a += _grain[oy:oy + H, ox:ox + W][..., None] * grain
    return img(a)
