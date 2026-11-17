# Original profile picture for "Leonida Millonario" (no Rockstar assets). 2048x2048 PNG.
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
S = 2048; F = "../videos/gta6-secrets/fonts/"
def font(n, s): return ImageFont.truetype(F + n, s)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
yy = np.linspace(0, 1, S)[:, None]
stops = [(0, (18, 4, 48)), (0.45, (120, 20, 140)), (0.62, (255, 60, 140)), (0.74, (255, 150, 70)), (1, (40, 8, 60))]
sky = np.stack([np.interp(yy, [s[0] for s in stops], [s[1][c] for s in stops]) * np.ones((1, S)) for c in range(3)], -1)
img = to_img(sky).convert("RGBA")
def glow(lay, r, k=1.0):
    g = lay.filter(ImageFilter.GaussianBlur(r))
    if k != 1: a = np.asarray(g).astype(float); a[..., 3] *= k; g = to_img(a)
    img.alpha_composite(g); img.alpha_composite(lay)
# striped synthwave sun
sun = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(sun); cx, cy, R = S / 2, S * 0.60, 640
for y in range(int(cy - R), int(cy + R)):
    u = (y - (cy - R)) / (2 * R); hw = math.sqrt(max(0, R * R - (y - cy) ** 2))
    if u > 0.5 and (y // 14) % (2 + int((1 - u) * 7)) == 0: continue
    d.line([cx - hw, y, cx + hw, y], fill=(255, int(235 - 150 * u), int(80 + 60 * u), 255))
glow(sun, 90, 0.9)
# horizon grid
grid = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(grid); hz = int(S * 0.78)
d.rectangle([0, hz, S, S], fill=(20, 4, 40, 255))
for i in range(-20, 21): d.line([S / 2 + i * 60, hz, S / 2 + i * 380, S], fill=(255, 60, 200, 220), width=6)
for k in range(9):
    y = hz + (S - hz) * (k / 8) ** 1.8; d.line([0, y, S, y], fill=(255, 60, 200, 220), width=6)
glow(grid, 14)
# palm silhouettes
pal = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(pal)
def palm(x, base, h, lean, side):
    pts = [(x + lean * h * (i / 30) ** 2, base - h * i / 30) for i in range(31)]
    for i in range(30): d.line([pts[i], pts[i + 1]], fill=(14, 2, 26, 255), width=int(h * 0.035 * (1 - i / 45)))
    tx, ty = pts[-1]
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.42; L = h * 0.42
        fr = [(tx + L * u * math.cos(a), ty + L * u * math.sin(a) + L * 0.5 * u * u) for u in np.linspace(0, 1, 16)]
        for j in range(15):
            d.line([fr[j], fr[j + 1]], fill=(14, 2, 26, 255), width=max(6, int(h * 0.03 * (1 - j / 16))))
            for s in (-1, 1): d.line([fr[j], (fr[j][0] + s * 22 * (1 - j / 16), fr[j][1] + 34 * (1 - j / 16))], fill=(14, 2, 26, 255), width=7)
palm(250, S * 0.86, 1250, 0.25, 1); palm(1830, S * 0.88, 1150, -0.22, -1)
img.alpha_composite(pal)
# big gold dollar sign with neon outline
lay = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(lay); f = font("Anton-Regular.ttf", 1250)
bb = d.textbbox((0, 0), "$", font=f); w, h = bb[2] - bb[0], bb[3] - bb[1]
pos = (S / 2 - w / 2 - bb[0], S * 0.46 - h / 2 - bb[1])
d.text(pos, "$", font=f, fill=(255, 215, 60, 255), stroke_width=34, stroke_fill=(40, 0, 60, 255))
glow(lay, 60, 1.4)
shine = Image.new("RGBA", (S, S)); ds = ImageDraw.Draw(shine)
ds.text(pos, "$", font=f, fill=(255, 250, 200, 0)); 
# name band
band = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(band)
fb = font("Anton-Regular.ttf", 210); t = "LEONIDA"
tw = d.textlength(t, font=fb); d.text(((S - tw) / 2, S * 0.755), t, font=fb, fill=(255, 255, 255, 255), stroke_width=14, stroke_fill=(30, 0, 50, 255))
fm = font("Anton-Regular.ttf", 150); t2 = "MILLONARIO"
tw2 = d.textlength(t2, font=fm); d.text(((S - tw2) / 2, S * 0.865), t2, font=fm, fill=(80, 240, 255, 255), stroke_width=12, stroke_fill=(30, 0, 50, 255))
glow(band, 22, 0.8)
img.convert("RGB").save("avatar_leonida_millonario.png")
# version without text (better at tiny sizes)
print("ok")
