# GTA VI highlights montage (1080x1920, 30 fps, 70 s) built from official Rockstar Games images.
# Cuts are on a 120 BPM grid (beat = 0.5 s) so any 120 BPM epic track lines up: 2-beat, 1-beat... sections.
# No music — the user adds their own. A silent audio track is included for editor compatibility.
# Images: assets/official/<prefix>*.jpg (fetched from rockstargames.com/VI; © Rockstar Games; not in git).
# Usage: python3 render.py still <t>... | python3 render.py video <worker> <nworkers>
import sys, os, math, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, TOTAL = 1080, 1920, 30, 70.0
FD = os.path.join(HERE, "..", "gta6-secrets", "fonts")
ANTON = lambda s: ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), s)
def MONT(s, w=700):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
IMG_DIR = os.path.join(HERE, "assets", "official")

# (image prefix, focal x 0..1, label)
A = [("Jason_Lucia_Rooftop_portrait", .5, None), ("Vice_City_01", .5, None)]
B = [("Vice_City_15", .45, "VICE CITY"), ("Leonida_Keys_01", .55, "LEONIDA KEYS"), ("Grassrivers_04", .5, "GRASSRIVERS"),
     ("Ambrosia_04", .45, "AMBROSIA"), ("Port_Gellhorn_01", .3, "PORT GELLHORN"), ("Mount_Kalaga_National_Park_02", .38, "MOUNT KALAGA"),
     ("Vice_City_08", .5, "VICE CITY · NIGHT"), ("ULTIMATE_EDITION_SQUALO_01", .45, "LEONIDA")]
C = [("Jason_Duval_01", .7, "JASON"), ("Lucia_Caminos_02", .5, "LUCIA"), ("Boobie_Ike_02", .3, None), ("Real_Dimez_04", .5, None),
     ("Raul_Bautista_03", .82, None), ("Brian_Heder_04", .5, None), ("Cal_Hampton_02", .45, None), ("DreQuan_Priest_03", .45, None),
     ("Jason_and_Lucia_17", .55, None), ("Lucia_Caminos_03", .48, None), ("Jason_Duval_14", .55, None), ("Vice_City_04", .4, None),
     ("Lucia_Caminos_06", .45, None), ("Jason_Duval_15", .5, None), ("Vice_City_24", .2, None), ("Real_Dimez_03", .5, None)]
D = [("Jason_Duval_17", .33, None), ("Lucia_Caminos_13", .3, None), ("Jason_Duval_16", .4, None), ("Vice_City_17", .5, None),
     ("Grassrivers_08", .45, None), ("Jason_Duval_13", .45, None), ("Lucia_Caminos_14", .4, None), ("Jason_Duval_12", .55, None),
     ("Vice_City_14", .62, None), ("Jason_Duval_05", .35, None), ("Lucia_Caminos_11", .55, None), ("Jason_Duval_19", .65, None),
     ("Grassrivers_03", .4, None), ("Jason_Duval_18", .5, None), ("Vice_City_06", .5, None), ("Ambrosia_01", .55, None),
     ("Mount_Kalaga_National_Park_01", .5, None), ("Leonida_Keys_05", .4, None), ("Vice_City_13", .5, None), ("Port_Gellhorn_04", .55, None),
     ("ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_04", .5, None), ("ULTIMATE_EDITION_GROTTI_CHEETAH_01", .5, None), ("Vice_City_18", .3, None),
     ("ULTIMATE_EDITION_ELECTRIC_FANG_02", .3, None), ("Grassrivers_07", .35, None), ("Vice_City_21", .5, None), ("Lucia_Caminos_05", .32, None),
     ("Ambrosia_05", .55, None), ("Vice_City_16", .55, None), ("Jason_Duval_03", .3, None), ("ULTIMATE_EDITION_SQUALO_04", .5, None),
     ("Vice_City_19", .45, None)]
E = [("Jason_and_Lucia_14", .5, None), ("Jason_and_Lucia_16", .5, None), ("Mount_Kalaga_National_Park_06", .48, None),
     ("Leonida_Keys_04", .5, None), ("Vice_City_26", .5, None)]
F = [("Jason_Lucia_Lock_And_Load_portrait", .5, None)]

SHOTS = []  # (start, end, prefix, focal, label, section)
def add(lst, t0, dur, sec):
    t = t0
    for (p, fx, lab) in lst:
        SHOTS.append((t, t + dur, p, fx, lab, sec)); t += dur
    return t
t = add(A, 0.0, 4.0, "A"); t = add(B, t, 2.0, "B"); t = add(C, t, 1.0, "C"); t = add(D, t, 0.5, "D"); t = add(E, t, 2.0, "E"); add(F, t, TOTAL - t, "F")
assert abs(SHOTS[-1][1] - TOTAL) < 1e-6

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

@lru_cache(maxsize=12)
def load(prefix):
    fs = sorted(glob.glob(os.path.join(IMG_DIR, prefix + ".*jpg"))) or sorted(glob.glob(os.path.join(IMG_DIR, prefix + "*.jpg")))
    im = Image.open(fs[0]).convert("RGB"); s = 2100 / im.height
    return im.resize((int(im.width * s), 2100), Image.LANCZOS)

rng = np.random.default_rng(5)
MOVES = {}
def view(i, prefix, fx, p, sec):
    im = load(prefix)
    if i not in MOVES:
        r = np.random.default_rng(i)
        z0, z1 = (1.0, 1.18) if r.random() < .5 else (1.18, 1.0)
        if sec == "D": z0, z1 = (1.12, 1.25) if i % 2 else (1.25, 1.12)
        MOVES[i] = (z0, z1, r.uniform(-1, 1), r.uniform(-.6, .6))
    z0, z1, dx, dy = MOVES[i]
    z = z0 + (z1 - z0) * (ease(p) * .5 + p * .5)
    ch = im.height / z; cw = ch * W / H
    if cw > im.width: cw = im.width / z; ch = cw * H / W
    cx = im.width * fx + dx * (p - .5) * cw * 0.25; cy = im.height / 2 + dy * (p - .5) * (im.height - ch)
    cx = min(max(cx, cw / 2), im.width - cw / 2); cy = min(max(cy, ch / 2), im.height - ch / 2)
    return np.asarray(im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))).astype(np.float32)

YY, XX = np.mgrid[0:H, 0:W]
VIG = np.clip(1.15 - (((XX - W / 2) / (W * .65)) ** 2 + ((YY - H / 2) / (H * .65)) ** 2) * .5, .35, 1)[..., None].astype(np.float32)
GRAIN = [np.random.default_rng(k).standard_normal((H // 2, W // 2)).astype(np.float32) * 5 for k in range(4)]

def grade(a):  # light cinematic grade: contrast + warm highlights / cool shadows
    l = a.mean(-1, keepdims=True) / 255
    a = (a - 128) * 1.08 + 128
    a = a + (l - .5) * np.array([14, 4, -12], np.float32)
    return a

def text_layer(s, size, y, alpha, spacing=0.0, col=(255, 255, 255), sub=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = ANTON(size)
    chars = list(s); widths = [d.textlength(c, font=f) for c in chars]
    total = sum(widths) + spacing * (len(chars) - 1); x = (W - total) / 2
    for c, w_ in zip(chars, widths):
        d.text((x, y), c, font=f, fill=col + (int(255 * alpha),), stroke_width=6, stroke_fill=(0, 0, 0, int(160 * alpha))); x += w_ + spacing
    if sub:
        fm = MONT(40, 800); tw = d.textlength(sub, font=fm)
        d.text(((W - tw) / 2, y + size * 1.15), sub, font=fm, fill=(255, 210, 60, int(255 * alpha)))
    return lay

def shot_index(t):
    for i, s in enumerate(SHOTS):
        if s[0] <= t < s[1]: return i
    return len(SHOTS) - 1

def frame(t, fi):
    i = shot_index(t); a, b, prefix, fx, lab, sec = SHOTS[i]; p = (t - a) / (b - a); age = t - a
    img = view(i, prefix, fx, p, sec)
    # crossfades in slow sections
    xf = {"A": .6, "B": .35, "E": .5, "F": .5}.get(sec, 0)
    if xf and i > 0 and age < xf and SHOTS[i - 1][5] in ("A", "B", "E", "F"):
        j = i - 1; pa, pb, pp, pfx, _, psec = SHOTS[j]
        prev = view(j, pp, pfx, min(1, (t - pa) / (pb - pa)), psec)
        k = ease(age / xf); img = prev * (1 - k) + img * k
    # punch-in / shake on fast cuts
    if sec in ("C", "D") and age < 0.12:
        z = 1 + (0.08 if sec == "C" else 0.12) * (1 - age / 0.12)
        cw, ch = W / z, H / z; sh = 18 * (1 - age / 0.12) if sec == "D" else 0
        dx = sh * math.sin(fi * 2.1); dy = sh * math.cos(fi * 3.3)
        img = np.asarray(to_img(img).resize((W, H), Image.BILINEAR, box=((W - cw) / 2 + dx, (H - ch) / 2 + dy, (W + cw) / 2 + dx, (H + ch) / 2 + dy))).astype(np.float32)
    if sec == "D" and age < 0.1:  # RGB split
        o = int(16 * (1 - age / 0.1)); img = img.copy(); img[..., 0] = np.roll(img[..., 0], o, 1); img[..., 2] = np.roll(img[..., 2], -o, 1)
    img = grade(img)
    # flashes: every cut in C (soft), every 4th cut in D (hard), section changes (hard)
    if age < 0.08 and i > 0:
        if SHOTS[i - 1][5] != sec: img = img + 255 * (1 - age / 0.08) * .9
        elif sec == "D" and i % 4 == 0: img = img + 255 * (1 - age / 0.08) * .7
        elif sec == "C": img = img + 255 * (1 - age / 0.08) * .25
    # fade from black at the start, fade to black at the end
    if t < 1.2: img = img * ease(t / 1.2)
    img = img * VIG + np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    out = to_img(img).convert("RGBA")
    # titles
    if sec == "A" and i == 0 and t > 1.6:
        k = eout((t - 1.6) / .8); out.alpha_composite(text_layer("GTA VI", 300, 1300, k, spacing=40 * (1 - k) + 10))
    if sec == "A" and i == 1:
        k = min(1, age / .5) * min(1, (b - t) / .4); out.alpha_composite(text_layer("WELCOME TO LEONIDA", 120, 250, k, spacing=6))
    if lab and sec == "B":
        k = min(1, (age - .15) / .35) * min(1, (b - t) / .3) if age > .15 else 0
        if k > 0: out.alpha_composite(text_layer(lab, 130, 1450, k, spacing=14 * (1 - eout(age / 1.2)) + 4))
    if lab and sec == "C":
        out.alpha_composite(text_layer(lab, 160, 1480, 1.0, spacing=10))
    if sec == "F":
        k = eout((age - .3) / .7)
        if k > 0:
            dark = Image.new("RGBA", (W, H), (0, 0, 0, int(120 * k))); out.alpha_composite(dark)
            out.alpha_composite(text_layer("GTA VI", 280, 1280, k, spacing=12, sub="19 · 11 · 2026"))
    d = ImageDraw.Draw(out)
    d.text((40, H - 60), "IMAGES © ROCKSTAR GAMES", font=MONT(22, 700), fill=(255, 255, 255, 140))
    return out.convert("RGB")

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s), int(float(s) * FPS)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                              os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 150 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
