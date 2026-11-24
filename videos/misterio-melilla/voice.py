# Locución con Kokoro TTS (Apache 2.0) vía kokoro-onnx, fonética de español de España (θ, ʎ).
#   misterio / narrador / documental -> em_alex (masculina natural; "misterio" lleva un poco de sala)
#   alien -> em_santa, más aguda y ondulada (efecto cómico de extraterrestre)
# Modelos: https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX (onnx/model.onnx + voices/em_alex.bin, em_santa.bin)
import os, sys, json, subprocess
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import VOICE, TOTAL
from kokoro_onnx import Kokoro

KD = os.environ.get("KOKORO_DIR", os.path.join(HERE, "voices"))
VB = os.path.join(KD, "voices.bin")
if not os.path.exists(VB):
    v = {n: np.fromfile(os.path.join(KD, f"{n}.bin"), dtype=np.float32).reshape(-1, 1, 256) for n in ("em_alex", "em_santa")}
    np.savez(VB + ".npz", **v); os.replace(VB + ".npz", VB)
K = Kokoro(os.path.join(KD, "model.onnx"), VB)
OUT = os.path.join(HERE, "vo"); os.makedirs(OUT, exist_ok=True)
CLEAN = "highpass=f=75,equalizer=f=220:t=q:w=1:g=-1.5,equalizer=f=4000:t=q:w=1.5:g=2,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=150"
CFG = {
    "misterio":   dict(voice="em_alex", speed=0.92, fx=CLEAN + ",aecho=0.8:0.5:90|170:0.22|0.12"),
    "narrador":   dict(voice="em_alex", speed=1.0, fx=CLEAN),
    "documental": dict(voice="em_alex", speed=1.0, fx=CLEAN + ",equalizer=f=150:t=q:w=1:g=1.5"),
    "alien":      dict(voice="em_santa", speed=1.0,
                       fx="rubberband=pitch=1.32:formant=shifted,vibrato=f=7:d=0.12,flanger=delay=1.5:depth=2:speed=0.6,"
                          "highpass=f=120,acompressor=threshold=-18dB:ratio=3"),
}
def trim(a, sr, thr=0.01):
    idx = np.where(np.abs(a) > thr)[0]
    return a[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)] if len(idx) else a
meta = []
for i, (start, who, text) in enumerate(VOICE):
    nxt = VOICE[i + 1][0] if i + 1 < len(VOICE) else TOTAL - 0.25
    room = nxt - start - 0.1
    c = CFG[who]; sp = c["speed"]
    a, sr = K.create(text, voice=c["voice"], speed=sp, lang="es"); a = trim(a, sr)
    if len(a) / sr > room:
        sp = min(1.25, sp * (len(a) / sr) / room * 1.02)
        a, sr = K.create(text, voice=c["voice"], speed=sp, lang="es"); a = trim(a, sr)
    raw = os.path.join(OUT, f"raw_{i:02}.wav"); fin = os.path.join(OUT, f"vo_{i:02}.wav")
    sf.write(raw, a, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", c["fx"] + ",aresample=48000", "-ac", "1", fin], check=True)
    d = sf.info(fin).duration
    meta.append(dict(start=start, who=who, file=fin, dur=d))
    print(f"{i} {who:10s} {start:5.2f}-{start + d:5.2f} (hueco {room:4.2f}, vel {sp:.2f})  {text}")
json.dump(meta, open(os.path.join(OUT, "voice.json"), "w"), indent=1)
