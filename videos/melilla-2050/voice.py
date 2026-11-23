# Locución con Kokoro TTS (Apache 2.0) vía kokoro-onnx, fonética de español de España (espeak "es": θ, ʎ).
#   narrador     -> em_alex  (masculina, tono natural, suave y limpia; sin cambios de tono ni eco)
#   presentadora -> ef_dora  (femenina, para el informativo)
# Modelos: https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX  (onnx/model.onnx + voices/*.bin)
# Carpeta configurable con KOKORO_DIR (por defecto ./voices). Requiere: pip install kokoro-onnx soundfile
import os, sys, json, subprocess
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import VOICE, TOTAL
from kokoro_onnx import Kokoro

KD = os.environ.get("KOKORO_DIR", os.path.join(HERE, "voices"))
VB = os.path.join(KD, "voices.bin")
if not os.path.exists(VB):          # empaqueta los .bin sueltos de Hugging Face en el formato de kokoro-onnx
    v = {n: np.fromfile(os.path.join(KD, f"{n}.bin"), dtype=np.float32).reshape(-1, 1, 256) for n in ("em_alex", "ef_dora")}
    np.savez(VB + ".npz", **v); os.replace(VB + ".npz", VB)
K = Kokoro(os.path.join(KD, "model.onnx"), VB)
OUT = os.path.join(HERE, "vo"); os.makedirs(OUT, exist_ok=True)
CFG = {"narrador": dict(voice="em_alex", speed=1.0), "presentadora": dict(voice="ef_dora", speed=1.08)}
# Ecualización ligera: limpia graves, un poco de presencia, compresión suave. Nada de pitch ni reverb.
FX = "highpass=f=75,equalizer=f=220:t=q:w=1:g=-1.5,equalizer=f=4000:t=q:w=1.5:g=2,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=150,aresample=48000"

def trim(a, sr, thr=0.01):
    idx = np.where(np.abs(a) > thr)[0]
    return a[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)] if len(idx) else a

meta = []
for i, (start, who, text) in enumerate(VOICE):
    nxt = VOICE[i + 1][0] if i + 1 < len(VOICE) else TOTAL - 0.4
    room = nxt - start - 0.12
    c = CFG[who]; sp = c["speed"]
    a, sr = K.create(text, voice=c["voice"], speed=sp, lang="es"); a = trim(a, sr)
    if len(a) / sr > room:          # si no cabe, acelera un poco (máx. 1,2x)
        sp = min(1.25, sp * (len(a) / sr) / room * 1.02)
        a, sr = K.create(text, voice=c["voice"], speed=sp, lang="es"); a = trim(a, sr)
    raw = os.path.join(OUT, f"raw_{i:02}.wav"); fin = os.path.join(OUT, f"vo_{i:02}.wav")
    sf.write(raw, a, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", FX, "-ac", "1", fin], check=True)
    d = sf.info(fin).duration
    meta.append(dict(start=start, who=who, file=fin, dur=d))
    print(f"{i} {who:12s} {start:5.2f}-{start + d:5.2f} (hueco {room:4.2f}, vel {sp:.2f})  {text}")
json.dump(meta, open(os.path.join(OUT, "voice.json"), "w"), indent=1)
