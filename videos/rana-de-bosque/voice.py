# Voz en off con Piper TTS (voz es_ES "davefx", español de España).
# Genera build/voice.wav (48 kHz, procesada: tono algo más grave, EQ, compresión)
# y build/timing.json con los tiempos reales de cada frase y de cada bloque de subtítulo.
import os, sys, json, wave, tarfile, subprocess, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, LEAD_IN, TAIL, TIMING

BUILD = os.path.join(HERE, "build"); os.makedirs(BUILD, exist_ok=True)
VOICE = os.environ.get("VOICE", "davefx")                 # davefx | sharvard
# Estilo "viral" (por defecto), ajustado midiendo voces de canales de curiosidades que se hacen virales:
# ~25 % más rápida, entonación exagerada (rango de tono x1,5), pausas cortas y sonido brillante.
# VOICE_STYLE=documental recupera la voz anterior: más lenta, grave y plana.
STYLE = os.environ.get("VOICE_STYLE", "viral")
VIRAL = STYLE == "viral"
LENGTH = float(os.environ.get("VOICE_SPEED", "0.76" if VIRAL else "0.90"))   # <1 = más rápido
PITCH_RANGE = float(os.environ.get("VOICE_EXPRESSION", "1.35" if VIRAL else "1.0"))  # >1 = más entonación
PAUSE_SCALE = 0.6 if VIRAL else 1.0
MODEL_DIR = os.path.join(HERE, "assets", "voice")
URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_ES-{VOICE}-medium.tar.bz2"


def model_path():
    onnx = os.path.join(MODEL_DIR, f"es_ES-{VOICE}-medium.onnx")
    if not os.path.exists(onnx):
        os.makedirs(MODEL_DIR, exist_ok=True)
        tmp = os.path.join(MODEL_DIR, "voice.tar.bz2")
        print("descargando voz", URL, flush=True)
        urllib.request.urlretrieve(URL, tmp)
        with tarfile.open(tmp) as tf:
            for m in tf.getmembers():
                if m.name.endswith((".onnx", ".onnx.json")):
                    m.name = os.path.basename(m.name); tf.extract(m, MODEL_DIR)
        os.remove(tmp)
    return onnx


from piper import PiperVoice, SynthesisConfig
voice = PiperVoice.load(model_path())
SR = voice.config.sample_rate
CFG = SynthesisConfig(length_scale=LENGTH, noise_scale=0.62, noise_w_scale=0.75, speaker_id=None)


def expressive(a):
    """Exagera la curva de entonación (vocoder WORLD) sin cambiar la duración."""
    if abs(PITCH_RANGE - 1.0) < 1e-3: return a
    import pyworld as pw
    x = a.astype(np.float64)
    f0, tt = pw.harvest(x, SR, f0_floor=60, f0_ceil=400, frame_period=5)
    sp = pw.cheaptrick(x, f0, tt, SR); ap = pw.d4c(x, f0, tt, SR)
    v = f0 > 0
    if v.sum() < 5: return a
    lm = np.exp(np.mean(np.log(f0[v])))
    f0[v] = lm * 1.04 * np.exp(PITCH_RANGE * (np.log(f0[v]) - np.log(lm)))
    y = pw.synthesize(f0, sp, ap, SR, frame_period=5)[:len(a)]
    return (y / max(1e-6, np.abs(y).max()) * min(0.9, np.abs(a).max())).astype(np.float32)


def synth(text, expr=False):
    a = np.concatenate([c.audio_float_array for c in voice.synthesize(text, CFG)])
    if expr: a = expressive(a)
    # recorta silencios de los extremos
    env = np.convolve(np.abs(a), np.ones(256) / 256, "same")
    idx = np.where(env > 0.01)[0]
    if len(idx): a = a[max(0, idx[0] - 200): idx[-1] + 400]
    return a.astype(np.float32)


def speech_len(text):
    return len(synth(text)) / SR


parts, t = [np.zeros(int(LEAD_IN * SR), np.float32)], LEAD_IN
tm = {"scenes": []}
for sc in SCENES:
    tsc = {"name": sc["name"], "lines": []}
    for text, chunks, pause in sc["lines"]:
        a = synth(text, expr=True); dur = len(a) / SR; pause *= PAUSE_SCALE
        # duración relativa de cada bloque de subtítulo = lo que tarda la voz en decirlo suelto
        w = [speech_len(c.replace("*", "").replace("…", "").lower()) for c in chunks]
        k = dur / sum(w); c0 = t; ch = []
        for c, wi in zip(chunks, w):
            ch.append({"text": c, "start": round(c0, 3), "end": round(c0 + wi * k, 3)}); c0 += wi * k
        tsc["lines"].append({"text": text, "start": round(t, 3), "end": round(t + dur, 3), "chunks": ch})
        parts += [a, np.zeros(int(pause * SR), np.float32)]
        t += dur + pause
        print(f"{t:6.2f}s  {text[:60]}", flush=True)
    tm["scenes"].append(tsc)

# los subtítulos aguantan hasta que empieza el siguiente bloque (sin parpadeos en pausas cortas)
caps = [c for s in tm["scenes"] for l in s["lines"] for c in l["chunks"]]
for c, n in zip(caps, caps[1:]):
    if n["start"] - c["end"] < 0.45: c["end"] = n["start"]
caps[-1]["end"] = round(caps[-1]["end"] + 0.6, 3)

tm["total"] = round(t + TAIL, 2)
tm["voice"] = VOICE
raw = np.concatenate(parts + [np.zeros(int(TAIL * SR), np.float32)])
raw_path = os.path.join(BUILD, "voice_raw.wav")
with wave.open(raw_path, "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((np.clip(raw, -1, 1) * 32767).astype(np.int16).tobytes())

# Procesado tipo locución: algo más grave, cuerpo en graves, presencia, de-esser suave, compresión
chain = ("aresample=48000:resampler=soxr,"
         + ("highpass=f=80,"
            "equalizer=f=140:t=q:w=1.0:g=2,"
            "equalizer=f=300:t=q:w=1.2:g=-2.5,"
            "equalizer=f=3500:t=q:w=1.0:g=4,"
            "highshelf=f=9000:g=2," if VIRAL else
            "rubberband=pitch=0.94:transients=crisp:pitchq=quality,"
            "highpass=f=70,"
            "equalizer=f=120:t=q:w=1.0:g=3.5,"
            "equalizer=f=300:t=q:w=1.2:g=-2,"
            "equalizer=f=3200:t=q:w=1.0:g=2.5,") +
         "equalizer=f=7500:t=q:w=2.0:g=-3,"
         "acompressor=threshold=-20dB:ratio=3.5:attack=4:release=90:makeup=4,"
         "alimiter=limit=0.89:level=false")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw_path, "-af", chain, "-ac", "1",
                "-t", str(tm["total"]), os.path.join(BUILD, "voice.wav")], check=True)
with open(TIMING, "w", encoding="utf-8") as f:
    json.dump(tm, f, ensure_ascii=False, indent=1)
print("voz:", VOICE, "estilo:", STYLE, "duración total", tm["total"], "s")
