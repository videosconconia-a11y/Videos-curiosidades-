"""Genera la narración con Piper TTS (voz es_ES) escena a escena y guarda las duraciones reales.

Uso: python3 voz.py [ruta_modelo.onnx]
Por defecto busca el modelo en $PIPER_VOICE o en ~/voces/es_ES-davefx-medium.onnx
(descarga: https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_ES/davefx/medium).
"""
import json, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import script_data  # noqa: E402
from script_data import SCENES  # noqa: E402
SAY = getattr(script_data, 'SAY', {})

MODEL = (sys.argv[1] if len(sys.argv) > 1 else
         os.environ.get("PIPER_VOICE", os.path.expanduser("~/voces/es_ES-davefx-medium.onnx")))
SPEED = 0.97          # algo más pausada: así el vídeo pasa del minuto (TikTok) y el gancho pesa más
OUT = os.path.join(HERE, "voz")


def tts(text, path):
    # Piper lee mejor sin puntos suspensivos tipográficos
    txt = text.replace("…", ",")
    for a, b in SAY.items(): txt = txt.replace(a, b)
    subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "--length-scale", str(SPEED),
                    "--sentence-silence", "0.12", "-f", path], input=txt.encode(), check=True,
                   stderr=subprocess.DEVNULL)


def trim(path):
    """Recorta silencios al principio y al final para que no haya huecos entre frases."""
    with wave.open(path) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
    a = np.abs(x.astype(np.float32))
    thr = 0.02 * a.max()
    idx = np.where(a > thr)[0]
    i0 = max(0, idx[0] - int(0.02 * sr)); i1 = min(len(x), idx[-1] + int(0.06 * sr))
    x = x[i0:i1]
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())
    return len(x) / sr


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    durs = []
    for i, s in enumerate(SCENES):
        p = os.path.join(OUT, f"frase_{i:02}.wav")
        tts(s[0], p)
        d = trim(p); durs.append(round(d, 3))
        print(f"frase {i}: {d:.2f} s · {len(s[0].split()) / d:.2f} pal/s")
    json.dump(durs, open(os.path.join(OUT, "duraciones.json"), "w"))
    print(f"total voz {sum(durs):.2f} s")
