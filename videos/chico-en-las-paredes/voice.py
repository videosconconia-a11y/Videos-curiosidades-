# Genera la narración con Piper TTS (voz masculina es_ES "davefx") y guarda timings.json.
import os, sys, json, subprocess, wave, urllib.request
import numpy as np
from scipy.signal import resample_poly, butter, sosfilt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import LINES as SCENES_TXT
VDIR = os.path.join(HERE, "..", ".voices"); os.makedirs(VDIR, exist_ok=True)
NAME = "es_ES-davefx-medium"
URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/"
MODEL = os.path.join(VDIR, NAME + ".onnx")
for ext in (".onnx", ".onnx.json"):
    p = os.path.join(VDIR, NAME + ext)
    if not os.path.exists(p): urllib.request.urlretrieve(URL + NAME + ext + "?download=true", p)

SR = 48000
clips, durs = [], []
for i, (txt, *_r) in enumerate(SCENES_TXT):
    out = os.path.join(VDIR, f"vo_{i:02}.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", out, "--length-scale", "1.07",
                    "--sentence-silence", "0.32", "--noise-scale", "0.6", "--noise-w-scale", "0.75"],
                   input=txt.encode("utf-8"), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(out) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    if sr != SR:
        from math import gcd
        g = gcd(SR, sr); x = resample_poly(x, SR // g, sr // g)
    # recorta silencios de los extremos
    e = np.convolve(np.abs(x), np.ones(480) / 480, "same"); idx = np.where(e > 0.01)[0]
    x = x[max(0, idx[0] - 960): idx[-1] + 2400]
    clips.append(x); durs.append(round(len(x) / SR, 3))

# Procesado: paso alto, presencia suave, compresión ligera -> voz limpia y cercana
sos_hp = butter(2, 80, "hp", fs=SR, output="sos")
sos_lo = butter(2, 220, "lp", fs=SR, output="sos")
for i, x in enumerate(clips):
    x = sosfilt(sos_hp, x); x = x + 0.25 * sosfilt(sos_lo, x)
    env = np.sqrt(np.convolve(x ** 2, np.ones(960) / 960, "same")) + 1e-6
    gain = np.minimum(1, (0.12 / env) ** 0.35); x = x * gain
    clips[i] = x / (np.abs(x).max() + 1e-9) * 0.9
np.save(os.path.join(HERE, "voice_clips.npy"), np.array(clips, dtype=object), allow_pickle=True)
json.dump(durs, open(os.path.join(HERE, "timings.json"), "w"))
print("voz ok", durs, round(sum(durs), 1))
