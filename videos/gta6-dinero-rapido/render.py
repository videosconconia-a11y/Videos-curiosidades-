# Render de fotogramas 1080x1920 con PIL -> ffmpeg.
# Uso: python3 render.py video            (vídeo completo sin audio: video_only.mp4)
#      python3 render.py frames t1 t2 ...  (fotogramas de prueba en preview/)
import sys, os, math
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
from script_data import timeline, FPS

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
LINES, WORDS, SHOTS, TOTAL = timeline()
ANTON = os.path.join(HERE, "fonts", "Anton-Regular.ttf")
INTER = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
YEL, RED, WHITE = (255, 214, 0), (235, 30, 40), (255, 255, 255)
_font_cache = {}
def font(path, size):
    k = (path, int(size))
    if k not in _font_cache: _font_cache[k] = ImageFont.truetype(path, int(size))
    return _font_cache[k]

_img_cache = {}
def src(name):
    if name not in _img_cache:
        _img_cache[name] = Image.open(os.path.join(HERE, "img", name + ".jpg")).convert("RGB")
    return _img_cache[name]

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def clamp(x, a=0, b=1): return max(a, min(b, x))

def frame_bg(shot, t):
    """Encuadre 9:16 con zoom/pan; devuelve imagen y función imagen->pantalla."""
    im = src(shot["img"]); iw, ih = im.size
    p = clamp((t - shot["a"]) / max(0.01, shot["b"] - shot["a"]))
    e = shot["e"]; fx = shot.get("fx", 0.5); fy = 0.5
    z = 1.0 + 0.10 * p
    if e == "hook": z = 1.30 - 0.22 * ease(p * 2.2)
    if e in ("circle", "arrow"): z = 1.05 + 0.30 * ease(p * 1.5)
    if e == "step": z = 1.12 - 0.08 * p
    if e == "pan": fx = fx - 0.10 + 0.20 * p
    if e == "end": z = 1.0 + 0.05 * p
    if e in ("circle", "arrow"):  # el zoom se acerca al objetivo
        tx, ty = shot["t"]; k = 0.7 * ease(p * 1.5)
        fx = fx + (tx - fx) * k; fy = 0.5 + (ty - 0.5) * k * 1.4
    s = max(W / iw, H / ih) * z
    cw, ch = W / s, H / s
    cx = clamp(fx * iw, cw / 2, iw - cw / 2); cy = clamp(fy * ih, ch / 2, ih - ch / 2)
    # temblor en el gancho y en avisos
    if e in ("hook", "warn") and p < 0.35:
        cx += math.sin(t * 90) * 6 / s * (1 - p / 0.35); cy += math.cos(t * 77) * 6 / s * (1 - p / 0.35)
    cw, ch = min(cw, iw - 0.01), min(ch, ih - 0.01)
    cx = clamp(cx, cw / 2, iw - cw / 2); cy = clamp(cy, ch / 2, ih - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    out = im.resize((W, H), Image.BILINEAR, box=box, reducing_gap=None)
    to_screen = lambda x, y: ((x * iw - box[0]) * s, (y * ih - box[1]) * s)
    return out, to_screen, p

def text_c(d, xy, txt, f, fill, stroke=8, sfill=(0, 0, 0), anchor="mm"):
    d.text(xy, txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill, anchor=anchor)

def money(v):
    return "$" + f"{int(v):,}".replace(",", ".")

def draw_overlays(img, shot, t, to_screen, p):
    d = ImageDraw.Draw(img, "RGBA")
    e = shot["e"]; dt = t - shot["a"]
    # oscurecer arriba/abajo para legibilidad
    grad = Image.new("L", (1, H))
    for y in range(H):
        v = 0
        if y < 420: v = int(150 * (1 - y / 420))
        if y > 1000: v = int(170 * clamp((y - 1000) / 700))
        grad.putpixel((0, y), v)
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), grad.resize((W, H)))
    d = ImageDraw.Draw(img, "RGBA")

    if e == "hook":
        a = ease(dt / 0.25)
        f1 = font(ANTON, 120 * (1.3 - 0.3 * a)); f2 = font(ANTON, 150 * (1.3 - 0.3 * a))
        text_c(d, (W / 2, 250), "TODO LO QUE", f1, WHITE, 10)
        text_c(d, (W / 2, 395), "TIENES QUE SABER", f1, WHITE, 10)
        tw = d.textlength("DINERO EN GTA 6", font=f2)
        d.rectangle([W / 2 - tw / 2 - 24, 480, W / 2 + tw / 2 + 24, 670], fill=RED + (235,))
        text_c(d, (W / 2, 572), "DINERO EN GTA 6", f2, YEL, 10)
    if e == "warn":
        a = 0.5 + 0.5 * math.sin(dt * 14)
        d.rectangle([0, 0, W, H], outline=RED + (int(200 * a),), width=26)
        f = font(ANTON, 150)
        d.polygon([(W / 2 - 330, 420), (W / 2 - 250, 280), (W / 2 - 170, 420)], fill=YEL)
        text_c(d, (W / 2 - 250, 375), "!", font(ANTON, 110), (0, 0, 0), 0)
        text_c(d, (W / 2 + 90, 350), "ERROR", f, RED, 12, WHITE)
        text_c(d, (W / 2, 520), "QUE TE ARRUINA", font(ANTON, 96), WHITE, 9)
    if e == "step":
        a = ease(dt / 0.3); x = -500 + (W / 2 + 500) * a
        d.rounded_rectangle([x - 260, 250, x + 260, 470], 30, fill=RED + (240,))
        text_c(d, (x, 355), f"PASO {shot['n']}", font(ANTON, 170), WHITE, 0)
    if e in ("counter_down", "counter_up"):
        if e == "counter_down":
            v = 1_000_000 * (1 - ease(dt / 1.3)); col = RED if v < 999_000 else (110, 255, 120)
        else:
            v = 1_000_000 * ease(dt / 1.4); col = (110, 255, 120)
        f = font(ANTON, 180)
        bounce = 1 + 0.06 * math.sin(dt * 30) * (1 - clamp(dt / 1.4))
        f = font(ANTON, 180 * bounce)
        text_c(d, (W / 2, 400), money(v), f, col, 12)
        lab = "¡PERDIDO!" if (e == "counter_down" and v < 1) else ("EJEMPLO" if e == "counter_up" else "")
        if lab: text_c(d, (W / 2, 560), lab, font(ANTON, 84), YEL if e == "counter_up" else RED, 8, (0, 0, 0))
    if e in ("circle", "arrow"):
        tx, ty = shot["t"]; sx, sy = to_screen(tx, ty)
        a = ease((dt - 0.15) / 0.45)
        if a > 0:
            if e == "circle":
                r = 150
                d.arc([sx - r, sy - r * 0.8, sx + r, sy + r * 0.8], -90, -90 + 360 * a, fill=RED, width=16)
            # flecha que entra desde arriba a la derecha
            ex, ey = sx + 200 * math.cos(-0.9), sy - 230
            if e == "arrow": ex, ey = sx + 260, sy - 300
            hx, hy = (sx + (ex - sx) * 0.42, sy + (ey - sy) * 0.42) if e == "circle" else (sx + 30, sy - 35)
            k = clamp((dt - 0.35) / 0.3)
            if k > 0:
                bx, by = hx + (ex - hx) * 1.0, hy + (ey - hy) * 1.0
                px, py = bx + (hx - bx) * k, by + (hy - by) * k
                d.line([(bx, by), (px, py)], fill=RED, width=22)
                ang = math.atan2(hy - by, hx - bx)
                if k >= 1:
                    L = 60
                    pts = [(hx + 10 * math.cos(ang), hy + 10 * math.sin(ang)),
                           (hx - L * math.cos(ang - 0.5), hy - L * math.sin(ang - 0.5)),
                           (hx - L * math.cos(ang + 0.5), hy - L * math.sin(ang + 0.5))]
                    d.polygon(pts, fill=RED)
    if e == "end":
        a = ease(dt / 0.4)
        f = font(ANTON, 130)
        y0 = 360 - 60 * (1 - a)
        text_c(d, (W / 2, y0), "¿CUÁNTO DINERO", f, WHITE, 10)
        text_c(d, (W / 2, y0 + 150), "LLEVAS TÚ?", font(ANTON, 170), YEL, 11)
        k = ease((dt - 0.6) / 0.4)
        if k > 0:
            d.rounded_rectangle([W / 2 - 360, 640, W / 2 + 360, 760], 60, fill=RED + (int(240 * k),))
            text_c(d, (W / 2, 700), "TE LEO EN COMENTARIOS", font(ANTON, 64), WHITE, 0)


def draw_captions(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    # palabras de la frase activa, en bloques de hasta 3 palabras
    cur = [w for w in WORDS if w["a"] - 0.05 <= t]
    if not cur: return
    last = cur[-1]
    line = [w for w in WORDS if w["line"] == last["line"]]
    if t > LINES[last["line"]]["end"] + 0.15: return
    blocks, b = [], []
    for w in line:
        b.append(w)
        if len(b) >= 3 or w["text"][-1] in ".,:?…" or w["text"].endswith("..."):
            blocks.append(b); b = []
    if b: blocks.append(b)
    blk = next(bb for bb in blocks if last in bb)
    f = font(ANTON, 104)
    texts = [w["text"].upper() for w in blk]
    widths = [d.textlength(x, font=f) for x in texts]
    gap = 34; total = sum(widths) + gap * (len(texts) - 1)
    if total > W - 80:
        f = font(ANTON, 104 * (W - 80) / total); widths = [d.textlength(x, font=f) for x in texts]
        total = sum(widths) + gap * (len(texts) - 1)
    x = W / 2 - total / 2; y = 1180
    for w, txt, wd in zip(blk, texts, widths):
        if w["a"] - 0.05 > t:
            x += wd + gap; continue  # aún no dicha: hueco
        active = w is last and t <= w["b"] + 0.1
        pop = 1 + 0.08 * (1 - clamp((t - w["a"]) / 0.12)) if active else 1
        ff = font(ANTON, f.size * pop)
        col = YEL if w["key"] else WHITE
        if active and not w["key"]: col = (255, 255, 255)
        d.text((x + wd / 2, y), txt, font=ff, fill=col, stroke_width=10, stroke_fill=(0, 0, 0), anchor="mm")
        x += wd + gap

def credit(img):
    d = ImageDraw.Draw(img, "RGBA")
    f = font(INTER, 26); txt = "Imágenes © Rockstar Games · vídeo fan, no afiliado"
    tw = d.textlength(txt, font=f)
    d.rounded_rectangle([W / 2 - tw / 2 - 16, 1478, W / 2 + tw / 2 + 16, 1522], 20, fill=(0, 0, 0, 140))
    d.text((W / 2, 1500), txt, font=f, fill=(235, 235, 235), anchor="mm")

def render(t):
    shot = next((s for s in SHOTS if s["a"] <= t < s["b"]), SHOTS[-1] if t >= SHOTS[-1]["a"] else SHOTS[0])
    img, to_screen, p = frame_bg(shot, t)
    draw_overlays(img, shot, t, to_screen, p)
    draw_captions(img, t)
    # destello en cada corte
    dt = t - shot["a"]
    if dt < 0.1 and shot is not SHOTS[0]:
        img = Image.blend(img, Image.new("RGB", (W, H), WHITE), 0.55 * (1 - dt / 0.1))
    # fundido final
    if t > TOTAL - 0.4:
        img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), clamp((t - (TOTAL - 0.4)) / 0.4))
    return img

def chunk(args):
    i0, i1, path = args
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(render(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    return path

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
        for x in sys.argv[2:]:
            render(float(x)).save(os.path.join(HERE, "preview", f"f_{float(x):05.2f}.jpg"), quality=85)
    else:
        n = int(math.ceil(TOTAL * FPS)); k = os.cpu_count() or 4
        parts = [(n * j // k, n * (j + 1) // k, os.path.join(HERE, f"part_{j:02d}.mp4")) for j in range(k)]
        with Pool(k) as pool: files = pool.map(chunk, parts)
        with open(os.path.join(HERE, "parts.txt"), "w") as f:
            for x in files: f.write(f"file '{x}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(HERE, "parts.txt"),
                        "-c", "copy", os.path.join(HERE, "video_only.mp4")], check=True)
        for x in files: os.remove(x)
        os.remove(os.path.join(HERE, "parts.txt"))
        print("video_only.mp4", n, "frames")
