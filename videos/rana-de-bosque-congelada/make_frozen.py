"""Crea assets/hero_frozen.jpg a partir de assets/hero_alive.jpg: la misma rana cubierta de escarcha (procedural)."""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
src = Image.open(os.path.join(HERE, "assets", "hero_alive.jpg")).convert("RGB")
w, h = src.size
a = np.asarray(src, np.float32)
r = np.random.default_rng(1)

g = a.mean(2, keepdims=True)
cold = (g + (a - g) * 0.45) * np.array([0.86, 0.97, 1.12]) + 18          # desaturada y azulada

lum = np.asarray(src.convert("L").filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
edges = np.asarray(src.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255

def grains(scale, p):
    n = (r.random((h // scale, w // scale)) > p).astype(np.uint8) * 255
    im = Image.fromarray(n).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.6))
    return np.asarray(im, np.float32) / 255

frost = np.clip(grains(1, 0.97) * 0.35 + grains(2, 0.95) * 0.9 + grains(3, 0.975) * 1.0, 0, 1)
foc = np.asarray(src.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(14)), np.float32) / 255
foc = np.clip(foc / (foc.max() * 0.35), 0, 1)             # zonas enfocadas (la rana) reciben más escarcha
dens = np.clip(0.15 + edges * 5 + foc * 0.75, 0, 1)

needles = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(needles)
for _ in range(26000):
    x, y = r.uniform(0, w), r.uniform(0, h)
    ang = r.uniform(0, np.pi); L = r.uniform(4, 16)
    d.line([(x, y), (x + L * np.cos(ang), y + L * np.sin(ang))], fill=int(r.uniform(120, 255)), width=1)
nd = np.asarray(needles.filter(ImageFilter.GaussianBlur(0.4)), np.float32) / 255

m = np.clip(frost * dens + nd * dens * 1.1, 0, 1)[..., None]
out = cold * (1 - m * 0.85) + np.array([235, 245, 255]) * m * 0.85
haze = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)
out = out * 0.88 + haze * 0.12 + 6
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(HERE, "assets", "hero_frozen.jpg"), quality=94)
print("assets/hero_frozen.jpg")
