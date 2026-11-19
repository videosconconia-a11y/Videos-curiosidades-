# Monta el vídeo 9:16: imágenes IA con movimiento de cámara (Ken Burns), fundidos,
# y subtítulos sincronizados palabra a palabra con la voz.
#   python3 render.py stills 1.0 20.5 ...   -> fotogramas de prueba
#   python3 render.py video                 -> video_only.mp4 (en paralelo)
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import load, captions, shots

LANDSCAPE = os.environ.get('FORMATO', 'vertical') == 'horizontal'
W, H, FPS = (1920, 1080, 30) if LANDSCAPE else (1080, 1920, 30)
SCENES, WORDS, TOTAL = load()
CAPS = captions(WORDS)
SHOTS = shots(SCENES, WORDS)
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
YELLOW = (255, 221, 0); WHITE = (255, 255, 255)
XF = 0.30                              # duración del fundido entre planos
CAP_Y = 760 if LANDSCAPE else 1180     # zona de subtítulos (en vertical, por encima de la interfaz de TikTok)
CAP_SIZE = 84 if LANDSCAPE else 104
MARGIN = 1.14                          # margen para el movimiento de cámara

_cache = {}
def src(name):
    if name not in _cache:
        im = Image.open(os.path.join(HERE, "assets", "img", f"{name}.png")).convert("RGB")
        s = max(W * MARGIN / im.width, H * MARGIN / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(2, 60, 2))
        im = ImageEnhance.Contrast(im).enhance(1.06)
        _cache[name] = im
    return _cache[name]

def move(k):
    # (zoom inicial, zoom final, desplazamiento x, desplazamiento y) distinto en cada plano
    opts = [(1.0, 1.12, 0.0, -0.3), (1.12, 1.0, 0.4, 0.0), (1.02, 1.14, -0.4, 0.2), (1.13, 1.02, 0.0, 0.4),
            (1.0, 1.1, 0.3, 0.3), (1.1, 1.0, -0.3, -0.2)]
    return opts[k % len(opts)]

def shot_img(k, t):
    a, b, name = SHOTS[k]
    a0, b0 = a - (XF if k > 0 else 0), b + XF
    p = min(max((t - a0) / (b0 - a0), 0), 1)
    e = p * p * (3 - 2 * p) * 0.35 + p * 0.65
    z0, z1, dx, dy = move(k)
    z = z0 + (z1 - z0) * e
    im = src(name)
    cw, ch = im.width / MARGIN / z, im.height / MARGIN / z
    # zoom 1 ya deja margen; el paneo se mueve dentro del margen disponible
    cx = im.width / 2 + dx * (e - 0.5) * (im.width - cw)
    cy = im.height / 2 + dy * (e - 0.5) * (im.height - ch)
    return im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

yy, xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1.12 - (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2) * 0.55, 0.45, 1)[..., None].astype(np.float32)
# degradado oscuro detrás de los subtítulos para que se lean siempre
SHADE = (1 - 0.38 * np.exp(-((yy - (CAP_Y + 110)) / 260.0) ** 2))[..., None].astype(np.float32)
del yy, xx
GRAIN = [np.random.default_rng(i).normal(0, 5, (H // 2, W // 2)).astype(np.float32) for i in range(4)]

FONTS = {s: ImageFont.truetype(FONT, s) for s in range(60, 112, 4)}

def caption(img, t):
    cur = [c for c in CAPS if c[0] <= t < c[1]]
    if not cur: return img
    a, b, ws = cur[0]
    words = [w[0].upper() for w in ws]
    size = CAP_SIZE
    d = ImageDraw.Draw(img)
    while size > 60 and d.textlength(" ".join(words), font=FONTS[size]) > W - 120: size -= 4
    f = FONTS[size]
    age = t - a
    pop = 0.86 + 0.14 * min(1, age / 0.09) + 0.05 * math.sin(min(1, age / 0.12) * math.pi)
    lay = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    space = dl.textlength(" ", font=f)
    total = sum(dl.textlength(w, font=f) for w in words) + space * (len(words) - 1)
    x = (W - total) / 2
    for (wtxt, wa, wb, hl), up in zip(ws, words):
        spoken = wa - 0.03 <= t
        col = YELLOW if (spoken and (t < wb + 0.12 or hl)) else WHITE
        if not spoken: col = (235, 235, 235)
        dl.text((x, 90), up, font=f, fill=col + (255,), stroke_width=max(6, size // 11), stroke_fill=(0, 0, 0, 255))
        x += dl.textlength(up, font=f) + space
    sh = lay.filter(ImageFilter.GaussianBlur(10))
    sh = Image.merge("RGBA", (*[Image.new("L", lay.size, 0)] * 3, sh.split()[3].point(lambda v: v * 0.7)))
    if pop != 1:
        nw, nh = int(W * pop), int(300 * pop)
        lay = lay.resize((nw, nh), Image.BILINEAR); sh = sh.resize((nw, nh), Image.BILINEAR)
        ox, oy = (W - nw) // 2, CAP_Y + (300 - nh) // 2
    else:
        ox, oy = 0, CAP_Y
    img.paste(sh, (ox, oy + 8), sh); img.paste(lay, (ox, oy), lay)
    return img

def frame(t, fi):
    ks = [k for k, (a, b, _) in enumerate(SHOTS) if a - XF / 2 <= t < b + XF / 2] or [len(SHOTS) - 1]
    k = ks[0]
    img = shot_img(k, t)
    a, b, _ = SHOTS[k]
    if k + 1 < len(SHOTS) and t > b - XF / 2:          # fundido al siguiente plano
        mix = (t - (b - XF / 2)) / XF
        img = Image.blend(img, shot_img(k + 1, t), min(1, max(0, mix)))
    arr = np.asarray(img, np.float32) * VIG * SHADE
    g = GRAIN[fi % 4]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    if t < 0.2: arr *= t / 0.2
    if t > TOTAL - 0.8: arr *= max(0, (TOTAL - t) / 0.8)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return caption(img, t)

def render_chunk(args):
    ci, f0, f1 = args
    path = os.path.join(HERE, f"chunk_{ci:02}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()
    return path

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for x in sys.argv[2:]:
            frame(float(x), 0).save(os.path.join(HERE, "stills", f"still_{float(x):05.1f}.jpg"), quality=88)
    else:
        nf = int(round(TOTAL * FPS)); nproc = int(os.environ.get("JOBS", os.cpu_count()))
        bounds = np.linspace(0, nf, nproc * 2 + 1).astype(int)
        jobs = [(i, bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
        with Pool(nproc) as pool:
            parts = pool.map(render_chunk, jobs)
        with open(os.path.join(HERE, "list.txt"), "w") as f:
            for p in parts: f.write(f"file '{os.path.basename(p)}'\n")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                               os.path.join(HERE, "list.txt"), "-c", "copy", os.path.join(HERE, "video_only.mp4")])
        for p in parts: os.remove(p)
        os.remove(os.path.join(HERE, "list.txt"))
        print("video ok")
