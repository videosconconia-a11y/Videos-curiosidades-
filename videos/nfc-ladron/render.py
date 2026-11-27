# Render de "¿TÚ SABES LO QUE ES UNA NFC?" (1080x1920, 30 fps).
# Personajes y tienda dibujados por código (estilo dibujos animados) + fotos reales de Melilla (Wikimedia Commons).
# Motor compartido (fotos, cámara, texto, efectos): base.py
import sys, os, math, json, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import base as B
from base import (W, H, FPS, BW, BH, CYAN, MAG, GOLD, RED, WHITE, FB, FXB, FBI, FM, font, to_img, ease, eout, back, hrand,
                  photo, cam, ctext, draw_text, text_w, fit_font, rgba, glow_paste, particles, star, nfc_icon, glitch, scanlines)
from script_data import SHOTS, HITS, TOTAL, VOICE, PRICE, PHONE

PINK = (255, 90, 160); YEL = (255, 214, 0); INK = (25, 25, 35)
B.PHOTO.update({
    "street": "Calle Ejército Español, Melilla 7.jpg",
    "u_web": "Melilla - Plaza de España - Centro.jpg",
    "u_catalogo": "La Avenida, Melilla, 7.jpg",
    "u_promo": "La Avenida, 25, Melilla.jpg",
    "u_contacto": "Casa Tortosa Melilla.jpg",
    "u_video": "Frente de la Marina, Melilla la Vieja.jpg",
    "thief_out": "Plaza de España de Melilla (2).jpg",
    "m_reconquista": "Antiguos almacenes La Reconquista, Melilla.jpg",
    "m_asamblea": "Palacio de la Asamblea de Melilla, Amaneciendo en Melilla.jpg",
    "endcard": "Aterrizando en Melilla (16668390111).jpg",
})
B.FOCUS.update({"u_web": 0.5, "u_video": 0.55, "m_asamblea": 0.42, "thief_out": 0.5, "street": 0.4})
B.EXTRA.update({"u_video": (1.4, 0.85), "m_asamblea": (1.3, 0.75)})
PLACE = {"u_web": "Plaza de España", "u_catalogo": "La Avenida", "u_promo": "La Avenida", "u_contacto": "Casa Tortosa · modernismo",
         "u_video": "Melilla la Vieja", "thief_out": "Plaza de España", "m_reconquista": "Almacenes La Reconquista · modernismo",
         "m_asamblea": "Palacio de la Asamblea · modernismo"}

# ------------------------------------------------------------------ voz: envolvente por personaje + palabras cronometradas
META = json.load(open(os.path.join(HERE, "vo", "voice.json")))
ENV = {k: np.zeros(int(TOTAL * FPS) + 2) for k in ("dependiente", "cliente", "ladron")}
import soundfile as sf
for m in META:
    a, sr = sf.read(m["file"]); a = np.abs(a if a.ndim == 1 else a.mean(1)); hop = sr // FPS
    for k in range(len(a) // hop):
        fi = int(round(m["start"] * FPS)) + k
        if fi < len(ENV[m["who"]]): ENV[m["who"]][fi] = a[k * hop:(k + 1) * hop].mean()
for k in ENV: ENV[k] = np.clip(ENV[k] / (ENV[k].max() + 1e-9) * 1.6, 0, 1)
def talk(who, t):
    fi = int(t * FPS); return float(ENV[who][fi]) if 0 <= fi < len(ENV[who]) else 0.0

WORDS = []        # (inicio, fin, palabra, resaltada, personaje, id_frase)
for li, ((start, who, _txt, sub), m) in enumerate(zip(VOICE, META)):
    toks = sub.split(" "); hl = False; ws = []
    for tk in toks:
        if tk.startswith("*") or tk.startswith("¿*") or tk.startswith("¿¡*"): hl = True
        clean = tk.replace("*", "")
        ws.append((clean, hl))
        if "*" in tk and (tk.rstrip(".,!?…:").endswith("*") or tk.endswith("*") or re.search(r"\*[^*]*$", tk) and tk.count("*") == 2): hl = False
        if tk.count("*") == 1 and not tk.lstrip("¿¡").startswith("*"): hl = False
    dur = m["dur"] - 0.1; wts = [len(w) + 2 for w, _ in ws]; tot = sum(wts); t0 = start + 0.03
    for (w, h_), wt in zip(ws, wts):
        d = dur * wt / tot; WORDS.append((t0, t0 + d, w, h_, who, li)); t0 += d
def chunks_for(li):
    ws = [w for w in WORDS if w[5] == li]; out = []; cur = []
    for w in ws:
        cur.append(w)
        if len(cur) >= 3 or sum(len(x[2]) for x in cur) > 15 or w[2][-1] in ".?!…:":
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out
CHUNKS = [c for li in range(len(VOICE)) for c in chunks_for(li)]

# ------------------------------------------------------------------ etiqueta NFC (producto genérico)
def make_tag(D=420):
    S = rgba((D + 80, D + 80)); d = ImageDraw.Draw(S); c = (D + 80) / 2
    sh = rgba(S.size); ImageDraw.Draw(sh).ellipse([c - D / 2 + 10, c - D / 2 + 18, c + D / 2 + 10, c + D / 2 + 18], fill=(0, 0, 0, 120))
    S.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d.ellipse([c - D / 2, c - D / 2, c + D / 2, c + D / 2], fill=(250, 250, 252, 255), outline=(210, 214, 225, 255), width=6)
    d.ellipse([c - D / 2 + 26, c - D / 2 + 26, c + D / 2 - 26, c + D / 2 - 26], outline=(20, 24, 40, 255), width=8)
    nfc_icon(d, c - 18, c - 40, D * 0.42, (20, 24, 40, 255))
    ctext(d, c + D * 0.12, "NFC", font(FB, int(D * 0.17)), (20, 24, 40, 255), cx=c)
    ctext(d, c + D * 0.31, "ACERCA TU MÓVIL", font(FXB, int(D * 0.07)), (60, 70, 100, 255), cx=c)
    hl = rgba(S.size); ImageDraw.Draw(hl).ellipse([c - D * 0.38, c - D * 0.45, c + D * 0.05, c - D * 0.15], fill=(255, 255, 255, 120))
    S.alpha_composite(hl.filter(ImageFilter.GaussianBlur(20)))
    return S
TAG = make_tag()
def put_tag(img, cx, cy, size, glow=0.0, persp=1.0):
    s = TAG.resize((int(size), max(1, int(size * persp))), Image.LANCZOS)
    if glow > 0:
        g = Image.new("RGBA", s.size, CYAN + (0,)); g.putalpha(s.getchannel("A").filter(ImageFilter.GaussianBlur(25)).point(lambda v: int(min(255, v * glow))))
        img.alpha_composite(g, (int(cx - s.size[0] / 2), int(cy - s.size[1] / 2)))
    img.alpha_composite(s, (int(cx - s.size[0] / 2), int(cy - s.size[1] / 2)))
def rings(img, cx, cy, u, col=CYAN, squash=1.0):
    if not (0 <= u < 1.0): return
    lay = rgba(); d = ImageDraw.Draw(lay)
    for k in range(4):
        r = u * 900 - k * 120
        if r > 0: d.ellipse([cx - r, cy - r * squash, cx + r, cy + r * squash], outline=col + (int(max(0, 255 - r / 3.5)),), width=10)
    glow_paste(img, lay, 10)

# ------------------------------------------------------------------ personajes (dibujos)
SKIN = (240, 196, 165); SKIN2 = (214, 160, 128); OUT = (60, 40, 35)
def limb(d, pts, col, w):
    d.line(pts, fill=col, width=w, joint="curve")
    for p in (pts[0], pts[-1]): d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)

def paco(t, talk_=0.0, pose="mug", look=(0, 0), blink=False, brow=0.0, smile=0.0):
    """Paco, el dependiente: calvo, bigote, gafas redondas, delantal. Lienzo 900x1300 (medio cuerpo)."""
    S = rgba((900, 1300)); d = ImageDraw.Draw(S)
    shirt = (236, 236, 228); apron = (36, 66, 112)
    d.rounded_rectangle([190, 640, 710, 1320], 190, fill=shirt)
    d.polygon([(285, 770), (615, 770), (665, 1320), (235, 1320)], fill=apron)
    d.line([(300, 772), (380, 640)], fill=apron, width=22); d.line([(600, 772), (520, 640)], fill=apron, width=22)
    d.rectangle([380, 920, 520, 1010], outline=(70, 100, 150), width=6); d.line([(470, 900), (470, 960)], fill=GOLD, width=10)
    d.rectangle([400, 560, 500, 680], fill=SKIN2)
    # brazos
    if pose == "mug":
        limb(d, [(250, 720), (190, 980), (340, 900)], shirt, 92)
        d.ellipse([300, 850, 390, 940], fill=SKIN)
        d.rounded_rectangle([320, 800, 420, 920], 16, fill=(250, 250, 250), outline=(180, 60, 50), width=8)
        d.arc([400, 825, 455, 885], -90, 90, fill=(180, 60, 50), width=9)
        for k in range(3):
            x = 340 + k * 30; ph = t * 3 + k
            d.line([(x, 790), (x + 12 * math.sin(ph), 750), (x - 8 * math.sin(ph + 1), 710)], fill=(255, 255, 255, 140), width=6)
    elif pose == "shrug":
        limb(d, [(230, 730), (110, 940), (90, 760)], shirt, 92); limb(d, [(670, 730), (790, 940), (810, 760)], shirt, 92)
        for x in (90, 810): d.ellipse([x - 55, 690, x + 55, 790], fill=SKIN)
    elif pose == "point":
        limb(d, [(250, 720), (200, 980), (330, 1080)], shirt, 92)
        limb(d, [(660, 720), (790, 800), (870, 860)], shirt, 92)
        d.ellipse([830, 820, 900, 890], fill=SKIN); d.line([(880, 850), (900, 900)], fill=SKIN, width=22)
    # cabeza
    d.ellipse([245, 290, 300, 410], fill=SKIN2); d.ellipse([600, 290, 655, 410], fill=SKIN2)
    d.ellipse([265, 100, 635, 590], fill=SKIN)
    d.ellipse([350, 140, 470, 215], fill=(255, 225, 200))
    for x0 in (250, 575): d.ellipse([x0, 230, x0 + 75, 400], fill=(168, 168, 172))
    # cejas
    for sgn, cx in ((-1, 380), (1, 520)):
        y = 262 - brow * 22
        d.line([(cx - 55, y + sgn * 0 + 6), (cx + 55, y - 6 * sgn * 0)], fill=(130, 130, 135), width=16)
    # ojos + gafas
    lx, ly = look
    for cx in (380, 520):
        if blink: d.line([(cx - 24, 352), (cx + 24, 352)], fill=INK, width=7)
        else:
            d.ellipse([cx - 16 + lx * 10, 338 + ly * 8, cx + 16 + lx * 10, 370 + ly * 8], fill=INK)
            d.ellipse([cx - 6 + lx * 10, 342 + ly * 8, cx + 2 + lx * 10, 350 + ly * 8], fill=WHITE)
            d.arc([cx - 30, 322, cx + 30, 372], 200, 340, fill=SKIN2, width=8)        # párpado tranquilo
        d.ellipse([cx - 60, 292, cx + 60, 412], outline=(40, 40, 50), width=10)
    d.line([(440, 340), (460, 340)], fill=(40, 40, 50), width=9)
    d.ellipse([423, 380, 477, 455], fill=SKIN2)
    # boca y bigote
    o = 8 + 52 * talk_
    if smile > 0 and talk_ < 0.2: d.arc([395, 470, 505, 540], 10, 170, fill=(120, 40, 40), width=10)
    else: d.ellipse([405, 505 - o / 2, 495, 505 + o / 2], fill=(110, 35, 40))
    d.chord([340, 425, 455, 510], 180, 360, fill=(125, 105, 95)); d.chord([445, 425, 560, 510], 180, 360, fill=(125, 105, 95))
    return S

def loli(t, talk_=0.0, pose="scream", look=(0, 0), angry=0.0):
    """Loli, la clienta: moño, pendientes, top rojo. Lienzo 900x1400 (medio cuerpo)."""
    S = rgba((900, 1400)); d = ImageDraw.Draw(S)
    top = (220, 40, 60); hair = (92, 52, 32); sk = (236, 188, 150); sk2 = (210, 155, 120)
    d.ellipse([220, 70, 680, 600], fill=hair); d.ellipse([370, -10, 530, 140], fill=hair)
    d.rounded_rectangle([190, 640, 710, 1420], 190, fill=top)
    d.line([(300, 650), (250, 1100)], fill=(60, 40, 30), width=14)              # asa del bolso
    d.rectangle([405, 560, 495, 680], fill=sk2)
    d.ellipse([300, 150, 600, 580], fill=sk)
    d.ellipse([270, 140, 630, 330], fill=hair); d.ellipse([310, 230, 590, 300], fill=sk)
    for x in (300, 600): d.ellipse([x - 16, 420, x + 16, 452], fill=GOLD)
    lx, ly = look
    for sgn, cx in ((-1, 390), (1, 510)):
        d.ellipse([cx - 38, 330, cx + 38, 412], fill=WHITE, outline=INK, width=5)
        d.ellipse([cx - 15 + lx * 12, 356 + ly * 10, cx + 15 + lx * 12, 386 + ly * 10], fill=INK)
        y = 305 + angry * 12
        d.line([(cx - 40, y - sgn * angry * 14 * -1 - 8 * (1 - angry)), (cx + 40, y + sgn * angry * 14 * -1 - 8 * (1 - angry))], fill=hair, width=12)
    d.ellipse([435, 400, 465, 450], fill=sk2)
    o = 14 + 120 * talk_
    d.ellipse([400, 480 - 10, 500, 480 + o], fill=(110, 25, 40))
    if talk_ > 0.3: d.ellipse([420, 480 + o * 0.45, 480, 480 + o * 0.9], fill=(230, 100, 110))
    if pose == "scream":
        limb(d, [(240, 720), (170, 900), (300, 480)], top, 88); limb(d, [(660, 720), (730, 900), (600, 480)], top, 88)
        d.ellipse([255, 430, 345, 530], fill=sk); d.ellipse([555, 430, 645, 530], fill=sk)
    elif pose == "cross":
        d.rounded_rectangle([230, 850, 680, 950], 50, fill=(200, 30, 50)); d.rounded_rectangle([220, 900, 670, 1000], 50, fill=(235, 50, 70))
        d.ellipse([640, 845, 720, 925], fill=sk); d.ellipse([180, 920, 260, 1000], fill=sk)
    elif pose == "point":
        limb(d, [(240, 720), (110, 760), (10, 700)], top, 88); d.ellipse([-20, 660, 50, 730], fill=sk)
        limb(d, [(660, 720), (730, 960), (640, 1100)], top, 88)
    return S

PAPERS = [("FOLLETOS", (255, 255, 255)), ("CATÁLOGO 2019", (255, 236, 150)), ("TARJETAS", (200, 230, 255)), ("FOLLETOS", (255, 210, 210)), ("CARTEL", (220, 255, 210))]
def ladron(t, phase=0.0, pose="run", talk_=0.0):
    """El ladrón de folletos: gorro, antifaz, camiseta de rayas. Lienzo 700x1500 (cuerpo entero)."""
    S = rgba((700, 1500)); d = ImageDraw.Draw(S)
    sw = math.sin(phase * 2 * math.pi)
    pants = (30, 30, 40); sk = (228, 180, 140)
    if pose == "run":
        for sgn in (-1, 1):
            a = sgn * sw * 0.7
            hx, hy = 350, 960; kx, ky = hx + 200 * math.sin(a), hy + 240 * math.cos(a) * 0.9
            fx, fy = kx + 150 * math.sin(a - 0.6 * sgn), ky + 230
            limb(d, [(hx, hy), (kx, ky), (fx, fy)], pants, 70)
            d.ellipse([fx - 60, fy - 20, fx + 70, fy + 40], fill=(15, 15, 20))
    else:
        for x in (290, 410):
            limb(d, [(x, 960), (x, 1300), (x, 1420)], pants, 70); d.ellipse([x - 60, 1400, x + 70, 1460], fill=(15, 15, 20))
    d.rounded_rectangle([200, 560, 500, 1000], 110, fill=WHITE)
    for k in range(6): d.rectangle([200, 600 + k * 70, 500, 635 + k * 70], fill=INK)
    d.ellipse([230, 230, 470, 560], fill=sk)
    d.chord([220, 180, 480, 420], 180, 360, fill=INK); d.rectangle([215, 290, 485, 330], fill=(50, 50, 60))
    d.rounded_rectangle([225, 345, 475, 420], 30, fill=INK)
    for cx in (300, 400):
        d.ellipse([cx - 30, 360, cx + 30, 405], fill=WHITE); d.ellipse([cx - 11, 370, cx + 11, 395], fill=INK)
    o = 10 + 40 * talk_
    d.ellipse([320, 470 - 4, 380, 470 + o], fill=(110, 30, 40))
    if pose == "run":       # montón de folletos en brazos
        for k, (lab, col) in enumerate(PAPERS):
            y = 640 + k * 70 + 8 * math.sin(t * 20 + k)
            d.rectangle([120 + k * 6, y, 560 - k * 4, y + 64], fill=col, outline=(120, 120, 130), width=3)
            ctext(d, y + 10, lab, font(FB, 38), (40, 40, 60), cx=340)
        d.ellipse([90, 820, 160, 890], fill=sk); d.ellipse([540, 820, 610, 890], fill=sk)
    elif pose == "toss":
        limb(d, [(220, 620), (130, 450), (110, 300)], WHITE, 70); limb(d, [(480, 620), (570, 450), (590, 300)], WHITE, 70)
        d.ellipse([75, 250, 145, 320], fill=sk); d.ellipse([555, 250, 625, 320], fill=sk)
    elif pose == "peek":
        limb(d, [(470, 640), (600, 700), (640, 560)], WHITE, 70); d.ellipse([605, 510, 675, 580], fill=sk)
        d.rectangle([560, 380, 700, 540], fill=(255, 236, 150), outline=(120, 120, 130), width=3)
        draw_text(d, (570, 440), "CATÁLOGO", font(FB, 22), (40, 40, 60))
    return S

def place(img, spr, cx, top, scale=1.0, flip=False, ang=0.0):
    s = spr
    if scale != 1.0: s = s.resize((max(1, int(s.size[0] * scale)), max(1, int(s.size[1] * scale))), Image.BICUBIC)
    if flip: s = s.transpose(Image.FLIP_LEFT_RIGHT)
    if ang: s = s.rotate(ang, Image.BICUBIC, expand=True)
    img.alpha_composite(s, (int(cx - s.size[0] / 2), int(top)))

# ------------------------------------------------------------------ la tienda (decorado)
WIN = (60, 300, 520, 1150)     # ventana (coordenadas del decorado 1260x2240)
def make_shop():
    a = np.zeros((BH, BW, 3), np.float32); yy = np.linspace(0, 1, BH)[:, None, None]
    a += np.array([250, 236, 210]) * (1 - yy) + np.array([232, 208, 172]) * yy
    img = to_img(a).convert("RGBA"); d = ImageDraw.Draw(img)
    d.rectangle([0, 1250, BW, 1330], fill=(205, 170, 130, 255))
    # escaparate con la calle real (C/ Ejército Español)
    st = photo("street", "future", (WIN[2] - WIN[0], WIN[3] - WIN[1]))
    img.paste(st, (WIN[0], WIN[1]))
    d.rectangle(WIN, outline=(110, 78, 55, 255), width=26)
    d.line([((WIN[0] + WIN[2]) / 2, WIN[1]), ((WIN[0] + WIN[2]) / 2, WIN[3])], fill=(110, 78, 55, 255), width=16)
    d.line([(WIN[0], 700), (WIN[2], 700)], fill=(110, 78, 55, 255), width=16)
    d.rounded_rectangle([110, 760, 260, 830], 12, fill=(30, 150, 70, 230)); ctext(d, 772, "ABIERTO", font(FB, 34), WHITE + (255,), cx=185)
    # estanterías con productos
    rng = np.random.default_rng(4)
    for y in (430, 720, 1010):
        d.rectangle([600, y, 1220, y + 22], fill=(150, 105, 70, 255))
        x = 615
        while x < 1190:
            w = int(rng.uniform(55, 110)); h = int(rng.uniform(110, 230))
            col = tuple(int(c) for c in rng.choice([(230, 80, 70), (60, 140, 220), (250, 190, 60), (90, 180, 120), (180, 110, 200), (240, 240, 240)]))
            d.rounded_rectangle([x, y - h, x + w, y], 8, fill=col + (255,), outline=(0, 0, 0, 60), width=2)
            d.rectangle([x + 8, y - h * 0.6, x + w - 8, y - h * 0.4], fill=(255, 255, 255, 170))
            x += w + 10
    d.rounded_rectangle([660, 110, 1180, 250], 26, fill=(36, 66, 112, 255))
    ctext(d, 140, "TIENDA DE PACO", font(FB, 62), WHITE + (255,), cx=920)
    # expositor de folletos… vacío
    d.rectangle([560, 1060, 590, 1500], fill=(120, 120, 130, 255))
    for k in range(3): d.rectangle([520, 1080 + k * 90, 640, 1150 + k * 90], outline=(120, 120, 130, 255), width=6)
    d.rounded_rectangle([500, 1000, 660, 1060], 10, fill=(250, 250, 250, 255)); ctext(d, 1012, "FOLLETOS", font(FB, 30), INK + (255,), cx=580)
    return img
SHOP = make_shop()

def counter_layer(t, tag_glow=0.0):
    C = rgba((BW, BH)); d = ImageDraw.Draw(C)
    d.rectangle([0, 1560, BW, BH], fill=(140, 92, 58, 255))
    for x in range(0, BW, 180): d.line([(x, 1640), (x, BH)], fill=(120, 78, 48, 255), width=6)
    d.rectangle([0, 1480, BW, 1580], fill=(196, 146, 98, 255)); d.rectangle([0, 1570, BW, 1590], fill=(110, 72, 45, 255))
    d.rounded_rectangle([90, 1280, 420, 1500], 24, fill=(70, 74, 90, 255)); d.rectangle([130, 1310, 380, 1390], fill=(150, 230, 190, 255))
    draw_text(d, (150, 1325), "0,00", font(FM, 50), (20, 60, 40, 255))
    put_tag(C, 940, 1490, 300, glow=tag_glow, persp=0.42)
    return C

def shop_scene(t, paco_kw=None, loli_kw=None, thief_kw=None, window_thief=None, paco_pos=(940, 420, 1.0), loli_pos=(330, 980, 1.0), tag_glow=0.0):
    img = SHOP.copy()
    if window_thief is not None:         # el ladrón visto por el escaparate
        cx, top, sc, ph, pose = window_thief
        spr = ladron(t, ph, pose)
        sub = rgba((BW, BH)); place(sub, spr, cx, top, sc)
        m = Image.new("L", (BW, BH), 0); ImageDraw.Draw(m).rectangle([WIN[0] + 13, WIN[1] + 13, WIN[2] - 13, WIN[3] - 13], fill=255)
        sub.putalpha(Image.fromarray(np.minimum(np.asarray(sub.getchannel("A")), np.asarray(m))))
        img.alpha_composite(sub)
        d = ImageDraw.Draw(img); d.rectangle(WIN, outline=(110, 78, 55, 255), width=26)
        d.line([((WIN[0] + WIN[2]) / 2, WIN[1]), ((WIN[0] + WIN[2]) / 2, WIN[3])], fill=(110, 78, 55, 255), width=16)
        d.line([(WIN[0], 700), (WIN[2], 700)], fill=(110, 78, 55, 255), width=16)
    if paco_kw is not None: place(img, paco(t, **paco_kw), paco_pos[0], paco_pos[1], paco_pos[2])
    img.alpha_composite(counter_layer(t, tag_glow))
    if thief_kw is not None:
        cx, top, sc, ph, pose, flip = thief_kw; place(img, ladron(t, ph, pose), cx, top, sc, flip)
    if loli_kw is not None: place(img, loli(t, **loli_kw), loli_pos[0], loli_pos[1], loli_pos[2])
    return img

# ------------------------------------------------------------------ móvil y pantallas
PW, PH = 560, 1140
def screen(kind, p):
    s = Image.new("RGBA", (PW - 40, PH - 40), (248, 248, 250, 255)); d = ImageDraw.Draw(s); sw, sh = s.size
    draw_text(d, (30, 18), "10:42", font(FXB, 30), INK + (255,)); draw_text(d, (sw - 110, 18), "5G ▮", font(FXB, 26), INK + (255,))
    d.rounded_rectangle([20, 64, sw - 20, 120], 28, fill=(232, 236, 244, 255)); draw_text(d, (46, 76), "tunegocio.es", font(FM, 26), (90, 100, 120, 255))
    q = eout(p / 0.35); oy = int((1 - q) * 300)
    if kind == "web":
        d.rectangle([0, 140 + oy, sw, 520 + oy], fill=(36, 66, 112, 255))
        ctext(d, 250 + oy, "TU NEGOCIO", font(FB, 64), WHITE + (255,), cx=sw / 2); ctext(d, 340 + oy, "Melilla", font(FXB, 38), (200, 220, 255, 255), cx=sw / 2)
        for k, lab in enumerate(["Ver catálogo", "Cómo llegar", "Llamar"]):
            y = 580 + k * 130 + oy
            d.rounded_rectangle([50, y, sw - 50, y + 100], 50, fill=(255, 200, 0, 255) if k == 0 else (230, 234, 242, 255))
            ctext(d, y + 26, lab, font(FXB, 40), INK + (255,), cx=sw / 2)
    elif kind == "catalogo":
        draw_text(d, (40, 150 + oy), "Catálogo", font(FB, 56), INK + (255,))
        cols = [(230, 80, 70), (60, 140, 220), (250, 190, 60), (90, 180, 120), (180, 110, 200), (240, 150, 90)]
        for k in range(6):
            x = 40 + (k % 2) * 230; y = 250 + (k // 2) * 270 + oy
            d.rounded_rectangle([x, y, x + 210, y + 250], 20, fill=(255, 255, 255, 255), outline=(220, 224, 232, 255), width=3)
            d.rounded_rectangle([x + 20, y + 20, x + 190, y + 160], 14, fill=cols[k] + (255,))
            draw_text(d, (x + 22, y + 178), f"Producto {k + 1}", font(FXB, 28), INK + (255,))
    elif kind == "promo":
        d.rounded_rectangle([30, 160 + oy, sw - 30, 640 + oy], 30, fill=(255, 60, 90, 255))
        ctext(d, 220 + oy, "OFERTA", font(FB, 90), WHITE + (255,), cx=sw / 2); ctext(d, 330 + oy, "DE LA SEMANA", font(FB, 56), YEL + (255,), cx=sw / 2)
        for k in range(5): star(d, sw / 2 - 160 + k * 80, 500 + oy, 30, YEL + (255,))
        ctext(d, 720 + oy, "Novedades, descuentos", font(FXB, 40), INK + (255,), cx=sw / 2)
        ctext(d, 780 + oy, "y eventos de tu tienda", font(FXB, 40), INK + (255,), cx=sw / 2)
    elif kind == "contacto":
        d.ellipse([sw / 2 - 110, 170 + oy, sw / 2 + 110, 390 + oy], fill=(36, 66, 112, 255)); ctext(d, 235 + oy, "TN", font(FB, 90), WHITE + (255,), cx=sw / 2)
        ctext(d, 420 + oy, "Tu Negocio", font(FB, 56), INK + (255,), cx=sw / 2); ctext(d, 490 + oy, "Melilla", font(FXB, 34), (110, 118, 135, 255), cx=sw / 2)
        for k, (lab, col) in enumerate([("Llamar", (40, 170, 90)), ("Enviar mensaje", (40, 120, 230)), ("Cómo llegar", (240, 150, 40)), ("Guardar contacto", (120, 120, 140))]):
            y = 580 + k * 120 + oy
            d.rounded_rectangle([50, y, sw - 50, y + 96], 48, fill=col + (255,)); ctext(d, y + 24, lab, font(FXB, 40), WHITE + (255,), cx=sw / 2)
    elif kind == "video":
        d.rounded_rectangle([20, 150 + oy, sw - 20, 600 + oy], 20, fill=(15, 18, 30, 255))
        d.polygon([(sw / 2 - 50, 300 + oy), (sw / 2 - 50, 450 + oy), (sw / 2 + 70, 375 + oy)], fill=WHITE + (255,))
        d.rectangle([40, 560 + oy, 40 + int((sw - 80) * min(1, p)), 572 + oy], fill=RED + (255,))
        ctext(d, 650 + oy, "Síguenos", font(FB, 52), INK + (255,), cx=sw / 2)
        for k, col in enumerate([(225, 48, 108), (20, 20, 20), (230, 30, 30), (24, 119, 242)]):
            x = 70 + k * 115; d.rounded_rectangle([x, 750 + oy, x + 95, 845 + oy], 26, fill=col + (255,))
            d.ellipse([x + 28, 778 + oy, x + 67, 817 + oy], outline=WHITE + (255,), width=6)
    return s
def phone_img(kind, p, scan=False):
    P = rgba((PW, PH)); d = ImageDraw.Draw(P)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], 74, fill=(22, 24, 30, 255), outline=(140, 150, 170, 255), width=5)
    if scan:
        s = Image.new("RGBA", (PW - 40, PH - 40), (12, 18, 40, 255)); ds = ImageDraw.Draw(s)
        nfc_icon(ds, s.size[0] / 2 - 20, s.size[1] / 2, 170, CYAN + (255,)); ctext(ds, s.size[1] / 2 + 150, "Acerca a la etiqueta", font(FXB, 36), WHITE + (255,), cx=s.size[0] / 2)
    else: s = screen(kind, p)
    m = Image.new("L", s.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, s.size[0] - 1, s.size[1] - 1], 56, fill=255)
    P.paste(s, (20, 20), m); d.rounded_rectangle([PW / 2 - 60, 34, PW / 2 + 60, 64], 15, fill=(0, 0, 0, 255))
    return P

# ------------------------------------------------------------------ subtítulos dinámicos (palabra a palabra)
SPK = {"dependiente": (WHITE, YEL, "PACO"), "cliente": (WHITE, PINK, "CLIENTA"), "ladron": (WHITE, CYAN, "LADRÓN")}
def caption_layer(t, y):
    ch = next((c for c in CHUNKS if c[0][0] - 0.02 <= t < (c[-1][1] + 0.18)), None)
    if ch is None: return None
    who = ch[0][4]; base_col, hl_col, label = SPK[who]
    lay = rgba(); d = ImageDraw.Draw(lay)
    f = font(FB, 92); words = [w[2] for w in ch]
    tw_ = lambda ff: sum(text_w(d, w, ff) + ff.size * 0.5 for w in words)
    while tw_(f) > W - 140: f = font(FB, f.size - 6)
    x = (W - tw_(f)) / 2
    draw_text(d, (W / 2 - text_w(d, label, font(FM, 28), 4) / 2, y - 46), label, font(FM, 28), hl_col + (255,), sp=4)
    for (a, b, w, h_, _, _) in ch:
        cur = a <= t < b; spoken = t >= a
        col = hl_col if (h_ or cur) else base_col
        alpha = 255 if spoken else 110
        wd = text_w(d, w, f) + f.size * 0.5
        if cur:
            sub = rgba((int(wd + 40), 160)); ds = ImageDraw.Draw(sub)
            if h_: ds.rounded_rectangle([0, 18, wd + 6, 140], 22, fill=(0, 0, 0, 150))
            draw_text(ds, (10, 20), w, f, col + (255,), stroke=10, sf=(0, 0, 0, 255))
            pop = 1.0 + 0.16 * max(0, 1 - (t - a) / 0.12)
            sub = sub.resize((int(sub.size[0] * pop), int(sub.size[1] * pop)))
            lay.alpha_composite(sub, (int(x - 10 - (pop - 1) * wd / 2), int(y - 20 - (pop - 1) * 70)))
        else:
            draw_text(d, (x, y), w, f, col + (alpha,), stroke=10, sf=(0, 0, 0, alpha))
        x += wd
    return lay

# ------------------------------------------------------------------ planos
def zoomcrop(img, z, fx, fy):
    w, h = img.size; cw, ch = w / z, h / z
    x0 = min(max(fx - cw / 2, 0), w - cw); y0 = min(max(fy - ch / 2, 0), h - ch)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
def blink_at(t, seed=0): return (int(t * 10) + seed) % 37 == 0
def chip(d, x, y, txt, col=YEL, tc=INK, size=46):
    f = font(FB, size); w = text_w(d, txt, f)
    d.rounded_rectangle([x, y, x + w + 60, y + size + 40], (size + 40) / 2, fill=col + (255,)); draw_text(d, (x + 30, y + 16), txt, f, tc + (255,))
def pin_label(img, txt, y=200):
    d = ImageDraw.Draw(img); f = font(FB, 40); w = text_w(d, txt, f)
    d.rounded_rectangle([60, y, 60 + w + 110, y + 76], 38, fill=(0, 0, 0, 170))
    d.ellipse([84, y + 16, 120, y + 52], fill=RED + (255,)); d.polygon([(88, y + 42), (116, y + 42), (102, y + 66)], fill=RED + (255,))
    d.ellipse([96, y + 28, 108, y + 40], fill=WHITE + (255,))
    draw_text(d, (136, y + 16), txt, f, WHITE + (255,))

USES = {"u_web": "web", "u_catalogo": "catalogo", "u_promo": "promo", "u_contacto": "contacto", "u_video": "video"}
def shot(name, t, a, b):
    p = min(max((t - a) / (b - a), 0.0), 1.0); u = t - a
    if name == "hook":
        tx = -450 + 2100 * min(1, u / 1.75)
        sc = shop_scene(t, paco_kw=dict(pose="mug", blink=blink_at(t), look=(-0.6, 0)),
                        thief_kw=(tx, 560, 0.95, u * 3.2, "run", False),
                        loli_kw=dict(talk_=talk("cliente", t), pose="scream", look=(-0.8, 0)), loli_pos=(260, 1180, 0.92))
        img = zoomcrop(sc, 1.0 + 0.12 * p, BW / 2, BH / 2 + 80).convert("RGBA")
        lay = rgba(); d = ImageDraw.Draw(lay)
        for i in range(14):                                   # folletos volando
            x = (tx * 0.86 - 200 - i * 90) ; y = 520 + 500 * hrand(i, 2) + 200 * math.sin(t * 4 + i)
            if x < -100: continue
            s = rgba((140, 100)); ImageDraw.Draw(s).rectangle([4, 4, 136, 96], fill=PAPERS[i % 5][1] + (255,), outline=(120, 120, 130, 255), width=3)
            s = s.rotate(t * 300 + i * 40, expand=True); lay.alpha_composite(s, (int(x), int(y)))
        img.alpha_composite(lay)
        if int(t * 6) % 2 == 0: img.alpha_composite(Image.new("RGBA", (W, H), RED + (40,)))
        return img
    if name == "paco_calm":
        sc = shop_scene(t, paco_kw=dict(pose="mug", talk_=talk("dependiente", t), blink=blink_at(t), brow=0.3), loli_kw=None)
        z = 1.0 + 1.25 * eout(u / 0.25) + 0.08 * p
        return zoomcrop(sc, z, 940, 860).convert("RGBA")
    if name in ("loli_ahora", "loli_nada"):
        sc = shop_scene(t, loli_kw=dict(talk_=talk("cliente", t), pose="point" if name == "loli_ahora" else "cross", angry=1.0, look=(0.5, 0)),
                        loli_pos=(630, 760, 1.15))
        img = zoomcrop(sc, 1.55 + 0.1 * p, 630, 1180).convert("RGBA")
        if name == "loli_nada": img = img.rotate(-3 * (1 - eout(u / 0.3)), Image.BICUBIC)
        return img
    if name == "freeze":
        sc = shop_scene(t, paco_kw=dict(pose="point", talk_=talk("dependiente", t), blink=blink_at(t), brow=0.2),
                        loli_kw=dict(talk_=0.8, pose="scream", look=(-0.8, 0)), loli_pos=(300, 1050, 1.05),
                        window_thief=(300, 560, 0.42, 0.18, "run"), tag_glow=1.2)
        img = zoomcrop(sc, 1.05, BW / 2, BH / 2 + 60).convert("RGBA")
        g = np.asarray(img.convert("RGB"), np.float32); gray = g.mean(2, keepdims=True)
        g = gray * 0.75 + g * 0.25; g = g * np.array([0.8, 0.9, 1.15]); img = to_img(g).convert("RGBA")
        # diagrama holográfico
        lay = rgba(); d = ImageDraw.Draw(lay); cx, cy = W / 2, 1000
        put_tag(lay, cx, cy + 140, 300, glow=1.5)
        q = eout((u - 0.3) / 1.2); py = cy - 760 + 520 * q
        ph = phone_img("web", 0, scan=True).resize((300, 610)); lay.alpha_composite(ph, (int(cx - 150), int(py)))
        if u > 1.5: rings(lay, cx, cy + 140, (u - 1.5) % 1.0, CYAN, 0.6)
        if u > 0.6:
            chip(d, 90, 520, "NFC = Near Field Communication", (10, 30, 50), CYAN, 40)
            chip(d, 160, 610, "comunicación de campo cercano", (10, 30, 50), WHITE, 36)
        if u > 2.0: chip(d, 280, 1380, "a pocos centímetros", YEL, INK, 44)
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img); d.rectangle([60, 200, 300, 280], fill=(0, 0, 0, 170))
        d.rectangle([90, 218, 108, 262], fill=WHITE + (255,)); d.rectangle([124, 218, 142, 262], fill=WHITE + (255,))
        draw_text(d, (160, 214), "PAUSA", font(FM, 44), WHITE + (255,))
        return scanlines(img, 0.08)
    if name in USES:
        kind = USES[name]
        img = cam(photo(name, "future"), p, 1.05, 1.18, (-1) ** len(name) * 0.4, 0.1).convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 20, 60)))
        tx, ty = 300, 1250
        put_tag(img, tx, ty, 300, glow=1.0 + (1.5 if 0.35 < u < 0.7 else 0))
        q = eout(u / 0.35)
        P = phone_img(kind, max(0, u - 0.4), scan=u < 0.4).resize((470, 957))
        P = P.rotate(-6, Image.BICUBIC, expand=True)
        px = 610 + (1 - q) * 300 - (60 * q if u < 0.5 else 0); py = 420 + (1 - q) * 500
        img.alpha_composite(P, (int(px - P.size[0] / 2 + 120), int(py)))
        rings(img, tx, ty, (u - 0.35) * 1.6, CYAN, 1.0)
        pin_label(img, PLACE[name] + ", Melilla", 210)
        return img
    if name == "paco_shrug":
        sc = shop_scene(t, paco_kw=dict(pose="shrug", talk_=talk("dependiente", t), blink=blink_at(t), brow=0.6, smile=0.5), loli_kw=None)
        return zoomcrop(sc, 1.9 + 0.08 * p, 940, 880).convert("RGBA")
    if name == "thief_out":
        img = cam(photo("thief_out", "future"), p, 1.05, 1.12, 0, 0).convert("RGBA")
        place(img, ladron(t, 0, "toss"), W / 2, 560, 0.85)
        lay = rgba()
        for i in range(26):                                  # lanza los folletos al aire
            x = W / 2 + (hrand(i, 1) - 0.5) * 900 * min(1, u / 0.8); y = 620 - 700 * math.sin(min(1, u / 1.4) * math.pi * 0.6) * hrand(i, 2) + u * 200 * hrand(i, 3)
            s = rgba((130, 92)); ImageDraw.Draw(s).rectangle([4, 4, 126, 88], fill=PAPERS[i % 5][1] + (255,), outline=(120, 120, 130, 255), width=3)
            s = s.rotate(t * 200 + i * 33, expand=True); lay.alpha_composite(s, (int(x), int(y)))
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img); chip(d, 90, 330, "Mientras tanto, el ladrón:", (0, 0, 0), WHITE, 44)
        pin_label(img, PLACE[name] + ", Melilla", 210)
        return img
    if name == "thief_back":
        sc = shop_scene(t, paco_kw=dict(pose="mug", blink=blink_at(t), smile=1.0, look=(-0.7, 0)), loli_kw=None,
                        window_thief=None)
        img = zoomcrop(sc, 1.0, BW / 2, BH / 2 + 60).convert("RGBA")
        q = eout(u / 0.4)
        place(img, ladron(t, 0, "peek", talk_=talk("ladron", t)), -80 + 330 * q, 520, 1.0, ang=-8)
        return img
    if name in ("paco_cam", "paco_cam2"):
        bg = SHOP.filter(ImageFilter.GaussianBlur(14))
        img = cam(bg, p, 1.3, 1.36).convert("RGBA")
        place(img, paco(t, talk_=talk("dependiente", t), pose="cam" if name == "paco_cam" else "point", blink=blink_at(t, 5), look=(0, 0.1), brow=0.15, smile=0.3),
              W / 2 if name == "paco_cam" else W / 2 - 120, 300, 1.55)
        if name == "paco_cam2":
            put_tag(img, 900, 1250, 260, glow=1.2); rings(img, 900, 1250, (u * 1.2) % 1.0)
        if name == "paco_cam" and t > 27.55:                 # «30 €» gigante
            q = back((t - 27.55) / 0.3); lay = rgba(); d = ImageDraw.Draw(lay)
            cx, cy, R = 800, 520, 230
            pts = [(cx + (R if k % 2 == 0 else R * 0.78) * math.cos(k * math.pi / 12 + t), cy + (R if k % 2 == 0 else R * 0.78) * math.sin(k * math.pi / 12 + t)) for k in range(24)]
            d.polygon(pts, fill=YEL + (255,), outline=INK + (255,), width=8)
            ctext(d, cy - 85, PRICE, font(FB, 130), INK + (255,), cx=cx)
            s = max(0.05, q); lay = lay.resize((int(W * s), int(H * s)))
            img.alpha_composite(lay, (int(cx - cx * s), int(cy - cy * s)))
        return img
    if name in ("m_reconquista", "m_asamblea"):
        img = cam(photo(name, "warm"), p, 1.06, 1.18, 0.3, 0.1).convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 50)))
        d = ImageDraw.Draw(img)
        if name == "m_reconquista": chip(d, 150, 600, "✓ COMERCIOS".replace("✓ ", ""), YEL, INK, 72)
        else:
            chip(d, 150, 600, "COMERCIOS", (255, 255, 255), INK, 60); chip(d, 150, 730, "PROFESIONALES", YEL, INK, 72)
        pin_label(img, PLACE[name].split(" · ")[0] + ", Melilla", 210)
        return img
    if name == "endcard":
        return endcard(t, u)
    raise KeyError(name)

def endcard(t, u):
    bg = photo("endcard", "night").filter(ImageFilter.GaussianBlur(10))
    img = cam(bg, min(1, u / 6), 1.1, 1.2).convert("RGBA")
    img.alpha_composite(Image.new("RGBA", (W, H), (5, 10, 30, 150)))
    particles(img, t, 50, CYAN, 7, True, 4)
    q = eout(u / 0.3)
    put_tag(img, W / 2, 400, 330, glow=1.4)
    rings(img, W / 2, 400, (u * 0.8) % 1.0, CYAN, 1.0)
    lay = rgba(); d = ImageDraw.Draw(lay)
    ctext(d, 640, "MODERNIZA TU NEGOCIO", fit_font(d, "MODERNIZA TU NEGOCIO", FB, 90, 860), WHITE + (255,), stroke=6, sf=(0, 0, 0, 255))
    ctext(d, 750, "CON NFC", font(FB, 120), CYAN + (255,), stroke=6, sf=(0, 0, 0, 255))
    d.rounded_rectangle([110, 930, W - 110, 1160], 50, fill=YEL + (255,), outline=INK + (255,), width=6)
    ctext(d, 950, "ETIQUETAS NFC:", font(FB, 64), INK + (255,))
    ctext(d, 1030, "SOLO " + PRICE, font(FB, 110), INK + (255,))
    d.rounded_rectangle([110, 1210, W - 110, 1420], 50, fill=(10, 14, 28, 245), outline=WHITE + (255,), width=5)
    ctext(d, 1228, "CONTACTA:", font(FB, 56), (180, 200, 230, 255))
    ctext(d, 1300, PHONE, fit_font(d, PHONE, FB, 96, 800), WHITE + (255,))
    s = 0.85 + 0.15 * q
    if s < 1: lay = lay.resize((int(W * s), int(H * s))); img.alpha_composite(lay, (int(W * (1 - s) / 2), int(H * (1 - s) / 2)))
    else: img.alpha_composite(lay)
    return img

# ------------------------------------------------------------------ fotograma
CAP_Y = {"hook": 1300, "paco_calm": 1330, "loli_ahora": 1330, "freeze": 1640, "paco_shrug": 1330, "thief_out": 1500,
         "thief_back": 1330, "paco_cam": 1420, "paco_cam2": 1420, "loli_nada": 1330}
CUTS = [s[0] for s in SHOTS[1:]]
def frame(t, fi):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t)
    a, b, name = SHOTS[i]
    img = shot(name, t, a, b)
    sh = 0.0
    for h in HITS:
        u = t - h
        if 0 <= u < 0.3: sh = max(sh, 1 - u / 0.3)
    if name == "hook": sh = max(sh, 0.5)
    if sh > 0:
        dx = (hrand(fi, 1) - 0.5) * 44 * sh; dy = (hrand(fi, 2) - 0.5) * 44 * sh
        img = img.transform((W, H), Image.AFFINE, (1 / 1.03, 0, -dx + W * 0.015, 0, 1 / 1.03, -dy + H * 0.015), Image.BILINEAR)
    if name != "endcard":
        cl = caption_layer(t, CAP_Y.get(name, 1580))
        if cl is not None: img.alpha_composite(cl)
    arr = np.asarray(img.convert("RGB"), np.float32) * (0.35 + 0.65 * B.VIG)
    for h in HITS:
        u = t - h
        if 0 <= u < 0.12 and name != "endcard": arr += (1 - u / 0.12) * 110
    arr += np.repeat(np.repeat(B.GRAIN[fi % 4], 2, 0), 2, 1)[..., None] * 0.7
    if t > TOTAL - 0.25: arr *= max(0, (TOTAL - t) / 0.25)
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
    elif sys.argv[1] == "srt":
        blocks = []
        for i, c in enumerate(CHUNKS):
            end = c[-1][1] + 0.15
            if i + 1 < len(CHUNKS): end = min(end, CHUNKS[i + 1][0][0] - 0.01)
            blocks.append((c[0][0], end, " ".join(w[2] for w in c)))
        from script_data import write_srt; write_srt(os.path.join(HERE, "subtitulos.srt"), blocks)
    else:
        k, n = int(sys.argv[2]), int(sys.argv[3]); NF = int(round(TOTAL * FPS))
        render_range(NF * k // n, NF * (k + 1) // n, os.path.join(HERE, f"part_{k:02}.mp4")); print("parte", k, flush=True)
