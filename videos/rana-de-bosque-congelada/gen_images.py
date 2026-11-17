"""Genera las imágenes fotorrealistas de las escenas con RealVisXL V5.0 Lightning (SDXL, licencia OpenRAIL++)
en local (CPU sirve: ~2 min por imagen). Las versiones congelada/descongelada de una misma rana se obtienen
por img2img a partir de la misma imagen, para que el animal sea idéntico en la transición.
Requiere: pip install torch diffusers transformers accelerate  (y ~7 GB para el modelo).
Salida: assets/<nombre>.jpg"""
import json, os, sys, time
import torch
from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline, DPMSolverMultistepScheduler
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = "SG161222/RealVisXL_V5.0_Lightning"
NEG = "cartoon, illustration, 3d render, painting, drawing, text, watermark, deformed, extra legs, blurry, lowres"
torch.set_num_threads(os.cpu_count())
J = json.load(open(os.path.join(HERE, "prompts.json"), encoding="utf-8"))
dev = "cuda" if torch.cuda.is_available() else "cpu"; dt = torch.float16 if dev == "cuda" else torch.bfloat16

def setup(cls, base=None):
    p = cls.from_pretrained(MODEL, torch_dtype=dt, variant="fp16") if base is None else cls(**base.components)
    p.scheduler = DPMSolverMultistepScheduler.from_config(p.scheduler.config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++")
    p.enable_attention_slicing(); p.vae.enable_tiling(); return p.to(dev)

def out(n): return os.path.join(HERE, "assets", n + ".jpg")
t2i = setup(StableDiffusionXLPipeline)
for j in J["txt2img"]:
    if os.path.exists(out(j["name"])): continue
    im = t2i(prompt=j["prompt"], negative_prompt=NEG, num_inference_steps=6, guidance_scale=1.5, width=768, height=1344,
             generator=torch.Generator().manual_seed(j["seed"])).images[0]
    im.save(out(j["name"]), quality=94); print(j["name"])
i2i = setup(StableDiffusionXLImg2ImgPipeline, t2i)
for j in J["img2img"]:
    if os.path.exists(out(j["name"])): continue
    im = i2i(prompt=j["prompt"], negative_prompt=NEG, image=Image.open(out(j["src"])).convert("RGB"), strength=j["strength"],
             num_inference_steps=10, guidance_scale=1.5, generator=torch.Generator().manual_seed(j["seed"])).images[0]
    im.save(out(j["name"]), quality=94); print(j["name"])
