# El modelo no sabe dibujar el tallo del hongo Ophiocordyceps: se pinta un esbozo del tallo sobre una
# imagen buena de hormiga y SDXL-Turbo (img2img) lo convierte en fotorrealista.
import os, sys, torch
from PIL import Image, ImageDraw, ImageFilter
from diffusers import AutoPipelineForImage2Image
HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(HERE, "assets", "img")
torch.set_num_threads(os.cpu_count())
pipe = AutoPipelineForImage2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.bfloat16, variant="fp16")
pipe.set_progress_bar_config(disable=True)

def stalk(im, p0, p1, p2, w0=16, w1=5, col=(205, 185, 150)):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    N = 60; pts = []
    for i in range(N + 1):
        t = i / N
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pts.append((x, y, t))
    for (x, y, t) in pts:
        r = (w0 + (w1 - w0) * t) / 2
        if 0.55 < t < 0.75: r *= 1.7                     # engrosamiento (ascoma) típico del hongo
        shade = tuple(int(c * (0.8 + 0.2 * (1 - t))) for c in col)
        d.ellipse([x - r, y - r, x + r, y + r], fill=shade + (255,))
        d.ellipse([x - r * 0.35 - r * 0.3, y - r * 0.6, x - r * 0.3 + r * 0.2, y + r * 0.2], fill=(240, 230, 210, 200))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    out = im.copy(); out.paste(lay, (0, 0), lay); return out

JOBS = {  # salida: (imagen base, puntos del tallo, prompt, fuerza, semilla)
    "hook_zombie": ("bite_vein_b.png", ((410, 480), (360, 250), (470, 40)), 0.45, 7),
    "stalk_grow": ("death_grip_c202.png", ((285, 520), (250, 330), (330, 110)), 0.45, 8),
    "final_ant": ("bite_vein_b.png", ((410, 480), (330, 260), (420, 60)), 0.55, 9),
}
PROMPT = ("macro photo of a dead ant infected by ophiocordyceps fungus, a thin pale brown fungal stalk growing out of "
          "the back of its head, cinematic, ultra realistic, dramatic moody light, shallow depth of field")
for name, (base, pts, strength, seed) in JOBS.items():
    if sys.argv[1:] and name not in sys.argv[1:]: continue
    im = Image.open(os.path.join(IMG, base)).convert("RGB")
    sk = stalk(im, *pts)
    if name == "final_ant":                                # versión más oscura para el cierre
        from PIL import ImageEnhance
        sk = ImageEnhance.Brightness(sk).enhance(0.6)
    sk.save(os.path.join(IMG, f"{name}_sketch.png"))
    out = pipe(PROMPT, image=sk, strength=strength, num_inference_steps=max(2, int(round(2 / strength))),
               guidance_scale=0.0, generator=torch.Generator().manual_seed(seed)).images[0]
    out.save(os.path.join(IMG, f"{name}_s.png")); print(name, flush=True)
