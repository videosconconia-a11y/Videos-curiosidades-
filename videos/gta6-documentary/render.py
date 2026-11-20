# "GTA 6: The $1 Billion Gamble" — long-form YouTube documentary, 16:9 1920x1080, 24 fps.
# Identity "PRESTIGE DOC": slow Ken Burns on official Rockstar images with soft cross-dissolves, warm/teal grade, grain,
# serif chapter cards, big-number callouts with sources, date stamps, quote cards, timeline, bar chart, list, subscribe card.
# Every on-screen figure has a source tag; estimates are labelled. Usage: still <t>... | video <worker> <nworkers>
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

W, H, FPS = 1920, 1080, 24
FD = os.path.join(HERE, "fonts")
@lru_cache(maxsize=64)
def VF(name, s, w=None):
    f = ImageFont.truetype(os.path.join(FD, name), int(s))
    if w:
        try: f.set_variation_by_axes([w])
        except Exception: pass
    return f
MS = lambda s, w=700: VF("Montserrat-VF.ttf", s, w)
OSW = lambda s, w=600: VF("Oswald-VF.ttf", s, w)
SERIF = lambda s: VF("DMSerifDisplay-Regular.ttf", s)
SERIFI = lambda s: VF("DMSerifDisplay-Italic.ttf", s)
ANTON = lambda s: VF("Anton-Regular.ttf", s)
GOLD = (236, 190, 110); PINK = (255, 80, 160); WHITE = (255, 255, 255); INK = (10, 10, 14); GREY = (200, 200, 205); RED = (230, 60, 60)

TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word):
    for w in SEGT[seg]["words"]:
        if clean(w["w"]) == clean(word): return w["a"]
    raise KeyError((seg, word))
# segment windows: from previous end to this segment's next start
WIN = []
for i, (sd, sg) in enumerate(zip(SEGMENTS, TM["segments"])):
    a = 0.0 if i == 0 else TM["segments"][i]["a"] - 0.25
    b = TM["segments"][i + 1]["a"] - 0.25 if i + 1 < len(SEGMENTS) else TOTAL
    WIN.append((a, b, sd, sg))
CH_NOW = []
cur = ("", "")
for a, b, sd, sg in WIN:
    if sd["chapter"]: cur = sd["chapter"]
    CH_NOW.append(cur)

def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.4): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)

@lru_cache(maxsize=6)
def load(key):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", key + ".*jpg")))[0]
    return Image.open(f).convert("RGB")
def kb(key, p, seed):
    im = load(key); rng = np.random.default_rng(abs(hash(key)) % 1000 + seed)
    z0, z1 = (1.0, 1.14) if seed % 2 == 0 else (1.14, 1.0); z = z0 + (z1 - z0) * p
    ch = im.height / z; cw = ch * W / H
    if cw > im.width: cw = im.width / z; ch = cw * H / W
    px, py = rng.uniform(-.25, .25), rng.uniform(-.15, .15)
    cx = im.width / 2 + px * (p - .5) * (im.width - cw); cy = im.height / 2 + py * (p - .5) * (im.height - ch)
    cx = min(max(cx, cw / 2), im.width - cw / 2); cy = min(max(cy, ch / 2), im.height - ch / 2)
    return np.asarray(im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)), np.float32)

_x = np.linspace(-1, 1, W)[None, :]; _y = np.linspace(-1, 1, H)[:, None]
VIG = np.clip(1.12 - (_x ** 2 * .55 + _y ** 2 * .8) * .55, .5, 1)[..., None].astype(np.float32)
GRAIN = [np.random.default_rng(k).normal(0, 5, (H // 2, W // 2)).astype(np.float32) for k in range(4)]
def grade(a, fi):
    l = a.mean(-1, keepdims=True); a = (a - 128) * 1.05 + 126; a = l + (a - l) * 1.06
    a = a + (l / 255 - .5) * np.array([14, 3, -12], np.float32)
    g = GRAIN[fi % 4]; a = a + np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    return a * VIG

def background(t, fi, si):
    a, b, sd, sg = WIN[si]; imgs = sd["imgs"]; n = len(imgs); dur = b - a; seg = dur / n
    k = min(n - 1, int((t - a) / seg)); p = (t - a - k * seg) / seg
    arr = kb(imgs[k], min(1, p * .85 + .05), si * 7 + k)
    XF = .7
    if k + 1 < n and (k + 1) * seg - (t - a) < XF:              # dissolve to next image in the segment
        q = 1 - ((k + 1) * seg - (t - a)) / XF; arr = arr * (1 - ease(q)) + kb(imgs[k + 1], .05, si * 7 + k + 1) * ease(q)
    if si > 0 and t - a < XF:                                    # dissolve from the previous segment
        pa, pb, psd, _ = WIN[si - 1]; q = (t - a) / XF
        prev = kb(psd["imgs"][-1], 1.0, (si - 1) * 7 + len(psd["imgs"]) - 1); arr = prev * (1 - ease(q)) + arr * ease(q)
    return arr

# ======================================================= overlays
def panel(d, box, a=170, r=18): d.rounded_rectangle(box, r, fill=(8, 8, 12, a))
def chapter_card(img, num, title, age):
    if age > 2.6: return
    k_in = eout(age / .5); k_out = 1 - ease((age - 2.1) / .5)
    k = min(k_in, k_out)
    if k <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, int(150 * k))); d = ImageDraw.Draw(lay)
    if num: s = f"CHAPTER {num}"; f = OSW(46, 500); d.text((W / 2 - d.textlength(s, font=f) / 2, 380 + (1 - k) * 20), s, font=f, fill=GOLD + (int(255 * k),))
    f = SERIF(118); w = d.textlength(title, font=f)
    while w > W - 200: f = SERIF(f.size - 4); w = d.textlength(title, font=f)
    d.text((W / 2 - w / 2, 450 + (1 - k) * 20), title, font=f, fill=WHITE + (int(255 * k),))
    lw = 600 * eout(age / .8); d.line([(W / 2 - lw / 2, 610), (W / 2 + lw / 2, 610)], fill=GOLD + (int(255 * k),), width=4)
    img.alpha_composite(lay)

def ov_num(img, args, age, slot=0):
    big, lab, src = args; k = eout(age / .4); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0 = 110 + (1 - k) * -60; y0 = 300 + slot * 0
    f = ANTON(170); bw = max(d.textlength(big, font=f), d.textlength(lab, font=OSW(44, 600))) + 80
    panel(d, [x0 - 40, y0 - 30, x0 + bw, y0 + 330], int(170 * k))
    d.text((x0, y0), big, font=f, fill=GOLD + (int(255 * k),))
    d.text((x0, y0 + 205), lab, font=OSW(44, 600), fill=WHITE + (int(255 * k),))
    d.text((x0, y0 + 268), src, font=MS(24, 600), fill=GREY + (int(255 * k),))
    img.alpha_composite(lay)
def ov_tag(img, args, age, idx):
    s = args[0]; k = back(min(1, age / .3)); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = OSW(44, 700); w = d.textlength(s, font=f); x, y = 110, 170 + idx * 86
    d.rounded_rectangle([x, y, x + (w + 50) * k, y + 70], 12, fill=RED + (235,))
    if k > .8: d.text((x + 25, y + 6), s, font=f, fill=WHITE)
    img.alpha_composite(lay)
def ov_date(img, args, age):
    s, cap = args; k = eout(age / .4); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x, y = 110, 760 + (1 - k) * 30
    f = ANTON(110); w = max(d.textlength(s, font=f), d.textlength(cap, font=OSW(36, 500))) + 70
    panel(d, [x - 35, y - 20, x + w, y + 200], int(175 * k))
    d.rectangle([x - 35, y - 20, x - 27, y + 200], fill=GOLD + (int(255 * k),))
    d.text((x, y), s, font=f, fill=WHITE + (int(255 * k),)); d.text((x, y + 140), cap, font=OSW(36, 500), fill=GOLD + (int(255 * k),))
    img.alpha_composite(lay)
def wrap(d, s, f, maxw):
    words = s.split(); lines = []; cur = ""
    for w in words:
        if d.textlength(cur + " " + w, font=f) > maxw and cur: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return lines + [cur]
def ov_quote(img, args, age):
    q, who = args; k = eout(age / .5); lay = Image.new("RGBA", (W, H), (0, 0, 0, int(110 * k))); d = ImageDraw.Draw(lay)
    f = SERIFI(78); lines = wrap(d, "“" + q + "”", f, 1300); h = len(lines) * 96 + 120
    y0 = H / 2 - h / 2 + (1 - k) * 20
    for i, l in enumerate(lines): d.text((W / 2 - d.textlength(l, font=f) / 2, y0 + i * 96), l, font=f, fill=WHITE + (int(255 * k),))
    s = "— " + who; d.text((W / 2 - d.textlength(s, font=OSW(40, 500)) / 2, y0 + len(lines) * 96 + 30), s, font=OSW(40, 500), fill=GOLD + (int(255 * k),))
    img.alpha_composite(lay)
def ov_title(img, args, age):
    t1, t2 = args; k = eout(age / .7); lay = Image.new("RGBA", (W, H), (0, 0, 0, int(120 * k))); d = ImageDraw.Draw(lay)
    f = ANTON(150); d.text((W / 2 - d.textlength(t1, font=f) / 2, 380 + (1 - k) * 30), t1, font=f, fill=GOLD + (int(255 * k),))
    f2 = SERIFI(64); d.text((W / 2 - d.textlength(t2, font=f2) / 2, 590), t2, font=f2, fill=WHITE + (int(255 * k),))
    img.alpha_composite(lay)
def ov_timeline(img, args, age, t, seg_id):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); k = eout(age / .6)
    panel(d, [160, 700, W - 160, 960], int(180 * k)); x0, x1, y = 300, W - 300, 790
    d.line([(x0, y), (x0 + (x1 - x0) * k, y)], fill=WHITE + (200,), width=6)
    for i, (lab, sub) in enumerate(args):
        x = x0 + (x1 - x0) * i / (len(args) - 1); ki = eout((age - .3 - i * .5) / .4)
        if ki <= 0: continue
        col = GOLD if i == len(args) - 1 else (170, 170, 175)
        d.ellipse([x - 18, y - 18, x + 18, y + 18], fill=col + (int(255 * ki),))
        f = OSW(48, 700); d.text((x - d.textlength(lab, font=f) / 2, y + 36), lab, font=f, fill=col + (int(255 * ki),))
        d.text((x - d.textlength(sub, font=MS(28, 600)) / 2, y + 104), sub, font=MS(28, 600), fill=GREY + (int(255 * ki),))
        if i < len(args) - 1 and age > 1.6 + i * .6:
            w = d.textlength(lab, font=f); d.line([(x - w / 2 - 6, y + 70), (x + w / 2 + 6, y + 70)], fill=RED + (255,), width=6)
    img.alpha_composite(lay)
def ov_bars(img, args, age):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); k = eout(age / .5)
    panel(d, [1000, 250, W - 110, 820], int(185 * k)); d.text((1050, 280), "DEVELOPMENT COST", font=OSW(44, 700), fill=WHITE + (int(255 * k),))
    mx = max(v for _, v, _ in args)
    for i, (lab, v, note) in enumerate(args):
        y = 400 + i * 200; kk = eout((age - .3 - i * .5) / 1.0); bw = 640 * v / mx * kk
        d.text((1050, y), lab, font=OSW(46, 700), fill=WHITE + (int(255 * k),))
        d.rounded_rectangle([1050, y + 64, 1050 + max(8, bw), y + 124], 10, fill=(GOLD if i == len(args) - 1 else (150, 150, 160)) + (255,))
        d.text((1050, y + 134), note, font=MS(28, 600), fill=GREY + (int(255 * kk),))
    img.alpha_composite(lay)
def ov_list(img, args, age):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    panel(d, [1180, 220, W - 110, 260 + 110 * len(args)], int(180 * eout(age / .4)))
    for i, s in enumerate(args):
        ki = eout((age - i * .9) / .4)
        if ki <= 0: continue
        y = 250 + i * 110; d.rectangle([1215, y + 12, 1225, y + 66], fill=GOLD + (int(255 * ki),))
        d.text((1250 + (1 - ki) * 30, y), s, font=OSW(56, 600), fill=WHITE + (int(255 * ki),))
    img.alpha_composite(lay)
def ov_subscribe(img, age, t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); k = back(min(1, age / .4))
    bw, bh = 520 * k, 130 * k; cx, cy = W / 2, 820
    d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 26, fill=(230, 33, 23, 255))
    if k > .8: d.text((cx - d.textlength("SUBSCRIBE", font=ANTON(84)) / 2, cy - 52), "SUBSCRIBE", font=ANTON(84), fill=WHITE)
    bx = cx + bw / 2 + 90; sw = math.sin(t * 14) * 10 if age > .6 else 0
    d.polygon([(bx - 40 + sw, cy + 35), (bx + 40 + sw, cy + 35), (bx + 30 + sw * .6, cy - 20), (bx + sw * .3, cy - 50), (bx - 30 + sw * .6, cy - 20)], fill=WHITE)
    img.alpha_composite(lay)

def chrome(img, t, si):
    d = ImageDraw.Draw(img); num, title = CH_NOW[si]
    if title and not WIN[si][2]["chapter"] or (WIN[si][2]["chapter"] and t - WIN[si][0] > 2.6):
        s = (f"CH {num} · " if num else "") + title; d.text((W - 110 - d.textlength(s, font=OSW(30, 500)), 60), s, font=OSW(30, 500), fill=(235, 235, 235))
    d.text((110, 60), "GTA6 SECRETS", font=OSW(30, 700), fill=GOLD)
    src = WIN[si][2].get("src")
    if src:
        s = "Sources: " + src; d.text((110, H - 70), s, font=MS(22, 600), fill=(225, 225, 225))
    d.text((W - 110 - d.textlength("Images © Rockstar Games", font=MS(22, 600)), H - 70), "Images © Rockstar Games", font=MS(22, 600), fill=(225, 225, 225))
    d.rectangle([0, H - 6, W * t / TOTAL, H], fill=GOLD)

def seg_at(t):
    for i, (a, b, sd, sg) in enumerate(WIN):
        if a <= t < b: return i
    return len(WIN) - 1
def frame(t, fi=0):
    si = seg_at(t); a, b, sd, sg = WIN[si]
    arr = grade(background(t, fi, si), fi)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # overlays
    ovs = sd["ov"]; tags = 0
    for j, (kind, word, args) in enumerate(ovs):
        try: t0 = word_time(sd["id"], word) - .15
        except KeyError: t0 = a + .5
        same_next = [word_time(sd["id"], w2) - .15 for (k2, w2, _) in ovs[j + 1:] if k2 == kind or {k2, kind} <= {"num", "quote", "bars", "title", "date"}]
        end = min(same_next) if (same_next and kind != "tag") else b - .15
        if not (t0 <= t < end): continue
        age = t - t0
        if kind == "num": ov_num(img, args, age)
        elif kind == "tag": ov_tag(img, args, age, tags); tags += 1
        elif kind == "date": ov_date(img, args, age)
        elif kind == "quote": ov_quote(img, args, age)
        elif kind == "title": ov_title(img, args, age)
        elif kind == "timeline": ov_timeline(img, args, age, t, sd["id"])
        elif kind == "bars": ov_bars(img, args, age)
        elif kind == "list": ov_list(img, args, age)
        elif kind == "subscribe": ov_subscribe(img, age, t)
    if sd["chapter"]: chapter_card(img, sd["chapter"][0], sd["chapter"][1], t - a)
    chrome(img, t, si)
    out = img.convert("RGB")
    if t < .6: out = Image.fromarray((np.asarray(out, np.float32) * ease(t / .6)).astype(np.uint8))
    if TOTAL - t < 1.2: out = Image.fromarray((np.asarray(out, np.float32) * ease((TOTAL - t) / 1.2)).astype(np.uint8))
    return out

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s), int(float(s) * FPS)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 240 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
