# Personajes ilustrados de la telenovela (dibujo vectorial con PIL, escalable para primerísimos planos)
import math
from PIL import Image, ImageDraw

CHARS = {
    "rafa": dict(skin=(196, 142, 106), skin2=(170, 118, 86), hair=(24, 18, 16), hairstyle="tupe", mustache=True, beard="sombra",
                 shirt=(240, 238, 232), vest=(30, 30, 36), brow=(22, 16, 14), iris=(92, 58, 30), lips=(150, 80, 70)),
    "sofia": dict(skin=(222, 172, 136), skin2=(196, 146, 112), hair=(46, 24, 16), hairstyle="melena", mustache=False, beard=None,
                  shirt=(170, 20, 40), vest=None, brow=(40, 22, 14), iris=(60, 110, 60), lips=(185, 20, 45), earrings=True, lunar=True),
    "carmen": dict(skin=(228, 186, 156), skin2=(205, 160, 130), hair=(205, 205, 210), hairstyle="mono", mustache=False, beard=None,
                   shirt=(110, 60, 130), vest=None, brow=(160, 160, 165), iris=(80, 60, 40), lips=(170, 90, 100), glasses=True, pearls=True),
    "nacho": dict(skin=(186, 128, 92), skin2=(160, 106, 76), hair=(58, 36, 22), hairstyle="rizos", mustache=False, beard="barba",
                  shirt=(40, 90, 70), vest=None, brow=(50, 30, 18), iris=(70, 45, 25), lips=(140, 75, 65), apron=(235, 230, 215)),
}

def _e(d, cx, cy, rx, ry, **k): d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], **k)

def draw_char(img, cx, cy, u, who, expr="neutral", mouth=0.0, look=(0.0, 0.0), tears=0.0, t=0.0, body=True, blink=False):
    """Dibuja al personaje con el centro de la cara en (cx, cy); u = medio ancho de la cabeza en píxeles.
    expr: neutral | preocupado | triste | shock | chulesca | devocion | grito | camara
    mouth: 0..1 apertura (sincronía labial). look: dirección de la mirada (-1..1, -1..1)."""
    c = CHARS[who]
    d = ImageDraw.Draw(img, "RGBA")
    S = lambda v: v * u
    def P(x, y): return (cx + S(x), cy + S(y))
    def E(x, y, rx, ry, **k): _e(d, cx + S(x), cy + S(y), S(rx), S(ry), **k)
    # ---- pelo de atrás
    if c["hairstyle"] == "melena":
        pts = [P(-1.25, -0.6), P(-1.45, 0.8), P(-1.35, 2.3), P(-0.6, 2.6), P(0.6, 2.6), P(1.35, 2.3), P(1.45, 0.8), P(1.25, -0.6), P(0, -1.5)]
        d.polygon(pts, fill=c["hair"])
        for k in range(-3, 4):  # ondas
            d.arc([cx + S(k * 0.4 - 0.4), cy + S(1.5), cx + S(k * 0.4 + 0.4), cy + S(2.4)], 200, 340, fill=(80, 45, 30), width=max(2, int(S(0.05))))
    if c["hairstyle"] == "mono":
        E(0, -1.35, 0.55, 0.45, fill=c["hair"])
    # ---- cuerpo
    if body:
        d.rounded_rectangle([cx - S(0.38), cy + S(0.8), cx + S(0.38), cy + S(1.6)], S(0.1), fill=c["skin2"])
        d.rounded_rectangle([cx - S(1.9), cy + S(1.45), cx + S(1.9), cy + S(5.5)], S(0.9), fill=c["shirt"])
        if c.get("vest"):
            d.polygon([P(-1.9, 1.9), P(-0.35, 1.5), P(-0.15, 5.5), P(-1.9, 5.5)], fill=c["vest"])
            d.polygon([P(1.9, 1.9), P(0.35, 1.5), P(0.15, 5.5), P(1.9, 5.5)], fill=c["vest"])
            d.polygon([P(-0.38, 1.45), P(0, 2.0), P(0.38, 1.45)], fill=c["skin2"])
            for k in range(3): E(-0.32, 2.6 + k * 0.7, 0.07, 0.07, fill=(200, 170, 80))
        if who == "sofia":
            d.polygon([P(-0.6, 1.5), P(0, 2.3), P(0.6, 1.5)], fill=c["skin2"])
        if c.get("apron"):
            d.rounded_rectangle([cx - S(1.1), cy + S(2.4), cx + S(1.1), cy + S(5.5)], S(0.2), fill=c["apron"])
            d.line([P(-1.1, 2.4), P(-0.5, 1.5)], fill=c["apron"], width=int(S(0.12)))
            d.line([P(1.1, 2.4), P(0.5, 1.5)], fill=c["apron"], width=int(S(0.12)))
        if c.get("pearls"):
            for k in range(13):
                a = math.pi * (0.15 + 0.7 * k / 12)
                E(1.0 * math.cos(a), 1.45 + 0.55 * math.sin(a), 0.07, 0.07, fill=(245, 240, 230))
    # ---- orejas y cabeza
    E(-1.0, 0.05, 0.18, 0.26, fill=c["skin2"]); E(1.0, 0.05, 0.18, 0.26, fill=c["skin2"])
    d.ellipse([cx - S(1.0), cy - S(1.25), cx + S(1.0), cy + S(1.15)], fill=c["skin"])
    if c.get("earrings"):
        for s in (-1, 1):
            E(s * 1.02, 0.42, 0.09, 0.09, fill=(235, 190, 60)); E(s * 1.02, 0.65, 0.13, 0.18, outline=(235, 190, 60), width=max(2, int(S(0.05))))
    # ---- sombra de barba
    if c["beard"] == "sombra":
        d.chord([cx - S(0.95), cy - S(0.2), cx + S(0.95), cy + S(1.15)], 20, 160, fill=(60, 50, 45, 70))
    if c["beard"] == "barba":
        d.chord([cx - S(1.02), cy - S(0.5), cx + S(1.02), cy + S(1.3)], 5, 175, fill=c["hair"])
    # ---- pelo delantero
    hc = c["hair"]
    if c["hairstyle"] == "tupe":
        d.polygon([P(-1.02, -0.2), P(-1.05, -0.9), P(-0.7, -1.35), P(-0.1, -1.62), P(0.6, -1.55), P(1.05, -1.1), P(1.02, -0.2),
                   P(0.85, -0.75), P(0.2, -0.95), P(-0.5, -0.85), P(-0.85, -0.6)], fill=hc)
        d.arc([cx - S(0.6), cy - S(1.6), cx + S(0.7), cy - S(0.9)], 200, 330, fill=(90, 80, 75), width=max(2, int(S(0.04))))
    elif c["hairstyle"] == "melena":
        d.polygon([P(-1.08, 0.3), P(-1.05, -0.8), P(-0.5, -1.35), P(0.4, -1.38), P(1.05, -0.85), P(1.08, 0.3), P(0.85, -0.6), P(0.2, -1.0), P(-0.5, -0.8), P(-0.95, -0.3)], fill=hc)
    elif c["hairstyle"] == "mono":
        d.chord([cx - S(1.02), cy - S(1.3), cx + S(1.02), cy + S(0.3)], 180, 360, fill=hc)
        for k in range(-3, 4): d.arc([cx + S(k * 0.28 - 0.3), cy - S(1.2), cx + S(k * 0.28 + 0.3), cy - S(0.6)], 180, 300, fill=(170, 170, 178), width=max(2, int(S(0.04))))
    elif c["hairstyle"] == "rizos":
        for k in range(14):
            a = math.pi * (1.0 + k / 13)
            E(0.95 * math.cos(a), -0.45 + 0.85 * math.sin(a), 0.28, 0.26, fill=hc)
    # ---- ojos
    eye_y = -0.12
    wide = {"shock": 1.55, "grito": 0.25, "devocion": 1.2, "chulesca": 0.62, "triste": 0.8, "camara": 0.9}.get(expr, 1.0)
    if blink: wide = 0.08
    lx, ly = look
    for s in (-1, 1):
        ex = s * 0.4
        rx, ry = 0.22, 0.14 * wide
        E(ex, eye_y, rx, max(0.012, ry), fill=(250, 248, 244))
        if ry > 0.05:
            ir = 0.105 if expr != "shock" else 0.08
            ix, iy = ex + lx * 0.09, eye_y + ly * 0.05
            E(ix, iy, ir, min(ir, ry * 1.05), fill=c["iris"])
            E(ix, iy, ir * 0.5, min(ir * 0.5, ry * 0.6), fill=(10, 8, 8))
            E(ix - 0.04, iy - 0.04, ir * 0.3, ir * 0.3, fill=(255, 255, 255))
            if expr == "devocion":  # brillos de admiración
                for k in range(4):
                    a = k * math.pi / 2 + t * 3
                    d.line([P(ix + 0.03 * math.cos(a), iy + 0.03 * math.sin(a)), P(ix + 0.08 * math.cos(a), iy + 0.08 * math.sin(a))], fill=(255, 255, 255), width=max(1, int(S(0.015))))
        # pestañas / párpado
        lid = c["brow"] if who in ("sofia",) else (60, 40, 35)
        d.arc([cx + S(ex - rx), cy + S(eye_y - max(0.012, ry)), cx + S(ex + rx), cy + S(eye_y + max(0.012, ry))], 190, 350, fill=lid, width=max(2, int(S(0.035 if who == "sofia" else 0.025))))
        if who == "sofia":
            d.line([P(ex + s * rx, eye_y - ry * 0.4), P(ex + s * (rx + 0.08), eye_y - ry - 0.04)], fill=lid, width=max(2, int(S(0.03))))
        if expr == "chulesca" or expr == "triste":
            d.chord([cx + S(ex - rx - 0.01), cy + S(eye_y - ry - 0.02), cx + S(ex + rx + 0.01), cy + S(eye_y + ry + 0.02)], 180, 360, fill=c["skin"])
    if c.get("glasses"):
        for s in (-1, 1):
            E(s * 0.4, eye_y, 0.3, 0.24, outline=(120, 90, 40), width=max(2, int(S(0.04))))
        d.line([P(-0.1, eye_y), P(0.1, eye_y)], fill=(120, 90, 40), width=max(2, int(S(0.04))))
    # ---- cejas
    bw = max(2, int(S(0.09 if who in ("rafa", "nacho") else 0.055)))
    for s in (-1, 1):
        inner, outer = (s * 0.15, s * 0.65)
        if expr in ("preocupado", "triste", "grito", "camara"):
            yi, yo = -0.52, -0.36
        elif expr == "shock":
            yi, yo = -0.62, -0.55
        elif expr == "chulesca":
            yi, yo = (-0.40, -0.40) if s < 0 else (-0.58, -0.66)
        elif expr == "devocion":
            yi, yo = -0.50, -0.44
        else:
            yi, yo = -0.40, -0.42
        d.line([P(inner, yi), P((inner + outer) / 2, min(yi, yo) - 0.06), P(outer, yo)], fill=c["brow"], width=bw, joint="curve")
    # ---- nariz
    d.line([P(0.02, -0.05), P(0.1, 0.3), P(-0.04, 0.36)], fill=c["skin2"], width=max(2, int(S(0.045))), joint="curve")
    if c.get("lunar"): E(0.42, 0.52, 0.035, 0.035, fill=(60, 30, 25))
    # ---- boca
    my = 0.62
    m = max(0.0, min(1.2, mouth))
    if expr == "grito":
        E(0, my + 0.05, 0.32, 0.36, fill=(60, 15, 20)); E(0, my + 0.28, 0.18, 0.1, fill=(200, 80, 90))
        d.rectangle([cx - S(0.2), cy + S(my - 0.3), cx + S(0.2), cy + S(my - 0.22)], fill=(250, 250, 245))
    elif expr == "shock" and m < 0.3:
        E(0, my + 0.04, 0.13, 0.17, fill=(70, 20, 25))
    elif m > 0.08:
        h = 0.04 + 0.18 * m
        E(0, my, 0.2, h, fill=(80, 22, 28)); E(0, my - h * 0.55, 0.16, h * 0.3, fill=(245, 245, 240))
        d.ellipse([cx - S(0.21), cy + S(my - h - 0.01), cx + S(0.21), cy + S(my + h + 0.01)], outline=c["lips"], width=max(2, int(S(0.04))))
    elif expr in ("chulesca",):
        d.line([P(-0.2, my + 0.04), P(0.05, my + 0.02), P(0.24, my - 0.08)], fill=c["lips"], width=max(2, int(S(0.06))), joint="curve")
    elif expr in ("preocupado", "triste", "camara"):
        d.arc([cx - S(0.2), cy + S(my), cx + S(0.2), cy + S(my + 0.25)], 200, 340, fill=c["lips"], width=max(2, int(S(0.06))))
    elif expr == "devocion":
        E(0, my, 0.08, 0.1, fill=(80, 22, 28))
    else:
        d.line([P(-0.18, my), P(0.18, my)], fill=c["lips"], width=max(2, int(S(0.06))))
    if c["mustache"]:
        d.polygon([P(-0.42, my - 0.08), P(-0.2, my - 0.25), P(0, my - 0.2), P(0.2, my - 0.25), P(0.42, my - 0.08), P(0.3, my - 0.05), P(0, my - 0.12), P(-0.3, my - 0.05)], fill=c["hair"])
    # ---- lágrimas
    if tears > 0:
        for s in (-1, 1):
            if s > 0 and tears < 0.5: continue
            L = min(1.0, tears) * 1.1
            x0 = s * 0.42
            d.line([P(x0, eye_y + 0.12), P(x0 + s * 0.04, eye_y + 0.12 + L * 0.6), P(x0, eye_y + 0.12 + L)], fill=(170, 220, 255, 220), width=max(2, int(S(0.06))), joint="curve")
            E(x0, eye_y + 0.15 + L, 0.06, 0.08, fill=(200, 235, 255, 240))
    return img
