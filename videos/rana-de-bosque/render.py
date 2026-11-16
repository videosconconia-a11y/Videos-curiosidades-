# Render del vídeo 9:16 (1080x1920, 30 fps): fotos reales con movimiento de cámara, etalonaje,
# escarcha animada, nieve, gráficos de datos, destellos en los golpes y subtítulos dinámicos.
# Uso:  python3 render.py stills 1.0 12.5 ...   (fotogramas de prueba en build/)
#       python3 render.py video 0 1 2 ...        (escenas -> build/scene_XX.mp4)
import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, load_timing, scene_bounds, caption_timeline, shot_timeline, heart_beats
from media import PHOTOS

TM = load_timing(); TOTAL = TM["total"]
BUILD = os.path.join(HERE, "build")
W, H, FPS = 1080, 1920, 30
BW, BH = 1300, 2310          # fondos algo mayores que el encuadre para mover la cámara
rng = np.random.default_rng(3)
FONTS = os.path.join(HERE, "assets", "fonts")
FONT = os.path.join(FONTS, "Poppins-Black.ttf")
FONT_B = os.path.join(FONTS, "Poppins-ExtraBold.ttf")
F_CAP = ImageFont.truetype(FONT, 100)
F_BIG = ImageFont.truetype(FONT, 330)
F_MED = ImageFont.truetype(FONT_B, 92)
F_SM = ImageFont.truetype(FONT_B, 52)
ICE = (127, 227, 255); GOLD = (255, 214, 77)

# ---------------------------------------------------------------- utilidades
def grad(c1, c2, w=BW, h=BH, power=1.0):
    y = (np.linspace(0, 1, h) ** power)[:, None, None]
    a = np.array(c1, float); b = np.array(c2, float)
    return np.broadcast_to(a + (b - a) * y, (h, w, 3)).copy()

def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def glow(img, r=25, k=1.0):
    g = np.asarray(img.filter(ImageFilter.GaussianBlur(r)), float)
    return to_img(np.asarray(img, float) + g * k)

def noise_tex(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((h // scale + 2, w // scale + 2))
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, float) / 255

def ease(p): p = min(max(p, 0.0), 1.0); return p * p * (3 - 2 * p)

def cam(bg, p, mode):
    """Recorte W x H de un fondo BW x BH con zoom/paneo suave. mode = (zoom ini, zoom fin, paneo x, paneo y)."""
    z0, z1, dx, dy = mode
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * (ease(p) * 0.5 + p * 0.5)
    sw, sh = bg.size
    ch = sh / z; cw = ch * W / H
    cx = sw / 2 + dx * (p - 0.5) * (sw - cw); cy = sh / 2 + dy * (p - 0.5) * (sh - ch)
    return bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def text_c(d, y, s, font, fill, stroke=0, sc=(0, 0, 0)):
    w = d.textlength(s, font=font)
    d.text(((W - w) / 2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)

# ---------------------------------------------------------------- fotos reales
_PH = {}
def photo(key):
    """Foto recortada a 9:16 alrededor de su punto de interés, a tamaño BW x BH."""
    if key in _PH: return _PH[key]
    m = PHOTOS[key]
    im = ImageOps.exif_transpose(Image.open(os.path.join(HERE, "assets", m.get("dir", "photos"), m["file"]))).convert("RGB")
    w, h = im.size
    zoom = m.get("zoom", 1.0)
    ch = h / zoom; cw = ch * 9 / 16
    if cw > w: cw = w; ch = cw * 16 / 9
    fx, fy = m.get("focus", (0.5, 0.5))
    x0 = min(max(fx * w - cw / 2, 0), w - cw); y0 = min(max(fy * h - ch / 2, 0), h - ch)
    im = im.resize((BW, BH), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    im = im.filter(ImageFilter.UnsharpMask(2.2, 70, 2))
    _PH[key] = im
    return im

def grade(img, kind, amt=1.0):
    a = np.asarray(img, float)
    lum = a @ np.array([0.299, 0.587, 0.114])
    if kind == "natural":       # contraste suave, sombras frías y luces cálidas (look documental)
        out = a * 1.0
        out += ((lum < 110)[..., None] * np.array([-6, 0, 8]) + (lum > 150)[..., None] * np.array([8, 3, -6]))
        out = (out - 128) * 1.08 + 128
    elif kind == "cold":
        out = a * 0.55 + lum[..., None] * 0.45
        out = out * np.array([0.82, 0.95, 1.15]) + np.array([0, 6, 18])
    elif kind == "frozen":
        out = a * 0.25 + lum[..., None] * 0.75
        out = out * np.array([0.74, 0.92, 1.18]) + np.array([4, 18, 38])
        out = (out - 128) * 1.12 + 128
    elif kind == "warm":
        out = a * np.array([1.1, 1.02, 0.86]) + np.array([12, 6, -4])
        out = (out - 128) * 1.06 + 128
    else:
        out = a
    return to_img(a + (out - a) * amt)

# ---------------------------------------------------------------- escarcha, nieve, partículas (en espacio de pantalla)
def make_ice(w, h, seed=21, seeds=None):
    r = np.random.default_rng(seed)
    img = Image.new("RGB", (w, h)); d = ImageDraw.Draw(img)
    seeds = seeds or [(w * 0.5, h * 0.6), (w * 0.2, h * 0.22), (w * 0.85, h * 0.82), (w * 0.23, h * 0.82), (w * 0.8, h * 0.2)]
    def branch(x, y, ang, L, depth, wdt):
        if depth == 0 or L < 8: return
        x2, y2 = x + L * math.cos(ang), y + L * math.sin(ang)
        d.line([x, y, x2, y2], fill=(170, 225, 255), width=max(1, int(wdt)))
        for k in range(1, 5):
            px, py = x + (x2 - x) * k / 5, y + (y2 - y) * k / 5
            for s in (-1, 1):
                branch(px, py, ang + s * math.pi / 3, L * 0.33 * r.uniform(0.7, 1.1), depth - 1, wdt * 0.6)
        branch(x2, y2, ang + r.normal(0, 0.1), L * 0.6, depth - 1, wdt * 0.8)
    for sx, sy in seeds:
        for k in range(6):
            branch(sx, sy, k * math.pi / 3 + r.uniform(-.1, .1), r.uniform(230, 380) * w / 1300, 4, 5)
    img = glow(img.filter(ImageFilter.GaussianBlur(0.8)), 14, 1.4)
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.min([np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2) for sx, sy in seeds], axis=0)
    return np.asarray(img, float), dist

print("preparando texturas", flush=True)
ICE_CRYST, ICE_DIST = make_ice(BW, BH)
ICE_BASE = grad((4, 14, 34), (10, 40, 70))
ICE_FULL = ICE_BASE + ICE_CRYST
# escarcha de pantalla: cristales + grano fino; crece desde los bordes hacia el centro
_yy, _xx = np.mgrid[0:H, 0:W]
EDGE = np.minimum.reduce([_xx / W, (W - _xx) / W, _yy / W, (H - _yy) / W])      # 0 en el borde
EDGE = EDGE / EDGE.max() + (noise_tex(W, H, 40, 31) - 0.5) * 0.35
_cr = np.asarray(Image.fromarray(np.clip(ICE_CRYST, 0, 255).astype(np.uint8)).resize((W, H)), float).mean(2) / 255
FROST = np.clip(_cr * 1.3 + noise_tex(W, H, 2, 5) ** 7 * 2.2 + noise_tex(W, H, 18, 6) ** 2 * 0.55, 0, 1)
FROST_COL = np.array([228, 242, 255], float)
CENTER_KEEP = 1 - 0.55 * np.clip((EDGE - 0.45) / 0.4, 0, 1)   # el centro (el animal) siempre se intuye

def frost(img, cover):
    """cover 0..1: fracción de la imagen cubierta de escarcha (desde los bordes)."""
    if cover <= 0.001: return img
    a = np.asarray(img, float)
    m = np.clip((cover * 1.15 - EDGE) / 0.22, 0, 1)
    k = (m * (0.2 + 0.8 * FROST) * CENTER_KEEP)[..., None] * 0.9
    return to_img(a * (1 - k) + FROST_COL * k)

FLAKES = rng.random((300, 5))   # x, y, tamaño, velocidad, fase
def draw_snow(img, t, density=1.0, warm=False, big=False):
    d = ImageDraw.Draw(img, "RGBA")
    for fx, fy, fs, sp, ph in FLAKES[:int(len(FLAKES) * density)]:
        s = (2 + fs ** 3 * 13) * (2.0 if big else 1)
        y = (fy * H + t * (60 + sp * 200) * (1 + fs)) % (H + 40) - 20
        x = (fx * W + 40 * math.sin(t * (0.5 + ph) + ph * 6)) % W
        col = (255, 225, 150, int(80 + fs * 110)) if warm else (235, 245, 255, int(100 + fs * 140))
        d.ellipse([x - s, y - s, x + s, y + s], fill=col)

def drips(img, t, n=16):
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(n):
        x = (k * 137 + 40) % W; y = ((t * 700 + k * 333) % (H + 200)) - 100
        d.ellipse([x - 7, y - 12, x + 7, y + 12], fill=(210, 235, 255, 150))

def light_rays(img, p, col=(255, 220, 150), strength=0.22):
    lay = Image.new("RGB", (W // 4, H // 4)); d = ImageDraw.Draw(lay)
    for i in range(6):
        x = (40 + i * 50 + p * 30)
        d.polygon([(W // 4 + 20, -30), (x - 12, H // 4), (x + 12, H // 4)], fill=col)
    lay = lay.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
    return to_img(np.asarray(img, float) + np.asarray(lay, float) * strength)

# ---------------------------------------------------------------- fondos procedurales (si falta una foto)
def bg_dark(c1=(4, 10, 24), c2=(14, 34, 60)): return to_img(grad(c1, c2))

def bg_aurora():
    a = grad((2, 4, 14), (10, 30, 45), power=0.8)
    yy, xx = np.mgrid[0:BH, 0:BW]
    for k, (col, y0, amp, fr) in enumerate([((40, 255, 160), 700, 180, 0.004), ((60, 200, 255), 950, 140, 0.006), ((150, 90, 255), 520, 120, 0.003)]):
        c = y0 + amp * np.sin(xx * fr + k * 2) + 60 * np.sin(xx * fr * 3.1 + k)
        dist = (yy - c)
        band = np.exp(-np.clip(dist, 0, None) / 260) * np.exp(-np.clip(-dist, 0, None) / 25)
        band *= 0.55 + 0.45 * np.sin(xx * 0.03 + k) ** 2
        a += band[..., None] * np.array(col, float) * 0.7
    a[rng.random((BH, BW)) > 0.9985] = 255
    img = to_img(a); d = ImageDraw.Draw(img)
    pts = [(0, 1650)] + [(x, 1650 - 380 * abs(math.sin(x * 0.004 + 1)) - 140 * abs(math.sin(x * 0.013))) for x in range(0, BW + 20, 20)] + [(BW, BH), (0, BH)]
    d.polygon(pts, fill=(8, 14, 24))
    return img

# ---------------------------------------------------------------- gráficos de datos
def ecg(img, t, beats, flat_after=None, color=(60, 255, 120)):
    d = ImageDraw.Draw(img, "RGBA")
    for gy in range(0, H, 90): d.line([0, gy, W, gy], fill=(30, 80, 50, 60))
    for gx in range(0, W, 90): d.line([gx, 0, gx, H], fill=(30, 80, 50, 60))
    pts = []; win = 3.0
    for i in range(0, W, 3):
        tt = t - win + win * i / W; v = 0
        for b in beats:
            u = tt - b
            v += 260 * math.exp(-(u / 0.018) ** 2) - 90 * math.exp(-((u - 0.05) / 0.025) ** 2) + 50 * math.exp(-((u - 0.25) / 0.06) ** 2)
        pts.append((i, 900 - v))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.line(pts, fill=color + (255,), width=9, joint="curve")
    g = lay.filter(ImageFilter.GaussianBlur(14)); img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
    last = [b for b in beats if b <= t]
    dead = (flat_after is not None and t > flat_after) or not last
    bpm = 0 if dead else (int(60 / max(0.3, (last[-1] - last[-2]))) if len(last) > 1 else 40)
    text_c(d, 300, f"{bpm} LPM", F_MED, (255, 70, 70) if bpm == 0 else color)
    # corazón que late
    if last and not dead:
        u = t - last[-1]; s = 1 + 0.25 * math.exp(-u * 8)
    else: s = 1.0
    cx, cy, r = W / 2, 1660, 70 * s
    col = (255, 70, 70, 255) if not dead else (120, 120, 130, 255)
    d.ellipse([cx - r * 1.05, cy - r, cx + r * 0.05, cy + r * 0.05], fill=col)
    d.ellipse([cx - r * 0.05, cy - r, cx + r * 1.05, cy + r * 0.05], fill=col)
    d.polygon([(cx - r * 1.0, cy - r * 0.3), (cx + r * 1.0, cy - r * 0.3), (cx, cy + r * 1.2)], fill=col)

def counter(img, p, target, unit, sub, color, fmt="{:d}"):
    d = ImageDraw.Draw(img, "RGBA")
    v = target * min(1, (p / 0.55)) ** 0.5
    s = fmt.format(int(round(v)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    text_c(dl, 230, s, F_BIG, color + (255,), 6, (0, 20, 40))
    text_c(dl, 610, unit, F_MED, (255, 255, 255, 255), 5)
    g = lay.filter(ImageFilter.GaussianBlur(30))
    img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
    text_c(d, 735, sub, F_SM, (215, 235, 250), 4)

# ---------------------------------------------------------------- definición de planos
# src: clave de foto (media.py) | mode: (zoom ini, zoom fin, paneo x, paneo y) | grade | frost: (ini, fin)
SHOTDEF = {
    "frozen_frog":   dict(src="frog_cold", mode=(1.0, 1.22, 0.1, -0.1), grade="frozen", frost=(0.35, 0.7), snow=0.5),
    "frog_eye":      dict(src="frog_head", mode=(1.35, 1.05, 0.0, 0.0), grade="warm", frost=(1.0, 0.0), snow=0.0, rays=True),
    "frog_hero":     dict(src="frog_hero", mode=(1.0, 1.18, 0.3, 0.0), grade="natural", snow=0.0),
    "frog_side":     dict(src="frog_side", mode=(1.15, 1.0, -0.5, 0.0), grade="natural", snow=0.0),
    "boreal":        dict(src="boreal", mode=(1.0, 1.15, 0.6, 0.0), grade="cold", snow=0.6),
    "aurora":        dict(src="aurora", mode=(1.15, 1.0, -0.5, -0.2), grade="none", snow=0.3),
    "snow_forest":   dict(src="boreal_2", mode=(1.0, 1.2, 0.0, 0.3), grade="cold", snow=1.0),
    "frog_leaves":   dict(src="frog_leaves", mode=(1.2, 1.0, 0.0, 0.4), grade="cold", frost=(0.0, 0.3), snow=0.6),
    "frost_leaves":  dict(src="frost_leaves", mode=(1.0, 1.25, -0.3, 0.2), grade="cold", snow=0.5),
    "snowfall_close": dict(src="oak_frost", mode=(1.0, 1.15, 0.2, 0), grade="cold", grade_amt=0.35, snow=1.0, big=True),
    "frog_freeze":   dict(src="frog_freeze", mode=(1.0, 1.3, 0.0, 0.0), grade="frozen", grade_ramp=True, frost=(0.0, 0.85), snow=0.3),
    "ice_macro":     dict(src="ice_macro", mode=(1.0, 1.3, 0.2, 0.2), grade="cold", snow=0.3),
    "frozen_frog_2": dict(src="frog_cold_2", mode=(1.05, 1.15, 0.0, 0.0), grade="frozen", frost=(0.45, 0.55), snow=0.25, dark=0.1),
    "frog_eye_still": dict(src="frog_head", mode=(1.6, 1.85, 0.0, 0.0), grade="frozen", frost=(0.45, 0.55), snow=0.0, dark=0.35),
    "frog_macro":    dict(src="frog_dark", mode=(1.1, 1.35, 0.0, 0.0), grade="natural", snow=0.0),
    "frog_hero_2":   dict(src="frog_stones", mode=(1.0, 1.15, -0.3, 0.0), grade="warm", grade_amt=0.5, snow=0.0),
    "frog_antifreeze": dict(src="frog_side", mode=(1.0, 1.2, 0.4, 0.0), grade="warm", grade_amt=0.8, frost=(0.55, 0.2), rays=True),
    "frog_track":    dict(src="frog_cold", mode=(1.25, 1.05, -0.2, 0.0), grade="cold", snow=0.7),
    "alaska":        dict(src="alaska", mode=(1.0, 1.18, 0.5, 0.0), grade="cold", snow=0.8),
    "frog_survive":  dict(src="frog_green", mode=(1.25, 1.0, 0.0, 0.0), grade="warm", grade_amt=0.6, rays=True),
    "thaw":          dict(src="frog_side", mode=(1.0, 1.15, 0.2, 0.0), grade="warm", grade_amt=0.7, frost=(0.9, 0.0), drips=True),
    "frog_spring":   dict(src="frog_spring", mode=(1.15, 1.0, 0.3, 0.0), grade="warm", grade_amt=0.6, rays=True),
    "pond":          dict(src="pond", mode=(1.0, 1.2, -0.3, 0.0), grade="warm", grade_amt=0.4),
    "frog_portrait": dict(src="frog_hero_head", mode=(1.0, 1.25, 0.0, 0.0), grade="natural"),
    "frog_eye_end":  dict(src="frog_head", mode=(1.05, 1.5, 0.0, 0.0), grade="cold", grade_ramp=True, frost=(0.0, 0.55), snow=0.4),
}
FALLBACK = {"boreal": "aurora_proc", "aurora": "aurora_proc", "alaska": "aurora_proc", "ice_macro": "ice_grow",
            "frost_leaves": "ice_grow", "pond": "frog_spring", "snow_forest": "aurora_proc"}

# imágenes generadas con IA (assets/ai/<plano>.jpg): si existen, sustituyen a la foto de ese plano
AI_DIR = os.path.join(HERE, "assets", "ai")
if os.path.isdir(AI_DIR):
    for f in sorted(os.listdir(AI_DIR)):
        if f.endswith(".jpg"):
            PHOTOS["ai_" + f[:-4]] = dict(dir="ai", file=f, focus=(0.5, 0.45))
def ai(name):
    return photo("ai_" + name) if "ai_" + name in PHOTOS else None
print("cargando fotos", flush=True)
BG = {"dark": bg_dark(), "lab": bg_dark((6, 16, 30), (20, 50, 70)), "aurora_proc": bg_aurora()}
MOL = rng.random((26, 5)); CELLS = rng.random((14, 3))
STOP, FLAT, BACK = heart_beats(TM)


def photo_or_none(key):
    return photo(key) if key in PHOTOS and os.path.exists(os.path.join(HERE, "assets", PHOTOS[key].get("dir", "photos"), PHOTOS[key]["file"])) else None


def shot_frame(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    # pequeño "punch-in" al entrar en cada plano (montaje más dinámico)
    punch = 1 + 0.06 * max(0, 1 - (t - a) / 0.35) ** 2
    if name in SHOTDEF:
        sd = SHOTDEF[name]
        src = ai(name)
        if src is not None: sd = dict(sd, grade_amt=sd.get("grade_amt", 1.0) * 0.35)
        else: src = photo_or_none(sd["src"])
        if src is None:
            fb = FALLBACK.get(name)
            if fb and fb in SHOTDEF and photo_or_none(SHOTDEF[fb]["src"]) is not None: return shot_frame(fb, t, a, b)
            if fb == "ice_grow" or fb is None and name not in BG: return shot_frame("ice_grow", t, a, b)
            src = BG[fb]
        z0, z1, dx, dy = sd["mode"]
        img = cam(src, p, (z0 * punch, z1 * punch, dx, dy))
        if sd.get("blur"): img = img.filter(ImageFilter.GaussianBlur(sd["blur"]))
        g = sd.get("grade", "none")
        amt = sd.get("grade_amt", 1.0) * (ease(p) if sd.get("grade_ramp") else 1.0)
        if g != "none": img = grade(img, g, amt)
        if "frost" in sd:
            f0, f1 = sd["frost"]; img = frost(img, f0 + (f1 - f0) * ease(p))
        if sd.get("dark"): img = to_img(np.asarray(img, float) * (1 - sd["dark"] * ease(p)))
        if sd.get("rays"): img = light_rays(img, p)
        if sd.get("drips"): drips(img, t)
        if sd.get("snow", 0) > 0: draw_snow(img, t, sd["snow"], big=sd.get("big", False))
        return img
    if name == "ice_grow" and ai(name) is not None:
        img = frost(cam(ai(name), p, (1.0 * punch, 1.25 * punch, 0.2, 0)), 0.1 + 0.5 * ease(p))
        draw_snow(img, t, 0.4); return img
    if name == "ice_grow":
        r = 200 + p * 1700
        m = np.clip((r - ICE_DIST) / 120, 0, 1)[..., None]
        img = cam(to_img(ICE_BASE + ICE_CRYST * m), p, (1.05 * punch, 1.2 * punch, -0.3, 0.2))
        draw_snow(img, t, 0.5); return img
    if name == "stat_65":
        base = ai(name) or photo_or_none(SHOTDEF["frog_freeze"]["src"])
        img = cam(base if base is not None else to_img(ICE_FULL), p, (1.1, 1.25, 0, 0)).filter(ImageFilter.GaussianBlur(4 if ai(name) else 10))
        img = frost(grade(img, "frozen"), 0.7 + 0.25 * p)
        img = to_img(np.asarray(img, float) * 0.55)
        counter(img, p, 65, "%", "DEL AGUA DE SU CUERPO", ICE)
        d = ImageDraw.Draw(img, "RGBA")
        fill = min(1, p / 0.55) * 0.65
        d.rounded_rectangle([140, 850, 940, 910], 30, outline=(200, 240, 255, 255), width=5)
        d.rounded_rectangle([146, 856, 146 + int(788 * fill), 904], 26, fill=ICE + (255,))
        text_c(d, 930, "SE CONVIERTE EN HIELO", F_SM, (255, 255, 255), 4)
        draw_snow(img, t, 0.4); return img
    if name in ("stat_193", "stat_18"):
        base = ai(name) or photo_or_none("aurora_2") or BG["aurora_proc"]
        img = cam(base, 0.3 + p * 0.4, (1.25, 1.35, 0.3 if name == "stat_193" else -0.3, 0)).filter(ImageFilter.GaussianBlur(4 if ai(name) else 9))
        img = to_img(np.asarray(grade(img, "cold"), float) * 0.5 + np.array([0, 8, 24]))
        d = ImageDraw.Draw(img, "RGBA")
        if name == "stat_193":
            counter(img, p, 193, "DÍAS", "SEGUIDOS CONGELADAS", ICE)
            ang = 360 * min(1, p / 0.55) * (193 / 365)
            d.arc([140, 120, 940, 920], -90, -90 + ang, fill=ICE + (255,), width=22)
            d.arc([140, 120, 940, 920], -90 + ang, 270, fill=(255, 255, 255, 50), width=22)
            text_c(d, 1560, "MÁS DE 6 MESES", F_MED, (255, 255, 255), 6)
        else:
            counter(img, p, -18, "°C", "MÍNIMAS EN SU REFUGIO", ICE)
            lvl = min(1, p / 0.55) * 0.85
            x0 = 900
            d.rounded_rectangle([x0, 250, x0 + 60, 760], 30, outline=(255, 255, 255, 230), width=5)
            d.ellipse([x0 - 30, 720, x0 + 90, 840], fill=ICE + (255,))
            d.rounded_rectangle([x0 + 12, 250 + int(480 * lvl), x0 + 48, 750], 18, fill=ICE + (255,))
        draw_snow(img, t, 1.0, big=name == "stat_18"); return img
    if name in ("heartbeat", "heartbeat_back"):
        bg = ai(name)
        img = to_img(np.asarray(cam(bg, p, (1.05, 1.2, 0, 0)), float) * 0.45) if bg is not None else to_img(np.zeros((H, W, 3)) + np.array([2, 8, 5]))
        if name == "heartbeat": ecg(img, t, STOP, flat_after=FLAT)
        else: ecg(img, t, BACK)
        return img
    if name in ("glucose", "cells"):
        if ai(name) is not None:
            img = cam(ai(name), p, (1.0 * punch, 1.2 * punch, 0, 0))
            d = ImageDraw.Draw(img, "RGBA")
            if name == "glucose":
                text_c(d, 230, "GLUCOSA", F_MED, GOLD + (255,), 6); text_c(d, 340, "ANTICONGELANTE NATURAL", F_SM, (255, 255, 255), 4)
            else:
                text_c(d, 230, "HIELO FUERA", F_MED, ICE + (255,), 6); text_c(d, 340, "CÉLULAS A SALVO", F_SM, GOLD + (255,), 4)
            return img
        img = cam(BG["dark"] if name == "glucose" else BG["lab"], p, (1.0, 1.1, 0, 0))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        if name == "glucose":
            for i, (mx, my, ms, sp, ph) in enumerate(MOL):
                cx = mx * W + 60 * math.sin(t * 0.7 + ph * 6); cy = (my * H - t * (40 + sp * 80) * (0.5 + ms)) % H
                R = 30 + ms * 70; rot = t * (0.5 + sp) + ph * 6
                pts = [(cx + R * math.cos(rot + k * math.pi / 3), cy + R * math.sin(rot + k * math.pi / 3)) for k in range(6)]
                col = GOLD if i % 3 else ICE
                d.line(pts + [pts[0]], fill=col + (230,), width=int(4 + ms * 6))
                for q in pts: d.ellipse([q[0] - 7, q[1] - 7, q[0] + 7, q[1] + 7], fill=col + (255,))
            text_c(d, 250, "GLUCOSA", F_MED, GOLD + (255,), 4)
            text_c(d, 360, "C6H12O6", F_SM, (255, 255, 255, 220))
        else:
            for (cxr, cyr, cr) in CELLS:
                cx = cxr * W; cy = cyr * H + 20 * math.sin(t + cxr * 9); R = 90 + cr * 110
                d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(255, 190, 70, 70), outline=(255, 220, 120, 255), width=6)
                d.ellipse([cx - R * 0.3, cy - R * 0.3, cx + R * 0.3, cy + R * 0.3], fill=(255, 160, 60, 180))
            m = cam(to_img(ICE_CRYST), p, (1.0, 1.1, 0, 0))
            ice_rgba = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ice_rgba.paste(m, (0, 0), m.convert("L"))
            lay = Image.alpha_composite(ice_rgba, lay)
            text_c(d, 250, "HIELO FUERA", F_MED, ICE + (255,), 4)
            text_c(d, 360, "CÉLULAS A SALVO", F_SM, GOLD + (255,), 3)
        g = lay.filter(ImageFilter.GaussianBlur(18))
        img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
        return img
    if name == "lab" and ai(name) is not None:
        img = cam(ai(name), p, (1.0 * punch, 1.2 * punch, 0, -0.2))
        d2 = ImageDraw.Draw(img, "RGBA")
        text_c(d2, 230, "CRIOCONSERVACIÓN", F_MED, ICE + (255,), 6); text_c(d2, 340, "DE ÓRGANOS", F_SM, (255, 255, 255), 4)
        return img
    if name == "lab":
        img = cam(BG["lab"], p, (1.0, 1.15, 0, -0.3))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for k in range(5):
            x = 140 + k * 200; top = 640 + (k % 2) * 60
            d.rounded_rectangle([x, top, x + 120, top + 620], 50, outline=(210, 240, 255, 255), width=7)
            lvl = top + 260 + 30 * math.sin(t * 2 + k)
            d.rounded_rectangle([x + 10, lvl, x + 110, top + 610], 45, fill=(90, 200, 255, 170))
            d.rectangle([x - 10, top - 50, x + 130, top], fill=(240, 240, 250, 255))
        g = lay.filter(ImageFilter.GaussianBlur(22)); img.paste(g, (0, 0), g); img.paste(lay, (0, 0), lay)
        fog = Image.new("RGBA", (W, H), (0, 0, 0, 0)); df = ImageDraw.Draw(fog)
        for k in range(12):
            x = (k * 211 + t * 40) % (W + 300) - 150; y = 1350 + 60 * math.sin(k + t)
            df.ellipse([x - 220, y - 90, x + 220, y + 90], fill=(220, 240, 255, 40))
        fog = fog.filter(ImageFilter.GaussianBlur(40)); img.paste(fog, (0, 0), fog)
        d2 = ImageDraw.Draw(img, "RGBA")
        text_c(d2, 300, "CRIOCONSERVACIÓN", F_MED, ICE + (255,), 5)
        text_c(d2, 410, "DE ÓRGANOS", F_SM, (255, 255, 255), 4)
        return img
    if name == "end_card":
        src = ai(name) or photo_or_none("frog_head")
        img = cam(src, p, (1.0, 1.2, 0, 0) if ai(name) else (1.5, 1.75, 0, 0)) if src is not None else to_img(ICE_FULL).resize((W, H))
        img = frost(grade(img, "cold"), 0.55 + 0.2 * p)
        img = to_img(np.asarray(img, float) * (1 - 0.5 * min(1, p * 2)))
        d = ImageDraw.Draw(img, "RGBA")
        if p > 0.1:
            text_c(d, 260, "¿TÚ LO HARÍAS?", F_MED, (255, 255, 255), 6)
            text_c(d, 380, "COMENTA  SÍ  o  NO", F_SM, GOLD, 5)
            cx = W / 2; yb = 480 + 18 * math.sin(t * 8)
            d.polygon([(cx - 45, yb), (cx + 45, yb), (cx, yb + 60)], fill=GOLD)
        return img
    if name in BG:
        return cam(BG[name], p, (1.0, 1.15, 0.3, 0))
    raise KeyError(name)

# ---------------------------------------------------------------- subtítulos
SHOTS = shot_timeline(TM)
CAPS = caption_timeline(TM)
try: HITS = [float(x) for x in open(os.path.join(BUILD, "hits.txt")).read().split()]
except FileNotFoundError: HITS = []
CAP_Y = 1180

def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, s = cur[0]
    age = t - a; k = min(1, age / 0.12)
    sc = 0.78 + 0.22 * k + 0.07 * math.sin(k * math.pi)       # "pop" al aparecer
    parts, hl = [], False
    for w in s.split(" "):
        if w.startswith("*") or w.startswith("¿*"): hl = True
        parts.append((w.replace("*", ""), hl))
        if w.rstrip("…?").endswith("*"): hl = False
    full = " ".join(p[0] for p in parts)
    lay = Image.new("RGBA", (W, 280), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    font = F_CAP
    while d.textlength(full, font=font) > W - 110: font = ImageFont.truetype(FONT, font.size - 6)
    x = (W - d.textlength(full, font=font)) / 2
    any_hl = any(h for _, h in parts)
    for i, (wd, h) in enumerate(parts):
        txt = wd + (" " if i < len(parts) - 1 else "")
        col = (GOLD if "HIELO" not in wd and "CONGEL" not in wd and "°C" not in wd else ICE) if h else (255, 255, 255)
        d.text((x, 70), txt, font=font, fill=col + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255))
        x += d.textlength(txt, font=font)
    shadow = lay.filter(ImageFilter.GaussianBlur(14))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 150), (0, 8), shadow)
    lay = Image.alpha_composite(sh, lay)
    if abs(sc - 1) > 1e-3:
        nw, nh = int(W * sc), int(280 * sc)
        lay2 = lay.resize((nw, nh), Image.BILINEAR); out = Image.new("RGBA", (W, 280), (0, 0, 0, 0))
        out.paste(lay2, ((W - nw) // 2, (280 - nh) // 2)); lay = out
    return lay

# ---------------------------------------------------------------- composición final
_yy2, _xx2 = np.mgrid[0:H, 0:W]
VIG = np.clip(1.15 - (((_xx2 - W / 2) / (W * 0.62)) ** 2 + ((_yy2 - H / 2) / (H * 0.62)) ** 2) * 0.6, 0.25, 1)[..., None]
GRAIN = [(rng.standard_normal((H // 2, W // 2)) * 4) for _ in range(4)]
XF = 0.16

def frame(t, fi):
    i = next((k for k, s in enumerate(SHOTS) if s[0] <= t < s[1]), len(SHOTS) - 1)
    a, b, name = SHOTS[i]
    img = shot_frame(name, t, a, b)
    if i + 1 < len(SHOTS) and t > b - XF:                 # fundido rápido al siguiente plano
        a2, b2, n2 = SHOTS[i + 1]
        img = Image.blend(img, shot_frame(n2, t, a2, b2), (t - (b - XF)) / XF)
    arr = np.asarray(img, float) * VIG
    for h in HITS:                                       # destello en los datos clave
        u = t - h
        if 0 <= u < 0.28: arr = arr + (1 - u / 0.28) ** 2 * 150
    arr += np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    # franjas superior/inferior oscurecidas para que los textos de las apps se lean
    if t < 0.3: arr *= t / 0.3
    if t > TOTAL - 0.7: arr *= max(0, (TOTAL - t) / 0.7)
    img = to_img(arr)
    cap = caption_layer(t)
    if cap is not None: img.paste(cap, (0, CAP_Y), cap)
    return img

def render_scene(si, path):
    a, b = scene_bounds(TM)[si]
    f0, f1 = int(round(a * FPS)), int(round(b * FPS))
    tmp = path.replace(".mp4", ".part.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, path)

if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    if sys.argv[1] == "stills":
        for tt in [float(x) for x in sys.argv[2:]]:
            frame(tt, 0).save(os.path.join(BUILD, f"still_{tt:05.1f}.jpg"), quality=85)
    else:
        for si in [int(x) for x in sys.argv[2:]]:
            render_scene(si, os.path.join(BUILD, f"scene_{si:02}.mp4")); print("escena", si, flush=True)
