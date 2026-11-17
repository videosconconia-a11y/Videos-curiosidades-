# Montaje del vídeo: imágenes IA con movimientos de cámara, etalonado cinematográfico,
# subtítulos animados, rótulos de estudios, contadores y efectos visuales.
#   python3 render.py stills 1.0 12.5 ...   -> fotogramas de prueba
#   python3 render.py video 0 1 2 ...        -> escenas (una por segmento del guion)
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS, segment_times, shot_timeline, caption_timeline, total, plain

W, H, FPS = 1080, 1920, 30
BW, BH = 1242, 2208                         # fondo 15 % mayor para mover la cámara
IMG_DIR = os.path.join(HERE, "ai_images")
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FX = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
F_CAP = ImageFont.truetype(FB, 92)
F_TAG = ImageFont.truetype(FX, 40)
F_SRC = ImageFont.truetype(FM, 30)
F_BIG = ImageFont.truetype(FB, 150)
F_MID = ImageFont.truetype(FX, 54)
YEL = (255, 210, 60); WHITE = (255, 255, 255)
TOTAL = total()
SEG = segment_times()
SEGT = {sid: (a, e, b) for sid, a, e, b in SEG}
SHOTS = shot_timeline()
CAPS = caption_timeline()
rng = np.random.default_rng(5)

# ---------------------------------------------------------------- imágenes
_cache = {}
def bg(name):
    if name not in _cache:
        im = Image.open(os.path.join(IMG_DIR, name + ".png")).convert("RGB")
        im = im.resize((BW, BH), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
        _cache[name] = im
    return _cache[name]

# movimiento de cámara por plano: (zoom inicial, zoom final, pan x, pan y)
MOVES = [(1.0, 1.13, 0.0, -0.3), (1.12, 1.0, 0.4, 0.0), (1.0, 1.1, -0.5, 0.2), (1.1, 1.0, 0.0, 0.5),
         (1.02, 1.14, 0.3, 0.3), (1.12, 1.02, -0.3, -0.2)]
SPECIAL = {"hook_eyes": (1.1, 1.0, 0.0, -0.4), "final_look": (1.0, 1.16, 0.0, -0.15),
           "eye_reflection": (1.0, 1.22, 0.0, 0.0), "nose_macro": (1.0, 1.2, 0.0, 0.0),
           "dog_dark_portrait": (1.0, 1.15, 0.0, 0.0)}

def ease(p): return p * p * (3 - 2 * p)

def cam(im, p, mv):
    z0, z1, dx, dy = mv
    z = z0 + (z1 - z0) * (0.35 * p + 0.65 * ease(p))
    cw, ch = W / z, H / z
    sx = (BW - cw) / 2; sy = (BH - ch) / 2
    cx = BW / 2 + dx * (p - 0.5) * sx * 0.9; cy = BH / 2 + dy * (p - 0.5) * sy * 0.9
    return im.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

# ---------------------------------------------------------------- etalonado
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.68)) ** 2)
VIG = np.clip(1.08 - _r ** 2.2 * 0.55, 0.30, 1.0)[..., None]
# degradado inferior/superior para legibilidad de textos y UI de TikTok
GRAD = np.ones((H, 1, 1), np.float32)
GRAD[:, 0, 0] = 1 - 0.40 * np.clip((yy[:, 0] - 1450) / 470, 0, 1) - 0.30 * np.clip((260 - yy[:, 0]) / 260, 0, 1)
GRAIN = [rng.normal(0, 6.5, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]

def grade(arr, warm=0.0):
    # curva en S suave + sombras frías / altas luces cálidas (look documental)
    a = arr / 255.0
    a = a + 0.10 * (a - 0.5) * (1 - np.abs(2 * a - 1))       # contraste medio
    lum = a.mean(axis=2, keepdims=True)
    shadow = np.clip(1 - lum * 2, 0, 1); high = np.clip(lum * 2 - 1, 0, 1)
    a = a + shadow * np.array([-0.012, 0.004, 0.022]) + high * np.array([0.03, 0.012, -0.02]) * (1 + warm)
    a = lum + (a - lum) * 0.92                                 # leve desaturación
    return a * 255.0

# ---------------------------------------------------------------- utilidades de texto
def text_size(d, s, f):
    b = d.textbbox((0, 0), s, font=f); return b[2] - b[0], b[3] - b[1]

def shadow_text(img, xy, s, f, fill, stroke=0, blur=10, alpha=170):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((xy[0] + 3, xy[1] + 6), s, font=f, fill=(0, 0, 0, alpha), stroke_width=stroke, stroke_fill=(0, 0, 0, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(blur)); img.alpha_composite(lay)
    ImageDraw.Draw(img).text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))

# ---------------------------------------------------------------- subtítulos
CAP_CX, CAP_Y = 520, 1235          # centrado algo a la izquierda: lejos de los botones de TikTok
def captions(img, t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return
    a, b, s = cur[-1]
    age = t - a
    k = min(1, age / 0.12)
    sc = 0.78 + 0.22 * (1 - (1 - k) ** 3) + 0.06 * math.sin(k * math.pi)
    parts, hl = [], False
    for w in s.split():
        if w.lstrip("¡¿").startswith("*"): hl = True
        parts.append((w.replace("*", ""), hl))
        if "*" in w.lstrip("¡¿*"): hl = False
    font = F_CAP
    tmp = ImageDraw.Draw(img)
    full = " ".join(p for p, _ in parts)
    while tmp.textlength(full, font=font) > 860: font = ImageFont.truetype(FB, font.size - 4)
    lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x = CAP_CX - d.textlength(full, font=font) / 2
    for i, (wd, h) in enumerate(parts):
        txt = wd + (" " if i < len(parts) - 1 else "")
        if h:   # palabra clave: caja amarilla con texto negro
            tw = d.textlength(wd, font=font)
            d.rounded_rectangle([x - 14, 52, x + tw + 14, 52 + font.size * 1.18], 18, fill=YEL + (255,))
            d.text((x, 60), wd, font=font, fill=(10, 10, 10, 255))
            d.text((x + tw, 60), txt[len(wd):], font=font, fill=WHITE + (255,), stroke_width=8, stroke_fill=(0, 0, 0, 255))
        else:
            d.text((x, 60), txt, font=font, fill=WHITE + (255,), stroke_width=8, stroke_fill=(0, 0, 0, 255))
        x += d.textlength(txt, font=font)
    sh = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); sh.paste((0, 0, 0, 150), (0, 0), lay.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    lay = Image.alpha_composite(sh, lay)
    if abs(sc - 1) > 0.003:
        nw, nh = int(W * sc), int(260 * sc)
        l2 = lay.resize((nw, nh), Image.BILINEAR); lay = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        lay.paste(l2, (int(CAP_CX - CAP_CX * sc), (260 - nh) // 2))
    if age < 0.06: lay.putalpha(lay.split()[3].point(lambda v: int(v * age / 0.06)))
    img.alpha_composite(lay, (0, CAP_Y - 130))

# ---------------------------------------------------------------- gráficos documentales
def fade_in_out(t, a, b, f=0.25):
    return max(0.0, min(1.0, (t - a) / f, (b - t) / f))

def chapter(img, t, a, b, num, label):
    al = fade_in_out(t, a, b, 0.3)
    if al <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    slide = (1 - min(1, (t - a) / 0.35)) ** 2 * -80
    x0 = 70 + slide; y0 = 250
    d.rounded_rectangle([x0, y0, x0 + 76, y0 + 76], 16, fill=YEL + (255,))
    nw, _ = text_size(d, num, F_TAG); d.text((x0 + 38 - nw / 2, y0 + 12), num, font=F_TAG, fill=(10, 10, 10, 255))
    d.text((x0 + 98, y0 + 13), label, font=F_TAG, fill=WHITE + (255,), stroke_width=3, stroke_fill=(0, 0, 0, 200))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    img.alpha_composite(lay)

def source(img, t, a, b, line1, line2):
    if not SHOW_SOURCES: return
    al = fade_in_out(t, a, b, 0.3)
    if al <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    y0 = 1440
    w1 = d.textlength(line1, font=F_SRC); w2 = d.textlength(line2, font=F_SRC)
    wb = max(w1, w2) + 44
    d.rounded_rectangle([70, y0, 70 + wb, y0 + 100], 14, fill=(0, 0, 0, 150))
    d.rectangle([70, y0, 76, y0 + 100], fill=YEL + (255,))
    d.text((96, y0 + 12), line1, font=F_SRC, fill=WHITE + (255,))
    d.text((96, y0 + 52), line2, font=F_SRC, fill=(200, 200, 200, 255))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    img.alpha_composite(lay)

def big_stat(img, t, a, b, value, unit, sub, y=430, count=True):
    al = fade_in_out(t, a, b, 0.25)
    if al <= 0: return
    p = min(1, (t - a) / 1.0); p = 1 - (1 - p) ** 3
    v = value * p if count else value
    s = f"{v:,.0f}".replace(",", ".") if value >= 100 else f"{v:.0f}"
    if unit == "%": s = f"{(value * p):.2f}".replace(".", ",")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = F_BIG
    while d.textlength(s + (unit if unit == "%" else ""), font=f) > 900: f = ImageFont.truetype(FB, f.size - 6)
    full = s + (unit if unit == "%" else "")
    tw = d.textlength(full, font=f)
    d.text((W / 2 - tw / 2, y), full, font=f, fill=YEL + (255,), stroke_width=6, stroke_fill=(0, 0, 0, 255))
    if unit != "%":
        uw = d.textlength(unit, font=F_MID); d.text((W / 2 - uw / 2, y + f.size + 10), unit, font=F_MID, fill=WHITE + (255,), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    fs = F_TAG; sy = y + f.size + (85 if unit != "%" else 20)
    sw = d.textlength(sub, font=fs); d.text((W / 2 - sw / 2, sy), sub, font=fs, fill=(235, 235, 235, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))
    g = lay.filter(ImageFilter.GaussianBlur(18)); g.putalpha(g.split()[3].point(lambda v: int(v * 0.6 * al)))
    lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    img.alpha_composite(g); img.alpha_composite(lay)

PART = rng.random((140, 5))
def scent_particles(img, t, a, b, strength=1.0):
    al = fade_in_out(t, a, b, 0.4) * strength
    if al <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for px, py, ps, sp, ph in PART:
        x = (px * W + 60 * math.sin(t * (0.6 + ph) + ph * 9)) % W
        y = (py * H - t * (40 + 90 * sp)) % H
        r = 2 + ps ** 2 * 9
        c = (255, 220, 150, int((90 + 140 * ps) * al)) if ph > 0.4 else (170, 220, 255, int((80 + 120 * ps) * al))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    g = lay.filter(ImageFilter.GaussianBlur(5)); img.alpha_composite(g); img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))

def scan_line(img, t, a, b):
    al = fade_in_out(t, a, b, 0.3)
    if al <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    y = 300 + ((t - a) / 1.6 % 1) * 1300
    for k in range(60):
        d.line([0, y - k, W, y - k], fill=(90, 200, 255, int(70 * (1 - k / 60) * al)))
    d.line([0, y, W, y], fill=(170, 235, 255, int(220 * al)), width=3)
    img.alpha_composite(lay)

def comment_icon(img, t, a):
    if t < a: return
    k = min(1, (t - a) / 0.35); s = 0.6 + 0.4 * (1 - (1 - k) ** 3) + 0.05 * math.sin(t * 6)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy, R = 520, 330, 85 * s
    d.ellipse([cx - R, cy - R * 0.85, cx + R, cy + R * 0.85], fill=WHITE + (int(235 * k),))
    d.polygon([(cx - R * 0.5, cy + R * 0.55), (cx - R * 0.75, cy + R * 1.1), (cx - R * 0.05, cy + R * 0.78)], fill=WHITE + (int(235 * k),))
    for j in (-1, 0, 1):
        d.ellipse([cx + j * R * 0.42 - 11 * s, cy - 11 * s, cx + j * R * 0.42 + 11 * s, cy + 11 * s], fill=(20, 20, 20, int(255 * k)))
    img.alpha_composite(lay)

HOOK_LINES = [[("TU PERRO PODRÍA SABER", 0)], [("QUE ESTÁS ", 0), ("TRISTE…", 1)],
              [("¡INCLUSO ANTES", 0)], [("DE QUE TÚ MISMO", 0)], [("TE DES ", 0), ("CUENTA!", 1)]]
def hook_title(img, t, end):
    al = min(1, (end - t) / 0.2)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(FB, 84)
    while max(d.textlength("".join(x for x, _ in l), font=f) for l in HOOK_LINES) > 850: f = ImageFont.truetype(FB, f.size - 2)
    y = 960
    for li, line in enumerate(HOOK_LINES):
        k = min(1, max(0, (t - li * 0.07) / 0.18)); dy = (1 - k) * 40
        full = "".join(s for s, _ in line); x = CAP_CX - d.textlength(full, font=f) / 2
        for s, h in line:
            tw = d.textlength(s, font=f); a = int(255 * k)
            if h:
                d.rounded_rectangle([x - 12, y + dy - 4, x + tw + 12, y + dy + f.size * 1.16], 16, fill=YEL + (a,))
                d.text((x, y + dy + 4), s, font=f, fill=(10, 10, 10, a))
            else:
                d.text((x, y + dy + 4), s, font=f, fill=WHITE + (a,), stroke_width=8, stroke_fill=(0, 0, 0, a))
            x += tw
        y += int(f.size * 1.3)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.paste((0, 0, 0, 160), (0, 0), lay.split()[3])
    lay = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), lay)
    if al < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * al)))
    img.alpha_composite(lay)

SHOW_SOURCES = False   # rótulos de estudios desactivados (fuentes en FUENTES.md)

def overlays(img, t):
    S = SEGT
    a, e, b = S["s03"]; chapter(img, t, a, S["s04"][2] - 0.1, "1", "LA CARA")
    source(img, t, a + 0.6, e, "Müller et al., 2015", "Current Biology")
    a, e, b = S["s04"]; source(img, t, a + 0.3, e, "Guo et al., 2009", "Animal Cognition")
    a, e, b = S["s05"]; chapter(img, t, a, b - 0.1, "2", "LA VOZ"); source(img, t, a + 1.5, e, "Andics et al., 2016", "Science")
    a, e, b = S["s07"]; chapter(img, t, a, S["s09"][2] - 0.1, "3", "EL OLFATO")
    w = {x["w"].strip(".,").lower(): x for x in __import__("script_data").load_timings()["s07"]["words"]}
    st = a + w.get("trescientos", {"start": 3.6})["start"]
    big_stat(img, t, st, st + 1.7, 300000000, "RECEPTORES OLFATIVOS", "PERRO")
    st2 = a + w.get("seis", {"start": 6.0})["start"]
    big_stat(img, t, st2 - 0.1, e + 0.25, 6000000, "RECEPTORES OLFATIVOS", "SER HUMANO")
    a, e, b = S["s08"]
    source(img, t, a + 0.4, a + 3.4, "Wilson et al., 2022", "PLOS ONE")
    big_stat(img, t, a + 3.7, b, 93.75, "%", "DE ACIERTO DETECTANDO ESTRÉS", y=430)
    a, e, b = S["s10"]; source(img, t, a + 1.4, e, "Custance & Mayer, 2012", "Animal Cognition")
    a, e, b = S["s11"]; source(img, t, a + 4.0, e, "Nagasawa et al., 2015", "Science")
    a, e, b = S["s14"]; comment_icon(img, t, a + 2.1)

def shot_fx(img, name, t, a, b):
    if name in ("nose_particles", "nose_macro", "dog_sniff_hand", "nose_side"): scent_particles(img, t, a, b + 0.3, 0.9)
    if name in ("dog_mri", "mri_monitor"): scan_line(img, t, a, b)
    if name in ("stress_sweat", "lab_samples", "lab_dog_sample"): scent_particles(img, t, a, b, 0.45)

# ---------------------------------------------------------------- composición
FLASH = []      # destellos en momentos clave
for sid in ("s02", "s03", "s05", "s07", "s10", "s12"):
    FLASH.append(SEGT[sid][0])
WARM_FROM = SEGT["s13"][0]

def shot_at(t):
    for i, (a, b, n) in enumerate(SHOTS):
        if a <= t < b: return i
    return len(SHOTS) - 1

def frame(t, fi=0):
    i = shot_at(t); a, b, name = SHOTS[i]
    mv = SPECIAL.get(name, MOVES[i % len(MOVES)])
    img = cam(bg(name), (t - a) / (b - a + 0.3), mv)
    XF = 0.22
    if i + 1 < len(SHOTS) and t > b - XF:
        a2, b2, n2 = SHOTS[i + 1]
        nxt = cam(bg(n2), (t - a2) / (b2 - a2 + 0.3), SPECIAL.get(n2, MOVES[(i + 1) % len(MOVES)]))
        img = Image.blend(img, nxt, ease((t - (b - XF)) / XF))
    arr = np.asarray(img, np.float32)
    warm = 0.6 * max(0, min(1, (t - WARM_FROM) / 3))
    arr = grade(arr, warm)
    arr = arr * VIG * GRAD
    for h in FLASH:
        u = t - h
        if 0 <= u < 0.3: arr = arr + (1 - u / 0.3) ** 2 * 120
    if t < 0.35: arr = arr * (0.25 + 0.75 * t / 0.35)       # entrada rápida, sin negro largo
    g = GRAIN[fi % len(GRAIN)]
    arr = arr + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    if t > TOTAL - 0.7: arr = arr * max(0, (TOTAL - t) / 0.7)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    shot_fx(img, name, t, a, b)
    overlays(img, t)
    hook_end = SEGT["s00"][2] + 0.15
    if t < hook_end: hook_title(img, t, hook_end)
    elif t < TOTAL - 0.3: captions(img, t)
    return img.convert("RGB")

def render_range(t0, t1, path):
    f0, f1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    tmp = path.replace(".mp4", ".part.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, path)

def parts(n):
    """Divide el vídeo en n trozos con frontera en fotograma exacto."""
    nf = int(round(TOTAL * FPS)); cuts = [round(nf * k / n) for k in range(n + 1)]
    return [(cuts[k] / FPS, cuts[k + 1] / FPS) for k in range(n)]

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]]:
            frame(tt, 0).save(os.path.join(HERE, "stills", f"still_{tt:05.2f}.jpg"), quality=88)
    elif sys.argv[1] == "nparts":
        print(int(sys.argv[2]))
    else:
        n = int(sys.argv[2])
        for k in [int(x) for x in sys.argv[3:]]:
            a, b = parts(n)[k]
            render_range(a, b, os.path.join(HERE, f"part_{k:02}.mp4")); print("part", k, flush=True)
