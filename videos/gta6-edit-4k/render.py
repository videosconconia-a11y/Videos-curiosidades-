# 20 s "beauty" edit of GTA VI in vertical 4K (2160x3840, 30 fps) from official Rockstar Games images.
# Smooth cinematic style: slow Ken Burns, zoom-blur transitions, light leaks, bloom, warm grade. No music.
# Images: assets/official (© Rockstar Games, not in git). Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, TOTAL = 2160, 3840, 30, 20.0
FD = os.path.join(HERE, "..", "gta6-secrets", "fonts")
IMG_DIR = os.path.join(HERE, "assets", "official")

# (image prefix, focal x, duration s, zoom from, zoom to, pan x)
SHOTS_DEF = [
    ("ULTIMATE_EDITION_SQUALO_01", .42, 2.0, 1.00, 1.10, -0.5),
    ("VINTAGE_VICE_CITY_PACK_02", .40, 2.0, 1.10, 1.00, 0.5),
    ("ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_03", .42, 1.0, 1.00, 1.08, 0.4),
    ("Vice_City_02", .62, 1.0, 1.08, 1.00, -0.4),
    ("Leonida_Keys_07", .45, 1.0, 1.00, 1.10, 0.0),
    ("ULTIMATE_EDITION_SQUALO_03", .62, 1.0, 1.10, 1.00, 0.4),
    ("Grassrivers_02", .55, 1.0, 1.00, 1.08, -0.4),
    ("Mount_Kalaga_National_Park_03", .30, 1.0, 1.08, 1.00, 0.4),
    ("Ambrosia_02", .50, 1.0, 1.00, 1.10, 0.4),
    ("VINTAGE_VICE_CITY_PACK_01", .45, 1.0, 1.10, 1.00, 0.0),
    ("ULTIMATE_EDITION_VAPID_GANADO_RETRO_BUILD_01", .45, 1.0, 1.00, 1.08, -0.4),
    ("ULTIMATE_EDITION_GROTTI_CHEETAH_03", .55, 1.0, 1.08, 1.00, 0.4),
    ("ULTIMATE_EDITION_SQUALO_04", .50, 1.0, 1.00, 1.10, -0.3),
    ("Jason_and_Lucia_18", .45, 1.0, 1.10, 1.00, 0.3),
    ("VINTAGE_VICE_CITY_PACK_EXCLUSIVE_LOOKS_01", .45, 4.0, 1.00, 1.12, 0.0),
]
SHOTS = []; t = 0.0
for d in SHOTS_DEF: SHOTS.append((t, t + d[2]) + d); t += d[2]
assert abs(t - TOTAL) < 1e-6

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

@lru_cache(maxsize=6)
def load(prefix):
    fs = sorted(glob.glob(os.path.join(IMG_DIR, prefix + ".*jpg"))) or sorted(glob.glob(os.path.join(IMG_DIR, prefix + "*.jpg")))
    return Image.open(fs[0]).convert("RGB")

def view(i, p):
    a, b, prefix, fx, dur, z0, z1, px = SHOTS[i]
    im = load(prefix)
    z = z0 + (z1 - z0) * (ease(p) * .6 + p * .4)
    ch = im.height / z; cw = ch * W / H
    cx = im.width * fx + px * (p - .5) * cw * 0.35; cy = im.height / 2
    cx = min(max(cx, cw / 2), im.width - cw / 2); cy = min(max(cy, ch / 2), im.height - ch / 2)
    v = im.resize((W, H), Image.LANCZOS, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    return v.filter(ImageFilter.UnsharpMask(radius=2.2, percent=55, threshold=2))

YY, XX = np.mgrid[0:H:4, 0:W:4]
VIG_S = np.clip(1.12 - (((XX - W / 2) / (W * .7)) ** 2 + ((YY - H / 2) / (H * .7)) ** 2) * .45, .45, 1).astype(np.float32)
VIG = np.asarray(Image.fromarray((VIG_S * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
GRAIN = [np.random.default_rng(k).standard_normal((H // 2, W // 2)).astype(np.float32) * 3.2 for k in range(4)]

def light_leak(t):
    """soft warm/magenta blobs drifting across the frame (computed small, upscaled)"""
    h, w = H // 8, W // 8; yy, xx = np.mgrid[0:h, 0:w]
    out = np.zeros((h, w, 3), np.float32)
    for k, (col, sp, ph) in enumerate([((255, 150, 60), .35, 0), ((255, 60, 150), .27, 2.1), ((255, 210, 120), .2, 4.2)]):
        cx = w * (.5 + .55 * math.sin(t * sp + ph)); cy = h * (.5 + .45 * math.cos(t * sp * .8 + ph))
        r = w * (.55 + .15 * math.sin(t + k))
        out += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None] * np.array(col, np.float32)
    return np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)

def bloom(a):
    small = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W // 8, H // 8), Image.BILINEAR)
    s = np.asarray(small, np.float32); s = np.clip(s - 170, 0, None) * 1.6
    g = Image.fromarray(np.clip(s, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BICUBIC)
    return np.asarray(g, np.float32)

def grade(a):
    l = a.mean(-1, keepdims=True) / 255
    a = (a - 128) * 1.06 + 132
    a = a + (l - .5) * np.array([16, 4, -14], np.float32)          # warm highlights / teal shadows
    sat = a.mean(-1, keepdims=True); a = sat + (a - sat) * 1.12      # a touch more saturation
    return a

def zoom_blur(img, k):
    """radial zoom-blur transition (k 0..1)"""
    if k <= 0.02: return img
    acc = img.astype(np.float32).copy(); n = 1
    pil = to_img(img)
    for s in (1 + .04 * k, 1 + .08 * k, 1 + .12 * k):
        cw, ch = W / s, H / s
        acc += np.asarray(pil.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)), np.float32); n += 1
    return acc / n

def shot_index(t):
    for i, s in enumerate(SHOTS):
        if s[0] <= t < s[1]: return i
    return len(SHOTS) - 1

def frame(t, fi):
    i = shot_index(t); a, b = SHOTS[i][:2]; p = (t - a) / (b - a); age = t - a; left = b - t
    img = np.asarray(view(i, p), np.float32)
    # crossfade into the shot (first 0.25 s), with zoom-blur around the cut
    XF = 0.25 if SHOTS[i][4] < 2 else 0.45
    if i > 0 and age < XF:
        pa, pb = SHOTS[i - 1][:2]
        prev = np.asarray(view(i - 1, min(1, (t - pa) / (pb - pa))), np.float32)
        k = ease(age / XF); img = prev * (1 - k) + img * k
        img = zoom_blur(img, 1 - abs(2 * k - 1))
    elif i + 1 < len(SHOTS) and left < 0.08:
        img = zoom_blur(img, 1 - left / 0.08)
    img = grade(img)
    img = img + bloom(img) * 0.35 + light_leak(t) * 0.10
    if t < 0.8: img = img * ease(t / 0.8)                               # fade in
    if TOTAL - t < 0.7: img = img * ease((TOTAL - t) / 0.7)             # fade out
    img = img * VIG + np.repeat(np.repeat(GRAIN[fi % 4], 2, 0), 2, 1)[..., None]
    out = to_img(img).convert("RGBA")
    d = ImageDraw.Draw(out)
    # final title on the last shot
    if i == len(SHOTS) - 1 and age > 0.8:
        k = eout((age - 0.8) / 1.0) * (ease((TOTAL - t) / 0.7) if TOTAL - t < 0.7 else 1)
        f = ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), 360)
        s = "GTA VI"; sp = 60 * (1 - k) + 24
        ws = [d.textlength(c, font=f) for c in s]; x = (W - sum(ws) - sp * (len(s) - 1)) / 2
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        for c, w_ in zip(s, ws): dl.text((x, 2700), c, font=f, fill=(255, 255, 255, int(255 * k))); x += w_ + sp
        g = lay.filter(ImageFilter.GaussianBlur(30)); out.alpha_composite(g); out.alpha_composite(lay)
    d.text((70, H - 110), "IMAGES © ROCKSTAR GAMES", font=ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), 40), fill=(255, 255, 255, 110))
    return out.convert("RGB")

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s), int(float(s) * FPS)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=92)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p",
                              os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 30 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
