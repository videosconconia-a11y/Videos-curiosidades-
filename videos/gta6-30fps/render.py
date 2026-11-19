# "The Biggest Problem With GTA 6…" — TECH BENCHMARK HUD identity, rendered at 60 fps.
# Black/graphite benchmark UI, live FPS counter, frame-time graph, a real 60-vs-30 split-screen (the 30 side holds every
# other frame), warning-tape "PROBLEM" hook, quote cards. Palette: signal red #FF2E2E, FPS green #39FF88, amber #FFB020.
# Official Rockstar images only (assets/official, not in git). Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS = 1080, 1920, 60
FD = os.path.join(HERE, "fonts")
@lru_cache(maxsize=64)
def VF(name, s, w):
    f = ImageFont.truetype(os.path.join(FD, name), s)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
MS = lambda s, w=800: VF("Montserrat-VF.ttf", s, w)
OSW = lambda s, w=700: VF("Oswald-VF.ttf", s, w)
@lru_cache(maxsize=16)
def ANTON(s): return ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), s)
RED = (255, 46, 46); GRN = (57, 255, 136); AMB = (255, 176, 32); WHITE = (255, 255, 255); INK = (10, 11, 14); YEL = (255, 214, 0)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word, nth=0): return [w["a"] for w in SEGT[seg]["words"] if clean(w["w"]) == word][nth]
def build_shots():
    out = []; segs = TM["segments"]
    for i, (sd, st_) in enumerate(zip(SEGMENTS, segs)):
        s0 = 0.0 if i == 0 else st_["a"] - 0.1
        s1 = segs[i + 1]["a"] - 0.1 if i + 1 < len(segs) else TOTAL
        starts = [(s0 if c is None else word_time(sd["id"], c) - 0.08, n) for n, c in sd["shots"]]
        for j, (a, n) in enumerate(starts):
            out.append((a, starts[j + 1][0] if j + 1 < len(starts) else s1, n, sd["id"]))
    return out
SHOTS = build_shots()
def st(n): return [s[0] for s in SHOTS if s[2] == n][0]

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def rgba(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))
def text_c(d, cx, y, s, f, fill, **kw): d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill, **kw)

@lru_cache(maxsize=10)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + ".*jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2200 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im
def crop(key, w, h, cx=.5, cy=.5, z=1.0):
    im = load(key); ch = im.height / z; cw = ch * w / h
    if cw > im.width: cw = im.width / z; ch = cw * h / w
    x = min(max(cx * im.width, cw / 2), im.width - cw / 2); y = min(max(cy * im.height, ch / 2), im.height - ch / 2)
    return im.resize((w, h), Image.BILINEAR, box=(x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2)).convert("RGBA")
def full(key, p, cx=.5, cy=.5, z0=1.0, z1=1.12, dark=1.0):
    z = z0 + (z1 - z0) * (ease(p) * .6 + p * .4); img = crop(key, W, H, cx, cy, z)
    if dark != 1: img = Image.fromarray(np.uint8(np.asarray(img, np.float32) * np.array([dark, dark, dark, 1])), "RGBA")
    return img

def tape(img, y, k, txt="WARNING · PROBLEM · WARNING · PROBLEM · WARNING · PROBLEM · ", rot=-6, t=0):
    if k <= 0: return
    lay = rgba(W + 400, 120); d = ImageDraw.Draw(lay); d.rectangle([0, 0, lay.width, 120], fill=YEL + (255,))
    for x in range(-200, lay.width, 70): d.polygon([(x, 0), (x + 30, 0), (x - 10, 14), (x - 40, 14)], fill=(0, 0, 0, 255)); d.polygon([(x, 106), (x + 30, 106), (x - 10, 120), (x - 40, 120)], fill=(0, 0, 0, 255))
    f = OSW(56, 700); off = (t * 220) % d.textlength(txt, font=f)
    d.text((-off, 26), txt * 3, font=f, fill=(0, 0, 0, 255))
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    x = int(-200 - (1 - eout(k)) * 1400)
    img.alpha_composite(lay, (x, int(y - lay.height / 2)))

def badge(img, cx, cy, s, fill, fg=INK, f=None, pad=28, k=1.0, r=18):
    if k <= 0: return
    f = f or OSW(64, 700); d0 = ImageDraw.Draw(img); tw = d0.textlength(s, font=f)
    w, h = tw + 2 * pad, f.size * 1.35
    lay = rgba(int(w) + 4, int(h) + 4); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([0, 0, w, h], r, fill=fill + (255,)); d.text((pad, h * .08), s, font=f, fill=fg)
    sc = back(min(1, k)); lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BILINEAR)
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))

def cross(img, x0, y0, x1, y1, k, w=16):
    if k <= 0: return
    lay = rgba(); d = ImageDraw.Draw(lay); e = eout(k)
    d.line([(x0, y0), (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)], fill=RED + (255,), width=w); img.alpha_composite(lay)

# ---------------------------------------------------------------- persistent FPS counter (top-left HUD)
def fps_value(t):
    if t < st("dip"): return 30.0 + .3 * math.sin(t * 7)
    if t < st("cpu"):
        a = t - st("dip"); return 30 - 7 * ease((a - .8) / 1.2) * (1 - ease((a - 4.0) / .6)) + .5 * math.sin(t * 13)
    return 30.0 + .3 * math.sin(t * 7)
def hud(img, t):
    v = fps_value(t); col = GRN if v > 29 else (AMB if v > 26 else RED)
    glass = rgba(); d = ImageDraw.Draw(glass)
    d.rounded_rectangle([40, 80, 360, 230], 20, fill=(0, 0, 0, 175), outline=col + (200,), width=3)
    d.text((64, 94), "FPS", font=OSW(34, 600), fill=(200, 200, 200, 255))
    d.text((64, 124), f"{v:4.1f}", font=OSW(84, 700), fill=col + (255,))
    ms = 1000 / max(v, 1); d.text((230, 100), f"{ms:4.1f} ms", font=OSW(28, 500), fill=(200, 200, 200, 255))
    # tiny frame-time sparkline
    pts = []
    for i in range(40):
        tt = t - (39 - i) * .05; vv = fps_value(max(0, tt)); pts.append((230 + i * 3, 210 - (1000 / max(vv, 1) - 30) * 1.4))
    d.line(pts, fill=col + (255,), width=3)
    img.alpha_composite(glass)
    ImageDraw.Draw(img).text((40, 250), "IMAGES © ROCKSTAR GAMES · FAN-MADE", font=MS(20, 600), fill=(220, 220, 220))

# ---------------------------------------------------------------- shots
def split(t, age, p):
    """real 60 vs 30 demonstration: same pan, right half only updates every 2nd 60-fps frame"""
    def pan(tt): return crop("ULTIMATE_EDITION_GROTTI_CHEETAH_01", W // 2, H, .25 + .5 * ((tt * .22) % 1.0), .5, 1.15)
    fi = int(round(t * FPS)); t30 = (fi - fi % 2) / FPS
    img = Image.new("RGBA", (W, H), INK + (255,))
    img.paste(pan(t), (0, 0)); img.paste(pan(t30), (W // 2, 0))
    d = ImageDraw.Draw(img); d.rectangle([W // 2 - 4, 0, W // 2 + 4, H], fill=(255, 255, 255))
    badge(img, W * .25, 420, "60 FPS", GRN, k=age / .3); badge(img, W * .75, 420, "30 FPS", RED, fg=WHITE, k=(age - .15) / .3)
    text_c(d, W / 2, 1640, "Illustration of frame rate · official artwork", MS(24, 600), (230, 230, 230))
    return img
def draw_shot(name, t, a, b):
    age = t - a; p = (t - a) / max(b - a, 1e-3)
    if name == "hook":
        img = full("GTAVI_Launch_Trailer_poster", p, .5, .5, 1.25, 1.05)
        k = word_time("hook", "one") - a
        if age > k - .1:
            img = Image.fromarray(np.uint8(np.asarray(img, np.float32) * np.array([.55, .5, .5, 1])), "RGBA")
            tape(img, 520, (age - k + .1) / .3, t=t); tape(img, 1120, (age - k) / .3, rot=5, t=-t)
            d = ImageDraw.Draw(img); kk = back(min(1, (age - k - .1) / .25)); f = ANTON(int(150 * kk) + 1)
            text_c(d, W / 2, 680, "ONE BIG", f, WHITE, stroke_width=8, stroke_fill=INK); text_c(d, W / 2, 850, "PROBLEM", f, RED, stroke_width=8, stroke_fill=INK)
        return img
    if name == "split": return split(t, age, p)
    if name == "consoles":
        img = full("Vice_City_15", p, .5, .5, 1.05, 1.15, dark=.4); d = ImageDraw.Draw(img)
        text_c(d, W / 2, 380, "LOCKED AT", OSW(70, 700), WHITE)
        text_c(d, W / 2, 450, "30", ANTON(420), RED)
        for i, s in enumerate(["PS5", "XBOX SERIES X|S", "PS5 PRO"]):
            badge(img, W / 2, 1000 + i * 120, s + "  =  30 FPS", (30, 30, 34), fg=WHITE, f=OSW(54, 700), k=(age - .3 - i * .35) / .25)
        return img
    if name == "nomode":
        img = Image.new("RGBA", (W, H), INK + (255,)); d = ImageDraw.Draw(img)
        for i in range(0, H, 60): d.line([0, i, W, i], fill=(255, 255, 255, 10))
        t60, t40 = word_time("s2", "sixty") - a, word_time("s2", "forty") - a
        for (y, s, tk) in ((520, "60 FPS MODE", t60), (900, "40 FPS MODE", t40)):
            if age > tk - .2:
                badge(img, W / 2, y, s, (40, 40, 46), fg=WHITE, f=ANTON(130), k=(age - tk + .2) / .25)
                cross(img, 120, y + 100, W - 120, y - 100, (age - tk - .2) / .2, 22)
        return img
    if name == "dip":
        img = full("Vice_City_06", p, .45, .5, 1.0, 1.12, dark=.55); d = ImageDraw.Draw(img)
        # frame-time graph
        gx0, gx1, gy0, gy1 = 80, W - 80, 880, 1180
        lay = rgba(); dl = ImageDraw.Draw(lay); dl.rounded_rectangle([gx0 - 20, gy0 - 70, gx1 + 20, gy1 + 30], 20, fill=(0, 0, 0, 190))
        dl.text((gx0, gy0 - 58), "FPS · BASE PS5 · HEAVY ACTION", font=OSW(34, 600), fill=(220, 220, 220, 255))
        for v in (30, 25, 20):
            y = gy0 + (30 - v) / 12 * (gy1 - gy0) + 20; dl.line([gx0, y, gx1, y], fill=(255, 255, 255, 50), width=2); dl.text((gx1 - 50, y - 34), str(v), font=OSW(26, 500), fill=(200, 200, 200, 255))
        n = int(min(1, age / 3.5) * 120); pts = []
        for i in range(n):
            tt = a + i / 120 * 3.5; v = fps_value(tt); pts.append((gx0 + i / 120 * (gx1 - gx0), gy0 + 20 + (30 - v) / 12 * (gy1 - gy0)))
        if len(pts) > 1: dl.line(pts, fill=RED + (255,), width=6)
        img.alpha_composite(lay)
        if age > 1.6: badge(img, W / 2, 690, "LOW 20s", RED, fg=WHITE, f=ANTON(90), k=(age - 1.6) / .25)
        text_c(ImageDraw.Draw(img), W / 2, 1640, "Source: Digital Foundry launch analysis", MS(26, 600), (230, 230, 230))
        return img
    if name == "cpu":
        img = Image.new("RGBA", (W, H), INK + (255,)); d = ImageDraw.Draw(img); k = back(min(1, age / .35))
        cx, cy, s = W / 2, 760, 300 * k
        lay = rgba(); dl = ImageDraw.Draw(lay)
        for i in range(-3, 4):
            for (dx, dy) in ((i * s / 4, -s * .62), (i * s / 4, s * .62), (-s * .62, i * s / 4), (s * .62, i * s / 4)):
                dl.rectangle([cx + dx - 10, cy + dy - 10, cx + dx + 10, cy + dy + 10], fill=(180, 180, 190, 255))
        dl.rounded_rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], 24, fill=(40, 42, 50, 255), outline=AMB + (255,), width=8)
        img.alpha_composite(lay)
        if k > .6: text_c(d, cx, cy - 70, "CPU", ANTON(130), AMB)
        if age > .5: text_c(d, W / 2, 1120, "THE BOTTLENECK", OSW(80, 700), WHITE)
        return img
    if name == "crowds":
        img = full("Vice_City_13", p, .5, .5, 1.0, 1.12, dark=.7)
        for i, (s, w_) in enumerate((("TRAFFIC", "traffic"), ("CROWDS", "crowds"), ("PHYSICS", "physics"))):
            tw = word_time("s4", w_) - a
            badge(img, [300, 760, 420][i], [520, 760, 1000][i], s, AMB, f=ANTON(96), k=(age - tw + .1) / .25)
        tc = word_time("s4", "cutting") - a
        if age > tc: d = ImageDraw.Draw(img); text_c(d, W / 2, 1150, "60 FPS = CUT THEM", OSW(64, 700), RED, stroke_width=4, stroke_fill=INK)
        return img
    if name == "beauty":
        img = full("Mount_Kalaga_National_Park_04", p, .55, .5, 1.0, 1.14)
        if age > .4:
            k = eout((age - .4) / .4); lay = rgba(); dl = ImageDraw.Draw(lay)
            y = 400 + (1 - k) * 40; dl.rounded_rectangle([60, y, W - 60, y + 380], 26, fill=(0, 0, 0, int(190 * k)))
            dl.text((100, y + 30), "“", font=ANTON(160), fill=GRN + (int(255 * k),))
            for i, line in enumerate(["The single most visually", "striking game of the", "generation."]):
                dl.text((110, y + 120 + i * 70), line, font=MS(54, 800), fill=(255, 255, 255, int(255 * k)))
            dl.text((110, y + 330), "— Digital Foundry", font=MS(32, 600), fill=(200, 200, 200, int(255 * k)))
            img.alpha_composite(lay)
        return img
    if name == "outro":
        img = full("Jason_Lucia_Lock_And_Load_portrait", p, .5, .4, 1.0, 1.08, dark=.75); d = ImageDraw.Draw(img)
        text_c(d, W / 2, 360, "60 FPS", ANTON(170), GRN, stroke_width=6, stroke_fill=INK)
        text_c(d, W / 2, 545, "OR", OSW(70, 700), WHITE, stroke_width=4, stroke_fill=INK)
        text_c(d, W / 2, 630, "CROWDS?", ANTON(170), AMB, stroke_width=6, stroke_fill=INK)
        ty = word_time("outro", "yes") - a
        badge(img, W / 2 - 200, 1060, "YES", GRN, f=ANTON(110), k=(age - ty + .1) / .25)
        badge(img, W / 2 + 200, 1060, "NO", RED, fg=WHITE, f=ANTON(110), k=(age - ty - .25) / .25)
        return img
    raise ValueError(name)

# ---------------------------------------------------------------- captions (bold white, red keyword plates)
def build_caps():
    groups = []
    for seg in TM["segments"]:
        hl = [s for s in SEGMENTS if s["id"] == seg["id"]][0]["hl"]; cur = []
        for i, w in enumerate(seg["words"]):
            cur.append(dict(w, hl=clean(w["w"]) in hl))
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(seg["words"]) - 1:
                groups.append((cur, seg["id"])); cur = []
    return groups
CAPS = build_caps()
NUM = {"six": "6", "thirty": "30", "sixty": "60", "forty.": "40.", "twenties": "20s"}
def disp(w):
    lw = w.lower(); core = lw.rstrip(".,?!"); tail = lw[len(core):]
    return (NUM[core] + tail).upper() if core in NUM else w.upper()
def caption(img, t):
    g = None
    for ws, sid in CAPS:
        if ws[0]["a"] - .05 <= t: g = (ws, sid)
    if g is None: return
    ws, sid = g
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if t > ws[-1]["b"] + .5 or (nxt and t >= nxt[0] - .12): return
    toks = [(w, disp(w["w"])) for w in ws]
    y = 1360; f = MS(84, 900); d = ImageDraw.Draw(img)
    widths = [d.textlength(s, font=f) for _, s in toks]; sp = 24
    while sum(widths) + sp * (len(toks) - 1) > W - 100:
        f = MS(f.size - 4, 900); widths = [d.textlength(s, font=f) for _, s in toks]
    x = (W - sum(widths) - sp * (len(toks) - 1)) / 2
    age = t - ws[0]["a"]; pop = back(min(1, age / .12)) if age > 0 else 0
    lay = rgba(); dl = ImageDraw.Draw(lay)
    for (w, s_), wd in zip(toks, widths):
        on = w["a"] - .03 <= t; yy = y + (1 - pop) * 24
        if w["hl"] and on:
            dl.rounded_rectangle([x - 12, yy - 2, x + wd + 12, yy + f.size + 16], 12, fill=RED + (255,)); dl.text((x, yy), s_, font=f, fill=WHITE)
        else:
            dl.text((x, yy), s_, font=f, fill=(255, 255, 255, 255 if on else 120), stroke_width=8, stroke_fill=(0, 0, 0, 255 if on else 100))
        x += wd + sp
    img.alpha_composite(lay)

def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); return i, SHOTS[i]
def frame(t, fi=None):
    i, (a, b, name, seg) = shot_at(t)
    img = draw_shot(name, t, a, b); age = t - a
    if i and age < .12:                                                     # glitch cut: RGB split + slice offset
        arr = np.asarray(img).copy(); k = 1 - age / .12; s = int(30 * k)
        arr[..., 0] = np.roll(arr[..., 0], s, 1); arr[..., 2] = np.roll(arr[..., 2], -s, 1)
        rng = np.random.default_rng(int(t * 1000))
        for _ in range(6):
            y0 = rng.integers(0, H - 80); arr[y0:y0 + 60] = np.roll(arr[y0:y0 + 60], int(rng.integers(-80, 80) * k), 1)
        img = Image.fromarray(arr, "RGBA")
    hud(img, t); caption(img, t)
    out = img.convert("RGB")
    if t < .15: out = to_img(np.asarray(out, np.float32) * ease(t / .15))
    if TOTAL - t < .3: out = to_img(np.asarray(out, np.float32) * ease((TOTAL - t) / .3))
    return out

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 120 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
