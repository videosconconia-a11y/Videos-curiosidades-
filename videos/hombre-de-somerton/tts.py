# Genera la voz en off (masculina, español de España), una pista por escena.
# 1) Intenta la API de OpenAI (gpt-4o-mini-tts, voz "onyx" con acento peninsular).
# 2) Si no hay saldo/acceso, usa Piper TTS con la voz es_ES-davefx-medium (hombre, castellano).
#    Descarga: https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_ES/davefx/medium
#    y pon la ruta del .onnx en PIPER_MODEL (por defecto ./voz/modelo/es_ES-davefx-medium.onnx).
# Salida: voz/escena_XX.wav + voz/timings.json
import json, os, subprocess, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import RAW

VOICE = os.environ.get("TTS_VOICE", "onyx")
INSTR = ("Habla en español de España, castellano peninsular con acento de Madrid: pronuncia la ce y la zeta "
         "como en España (distinción), nunca seseo ni acento latinoamericano. Voz masculina, grave, neutra y muy natural, "
         "de narrador de historias de misterio y crímenes reales para redes sociales. Tono íntimo y serio, con tensión contenida, "
         "pausas breves en los puntos suspensivos, ritmo ágil. Nada teatral ni robótico.")
OUT = os.path.join(HERE, "voz"); os.makedirs(OUT, exist_ok=True)

def tts(text, path):
    body = json.dumps({"model": "gpt-4o-mini-tts", "voice": VOICE, "input": text, "instructions": INSTR,
                       "response_format": "wav"}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/audio/speech", body, method="POST", headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + os.environ.get("OPENAI_API_KEY", "sk-proxy")})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())

PIPER_MODEL = os.environ.get("PIPER_MODEL", os.path.join(OUT, "modelo", "es_ES-davefx-medium.onnx"))
USE_PIPER = os.environ.get("TTS_ENGINE") == "piper"

def piper(text, path):
    # length_scale > 1 = más pausado; noise algo más alto = entonación menos plana
    subprocess.run([sys.executable, "-m", "piper", "-m", PIPER_MODEL, "-f", path, "--length-scale", os.environ.get("TTS_SPEED", "0.95"),
                    "--noise-scale", "0.72", "--noise-w-scale", "0.85", "--sentence-silence", "0.25"],
                   input=text.encode(), check=True, capture_output=True)

# Cadena de "locutor": quita graves sucios, da cuerpo, comprime suave y añade una sala muy discreta
VOICE_FX = ("highpass=f=75,equalizer=f=160:t=q:w=1:g=3,equalizer=f=3200:t=q:w=1.2:g=2,"
            "equalizer=f=7500:t=q:w=1:g=-2,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,"
            "aecho=0.8:0.5:38|61:0.10|0.06")

def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))

def main():
    global USE_PIPER
    if "--solo-medir" in sys.argv:   # voces externas ya colocadas en voz/escena_XX.wav
        durs = [round(dur(os.path.join(OUT, f"escena_{i:02}.wav")), 3) for i in range(len(RAW))]
        json.dump(durs, open(os.path.join(OUT, "timings.json"), "w")); print("total voz", sum(durs)); return
    only = [int(x) for x in sys.argv[1:]]
    durs = []
    for i, (n, _c, _v) in enumerate(RAW):
        raw = os.path.join(OUT, f"raw_{i:02}.wav"); fin = os.path.join(OUT, f"escena_{i:02}.wav")
        if not os.path.exists(fin) or i in only:
            if not USE_PIPER:
                try: tts(n, raw)
                except Exception as e:
                    print("OpenAI TTS no disponible (", e, ") -> Piper", flush=True); USE_PIPER = True
            if USE_PIPER: piper(n, raw)
            # recorta silencios de los extremos y normaliza a 48 kHz mono
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                            + (VOICE_FX if USE_PIPER else "highpass=f=70"),
                            "-ar", "48000", "-ac", "1", fin], check=True)
            os.remove(raw)
        durs.append(round(dur(fin), 3)); print(i, durs[-1], flush=True)
    json.dump(durs, open(os.path.join(OUT, "timings.json"), "w"))
    print("total voz", sum(durs))

if __name__ == "__main__":
    main()
