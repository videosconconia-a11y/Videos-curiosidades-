# Render de "EL MISTERIO DE MELILLA" (1080x1920, 30 fps).
# Reutiliza de base.py (motor del anuncio Melilla 2050): fotos, placa NFC 3D, móvil, HUD, partículas, glitch.
import sys, os, math, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import base as B
from base import (W, H, FPS, CYAN, MAG, GOLD, RED, WHITE, FB, FXB, FBI, FM, font, to_img, ease, eout, back, hrand,
                  photo, cam, ctext, draw_text, text_w, fit_font, rgba, glow_paste, put_card, product_shot, particles,
                  phone, star, nfc_icon, glitch, scanlines)
from script_data import SHOTS, TITLES, HITS, TOTAL, ALIEN_SUBS

GREEN = (110, 255, 140); HAZ = (255, 210, 0)
B.PHOTO.update({
    "puerto": "Puerto Deportivo de Melilla.jpg",
    "search": "Vista aérea de la Plaza de España, Melilla, La Plaza (4682499007).jpg",
    "plaza_flores": "Plaza de España de Melilla (2).jpg",
    "barber": "Barber shop Porto.jpg",
    "doc_pergola": "Restaurante La Pergóla, Puerto Pesquero y Torres V Centenario.jpg",
    "doc_barber": "175 The Barber Shop, costa de la Pols 5 (Palma).jpg",
    "doc_cafe": "La Avenida, 21 y Hotel-Restaurante Marina.jpg",
    "doc_mercado": "Mercado Central2.jpg",
    "doc_calle": "Calle Ejército Español, Melilla 7.jpg",
    "doc_tienda": "La Avenida, 25, Melilla.jpg",
    "o_marina": "Puerta de la Marina, Melilla.jpg",
    "o_reconquista": "Antiguos almacenes La Reconquista, Melilla.jpg",
    "o_culturas": "Plaza de las Culturas.jpg",
    "o_sagrado": "Iglesia del Sagrado Corazón, Melilla.jpg",
    "o_playa": "Playa de los Cárabos (9436872331).jpg",
    "o_faro": "Faro de Melilla de Noche.jpg",
    "alien_bg": "MelillaLuces.jpg",
})
B.FOCUS.update({"plaza_flores": 0.5, "o_culturas": 0.45, "doc_calle": 0.35, "puerto": 0.3})

# ------------------------------------------------------------------ envolvente de la voz (para mover la boca del marciano)
VOX = np.zeros(int(TOTAL * FPS) + 2)
try:
    import soundfile as sf
    for m in json.load(open(os.path.join(HERE, "vo", "voice.json"))):
        if m["who"] != "alien": continue
        a, sr = sf.read(m["file"]); a = np.abs(a if a.ndim == 1 else a.mean(1))
        hop = sr // FPS
        for k in range(len(a) // hop):
            fi = int(round(m["start"] * FPS)) + k
            if fi < len(VOX): VOX[fi] = a[k * hop:(k + 1) * hop].mean()
    VOX = VOX / (VOX.max() + 1e-9)
except Exception as e:
    print("sin envolvente de voz:", e, file=sys.stderr)
def talk(t):
    fi = int(t * FPS); return float(VOX[fi]) if 0 <= fi < len(VOX) else 0.0

# ------------------------------------------------------------------ ovni
def make_ufo(Wd=900, Hd=440):
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
    img = np.zeros((Hd, Wd, 4), np.float32)
    def ell(cx, cy, rx, ry): return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    hull = ell(450, 290, 440, 95)
    g = np.clip((yy - 200) / 190, 0, 1)
    col = np.stack([200 - 150 * g, 205 - 150 * g, 220 - 140 * g], -1)
    col += (np.exp(-((yy - 262) / 9) ** 2) * 90)[..., None]                          # brillo del borde
    img[hull, :3] = col[hull]; img[hull, 3] = 255
    under = ell(450, 330, 250, 70) & (yy > 300)
    img[under, :3] = np.array([70, 80, 100]); img[under, 3] = 255
    core = ell(450, 352, 120, 34)
    img[core, :3] = np.array([120, 255, 230]); img[core, 3] = 255
    dome = ell(450, 230, 190, 175) & (yy < 255)
    dg = np.clip((yy - 60) / 200, 0, 1)
    dcol = np.stack([60 + 60 * (1 - dg), 200 - 60 * dg, 255 - 40 * dg], -1)
    dcol += (np.exp(-(((xx - 390) / 50) ** 2 + ((yy - 120) / 35) ** 2)) * 180)[..., None]
    img[dome, :3] = dcol[dome]; img[dome, 3] = 235
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")
UFO = make_ufo()
def ufo_sprite(t, width, tilt=0.0):
    s = UFO.copy(); d = ImageDraw.Draw(s)
    for k in range(11):                                   # luces que giran por el borde
        a = (k / 11) * 2 * math.pi + t * 3.0
        x = 450 + 400 * math.cos(a); y = 288 + 60 * math.sin(a)
        if math.sin(a) < -0.2: continue
        c = [CYAN, MAG, GOLD][k % 3] if int(t * 8 + k) % 3 else WHITE
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=c + (255,))
    g = rgba(s.size); g.alpha_composite(s); g = g.filter(ImageFilter.GaussianBlur(14))
    out = rgba(s.size); out.alpha_composite(g); out.alpha_composite(s)
    h = int(out.size[1] * width / out.size[0]); out = out.resize((int(width), max(1, h)), Image.LANCZOS)
    if tilt: out = out.rotate(tilt, Image.BICUBIC, expand=True)
    return out
def draw_ufo(img, cx, cy, width, t, tilt=0.0, beam=0.0, beam_len=900, halo=1.0):
    if beam > 0:
        lay = rgba(); d = ImageDraw.Draw(lay); w0 = width * 0.18; w1 = width * 0.75
        d.polygon([(cx - w0, cy + width * 0.08), (cx + w0, cy + width * 0.08), (cx + w1, cy + beam_len), (cx - w1, cy + beam_len)],
                  fill=(150, 255, 220, int(110 * beam)))
        d.ellipse([cx - w1, cy + beam_len - w1 * 0.18, cx + w1, cy + beam_len + w1 * 0.18], fill=(190, 255, 230, int(130 * beam)))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(28)))
    if halo:
        lay = rgba(); d = ImageDraw.Draw(lay)
        d.ellipse([cx - width * 0.7, cy - width * 0.25, cx + width * 0.7, cy + width * 0.3], fill=(120, 255, 220, int(70 * halo)))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(width * 0.12)))
    s = ufo_sprite(t, width, tilt); img.alpha_composite(s, (int(cx - s.size[0] / 2), int(cy - s.size[1] / 2)))

# ------------------------------------------------------------------ humo
def _puff():
    yy, xx = np.mgrid[0:256, 0:256]; r = np.sqrt((xx - 128) ** 2 + (yy - 128) ** 2) / 128
    n = np.random.default_rng(5).random((32, 32)); n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((256, 256), Image.BICUBIC)) / 255
    a = np.clip(1 - r, 0, 1) ** 1.6 * (0.6 + 0.4 * n) * 255
    out = np.zeros((256, 256, 4), np.uint8); out[..., :3] = 215; out[..., 3] = a.astype(np.uint8)
    return Image.fromarray(out, "RGBA")
PUFF = _puff()
def smoke(img, t, t0, cx, cy, spread=600, n=26, tint=(215, 230, 235), alpha=1.0):
    if t < t0: return
    u = t - t0; lay = rgba()
    for i in range(n):
        ang = hrand(i, 3) * 2 * math.pi; sp = 0.4 + hrand(i, 4)
        r = spread * (1 - math.exp(-u * 1.4 * sp))
        x = cx + r * math.cos(ang) * 1.3; y = cy + r * math.sin(ang) * 0.25 - u * 60 * hrand(i, 5)
        s = int(220 + 380 * min(1, u / 2.5) * (0.5 + hrand(i, 6)))
        a = max(0.0, 1 - u / 4.0) * (0.55 + 0.45 * hrand(i, 7)) * alpha
        p = PUFF.resize((s, s)); ar = np.asarray(p).copy(); ar[..., 3] = (ar[..., 3] * a).astype(np.uint8)
        ar[..., :3] = np.array(tint, np.uint8)
        lay.alpha_composite(Image.fromarray(ar, "RGBA"), (int(x - s / 2), int(y - s / 2)))
    img.alpha_composite(lay)

# ------------------------------------------------------------------ extraterrestre
SKIN = (128, 205, 120); SKIN2 = (88, 160, 86); SUIT = (200, 208, 222); SUIT2 = (140, 150, 170)
def alien_sprite(t, talk_=0.0, blink=False, look=(0.0, 0.0), walk=0.0, arm_up=0.0):
    """Marciano entero (estilo CGI de dibujos). Lienzo 760x1500, cabeza arriba."""
    S = rgba((760, 1500)); d = ImageDraw.Draw(S); cx = 380
    sw = math.sin(walk * 2 * math.pi)
    # piernas
    for sgn in (-1, 1):
        lx = cx + sgn * 70 + sgn * 18 * sw * sgn
        d.rounded_rectangle([lx - 46, 1080, lx + 46, 1440 - (20 * max(0, sw * sgn))], 40, fill=SUIT2 + (255,))
        d.ellipse([lx - 70, 1400, lx + 70, 1470], fill=(60, 66, 84, 255))
    # cuerpo (mono plateado)
    d.rounded_rectangle([cx - 160, 720, cx + 160, 1130], 120, fill=SUIT + (255,))
    d.rectangle([cx - 160, 990, cx + 160, 1030], fill=(40, 200, 220, 255))
    nfc_icon(d, cx - 10, 860, 120, (40, 200, 220, 255))
    # brazos
    for sgn in (-1, 1):
        up = arm_up if sgn == 1 else 0
        x0 = cx + sgn * 160; y0 = 780
        x1 = x0 + sgn * 90; y1 = 1060 - up * 420
        d.line([x0, y0, x1, y1], fill=SUIT2 + (255,), width=70)
        d.ellipse([x1 - 50, y1 - 50, x1 + 50, y1 + 50], fill=SKIN + (255,))
        for f in (-1, 0, 1):   # tres dedos largos
            d.line([x1, y1, x1 + sgn * 20 + f * 30, y1 + 85 - up * 170], fill=SKIN + (255,), width=20)
    # cuello y cabeza (pera invertida)
    d.rectangle([cx - 40, 640, cx + 40, 740], fill=SKIN2 + (255,))
    d.ellipse([cx - 300, 40, cx + 300, 560], fill=SKIN + (255,))
    d.ellipse([cx - 170, 330, cx + 170, 720], fill=SKIN + (255,))
    d.ellipse([cx - 210, 90, cx + 60, 300], fill=(160, 230, 150, 110))               # brillo
    # antenas
    for sgn in (-1, 1):
        wob = 18 * math.sin(t * 6 + sgn)
        d.line([cx + sgn * 120, 80, cx + sgn * 190 + wob, -0 + 25], fill=SKIN2 + (255,), width=12)
        d.ellipse([cx + sgn * 190 + wob - 26, 0, cx + sgn * 190 + wob + 26, 52], fill=(255, 240, 120, 255) if int(t * 4) % 2 else (180, 255, 160, 255))
    # ojos almendrados
    lx, ly = look
    for sgn in (-1, 1):
        ex, ey = cx + sgn * 130, 380
        e = rgba((300, 200)); de = ImageDraw.Draw(e)
        if blink: de.rounded_rectangle([20, 92, 280, 108], 8, fill=(15, 20, 15, 255))
        else:
            de.ellipse([10, 20, 290, 180], fill=(12, 14, 20, 255))
            hx, hy = 110 + lx * 60, 70 + ly * 40
            de.ellipse([hx - 26, hy - 22, hx + 26, hy + 22], fill=(230, 250, 255, 255))
            de.ellipse([hx + 50, hy + 30, hx + 66, hy + 44], fill=(140, 230, 255, 255))
        e = e.rotate(-sgn * 22, Image.BICUBIC, expand=True)
        S.alpha_composite(e, (int(ex - e.size[0] / 2), int(ey - e.size[1] / 2)))
    # boca
    o = 4 + 46 * talk_
    d.ellipse([cx - 40 - 10 * talk_, 585 - o / 2, cx + 40 + 10 * talk_, 585 + o / 2], fill=(40, 60, 40, 255))
    return S

def alien_hand_phone(state, p, t, scale=1.0, ang=0.0):
    """Mano verde de tres dedos sujetando el móvil (manga plateada)."""
    PW, PH = B.PW, B.PH
    lay = rgba((PW + 360, PH + 560)); d = ImageDraw.Draw(lay); ox, oy = 180, 120
    d.rounded_rectangle([ox + 60, oy + PH - 420, ox + PW + 40, oy + PH + 180], 160, fill=SKIN2 + (255,))
    d.rounded_rectangle([ox + 120, oy + PH + 60, ox + PW, oy + PH + 560], 120, fill=SUIT + (255,))
    d.rectangle([ox + 120, oy + PH + 90, ox + PW, oy + PH + 130], fill=(40, 200, 220, 255))
    lay.alpha_composite(phone(state, p, t), (ox, oy))
    for k in range(3):
        y = oy + PH - 600 + k * 170
        d.rounded_rectangle([ox - 110, y, ox + 40, y + 120], 60, fill=SKIN + (255,))
        d.ellipse([ox - 120, y + 10, ox - 30, y + 110], fill=(170, 240, 160, 255))
    d.rounded_rectangle([ox + PW - 50, oy + PH - 560, ox + PW + 80, oy + PH - 160], 65, fill=SKIN + (255,))
    if scale != 1.0: lay = lay.resize((int(lay.size[0] * scale), int(lay.size[1] * scale)), Image.LANCZOS)
    if ang: lay = lay.rotate(ang, Image.BICUBIC, expand=True)
    return lay

# ------------------------------------------------------------------ galaxia
def make_galaxy(w=1300, h=2300):
    rng = np.random.default_rng(42)
    def nz(sc, seed):
        r = np.random.default_rng(seed).random((h // sc + 2, w // sc + 2))
        return np.asarray(Image.fromarray((r * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    n = nz(220, 1) * 0.5 + nz(90, 2) * 0.3 + nz(30, 3) * 0.2
    m = nz(260, 7) * 0.6 + nz(70, 8) * 0.4
    a = np.zeros((h, w, 3), np.float32) + np.array([3, 3, 14])
    a += (np.clip(n - 0.45, 0, 1) ** 1.5 * 3.2)[..., None] * np.array([190, 40, 170])
    a += (np.clip(m - 0.5, 0, 1) ** 1.5 * 3.2)[..., None] * np.array([30, 140, 220])
    st = rng.random((h, w)) > 0.9975; a[st] = 255
    img = to_img(a); d = ImageDraw.Draw(img)
    for i in range(70):
        x, y, s = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(2, 5)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 255, 255))
    return Image.blend(img, img.filter(ImageFilter.GaussianBlur(6)), 0.3)
GALAXY = make_galaxy()

# ------------------------------------------------------------------ elementos de escena
def counter(img, y0=1430):
    lay = rgba(); d = ImageDraw.Draw(lay)
    for y in range(y0, H, 6):
        k = (y - y0) / (H - y0)
        d.rectangle([0, y, W, y + 6], fill=(int(70 - 30 * k), int(44 - 20 * k), int(30 - 14 * k), 255))
    d.rectangle([0, y0, W, y0 + 10], fill=(150, 110, 80, 255))
    img.alpha_composite(lay)

def light_burst(img, t, t0, cx, cy):
    u = t - t0
    if not (0 <= u < 1.0): return
    lay = rgba(); d = ImageDraw.Draw(lay); a = 1 - u
    for k in range(28):
        ang = k / 28 * 2 * math.pi + u * 0.6; L = 400 + 1800 * eout(u / 0.5)
        w = 0.05
        d.polygon([(cx, cy), (cx + L * math.cos(ang - w), cy + L * math.sin(ang - w)), (cx + L * math.cos(ang + w), cy + L * math.sin(ang + w))],
                  fill=(255, 255, 230, int(170 * a)))
    r = 150 + 900 * eout(u / 0.4)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, int(220 * max(0, 1 - u / 0.6))))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(20)))

def hazard_bar(d, y, h, t):
    d.rectangle([0, y, W, y + h], fill=HAZ + (255,))
    off = (t * 220) % 80
    for x in range(-120, W + 120, 80):
        d.polygon([(x + off, y), (x + 40 + off, y), (x + off, y + h), (x - 40 + off, y + h)], fill=(15, 15, 15, 255))

def doc_overlay(img, t, a, b, label, sub=None, first=False):
    lay = rgba(); d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, W, 150], fill=(0, 0, 0, 255)); d.rectangle([0, H - 150, W, H], fill=(0, 0, 0, 255))
    p = eout((t - a - 0.1) / 0.35)
    x0 = 60 - (1 - p) * 400
    d.rectangle([x0, 1420, x0 + 14, 1560], fill=GOLD + (255,))
    d.rectangle([x0 + 14, 1420, x0 + 760, 1560], fill=(0, 0, 0, 170))
    draw_text(d, (x0 + 40, 1432), label, font(FB, 52), WHITE + (255,))
    if sub: draw_text(d, (x0 + 40, 1500), sub, font(FXB, 36), (230, 220, 190, 255))
    draw_text(d, (60, 172), "● OBSERVACIÓN DE CAMPO", font(FM, 30), (255, 90, 90, 255) if int(t * 2) % 2 else (255, 255, 255, 200))
    draw_text(d, (W - 300, 172), f"00:{int(t * 100) % 6000:04d}", font(FM, 30), (255, 255, 255, 200))
    img.alpha_composite(lay)

def doc_title(img, t):
    if not (16.0 <= t < 17.5): return
    u = t - 16.0; a = min(1, u / 0.3) * min(1, (17.5 - t) / 0.3)
    lay = rgba(); d = ImageDraw.Draw(lay)
    serif = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    ctext(d, 640, "EL COMERCIANTE", font(serif, 92), WHITE + (int(255 * a),), sp=6, stroke=3, sf=(0, 0, 0, int(200 * a)))
    ctext(d, 760, "MELILLENSE", font(serif, 120), GOLD + (int(255 * a),), sp=8, stroke=3, sf=(0, 0, 0, int(200 * a)))
    ctext(d, 920, "Homo commercialis melillensis", font("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 44), (240, 235, 220, int(255 * a)))
    img.alpha_composite(lay)

def binoculars(img):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    d.ellipse([20, 520, 560, 1200], fill=255); d.ellipse([520, 520, 1060, 1200], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(14))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255)); black.putalpha(Image.eval(m, lambda v: 255 - v))
    img.alpha_composite(black)

# ------------------------------------------------------------------ planos
DOC = {"doc_pergola": ("HÁBITAT: RESTAURANTE", "Puerto de Melilla"), "doc_barber": ("HÁBITAT: BARBERÍA", "Ejemplar en pleno corte"),
       "doc_cafe": ("HÁBITAT: HOSTELERÍA", "La Avenida, Melilla"), "doc_mercado": ("HÁBITAT: MERCADO", "Mercado Central"),
       "doc_calle": ("HÁBITAT: CALLE COMERCIAL", "C/ Ejército Español"), "doc_tienda": ("HÁBITAT: TIENDA", "Nuevo: tecnología NFC")}
DOC_CARD = {"doc_pergola": (800, 1180), "doc_barber": (820, 1240), "doc_cafe": (280, 1240), "doc_mercado": (800, 1240),
            "doc_calle": (270, 1240), "doc_tienda": (790, 1240)}

def shot(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0)
    if name == "black":
        img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        if int(t * 8) % 2 == 0:
            d = ImageDraw.Draw(img); d.ellipse([W / 2 - 18, H / 2 - 18, W / 2 + 18, H / 2 + 18], fill=RED + (255,))
        return img
    if name == "aerial_ufo":
        img = cam(photo("aerial", "night"), p, 1.05, 1.35, 0.2, 0.1).convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), RED + (int(60 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.6))),)))
        q = eout(p)
        draw_ufo(img, W * 0.85 - 400 * q, 1020 + 330 * q, 170 + 230 * q, t, tilt=-12 + 8 * q, beam=0.6 * (int(t * 6) % 2), beam_len=420)
        B.hud(img, t, "ALERTA · OBJETO NO IDENTIFICADO"); return img
    if name == "fly_puerto":
        img = cam(photo("puerto", "night"), p, 1.1, 1.25, -0.4, 0).convert("RGBA")
        x = -400 + (W + 800) * p
        lay = rgba(); d = ImageDraw.Draw(lay)
        d.ellipse([x - 700, 300, x + 700, 1500], fill=(150, 255, 220, 50)); img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(120)))
        draw_ufo(img, x, 620, 720, t, tilt=8, halo=1.2)
        particles(img, t, 30, CYAN, 9); return img
    if name == "fly_search":
        img = cam(photo("search", "night"), p, 1.0, 1.15, 0.3, 0.2).convert("RGBA")
        sx = W * (0.25 + 0.5 * p); sy = 1150 + 200 * math.sin(p * 3)
        lay = rgba(); d = ImageDraw.Draw(lay)
        d.polygon([(W / 2 - 40, 0), (W / 2 + 40, 0), (sx + 230, sy), (sx - 230, sy)], fill=(170, 255, 220, 70))
        d.ellipse([sx - 260, sy - 110, sx + 260, sy + 110], fill=(200, 255, 230, 120))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(25)))
        draw_ufo(img, W / 2, -60, 900, t, halo=0.8)
        return img
    if name == "landing":
        img = cam(photo("plaza_flores", "night"), p, 1.05, 1.18, 0, -0.2).convert("RGBA")
        q = eout(min(1, (t - 5.0) / 1.05))
        cy = 200 + (1180 - 200) * q
        draw_ufo(img, W / 2, cy, 640 + 120 * q, t, beam=0.9 if t < 6.05 else 0.4, beam_len=max(60, 1380 - cy), halo=1.3)
        smoke(img, t, 5.6, W / 2, 1380, spread=700, n=24)
        smoke(img, t, 6.05, W / 2, 1400, spread=1000, n=18, alpha=0.9)
        particles(img, t, 40, (180, 255, 220), 13, True, 5)
        B.hud(img, t, "CONTACTO · PLAZA DE ESPAÑA", tint=GREEN); return img
    if name in ("barber_enter", "barber_zoom"):
        tt = min(t, 9.1)
        bg = photo("barber", "future")
        img = cam(bg, 0.5, 1.12, 1.12).convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 20, 10, 70)))
        q = eout((tt - 7.0) / 1.5)
        al = alien_sprite(t, talk(t), blink=(int(t * 10) % 23 == 0), look=(-0.6 * q, 0.7 * q), walk=(tt - 7) * 1.6 * (1 - q))
        sc = 0.82; al = al.resize((int(al.size[0] * sc), int(al.size[1] * sc)))
        ax = W + 200 - (W + 200 - W * 0.66) * q; ay = 420 + 14 * abs(math.sin((tt - 7) * 6)) * (1 - q)
        img.alpha_composite(al, (int(ax - al.size[0] / 2), int(ay)))
        counter(img, 1430)
        put_card(img, W * 0.36, 1590, 520, yaw=-8, pitch=55, roll=-6, shine=((t - 7) / 1.3) % 1.5, glow=1.0 + (1.0 if name == "barber_zoom" else 0))
        if name == "barber_enter":
            if t > 8.4:
                d = ImageDraw.Draw(img)
                for k in range(3):
                    s = 90 + 30 * k; x = ax - 140 + k * 140; y = 330 - 25 * math.sin(t * 7 + k)
                    d.text((x, y), "?", font=font(FB, s), fill=GOLD + (255,), stroke_width=7, stroke_fill=(0, 0, 0, 255))
            return img
        # zoom exagerado sobre la placa
        z = 1 + 1.55 * eout((t - 9.1) / 0.28) + 0.12 * p
        fx, fy = W * 0.36, 1590
        cw, ch = W / z, H / z
        x0 = min(max(fx - cw / 2, 0), W - cw); y0 = min(max(fy - ch * 0.55, 0), H - ch)
        img = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
        lay = rgba(); d = ImageDraw.Draw(lay)
        if t < 9.45:      # líneas de velocidad
            for k in range(40):
                ang = hrand(k, 2) * 2 * math.pi; r0 = 300 + hrand(k, 3) * 300
                d.line([W / 2 + r0 * math.cos(ang), H / 2 + r0 * math.sin(ang), W / 2 + 1500 * math.cos(ang), H / 2 + 1500 * math.sin(ang)],
                       fill=(255, 255, 255, 150), width=5)
        sx = int(70 + 10 * math.sin(t * 20)); d.rectangle([sx, 330, W - sx, 1560], outline=GREEN + (230,), width=6)
        draw_text(d, (sx + 20, 1490), "ANALIZANDO OBJETO" + "." * (int(t * 4) % 4), font(FM, 40), GREEN + (255,))
        yscan = 330 + (t * 700) % 1230; d.line([sx, yscan, W - sx, yscan], fill=GREEN + (200,), width=5)
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3))); img.alpha_composite(lay)
        return img
    if name == "tap":
        bg = photo("barber", "future").filter(ImageFilter.GaussianBlur(12))
        img = cam(bg, p, 1.15, 1.25).convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 15, 10, 110)))
        counter(img, 1250)
        put_card(img, W / 2, 1530, 780, yaw=0, pitch=58, shine=((t - 11.5) / 1.2) % 1.6, glow=1.0 + (1.6 if 12.6 < t < 13.1 else 0))
        tap = 12.6
        if t < tap: q = eout((t - 11.5) / 1.1); y = 2150 + (1060 - 2150) * q; state = "scan"; sp = (t - 11.5) / 1.1
        else: q = ease((t - tap - 0.35) / 0.6); y = 1060 - 150 * q; state = "reviews" if t > tap + 0.2 else "scan"; sp = (t - tap - 0.2) / 2.6
        hp = alien_hand_phone(state, sp, t, scale=0.76, ang=-6 + 6 * (q if t >= tap else 0))
        img.alpha_composite(hp, (int(W / 2 - hp.size[0] / 2 + 60), int(y - 200)))
        light_burst(img, t, tap, W / 2, 1450)
        if t > tap + 0.5:
            lay = rgba(); d = ImageDraw.Draw(lay); pp = min(1, (t - tap - 0.5) / 0.25)
            d.rounded_rectangle([210, 1650, W - 210, 1760], 55, fill=(10, 30, 40, int(220 * pp)), outline=CYAN + (int(255 * pp),), width=4)
            ctext(d, 1675, "ENLACE ABIERTO", font(FM, 50), CYAN + (int(255 * pp),))
            glow_paste(img, lay, 10)
        return img
    if name in DOC:
        img = cam(photo(name, "warm"), p, 1.06, 1.18, (-1) ** len(name) * 0.4, 0.1).convert("RGBA")
        cx, cy = DOC_CARD[name]
        put_card(img, cx, cy + 10 * math.sin(t * 2), 260, yaw=12 * math.sin(t), pitch=8, roll=-4, shine=p, glow=1.1)
        d = ImageDraw.Draw(img)        # flecha de "nuevo ejemplar"
        ax = cx + (-1 if cx > W / 2 else 1) * 230
        d.line([ax, cy - 190, cx + (-1 if cx > W / 2 else 1) * 120, cy - 110], fill=GOLD + (255,), width=8)
        if name == "doc_cafe": binoculars(img)
        lab, sub = DOC[name]
        doc_overlay(img, t, a, b, lab, sub)
        doc_title(img, t)
        return img
    if name == "alien_cam":
        img = cam(photo("alien_bg", "night"), p, 1.2, 1.3).filter(ImageFilter.GaussianBlur(8)).convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 40, 20, 120)))
        bl = (int(t * 10) % 31 == 0)
        al = alien_sprite(t, talk(t), blink=bl, look=(0.0, 0.1), arm_up=0.0)
        sc = 1.75 + 0.06 * p
        al = al.resize((int(al.size[0] * sc), int(al.size[1] * sc)), Image.BICUBIC)
        img.alpha_composite(al, (int(W / 2 - al.size[0] / 2), int(190 - 30 * p)))
        img = scanlines(img, 0.18)
        lay = rgba(); d = ImageDraw.Draw(lay)
        d.rectangle([40, 190, W - 40, 270], fill=(0, 0, 0, 160))
        draw_text(d, (70, 206), "TRANSMISIÓN INTERCEPTADA", font(FM, 44), GREEN + (255,) if int(t * 3) % 2 else (200, 255, 210, 255))
        if int(t * 2) % 2 == 0: d.ellipse([W - 120, 212, W - 80, 252], fill=RED + (255,))
        draw_text(d, (70, H - 390), "ORIGEN: DESCONOCIDO · SEÑAL 98%", font(FM, 32), GREEN + (220,))
        img.alpha_composite(lay)
        if hrand(int(t * 15), 9) > 0.9: img = glitch(img, t, 0.35)
        return img
    if name.startswith("o_"):
        k = ["o_marina", "o_reconquista", "o_culturas", "o_sagrado", "o_playa", "o_faro"].index(name)
        img = cam(photo(name, "warm"), p, 1.06, 1.2, (-1) ** k * 0.5, 0.1).convert("RGBA")
        if name == "o_faro":
            draw_ufo(img, W * 0.2 + W * 0.8 * p, 520 - 380 * p, 260 - 150 * p, t, tilt=-10, halo=0.8)
        img.alpha_composite(B.SHADE)
        d = ImageDraw.Draw(img); d.rectangle([0, 0, W, 150], fill=(0, 0, 0, 255)); d.rectangle([0, H - 150, W, H], fill=(0, 0, 0, 255))
        return img
    if name == "space":
        img = cam(GALAXY, p, 1.05, 1.22, 0.3, -0.3).convert("RGBA")
        particles(img, t, 60, (200, 220, 255), 41, False, 3)
        u = t - 35.0
        if 0.6 < u < 3.6:
            q = (u - 0.6) / 3.0
            draw_ufo(img, -200 + (W + 400) * q, 1500 - 300 * q, 200, t, tilt=6, halo=0.6)
        q0 = eout(u / 0.8)
        put_card(img, W / 2, 980 + 20 * math.sin(t * 1.6), 380 + 220 * q0, yaw=(1 - q0) * 540 + 14 * math.sin(t * 1.2),
                 pitch=10 * math.sin(t * 0.9), roll=4 * math.sin(t * 0.7), shine=(u / 1.7) % 1.4, glow=1.8)
        lay = rgba(); d = ImageDraw.Draw(lay)
        for i, s in enumerate(["DA EL SALTO", "AL FUTURO"]):
            qq = back((u - 0.3 - i * 0.18) / 0.35)
            if u - 0.3 - i * 0.18 < 0: continue
            f = fit_font(d, s, FB, 170, W - 80)
            sub = rgba((W, 230)); ds = ImageDraw.Draw(sub)
            ctext(ds, 10, s, f, (WHITE if i == 0 else CYAN) + (255,), stroke=7, sf=(0, 0, 0, 255))
            scl = max(0.05, qq); sub = sub.resize((int(W * scl), int(230 * scl)))
            lay.alpha_composite(sub, (int(W / 2 - sub.size[0] / 2), int(300 + i * 190 - sub.size[1] / 2 + 100)))
        if u > 1.6:
            q = eout((u - 1.6) / 0.4); y = 1330 + (1 - q) * 80
            d.rounded_rectangle([70, y, W - 70, y + 140], 70, fill=GOLD + (int(255 * q),))
            s = "TARJETAS NFC PARA TU NEGOCIO"
            ctext(d, y + 34, s, fit_font(d, s, FB, 62, W - 220), (10, 10, 20, int(255 * q)))
        if u > 2.5:
            q = eout((u - 2.5) / 0.4); pulse = 1 + 0.04 * math.sin(t * 8); y = 1500 + (1 - q) * 80
            sub = rgba((W, 140)); ds = ImageDraw.Draw(sub)
            ds.rounded_rectangle([110, 10, W - 110, 130], 60, outline=CYAN + (255,), width=6, fill=(5, 20, 35, 230))
            ds.rectangle([170, 45, 250, 100], outline=WHITE + (255,), width=5); ds.line([170, 45, 210, 78, 250, 45], fill=WHITE + (255,), width=5)
            s = "ESCRÍBENOS POR PRIVADO"
            ctext(ds, 40, s, fit_font(ds, s, FB, 56, W - 470), WHITE + (255,), cx=W / 2 + 60)
            sub = sub.resize((int(W * pulse), int(140 * pulse)))
            ar = np.asarray(sub).copy(); ar[..., 3] = (ar[..., 3] * q).astype(np.uint8)
            lay.alpha_composite(Image.fromarray(ar, "RGBA"), (int(W / 2 - sub.size[0] / 2), int(y)))
        glow_paste(img, lay, 14)
        return img
    raise KeyError(name)

# ------------------------------------------------------------------ títulos
def title_layer(t):
    lay = rgba(); d = ImageDraw.Draw(lay); any_ = False
    for (a, b, lines, style) in TITLES:
        if not (a <= t < b): continue
        any_ = True; age = t - a; left = b - t
        if style == "alert":
            hazard_bar(d, 330, 46, t); hazard_bar(d, 860, 46, t)
            for i, s in enumerate(lines):
                q = eout((age - i * 0.2) / 0.22)
                if age - i * 0.2 < 0: continue
                f = fit_font(d, s, FB, 150 if i else 120, W - 80)
                jx = (hrand(int(t * 30), i) - 0.5) * 14
                col = WHITE if i < 2 else RED
                ctext(d, 410 + i * 150 + (1 - q) * 40, s, f, col + (int(255 * q),), stroke=9, sf=(0, 0, 0, int(255 * q)), cx=W / 2 + jx)
        elif style == "invade":
            for i, s in enumerate(lines):
                q = back((age - i * 0.25) / 0.35)
                if age - i * 0.25 < 0: continue
                f = fit_font(d, s, FB, 104 if i == 0 else 120, W - 70)
                sub = rgba((W, 200)); ds = ImageDraw.Draw(sub)
                ctext(ds, 20, s, f, (GREEN if i != 1 else WHITE) + (255,), stroke=9, sf=(0, 30, 0, 255))
                ang = 3 * math.sin(t * 5 + i * 2); scl = max(0.05, q)
                sub = sub.resize((int(W * scl), int(200 * scl))).rotate(ang, Image.BICUBIC, expand=True)
                lay.alpha_composite(sub, (int(W / 2 - sub.size[0] / 2), int(300 + i * 150 + 100 - sub.size[1] / 2)))
        elif style == "question":
            sh = (hrand(int(t * 24), 1) - 0.5) * 20
            for i, s in enumerate(lines):
                q = back((age - i * 0.15) / 0.3)
                if age - i * 0.15 < 0: continue
                f = fit_font(d, s, FB, 150, W - 70)
                sub = rgba((W, 220)); ds = ImageDraw.Draw(sub)
                ctext(ds, 20, s, f, (WHITE if i == 0 else GOLD) + (255,), stroke=10, sf=(0, 0, 0, 255))
                scl = max(0.05, q); sub = sub.resize((int(W * scl), int(220 * scl)))
                lay.alpha_composite(sub, (int(W / 2 - sub.size[0] / 2 + sh), int(170 + i * 170 + 110 - sub.size[1] / 2)))
        elif style in ("hero", "hero_low"):
            p = eout(age / 0.4); fo = min(1, left / 0.2); y0 = 260 if style == "hero" else 330
            for i, s in enumerate(lines):
                sp = int(30 * (1 - p)) + 2
                f = fit_font(d, s, FB, 140 if style == "hero" else 108, W - 90, sp)
                lt = rgba(); dl = ImageDraw.Draw(lt); g = rgba(); dg = ImageDraw.Draw(g)
                yy = y0 + i * (150 if style == "hero" else 122)
                ctext(dl, yy, s, f, WHITE + (int(255 * p * fo),), sp=sp, stroke=5, sf=(0, 0, 0, int(200 * p * fo)))
                ctext(dg, yy, s, f, (CYAN if style == "hero" else GREEN) + (int(255 * p * fo),), sp=sp)
                lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(16))); lay.alpha_composite(lt)
        elif style == "cine":
            fo = min(1, left / 0.2)
            for i, s in enumerate(lines):
                q = ease((age - i * 0.12) / 0.4); sp = int(12 + 16 * (1 - q)); last = i == len(lines) - 1
                f = fit_font(d, s, FB if last else FXB, 104 if last else 74, W - 90, sp)
                ctext(d, 1180 + i * 125 + (1 - q) * 30, s, f, (GOLD if last else WHITE) + (int(255 * q * fo),), sp=sp, stroke=4, sf=(0, 0, 0, int(170 * q * fo)))
    return lay if any_ else None

def alien_sub_layer(t, name):
    cur = [s for s in ALIEN_SUBS if s[0] <= t < s[1]]
    if not cur: return None
    a, b, s = cur[0]
    lay = rgba(); d = ImageDraw.Draw(lay)
    y = 650 if name in ("tap",) else (1660 if name != "alien_cam" else 1420)
    f = fit_font(d, s, FB, 58, W - 160)
    tw_ = text_w(d, s, f); pad = 34
    d.rounded_rectangle([W / 2 - tw_ / 2 - pad, y - 16, W / 2 + tw_ / 2 + pad, y + 82], 30, fill=(5, 30, 10, 225), outline=GREEN + (255,), width=4)
    draw_text(d, (W / 2 - tw_ / 2 - pad + 14, y - 58), "👽"[0:0] + "TRADUCCIÓN DEL MARCIANO", font(FM, 26), GREEN + (255,))
    ctext(d, y + 2, s, f, WHITE + (255,))
    return lay

# ------------------------------------------------------------------ fotograma
CUTS = [s[0] for s in SHOTS[1:]]
def frame(t, fi):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t)
    a, b, name = SHOTS[i]
    img = shot(name, t, a, b)
    sh = 0.0
    for h in HITS:
        u = t - h
        if 0 <= u < 0.4: sh = max(sh, 1 - u / 0.4)
    if sh > 0:
        dx = (hrand(fi, 1) - 0.5) * 56 * sh; dy = (hrand(fi, 2) - 0.5) * 56 * sh
        img = img.transform((W, H), Image.AFFINE, (1 / 1.04, 0, -dx + W * 0.02, 0, 1 / 1.04, -dy + H * 0.02), Image.BILINEAR)
    g = 0.0
    for c in CUTS:
        u = t - c
        if -0.05 <= u < 0.12: g = max(g, 1 - abs(u) / 0.12)
    if g > 0.15 and name not in ("tap",): img = glitch(img, t, g * 0.7)
    tl = title_layer(t)
    if tl is not None: img.alpha_composite(tl)
    sl = alien_sub_layer(t, name)
    if sl is not None: img.alpha_composite(sl)
    arr = np.asarray(img.convert("RGB"), np.float32) * B.VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.18: arr += (1 - u / 0.18) * 150
    arr += np.repeat(np.repeat(B.GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    if t > TOTAL - 0.45: arr *= max(0, (TOTAL - t) / 0.45)
    return to_img(arr)

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
    else:
        k, n = int(sys.argv[2]), int(sys.argv[3]); NF = int(round(TOTAL * FPS))
        render_range(NF * k // n, NF * (k + 1) // n, os.path.join(HERE, f"part_{k:02}.mp4")); print("parte", k, flush=True)
