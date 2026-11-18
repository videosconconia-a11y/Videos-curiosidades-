# Genera la voz de IA (Piper TTS, voz es_ES) de cada escena y guarda sus duraciones.
# Uso: python3 tts.py  [ruta al modelo .onnx]   (por defecto busca voice/es_ES-davefx-medium.onnx)
import json, os, subprocess, sys, wave
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCRIPT

VOICE_DIR = os.path.join(HERE, "voice")
MODEL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(VOICE_DIR, "es_ES-davefx-medium.onnx")
LENGTH_SCALE = os.environ.get("TTS_SPEED", "0.86")   # <1 = más rápido (ritmo de short)
URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx"

os.makedirs(VOICE_DIR, exist_ok=True)
if not os.path.exists(MODEL):
    for ext in ("", ".json"):
        subprocess.run(["curl", "-sSfL", "-o", MODEL + ext, URL + ext], check=True)

# Pronunciación: Piper lee en español; los nombres en inglés se escriben "como suenan".
SPOKEN = [("GTA 6", "ge te a seis"), ("GTA 5", "ge te a cinco"), ("PlayStation 5", "Pléisteishon cinco"),
          ("Xbox", "Équisbox"), ("PC", "pecé"), ("Vice City", "Váis Síti"), ("Jason", "Yéison"),
          ("Bonnie y Clyde", "Bóni y Cláid"), ("Guinness", "Guínes"), ("YouTube", "Yutúb"), ("Rockstar", "Rócstar"),
          ("tráiler", "tréiler"), ("iceberg", "áisberg")]
def spoken(t):
    for a, b in SPOKEN: t = t.replace(a, b)
    return t

durs = []
for i, (text, _c, _v) in enumerate(SCRIPT):
    out = os.path.join(VOICE_DIR, f"scene_{i:02}.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "--length-scale", LENGTH_SCALE,
                    "--sentence-silence", "0.12", "-f", out], input=spoken(text).encode(), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(out) as w:
        durs.append(round(w.getnframes() / w.getframerate(), 3))
    print(f"escena {i}: {durs[-1]:.2f}s", flush=True)

json.dump({"durations": durs, "model": os.path.basename(MODEL), "length_scale": LENGTH_SCALE},
          open(os.path.join(VOICE_DIR, "timings.json"), "w"), indent=1)
print("total voz", round(sum(durs), 2))
