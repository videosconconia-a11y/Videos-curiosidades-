# Narración con IA + tiempos por palabra (faster-whisper) para sincronizar subtítulos e imágenes.
#   TTS_ENGINE=openai python3 voice.py   -> OpenAI gpt-4o-mini-tts, español de España enérgico (por defecto)
#   TTS_ENGINE=piper  python3 voice.py   -> Piper es_ES-davefx-medium (sin conexión)
# La clave de OpenAI se lee de OPENAI_API_KEY (en la nube la inyecta el proxy del entorno).
import os, sys, json, wave, subprocess, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS, plain

ENGINE = os.environ.get("TTS_ENGINE", "openai")
OUT = os.path.join(HERE, "voice"); os.makedirs(OUT, exist_ok=True)
SR = 48000

# ---------------------------------------------------------------- OpenAI
OA_VOICE = os.environ.get("OPENAI_VOICE", "ash")
OA_INSTR = ("Habla en español de España, con acento castellano peninsular (la ce y la zeta como en Madrid, "
            "nada de acento latinoamericano). Eres un chico joven que narra vídeos virales de curiosidades en "
            "TikTok: voz enérgica, natural y cercana, con ritmo ágil, entonación intrigante y expresiva, "
            "remarcando las palabras clave y los datos sorprendentes. Nunca suenes robótico ni monótono.")

def tts_openai(text, path):
    body = json.dumps({"model": "gpt-4o-mini-tts", "voice": OA_VOICE, "input": text,
                       "instructions": OA_INSTR, "response_format": "wav"}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/audio/speech", data=body, headers={
        "Authorization": "Bearer " + os.environ.get("OPENAI_API_KEY", "proxy-injected"),
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())

# Procesado ligero: limpia graves, un poco de presencia, de-esser y compresión suave (sin cambiar el tono).
CHAIN_OPENAI = ("highpass=f=75,equalizer=f=180:t=q:w=1:g=1.5,equalizer=f=3500:t=q:w=1.5:g=1.5,"
                "deesser=i=0.4,acompressor=threshold=-18dB:ratio=2.5:attack=6:release=100:makeup=2dB,aresample=48000")

# ---------------------------------------------------------------- Piper (alternativa local)
# versión enérgica: sin bajar el tono, más presencia y brillo, compresión de locutor de redes
CHAIN_PIPER = ("highpass=f=80,equalizer=f=150:t=q:w=1:g=1.5,equalizer=f=400:t=q:w=1.2:g=-2,"
               "equalizer=f=3000:t=q:w=1.5:g=3,equalizer=f=8000:t=h:w=2000:g=2.5,deesser=i=0.5,"
               "acompressor=threshold=-22dB:ratio=3.5:attack=5:release=90:makeup=4dB,aresample=48000")
if ENGINE == "piper":
    from piper import PiperVoice, SynthesisConfig
    pv = PiperVoice.load(os.environ.get("PIPER_VOICE", "/tmp/claude-0/voices/es_ES-davefx-medium.onnx"))
    pcfg = SynthesisConfig(length_scale=0.93, noise_scale=0.62, noise_w_scale=0.85)   # más ágil y expresiva

def synth(text, path):
    tmp = path + ".raw.wav"
    if ENGINE == "openai":
        tts_openai(text, tmp); chain = CHAIN_OPENAI
    else:
        with wave.open(tmp, "wb") as w: pv.synthesize_wav(text, w, syn_config=pcfg)
        chain = CHAIN_PIPER
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", chain, "-ac", "1", path], check=True)
    os.remove(tmp)
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    thr = 0.012; idx = np.where(np.abs(a) > thr)[0]          # recorta silencios de los extremos
    return a[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.12 * SR)]

from faster_whisper import WhisperModel
from scipy.signal import resample_poly
asr = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")

only = sys.argv[1:]
tpath = os.path.join(OUT, "timings.json")
timings = json.load(open(tpath, encoding="utf-8")) if (only and os.path.exists(tpath)) else {}
for sid, txt, _shots, _pause in SEGMENTS:
    if only and sid not in only: continue
    p = os.path.join(OUT, f"{sid}.wav")
    a = synth(plain(txt), p)
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    segs, _ = asr.transcribe(resample_poly(a, 1, 3).astype(np.float32), language="es",
                             word_timestamps=True, beam_size=5, initial_prompt=plain(txt))
    words = [{"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
             for s in segs for w in s.words]
    timings[sid] = {"dur": round(len(a) / SR, 3), "words": words}
    print(sid, timings[sid]["dur"], len(words), "/", len(txt.split()), "|", " ".join(x["w"] for x in words), flush=True)

json.dump(timings, open(tpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total voz", round(sum(v["dur"] for v in timings.values()), 2))
