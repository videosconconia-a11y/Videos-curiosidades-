# Render 9:16 a partir de imágenes oficiales de Rockstar (img/), con movimiento de cámara,
# rótulos de datos y subtítulos sincronizados con la voz.
#   python3 render.py video          -> video_only.mp4
#   python3 render.py frames 1.0 9.5 -> check_XX.png (para revisar fotogramas sueltos)
import sys, os, math, subprocess, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import total, shot_timeline, caption_timeline, HIGHLIGHT
import script_data as SD
TAG = getattr(SD, "TAG", "GTA VI")

W, H, FPS = 1080, 1920, 30
TOTAL = total()
def font(size, w="Black"):
    for p in [f"/usr/share/fonts/opentype/inter/InterDisplay-{w}.otf", f"/usr/share/fonts/opentype/inter/Inter-{w}.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p, size)
F_CAP = font(92); F_STAT = font(200); F_STAT2 = font(150); F_SUB = font(56, "Bold"); F_TAG = font(38, "Bold")
F_CLOCK = font(150); F_PLACE = font(48, "Bold"); F_SMALL = font(30, "SemiBold")
YEL = (255, 214, 0); PINK = (255, 64, 160); CYAN = (60, 230, 255); WHITE = (255, 255, 255)
HANDLE = "@LeonidaMillonario"

_cache = {}
def load(name):
    if name not in _cache:
        _cache[name] = Image.open(os.path.join(HERE, "img", name + ".jpg")).convert("RGB")
    return _cache[name]

def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def back(x):  # sobrepaso para el "pop"
    x = min(max(x, 0), 1); c = 1.7; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def frame_bg(shot, u):
    name, fx, z0, z1, _ov = shot
    im = load(name); iw, ih = im.size
    z = z0 + (z1 - z0) * ease(u)
    ch = ih / z; cw = ch * W / H
    if cw > iw: cw = iw; ch = cw * H / W
    cx = fx * iw + (u - 0.5) * 0.04 * iw            # ligera panorámica
    cx = min(max(cx, cw / 2), iw - cw / 2); cy = ih / 2
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return im.resize((W, H), Image.BILINEAR, box=box)

# Degradados para que el texto se lea siempre
_g = np.zeros((H, 1), float); yy = np.arange(H)[:, None] / H
_g = np.clip((0.22 - yy) / 0.22, 0, 1) * 0.55 + np.clip((yy - 0.48) / 0.52, 0, 1) ** 1.3 * 0.78
SHADE = Image.fromarray((np.broadcast_to(_g, (H, W)) * 255).astype(np.uint8), "L")
BLACK = Image.new("RGB", (W, H), (0, 0, 0))

def text_w(d, s, f): return d.textlength(s, font=f)

def draw_center(img, y, s, f, fill, stroke=8, glow=None, scale=1.0):
    """Texto centrado con contorno; con scale != 1 se dibuja en capa y se escala (efecto pop)."""
    d0 = ImageDraw.Draw(img)
    bb = d0.textbbox((0, 0), s, font=f, stroke_width=stroke)
    tw, th = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
    lay = Image.new("RGBA", (int(tw), int(th)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((20 - bb[0], 20 - bb[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    if glow:
        g = Image.new("RGBA", lay.size, (0, 0, 0, 0)); dg = ImageDraw.Draw(g)
        dg.text((20 - bb[0], 20 - bb[1]), s, font=f, fill=glow + (255,), stroke_width=stroke + 6)
        g = g.filter(ImageFilter.GaussianBlur(22)); g.alpha_composite(lay); lay = g
    if scale != 1.0:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.BILINEAR)
    img.paste(lay, (int(W / 2 - lay.width / 2), int(y - lay.height / 2)), lay)

def fit_font(s, base, maxw, w="Black"):
    size = base.size; f = base
    while ImageDraw.Draw(BLACK).textlength(s, font=f) > maxw and size > 36:
        size -= 8; f = font(size, w)
    return f

def overlay(img, ov, u, dur):
    if not ov: return
    k = ov[0]; tt = u * dur
    p = back(tt / 0.35)
    if k == "stat":
        big, small = ov[1], ov[2]
        f = fit_font(big, F_STAT if len(big) <= 7 else F_STAT2, 980)
        draw_center(img, 560, big, f, YEL, 10, glow=PINK, scale=max(0.01, p))
        if tt > 0.15 and small:
            draw_center(img, 720, small.upper(), fit_font(small.upper(), F_SUB, 960, "Bold"), WHITE, 6, scale=max(0.01, back((tt - 0.15) / 0.3)))
    elif k == "clocks":
        d = ImageDraw.Draw(img, "RGBA")
        for i, (place, hour) in enumerate(ov[1]):
            q = back((tt - i * 0.35) / 0.35)
            if q <= 0: continue
            y = 430 + i * 330; x0, x1 = 120, 960
            off = (1 - min(q, 1)) * (W if i % 2 else -W)
            col = CYAN if i == 0 else YEL
            d.rounded_rectangle([x0 + off, y, x1 + off, y + 280], 40, fill=(10, 6, 30, 200), outline=col + (255,), width=6)
            d.text((x0 + 50 + off, y + 30), place, font=F_PLACE, fill=WHITE)
            d.text((x0 + 45 + off, y + 85), hour, font=F_CLOCK, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
    elif k == "bar":
        d = ImageDraw.Draw(img, "RGBA")
        frac = ease(min(tt / (dur * 0.9), 1)) * 0.37
        draw_center(img, 520, ov[1], F_SUB, WHITE, 6)
        x0, x1, y = 120, 960, 600
        d.rounded_rectangle([x0, y, x1, y + 70], 35, fill=(0, 0, 0, 170), outline=WHITE + (255,), width=5)
        d.rounded_rectangle([x0 + 10, y + 10, x0 + 10 + max(50, (x1 - x0 - 20) * frac), y + 60], 25, fill=YEL + (255,))
        draw_center(img, 735, f"{int(frac*212)} / 212 GB", F_SUB, YEL, 6)
    elif k == "end":
        d = ImageDraw.Draw(img, "RGBA")
        q = back(tt / 0.4)
        d.rounded_rectangle([90, 380, 990, 760], 50, fill=(10, 6, 30, int(200 * min(q, 1))))
        draw_center(img, 480, "SÍGUEME PARA MÁS", F_SUB, WHITE, 5, scale=max(0.01, q))
        draw_center(img, 590, HANDLE, fit_font(HANDLE, font(84), 860), YEL, 7, glow=PINK, scale=max(0.01, q))
        draw_center(img, 690, "Fan page · No afiliada a Rockstar Games", F_SMALL, WHITE, 3, scale=max(0.01, q))

def caption(img, tnow):
    for (a, b, txt) in caption_timeline():
        if a <= tnow < b: break
    else:
        return
    words = txt.upper().split()
    d = ImageDraw.Draw(img)
    lines = [[]];
    for w in words:
        test = " ".join(lines[-1] + [w])
        if lines[-1] and d.textlength(test, font=F_CAP) > 940: lines.append([w])
        else: lines[-1].append(w)
    p = back((tnow - a) / 0.16); sc = 0.75 + 0.25 * min(p, 1.08)
    f = font(int(92 * sc)) if sc != 1 else F_CAP
    y = 1290 - (len(lines) - 1) * 55
    for ln in lines:
        sp = d.textlength(" ", font=f)
        widths = [d.textlength(w, font=f) for w in ln]
        x = W / 2 - (sum(widths) + sp * (len(ln) - 1)) / 2
        for w, wd in zip(ln, widths):
            key = w.strip(",.:;¿?¡!…")
            col = YEL if key in HIGHLIGHT or any(c.isdigit() for c in key) else WHITE
            d.text((x, y), w, font=f, fill=col, stroke_width=9, stroke_fill=(0, 0, 0), anchor="lm")
            x += wd + sp
        y += 110

def chrome(img, tnow):
    d = ImageDraw.Draw(img, "RGBA")
    # etiqueta superior
    tag = TAG
    tw = d.textlength(tag, font=F_TAG)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, 150, W / 2 + tw / 2 + 26, 212], 31, fill=PINK + (230,))
    d.text((W / 2, 181), tag, font=F_TAG, fill=WHITE, anchor="mm")
    # crédito de imágenes solo en la parte central del vídeo (la cuenta solo aparece al final)
    a, b = TOTAL * 0.42, TOTAL * 0.58
    al = min(1, max(0, (tnow - a) / 0.4), max(0, (b - tnow) / 0.4))
    if al > 0:
        d.text((W / 2, 1585), "Imágenes: Rockstar Games", font=F_SUB, fill=(255, 255, 255, int(230 * al)), anchor="mm",
               stroke_width=4, stroke_fill=(0, 0, 0, int(230 * al)))
    # barra de progreso del vídeo (retención)
    d.rectangle([0, H - 8, W * tnow / TOTAL, H], fill=YEL + (255,))

def render_frame(tnow, shots):
    for i, (a, b, shot) in enumerate(shots):
        if a <= tnow < b or i == len(shots) - 1: break
    u = (tnow - a) / (b - a)
    img = frame_bg(shot, u)
    img = Image.composite(BLACK, img, SHADE)
    # flash + golpe de zoom al entrar en plano
    k = tnow - a
    if i > 0 and k < 0.12:
        img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.45 * (1 - k / 0.12))
    overlay(img, shot[4], u, b - a)
    caption(img, tnow)
    chrome(img, tnow)
    return img

def main():
    shots = shot_timeline()
    mode = sys.argv[1]
    if mode == "frames":
        for j, ts in enumerate(sys.argv[2:]):
            render_frame(float(ts), shots).save(os.path.join(HERE, f"check_{j:02}.png"))
        return
    n = int(TOTAL * FPS)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                             "-pix_fmt", "yuv420p", os.path.join(HERE, "video_only.mp4")], stdin=subprocess.PIPE)
    for fi in range(n):
        proc.stdin.write(render_frame(fi / FPS, shots).tobytes())
        if fi % 300 == 0: print(f"{fi}/{n}", flush=True)
    proc.stdin.close(); proc.wait()
    print("vídeo ok")

if __name__ == "__main__":
    main()
