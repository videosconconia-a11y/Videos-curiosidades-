# Voces con Piper TTS (español de España): narrador (davefx, más grave), Rafa (sharvard M) y Sofía (sharvard F).
# Genera voice.wav, subtitulos.srt y la envolvente de cada personaje para mover la boca (tmp/env_*.npy).
import os, sys, subprocess, json, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import VOICE, TOTAL, write_srt
V = os.path.join(HERE, "voices")
SR = 48000
CFG = {  # modelo, hablante, velocidad, tono, filtros extra
    "narr": ("es_ES-davefx-medium.onnx", None, 1.08, 0.90, "aecho=0.8:0.6:60|110:0.25|0.15"),
    "rafa": ("es_ES-sharvard-medium.onnx", 0, 1.0, 0.97, "aecho=0.8:0.5:35:0.12"),
    "rafa_grito": ("es_ES-sharvard-medium.onnx", 0, 1.0, 1.10, "acrusher=bits=12:mix=0.15,aecho=0.8:0.75:420|840|1260:0.55|0.35|0.2"),
    "sofia": ("es_ES-sharvard-medium.onnx", 1, 1.0, 0.96, "aecho=0.8:0.5:35:0.12"),
}
os.makedirs(os.path.join(HERE, "tmp"), exist_ok=True)
track = np.zeros(int(SR * (TOTAL + 1)))
per = {k: np.zeros_like(track) for k in ("narr", "rafa", "sofia")}
timing = []
for i, (start, who, text) in enumerate(VOICE):
    model, spk, ls, pitch, extra = CFG[who]
    raw = os.path.join(HERE, "tmp", f"v{i}.wav"); fx = os.path.join(HERE, "tmp", f"v{i}_48k.wav")
    cmd = [sys.executable, "-m", "piper", "-m", os.path.join(V, model), "-f", raw, "--length-scale", str(ls), "--sentence-silence", "0.15"]
    if spk is not None: cmd += ["-s", str(spk)]
    subprocess.run(cmd, input=text.encode(), check=True, capture_output=True)
    with wave.open(raw) as w: sr0 = w.getframerate()
    af = (f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          f"asetrate={int(sr0 * pitch)},aresample=48000,atempo={1 / pitch:.4f},"
          "highpass=f=80,equalizer=f=200:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1.2:g=3,"
          f"acompressor=threshold=-20dB:ratio=3.5:attack=5:release=80:makeup=4,{extra},apad=pad_dur=1.2")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af, "-ac", "1", "-ar", "48000", fx], check=True)
    with wave.open(fx) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    # recorta la cola de silencio que no lleva eco
    e = np.abs(x) > 0.004; last = len(x) - np.argmax(e[::-1]) if e.any() else len(x); x = x[:last]
    if who == "rafa_grito": x *= 1.25
    i0 = int(start * SR); n = min(len(x), len(track) - i0)
    track[i0:i0 + n] += x[:n]
    per["rafa" if who.startswith("rafa") else who][i0:i0 + n] += x[:n]
    # duración "hablada" (sin eco) para subtítulos
    with wave.open(raw) as w: dur = w.getnframes() / w.getframerate()
    timing.append((start, start + dur * (1 / 1.0), who, text))
    print(f"{start:5.2f}-{start + len(x) / SR:5.2f} [{who}] {text}")
for (a1, b1, w1, t1), (a2, *_r) in zip(timing, timing[1:]):
    if b1 > a2 - 0.05: print(f"AVISO: solape «{t1[:30]}…» termina {b1:.2f} > {a2:.2f}")
track /= max(1e-9, np.abs(track).max()) / 0.95
with wave.open(os.path.join(HERE, "voice.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((track * 32767).astype(np.int16).tobytes())
FPS = 30; hop = SR // FPS
for k, x in per.items():
    nfr = len(x) // hop
    env = np.sqrt(np.mean(x[:nfr * hop].reshape(nfr, hop) ** 2, 1))
    env = np.clip(env / (np.percentile(env[env > 1e-4], 90) + 1e-9) if (env > 1e-4).any() else env, 0, 1.2)
    np.save(os.path.join(HERE, "tmp", f"env_{k}.npy"), env)
json.dump(timing, open(os.path.join(HERE, "tmp", "voice_timing.json"), "w"), ensure_ascii=False)
write_srt(os.path.join(HERE, "subtitulos.srt"), timing)
