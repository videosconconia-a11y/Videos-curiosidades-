# Voz neuronal es-ES "Álvaro" (Microsoft Edge TTS): natural, masculina, castellano.
# Narrador con tono neutro; las citas de la carta, más lentas y graves, con un poco de eco.
# Guarda voice_clips.npy (audio 48 kHz por frase) y timings.json (duración + tiempo de cada palabra).
import os, sys, json, ssl, asyncio, subprocess
import numpy as np
from scipy.signal import butter, sosfilt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import LINES

CA = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):                     # proxy con CA propia (entorno en la nube)
    _o = ssl.create_default_context
    def _ctx(*a, **k):
        c = _o(*a, **k); c.load_verify_locations(CA); return c
    ssl.create_default_context = _ctx
import edge_tts

VOICE = "es-ES-AlvaroNeural"
STYLE = {"n": dict(rate="-3%", pitch="-2Hz"), "c": dict(rate="-12%", pitch="-7Hz")}
SR = 48000
CACHE = os.path.join(HERE, "..", ".voices", "vigilante"); os.makedirs(CACHE, exist_ok=True)

async def synth(i, text, sty):
    mp3 = os.path.join(CACHE, f"l{i:02}.mp3"); words = []
    c = edge_tts.Communicate(text, VOICE, boundary="WordBoundary", **STYLE[sty])
    with open(mp3, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary": words.append([ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]])
    return mp3, words

def decode(mp3):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp3, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float) / 32768

def echo(x):  # eco corto de habitación para las citas
    y = x.copy()
    for d, g in [(0.045, 0.28), (0.083, 0.2), (0.131, 0.14), (0.197, 0.09)]:
        n = int(d * SR); y[n:] += x[:-n] * g
    return y

sos_hp = butter(2, 70, "hp", fs=SR, output="sos")
clips, tim = [], []
for i, (text, _k, _s, _p, sty) in enumerate(LINES):
    mp3, words = asyncio.run(synth(i, text, sty))
    x = decode(mp3)
    # recorta el silencio final (el inicial se mantiene: los tiempos de palabra cuentan desde el inicio del audio)
    e = np.convolve(np.abs(x), np.ones(480) / 480, "same"); idx = np.where(e > 0.005)[0]
    end = min(len(x), idx[-1] + int(0.08 * SR)) if len(idx) else len(x)
    st = max(0, idx[0] - int(0.03 * SR)) if len(idx) else 0
    x = x[st:end]; words = [[w0 - st / SR, wd, wt] for (w0, wd, wt) in words]
    x = sosfilt(sos_hp, x)
    if sty == "c":
        x = echo(x)
    clips.append(x / (np.abs(x).max() + 1e-9) * (0.8 if sty == "c" else 0.9))
    tim.append({"dur": round(len(x) / SR, 3), "words": words})
np.save(os.path.join(HERE, "voice_clips.npy"), np.array(clips, dtype=object), allow_pickle=True)
json.dump(tim, open(os.path.join(HERE, "timings.json"), "w"), ensure_ascii=False)
print("voz ok", [t["dur"] for t in tim], round(sum(t["dur"] for t in tim), 1))
