# Render de «LA RESEÑA QUE DESTRUYÓ UNA FAMILIA» (9:16, 1080x1920, 30 fps)
# Uso:  python3 render.py stills 1.0 5.2 ...   |   python3 render.py video 0 1 2 ...   (índices de SHOTS)
import sys, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nfc_common as C
from nfc_common import (W, H, FPS, BW, BH, font, clamp01, ease, ease_out, ease_in, back_out, to_img, arr, over, glow_add,
                        photo, cam, draw_card, draw_phone, ripple, rgb_split)
from characters import draw_char
from script_data import SHOTS, TITLES, LOWER, TOTAL, VOICE, SPEAKER

GOLD = (255, 200, 90); GOLD2 = (200, 140, 40); RED = (200, 20, 40); WHITE = (255, 255, 255); CREAM = (255, 240, 215)
C.CYAN = GOLD            # brillos y ondas de la tarjeta en dorado (estética telenovela)
F_SERIF = "/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf"
F_SERIF_R = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"
F_BLACK = C.F_BLACK; F_BOLD = C.F_BOLD
rng = np.random.default_rng(9)

ENV = {k: (np.load(os.path.join(HERE, "tmp", f"env_{k}.npy")) if os.path.exists(os.path.join(HERE, "tmp", f"env_{k}.npy")) else np.zeros(1))
       for k in ("narr", "rafa", "sofia")}
def mouth(who, t):
    e = ENV[who]; i = int(t * FPS)
    if i >= len(e): return 0.0
    v = e[i]
    return float(np.clip((v - 0.12) * 1.3, 0, 1.0)) * (0.75 + 0.25 * math.sin(t * 37))

# ------------------------------------------------------------------ fondos ilustrados
def grad(c1, c2, w=BW, h=BH):
    y = np.linspace(0, 1, h)[:, None, None]
    return np.broadcast_to(np.array(c1, np.float32) + (np.array(c2, np.float32) - np.array(c1, np.float32)) * y, (h, w, 3)).copy()

def bg_barberia():
    a = grad((40, 70, 64), (22, 40, 36))
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    dam = (np.sin(xx / 38) * np.sin(yy / 38) > 0.55).astype(np.float32)        # papel pintado damasco
    a += dam[..., None] * np.array([18, 26, 20])
    img = to_img(a); d = ImageDraw.Draw(img)
    # espejo con marco dorado
    d.rounded_rectangle([230, 380, 1070, 1300], 60, fill=(120, 150, 160), outline=GOLD2, width=34)
    d.rounded_rectangle([270, 420, 1030, 1260], 40, fill=(150, 175, 185))
    for k in range(3): d.line([380 + k * 160, 460, 300 + k * 160, 1220], fill=(200, 220, 228), width=26)
    # poste de barbero
    d.rounded_rectangle([1130, 420, 1240, 1250], 50, fill=(245, 245, 245), outline=(180, 160, 90), width=10)
    for k in range(9): d.line([1135, 470 + k * 90, 1235, 400 + k * 90], fill=(200, 30, 40), width=22)
    for k in range(9): d.line([1135, 515 + k * 90, 1235, 445 + k * 90], fill=(30, 60, 170), width=14)
    # estante con frascos
    d.rectangle([0, 1380, BW, 1410], fill=(90, 55, 30))
    for k in range(9):
        x = 60 + k * 140; hgt = 120 + (k * 37) % 90
        col = [(170, 80, 40), (60, 120, 160), (200, 180, 90), (120, 40, 90)][k % 4]
        d.rounded_rectangle([x, 1380 - hgt, x + 70, 1380], 18, fill=col)
    d.rectangle([0, 1410, BW, BH], fill=(70, 40, 25))                         # mostrador de madera
    for k in range(12): d.line([0, 1450 + k * 70, BW, 1440 + k * 70], fill=(85, 50, 30), width=4)
    # lámpara cálida
    lamp = Image.new("RGB", (BW, BH)); dl = ImageDraw.Draw(lamp); dl.ellipse([100, 0, 700, 500], fill=(255, 190, 110))
    return to_img(arr(img) + arr(lamp.filter(ImageFilter.GaussianBlur(160))) * 0.35)

def bg_terciopelo(c=(110, 10, 25)):
    a = grad(tuple(int(v * 0.6) for v in c), c)
    xx = np.arange(BW, dtype=np.float32)
    folds = 0.65 + 0.35 * np.sin(xx / 46) ** 2
    a *= folds[None, :, None]
    return to_img(a)

def bg_tormenta():
    a = grad((12, 14, 30), (40, 42, 70))
    r = np.random.default_rng(4)
    small = r.random((BH // 60 + 2, BW // 60 + 2))
    n = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((BW, BH), Image.BICUBIC), np.float32) / 255
    a += (n ** 2)[..., None] * np.array([70, 70, 95])
    return to_img(a)

def bg_puerta():
    a = grad((30, 18, 14), (14, 8, 6)); img = to_img(a); d = ImageDraw.Draw(img)
    d.rectangle([380, 520, 920, 1650], fill=(10, 6, 5))
    return img

BG = {}
def bg(name):
    if name not in BG: BG[name] = {"barberia": bg_barberia, "terciopelo": bg_terciopelo, "tormenta": bg_tormenta, "puerta": bg_puerta}[name]()
    return BG[name]

# ------------------------------------------------------------------ efectos telenovela
yy0, xx0 = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.2 - (((xx0 - W / 2) / (W * 0.6)) ** 2 + ((yy0 - H / 2) / (H * 0.58)) ** 2) * 0.7, 0.18, 1)[..., None]
GRAIN = [rng.standard_normal((H // 2, W // 2)).astype(np.float32) * 6 for _ in range(4)]
PET = rng.random((70, 5))

def soap_grade(img, warmth=1.0, bloom=0.35):
    a = arr(img)
    a = a * np.array([1.0 + 0.08 * warmth, 1.0, 1.0 - 0.12 * warmth]) + np.array([10, 4, -4]) * warmth
    if bloom > 0:
        g = arr(img.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR))
        a = a + np.clip(g - 120, 0, None) * bloom * np.array([1.1, 0.95, 0.7])
    return a

def petals(img, t, n=50, col=(200, 20, 50)):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, y, s, ph, sp in PET[:n]:
        px = (x * W + 80 * math.sin(t * 0.9 + ph * 7)) % W
        py = (y * H + t * (90 + 120 * sp)) % (H + 60) - 30
        r = 10 + s * 18; a = t * (1 + sp * 2) + ph * 9
        pts = [(px + r * math.cos(a), py + r * 0.5 * math.sin(a)), (px + r * 0.3 * math.cos(a + 1.6), py + r * math.sin(a + 1.6)),
               (px - r * math.cos(a), py - r * 0.5 * math.sin(a)), (px - r * 0.3 * math.cos(a + 1.6), py - r * math.sin(a + 1.6))]
        d.polygon(pts, fill=col + (int(160 + 90 * s),))
    return over(img, lay)

def rain(img, t, k=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    r = np.random.default_rng(int(t * 30))
    for _ in range(int(160 * k)):
        x = r.uniform(-200, W); y = r.uniform(-100, H); L = r.uniform(40, 110)
        d.line([x, y, x + L * 0.25, y + L], fill=(200, 210, 240, int(r.uniform(60, 150))), width=2)
    return over(img, lay)

def rays(img, cx, cy, t, col=GOLD, k=1.0, n=14):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        a = i * 2 * math.pi / n + t * 0.25
        d.polygon([(cx, cy), (cx + 2200 * math.cos(a - 0.06), cy + 2200 * math.sin(a - 0.06)), (cx + 2200 * math.cos(a + 0.06), cy + 2200 * math.sin(a + 0.06))],
                  fill=col + (int(70 * k),))
    return over(img, lay.filter(ImageFilter.GaussianBlur(12)))

def shake(img, amt, t):
    if amt <= 0: return img
    dx = int(amt * math.sin(t * 91)); dy = int(amt * math.cos(t * 77))
    out = Image.new("RGB", (W, H)); out.paste(img, (dx, dy)); return out

def zoomed(img, z, cx=W / 2, cy=H / 2):
    if z <= 1.001: return img
    cw, ch = W / z, H / z
    cx = min(max(cx, cw / 2), W - cw / 2); cy = min(max(cy, ch / 2), H - ch / 2)
    return img.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def hand_phone(img, cx, cy, s, screen="busca", t=0):
    d = ImageDraw.Draw(img, "RGBA")
    w, h = 0.5 * s, 0.95 * s
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], s * 0.12, fill=(25, 25, 30))
    d.rounded_rectangle([cx - w * 0.88, cy - h * 0.92, cx + w * 0.88, cy + h * 0.92], s * 0.09, fill=(235, 240, 250))
    if screen == "busca":
        d.rounded_rectangle([cx - w * 0.75, cy - h * 0.7, cx + w * 0.75, cy - h * 0.5], s * 0.05, fill=(255, 255, 255), outline=(180, 180, 190), width=2)
        for k in range(3): d.rounded_rectangle([cx - w * 0.75, cy - h * 0.35 + k * h * 0.25, cx + w * (0.75 - k * 0.2), cy - h * 0.25 + k * h * 0.25], 6, fill=(210, 212, 220))
        # icono de carga girando
        a = t * 6
        d.arc([cx - s * 0.12, cy + h * 0.45, cx + s * 0.12, cy + h * 0.45 + s * 0.24], math.degrees(a), math.degrees(a) + 270, fill=(120, 130, 150), width=max(2, int(s * 0.03)))
    sk = (196, 142, 106)
    for k in range(4): d.rounded_rectangle([cx + w * 0.7, cy - h * 0.3 + k * h * 0.26, cx + w * 1.25, cy - h * 0.08 + k * h * 0.26], s * 0.1, fill=sk)
    d.rounded_rectangle([cx - w * 1.3, cy - h * 0.1, cx - w * 0.6, cy + h * 0.45], s * 0.12, fill=sk)
    return img

def arms_up(img, cx, cy, u, col, skin, t):
    d = ImageDraw.Draw(img, "RGBA")
    wob = 0.12 * math.sin(t * 9)
    for s in (-1, 1):
        sh = (cx + s * 1.6 * u, cy + 2.0 * u); el = (cx + s * 2.3 * u, cy + 0.2 * u); hd = (cx + s * (1.7 + wob) * u, cy - 1.9 * u)
        d.line([sh, el, hd], fill=col, width=int(0.75 * u), joint="curve")
        d.ellipse([hd[0] - 0.38 * u, hd[1] - 0.45 * u, hd[0] + 0.38 * u, hd[1] + 0.35 * u], fill=skin)
    return img

# ------------------------------------------------------------------ rótulos
def gold_text(d_img, xy, txt, f, anchor="mm", hl=False, alpha=255):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x, y = xy
    d.text((x + 6, y + 8), txt, font=f, fill=(0, 0, 0, int(alpha * 0.8)), anchor=anchor)
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text((x, y), txt, font=f, fill=alpha, anchor=anchor)
    if hl:
        fill = Image.new("RGBA", (W, H), (255, 70, 80, 255))
    else:
        g = np.zeros((H, W, 4), np.uint8)
        yy = np.linspace(0, 1, H)[:, None]
        band = (np.sin((yy * H - y) / 22) * 0.5 + 0.5)
        g[..., 0] = (255 * (0.85 + 0.15 * band)).astype(np.uint8); g[..., 1] = (190 + 50 * band).astype(np.uint8); g[..., 2] = (70 + 90 * band).astype(np.uint8); g[..., 3] = 255
        fill = Image.fromarray(g, "RGBA")
    lay.paste(fill, (0, 0), mask)
    d.text((x, y), txt, font=f, fill=None, anchor=anchor, stroke_width=2, stroke_fill=(90, 50, 10, alpha))
    return lay

def title_layer(t):
    cur = [x for x in TITLES if x[0] <= t < x[1]]
    if not cur: return None
    a, b, lines, style, yc = cur[0]
    age = t - a; fade = min(clamp01(age / 0.35), clamp01((b - t) / 0.25))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if style in ("drama", "logo"):
        size = 104 if style == "drama" else 150
        f = font(F_SERIF, size)
        dd = ImageDraw.Draw(lay)
        sizes = []
        for ln in lines:
            s = size
            while dd.textlength(ln.replace("*", ""), font=font(F_SERIF, s)) > W - 100: s -= 4
            sizes.append(s)
        tot = sum(s * 1.05 for s in sizes); y = yc - tot / 2
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(band).rectangle([0, y - 60, W, y + tot + (150 if style == "logo" else 50)], fill=(10, 0, 0, int(150 * fade)))
        lay.alpha_composite(band.filter(ImageFilter.GaussianBlur(40)))
        for i, (ln, s) in enumerate(zip(lines, sizes)):
            li = clamp01((age - i * 0.28) / 0.5)
            if li > 0:
                hl = "*" in ln
                sc = 1.12 - 0.12 * ease_out(li)  # cámara lenta: se asienta despacio
                l2 = gold_text(None, (W / 2, y + s / 2), ln.replace("*", ""), font(F_SERIF, int(s * sc)), hl=hl, alpha=int(255 * li * fade))
                lay.alpha_composite(l2)
            y += s * 1.05
        if style == "logo":
            d2 = ImageDraw.Draw(lay)
            al = int(255 * fade * clamp01((age - 0.6) / 0.4))
            for s in (-1, 1):
                d2.line([W / 2 + s * 120, y + 30, W / 2 + s * 430, y + 30], fill=GOLD + (al,), width=4)
                d2.polygon([(W / 2 + s * 100, y + 30), (W / 2 + s * 115, y + 20), (W / 2 + s * 130, y + 30), (W / 2 + s * 115, y + 40)], fill=GOLD + (al,))
            d2.text((W / 2, y + 95), "CAPÍTULO 1", font=font(F_SERIF_R, 60), fill=CREAM + (al,), anchor="mm")
        return lay
    if style == "shock":
        d = ImageDraw.Draw(lay)
        sc = 1.6 - 0.6 * back_out(age / 0.2)
        fs = 150
        while d.textlength(lines[0], font=font(F_BLACK, fs)) > W - 90: fs -= 4
        f = font(F_BLACK, int(fs * sc))
        jx = 10 * math.sin(t * 80); jy = 8 * math.cos(t * 70)
        d.text((W / 2 + jx, yc + jy), lines[0], font=f, fill=(255, 40, 50, int(255 * fade)), anchor="mm", stroke_width=10, stroke_fill=(255, 255, 255, int(255 * fade)))
        return lay
    if style == "cta":
        d = ImageDraw.Draw(lay)
        y = yc
        for i, ln in enumerate(lines):
            li = clamp01((age - i * 0.12) / 0.2)
            if li <= 0: y += 125; continue
            hl = "*" in ln; txt = ln.replace("*", "")
            s = 118 if hl else 96
            f = font(F_BLACK, int(s * (0.7 + 0.3 * back_out(li))))
            if hl:
                tw = d.textlength(txt, font=f)
                d.rounded_rectangle([W / 2 - tw / 2 - 26, y - s * 0.62, W / 2 + tw / 2 + 26, y + s * 0.62], 26, fill=GOLD + (int(255 * li),))
                d.text((W / 2, y), txt, font=f, fill=(60, 10, 20, int(255 * li)), anchor="mm")
            else:
                d.text((W / 2, y), txt, font=f, fill=WHITE + (int(255 * li),), anchor="mm", stroke_width=6, stroke_fill=(40, 0, 10, int(220 * li)))
            y += 125 if not hl else 150
        return lay
    return None

def lower_third(t):
    for a, b, name, role in LOWER:
        if a <= t < b:
            p = ease_out((t - a) / 0.4); q = clamp01((b - t) / 0.3)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            x0 = -600 + 660 * p; y = 1330
            al = int(255 * q)
            d.rectangle([x0, y, x0 + 600, y + 8], fill=GOLD + (al,))
            d.text((x0 + 10, y + 20), name, font=font(F_SERIF, 92), fill=CREAM + (al,), stroke_width=3, stroke_fill=(40, 10, 10, al))
            d.text((x0 + 14, y + 128), role, font=font(F_SERIF_R, 46), fill=GOLD + (al,), stroke_width=2, stroke_fill=(30, 10, 5, al))
            return lay
    return None

def subtitle_layer(t, timing):
    for a, b, who, text in timing:
        if a <= t < b + 0.15:
            words = text.split(" ")
            # trozos de ~6 palabras repartidos por duración
            chunks = []; cur = []
            for w_ in words:
                cur.append(w_)
                if len(cur) >= 6 or w_.endswith(("…", ".", "?", "!")): chunks.append(" ".join(cur)); cur = []
            if cur: chunks.append(" ".join(cur))
            lens = np.array([len(c) + 6 for c in chunks], float); edges = a + np.concatenate([[0], np.cumsum(lens) / lens.sum() * (b - a)])
            k = min(len(chunks) - 1, int(np.searchsorted(edges, t, "right") - 1))
            txt = chunks[max(0, k)]
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            f = font(F_BOLD, 58) if who != "narr" else font(F_SERIF, 62)
            while d.textlength(txt, font=f) > W - 120: f = font(f.path, f.size - 3)
            y = 1700
            col = {"narr": CREAM, "rafa": (255, 225, 130), "rafa_grito": (255, 225, 130), "sofia": (255, 150, 160)}[who]
            if who != "narr":
                d.text((W / 2, y - 70), "— " + SPEAKER[who] + " —", font=font(F_SERIF_R, 40), fill=col + (230,), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 200))
            d.text((W / 2, y), txt, font=f, fill=WHITE + (255,), anchor="mm", stroke_width=7, stroke_fill=(0, 0, 0, 255))
            return lay
    return None

def logo_bug(t):
    if t < 4.2 or t > 38.3: return None
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((W - 60, 95), "La reseña que", font=font(F_SERIF, 34), fill=GOLD + (170,), anchor="rm")
    d.text((W - 60, 135), "destruyó una familia", font=font(F_SERIF, 34), fill=GOLD + (170,), anchor="rm")
    d.text((W - 60, 178), "CAP. 1", font=font(F_SERIF_R, 28), fill=CREAM + (150,), anchor="rm")
    return lay

# ------------------------------------------------------------------ planos
def shot_frame(name, t, a, b):
    p = clamp01((t - a) / (b - a))
    if name == "faro_acantilado":
        return cam(photo("faro_acantilado"), p, 1.0, 1.18, 0.3, -0.2)
    if name == "faro_puerto":
        img = cam(photo("faro_puerto"), p, 1.15, 1.0, -0.3, 0)
        return to_img(arr(img) * 0.6)
    if name == "rafa_movil":
        img = cam(bg("barberia"), p, 1.0, 1.08).filter(ImageFilter.GaussianBlur(5))
        u = 150 + 25 * ease(p); cx, cy = W / 2, 820
        draw_char(img, cx, cy, u, "rafa", "preocupado", mouth("rafa", t), (0.1, 0.9), 0, t)
        hand_phone(img, cx + 0.3 * u, cy + 3.0 * u, 1.3 * u, "busca", t)
        return img
    if name == "rafa_lagrima":
        img = cam(bg("barberia"), 0.5, 1.4, 1.4).filter(ImageFilter.GaussianBlur(14))
        u = 470 + 160 * ease(p)
        draw_char(img, W / 2 + 60, 880 + 0.25 * u, u, "rafa", "triste", mouth("rafa", t), (0, 0.2), ease((p - 0.1) / 0.7), t, body=True)
        return img
    if name == "puerta_sofia":
        img = bg("puerta").resize((W, H), Image.BILINEAR, box=(110, 195, 1190, 2115)).copy()
        op = ease_out(p / 0.35)
        d = ImageDraw.Draw(img, "RGBA")
        x0, x1, y0, y1 = 270, 810, 330, 1460
        light = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(light)
        dl.rectangle([x0, y0, x0 + (x1 - x0) * op, y1], fill=(255, 220, 150, 255))
        dl.polygon([(x0, y1), (x0 + (x1 - x0) * op, y1), (x0 + (x1 - x0) * op + 300, H), (x0 - 200, H)], fill=(255, 210, 140, 110))
        img = glow_add(over(img, light), light, 60, 0.6)
        lit = clamp01((p - 0.25) / 0.4)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_char(lay, W / 2, 760, 125, "sofia", "chulesca", mouth("sofia", t), (0.3, 0), 0, t)
        if lit < 1:   # silueta a contraluz que se ilumina
            al = np.asarray(lay, np.float32); al[..., :3] *= lit; lay = Image.fromarray(al.astype(np.uint8), "RGBA")
        img = over(img, lay)
        img, q = draw_card(img, W / 2 + 270, 1060 - 40 * ease(p), 0.33, 0.1, -0.3, 0.15, sheen=p * 1.4 - 0.2, glow=1.2, shadow=False)
        d = ImageDraw.Draw(img); d.rounded_rectangle([W / 2 + 200, 1150 - 40 * ease(p), W / 2 + 300, 1260 - 40 * ease(p)], 30, fill=(222, 172, 136))
        return img
    if name == "zoom_shock":
        base = cam(bg("barberia"), 0.5, 1.2, 1.2).filter(ImageFilter.GaussianBlur(8))
        k = min(2, int(p * 3)); sub = (p * 3) % 1
        u = [190, 330, 560][k] * (1 + 0.04 * sub)
        img = base.copy()
        draw_char(img, W / 2, 900 + [0, 0.2, 0.35][k] * u, u, "rafa", "shock", 0, (0, 0), 0, t)
        img = shake(img, 18 * (1 - sub), t)
        if sub < 0.15: img = to_img(arr(img) * np.array([1.0, 0.7, 0.7]) + (1 - sub / 0.15) * np.array([120, 0, 0]))
        return img
    if name == "sofia_ceja":
        img = cam(bg("terciopelo"), p, 1.0, 1.1).filter(ImageFilter.GaussianBlur(4))
        u = 330 + 40 * ease(p)
        draw_char(img, W / 2 - 80, 900, u, "sofia", "chulesca", 0, (0.7, -0.1), 0, t)
        img, q = draw_card(img, W / 2 + 290, 1300, 0.55, 0.05, -0.35 + 0.2 * p, 0.12, sheen=p * 1.5 - 0.3, glow=1.4, shadow=False)
        return img
    if name == "tarjeta_epica":
        img = bg("terciopelo").resize((W, H), Image.BILINEAR, box=(110, 195, 1190, 2115))
        img = to_img(arr(img) * 0.55)
        img = rays(img, W / 2, 900, t, GOLD, 1.0)
        img = C.particles(img, t, 100, GOLD, 25, 4)
        sc = 0.9 + 0.12 * ease(p)
        img, q = draw_card(img, W / 2, 940, sc, 0.15 - 0.1 * p, -0.6 + 1.0 * ease(p), -0.05, sheen=-0.3 + 1.6 * p, glow=1.5, reflect=False)
        return img
    if name == "demo_toque":
        img = cam(bg("barberia"), 0.5, 1.0, 1.0)
        img = to_img(arr(img.filter(ImageFilter.GaussianBlur(10))) * 0.75)
        d = ImageDraw.Draw(img); d.polygon([(0, 1150), (W, 1150), (W, H), (0, H)], fill=(78, 46, 28))
        for k in range(10): d.line([0, 1200 + k * 75, W, 1190 + k * 75], fill=(95, 58, 34), width=4)
        img, q = draw_card(img, W / 2, 1300, 0.95, 0.95, 0.0, -0.06, sheen=p * 1.4 - 0.2, glow=0.9)
        tap = ease(p / 0.3) - ease((p - 0.38) / 0.22)
        if p < 0.38:
            img = draw_phone(img, W / 2 + 40, 1950 - 760 * tap, 0.95, 10 - 6 * tap, "home", 0, t)
        else:
            q2 = (p - 0.38) / 0.62
            img = ripple(img, W / 2, 1300, 0.1 + q2 * 2.2, n=3)
            img = draw_phone(img, W / 2 + 40, 1190 - 420 * ease(q2 / 0.4), 1.0, 4, "banner" if q2 < 0.35 else "review",
                             (q2 / 0.35) if q2 < 0.35 else 0.0, t)
        if 0.28 < p < 0.34: img = to_img(arr(img) + 90)
        return img
    if name in ("murallas", "noray", "calle", "rocas"):
        dirs = {"murallas": (0.3, 0), "noray": (-0.4, 0), "calle": (0, -0.3), "rocas": (0.4, 0.2)}[name]
        img = cam(photo(name), ease_out(p), 1.35, 1.05, *dirs)
        img = to_img(arr(img) * np.array([0.8, 0.82, 0.95]))
        img = rain(img, t, 0.8)
        return img
    if name == "grito_cielo":
        img = cam(bg("tormenta"), p, 1.1, 1.25, 0, -0.5, rot=6 * math.sin(p * 3))
        if (p * 6) % 1 < 0.12 or 0.42 < p < 0.48:   # relámpagos
            img = to_img(arr(img) + 140)
            d = ImageDraw.Draw(img); x = 200 + 600 * ((int(p * 6) * 37) % 10) / 10
            pts = [(x, 0)] + [(x + rng.uniform(-60, 60), k * 120) for k in range(1, 6)]
            d.line(pts, fill=(255, 255, 240), width=8)
        u = 175 + 30 * p
        cx, cy = W / 2, 1000
        img = arms_up(img, cx, cy, u, (30, 30, 36), (196, 142, 106), t)
        draw_char(img, cx, cy, u, "rafa", "grito", 1, (0, -1), 1.0, t)
        img = rain(img, t, 1.3)
        return zoomed(img, 1 + 0.25 * ease(p), W / 2, 800)
    if name == "familia_altar":
        img = bg("terciopelo").resize((W, H), Image.BILINEAR, box=(110, 195, 1190, 2115))
        img = rays(img, W / 2, 720, t, GOLD, 0.9)
        d = ImageDraw.Draw(img)
        d.rectangle([430, 1230, 650, 1900], fill=(170, 120, 45)); d.rectangle([470, 1230, 500, 1900], fill=(215, 170, 80))
        d.rectangle([390, 1200, 690, 1240], fill=(230, 190, 90)); d.rectangle([380, 1880, 700, 1920], fill=(230, 190, 90))
        img, q = draw_card(img, W / 2, 960 + 18 * math.sin(t * 2), 0.42, 0.1, 0.35 * math.sin(t * 1.4), 0, sheen=(t * 0.5) % 1.4 - 0.2, glow=1.6, shadow=False)
        z = 1 + 0.08 * p
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_char(lay, 160, 1180, 125, "carmen", "devocion", 0, (0.9, -0.7), 0, t)
        draw_char(lay, W - 160, 1180, 125, "nacho", "devocion", 0, (-0.9, -0.7), 0, t)
        draw_char(lay, 200, 1560, 160, "rafa", "devocion", 0, (0.9, -1), 0.7, t)
        draw_char(lay, W - 200, 1560, 160, "sofia", "devocion", 0, (-0.9, -1), 0, t)
        img = over(img, lay)
        img = petals(img, t, 60)
        return zoomed(img, z, W / 2, 1000)
    if name == "familia_caras":
        img = bg("terciopelo").resize((W, H), Image.BILINEAR, box=(110, 195, 1190, 2115))
        img = rays(img, W / 2, 400, t, GOLD, 0.7)
        k = min(2, int(p * 3)); sub = (p * 3) % 1
        who = ["carmen", "nacho", "sofia"][k]
        u = 360 + 40 * sub
        draw_char(img, W / 2 + [-60, 60, -40][k], 1050, u, who, "devocion", 0, ([0.7, -0.7, 0.7][k], -0.8), 0.8 if who == "carmen" else 0, t)
        img, q = draw_card(img, [850, 230, 850][k], 760, 0.32, 0.1, 0.3 * math.sin(t), 0, sheen=sub * 1.4 - 0.2, glow=1.6, shadow=False)
        img = petals(img, t, 40)
        if sub < 0.1: img = to_img(arr(img) + (1 - sub / 0.1) * 90)
        return img
    if name == "tarjeta_final":
        img = C.studio_bg(t, (40, 14, 10))
        img = C.particles(img, t, 120, GOLD, 20, 3)
        img, q = draw_card(img, W / 2, 1000, 0.95, 0.15, -0.5 + 0.9 * ease(p), -0.03, sheen=-0.3 + 1.6 * p, glow=1.4, reflect=True)
        return img
    if name == "rafa_camara":
        img = cam(bg("barberia"), p, 1.3, 1.4).filter(ImageFilter.GaussianBlur(10))
        u = 300 + 50 * ease(p)
        draw_char(img, W / 2, 860, u, "rafa", "camara", mouth("rafa", t), (0, 0), 0.3 + 0.7 * ease(p), t)
        return img
    if name == "continuara":
        img = bg("terciopelo").resize((W, H), Image.BILINEAR, box=(110, 195, 1190, 2115))
        img = to_img(arr(img) * 0.5)
        img = rays(img, W / 2, 720, t, GOLD, 0.6)
        img = petals(img, t, 35)
        img, q = draw_card(img, W / 2, 720, 0.72, 0.1, 0.25 * math.sin(t * 1.3), 0, sheen=(p * 1.6) - 0.3, glow=1.3, shadow=False)
        d = ImageDraw.Draw(img)
        sp = clamp01((p - 0.35) / 0.3)
        if sp > 0:
            d.text((W / 2, 200), "Continuará…", font=font(F_SERIF, int(70 + 10 * (1 - sp))), fill=CREAM, anchor="mm", stroke_width=3, stroke_fill=(60, 10, 10))
        return img
    raise KeyError(name)

FLASH = [2.25, 9.0, 14.0, 20.0, 26.0, 33.0, 38.4]
import json
TIMING = json.load(open(os.path.join(HERE, "tmp", "voice_timing.json"))) if os.path.exists(os.path.join(HERE, "tmp", "voice_timing.json")) else []

def frame(t, fi):
    idx = [i for i, s in enumerate(SHOTS) if s[0] <= t < s[1]]
    i = idx[0] if idx else len(SHOTS) - 1
    a, b, name = SHOTS[i]
    img = shot_frame(name, t, a, b)
    # fundido cruzado lento (cámara lenta) en algunos cortes
    if i + 1 < len(SHOTS) and t > b - 0.25 and SHOTS[i + 1][2] in ("rafa_lagrima", "familia_altar", "tarjeta_final", "rafa_camara", "faro_puerto"):
        a2, b2, n2 = SHOTS[i + 1]
        img = Image.blend(img, shot_frame(n2, t, a2, b2), (t - (b - 0.25)) / 0.25)
    x = soap_grade(img, 1.0, 0.4) * VIG
    for h in FLASH:
        u = t - h
        if 0 <= u < 0.18: x = x + (1 - u / 0.18) * 120
    x += np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    if t < 0.4: x *= t / 0.4
    img = to_img(x)
    for lay in (logo_bug(t), lower_third(t), title_layer(t), subtitle_layer(t, TIMING)):
        if lay is not None: img = over(img, lay)
    if t > TOTAL - 0.3: img = to_img(arr(img) * max(0, (TOTAL - t) / 0.3))
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
