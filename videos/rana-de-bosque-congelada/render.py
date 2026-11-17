"""Monta el vídeo 1080x1920 a 30 fps: planos, transiciones, gráficos científicos y subtítulos.
Uso: python3 render.py video            -> video_only.mp4 (en paralelo)
     python3 render.py frames t1 t2 ...  -> fotogramas de prueba en preview/
"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fx import *
from timeline import SENTENCES, TOTAL, word_time, caption_chunks, is_highlight

FPS = 30
S = SENTENCES
def st(i, k=0): return word_time(i, k) - 0.12 if (i or k) else 0.0
def se(i): return S[i]["end"]

# ======================================================================== planos
# Cada plano: función (lt, d) -> Image (lt = tiempo local, d = duración). 'cap' = posición del subtítulo.

def p_hook_eye(lt, d):
    im = cam(load("close_frozen"), 1.55 + 0.35 * ease(lt / d), 0.5, 0.42)
    im = frost_overlay(im, 0.25, sparkle_t=lt)
    cr = cracks(ease_out(lt / 0.9), seed=5, center=(0.5, 0.42)) if lt < 1.6 else cracks(1, seed=5, center=(0.5, 0.42))
    im = apply_layer(im, cr, k=0.8 * (1 - clamp01((lt - 1.2) / 1.5)))
    return grade(im, -0.4, 0.8)

def p_hook_side(lt, d):
    im = cam(load("frozen_snow_wide"), 1.05 + 0.18 * lt / d, 0.5 - 0.04 * lt / d, 0.45)
    return grade(frost_overlay(im, 0.2, sparkle_t=lt), -0.35, 0.8)

def p_flatline(lt, d):
    bg = grade(cam(load("frozen_snow_wide"), 1.1 + 0.05 * lt / d), -0.6, 0.5, 0.8)
    return ecg(bg, lt + 0.6, beats=[0.0, 0.85], y=1000, col=GREEN, label="LATIDO: 0")

def p_revive(lt, d):
    p = ease(clamp01((lt - 0.15) / (d * 0.75)))
    z = 1.5 - 0.35 * ease(lt / d)
    a = cam(load("close_frozen"), z, 0.5, 0.42); b = cam(load("close_alive"), z, 0.5, 0.42)
    im = freeze_mix(grade(b, 0.35, 1.1), grade(a, -0.4, 0.8), 1 - p, seed=4, origin=(0.5, 0.45), warm=True)
    return glow_bloom(im, 0.3 * p)

def p_title(lt, d):
    im = grade(cam(load("hero_alive"), 1.0 + 0.12 * ease(lt / d), 0.5, 0.5), 0.15, 1.05)
    a = ease_out(lt / 0.5)
    im = over(im, text_layer(["RANA DE BOSQUE"], 104, y=250 - 30 * (1 - a), col=YELLOW, alpha=a))
    return over(im, text_layer(["Lithobates sylvaticus"], 54, y=375, kind="semi", stroke=4, alpha=ease_out((lt - 0.3) / 0.5)))

def p_map(lt, d):
    t_ap = word_time(4, "Apalaches") - S[4]["start"]; t_ak = word_time(4, "Alaska") - S[4]["start"]
    t_ar = word_time(4, "Círculo") - S[4]["start"]
    pr = 0.15 + 0.85 * ease((lt - t_ap + 0.3) / max(0.5, t_ak - t_ap + 0.4)) if lt > t_ap - 0.3 else 0.15 * ease(lt / max(0.3, t_ap - 0.3))
    im = na_map(lt, pr, clamp01((lt - t_ar + 0.2) / 1.0))
    im = cam(im, 1.0 + 0.06 * lt / d)
    labs = []
    if lt > t_ap - 0.1: labs.append(("APALACHES", proj(-80, 36.5), ease_out((lt - t_ap + 0.1) / 0.4), (210, 255, 225)))
    if lt > t_ak - 0.1: labs.append(("ALASKA", proj(-152, 64), ease_out((lt - t_ak + 0.1) / 0.4), (210, 255, 225)))
    if lt > t_ar - 0.1: labs.append(("CÍRCULO POLAR ÁRTICO", proj(-118, 71.5), ease_out((lt - t_ar + 0.1) / 0.4), ICE))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    for s, (x, y), a, c in labs:
        f = font(46, "black"); tw = dd.textlength(s, font=f)
        x = min(max(x - tw / 2, 20), W - tw - 20)
        dd.text((x, y - 25), s, font=f, fill=c + (int(255 * a),), stroke_width=5, stroke_fill=(0, 0, 0, int(255 * a)))
    im = over(im, lay)
    im = over(im, text_layer(["DISTRIBUCIÓN APROXIMADA"], 38, y=1640, col=(170, 210, 190), kind="bold", stroke=3, alpha=ease_out(lt / 0.6)))
    return im

def p_hide(lt, d):
    im = grade(cam(load("hide_leaves"), 1.05 + 0.12 * lt / d, 0.5, 0.55), -0.25, 0.85)
    return snow(im, lt, 0.8)

def p_frost_leaves(lt, d):
    a = grade(cam(load("frost_leaves"), 1.25 - 0.15 * ease(lt / d)), -0.2)
    base = grade(a, 0.1, 0.9, 0.9)
    im = freeze_mix(base, frost_overlay(a, 0.6), ease(lt / (d * 0.9)), seed=6, origin=(0.5, 1.2))
    return snow(im, lt + 3, 0.4)

def p_freeze(lt, d):
    z = 1.0 + 0.15 * ease(lt / d)
    a = grade(cam(load("hero_alive"), z), 0.05, 0.95); b = grade(cam(load("hero_frozen"), z), -0.35, 0.75)
    im = freeze_mix(a, b, ease(clamp01((lt - 0.2) / (d * 0.85))), seed=2, origin=(0.5, 1.1))
    return im

def p_tissue(lt, d):
    t1 = word_time(7, "entre") - S[7]["start"]
    im = cam(tissue(lt, ease(clamp01(lt / (d + 0.3)))), 1.0 + 0.05 * lt / d)
    im = over(im, text_layer(["PIEL"], 58, y=410, col=(255, 230, 200), stroke=5, alpha=ease_out(lt / 0.4)))
    im = over(im, text_layer(["HIELO BAJO LA PIEL"], 56, y=640, col=ICE, stroke=5, alpha=ease_out((lt - 0.5) / 0.4)))
    im = over(im, text_layer(["MÚSCULO"], 58, y=1060, col=(255, 190, 190), stroke=5, alpha=ease_out((lt - t1 + 0.1) / 0.4)))
    return over(im, text_layer(["RECREACIÓN CIENTÍFICA"], 34, y=1700, col=(200, 200, 210), kind="bold", stroke=3))

def p_65(lt, d):
    t65 = word_time(8, "sesenta") - S[8]["start"]
    im = grade(cam(load("hero_frozen"), 1.2 + 0.1 * lt / d, 0.5, 0.55), -0.45, 0.6, 0.6)
    im = frost_overlay(im, 0.35, sparkle_t=lt)
    v = int(round(65 * ease_out(clamp01((lt - t65 + 0.2) / 1.2))))
    # medidor de agua corporal
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    x0, x1, y0, y1 = 140, W - 140, 1040, 1100
    dd.rounded_rectangle([x0, y0, x1, y1], 30, outline=(255, 255, 255, 230), width=5, fill=(10, 30, 60, 140))
    fx_ = x0 + (x1 - x0) * v / 100
    if v > 0: dd.rounded_rectangle([x0 + 6, y0 + 6, max(x0 + 40, fx_ - 6), y1 - 6], 24, fill=ICE + (255,))
    if lt > t65 - 0.4: im = over(im, lay)
    im = glow_text(im, f"{v} %", 230, 700, ICE, alpha=ease_out((lt - t65 + 0.4) / 0.4))
    return over(im, text_layer(["DEL AGUA DE SU CUERPO", "SE CONVIERTE EN HIELO"], 50, y=1140, col=(235, 245, 255), stroke=5, alpha=ease_out((lt - t65) / 0.5)))

def p_heart_stop(lt, d):
    bg = grade(cam(load("hero_frozen"), 1.3), -0.6, 0.4, 0.5)
    beats = [0.0, 0.75]
    b = sum(math.exp(-((lt - x) / 0.08) ** 2) for x in beats)
    im = heart(bg, b, frozen=ease(clamp01((lt - 0.8) / 0.8)), cy=760, scale=0.95)
    return ecg(im, lt + 0.9, beats=[x + 0.9 for x in beats], y=1300, amp=170, col=RED, label=None)

def p_no_breath(lt, d):
    im = grade(cam(load("close_frozen"), 1.3 + 0.1 * lt / d, 0.45, 0.5), -0.4, 0.7, 0.85)
    im = frost_overlay(im, 0.3, sparkle_t=lt)
    return over(im, text_layer([[("RESPIRACIÓN:", (230, 240, 255)), ("0", RED)]], 64, y=260, stroke=6, alpha=ease_out(lt / 0.3)))

def p_dead(lt, d):
    im = grade(cam(load("frozen_snow_wide"), 1.25 - 0.2 * ease(lt / d)), -0.5, 0.35, 0.8)
    return snow(im, lt, 0.35, seed=8, wind=10)

def p_not_dead(lt, d):
    im = cam(load("close_frozen"), 2.0 + 0.4 * ease_out(lt / d), 0.5, 0.42)
    im = grade(im, -0.3, 0.8)
    pulse = math.exp(-((lt - 0.55) / 0.18) ** 2)
    a = arr(im); yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - W / 2) / 420) ** 2 + ((yy - 900) / 420) ** 2)) * (0.3 + pulse)
    return img(a + g[..., None] * np.array(GOLD, np.float32) * 0.8)

def xray(lt, d, base="hero_frozen"):
    im = cam(load(base), 1.05, 0.5, 0.55)
    g = arr(im).mean(2); e = arr(im.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1)))
    a = np.zeros((H, W, 3), np.float32) + np.array((4, 14, 30), np.float32)
    a += (g / 255)[..., None] ** 1.5 * np.array((40, 110, 170), np.float32) + (e / 255 * 3)[..., None] * np.array((90, 200, 255), np.float32)
    return a

LIVER = (560, 1150)
def p_glucose(lt, d):
    t200 = word_time(13, "doscientos") - S[13]["start"]
    a = xray(lt, d)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lv = np.exp(-(((xx - LIVER[0]) / 150) ** 2 + ((yy - LIVER[1]) / 95) ** 2))
    pul = 0.7 + 0.3 * math.sin(lt * 6)
    a = a * (1 - np.clip(lv * 1.2, 0, 1)[..., None] * 0.5) + lv[..., None] * np.array((255, 170, 40), np.float32) * pul
    im = img(a)
    # moléculas de glucosa saliendo del hígado hacia todo el cuerpo
    r = np.random.default_rng(3); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    n = int(160 * ease(lt / 2.5))
    for k in range(n):
        ang = r.uniform(0, 6.28); sp = r.uniform(120, 420); born = r.uniform(0, 2.5)
        age = (lt - born) % 3.0
        x = LIVER[0] + math.cos(ang) * sp * age + 30 * math.sin(age * 3 + k); y = LIVER[1] + math.sin(ang) * sp * age * 1.2
        s = 11
        dd.polygon([(x + s * math.cos(j * math.pi / 3), y + s * math.sin(j * math.pi / 3)) for j in range(6)], outline=GOLD + (255,), fill=(255, 200, 70, 170))
    im = Image.alpha_composite(Image.alpha_composite(im.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(6))), lay).convert("RGB")
    im = over(im, text_layer(["HÍGADO"], 56, y=LIVER[1] + 120, col=GOLD, stroke=5, alpha=ease_out(lt / 0.4)))
    im = over(im, text_layer(["GLUCOSA"], 76, y=250, col=GOLD, stroke=6, alpha=ease_out((lt - 0.8) / 0.4)))
    if lt > t200 - 0.3:
        v = int(round(200 * ease_out(clamp01((lt - t200 + 0.3) / 0.9))))
        im = glow_text(im, f"×{v}", 210, 380, GOLD, alpha=ease_out((lt - t200 + 0.3) / 0.3))
        im = over(im, text_layer(["MÁS AZÚCAR EN LA SANGRE"], 40, y=610, col=(255, 235, 190), kind="bold", stroke=4, alpha=ease_out((lt - t200) / 0.4)))
    return over(im, text_layer(["RECREACIÓN CIENTÍFICA"], 34, y=1700, col=(200, 200, 210), kind="bold", stroke=3))

def p_cells(lt, d):
    t_out = word_time(14, "fuera") - S[14]["start"]; t_in = word_time(14, "dentro") - S[14]["start"]
    im = cells(lt, ice=ease(clamp01((lt - t_out + 1.2) / 2.4)), glucose=1.0)
    im = cam(im, 1.12 - 0.08 * lt / d)
    if lt > t_out - 0.2:
        im = over(im, text_layer([[("HIELO", ICE), ("FUERA", (255, 255, 255))]], 74, y=260, stroke=7, alpha=ease_out((lt - t_out + 0.2) / 0.3)))
    if lt > t_in - 0.2:
        im = over(im, text_layer([[("DENTRO:", (255, 255, 255)), ("SIN HIELO", (255, 190, 205))]], 60, y=370, stroke=6, alpha=ease_out((lt - t_in + 0.2) / 0.3)))
    return over(im, text_layer(["RECREACIÓN CIENTÍFICA"], 34, y=1740, col=(200, 200, 210), kind="bold", stroke=3))

def p_shrink(lt, d):
    sv = word_time(15, "sobreviven") - S[15]["start"]
    im = cells(lt + 5, ice=1.0, shrink=0.45 * ease(lt / (sv + 0.2)), glucose=1.0)
    im = cam(im, 1.04 + 0.04 * lt / d)
    if lt > sv - 0.1:
        a = ease_out((lt - sv + 0.1) / 0.3)
        im = glow_text(im, "✓", 260, 760, GREEN, alpha=a) if False else over(im, text_layer(["SOBREVIVEN"], 110, y=840, col=GREEN, stroke=9, alpha=a))
    return im

def p_alaska(lt, d):
    t_d = word_time(16, "doscientos") - S[16]["start"]; t_t = word_time(16, "dieciocho") - S[16]["start"]
    im = grade(cam(load("alaska_night"), 1.0 + 0.12 * lt / d, 0.5, 0.45), -0.1, 1.05)
    im = snow(im, lt, 0.5, seed=12, wind=60)
    im = over(im, text_layer(["ALASKA"], 70, y=230, col=(220, 240, 255), stroke=6, alpha=ease_out(lt / 0.4)))
    if lt > t_d - 0.4:
        v = int(round(193 * ease_out(clamp01((lt - t_d + 0.4) / 1.4))))
        im = glow_text(im, f"{v} DÍAS", 150, 600, (255, 255, 255), alpha=ease_out((lt - t_d + 0.4) / 0.3))
        im = over(im, text_layer(["CONGELADA SEGUIDOS"], 46, y=790, col=(220, 235, 255), kind="bold", stroke=4, alpha=ease_out((lt - t_d) / 0.4)))
    if lt > t_t - 0.2:
        im = glow_text(im, "−18 °C", 170, 960, ICE, alpha=ease_out((lt - t_t + 0.2) / 0.3))
    return im

def p_spring(lt, d):
    im = grade(cam(load("spring_sunrise"), 1.15 - 0.1 * ease(lt / d), 0.5, 0.5), 0.25, 1.05, 1.0 + 0.08 * ease(lt / d))
    im = light_rays(im, lt, k=0.3 + 0.2 * ease(lt / d))
    return glow_bloom(im, 0.25)

def p_thaw(lt, d):
    z = 1.15 - 0.1 * ease(lt / d)
    a = grade(cam(load("hero_frozen"), z), -0.35, 0.75); b = grade(cam(load("hero_alive"), z), 0.25, 1.05)
    p = ease(clamp01((lt - 0.1) / (d * 0.9)))
    im = freeze_mix(b, a, 1 - p, seed=3, origin=(0.5, 1.1), warm=True)
    im = drips(im, lt)
    return light_rays(im, lt, k=0.25 * p)

def p_heart_back(lt, d):
    t_l = word_time(18, "latir") - S[18]["start"]
    beats = [t_l - 0.15 + k * 0.8 for k in range(6)]
    bg = grade(cam(load("hero_alive"), 1.3), 0.3, 0.8, 0.6)
    b = sum(math.exp(-((lt - x) / 0.07) ** 2) for x in beats if lt > x - 0.3)
    im = heart(bg, b, frozen=1 - ease(clamp01((lt - t_l + 0.6) / 0.7)), cy=760, scale=0.95, dim=0.55)
    return ecg(im, lt + 0.9, beats=[x + 0.9 for x in beats], y=1300, amp=190, col=GREEN)

def p_breathe(lt, d):
    im = grade(cam(load("hero_wide"), 1.05 + 0.12 * lt / d + 0.006 * math.sin(lt * 4), 0.5, 0.52), 0.25, 1.05)
    return light_rays(im, lt, k=0.2)

def p_leap(lt, d):
    p = ease_out(lt / d)
    im = cam(load("pond"), 1.0 + 0.35 * p, 0.5, 0.42 - 0.04 * p)   # empujón de cámara hacia la rana en la charca
    sh = 10 * math.exp(-lt * 6); im = im.transform(im.size, Image.AFFINE, (1, 0, sh * math.sin(lt * 70), 0, 1, sh * math.cos(lt * 55)))
    im = grade(im, 0.2, 1.1)
    if lt < 0.35:  # desenfoque de movimiento al arrancar
        k = int(30 * (1 - lt / 0.35)) + 1
        im = im.filter(ImageFilter.BoxBlur(k // 3)) if k > 3 else im
    return glow_bloom(im, 0.2)

def p_pond(lt, d):
    im = grade(cam(load("spring_sunrise"), 1.25 - 0.15 * ease(lt / d), 0.5, 0.55), 0.25, 1.08)
    return light_rays(im, lt, k=0.25)

def p_split(lt, d):
    z = 1.08 + 0.04 * lt / d
    a = grade(cam(load("hero_frozen"), z), -0.4, 0.75); b = grade(cam(load("hero_alive"), z), 0.25, 1.05)
    xs = W * (1 - ease(clamp01(lt / (d * 0.8))))
    m = (np.arange(W)[None, :] >= xs).astype(np.float32)
    out = arr(a) * (1 - m[..., None]) + arr(b) * m[..., None]
    out[:, max(0, int(xs) - 3):int(xs) + 3] = 255
    im = img(out)
    im = over(im, text_layer(["INVIERNO"], 60, y=250, col=ICE, stroke=6, align_x=60, alpha=clamp01((xs - 380) / 200)))
    return over(im, text_layer(["PRIMAVERA"], 60, y=250, col=GOLD, stroke=6, align_x=W - 60 - 345, alpha=ease_out((lt - d * 0.35) / 0.4)))

def p_final(lt, d):
    im = grade(cam(load("final_ice_sun"), 1.0 + 0.15 * ease(lt / d), 0.5, 0.55), 0.2, 1.05)
    im = light_rays(im, lt, k=0.3)
    return glow_bloom(im, 0.3)

def p_end(lt, d):
    im = p_final(lt + 3, d + 3)
    a = ease_out((lt - 1.2) / 0.5)
    if a > 0:
        im = img(arr(im) * (1 - 0.45 * a))
        im = over(im, text_layer(["¿LO SABÍAS?"], 110, y=300, col=YELLOW, stroke=9, alpha=a))
        im = over(im, text_layer(["Cuéntamelo en comentarios"], 54, y=450, kind="bold", stroke=5, alpha=a))
    return im

# (inicio, función, posición subtítulo y, transición de entrada)
SHOTS = [
    (0.0,               p_hook_eye,    1380, "cut"),
    (st(0, "congelada"), p_hook_side,  1380, "flash"),
    (st(1),             p_flatline,    1480, "cut"),
    (st(2),             p_revive,      1380, "flash"),
    (st(3),             p_title,       1450, "zoom"),
    (st(4),             p_map,         1480, "fade"),
    (st(5),             p_hide,        1400, "fade"),
    (st(5, "espera"),   p_frost_leaves,1400, "fade"),
    (st(6),             p_freeze,      1380, "zoom"),
    (st(7),             p_tissue,      1420, "fade"),
    (st(8),             p_65,          1440, "fade"),
    (st(9),             p_heart_stop,  1530, "cut"),
    (st(10),            p_no_breath,   1420, "cut"),
    (st(11),            p_dead,        1420, "fade"),
    (st(12),            p_not_dead,    1420, "flash"),
    (st(13),            p_glucose,     1530, "zoom"),
    (st(14),            p_cells,       1380, "fade"),
    (st(15),            p_shrink,      1380, "fade"),
    (st(16),            p_alaska,      1420, "fade"),
    (st(17),            p_spring,      1420, "flash"),
    (st(17, "hielo"),   p_thaw,        1420, "fade"),
    (st(18),            p_heart_back,  1530, "cut"),
    (st(19),            p_breathe,     1420, "fade"),
    (st(19, "saltar"),  p_leap,        1420, "flash"),
    (st(20),            p_pond,        1420, "fade"),
    (st(21),            p_split,       1420, "cut"),
    (st(22),            p_final,       1420, "fade"),
    (se(23) - 0.3,      p_end,         1420, "cut"),
]
SHOT_STARTS = [s[0] for s in SHOTS]

def shot_at(t):
    k = max(i for i, s in enumerate(SHOT_STARTS) if s <= t + 1e-6)
    a = SHOT_STARTS[k]; b = SHOT_STARTS[k + 1] if k + 1 < len(SHOTS) else TOTAL
    return k, a, b

def render_shot(k, t):
    a = SHOT_STARTS[k]; b = SHOT_STARTS[k + 1] if k + 1 < len(SHOTS) else TOTAL
    return SHOTS[k][1](t - a, b - a)

TR = {"fade": 0.35, "zoom": 0.3, "flash": 0.22, "cut": 0.0}

def picture(t):
    k, a, b = shot_at(t)
    im = render_shot(k, t)
    kind = SHOTS[k][3]; dur = TR[kind]
    if k > 0 and dur and t - a < dur:
        p = (t - a) / dur
        prev = render_shot(k - 1, t)
        if kind == "fade":
            im = Image.blend(prev, im, ease(p))
        elif kind == "zoom":   # zoom de salida del plano anterior + fundido
            z = 1 + 0.25 * ease(p)
            pz = prev.resize((int(W * z), int(H * z)), Image.BILINEAR).crop((int(W * (z - 1) / 2), int(H * (z - 1) / 2), int(W * (z - 1) / 2) + W, int(H * (z - 1) / 2) + H))
            pz = pz.filter(ImageFilter.GaussianBlur(8 * p))
            im = Image.blend(pz, im, ease(p))
        elif kind == "flash":
            im = img(arr(im) + 255 * (1 - p) ** 2)
    elif kind == "flash" and t - a < 0.3:
        pass
    return im

# ======================================================================== subtítulos
CHUNKS = caption_chunks()
def captions(im, t, y):
    c = next((c for c in CHUNKS if c["start"] <= t < c["end"]), None)
    if c is None: return im
    words = [w[2].upper() for w in c["words"]]
    full = " ".join(words)
    age = t - c["start"]; s = 0.86 + 0.14 * ease_out(age / 0.12)
    size = int(92 * s)
    f = font(size, "black")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sp = d.textlength(" ", font=f)
    lines = [[]]; cur = 0
    for w in words:
        wl = d.textlength(w, font=f)
        if lines[-1] and cur + sp + wl > W - 140: lines.append([]); cur = 0
        lines[-1].append(w); cur += (sp if cur else 0) + wl
    yy = y - (len(lines) - 1) * size * 0.55
    for ln in lines:
        tw = sum(d.textlength(w, font=f) for w in ln) + sp * (len(ln) - 1); x = (W - tw) / 2
        for w in ln:
            col = YELLOW if is_highlight(w, full) else (255, 255, 255)
            d.text((x, yy), w, font=f, fill=col + (255,), stroke_width=max(6, size // 11), stroke_fill=(0, 0, 0, 255))
            x += d.textlength(w, font=f) + sp
        yy += size * 1.1
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(10))
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0)); base.putalpha(sh.point(lambda v: int(v * 0.8)))
    base = base.transform(base.size, Image.AFFINE, (1, 0, -4, 0, 1, -8))
    return Image.alpha_composite(Image.alpha_composite(im.convert("RGBA"), base), lay).convert("RGB")

def frame(t):
    k, a, b = shot_at(t)
    im = picture(t)
    im = finish(im, t)
    im = captions(im, t, SHOTS[k][2])
    if t > TOTAL - 0.6: im = img(arr(im) * clamp01((TOTAL - t) / 0.6))
    return im

# ======================================================================== salida
def encode(i0, i1, out):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 150 == 0: print(out, i, flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "frames":
        os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
        for x in sys.argv[2:]:
            frame(float(x)).save(os.path.join(HERE, "preview", f"f_{float(x):06.2f}.jpg"), quality=88)
    elif mode == "segment":
        i0, i1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; encode(i0, i1, out)
    elif mode == "video":
        N = int(TOTAL * FPS); J = int(os.environ.get("JOBS", "4"))
        cuts = [N * j // J for j in range(J + 1)]
        procs = [subprocess.Popen([sys.executable, __file__, "segment", str(cuts[j]), str(cuts[j + 1]), f"seg_{j}.mp4"], cwd=HERE) for j in range(J)]
        for p in procs: assert p.wait() == 0
        with open(os.path.join(HERE, "segs.txt"), "w") as f:
            for j in range(J): f.write(f"file 'seg_{j}.mp4'\n")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "segs.txt", "-c", "copy", "video_only.mp4"], cwd=HERE)
        for j in range(J): os.remove(os.path.join(HERE, f"seg_{j}.mp4"))
        os.remove(os.path.join(HERE, "segs.txt"))
        print("video_only.mp4", N, "frames")
