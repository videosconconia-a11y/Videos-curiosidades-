# Genera la narración con Piper TTS (voz es_ES) frase a frase y guarda sus duraciones.
# Requiere: pip install piper-tts  y el modelo en $PIPER_MODEL (por defecto /opt/piper/es_ES-davefx-medium.onnx)
import os, sys, json, subprocess, wave
import numpy as np
from scipy.signal import resample_poly
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import all_phrases

MODEL = os.environ.get("PIPER_MODEL", "/opt/piper/es_ES-davefx-medium.onnx")
LENGTH = os.environ.get("PIPER_LENGTH", "1.06")   # >1 = un poco más pausado y natural
OUT = os.path.join(HERE, "voice"); os.makedirs(OUT, exist_ok=True)
SR = 48000

def read(path):
    with wave.open(path) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    return x, sr

durs = []
for i, (say, *_r) in enumerate(all_phrases()):
    raw = os.path.join(OUT, f"raw_{i:02}.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", raw, "--length-scale", LENGTH,
                    "--noise-scale", "0.6", "--noise-w-scale", "0.75", "--sentence-silence", "0.32"],
                   input=say.replace("...", "…").encode(), check=True, capture_output=True)
    x, sr = read(raw)
    x = resample_poly(x, SR, sr)
    # recorta silencios del principio y del final
    e = np.convolve(np.abs(x), np.ones(480) / 480, "same")
    idx = np.where(e > 0.012)[0]
    a, b = max(0, idx[0] - 960), min(len(x), idx[-1] + 2400)
    x = x[a:b]
    x *= np.minimum(1, np.arange(len(x)) / 240)[::1] * np.minimum(1, (len(x) - np.arange(len(x))) / 960)
    np.save(os.path.join(OUT, f"p_{i:02}.npy"), x.astype(np.float32))
    durs.append(len(x) / SR)
    os.remove(raw)
    print(f"{i:2} {durs[-1]:5.2f}s  {say}")
with open(os.path.join(OUT, "durations.json"), "w") as f: json.dump(durs, f)
print("voz total", round(sum(durs), 2))
