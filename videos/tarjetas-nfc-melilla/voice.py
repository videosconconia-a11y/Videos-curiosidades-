# Genera la locución con Piper TTS (voz es_ES-davefx-medium). Necesita: pip install piper-tts y el modelo .onnx
import os, sys, subprocess, json, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import VOICE, TOTAL, write_srt
MODEL = os.environ.get("PIPER_MODEL", os.path.join(HERE, "voices", "es_ES-davefx-medium.onnx"))
SR = 48000
os.makedirs(os.path.join(HERE, "tmp"), exist_ok=True)
track = np.zeros(int(SR * (TOTAL + 1)))
timing = []
for i, (start, text) in enumerate(VOICE):
    raw = os.path.join(HERE, "tmp", f"v{i}.wav"); fx = os.path.join(HERE, "tmp", f"v{i}_48k.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", raw, "--length-scale", "0.86",
                    "--sentence-silence", "0.12"], input=text.encode(), check=True, capture_output=True)
    # voz de anuncio: limpieza de graves, presencia, compresión y un toque de brillo
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "highpass=f=90,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3200:t=q:w=1.2:g=3,equalizer=f=9000:t=h:w=1:g=2,"
                    "acompressor=threshold=-20dB:ratio=3.5:attack=5:release=80:makeup=4,aresample=48000",
                    "-ac", "1", "-f", "wav", fx], check=True)
    with wave.open(fx) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    i0 = int(start * SR); track[i0:i0 + len(x)] += x[:len(track) - i0]
    timing.append((start, start + len(x) / SR, text))
    print(f"{start:5.2f}-{start+len(x)/SR:5.2f}  {text}")
for a, b, _ in timing: pass
for (a1, b1, t1), (a2, _, _) in zip(timing, timing[1:]):
    if b1 > a2 - 0.05: print(f"AVISO: solape {t1[:30]}… termina {b1:.2f} > {a2:.2f}")
track /= max(1e-9, np.abs(track).max()) / 0.95
with wave.open(os.path.join(HERE, "voice.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((track * 32767).astype(np.int16).tobytes())
json.dump(timing, open(os.path.join(HERE, "tmp", "voice_timing.json"), "w"), ensure_ascii=False)
write_srt(os.path.join(HERE, "subtitulos.srt"), timing)
