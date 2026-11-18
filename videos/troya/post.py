"""Posproducción: toma escena3d.mp4 (render 3D) y añade subtítulos, cifras discretas, viñeta, grano,
desenfoque suave en los bordes y la tarjeta final. Mezcla con mezcla.wav → final_9x16.mp4.
Uso: python3 post.py            (vídeo completo)
     python3 post.py stills t1 t2 …"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import TIMES, TOTAL, SCENES, caption_timeline  # noqa: E402

W, H, FPS = 1080, 1920, 30
FONT = next(f for f in ["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
                        "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if os.path.exists(f))
F_CAP = ImageFont.truetype(FONT, 100)
F_TOP = ImageFont.truetype(FONT, 54)
F_END = ImageFont.truetype(FONT, 84)
GOLD = (255, 204, 64)
SC = {s[2]: (a, b, v) for (a, b, v), s in zip(TIMES, SCENES)}
CAPS = caption_timeline()
HITS = [SC['caballo'][0], SC['brecha'][0], SC['incendio'][0], SC['final'][0]]

rng = np.random.default_rng(3)
GRAIN = [rng.standard_normal((H // 2, W // 2)).astype(np.float32) * 6 for _ in range(4)]
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
VIG = np.clip(1.12 - r ** 2 * 0.5, 0.35, 1).astype(np.float32)[..., None]
BLUR_MASK = np.clip((np.abs(yy - H * 0.52) / H - 0.30) / 0.16, 0, 1).astype(np.float32)[..., None]   # bordes arriba/abajo

def caption_layer(t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return None
    a, b, s = cur[0]
    age = t - a; pop = min(1, age / 0.1)
    sc = 0.84 + 0.16 * pop + 0.05 * math.sin(pop * math.pi)
    parts, hl = [], False
    for w in s.split(" "):
        if w.startswith("*") or w.startswith("¿*"): hl = True
        parts.append((w.replace("*", ""), hl))
        if "*" in w[1:] and (w.endswith("*") or w[-2:-1] == "*"): hl = False
    lay = Image.new("RGBA", (W, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    full = " ".join(p[0] for p in parts); font = F_CAP
    while d.textlength(full, font=font) > W - 100: font = ImageFont.truetype(FONT, font.size - 6)
    x = (W - d.textlength(full, font=font)) / 2
    for i, (wd, h) in enumerate(parts):
        txt = wd + (" " if i < len(parts) - 1 else "")
        d.text((x, 60), txt, font=font, fill=(GOLD if h else (255, 255, 255)) + (255,), stroke_width=10, stroke_fill=(15, 10, 10, 255))
        x += d.textlength(txt, font=font)
    if abs(sc - 1) > 1e-3:
        nw, nh = int(W * sc), int(240 * sc)
        l2 = lay.resize((nw, nh), Image.BILINEAR); out = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
        out.paste(l2, ((W - nw) // 2, (240 - nh) // 2)); lay = out
    return lay

def top_label(d, t):
    """Etiqueta discreta arriba: qué parte es leyenda y qué parte es arqueología."""
    spans = [("LEYENDA", (255, 214, 140), SC['asedio'][0] + 0.3, SC['ruinas'][0] - 0.2),
             ("ARQUEOLOGÍA", (150, 230, 160), SC['ruinas'][0] + 0.4, SC['final'][0] - 0.1),
             ("LA ILÍADA", (190, 170, 255), SC['final'][0] + 0.3, SC['final'][2] + 3.2)]
    for s, col, t0, t1 in spans:
        if t0 < t < t1:
            al = int(255 * min(1, (t - t0) / 0.4) * min(1, (t1 - t) / 0.4))
            w = d.textlength(s, font=F_TOP)
            d.text(((W - w) / 2, 150), s, font=F_TOP, fill=col + (al,), stroke_width=6, stroke_fill=(10, 8, 8, al))

def end_card(img, t):
    a = SC['final'][2] + 4.6
    if t < a: return img
    u = min(1, (t - a) / 0.5)
    arr = np.asarray(img, np.float32) * (1 - 0.35 * u)
    img = Image.fromarray(arr.astype(np.uint8)); d = ImageDraw.Draw(img, "RGBA")
    w = d.textlength("COMENTA", font=F_END); al = int(255 * u)
    d.text(((W - w) / 2, 330), "COMENTA", font=F_END, fill=(255, 255, 255, al), stroke_width=8, stroke_fill=(10, 8, 8, al))
    cx, yb = W / 2, 450 + 16 * math.sin(t * 8)
    d.polygon([(cx - 40, yb), (cx + 40, yb), (cx, yb + 54)], fill=GOLD + (int(255 * u),))
    return img

# cámara viva y contraste: ajustados midiendo con tools/medir.py (ver GUIA_ESTILO.md)
CONTRAST, PIVOT = 1.32, 96

def live_cam(img, t):
    z = 1.06 + 0.02 * math.sin(2 * math.pi * t / 11.0) + 0.0008 * t
    dx = 14 * math.sin(2 * math.pi * t / 13.0) + 8 * math.sin(2 * math.pi * t / 7.3 + 1.1)
    dy = 12 * math.sin(2 * math.pi * t / 17.0 + 0.7) + 7 * math.sin(2 * math.pi * t / 5.9 + 2.3)
    cw, ch = W / z, H / z
    return img.resize((W, H), Image.BILINEAR, box=(W / 2 + dx - cw / 2, H / 2 + dy - ch / 2, W / 2 + dx + cw / 2, H / 2 + dy + ch / 2))

def process(img, t, fi):
    img = live_cam(img, t)
    blur = img.filter(ImageFilter.GaussianBlur(5))
    arr = np.asarray(img, np.float32); arr = arr + (np.asarray(blur, np.float32) - arr) * BLUR_MASK
    arr = (arr - PIVOT) * CONTRAST + PIVOT
    arr *= VIG
    for h in HITS:
        u = t - h
        if 0 <= u < 0.22: arr += (1 - u / 0.22) * 90
    g = GRAIN[fi % 4]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    if t < 0.2: arr *= t / 0.2
    if t > TOTAL - 0.5: arr *= max(0, (TOTAL - t) / 0.5)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img = end_card(img, t)
    d = ImageDraw.Draw(img, "RGBA"); top_label(d, t)
    cap = caption_layer(t)
    if cap is not None and t < TOTAL - 0.3: img.paste(cap, (0, 1250), cap)
    return img

def frames(path):
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield Image.frombuffer("RGB", (W, H), b)
    p.wait()

if __name__ == "__main__":
    src = os.path.join(HERE, "escena3d.mp4")
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        want = sorted(float(x) for x in sys.argv[2:])
        for fi, img in enumerate(frames(src)):
            t = fi / FPS
            for w in want:
                if abs(t - w) < 0.5 / FPS: process(img, t, fi).save(os.path.join(HERE, f"still_{w:05.1f}.jpg"), quality=88)
            if t > want[-1]: break
        sys.exit()
    out = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", os.path.join(HERE, "mezcla.wav"), "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(HERE, "final_9x16.mp4")],
                           stdin=subprocess.PIPE)
    for fi, img in enumerate(frames(src)):
        out.stdin.write(process(img, fi / FPS, fi).tobytes())
        if fi % 300 == 0: print("post", fi, flush=True)
    out.stdin.close(); out.wait()
    print("final_9x16.mp4 listo")
