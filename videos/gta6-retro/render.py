# "GTA 6 on Retro Consoles (It Looks TERRIBLE)" — official GTA VI images converted to each console's real limits:
# Atari 2600 (blocky 40×30, tiny palette), Game Boy (160×144, 4 greens, Bayer dither), NES (8-bit, ~13 colours,
# error-diffusion dither), PS1 (320×240, 15-bit colour, ordered dither, wobbling vertices), N64 (bilinear smear + fog),
# PS5 (clean 4K-ish). Shown on drawn generic CRT TVs / a generic handheld (no console logos). Outro = 6-screen vote grid.
import sys, os, math, json, glob, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
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
INK = (12, 12, 16); WHITE = (255, 255, 255); YEL = (255, 214, 0); RED = (240, 60, 60)
TM = json.load(open(os.path.join(HERE, "timings.json"))); TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
def clean(w): return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'’").replace("’", "'")
def word_time(seg, word): return [w["a"] for w in SEGT[seg]["words"] if clean(w["w"]) == clean(word)][0]
WIN = []
for i, (sd, sg) in enumerate(zip(SEGMENTS, TM["segments"])):
    a = 0.0 if i == 0 else sg["a"] - .1
    b = TM["segments"][i + 1]["a"] - .1 if i + 1 < len(SEGMENTS) else TOTAL
    WIN.append((a, b, sd["shots"][0][0], sd["id"]))
def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def eout(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def back(p, s=1.7): p = min(max(p, 0), 1) - 1; return 1 + p * p * ((s + 1) * p + s)

IMGS = {"atari": ["Lucia_Caminos_13", "Vice_City_15"], "gameboy": ["Vice_City_15", "Vice_City_01"], "nes": ["Jason_Duval_17", "Vice_City_24"],
        "ps1": ["ULTIMATE_EDITION_GROTTI_CHEETAH_01", "Jason_and_Lucia_16"], "n64": ["Vice_City_08", "Leonida_Keys_01"],
        "ps5": ["Mount_Kalaga_National_Park_04", "Jason_Lucia_Rooftop_portrait"], "intro": ["GTAVI_Launch_Trailer_poster"]}
FOC = {"Lucia_Caminos_13": .3, "Jason_Duval_17": .35, "Vice_City_24": .35, "Jason_and_Lucia_16": .55, "Jason_Lucia_Rooftop_portrait": .5}
LABEL = {"atari": ("ATARI 2600", "1977"), "gameboy": ("GAME BOY", "1989"), "nes": ("NES", "8-BIT"), "ps1": ("PLAYSTATION 1", "1994"),
         "n64": ("NINTENDO 64", "64-BIT"), "ps5": ("PS5", "2020")}

@lru_cache(maxsize=12)
def load(key):
    f = sorted(glob.glob(os.path.join(HERE, "assets", "official", key + ".*jpg")))[0]
    im = Image.open(f).convert("RGB"); s = 1400 / max(im.height, 1)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im
def crop(key, aspect, p, outw, outh):
    im = load(key); z = 1.0 + .12 * p; ch = im.height / z; cw = ch * aspect
    if cw > im.width: cw = im.width / z; ch = cw / aspect
    cx = im.width * FOC.get(key, .5) + (p - .5) * cw * .25; cx = min(max(cx, cw / 2), im.width - cw / 2); cy = im.height / 2
    return im.resize((outw, outh), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - .5
GB = np.array([[15, 56, 15], [48, 98, 48], [139, 172, 15], [155, 188, 15]], np.float32)
ATARI = Image.new("P", (1, 1)); ATARI.putpalette([0, 0, 0, 200, 72, 72, 228, 160, 80, 232, 232, 74, 72, 160, 72, 66, 72, 200, 160, 160, 160, 236, 236, 236] + [0] * 744)
def console_img(con, key, p, t, sw, sh):
    pq = round(p * 12) / 12                                      # stepped pan = low framerate feel on retro
    if con == "atari":
        im = crop(key, 4 / 3, pq, 40, 30).quantize(palette=ATARI, dither=Image.Dither.NONE).convert("RGB")
        return im.resize((sw, sh), Image.NEAREST)
    if con == "gameboy":
        im = np.asarray(crop(key, 10 / 9, pq, 160, 144).convert("L"), np.float32) / 255
        idx = np.clip(np.floor(im * 4 + np.tile(BAYER, (36, 40)) * .9), 0, 3).astype(int)
        return Image.fromarray(GB[idx].astype(np.uint8)).resize((sw, sh), Image.NEAREST)
    if con == "nes":
        im = crop(key, 4 / 3, pq, 72, 54).quantize(colors=10, dither=Image.Dither.FLOYDSTEINBERG).convert("RGB")
        return im.resize((sw, sh), Image.NEAREST)
    if con == "ps1":
        a = np.asarray(crop(key, 4 / 3, p, 160, 120), np.float32)
        a = np.floor((a + np.tile(BAYER, (30, 40))[..., None] * 24) / 24) * 24          # 15-bit + ordered dither
        # affine wobble: rows/cols of 16px blocks jitter by whole pixels every frame
        rng = np.random.default_rng(int(t * 30)); out = a.copy()
        for y in range(0, 120, 8):
            out[y:y + 8] = np.roll(a[y:y + 8], int(rng.integers(-2, 3) + 3 * math.sin(t * 3 + y * .1)), 1)
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((sw, sh), Image.NEAREST)
    if con == "n64":
        im = crop(key, 4 / 3, p, 320, 240).filter(ImageFilter.GaussianBlur(1.6)).resize((160, 120), Image.BILINEAR).resize((sw, sh), Image.BILINEAR)
        a = np.asarray(im, np.float32); fog = np.array([170, 175, 185], np.float32)
        g = np.linspace(.75, .35, sh)[:, None, None]; a = a * (1 - g) + fog * g
        return Image.fromarray(a.astype(np.uint8))
    return crop(key, sw / sh, p, sw, sh)

def crt(img, screen, label=None):
    """generic CRT TV, screen = PIL image placed in a 4:3 tube"""
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = 60, 520, 1020, 1300
    d.rounded_rectangle([x0, y0, x1, y1], 60, fill=(55, 50, 48), outline=INK, width=8)
    d.rounded_rectangle([x0 + 30, y1 - 10, x0 + 160, y1 + 50], 16, fill=(40, 36, 34)); d.rounded_rectangle([x1 - 160, y1 - 10, x1 - 30, y1 + 50], 16, fill=(40, 36, 34))
    sx0, sy0, sx1, sy1 = x0 + 50, y0 + 45, x1 - 50, y1 - 105
    sw, sh = sx1 - sx0, sy1 - sy0
    scr = screen.resize((sw, sh), Image.NEAREST) if screen.size != (sw, sh) else screen
    a = np.asarray(scr, np.float32)
    a[::3] *= .72                                              # scanlines
    yy, xx = np.mgrid[0:sh, 0:sw]; vg = 1 - .35 * (((xx - sw / 2) / (sw / 2)) ** 2 + ((yy - sh / 2) / (sh / 2)) ** 2) ** 1.5
    a = a * vg[..., None]
    m = Image.new("L", (sw, sh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw - 1, sh - 1], 40, fill=255)
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (sx0, sy0), m)
    for i, c in enumerate(((200, 60, 60), (60, 200, 90))): d.ellipse([x1 - 140 + i * 50, y1 - 75, x1 - 110 + i * 50, y1 - 45], fill=c)
def handheld(img, screen):
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = 230, 430, 850, 1480
    d.rounded_rectangle([x0, y0, x1, y1], 40, fill=(198, 196, 190), outline=INK, width=8)
    d.rounded_rectangle([x0 + 40, y0 + 40, x1 - 40, y0 + 560], 24, fill=(90, 90, 105))
    sx0, sy0 = x0 + 110, y0 + 90; sw, sh = 400, 360
    img.paste(screen.resize((sw, sh), Image.NEAREST), (sx0, sy0))
    d.ellipse([x0 + 70, y0 + 230, x0 + 90, y0 + 250], fill=(220, 40, 40))
    cx, cy = x0 + 160, y0 + 760; d.rectangle([cx - 70, cy - 22, cx + 70, cy + 22], fill=INK); d.rectangle([cx - 22, cy - 70, cx + 22, cy + 70], fill=INK)
    for (bx, by) in ((x1 - 200, y0 + 790), (x1 - 100, y0 + 730)): d.ellipse([bx - 45, by - 45, bx + 45, by + 45], fill=(160, 30, 80), outline=INK, width=4)
    for k in range(6): d.line([x1 - 160 + k * 22, y1 - 170, x1 - 210 + k * 22, y1 - 60], fill=(150, 148, 142), width=8)

def label_card(img, con, age):
    d = ImageDraw.Draw(img); name, year = LABEL[con]; k = back(min(1, age / .3))
    f = ANTON(int(130 * k) + 1); d.text((W / 2 - d.textlength(name, font=f) / 2, 150), name, font=f, fill=WHITE, stroke_width=8, stroke_fill=INK)
    f2 = ANTON(80); w = d.textlength(year, font=f2) + 50
    d.rounded_rectangle([W / 2 - w / 2, 320, W / 2 + w / 2, 420], 20, fill=YEL, outline=INK, width=6); d.text((W / 2 - w / 2 + 25, 322), year, font=f2, fill=INK)

def bg(t, con):
    cols = {"intro": ((30, 20, 50), (10, 8, 20)), "atari": ((70, 40, 20), (20, 12, 8)), "gameboy": ((60, 80, 40), (15, 22, 10)), "nes": ((90, 20, 30), (25, 6, 10)),
            "ps1": ((40, 40, 70), (10, 10, 20)), "n64": ((30, 60, 40), (8, 18, 12)), "ps5": ((20, 30, 70), (5, 8, 25)), "outro": ((40, 20, 60), (10, 6, 20))}[con]
    g = np.linspace(0, 1, H)[:, None, None]; a = np.array(cols[0]) * (1 - g) + np.array(cols[1]) * g
    img = Image.fromarray(np.repeat(a, W, 1).astype(np.uint8)); d = ImageDraw.Draw(img)
    for x in range(-W, W * 2, 90):                                # moving retro grid
        off = (t * 40) % 90; d.line([(x + off, 1350), (W / 2 + (x + off - W / 2) * 3, H)], fill=(255, 255, 255, 30), width=2)
    for k in range(8): y = 1350 + (k ** 1.8) * 9 + (t * 20 % 9); d.line([(0, y), (W, y)], fill=(80, 80, 110), width=2)
    return img

def caption(img, t):
    g = None
    for sd, sg in zip(SEGMENTS, TM["segments"]):
        ws = sg["words"]; cur = []
        for i, w in enumerate(ws):
            cur.append(w)
            if w["w"][-1] in ".?!," or len(cur) >= 3 or i == len(ws) - 1:
                if cur[0]["a"] - .05 <= t: g = (cur, sd["hl"], sg)
                cur = []
    if not g: return
    ws, hl, sg = g
    nxt = [x["a"] for x in TM["segments"] if x["a"] > ws[-1]["b"]]
    if t > ws[-1]["b"] + .45 or (nxt and t >= nxt[0] - .1): return
    NUM = {"six": "6", "twenty-six": "2600", "hundred,": "", "nineteen": "19", "seventy-seven.": "77.", "eighty-nine.": "89.", "ninety-four.": "94.",
           "sixty-four.": "64.", "thirty": "30", "eight-bit": "8-BIT", "one,": "1,"}
    toks = []
    for w in ws:
        s_ = NUM.get(w["w"].lower(), w["w"])
        if s_ == "": continue
        if toks and toks[-1][1] == "19": toks[-1] = (toks[-1][0], "19" + s_); continue
        toks.append((w, s_.upper()))
    d = ImageDraw.Draw(img); f = ANTON(96); widths = [d.textlength(s, font=f) for _, s in toks]; sp = 22
    while sum(widths) + sp * (len(toks) - 1) > W - 100: f = ANTON(f.size - 4); widths = [d.textlength(s, font=f) for _, s in toks]
    x = (W - sum(widths) - sp * (len(toks) - 1)) / 2; y = 1560; age = t - ws[0]["a"]; pop = back(min(1, age / .1)) if age > 0 else 0
    for (w, s_), wd in zip(toks, widths):
        on = w["a"] - .03 <= t
        d.text((x, y + (1 - pop) * 22), s_, font=f, fill=(YEL if clean(w["w"]) in {clean(h) for h in hl} and on else (WHITE if on else (210, 210, 210))), stroke_width=9, stroke_fill=INK)
        x += wd + sp

def outro(img, t, age):
    d = ImageDraw.Draw(img); cons = ["atari", "gameboy", "nes", "ps1", "n64", "ps5"]
    k = back(min(1, age / .3)); f = ANTON(int(100 * k) + 1); s = "WHICH ONE?"
    d.text((W / 2 - d.textlength(s, font=f) / 2, 140), s, font=f, fill=YEL, stroke_width=8, stroke_fill=INK)
    for i, c in enumerate(cons):
        kk = eout((age - .2 - i * .12) / .3)
        if kk <= 0: continue
        cx, cy = 290 + (i % 2) * 500, 470 + (i // 2) * 330; sw, sh = 420, 300
        scr = console_img(c, IMGS[c][0], .5, t, sw, sh if c != "gameboy" else int(sw * .9))
        img.paste(scr.resize((sw, sh)), (int(cx - sw / 2), int(cy - sh / 2))); d.rectangle([cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2], outline=WHITE, width=6)
        d.ellipse([cx - sw / 2 - 30, cy - sh / 2 - 30, cx - sw / 2 + 50, cy - sh / 2 + 50], fill=RED, outline=INK, width=5)
        d.text((cx - sw / 2 - 2, cy - sh / 2 - 26), str(i + 1), font=ANTON(66), fill=WHITE)
        lab = LABEL[c][0]; d.text((cx - d.textlength(lab, font=MS(30, 900)) / 2, cy + sh / 2 + 8), lab, font=MS(30, 900), fill=WHITE, stroke_width=3, stroke_fill=INK)

def frame(t, fi=None):
    i = max(k for k, w in enumerate(WIN) if w[0] <= t or k == 0); a, b, con, sid = WIN[i]; age = t - a; p = age / max(b - a, .1)
    img = bg(t, con)
    if con == "intro":
        rng = np.random.default_rng(int(t * 30)); stat = Image.fromarray((rng.random((240, 320)) * 255).astype(np.uint8)).convert("RGB")
        scr = stat if age < .8 else console_img("ps5", "GTAVI_Launch_Trailer_poster", p, t, 860, 630)
        crt(img, scr); d = ImageDraw.Draw(img); k = back(min(1, (age - .3) / .3))
        if k > 0:
            f = ANTON(int(120 * k) + 1); s = "GTA 6"; d.text((W / 2 - d.textlength(s, font=f) / 2, 150), s, font=f, fill=WHITE, stroke_width=8, stroke_fill=INK)
            f2 = ANTON(int(90 * k) + 1); s = "RETRO EDITION"; d.text((W / 2 - d.textlength(s, font=f2) / 2, 300), s, font=f2, fill=YEL, stroke_width=7, stroke_fill=INK)
    elif con == "outro":
        outro(img, t, age)
    else:
        key = IMGS[con][0] if p < .5 else IMGS[con][1]; pp = (p * 2) % 1
        if con == "gameboy": handheld(img, console_img(con, key, pp, t, 160, 144))
        else: crt(img, console_img(con, key, pp, t, 860, 630))
        label_card(img, con, age)
        if con == "ps5":
            tw = word_time("ps5", "thirty") - a
            if age > tw - .1:
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); kk = back(min(1, (age - tw + .1) / .25)); f = ANTON(int(170 * kk) + 1)
                s = "30 FPS"; w = dl.textlength(s, font=f); dl.rounded_rectangle([W / 2 - w / 2 - 30, 760, W / 2 + w / 2 + 30, 760 + f.size * 1.2], 20, outline=RED + (255,), width=14)
                dl.text((W / 2 - w / 2, 765), s, font=f, fill=RED + (255,))
                img = img.convert("RGBA"); img.alpha_composite(lay.rotate(-8, center=(W / 2, 880), resample=Image.BICUBIC)); img = img.convert("RGB")
    if i and age < .15:                                          # channel-change static between consoles
        rng = np.random.default_rng(int(t * 60)); n = (rng.random((H // 4, W // 4)) * 255).astype(np.uint8)
        st = Image.fromarray(n).resize((W, H), Image.NEAREST).convert("RGB"); img = Image.blend(img, st, .55 * (1 - age / .15))
    caption(img, t)
    ImageDraw.Draw(img).text((30, 30), "IMAGES © ROCKSTAR GAMES · RETRO FILTERS: FAN-MADE", font=MS(20, 700), fill=(230, 230, 230))
    if t < .12: img = Image.fromarray((np.asarray(img, np.float32) * ease(t / .12)).astype(np.uint8))
    return img

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
