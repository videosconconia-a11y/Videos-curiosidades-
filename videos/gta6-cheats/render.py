# "GTA 6 Cheat Codes Are FAKE (For Now)" — STICK-FIGURE DOODLE identity over darkened official images.
# Hand-drawn feel: wobbly white chalk lines with dark halo, doodled phone, crossed-out number list (placeholder digits, no
# real codes), red ✗ stamps, a sticky-note checklist, a search bar typing "gta 6 cheats". Official images © Rockstar Games.
# Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS = 1080, 1920, 30
FD = os.path.join(HERE, "fonts")
@lru_cache(maxsize=64)
def MS(s, w=800):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), int(s))
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
@lru_cache(maxsize=32)
def ANTON(s): return ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), int(s))
WHITE = (255, 255, 255); RED = (255, 55, 55); YEL = (255, 214, 0); INK = (12, 12, 16); GRN = (60, 220, 120)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word, nth=0): return [w["a"] for w in SEGT[seg]["words"] if clean(w["w"]) == clean(word)][nth]
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
def rgba(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def text_c(d, cx, y, s, f, fill, **kw): d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill, **kw)

@lru_cache(maxsize=8)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + ".*jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2200 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im
def bg(key, p, cx=.5, z0=1.0, z1=1.1, dark=.38):
    im = load(key); z = z0 + (z1 - z0) * p; ch = im.height / z; cw = ch * W / H
    if cw > im.width: cw = im.width / z; ch = cw * H / W
    x = min(max(cx * im.width, cw / 2), im.width - cw / 2); y = im.height / 2
    v = im.resize((W, H), Image.BILINEAR, box=(x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2)).filter(ImageFilter.GaussianBlur(3))
    return Image.fromarray((np.asarray(v, np.float32) * dark).astype(np.uint8)).convert("RGBA")

# ---------------------------------------------------------------- hand-drawn primitives (wobble that "boils" 8x/s)
def wob(pts, t, amp=3.0, seed=0):
    k = int(t * 8); rng = np.random.default_rng(seed * 97 + k)
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in pts]
def seg_pts(a, b, n=6): return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
def chalk_line(lay, a, b, t, col=WHITE, w=12, seed=0):
    d = ImageDraw.Draw(lay); pts = wob(seg_pts(a, b), t, 2.5, seed)
    d.line(pts, fill=(0, 0, 0, 160), width=w + 10, joint="curve"); d.line(pts, fill=col + (255,), width=w, joint="curve")
def chalk_circle(lay, c, r, t, col=WHITE, w=12, seed=0, fill=None):
    d = ImageDraw.Draw(lay); pts = wob([(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 28)], t, 2.5, seed)
    if fill: d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=(0, 0, 0, 160), width=w + 10, joint="curve"); d.line(pts + [pts[0]], fill=col + (255,), width=w, joint="curve")

def stick(lay, x, y, t, pose="stand", s=1.0, seed=0, face="neutral", col=WHITE):
    """stick figure, feet at (x, y)"""
    hr = 55 * s; hip = (x, y - 230 * s); neck = (x, y - 430 * s); head = (x, y - 430 * s - hr)
    bob = math.sin(t * 5 + seed) * 6 * s
    hip = (hip[0], hip[1] + bob); neck = (neck[0], neck[1] + bob); head = (head[0], head[1] + bob)
    chalk_circle(lay, head, hr, t, col, seed=seed)
    chalk_line(lay, neck, hip, t, col, seed=seed + 1)
    for sgn in (-1, 1): chalk_line(lay, hip, (x + sgn * 70 * s, y), t, col, seed=seed + 2 + sgn)
    sh = (neck[0], neck[1] + 40 * s)
    if pose == "phone":            # right hand at ear, left on hip
        chalk_line(lay, sh, (x + 70 * s, sh[1] + 40 * s), t, col, seed=seed + 4); chalk_line(lay, (x + 70 * s, sh[1] + 40 * s), (head[0] + hr * .9, head[1] + 10 * s), t, col, seed=seed + 5)
        d = ImageDraw.Draw(lay); px, py = head[0] + hr * 1.05, head[1] - 10 * s
        d.rounded_rectangle([px - 18 * s, py - 45 * s, px + 18 * s, py + 45 * s], 8, fill=(30, 30, 40, 255), outline=WHITE + (255,), width=5)
        chalk_line(lay, sh, (x - 60 * s, hip[1] - 30 * s), t, col, seed=seed + 6); chalk_line(lay, (x - 60 * s, hip[1] - 30 * s), (x - 15 * s, hip[1] - 5 * s), t, col, seed=seed + 7)
    elif pose == "shrug":
        for sgn in (-1, 1):
            e = (x + sgn * 90 * s, sh[1] + 30 * s); chalk_line(lay, sh, e, t, col, seed=seed + 8 + sgn); chalk_line(lay, e, (x + sgn * 150 * s, sh[1] - 50 * s), t, col, seed=seed + 10 + sgn)
    elif pose == "point":          # right arm points up-right at a sign
        chalk_line(lay, sh, (x + 190 * s, sh[1] - 120 * s), t, col, seed=seed + 12); chalk_line(lay, sh, (x - 80 * s, sh[1] + 140 * s), t, col, seed=seed + 13)
    elif pose == "stop":           # both palms out
        for sgn in (-1, 1): chalk_line(lay, sh, (x + sgn * 170 * s, sh[1] - 10 * s), t, col, seed=seed + 14 + sgn)
        for sgn in (-1, 1): chalk_circle(lay, (x + sgn * 185 * s, sh[1] - 15 * s), 20 * s, t, col, w=8, seed=seed + 16 + sgn)
    elif pose == "cheer":
        for sgn in (-1, 1): chalk_line(lay, sh, (x + sgn * 120 * s, sh[1] - 170 * s + 20 * math.sin(t * 12 + sgn)), t, col, seed=seed + 18 + sgn)
    elif pose == "facepalm":
        chalk_line(lay, sh, (x + 60 * s, sh[1] + 40 * s), t, col, seed=seed + 20); chalk_line(lay, (x + 60 * s, sh[1] + 40 * s), (head[0], head[1] + 10 * s), t, col, seed=seed + 21)
        chalk_line(lay, sh, (x - 70 * s, sh[1] + 150 * s), t, col, seed=seed + 22)
    else:
        for sgn in (-1, 1): chalk_line(lay, sh, (x + sgn * 80 * s, sh[1] + 150 * s), t, col, seed=seed + 24 + sgn)
    d = ImageDraw.Draw(lay); hx, hy = head
    if face == "x":                # X eyes
        for ex in (-20, 20):
            d.line([hx + ex * s - 10, hy - 18, hx + ex * s + 10, hy + 2], fill=col + (255,), width=6); d.line([hx + ex * s - 10, hy + 2, hx + ex * s + 10, hy - 18], fill=col + (255,), width=6)
    else:
        for ex in (-20, 20): d.ellipse([hx + ex * s - 7, hy - 15, hx + ex * s + 7, hy - 1], fill=col + (255,))
    if face == "happy": d.arc([hx - 25 * s, hy - 10, hx + 25 * s, hy + 30 * s], 20, 160, fill=col + (255,), width=6)
    elif face in ("sad", "x"): d.arc([hx - 22 * s, hy + 12 * s, hx + 22 * s, hy + 40 * s], 200, 340, fill=col + (255,), width=6)
    elif face == "shout": d.ellipse([hx - 14 * s, hy + 6 * s, hx + 14 * s, hy + 34 * s], outline=col + (255,), width=6)
    else: d.line([hx - 18 * s, hy + 20 * s, hx + 18 * s, hy + 20 * s], fill=col + (255,), width=6)

def xstamp(lay, cx, cy, r, k, t):
    if k <= 0: return
    e = eout(min(1, k)); rr = r * (1.6 - .6 * back(min(1, k)))
    chalk_line(lay, (cx - rr, cy - rr), (cx - rr + 2 * rr * min(1, e * 2), cy - rr + 2 * rr * min(1, e * 2)), t, RED, 26, 40)
    if e > .5: chalk_line(lay, (cx + rr, cy - rr), (cx + rr - 2 * rr * (e - .5) * 2, cy - rr + 2 * rr * (e - .5) * 2), t, RED, 26, 41)
def stamp(img, s, cx, cy, k, col=RED, size=170, rot=-8):
    if k <= 0: return
    sc = 2.0 - back(min(1, k)); f = ANTON(size * sc); lay = rgba(); d = ImageDraw.Draw(lay); w = d.textlength(s, font=f)
    d.rounded_rectangle([cx - w / 2 - 30, cy - f.size * .15, cx + w / 2 + 30, cy + f.size * 1.2], 20, outline=col + (255,), width=14)
    text_c(d, cx, cy, s, f, col + (255,)); img.alpha_composite(lay.rotate(rot, center=(cx, cy + f.size / 2), resample=Image.BICUBIC))

def draw_shot(name, t, a, b):
    age = t - a; p = (t - a) / max(b - a, 1e-3)
    if name == "hook":
        img = bg("Vice_City_08", p); lay = rgba()
        stick(lay, 540, 1250, t, "stop", 1.15, 1, "shout"); img.alpha_composite(lay)
        d = ImageDraw.Draw(img); k = back(min(1, age / .3))
        text_c(d, W / 2, 230, "STOP", ANTON(int(230 * k) + 1), RED, stroke_width=8, stroke_fill=INK)
        tw = word_time("hook", "don't") - a
        if age > tw - .1: stamp(img, "DON'T WORK", W / 2, 520, (age - tw + .1) / .25, size=110)
        return img
    if name == "search":
        img = bg("Vice_City_15", p); d = ImageDraw.Draw(img)
        d.rounded_rectangle([90, 330, W - 90, 450], 60, fill=(255, 255, 255), outline=INK, width=6)
        q = "gta 6 cheats"; n = min(len(q), int(age * 12)); d.text((150, 360), q[:n] + ("|" if int(t * 3) % 2 else ""), font=MS(54, 700), fill=INK)
        d.ellipse([W - 190, 355, W - 130, 415], outline=INK, width=8); d.line([W - 140, 405, W - 115, 430], fill=INK, width=10)
        lay = rgba()
        for i, x in enumerate((230, 540, 850)): stick(lay, x, 1250, t + i, "phone" if i == 1 else "stand", .85, 10 + i * 5, "happy")
        img.alpha_composite(lay)
        for i, s in enumerate(["gta 6 cheats", "gta 6 cheat codes", "gta 6 cheat code number"]):
            kk = eout((age - .8 - i * .25) / .3)
            if kk > 0: d.text((150, 470 + i * 70), "🔍 " if False else "› " + s, font=MS(40, 600), fill=(255, 255, 255, int(255 * kk)))
        return img
    if name == "list":
        img = bg("Vice_City_01", p); lay = rgba(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle([140, 280, W - 140, 1000], 30, fill=(255, 240, 150, 245), outline=INK, width=6)
        text_c(d, W / 2, 310, "\"GTA 6 CHEATS\"", ANTON(80), INK)
        for i in range(6):
            y = 440 + i * 88; kk = eout((age - i * .15) / .25)
            if kk > 0:
                d.text((210, y), f"1-999-{'X' * 3}-{'X' * 4}", font=MS(52, 800), fill=(40, 40, 60, int(255 * kk)))
        tg = word_time("s2", "old") - a
        if age > tg: text_c(d, W / 2, 940 - 30, "", MS(10), INK)
        img.alpha_composite(lay)
        if age > tg - .1: stamp(img, "GTA 5 CODES", W / 2, 1040, (age - tg + .1) / .25, col=(255, 140, 40), size=110, rot=-6)
        lay2 = rgba(); stick(lay2, 880, 1350, t, "point", .7, 30, "neutral"); img.alpha_composite(lay2)
        return img
    if name == "dial":
        img = bg("Vice_City_08", p, .6, 1.05, 1.12); lay = rgba()
        dead = age > 1.6
        stick(lay, 400, 1300, t, "phone" if not dead else "facepalm", 1.1, 50, "x" if dead else "neutral")
        # big phone screen doodle
        d = ImageDraw.Draw(lay); x0, y0 = 620, 420
        d.rounded_rectangle([x0, y0, x0 + 340, y0 + 600], 40, fill=(20, 20, 30, 240), outline=WHITE + (255,), width=8)
        d.text((x0 + 40, y0 + 60), "CALLING…" if not dead else "NOTHING", font=MS(46, 900), fill=(GRN if not dead else RED) + (255,))
        d.text((x0 + 40, y0 + 140), "1-999-XXX", font=MS(40, 700), fill=(220, 220, 220, 255))
        for i in range(3):
            if not dead and int(t * 3) % 3 >= i: d.ellipse([x0 + 60 + i * 60, y0 + 300, x0 + 90 + i * 60, y0 + 330], fill=WHITE + (255,))
        img.alpha_composite(lay)
        tn = word_time("s2", "nothing") - a
        if age > tn - .1:
            lay3 = rgba(); xstamp(lay3, x0 + 170, y0 + 330, 170, (age - tn + .1) / .3, t); img.alpha_composite(lay3)
        return img
    if name == "rockstar":
        img = bg("Leonida_Keys_01", p); d = ImageDraw.Draw(img); lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([110, 300, W - 110, 900], 30, fill=(255, 255, 255, 240), outline=INK, width=6)
        text_c(dl, W / 2, 330, "OFFICIAL CHEAT LIST", ANTON(84), INK)
        dl.line([170, 450, W - 170, 450], fill=INK, width=4)
        text_c(dl, W / 2, 560, "(empty)", MS(70, 700), (150, 150, 150, 255))
        img.alpha_composite(lay)
        ty = word_time("s3", "yet.") - a
        if age > ty - .2: stamp(img, "NOT YET", W / 2, 640, (age - ty + .2) / .25, size=120)
        lay2 = rgba(); stick(lay2, 540, 1400, t, "shrug", .9, 60, "neutral"); img.alpha_composite(lay2)
        return img
    if name == "fake":
        img = bg("Vice_City_18", p, .5, 1.1, 1.2, .3); d = ImageDraw.Draw(img); lay = rgba(); dl = ImageDraw.Draw(lay)
        # doodle of a clickbait thumbnail
        dl.rounded_rectangle([120, 300, W - 120, 860], 26, fill=(255, 60, 60, 230), outline=WHITE + (255,), width=8)
        text_c(dl, W / 2, 360, "INFINITE MONEY", ANTON(100), WHITE + (255,)); text_c(dl, W / 2, 490, "CHEAT 100% WORKING", ANTON(70), YEL + (255,))
        text_c(dl, W / 2, 620, "$$$$$$$$", ANTON(110), (40, 220, 120, 255))
        img.alpha_composite(lay)
        tf = word_time("s4", "fake.") - a
        if age > tf - .15: stamp(img, "FAKE", W / 2, 470, (age - tf + .15) / .25, col=YEL, size=220, rot=-12)
        lay2 = rgba(); stick(lay2, 540, 1400, t, "facepalm" if age > tf else "stand", .9, 70, "sad"); img.alpha_composite(lay2)
        return img
    if name == "outro":
        img = bg("Jason_Lucia_Rooftop_portrait", p, .5, 1.0, 1.06, .45); d = ImageDraw.Draw(img)
        lay = rgba(); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([140, 330, W - 140, 760], 30, fill=(255, 240, 150, 245), outline=INK, width=6)
        text_c(dl, W / 2, 360, "REAL CHEATS", ANTON(90), INK)
        for i, s in enumerate(["☐ confirmed by testers", "☐ shown working in-game"]):
            dl.text((200, 500 + i * 90), s.replace("☐", "[ ]"), font=MS(46, 800), fill=INK)
        img.alpha_composite(lay)
        tc = word_time("outro", "cheats.") - a
        if age > tc - .2: stamp(img, "COMMENT \"CHEATS\"", W / 2, 830, (age - tc + .2) / .25, col=GRN, size=90, rot=-4)
        lay2 = rgba(); stick(lay2, 540, 1400, t, "cheer", .9, 80, "happy"); img.alpha_composite(lay2)
        return img
    raise ValueError(name)

def build_caps():
    groups = []
    for seg in TM["segments"]:
        hl = [s for s in SEGMENTS if s["id"] == seg["id"]][0]["hl"]; cur = []
        for i, w in enumerate(seg["words"]):
            cur.append(dict(w, hl=clean(w["w"]) in {clean(x) for x in hl}))
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(seg["words"]) - 1:
                groups.append((cur, seg["id"])); cur = []
    return groups
CAPS = build_caps()
NUM = {"six": "6", "six.": "6.", "five": "5"}
def caption(img, t):
    g = None
    for ws, sid in CAPS:
        if ws[0]["a"] - .05 <= t: g = (ws, sid)
    if g is None: return
    ws, sid = g
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if t > ws[-1]["b"] + .5 or (nxt and t >= nxt[0] - .12): return
    toks = [(w, NUM.get(w["w"].lower(), w["w"]).upper()) for w in ws]
    d = ImageDraw.Draw(img); f = ANTON(100)
    widths = [d.textlength(s, font=f) for _, s in toks]; sp = 22
    while sum(widths) + sp * (len(toks) - 1) > W - 100:
        f = ANTON(f.size - 4); widths = [d.textlength(s, font=f) for _, s in toks]
    x = (W - sum(widths) - sp * (len(toks) - 1)) / 2; y = 1470
    age = t - ws[0]["a"]; pop = back(min(1, age / .12)) if age > 0 else 0
    for (w, s_), wd in zip(toks, widths):
        on = w["a"] - .03 <= t; yy = y + (1 - pop) * 24
        d.text((x, yy), s_, font=f, fill=(YEL if w["hl"] and on else (WHITE if on else (200, 200, 200))), stroke_width=9, stroke_fill=INK)
        x += wd + sp

def shot_at(t):
    i = max(k for k, s in enumerate(SHOTS) if s[0] <= t or k == 0); return i, SHOTS[i]
def frame(t, fi=None):
    i, (a, b, name, seg) = shot_at(t)
    img = draw_shot(name, t, a, b); age = t - a
    if i and age < .18:                                        # page-flip wipe
        prev = draw_shot(SHOTS[i - 1][2], a - 1e-3, SHOTS[i - 1][0], SHOTS[i - 1][1]); k = eout(age / .18)
        canvas = prev.copy(); canvas.alpha_composite(img.crop((0, 0, int(W * k) or 1, H)), (0, 0)); img = canvas
    caption(img, t)
    d = ImageDraw.Draw(img); d.text((30, 30), "IMAGES © ROCKSTAR GAMES · DOODLES: ORIGINAL · FAN-MADE", font=MS(20, 700), fill=(235, 235, 235))
    out = img.convert("RGB")
    if t < .12: out = Image.fromarray((np.asarray(out, np.float32) * ease(t / .12)).astype(np.uint8))
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
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
