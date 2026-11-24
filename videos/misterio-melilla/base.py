# Render del anuncio "MELILLA 2050" (1080x1920, 30 fps).
# Fotos reales de Melilla (Wikimedia Commons, ver FUENTES.md) + tarjeta NFC 3D + HUD + efectos, todo con PIL/numpy.
import sys, math, os, subprocess, json, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import SCENES, SHOTS, TITLES, HITS, TOTAL

W, H, FPS = 1080, 1920, 30
BW, BH = 1260, 2240                  # fondos más grandes que el cuadro para mover la cámara
IMG = os.path.join(HERE, "img")
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FXB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
FBI = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
FM = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
_fc = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]
CYAN = (40, 235, 255); MAG = (255, 50, 190); GOLD = (255, 205, 70); RED = (255, 40, 60); WHITE = (255, 255, 255)

def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def ease(p): p = min(max(p, 0.0), 1.0); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0.0), 1.0); return 1 - (1 - p) ** 3
def back(p, s=1.7):
    p = min(max(p, 0.0), 1.0); p -= 1; return p * p * ((s + 1) * p + s) + 1
def hrand(*a):                      # ruido determinista
    x = math.sin(sum(v * k for v, k in zip(a, (12.9898, 78.233, 37.719, 11.13)))) * 43758.5453
    return x - math.floor(x)

# ------------------------------------------------------------------ fotos
def slug(title): return re.sub(r"[^a-z0-9]+", "_", ("File:" + title)[5:].lower())[:50].strip("_")
PHOTO = {   # plano -> archivo de Commons
    "aerial": "Aterrizando en Melilla (16668390111).jpg",
    "night_city": "MelillaNoche.jpg",
    "shop_pergola": "Restaurante La Pergóla, Puerto Pesquero y Torres V Centenario.jpg",
    "shop_mercado": "Mercado Central2.jpg",
    "shop_barber1": "175 The Barber Shop, costa de la Pols 5 (Palma).jpg",
    "shop_avenida": "La Avenida, Melilla, 7.jpg",
    "plaza": "Melilla - Plaza de España - Centro.jpg",
    "tap_bg": "Melilla noche (2).jpg",
    "m_playa": "Playa de los Cárabos (9436872331).jpg",
    "m_marina": "Puerta de la Marina, Melilla.jpg",
    "m_tortosa": "Casa Tortosa Melilla.jpg",
    "m_barber2": "Barber shop Porto.jpg",
    "m_restaurante": "La Avenida, 21 y Hotel-Restaurante Marina.jpg",
    "m_tienda": "La Avenida, 25, Melilla.jpg",
    "news_screen": "Palacio de la Asamblea de Melilla (de noche).jpg",
    "o_vieja": "Frente de la Marina, Melilla la Vieja.jpg",
    "o_asamblea": "Palacio de la Asamblea de Melilla, Amaneciendo en Melilla.jpg",
    "o_faro": "Faro de Melilla de Noche.jpg",
    "o_parque": "Parque Hernández, Melilla (3).jpg",
    "o_casino": "CASINO MILITAR (MELILLA).jpg",
    "o_cala": "Melilla La Vieja y Puerto de Melilla.jpg",
    "finale_bg": "MelillaLuces.jpg",
}
FOCUS = {  # punto de interés horizontal (0..1) para el recorte vertical
    "aerial": 0.5, "plaza": 0.5, "m_marina": 0.5, "m_tortosa": 0.45, "o_asamblea": 0.42, "o_vieja": 0.55, "o_cala": 0.22, "o_faro": 0.5,
}
EXTRA = {"o_vieja": (1.5, 0.85), "o_cala": (1.7, 0.85), "o_asamblea": (1.3, 0.75)}   # zoom extra, foco vertical
_ph = {}
def grade(im, kind):
    a = np.asarray(im, float)
    if kind == "future":          # sombras cian, altas luces cálidas, más contraste
        lum = a.mean(2, keepdims=True) / 255
        a = (a - 128) * 1.18 + 128
        a = a * (1 - 0.22 * (1 - lum)) + (1 - lum) * np.array([0, 40, 60]) * 0.9 + lum * np.array([25, 8, -10])
    elif kind == "night":
        a = (a - 128) * 1.1 + 118; a = a * np.array([0.72, 0.9, 1.15])
    elif kind == "warm":          # cine dorado
        lum = a.mean(2, keepdims=True) / 255
        a = (a - 128) * 1.12 + 128
        a = a + lum * np.array([28, 12, -18]) + (1 - lum) * np.array([-6, 10, 22])
    elif kind == "chaos":
        a = (a - 128) * 1.25 + 128; g = a.mean(2, keepdims=True); a = g + (a - g) * 1.35
    return to_img(a)
def photo(name, kind="future", size=(BW, BH)):
    k = (name, kind, size)
    if k not in _ph:
        fp = os.path.join(IMG, slug(PHOTO[name]) + ".jpg")
        if not os.path.exists(fp):
            print("FALTA", PHOTO[name], file=sys.stderr); im = Image.new("RGB", (1600, 1000), (90, 90, 110))
        else: im = Image.open(fp).convert("RGB")
        fx = FOCUS.get(name, 0.5)
        sw, sh = im.size; tw, th = size
        sc = max(tw / sw, th / sh) * EXTRA.get(name, (1, 0.5))[0]; im = im.resize((max(tw, int(sw * sc + 0.5)), max(th, int(sh * sc + 0.5))), Image.LANCZOS)
        x0 = int((im.size[0] - tw) * fx); y0 = int((im.size[1] - th) * EXTRA.get(name, (1, 0.5))[1])
        _ph[k] = grade(im.crop((x0, y0, x0 + tw, y0 + th)), kind)
    return _ph[k]

def cam(bg, p, z0, z1, dx=0.0, dy=0.0, rot=0.0):
    p = min(max(p, 0.0), 1.0)
    z = z0 + (z1 - z0) * p
    bw, bh = bg.size; cw, ch = bw / z * (W / BW), bh / z * (H / BH)
    cx = bw / 2 + dx * (p - 0.5) * (bw - cw); cy = bh / 2 + dy * (p - 0.5) * (bh - ch)
    out = bg.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    if rot: out = out.rotate(rot, Image.BILINEAR)
    return out

# ------------------------------------------------------------------ dibujo
def text_w(d, s, f, sp=0):
    return d.textlength(s, font=f) + sp * max(0, len(s) - 1)
def draw_text(d, xy, s, f, fill, sp=0, stroke=0, sf=(0, 0, 0)):
    x, y = xy
    if sp == 0:
        d.text((x, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sf); return
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=sf); x += d.textlength(ch, font=f) + sp
def ctext(d, y, s, f, fill, sp=0, stroke=0, sf=(0, 0, 0), cx=W / 2):
    draw_text(d, (cx - text_w(d, s, f, sp) / 2, y), s, f, fill, sp, stroke, sf)
def fit_font(d, s, path, size, maxw, sp=0):
    while size > 20 and text_w(d, s, font(path, size), sp) > maxw: size -= 4
    return font(path, size)
def star(d, cx, cy, r, fill, outline=None, width=0):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline, width=width)
def nfc_icon(d, cx, cy, s, col, w=None):
    w = w or max(3, int(s * 0.09))
    for k in range(3):
        r = s * (0.32 + 0.26 * k)
        d.arc([cx - r, cy - r, cx + r, cy + r], -45, 45, fill=col, width=w)
    d.ellipse([cx - s * 0.1, cy - s * 0.1, cx + s * 0.1, cy + s * 0.1], fill=col)
def glow_paste(base, lay, r=18, k=1.0):
    g = lay.filter(ImageFilter.GaussianBlur(r))
    if k != 1.0:
        a = np.asarray(g, float); a[..., 3] *= k; g = to_img(a).convert("RGBA") if False else Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    base.alpha_composite(g); base.alpha_composite(lay)
def rgba(size=(W, H)): return Image.new("RGBA", size, (0, 0, 0, 0))

# ------------------------------------------------------------------ tarjeta NFC
CW, CH = 1000, 1000                   # placa NFC cuadrada (producto real)
PRODUCT = os.path.join(HERE, "producto", "placa_nfc_original.jpg")
PLATE_CORNERS = [(68, 297), (758, 275), (757, 1013), (70, 1062)]   # esquinas de la placa frontal en la foto
def _coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()
def card_textures():
    """Cara frontal = foto real de la placa (enderezada). Trasera = adhesivo 3M de doble cara."""
    im = Image.open(PRODUCT).convert("RGB")
    front = im.transform((CW, CH), Image.PERSPECTIVE, _coeffs([(0, 0), (CW, 0), (CW, CH), (0, CH)], PLATE_CORNERS), Image.BICUBIC)
    front = ImageEnhance.Contrast(front).enhance(1.05).convert("RGBA")
    mask = Image.new("L", (CW, CH), 0); ImageDraw.Draw(mask).rounded_rectangle([3, 3, CW - 4, CH - 4], 46, fill=255)
    d = ImageDraw.Draw(front)                                   # canto de metacrilato
    d.rounded_rectangle([3, 3, CW - 4, CH - 4], 46, outline=(235, 245, 255, 255), width=5)
    front.putalpha(mask)
    backi = Image.new("RGBA", (CW, CH), (238, 240, 244, 255)); d = ImageDraw.Draw(backi)
    blue = (25, 80, 200, 255)
    for r in range(7):
        for c in range(3):
            x = 40 + c * 330 + (110 if r % 2 else 0); y = 40 + r * 140
            lab = rgba((300, 90)); dl = ImageDraw.Draw(lab)
            dl.text((0, 0), "3M", font=font(FB, 64), fill=blue); dl.text((105, 4), "9448A", font=font(FXB, 30), fill=blue)
            dl.text((105, 42), "Double Coated Tissue Tape", font=font(FXB, 16), fill=blue)
            if r % 2: lab = lab.rotate(180)
            backi.alpha_composite(lab, (int(x), int(y)))
    d.rounded_rectangle([3, 3, CW - 4, CH - 4], 46, outline=(225, 235, 250, 255), width=5)
    backi.putalpha(mask)
    return front, backi
CARD_F, CARD_B = card_textures()

PRODUCT_CUT = Image.open(os.path.join(HERE, "producto", "placas_recorte.png")).convert("RGBA")   # la imagen del cliente, sin fondo
def product_shot(img, cx, cy, width, t, glow=1.2, shine=None, ang=0.0):
    """Pega la foto original del producto (las dos placas) con brillo y halo."""
    w = int(width); h = int(PRODUCT_CUT.size[1] * w / PRODUCT_CUT.size[0])
    p = PRODUCT_CUT.resize((w, h), Image.LANCZOS)
    if shine is not None:
        sh = rgba((w, h)); ds = ImageDraw.Draw(sh); x = -w * 0.4 + shine * w * 1.8
        ds.polygon([(x, 0), (x + w * 0.12, 0), (x - w * 0.2, h), (x - w * 0.32, h)], fill=(255, 255, 255, 80))
        sh = sh.filter(ImageFilter.GaussianBlur(w * 0.02)); m = p.getchannel("A"); p.alpha_composite(sh); p.putalpha(m)
    if ang: p = p.rotate(ang, Image.BICUBIC, expand=True)
    g = Image.new("RGBA", p.size, CYAN + (0,)); g.putalpha(p.getchannel("A").filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(min(255, v * 0.8 * glow))))
    pos = (int(cx - p.size[0] / 2), int(cy - p.size[1] / 2))
    img.alpha_composite(g, pos); img.alpha_composite(p, pos)

def persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def card_layer(cx, cy, width, yaw=0.0, pitch=0.0, roll=0.0, shine=None, glow=1.0, size=(W, H), alpha=1.0):
    """Tarjeta en 3D: ángulos en grados, width = ancho en píxeles con rotación 0."""
    f = 1700.0; s = width / CW
    yw, pt, rl = math.radians(yaw), math.radians(pitch), math.radians(roll)
    pts3 = [(-CW / 2, -CH / 2), (CW / 2, -CH / 2), (CW / 2, CH / 2), (-CW / 2, CH / 2)]
    out = []
    for (x, y) in pts3:
        x, y, z = x * s, y * s, 0.0
        x, y = x * math.cos(rl) - y * math.sin(rl), x * math.sin(rl) + y * math.cos(rl)
        x, z = x * math.cos(yw) + z * math.sin(yw), -x * math.sin(yw) + z * math.cos(yw)
        y, z = y * math.cos(pt) - z * math.sin(pt), y * math.sin(pt) + z * math.cos(pt)
        z += f
        out.append((cx + f * x / z, cy + f * y / z))
    (x0, y0), (x1, y1), (x2, y2) = out[0], out[1], out[2]
    facing = ((x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)) > 0
    tex = CARD_F if facing else CARD_B.transpose(Image.FLIP_LEFT_RIGHT)
    if shine is not None:      # barrido de brillo
        tex = tex.copy(); sh = rgba((CW, CH)); ds = ImageDraw.Draw(sh)
        x = -500 + shine * (CW + 1000)
        ds.polygon([(x, 0), (x + 220, 0), (x - 260, CH), (x - 480, CH)], fill=(255, 255, 255, 90))
        sh = sh.filter(ImageFilter.GaussianBlur(30)); m = tex.getchannel("A")
        tex.alpha_composite(sh); tex.putalpha(m)
    src = [(0, 0), (CW, 0), (CW, CH), (0, CH)]
    lay = tex.transform(size, Image.PERSPECTIVE, persp_coeffs(out, src), Image.BICUBIC)
    if alpha < 1:
        a = lay.getchannel("A").point(lambda v: int(v * alpha)); lay.putalpha(a)
    if glow > 0:
        g = Image.new("RGBA", size, CYAN + (0,)); g.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(min(255, v * 0.9 * glow))))
        return g, lay
    return None, lay

def put_card(img, *a, **k):
    g, lay = card_layer(*a, **k)
    if g is not None: img.alpha_composite(g)
    img.alpha_composite(lay)

# ------------------------------------------------------------------ HUD futurista
def hud(img, t, label="MELILLA · 2050", tint=CYAN, rec=True):
    lay = rgba(); d = ImageDraw.Draw(lay); c = tint + (210,)
    m, L = 60, 90
    for (x, y, sx, sy) in [(m, 230, 1, 1), (W - m, 230, -1, 1), (m, H - 330, 1, -1), (W - m, H - 330, -1, -1)]:
        d.line([x, y, x + sx * L, y], fill=c, width=6); d.line([x, y, x, y + sy * L], fill=c, width=6)
    f = font(FM, 30)
    draw_text(d, (m + 20, 245), label, f, c, sp=3)
    if rec and int(t * 2) % 2 == 0: d.ellipse([W - m - 150, 250, W - m - 128, 272], fill=RED + (255,))
    if rec: draw_text(d, (W - m - 118, 245), "REC", f, c)
    draw_text(d, (m + 20, H - 385), "35°17'N  2°56'W", f, c, sp=2)
    draw_text(d, (W - m - 260, H - 385), f"T+{t:05.2f}", f, c, sp=2)
    # mira central
    cx, cy = W / 2, H / 2 - 60
    for a0 in (0, 90, 180, 270):
        d.arc([cx - 70, cy - 70, cx + 70, cy + 70], a0 + 15 + t * 40, a0 + 70 + t * 40, fill=tint + (140,), width=4)
    d.line([cx - 20, cy, cx + 20, cy], fill=tint + (160,), width=3); d.line([cx, cy - 20, cx, cy + 20], fill=tint + (160,), width=3)
    img.alpha_composite(lay)

def scanlines(img, k=0.10):
    a = np.asarray(img).astype(np.float32)
    a[::4] *= (1 - k); return Image.fromarray(a.astype(np.uint8), img.mode)

def particles(img, t, n=70, col=CYAN, seed=1, up=True, size=6):
    lay = rgba(); d = ImageDraw.Draw(lay)
    for i in range(n):
        x = hrand(i, seed) * W + 30 * math.sin(t * 1.3 + i)
        sp = 80 + hrand(i, seed, 2) * 260
        y = (hrand(i, seed, 3) * H - (t * sp if up else -t * sp)) % H
        s = 1.5 + hrand(i, seed, 4) * size
        d.ellipse([x - s, y - s, x + s, y + s], fill=col + (int(110 + 140 * hrand(i, seed, 5)),))
    glow_paste(img, lay, 8)

# ------------------------------------------------------------------ teléfono
PW, PH = 600, 1220
def phone_screen(state, p, t):
    """state: 'lock' | 'scan' | 'reviews'. Pantalla simulada (no es una captura real)."""
    s = Image.new("RGBA", (PW - 44, PH - 44), (10, 14, 26, 255)); d = ImageDraw.Draw(s); sw, sh = s.size
    draw_text(d, (34, 22), "20:50", font(FXB, 34), WHITE + (255,))
    draw_text(d, (sw - 120, 22), "5G ▮", font(FXB, 30), WHITE + (255,))
    if state in ("lock", "scan"):
        a = np.zeros((sh, sw, 3)); yy = np.linspace(0, 1, sh)[:, None, None]
        a += np.array([10, 20, 50]) * (1 - yy) + np.array([60, 10, 70]) * yy
        s.paste(to_img(a), (0, 80)); d = ImageDraw.Draw(s)
        ctext(d, 200, "20:50", font(FB, 150), WHITE + (255,), cx=sw / 2)
        ctext(d, 380, "MELILLA · 23 NOV 2050", font(FM, 28), (200, 220, 255, 255), cx=sw / 2)
        if state == "scan":
            for k in range(4):
                r = ((p * 3 + k / 4) % 1) * 300
                d.ellipse([sw / 2 - r, sh * 0.62 - r, sw / 2 + r, sh * 0.62 + r], outline=CYAN + (int(255 * (1 - r / 300)),), width=6)
            nfc_icon(d, sw / 2 - 30, sh * 0.62, 150, CYAN + (255,))
            ctext(d, sh * 0.80, "LEYENDO NFC…", font(FM, 36), CYAN + (255,), cx=sw / 2)
        return s
    # --- página de reseñas (maqueta)
    d.rectangle([0, 80, sw, sh], fill=(250, 250, 252, 255))
    d.rounded_rectangle([24, 100, sw - 24, 170], 35, fill=(235, 238, 244, 255))
    draw_text(d, (54, 116), "🔒 g.page/r/tu-negocio/review"[2:], font(FM, 24), (90, 100, 120, 255))
    draw_text(d, (40, 210), "Google", font(FXB, 46), (70, 80, 100, 255))
    draw_text(d, (40, 275), "TU NEGOCIO", font(FB, 62), (20, 24, 34, 255))
    draw_text(d, (40, 352), "Melilla", font(FXB, 34), (110, 118, 135, 255))
    d.line([40, 420, sw - 40, 420], fill=(220, 224, 232, 255), width=3)
    draw_text(d, (40, 455), "Valora tu experiencia", font(FXB, 40), (30, 34, 44, 255))
    nf = int(min(5, max(0, (p - 0.25) / 0.09)))
    for k in range(5):
        cx = 75 + k * 102; on = k < nf
        star(d, cx, 580, 44, GOLD + (255,) if on else (255, 255, 255, 255), outline=(150, 156, 170, 255) if not on else None, width=4)
    d.rounded_rectangle([40, 670, sw - 40, 920], 22, outline=(200, 205, 215, 255), width=3)
    typed = "¡Genial! Súper fácil."[: max(0, int((p - 0.72) * 70))]
    draw_text(d, (64, 700), typed if typed else "Escribe una reseña…", font(FXB, 34), (30, 34, 44, 255) if typed else (150, 156, 170, 255))
    d.rounded_rectangle([sw - 260, 960, sw - 40, 1040], 40, fill=(40, 110, 240, 255))
    ctext(d, 978, "Publicar", font(FXB, 36), WHITE + (255,), cx=sw - 150)
    return s

def phone(state, p, t):
    ph = rgba((PW, PH)); d = ImageDraw.Draw(ph)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], 80, fill=(20, 22, 28, 255), outline=(120, 130, 150, 255), width=5)
    scr = phone_screen(state, p, t)
    m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.size[0] - 1, scr.size[1] - 1], 60, fill=255)
    ph.paste(scr, (22, 22), m)
    d.rounded_rectangle([PW / 2 - 70, 40, PW / 2 + 70, 76], 18, fill=(0, 0, 0, 255))
    return ph

def hand_with_phone(state, p, t, ang=0.0, scale=1.0):
    """Mano estilizada (CGI) que sujeta el móvil."""
    lay = rgba((PW + 360, PH + 520)); d = ImageDraw.Draw(lay)
    ox, oy = 180, 120
    skin, skin2 = (205, 150, 115, 255), (170, 115, 85, 255)
    # palma y muñeca (detrás del móvil)
    d.rounded_rectangle([ox + 60, oy + PH - 420, ox + PW + 40, oy + PH + 180], 160, fill=skin2)
    d.rounded_rectangle([ox + 140, oy + PH + 60, ox + PW - 20, oy + PH + 520], 120, fill=(40, 50, 80, 255))   # manga
    lay.alpha_composite(phone(state, p, t), (ox, oy))
    # dedos por la izquierda y pulgar por la derecha
    for k in range(4):
        y = oy + PH - 560 + k * 120
        d.rounded_rectangle([ox - 70, y, ox + 40, y + 100], 50, fill=skin if k % 2 == 0 else (198, 142, 108, 255))
        d.arc([ox + 5, y + 20, ox + 45, y + 80], 270, 90, fill=skin2, width=5)
    d.rounded_rectangle([ox + PW - 50, oy + PH - 520, ox + PW + 70, oy + PH - 160], 60, fill=skin)
    d.ellipse([ox + PW - 30, oy + PH - 510, ox + PW + 40, oy + PH - 440], fill=(230, 190, 170, 255))
    if scale != 1.0: lay = lay.resize((int(lay.size[0] * scale), int(lay.size[1] * scale)), Image.LANCZOS)
    if ang: lay = lay.rotate(ang, Image.BICUBIC, expand=True)
    return lay

# ------------------------------------------------------------------ títulos
def siren_icon(d, cx, cy, s, t):
    on = int(t * 6) % 2 == 0
    d.pieslice([cx - s, cy - s, cx + s, cy + s], 180, 360, fill=(RED if on else (150, 20, 30)) + (255,))
    d.rectangle([cx - s * 1.2, cy, cx + s * 1.2, cy + s * 0.35], fill=(230, 230, 235, 255))
    if on:
        for a in (-150, -120, -90, -60, -30):
            r1, r2 = s * 1.3, s * 1.8; ar = math.radians(a)
            d.line([cx + r1 * math.cos(ar), cy + r1 * math.sin(ar), cx + r2 * math.cos(ar), cy + r2 * math.sin(ar)], fill=(255, 220, 80, 255), width=8)

def title_layer(t):
    lay = rgba(); d = ImageDraw.Draw(lay); any_ = False
    for (a, b, lines, style) in TITLES:
        if not (a <= t < b): continue
        any_ = True; age = t - a; left = b - t
        if style == "alert":
            pin = eout(age / 0.18)
            bar_w = W * pin
            d.rectangle([W / 2 - bar_w / 2, 380, W / 2 + bar_w / 2, 520], fill=RED + (235,))
            if pin > 0.6:
                siren_icon(d, 80, 470, 40, t); siren_icon(d, W - 80, 470, 40, t)
                ctext(d, 398, lines[0], font(FB, 92), WHITE + (255,), sp=4)
            for i, s in enumerate(lines[1:]):
                p = eout((age - 0.35 - i * 0.18) / 0.25)
                if p <= 0: continue
                f = fit_font(d, s, FB, 118, W - 90)
                jx = (hrand(int(t * 30), i) - 0.5) * 18 if age < 0.8 else 0
                y = 590 + i * 150 + (1 - p) * 60
                ctext(d, y, s, f, CYAN + (int(255 * p),), stroke=8, sf=(0, 0, 0, int(255 * p)), cx=W / 2 + jx)
        elif style == "chaos":
            for i, s in enumerate(lines):
                p = back((age - i * 0.22) / 0.3)
                if age - i * 0.22 < 0: continue
                f = fit_font(d, s, FB, 150 if i == 1 else 112, W - 80)
                sub = rgba((W, 220)); ds = ImageDraw.Draw(sub)
                ctext(ds, 20, s, f, (GOLD if i == 1 else WHITE) + (255,), stroke=10, sf=(0, 0, 0, 255))
                ang = (-6, 5, -3)[i] + 2.5 * math.sin(t * 9 + i)
                sc = max(0.05, p)
                sub = sub.resize((max(1, int(W * sc)), max(1, int(220 * sc)))).rotate(ang, Image.BICUBIC, expand=True)
                lay.alpha_composite(sub, (int(W / 2 - sub.size[0] / 2), int(430 + i * 175 + 110 - sub.size[1] / 2)))
        elif style == "hero":
            p = eout(age / 0.45); fo = min(1, left / 0.2)
            n = len(lines); y0 = (1340 if n == 2 else 1380) if a < 10 else 330
            for i, s in enumerate(lines):
                sp = int(40 * (1 - p)) + 2
                f = fit_font(d, s, FB, 128 if n == 1 else 112, W - 100, sp)
                lt = rgba(); dl = ImageDraw.Draw(lt)
                ctext(dl, y0 + i * 135, s, f, WHITE + (int(255 * p * fo),), sp=sp)
                g = rgba(); dg = ImageDraw.Draw(g); ctext(dg, y0 + i * 135, s, f, CYAN + (int(255 * p * fo),), sp=sp)
                lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(16))); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(5))); lay.alpha_composite(lt)
        elif style == "punch":
            p = age / 0.16; sc = 1.0 + max(0, 1 - p) * 0.3
            col = [GOLD, CYAN, MAG][TITLES.index((a, b, lines, style)) % 3]
            sub = rgba((W, 520)); ds = ImageDraw.Draw(sub)
            for i, s in enumerate(lines):
                f = fit_font(ds, s, FBI, 190, (W - 70) / 1.3)
                ctext(ds, 40 + i * 210 + (105 if len(lines) == 1 else 0), s, f, (WHITE if i == 0 and len(lines) > 1 else col) + (255,), stroke=10, sf=(0, 0, 0, 255))
            if sc != 1: sub = sub.resize((int(W * sc), int(520 * sc)))
            lay.alpha_composite(sub, (int(W / 2 - sub.size[0] / 2), int(700 - sub.size[1] / 2 + 160)))
        elif style == "cine":
            p = ease(age / 0.5); fo = min(1, left / 0.25)
            for i, s in enumerate(lines):
                q = ease((age - i * 0.15) / 0.5)
                sp = int(14 + 20 * (1 - q))
                f = fit_font(d, s, FB if i == len(lines) - 1 else FXB, 104 if i == len(lines) - 1 else 76, W - 100, sp)
                col = GOLD if (i == len(lines) - 1) else WHITE
                ctext(d, 1180 + i * 125 + (1 - q) * 30, s, f, col + (int(255 * q * fo),), sp=sp, stroke=4, sf=(0, 0, 0, int(160 * q * fo)))
    return lay if any_ else None

# ------------------------------------------------------------------ planos
def popup(d, x, y, w, h, title, msg, col=(235, 235, 240)):
    d.rounded_rectangle([x + 10, y + 12, x + w + 10, y + h + 12], 18, fill=(0, 0, 0, 120))
    d.rounded_rectangle([x, y, x + w, y + h], 18, fill=col + (250,), outline=(40, 40, 40, 255), width=3)
    d.rounded_rectangle([x, y, x + w, y + 64], 18, fill=(200, 30, 50, 255)); d.rectangle([x, y + 40, x + w, y + 64], fill=(200, 30, 50, 255))
    draw_text(d, (x + 24, y + 12), title, font(FXB, 34), WHITE + (255,))
    d.text((x + w - 50, y + 8), "✕"[0] if False else "x", font=font(FB, 40), fill=WHITE + (255,))
    for i, line in enumerate(msg.split("\n")):
        draw_text(d, (x + 26, y + 88 + i * 50), line, font(FXB, 36), (20, 20, 30, 255))

SEARCHES = ["reseñas cafetería melilla", "la barbería esa de al lado de…", "¿cómo se dejaba una reseña?", "perfil de google del restaurante???"]

def shot(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    if name == "aerial":
        img = cam(photo("aerial", "night"), p, 1.0, 1.45, 0.2, 0.1).convert("RGBA")
        red = Image.new("RGBA", (W, H), RED + (int(70 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.6))),)); img.alpha_composite(red)
        hud(img, t, "ALERTA · SECTOR MELILLA"); return img
    if name == "night_city":
        img = cam(photo("night_city", "future"), p, 1.25, 1.05, -0.5, 0).convert("RGBA")
        particles(img, t, 50, CYAN, 4); hud(img, t, "MELILLA · AÑO 2050")
        red = Image.new("RGBA", (W, H), RED + (int(55 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.6))),)); img.alpha_composite(red)
        return img
    if name.startswith("shop_"):
        k = ["shop_pergola", "shop_mercado", "shop_barber1", "shop_avenida"].index(name)
        img = cam(photo(name, "chaos"), p, 1.05 + 0.1 * (k % 2), 1.35, (-1) ** k * 0.6, 0.2, rot=(-1) ** k * 2.5 * p).convert("RGBA")
        lay = rgba(); d = ImageDraw.Draw(lay)
        # barra de búsqueda con escritura torpe
        q = SEARCHES[k]; n = int(len(q) * min(1, p * 1.6))
        d.rounded_rectangle([70, 1380, W - 70, 1500], 60, fill=(255, 255, 255, 240), outline=(0, 0, 0, 255), width=4)
        draw_text(d, (130, 1408), q[:n] + ("|" if int(t * 8) % 2 else ""), font(FXB, 44), (40, 40, 50, 255))
        # interrogaciones flotando
        for i in range(7):
            x = hrand(i, k) * W; y = 300 + hrand(i, k, 1) * 900 - p * 120
            s = 60 + hrand(i, k, 2) * 90
            d.text((x, y), "?", font=font(FB, int(s)), fill=(255, 230, 60, 230), stroke_width=6, stroke_fill=(0, 0, 0, 255))
        if k == 3: popup(d, 150, 1560, 780, 180, "Cliente.exe", "No encuentro vuestro perfil… :(")
        img.alpha_composite(lay); return img
    if name == "error_screen":
        img = cam(photo("shop_avenida", "chaos"), 1.0, 1.35, 1.6, 0.6, 0.2).filter(ImageFilter.GaussianBlur(10)).convert("RGBA")
        lay = rgba(); d = ImageDraw.Draw(lay)
        msgs = [("ERROR 404", "Perfil no encontrado"), ("Cliente.exe", "ha dejado de\nresponder"), ("AVISO", "Demasiadas\npestañas abiertas"),
                ("ERROR", "Reseña perdida\nen el espacio"), ("¿¿??", "¿Era con tilde\no sin tilde?")]
        for i, (ti, ms) in enumerate(msgs):
            if p * 6 > i:
                popup(d, 60 + (i * 97) % 360, 1060 + i * 140, 640, 230, ti, ms)
        img.alpha_composite(lay); return img
    if name == "plaza_card":
        bg = photo("plaza", "night")
        img = cam(bg, p, 1.0, 1.18, 0, -0.3).convert("RGBA")
        lay = rgba(); d = ImageDraw.Draw(lay)
        # haz de luz desde el cielo
        beam = max(0.0, min(1.0, (t - 6.3) / 0.6))
        if beam > 0:
            d.polygon([(W / 2 - 60, 0), (W / 2 + 60, 0), (W / 2 + 330, 1500), (W / 2 - 330, 1500)], fill=CYAN + (int(90 * beam),))
            lay = lay.filter(ImageFilter.GaussianBlur(35)); img.alpha_composite(lay)
        # ondas en el suelo al aterrizar
        lay = rgba(); d = ImageDraw.Draw(lay)
        if t > 8.15:
            for k in range(3):
                r = ((t - 8.15) * 900 + k * 260) % 1400
                d.ellipse([W / 2 - r, 1460 - r * 0.22, W / 2 + r, 1460 + r * 0.22], outline=CYAN + (int(220 * (1 - r / 1400)),), width=8)
        glow_paste(img, lay, 10)
        particles(img, t, 80, CYAN, 7, True, 5)
        # la tarjeta desciende girando y queda flotando
        q = eout((t - 6.4) / 1.75)
        cy = -400 + (820 + 1300 * 0) * q + 400 * q + 20 * math.sin(t * 2.2)
        cy = -500 + 1300 * q + 18 * math.sin(t * 2.2)
        yaw = (1 - q) * 720 + 18 * math.sin(t * 1.3)
        put_card(img, W / 2, cy, 700, yaw=yaw, pitch=12 + 6 * math.sin(t * 1.7), roll=-4, shine=((t - 8.1) / 1.2) if t > 8.1 else None, glow=1.4)
        hud(img, t, "OBJETO DETECTADO · PLAZA DE ESPAÑA", rec=False); return img
    if name == "tap":
        bg = photo("tap_bg", "night").filter(ImageFilter.GaussianBlur(14))
        img = cam(bg, p, 1.1, 1.25).convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 90)))
        # rejilla holográfica de suelo
        lay = rgba(); d = ImageDraw.Draw(lay)
        for k in range(16):
            x = W / 2 + (k - 7.5) * 140
            d.line([W / 2 + (x - W / 2) * 0.15, 1150, x * 2.6 - W * 0.8, H], fill=CYAN + (70,), width=3)
        for k in range(9):
            y = 1150 + (H - 1150) * ((k + (t * 1.5) % 1) / 9) ** 1.8
            d.line([0, y, W, y], fill=CYAN + (60,), width=3)
        img.alpha_composite(lay)
        # tarjeta tumbada sobre el mostrador
        put_card(img, W / 2, 1500, 760, yaw=0, pitch=60, roll=0, shine=((t - 10) / 1.2) % 1.6, glow=1.0 + (1.5 if 11.2 < t < 11.6 else 0))
        # el móvil baja hasta tocarla (11,2 s) y luego sube mostrando las reseñas
        tap = 11.2
        if t < tap: q = eout((t - 10.0) / 1.2); y = 2100 + (1020 - 2100) * q; state = "scan"; sp = (t - 10) / 1.2
        else: q = ease((t - tap - 0.35) / 0.6); y = 1020 - 290 * q; state = "reviews" if t > tap + 0.25 else "scan"; sp = (t - tap - 0.25) / 2.3
        hp = hand_with_phone(state, sp, t, ang=-8 + 8 * (q if t >= tap else 0), scale=0.78)
        img.alpha_composite(hp, (int(W / 2 - hp.size[0] / 2 + 30), int(y - 200)))
        if tap - 0.05 <= t < tap + 0.9:        # anillos del escáner
            lay = rgba(); d = ImageDraw.Draw(lay)
            for k in range(4):
                r = (t - tap) * 1400 - k * 140
                if r > 0: d.ellipse([W / 2 - r, 1500 - r * 0.45, W / 2 + r, 1500 + r * 0.45], outline=CYAN + (int(max(0, 255 - r / 4)),), width=10)
            glow_paste(img, lay, 12)
        if t > tap + 0.3:
            lay = rgba(); d = ImageDraw.Draw(lay)
            pp = min(1, (t - tap - 0.3) / 0.25)
            d.rounded_rectangle([210, 1640, W - 210, 1750], 55, fill=(10, 30, 40, int(220 * pp)), outline=CYAN + (int(255 * pp),), width=4)
            ctext(d, 1665, "ENLACE ABIERTO", font(FM, 50), CYAN + (int(255 * pp),))
            glow_paste(img, lay, 10)
        return img
    if name.startswith("m_") and name != "m_card":
        k = ["m_playa", "m_marina", "m_tortosa", "m_barber2", "m_restaurante", "m_tienda"].index(name)
        z = 1.5 - 0.4 * eout(p / 0.35) + 0.08 * p
        img = cam(photo(name, "future"), p, z, z + 0.06, (-1) ** k * 0.8, 0.3 * (-1) ** (k // 2), rot=(-1) ** k * 3 * (1 - eout(p / 0.3))).convert("RGBA")
        # sello holográfico de "tarjeta NFC aquí" en cada sitio
        put_card(img, W / 2 + (-1) ** k * 230, 1560, 360, yaw=(-1) ** k * 25 + 20 * math.sin(t * 3), pitch=10, roll=(-1) ** k * 6,
                 shine=(p * 1.4), glow=1.3)
        return img
    if name == "m_card":
        img = Image.new("RGBA", (W, H), (4, 8, 20, 255)); particles(img, t, 90, MAG, 11, True, 7)
        product_shot(img, W / 2, H / 2 + 330, 820 + 120 * p, t, glow=1.6, shine=p * 1.2, ang=4 - 6 * p)
        return img
    if name == "news":
        return news(t, p)
    if name == "card_glitch":
        img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        put_card(img, W / 2, H / 2, 900 + 150 * p, yaw=10 * math.sin(t * 40), pitch=0, roll=0, glow=2.0)
        return glitch(img, t, 1.0)
    if name.startswith("o_"):
        k = ["o_vieja", "o_asamblea", "o_faro", "o_parque", "o_casino", "o_cala"].index(name)
        img = cam(photo(name, "warm"), p, 1.08, 1.22, (-1) ** k * 0.5, 0.15).convert("RGBA")
        pos = [(780, 760, 300), (290, 1640, 320), (790, 1650, 300), (300, 760, 300), (770, 1640, 320), (W / 2, 900, 380)][k]
        put_card(img, pos[0], pos[1] + 15 * math.sin(t * 2), pos[2], yaw=20 * math.sin(t * 1.5 + k), pitch=12, roll=(-1) ** k * 8,
                 shine=p * 1.2, glow=1.2)
        img.alpha_composite(SHADE)
        d = ImageDraw.Draw(img)   # bandas de cine
        d.rectangle([0, 0, W, 150], fill=(0, 0, 0, 255)); d.rectangle([0, H - 150, W, H], fill=(0, 0, 0, 255))
        return img
    if name == "finale":
        return finale(t, p)
    raise KeyError(name)

_sy = np.linspace(0, 1, H)[:, None]
SHADE = Image.fromarray((np.broadcast_to(np.clip(1 - np.abs(_sy - 0.67) / 0.2, 0, 1) * 150, (H, W))).astype(np.uint8), "L")
SHADE = Image.merge("RGBA", (Image.new("L", (W, H), 0),) * 3 + (SHADE,))
TICKER = ("ÚLTIMA HORA  ·  LAS GAVIOTAS DEL PUERTO PIDEN SU PROPIA TARJETA NFC  ·  UN VECINO INTENTA PAGAR EL CAFÉ CON LA TARJETA "
          "DE RESEÑAS (NO FUNCIONA)  ·  LA PRESENTADORA ES UN HOLOGRAMA Y NO TIENE PIERNAS  ·  ")
def news(t, p):
    img = Image.new("RGBA", (W, H), (6, 10, 30, 255)); d = ImageDraw.Draw(img)
    a = np.zeros((H, W, 3)); yy = np.linspace(0, 1, H)[:, None, None]
    a += np.array([4, 14, 50]) * (1 - yy) + np.array([30, 4, 40]) * yy
    img = to_img(a).convert("RGBA")
    # pantalla gigante del plató con Melilla
    scr = photo("news_screen", "future", (980, 720))
    zz = 1 + 0.08 * p
    scr = scr.resize((int(980 * zz), int(720 * zz))).crop((0, 0, 980, 720))
    img.paste(scr, (50, 300)); d = ImageDraw.Draw(img)
    d.rectangle([50, 300, 1030, 1020], outline=CYAN + (255,), width=6)
    d.rectangle([50, 300, 360, 360], fill=RED + (255,)); draw_text(d, (70, 306), "EN DIRECTO", font(FB, 42), WHITE + (255,))
    draw_text(d, (720, 970), "MELILLA", font(FB, 40), WHITE + (255,), sp=4)
    # presentadora holográfica
    hol = rgba(); dh = ImageDraw.Draw(hol)
    flick = 0.85 + 0.15 * math.sin(t * 37) * math.sin(t * 13)
    col = (120, 230, 255, int(170 * flick))
    cx = W / 2 + (8 * math.sin(t * 50) if hrand(int(t * 10)) > 0.85 else 0)
    dh.ellipse([cx - 120, 760, cx + 120, 1050], fill=col)                         # cabeza
    dh.polygon([(cx - 55, 1040), (cx + 55, 1040), (cx + 70, 1120), (cx - 70, 1120)], fill=col)  # cuello
    dh.rounded_rectangle([cx - 330, 1100, cx + 330, 1600], 160, fill=col)           # hombros
    dh.polygon([(cx - 70, 1110), (cx + 70, 1110), (cx, 1300)], fill=(30, 80, 120, 200))   # solapas
    dh.ellipse([cx - 135, 730, cx + 135, 900], fill=(90, 200, 240, int(190 * flick)))      # pelo
    # boca que "habla"
    talk = 19.35 < t < 24.4 and int(t * 12) % 2 == 0
    dh.ellipse([cx - 32, 975, cx + 32, 975 + (26 if talk else 8)], fill=(10, 40, 70, 230))
    dh.ellipse([cx - 70, 900, cx - 30, 925], fill=(10, 40, 70, 230)); dh.ellipse([cx + 30, 900, cx + 70, 925], fill=(10, 40, 70, 230))
    hol = scanlines(hol, 0.6)
    img.alpha_composite(hol.filter(ImageFilter.GaussianBlur(18))); img.alpha_composite(hol)
    d = ImageDraw.Draw(img)
    # mesa del plató
    d.polygon([(0, 1430), (W, 1430), (W, 1560), (0, 1560)], fill=(14, 20, 50, 255))
    d.line([0, 1430, W, 1430], fill=CYAN + (255,), width=6)
    draw_text(d, (60, 1460), "M50 NOTICIAS", font(FB, 64), WHITE + (255,), sp=4)
    nfc_icon(d, 980, 1495, 70, CYAN + (255,))
    # rótulo inferior
    d.rectangle([0, 1580, 300, 1650], fill=RED + (255,)); draw_text(d, (22, 1588), "ÚLTIMA HORA", font(FB, 46), WHITE + (255,))
    d.rectangle([0, 1650, W, 1790], fill=(250, 250, 250, 255))
    draw_text(d, (22, 1662), "Los negocios de Melilla ya pueden", font(FXB, 50), (10, 10, 30, 255))
    draw_text(d, (22, 1722), "usar NFC para facilitar sus reseñas", font(FXB, 50), (10, 10, 30, 255))
    d.rectangle([0, 1790, W, 1860], fill=(10, 20, 60, 255))
    f = font(FXB, 40); tw = d.textlength(TICKER, font=f); x = -((t - 19) * 330) % tw
    draw_text(d, (x - tw, 1800), TICKER, f, GOLD + (255,)); draw_text(d, (x, 1800), TICKER, f, GOLD + (255,))
    draw_text(d, (W - 230, 1590), "20:50", font(FM, 50), WHITE + (255,))
    return img

def finale(t, p):
    t0 = t - 32.0
    bg = photo("finale_bg", "night").filter(ImageFilter.GaussianBlur(6 + 10 * min(1, t0 / 3.3)))
    img = cam(bg, p, 1.1, 1.35).convert("RGBA")
    img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 10, 110)))
    particles(img, t, 90, CYAN, 21, True, 6)
    if t0 < 3.3:                                # gira en el aire y crece hasta llenar la pantalla
        q = t0 / 3.3; grow = q ** 3
        width = 560 + 2600 * grow
        put_card(img, W / 2, H / 2 - 80 + 80 * grow, width, yaw=720 * eout(q), pitch=14 * (1 - q), roll=0,
                 shine=(q * 2) % 1, glow=1.6)
        return img
    # tarjeta a pantalla completa (cara frontal, en vertical) y textos finales
    t1 = t0 - 3.3
    full = CARD_F
    sc = max(W / full.size[0], H / full.size[1]) * (1.12 - 0.06 * min(1, t1 / 4.7))
    full = full.resize((int(full.size[0] * sc), int(full.size[1] * sc)), Image.BICUBIC)
    img2 = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img2.alpha_composite(full, (int(W / 2 - full.size[0] / 2), int(H / 2 - full.size[1] / 2)))
    img2 = img2.filter(ImageFilter.GaussianBlur(5)); img2.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 15, 200)))
    particles(img2, t, 60, GOLD, 31, True, 5)
    q0 = eout(t1 / 0.5)
    product_shot(img2, W / 2, 1015 + 40 * (1 - q0) + 8 * math.sin(t * 2), 640 + 80 * (1 - q0), t, glow=1.4, shine=(t1 / 1.8) % 1.3)
    lay = rgba(); d = ImageDraw.Draw(lay)
    for i, s in enumerate(["EL FUTURO", "DE TU NEGOCIO", "ESTÁ A", "UN TOQUE"]):
        q = back((t1 - i * 0.14) / 0.35)
        if t1 - i * 0.14 < 0: continue
        big = i == 3
        f = fit_font(d, s, FB, 180 if big else 104, W - 80)
        sub = rgba((W, 240)); ds = ImageDraw.Draw(sub)
        ctext(ds, 10, s, f, (CYAN if big else WHITE) + (255,), stroke=6, sf=(0, 0, 0, 255))
        sc2 = max(0.05, q); sub = sub.resize((int(W * sc2), int(240 * sc2)))
        lay.alpha_composite(sub, (int(W / 2 - sub.size[0] / 2), int(150 + [0, 120, 240, 360][i] + 120 - sub.size[1] / 2)))
    if t1 > 1.4:
        q = eout((t1 - 1.4) / 0.4)
        y = 1300 + (1 - q) * 80
        d.rounded_rectangle([90, y, W - 90, y + 150], 75, fill=GOLD + (int(255 * q),))
        ctext(d, y + 34, "CONSIGUE TU TARJETA NFC", fit_font(d, "CONSIGUE TU TARJETA NFC", FB, 66, W - 260), (10, 10, 20, int(255 * q)))
    if t1 > 2.3:
        q = eout((t1 - 2.3) / 0.4); pulse = 1 + 0.04 * math.sin(t * 8)
        y = 1475 + (1 - q) * 80
        sub = rgba((W, 140)); ds = ImageDraw.Draw(sub)
        ds.rounded_rectangle([120, 10, W - 120, 130], 60, outline=CYAN + (255,), width=6, fill=(5, 20, 35, 220))
        # sobre de mensaje
        ds.rectangle([175, 45, 255, 100], outline=WHITE + (255,), width=5); ds.line([175, 45, 215, 78, 255, 45], fill=WHITE + (255,), width=5)
        ctext(ds, 40, "ESCRÍBENOS POR PRIVADO", fit_font(ds, "ESCRÍBENOS POR PRIVADO", FB, 56, W - 470), WHITE + (255,), cx=W / 2 + 60)
        sub = sub.resize((int(W * pulse), int(140 * pulse)))
        a = np.asarray(sub).copy(); a[..., 3] = (a[..., 3] * q).astype(np.uint8); sub = Image.fromarray(a, "RGBA")
        lay.alpha_composite(sub, (int(W / 2 - sub.size[0] / 2), int(y)))
    glow_paste(img2, lay, 14)
    return img2

# ------------------------------------------------------------------ post-proceso
def glitch(img, t, amt):
    a = np.asarray(img.convert("RGB")).copy()
    n = int(6 + 14 * amt)
    for i in range(n):
        y = int(hrand(i, int(t * 30)) * H); h = int(10 + hrand(i, int(t * 30), 1) * 120 * amt)
        dx = int((hrand(i, int(t * 30), 2) - 0.5) * 220 * amt)
        a[y:y + h] = np.roll(a[y:y + h], dx, axis=1)
    sh = int(12 * amt) + 2
    a[..., 0] = np.roll(a[..., 0], sh, axis=1); a[..., 2] = np.roll(a[..., 2], -sh, axis=1)
    return Image.fromarray(a).convert("RGBA")

VIG = None
def vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.65)) ** 2 + ((yy - H / 2) / (H * 0.65)) ** 2)
    return np.clip(1.12 - r ** 2 * 0.55, 0.3, 1)[..., None].astype(np.float32)
VIG = vignette()
GRAIN = [np.random.default_rng(i).standard_normal((H // 2, W // 2)).astype(np.float32) * 6 for i in range(4)]
CUTS = [s[0] for s in SHOTS[1:]]

def frame(t, fi):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t) if t >= 0 else 0
    a, b, name = SHOTS[i]
    img = shot(name, t, a, b)
    # temblor de cámara en los golpes
    sh = 0.0
    for h in HITS:
        u = t - h
        if 0 <= u < 0.35: sh = max(sh, (1 - u / 0.35))
    if sh > 0:
        dx = (hrand(fi, 1) - 0.5) * 50 * sh; dy = (hrand(fi, 2) - 0.5) * 50 * sh
        img = img.transform((W, H), Image.AFFINE, (1 / 1.04, 0, -dx + W * 0.02, 0, 1 / 1.04, -dy + H * 0.02), Image.BILINEAR)
    # glitch en los cortes
    g = 0.0
    for c in CUTS:
        u = t - c
        if -0.05 <= u < 0.12: g = max(g, 1 - abs(u) / 0.12)
    if g > 0.15 and name not in ("tap",): img = glitch(img, t, g * 0.7)
    tl = title_layer(t)
    if tl is not None: img.alpha_composite(tl)
    arr = np.asarray(img.convert("RGB"), np.float32) * VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.18: arr += (1 - u / 0.18) * 150
    arr += np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    if t > TOTAL - 0.5: arr *= max(0, (TOTAL - t) / 0.5)
    out = to_img(arr)
    return out

def render_range(f0, f1, path):
    tmp = path.replace(".mp4", ".part.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.replace(tmp, path)

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for tt_ in [float(x) for x in sys.argv[2:]]:
            frame(tt_, int(tt_ * FPS)).save(os.path.join(HERE, "stills", f"still_{tt_:05.2f}.jpg"), quality=85)
    else:   # video <parte> <nºpartes>
        k, n = int(sys.argv[2]), int(sys.argv[3]); NF = int(round(TOTAL * FPS))
        f0, f1 = NF * k // n, NF * (k + 1) // n
        render_range(f0, f1, os.path.join(HERE, f"part_{k:02}.mp4")); print("parte", k, flush=True)
