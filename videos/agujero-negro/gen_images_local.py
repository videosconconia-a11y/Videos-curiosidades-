# Genera las imágenes IA localmente (CPU) con SDXL-Turbo cuando no hay API de imágenes disponible.
# Uso: python3 gen_images_local.py [nombre ...]   (sin nombres = todas las que falten)
import os, sys, time, torch
from diffusers import AutoPipelineForText2Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES

OUT = os.path.join(HERE, "assets", "img"); os.makedirs(OUT, exist_ok=True)
STYLE = "cinematic space art, ultra realistic, dramatic light, highly detailed, epic, interstellar movie style"
W, H = int(os.environ.get("IMG_W", 576)), int(os.environ.get("IMG_H", 1024))
STEPS = int(os.environ.get("STEPS", 4))

torch.set_num_threads(os.cpu_count())
pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.bfloat16, variant="fp16")
pipe.set_progress_bar_config(disable=True)

want = sys.argv[1:]
for si, s in enumerate(SCENES):
    for k, (name, prompt) in enumerate(s["images"]):
        path = os.path.join(OUT, f"{name}{os.environ.get('SUF', '')}.png")
        if (want and name not in want) or (not want and os.path.exists(path)):
            continue
        t0 = time.time()
        g = torch.Generator().manual_seed(1000 + si * 10 + k + int(os.environ.get("SEED", 0)))
        img = pipe(prompt=f"{prompt}, {STYLE}", num_inference_steps=STEPS, guidance_scale=0.0,
                   width=W, height=H, generator=g).images[0]
        img.save(path)
        print(f"{name} {time.time() - t0:.0f}s", flush=True)
