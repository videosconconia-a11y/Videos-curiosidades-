# Imágenes generadas con IA (OpenAI Images API), una por plano, siguiendo la narración.
# Guarda assets/ai/<plano>.jpg y no regenera las que ya existen (borra una para rehacerla).
# Uso:  python3 ai_images.py [plano ...]     Variables: AI_MODEL (gpt-image-1), AI_QUALITY (high)
# La clave se toma de OPENAI_API_KEY (en este entorno la inyecta el proxy de red).
import os, sys, json, base64, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import io

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "ai"); os.makedirs(OUT, exist_ok=True)
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
    with ThreadPoolExecutor(4) as ex:
        for k, r in ex.map(generate, keys):
            print(f"{k:16} {r}", flush=True)
