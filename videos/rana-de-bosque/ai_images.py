# Imágenes generadas con IA (OpenAI Images API), una por plano, siguiendo la narración.
# Guarda assets/ai/<plano>.jpg y no regenera las que ya existen (borra una para rehacerla).
# Uso:  python3 ai_images.py [plano ...]
# Motores (AI_BACKEND):
#   local  (por defecto) SDXL base + SDXL-Lightning 4 pasos (ByteDance, licencia OpenRAIL++), en CPU, gratis.
#   openai API de imágenes de OpenAI (AI_MODEL=gpt-image-1, AI_QUALITY=high); clave en OPENAI_API_KEY.
import os, sys, json, base64, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import io

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "ai"); os.makedirs(OUT, exist_ok=True)
BACKEND = os.environ.get("AI_BACKEND", "local")
MODEL = os.environ.get("AI_MODEL", "gpt-image-1")
QUALITY = os.environ.get("AI_QUALITY", "high")
KEY = os.environ.get("OPENAI_API_KEY", "proxy-injected")

FROG = ("a North American wood frog (Lithobates sylvaticus): small tan to reddish-brown frog with a distinctive "
        "dark brown mask stripe through the eye and a pale upper-lip line")
STYLE = (" Photorealistic wildlife documentary photograph, National Geographic style, cinematic lighting, "
         "shallow depth of field, ultra detailed, vertical 9:16 composition with the subject in the upper-middle "
         "of the frame. No text, no letters, no watermark, no logos.")

# plano -> descripción de la imagen (lo que dice la voz en ese momento va en el comentario)
PROMPTS = {
    # «Este animal se congela por completo…»
    "frozen_frog": f"Close-up of {FROG} frozen solid on the forest floor in deep winter, its whole body coated in white hoarfrost and tiny ice crystals, half buried in snow-dusted brown leaves, cold blue moonlight.",
    "ice_grow": f"Extreme macro of feathery ice crystals spreading across the frosted brown skin of {FROG}, the frog's eye visible at the edge of frame, cold blue light, sparkling.",
    # «…y meses después, vuelve a la vida.»
    "frog_eye": f"Extreme macro of the golden eye of {FROG} just opening as the last frost melts off its face, water droplets glowing in warm golden spring sunlight.",
    # «Es la rana de bosque.»
    "frog_hero": f"Hero portrait of {FROG} sitting on green moss on a forest floor, soft morning light, eye in sharp focus.",
    # «Vive en los bosques de Norteamérica…»
    "frog_side": f"Side profile of {FROG} among fallen leaves in a North American deciduous forest in autumn, warm light, forest bokeh behind.",
    # «…llega más al norte que ningún otro anfibio…»
    "boreal": "Vast snowy boreal spruce forest in interior Alaska stretching to the horizon, low pale winter sun, frozen silence, cold blue tones.",
    # «…más allá del Círculo Polar Ártico.»
    "aurora": "Green and violet aurora borealis rippling over a snow-covered Arctic boreal forest at night, stars, spruce silhouettes.",
    # «Cuando llega el invierno…»
    "snow_forest": "Forest floor in early winter at dusk, first snow falling on brown fallen leaves between dark tree trunks, cold blue light, snowflakes in the air.",
    # «…no huye, ni se esconde bajo el agua.»
    "snowfall_close": "A small forest pond freezing over in early winter, thin ice and snow on its surface, frozen reeds, empty and silent, cold blue light.",
    # «Se queda entre las hojas del suelo del bosque…»
    "frog_leaves": f"{FROG} hiding motionless under a blanket of brown fallen oak and maple leaves on the forest floor in late autumn, only its head and eye visible, first frost on the leaves.",
    # «…y deja que el hielo la atrape.»
    "frost_leaves": f"Fallen leaves covered in thick hoarfrost on the forest floor, and beneath them the barely visible frosted face of {FROG}, being trapped by the ice, blue cold light.",
    # «El hielo empieza en su piel, y avanza hacia dentro.»
    "frog_freeze": f"Extreme macro of the back skin of {FROG} with ice crystals forming on its surface and creeping across it, frost patterns, cold light.",
    "ice_macro": "Macro photograph of long needle-like ice crystals growing inward, glittering, deep blue background, sense of freezing in progress.",
    # «Hasta el 65 % del agua de su cuerpo se convierte en hielo.»
    "stat_65": f"Top-down view of {FROG} completely encased in a block of clear ice with frost, cold blue light, dark background.",
    # «Su corazón deja de latir.»
    "heartbeat": f"Dark moody close-up of the frozen pale belly and chest of {FROG} covered in frost, a faint dim red glow of its stopped heart visible through the translucent frosted skin.",
    # «No respira. No circula la sangre.»
    "frozen_frog_2": f"{FROG} frozen completely motionless in snow, stiff legs, body covered in ice crystals, lifeless looking, dim cold blue light.",
    # «A todos los efectos… parece muerta.»
    "frog_eye_still": f"Extreme macro of the eye of a frozen {FROG}, the eye clouded and covered with frost crystals, lifeless and still, dark cold tones.",
    # «¿El truco? En cuanto nota el hielo…»
    "frog_macro": f"Close-up of {FROG} on frosty leaves at night as the first ice crystals touch its toes, dramatic rim light, dark background.",
    # «…su hígado inunda el cuerpo de glucosa.»
    "glucose": f"Scientific visualization inside the body of {FROG}: its liver glowing warm gold and releasing streams of luminous golden glucose particles into the bloodstream, dark background, semi-transparent anatomy, documentary CGI style.",
    # «Ese azúcar funciona como un anticongelante…»
    "frog_antifreeze": f"{FROG} in the snow with faintly glowing golden veins under its skin while blue frost tries to cover it, magical but realistic, cold and warm contrast.",
    # «…el hielo se queda fuera de las células…»
    "cells": "Microscopic view of living animal cells glowing warm amber and protected, while sharp blue ice crystals grow only in the spaces between the cells, scientific microscopy style, dark background.",
    # «…y las células sobreviven.»
    "frog_hero_2": f"Close-up of {FROG} partly covered in frost but intact and healthy-looking, a soft warm light touching its face, hope.",
    # «En Alaska, los científicos…»
    "alaska": "Aerial view of the interior Alaska wilderness in winter near Fairbanks: endless snowy boreal forest, frozen rivers, mountains, low sun.",
    # «…siguieron a ranas en plena naturaleza.»
    "frog_track": "A field biologist in warm winter gear kneeling in a snowy Alaskan boreal forest, gently checking a small temperature sensor placed under the leaf litter, breath visible in the cold air.",
    # «…193 días seguidos congeladas…»
    "stat_193": f"{FROG} frozen under snow on the forest floor at night, seen through a cross-section of the snow layer, long winter, stars above.",
    # «…mínimas de hasta 18 grados bajo cero.»
    "stat_18": "Bitter cold night in a snowy boreal forest, frost on everything, ice fog, deep blue tones, an old analog thermometer frozen in the snow (no readable numbers).",
    # «Y sobrevivieron todas.»
    "frog_survive": f"{FROG} alive and alert in the first spring sunlight on wet leaves with melting snow around, golden light, triumphant mood.",
    # «Y en primavera, con el deshielo…»
    "thaw": f"Close-up of frost and ice melting off the back of {FROG} in spring, water droplets running down its skin, warm sunlight, steam.",
    # «…su corazón vuelve a latir por sí solo.»
    "heartbeat_back": f"Close-up of the chest of {FROG} with a warm red glow of its beating heart visible through the skin, thawing droplets, warm light, dark background.",
    # «En pocas horas respira, se mueve…»
    "frog_spring": f"{FROG} breathing, throat inflated, sitting on wet green moss in early spring, raindrops, fresh green light.",
    # «…y salta hacia la charca.»
    "pond": f"{FROG} leaping into a small forest vernal pool in early spring, mid-air with a splash, other wood frogs in the water, fresh green and golden light.",
    # «Hoy, los científicos la estudian…»
    "lab": "Modern cryobiology laboratory, a scientist in a lab coat lifting a vial from a steaming liquid nitrogen tank, cold blue light, frost vapor.",
    # «…para conservar órganos humanos para trasplantes.»
    "frog_portrait": "A medical organ transport container being carefully closed by gloved hands in a hospital lab, frost and cold vapor, cool blue light, hope.",
    # «Y ahora, piénsalo: ¿te dejarías congelar…»
    "frog_eye_end": f"Extreme macro of the eye of {FROG} with frost slowly forming around it, the eye looking directly at the viewer, mysterious, cold blue light.",
    # «Te leo en comentarios.»
    "end_card": f"Dark, mysterious close-up of the frost-covered face of {FROG} emerging from snow, cold blue light, lots of dark negative space at the top of the frame.",
}


NEG = ("text, watermark, cartoon, cute, toy, front view, human face, illustration, painting, 3d render, deformed, "
       "extra legs, extra eyes, blurry, lowres")
_PIPE = None
def local_pipe():
    global _PIPE
    if _PIPE is None:
        import torch
        from diffusers import StableDiffusionXLPipeline, UNet2DConditionModel, EulerDiscreteScheduler
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file
        torch.set_num_threads(os.cpu_count())
        from huggingface_hub import snapshot_download
        base = snapshot_download("stabilityai/stable-diffusion-xl-base-1.0", allow_patterns=[
            "model_index.json", "scheduler/*", "text_encoder/config.json", "text_encoder/model.fp16.safetensors",
            "text_encoder_2/config.json", "text_encoder_2/model.fp16.safetensors", "tokenizer/*", "tokenizer_2/*",
            "vae/config.json", "vae/diffusion_pytorch_model.fp16.safetensors", "unet/config.json"])
        unet = UNet2DConditionModel.from_config(UNet2DConditionModel.load_config(base, subfolder="unet"))
        unet.load_state_dict(load_file(hf_hub_download("ByteDance/SDXL-Lightning", "sdxl_lightning_4step_unet.safetensors")))
        pipe = StableDiffusionXLPipeline.from_pretrained(base, unet=unet, variant="fp16", torch_dtype=torch.bfloat16)
        pipe.to(torch.bfloat16)
        pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
        _PIPE = pipe
    return _PIPE


FROG_SHORT = "a brown wood frog (Rana sylvatica) seen in side profile, with a black mask stripe through its eye"
STYLE_SHORT = ", National Geographic wildlife photo, photorealistic, sharp focus"


# Prompts cortos para SDXL (límite de 77 tokens): primero el efecto que pide la narración.
LOCAL = {
    "frozen_frog": "brown wood frog frozen solid, body completely covered in thick white hoarfrost and ice crystals, snow, blue cold light",
    "ice_grow": "feathery ice crystals spreading over frog skin, thick white frost, extreme macro, cold blue light",
    "frog_eye": "golden frog eye opening as frost melts, water droplets, warm golden spring sunlight",
    "frog_hero": "brown wood frog with black eye mask on forest floor, soft morning light",
    "frog_side": "brown wood frog with black eye mask in autumn deciduous forest leaf litter, warm light",
    "boreal": "vast snowy boreal spruce forest in interior Alaska, low pale winter sun, cold blue tones, landscape",
    "aurora": "green aurora borealis over snowy arctic spruce forest at night, stars",
    "snow_forest": "first snow falling on brown fallen leaves on the forest floor at dusk, dark tree trunks, cold blue light",
    "snowfall_close": "small forest pond freezing over, thin ice and snow on the surface, frozen reeds, cold blue light",
    "frog_leaves": "brown wood frog hiding under fallen autumn leaves, first frost on the leaves, cold morning",
    "frost_leaves": "fallen leaves covered in thick hoarfrost on the forest floor, ice crystals, cold blue light",
    "frog_freeze": "frog skin turning to ice, white frost crystals forming over the back of a brown frog, cold blue light",
    "ice_macro": "macro of long needle ice crystals growing, glittering, deep blue background",
    "stat_65": "frog frozen inside a block of ice, covered in white frost, cold blue light, dark background",
    "heartbeat": "frozen frog covered in frost, dark moody blue light, faint red glow in its chest",
    "frozen_frog_2": "frog frozen motionless, completely covered in white frost and ice, lifeless, dim cold blue light",
    "frog_eye_still": "frozen frog eye covered in white frost crystals, lifeless, dark cold blue tones",
    "frog_macro": "brown wood frog at night, first ice crystals touching its toes, frost, dramatic rim light",
    "glucose": "glowing golden liver releasing luminous golden particles into dark blood vessels, scientific visualization, dark background",
    "frog_antifreeze": "brown frog with faintly glowing golden veins under its skin, blue frost around it, cold and warm contrast",
    "cells": "microscope view of round amber glowing cells with sharp blue ice crystals growing only between them, dark background",
    "frog_hero_2": "brown frog partly covered in frost but healthy, soft warm light on its face",
    "alaska": "aerial view of interior Alaska wilderness in winter, endless snowy boreal forest, frozen river, mountains",
    "frog_track": "field biologist in winter parka kneeling in snowy Alaskan forest checking a small sensor in the leaf litter",
    "stat_193": "frog frozen under snow on the forest floor at night, frost, long winter, cold blue light",
    "stat_18": "bitter cold night in a snowy boreal forest, ice fog, frost on spruce trees, deep blue",
    "frog_survive": "brown wood frog alive in the first spring sunlight, melting snow, golden light",
    "thaw": "frost melting off a brown frog in spring, water droplets running down its skin, warm sunlight",
    "heartbeat_back": "brown frog in warm light with a glowing red heart visible through its skin, thawing droplets",
    "frog_spring": "brown wood frog breathing on wet green moss in early spring, raindrops, fresh green light",
    "pond": "forest vernal pool in early spring, fresh green and golden light, reflections",
    "lab": "modern cryobiology laboratory, scientist lifting a vial from a steaming liquid nitrogen tank, cold blue light",
    "frog_portrait": "surgeon in blue scrubs carrying a white medical transplant cooler box down a bright hospital corridor, hope",
    "frog_eye_end": "frog eye with frost forming around it, looking at the viewer, mysterious cold blue light",
    "end_card": "frost covered frog face emerging from snow, dark, cold blue light, dark empty space above",
}


def local_prompt(key):
    return LOCAL[key] + STYLE_SHORT


# Planos de la rana: la IA parte de una foto real (img2img) para que la anatomía sea correcta.
# plano -> (clave de foto en media.py, fuerza de la transformación 0..1)
INIT = {
    "frozen_frog": ("frog_cold", 0.72), "ice_grow": ("frog_freeze", 0.7), "frog_eye": ("frog_head", 0.45),
    "frog_hero": ("frog_hero", 0.4), "frog_side": ("frog_side", 0.4), "frog_leaves": ("frog_leaves", 0.5),
    "frost_leaves": ("frost_leaves", 0.5), "frog_freeze": ("frog_freeze", 0.66), "stat_65": ("frog_freeze", 0.72),
    "heartbeat": ("frog_cold_2", 0.68), "frozen_frog_2": ("frog_cold_2", 0.7), "frog_eye_still": ("frog_head", 0.68),
    "frog_macro": ("frog_dark", 0.45), "frog_antifreeze": ("frog_side", 0.55), "frog_hero_2": ("frog_stones", 0.5),
    "stat_193": ("frog_cold_2", 0.72), "frog_survive": ("frog_green", 0.45), "thaw": ("frog_side", 0.55),
    "heartbeat_back": ("frog_spring", 0.55), "frog_spring": ("frog_spring", 0.45), "pond": ("pond", 0.55),
    "frog_eye_end": ("frog_head", 0.55), "end_card": ("frog_head", 0.68),
}


def init_image(key):
    sys.path.insert(0, HERE)
    from media import PHOTOS
    m = PHOTOS[INIT[key][0]]
    im = Image.open(os.path.join(HERE, "assets", "photos", m["file"])).convert("RGB")
    w, h = im.size; z = m.get("zoom", 1.0)
    ch = h / z; cw = ch * 9 / 16
    if cw > w: cw = w; ch = cw * 16 / 9
    fx, fy = m.get("focus", (0.5, 0.5))
    x0 = min(max(fx * w - cw / 2, 0), w - cw); y0 = min(max(fy * h - ch / 2, 0), h - ch)
    return im.resize((768, 1344), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


def generate_local(key, seed=7):
    import torch
    path = os.path.join(OUT, key + ".jpg")
    if os.path.exists(path): return key, "ya existe"
    pipe = local_pipe()
    g = torch.Generator().manual_seed(seed + sum(map(ord, key)))
    if key in INIT:
        from diffusers import StableDiffusionXLImg2ImgPipeline
        i2i = StableDiffusionXLImg2ImgPipeline(**pipe.components)
        strength = INIT[key][1]
        img = i2i(local_prompt(key), image=init_image(key), strength=strength, num_inference_steps=round(4 / strength),
                  guidance_scale=0, generator=g).images[0]
    else:
        img = pipe(local_prompt(key), negative_prompt=NEG, num_inference_steps=4, guidance_scale=0,
                   width=768, height=1344, generator=g).images[0]
    img.convert("RGB").save(path, quality=94)
    return key, "ok"


def generate(key):
    path = os.path.join(OUT, key + ".jpg")
    if os.path.exists(path): return key, "ya existe"
    body = json.dumps({"model": MODEL, "prompt": PROMPTS[key] + STYLE, "size": "1024x1536",
                       "quality": QUALITY, "n": 1}).encode()
    for attempt in range(5):
        req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body, headers={
            "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            d = json.load(urllib.request.urlopen(req, timeout=300))
            item = d["data"][0]
            raw = base64.b64decode(item["b64_json"]) if item.get("b64_json") else urllib.request.urlopen(item["url"]).read()
            Image.open(io.BytesIO(raw)).convert("RGB").save(path, quality=93)
            return key, "ok"
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (401, 403): return key, f"ERROR {e.code}: {msg}"
            if e.code == 400: return key, f"ERROR 400 (prompt rechazado?): {msg}"
            time.sleep(10 * (attempt + 1))
        except Exception as e:
            time.sleep(10 * (attempt + 1)); last = str(e)
    return key, "ERROR: reintentos agotados"


if __name__ == "__main__":
    keys = sys.argv[1:] or list(PROMPTS)
    if BACKEND == "local":
        for k in keys:
            t0 = time.time(); k, r = generate_local(k); print(f"{k:16} {r} ({time.time() - t0:.0f} s)", flush=True)
        sys.exit(0)
    with ThreadPoolExecutor(4) as ex:
        for k, r in ex.map(generate, keys):
            print(f"{k:16} {r}", flush=True)
