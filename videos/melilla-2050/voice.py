# Genera la locución con Piper TTS (voces es_ES) y la procesa:
#   narrador  -> es_ES-davefx-medium, más grave, lento y con reverberación (potente y misterioso)
#   presentadora -> es_ES-sharvard-medium (F), con ecualización "de estudio de TV"
# Modelos: https://huggingface.co/rhasspy/piper-voices (carpeta es/es_ES). Ruta configurable con PIPER_VOICES.
import os, subprocess, sys, json, wave
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import VOICE
VD = os.environ.get("PIPER_VOICES", os.path.join(HERE, "voices"))
OUT = os.path.join(HERE, "vo"); os.makedirs(OUT, exist_ok=True)
CFG = {
    "narrador": dict(model="es_ES-davefx-medium.onnx", spk=0, ls=1.0,
                     fx="rubberband=pitch=0.86:tempo=1.0:formant=preserved,"
                        "equalizer=f=110:t=q:w=1:g=5,equalizer=f=3500:t=q:w=1.5:g=3,"
                        "aecho=0.8:0.6:60|130:0.25|0.14,acompressor=threshold=-20dB:ratio=4:attack=5:release=120"),
    "presentadora": dict(model="es_ES-sharvard-medium.onnx", spk=1, ls=0.86,
                     fx="highpass=f=140,equalizer=f=2800:t=q:w=1.2:g=4,"
                        "aecho=0.8:0.3:25:0.12,acompressor=threshold=-18dB:ratio=3"),
}
TEMPO = {0: 1.3, 5: 1.16}   # líneas que deben caber en su escena
meta = []
for i, (start, who, text) in enumerate(VOICE):
    c = CFG[who]; raw = os.path.join(OUT, f"raw_{i:02}.wav"); fin = os.path.join(OUT, f"vo_{i:02}.wav")
    subprocess.run(["piper", "-m", os.path.join(VD, c["model"]), "-s", str(c["spk"]), "--length-scale", str(c["ls"]),
                    "--sentence-silence", "0.12", "-f", raw], input=text.encode(), check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f"atempo={TEMPO.get(i, 1.0)}," + c["fx"] + ",aresample=48000", "-ac", "1", fin], check=True)
    with wave.open(fin) as w: d = w.getnframes() / w.getframerate()
    meta.append(dict(start=start, who=who, file=fin, dur=d)); print(f"{i} {who:12s} {start:5.2f}-{start+d:5.2f}  {text}")
json.dump(meta, open(os.path.join(OUT, "voice.json"), "w"), indent=1)
