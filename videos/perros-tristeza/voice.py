# Narración con IA: Piper TTS (voz masculina es_ES "davefx"), procesado tipo locutor
# y tiempos por palabra con faster-whisper para sincronizar subtítulos e imágenes.
#   python3 voice.py  [ruta_voz.onnx]
import os, sys, json, wave, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS, plain

VOICE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "PIPER_VOICE", "/tmp/claude-0/voices/es_ES-davefx-medium.onnx")
OUT = os.path.join(HERE, "voice"); os.makedirs(OUT, exist_ok=True)
SR = 48000

from piper import PiperVoice, SynthesisConfig
voice = PiperVoice.load(VOICE)
# más lento y con menos ruido de muestreo = dicción más limpia y pausada (tono documental)
cfg = SynthesisConfig(length_scale=1.04, noise_scale=0.42, noise_w_scale=0.55)

# Cadena de "estudio": quita graves sucios, cuerpo en 120 Hz (voz más profunda), presencia,
# de-esser, compresión suave y una sala muy corta para que no suene seca/robótica.
CHAIN = ("highpass=f=70,"
         "rubberband=pitch=0.94:formant=preserved,"
         "equalizer=f=120:t=q:w=1:g=3.5,equalizer=f=350:t=q:w=1.2:g=-2.5,"
         "equalizer=f=3200:t=q:w=1.5:g=2,equalizer=f=9000:t=h:w=2000:g=1.5,"
         "deesser=i=0.5,"
         "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3dB,"
         "aecho=0.85:0.5:28|47:0.10|0.07,"
         "aresample=48000")

def synth(text, path):
    tmp = path + ".raw.wav"
    with wave.open(tmp, "wb") as w:
        voice.synthesize_wav(text, w, syn_config=cfg)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", CHAIN, "-ac", "1", path], check=True)
    os.remove(tmp)
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    # recorta silencios de los extremos
    thr = 0.01; idx = np.where(np.abs(a) > thr)[0]
    a = a[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.12 * SR)]
    return a

from faster_whisper import WhisperModel
asr = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")

timings = {}
for sid, txt, _shots, _pause in SEGMENTS:
    p = os.path.join(OUT, f"{sid}.wav")
    a = synth(plain(txt), p)
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
    from scipy.signal import resample_poly
    a16 = resample_poly(a, 1, 3).astype(np.float32)
    segs, _ = asr.transcribe(a16, language="es", word_timestamps=True, beam_size=5,
                             initial_prompt=plain(txt))
    words = [{"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
             for s in segs for w in s.words]
    timings[sid] = {"dur": round(len(a) / SR, 3), "words": words}
    print(sid, timings[sid]["dur"], len(words), "/", len(txt.split()), flush=True)

json.dump(timings, open(os.path.join(OUT, "timings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total voz", round(sum(v["dur"] for v in timings.values()), 2))
