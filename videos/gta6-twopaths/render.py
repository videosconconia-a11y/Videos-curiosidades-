# "Two Paths" meme → epic GTA 6 edit. Part 1 (0–7 s): original cartoon fork in the road — the crowd walks the right path
# (sign: FORTNITE / TOKEN PIRATA), one guy ("ME") breaks away and sprints down the left path (sign: GTA 6); camera pushes
# into the glowing left path → white flash. Part 2 (7 s →): beat-synced hard-cut edit of official Rockstar images
# (120 BPM, zoom punch, letterbox, RGB-split hits) ending on "GTA VI" + FOLLOW. Usage: still <t>... | video <w> <n>
import sys, os, math, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, S = 1080, 1920, 30, 2
FD = os.path.join(HERE, "fonts")
@lru_cache(maxsize=64)
def MS(s, w=800):
    f = ImageFont.truetype(os.path.join(FD, "Montserrat-VF.ttf"), int(s))
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f
@lru_cache(maxsize=32)
def ANTON(s): return ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), int(s))
INK = (20, 16, 22); WHITE = (255, 255, 255); PINK = (255, 60, 150); ORANGE = (255, 150, 40); YEL = (255, 214, 0)
def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def ein(p): p = min(max(p, 0), 1); return p ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)

T_SPLIT, T_PUSH, T_EDIT = 3.0, 5.4, 7.0                  # hero breaks away / camera push / edit starts
BEAT = 0.5
EDIT = ["Vice_City_15", "Leonida_Keys_01", "Jason_and_Lucia_16", "Vice_City_17", "Mount_Kalaga_National_Park_04", "Grassrivers_04",
        "ULTIMATE_EDITION_SQUALO_01", "Vice_City_08", "Lucia_Caminos_13", "Jason_Duval_17", "Vice_City_01", "Leonida_Keys_05",
        "ULTIMATE_EDITION_GROTTI_CHEETAH_01", "Jason_and_Lucia_14", "Vice_City_26", "Vice_City_02", "Vice_City_24",
        "VINTAGE_VICE_CITY_PACK_02", "Leonida_Keys_04", "Vice_City_06", "Jason_Lucia_Rooftop_portrait", "GTAVI_Launch_Trailer_poster"]
FOCAL = {"Lucia_Caminos_13": .32, "Jason_Duval_17": .35, "Vice_City_24": .35, "Jason_and_Lucia_16": .55, "Vice_City_06": .42}
# cut lengths in beats: steady, then a double-time burst, then the final hold
CUTS = [2, 1, 1, 1, 1, 1, 1, 2, .5, .5, .5, .5, 1, 1, 1, .5, .5, .5, .5, 1, 2]
TITLE_DUR = 3.0
EDIT_LEN = sum(CUTS) * BEAT
TOTAL = T_EDIT + EDIT_LEN + TITLE_DUR

# ======================================================= PART 1: the fork
HOR = 700; FORK = (540, 1260); LFAR = (250, HOR + 20); RFAR = (830, HOR + 20)
def depth(y): return max(.12, (y - HOR) / (H - HOR)) * 1.25
def lerp(a, b, k): return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
def path_point(v, side):
    """v in [0,1): trunk from bottom to fork; v in [1,2]: branch to the far end"""
    if v < 1: return lerp((540, H + 80), FORK, v)
    k = 1 - (1 - (v - 1)) ** 1.6
    return lerp(FORK, RFAR if side == "R" else LFAR, k)

@lru_cache(maxsize=1)
def fork_bg():
    img = Image.new("RGB", (W * S, H * S)); d = ImageDraw.Draw(img)
    for i in range(0, HOR, 10):
        k = i / HOR; d.rectangle([0, i * S, W * S, (i + 10) * S], fill=(int(90 + 120 * k), int(150 + 60 * k), int(230 - 20 * k)))
    # distant hills + left-path glow (sunset over GTA side)
    d.ellipse([(LFAR[0] - 420) * S, (HOR - 260) * S, (LFAR[0] + 420) * S, (HOR + 260) * S], fill=(255, 150, 110))
    for i in range(HOR, H, 10):
        k = (i - HOR) / (H - HOR); d.rectangle([0, i * S, W * S, (i + 10) * S], fill=(int(70 + 40 * k), int(150 + 40 * k), int(70 + 20 * k)))
    d.polygon([(0, HOR * S), (260 * S, (HOR - 90) * S), (560 * S, HOR * S)], fill=(90, 130, 110))
    d.polygon([(520 * S, HOR * S), (850 * S, (HOR - 130) * S), (1080 * S, (HOR - 40) * S), (1080 * S, HOR * S)], fill=(100, 140, 120))
    def road(pts_l, pts_r, col):
        d.polygon([(x * S, y * S) for x, y in pts_l + pts_r[::-1]], fill=col)
    # trunk
    road([(300, H), (470, FORK[1])], [(780, H), (610, FORK[1])], (215, 190, 140))
    # right branch (wide, worn) and left branch (narrow, dark, glowing at the end)
    road([(470, FORK[1]), (RFAR[0] - 30, RFAR[1])], [(700, FORK[1] + 30), (RFAR[0] + 30, RFAR[1])], (225, 200, 150))
    road([(380, FORK[1] + 30), (LFAR[0] - 14, LFAR[1])], [(560, FORK[1]), (LFAR[0] + 14, LFAR[1])], (150, 120, 120))
    # grass tufts
    rng = np.random.default_rng(3)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(HOR + 20, H); s = depth(y) * 10
        d.line([(x * S, y * S), ((x - s * .4) * S, (y - s) * S)], fill=(50, 120, 55), width=max(1, int(s * .4 * S)))
    img = img.resize((W, H), Image.LANCZOS)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([LFAR[0] - 260, LFAR[1] - 230, LFAR[0] + 260, LFAR[1] + 200], fill=(255, 80, 170, 150))
    img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(60)))
    return img

def person(d, x, y, s, col, t, ph, run=False, look=0, hero=False):
    """simple cartoon walker, feet at (x,y), s = scale"""
    sw = math.sin(t * (14 if run else 7) + ph); bob = abs(sw) * 6 * s
    h = 150 * s; y -= bob
    for k in (-1, 1):                                   # legs
        lx = x + k * 14 * s + (sw * k * (22 if run else 12) * s)
        d.line([(x + k * 10 * s, y - h * .38), (lx, y)], fill=INK, width=max(2, int(12 * s)))
    d.rounded_rectangle([x - 26 * s, y - h * .78, x + 26 * s, y - h * .34], radius=int(18 * s) + 1, fill=col, outline=INK, width=max(1, int(4 * s)))
    for k in (-1, 1):                                   # arms
        ax = x + k * 26 * s; d.line([(ax, y - h * .7), (ax + k * 10 * s - sw * k * (24 if run else 12) * s, y - h * .45)], fill=INK, width=max(2, int(9 * s)))
    hr = 24 * s; hx = x + look * 8 * s; hy = y - h * .78 - hr
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(255, 205, 165), outline=INK, width=max(1, int(4 * s)))
    if hero:
        d.ellipse([hx - hr * 1.6, hy - hr * 1.6, hx + hr * 1.6, hy + hr * 1.6], outline=YEL, width=max(2, int(6 * s)))

CROWD = [(i * .13 % 2.0, ["#6aa", "#c66", "#69c", "#cc6", "#9c6", "#c9c", "#aaa"][i % 7], i * .9) for i in range(30)]
def hexc(h): h = h.lstrip("#"); h = "".join(c * 2 for c in h) if len(h) == 3 else h; return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def sign(img, x, y, lines, cols, sizes, k, glow=None, tilt=0):
    if k <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); sc = back(min(1, k))
    w = max(d.textlength(s, font=ANTON(sz)) for s, sz in zip(lines, sizes)) + 70; h = sum(sizes) * 1.2 + 50
    w, h = w * sc, h * sc
    d.rectangle([x - 10, y + h / 2, x + 10, HOR + 30], fill=(110, 75, 45))
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], 18, fill=(250, 245, 235, 255), outline=INK, width=8)
    yy = y - h / 2 + 25 * sc
    for s_, c, sz in zip(lines, cols, sizes):
        f = ANTON(max(1, int(sz * sc))); d.text((x - d.textlength(s_, font=f) / 2, yy), s_, font=f, fill=c); yy += sz * 1.2 * sc
    if glow:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle([x - w / 2 - 30, y - h / 2 - 30, x + w / 2 + 30, y + h / 2 + 30], 30, fill=glow)
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
    img.alpha_composite(lay.rotate(tilt, center=(x, y), resample=Image.BICUBIC))

def label(d, x, y, s, col):
    f = ANTON(54); w = d.textlength(s, font=f)
    d.rounded_rectangle([x - w / 2 - 18, y - 8, x + w / 2 + 18, y + 70], 16, fill=col, outline=INK, width=6)
    d.polygon([(x - 14, y + 70), (x + 14, y + 70), (x, y + 92)], fill=col, outline=INK)
    d.text((x - w / 2, y), s, font=f, fill=WHITE if col != YEL else INK)

def part1(t):
    img = fork_bg().copy(); d = ImageDraw.Draw(img)
    people = []
    for v0, col, ph in CROWD:                         # crowd keeps walking toward the right path
        v = (v0 + t * .16) % 2.0; x, y = path_point(v, "R"); x += math.sin(ph * 3) * 70 * depth(y)
        people.append((y, x, depth(y), hexc(col), ph, False))
    # hero: walks with the crowd, then sprints down the left branch
    if t < T_SPLIT: hv = .55 + t * .16; hx, hy = path_point(hv, "R"); run = False
    else:
        k = (t - T_SPLIT) / 2.6; hv = 1.03 + .9 * (k * .6 + .4 * ease(k)) if k < 1 else 1.93
        x0, y0 = path_point(.55 + T_SPLIT * .16, "R"); x1, y1 = path_point(hv, "L"); m = min(1, (t - T_SPLIT) / .35)
        hx, hy = x0 + (x1 - x0) * m if m < 1 else x1, y0 + (y1 - y0) * m if m < 1 else y1; run = True
    people.append((hy, hx, depth(hy) * 1.35, (230, 40, 40), 0, True))
    signs_done = False
    for y, x, s, col, ph, hero in sorted(people, key=lambda p: p[0]):
        if not signs_done and y > 760:
            sign(img, 800, 420, ["FORTNITE", "TOKEN PIRATA"], [(60, 110, 230), (200, 50, 50)], [96, 62], (t - .2) / .3, tilt=-3)
            sign(img, 280, 440, ["GTA 6"], [PINK], [120], (t - .55) / .3, glow=(255, 80, 170, 160), tilt=3)
            d = ImageDraw.Draw(img); signs_done = True
        look = -1 if (not hero and T_SPLIT + .3 < t) else 0
        if hero and t >= T_SPLIT:                         # dust puffs + speed lines behind the runner
            for k_ in range(4):
                ph_ = (t * 3 + k_ / 4) % 1; r_ = (10 + 30 * ph_) * s
                d.ellipse([x + 30 * s + ph_ * 60 * s - r_, y - r_ * .6 + ph_ * 20 * s, x + 30 * s + ph_ * 60 * s + r_, y + r_ * .6 + ph_ * 20 * s], fill=(235, 220, 190))
            for k_ in range(3): d.line([(x + 40 * s, y - (60 + k_ * 35) * s), (x + 120 * s, y - (40 + k_ * 35) * s)], fill=WHITE, width=max(2, int(6 * s)))
        person(d, x, y, s, col, t, ph, run=hero and t >= T_SPLIT, look=look, hero=hero)
    if 1.0 < t < T_PUSH:
        label(d, 820, 1000, "EVERYONE", (60, 110, 230))
        hs = depth(hy); label(d, hx, hy - 260 * hs - 120, "ME", (230, 40, 40))
    if T_SPLIT - .5 < t < T_SPLIT + .4:
        d.text((hx + 40, hy - 330 * depth(hy)), "?!", font=ANTON(90), fill=YEL, stroke_width=6, stroke_fill=INK)
    # camera push into the left path + light bloom, then white flash
    if t > T_PUSH:
        k = ein((t - T_PUSH) / (T_EDIT - T_PUSH)); z = 1 + 3.2 * k; cx, cy = LFAR[0] + 40, LFAR[1] + 120
        cw, ch = W / z, H / z; cx = min(max(cx, cw / 2), W - cw / 2); cy = min(max(cy, ch / 2), H - ch / 2)
        img = img.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        arr = np.asarray(img.convert("RGB"), np.float32); arr = arr + (255 - arr) * min(1, k ** 2 * 1.1)
        img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    return img.convert("RGB")

# ======================================================= PART 2: the edit
@lru_cache(maxsize=6)
def load(prefix):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", prefix + ".*jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 2200 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im
def view(key, p, z0, z1, px):
    im = load(key); z = z0 + (z1 - z0) * p; ch = im.height / z; cw = ch * W / H
    if cw > im.width: cw = im.width / z; ch = cw * H / W
    cx = im.width * FOCAL.get(key, .5) + px * (p - .5) * cw * .3
    cx = min(max(cx, cw / 2), im.width - cw / 2); cy = im.height / 2
    return im.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
STARTS = np.cumsum([0] + [c * BEAT for c in CUTS])[:-1] + T_EDIT
_g = np.linspace(-1, 1, W)[None, :]; _v = np.linspace(-1, 1, H)[:, None]
VIG = np.clip(1.15 - (_g ** 2 + _v ** 2) * .45, .45, 1)[..., None].astype(np.float32)
def grade(a):
    l = a.mean(-1, keepdims=True); a = (a - 128) * 1.12 + 128; a = l + (a - l) * 1.18
    a = a + (l / 255 - .5) * np.array([18, 2, -16], np.float32); return a * VIG
def part2(t):
    if t >= T_EDIT + EDIT_LEN: return title(t - T_EDIT - EDIT_LEN)
    i = int(np.searchsorted(STARTS, t, side="right") - 1); a = STARTS[i]; dur = CUTS[i] * BEAT; age = t - a; p = age / dur
    key = EDIT[i % len(EDIT)]; z0, z1 = (1.0, 1.12) if i % 2 == 0 else (1.12, 1.0)
    v = view(key, p, z0, z1, 1 if i % 3 else -1)
    if age < .14:                                                   # zoom punch on every cut
        z = 1 + .1 * (1 - eout(age / .14)); cw, ch = W / z, H / z
        v = v.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    arr = grade(np.asarray(v, np.float32))
    if age < 1 / FPS + 1e-6: arr = arr * 1.25 + 25                 # 1-frame flash
    if age < .1 and CUTS[i] <= .5:                                  # RGB split on the fast cuts
        s = int(18 * (1 - age / .1)); arr[..., 0] = np.roll(arr[..., 0], s, 1); arr[..., 2] = np.roll(arr[..., 2], -s, 1)
    if t - T_EDIT < .35: arr = arr + (255 - arr) * (1 - (t - T_EDIT) / .35)   # out of the white flash
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    bar = 130; d.rectangle([0, 0, W, bar], fill=(0, 0, 0)); d.rectangle([0, H - bar, W, H], fill=(0, 0, 0))   # letterbox
    if i == 0:
        k = eout(age / .4); f = ANTON(96); s = "WELCOME TO LEONIDA"; w = d.textlength(s, font=f)
        d.text((W / 2 - w / 2, 1450 + (1 - k) * 40), s, font=f, fill=(255, 255, 255, int(255 * k)), stroke_width=6, stroke_fill=INK)
    d.text((30, 30), "IMAGES © ROCKSTAR GAMES · FAN EDIT", font=MS(22, 700), fill=(220, 220, 220))
    return img
def title(age):
    img = view("Jason_Lucia_Lock_And_Load_portrait", min(1, age / TITLE_DUR), 1.0, 1.08, 0)
    arr = grade(np.asarray(img, np.float32)) * .55; img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    k = eout(age / .5); sp = 60 * (1 - k) + 18; f = ANTON(300); s = "GTA VI"
    ws = [d.textlength(c, font=f) for c in s]; x = (W - sum(ws) - sp * (len(s) - 1)) / 2
    for c, w_ in zip(s, ws):
        for yy in range(0, 330, 6):
            pass
        d.text((x, 640), c, font=f, fill=(255, 255, 255, int(255 * k))); x += w_ + sp
    g = lay.filter(ImageFilter.GaussianBlur(26)); tint = Image.new("RGBA", (W, H), (255, 70, 160, 0)); tint.putalpha(g.getchannel("A"))
    img.alpha_composite(tint); img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    if age > .9:
        kk = back(min(1, (age - .9) / .3)); bw = 620 * kk
        d.rounded_rectangle([W / 2 - bw / 2, 1100, W / 2 + bw / 2, 1250], 70, fill=(235, 50, 50), outline=INK, width=8)
        if kk > .7: d.text((W / 2 - d.textlength("FOLLOW", font=ANTON(110)) / 2, 1112), "FOLLOW", font=ANTON(110), fill=WHITE)
        d.text((W / 2 - d.textlength("for more GTA 6", font=MS(56, 900)) / 2, 1290), "for more GTA 6", font=MS(56, 900), fill=WHITE)
    d.rectangle([0, 0, W, 130], fill=(0, 0, 0)); d.rectangle([0, H - 130, W, H], fill=(0, 0, 0))
    out = img.convert("RGB")
    if TITLE_DUR - age < .4: out = Image.fromarray((np.asarray(out, np.float32) * ease((TITLE_DUR - age) / .4)).astype(np.uint8))
    return out

def frame(t, fi=None):
    out = part1(t) if t < T_EDIT else part2(t)
    if t < .15: out = Image.fromarray((np.asarray(out, np.float32) * ease(t / .15)).astype(np.uint8))
    return out

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    if mode == "still":
        for s in sys.argv[2:]: frame(float(s)).save(os.path.join(HERE, f"still_{s}.jpg"), quality=88)
    elif mode == "video":
        wk, nw = int(sys.argv[2]), int(sys.argv[3]); nf = int(round(TOTAL * FPS))
        per = math.ceil(nf / nw); f0, f1 = wk * per, min(nf, (wk + 1) * per)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", os.path.join(HERE, f"part_{wk}.mp4")], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame(fi / FPS, fi).tobytes())
            if (fi - f0) % 60 == 0: print(f"w{wk} {fi - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
