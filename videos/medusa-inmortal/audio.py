# Música de fondo suave (pad + arpegio tipo campana + pulso grave), sintetizada,
# mezclada con la voz y bajando la música mientras habla el narrador (ducking).
import os, sys, wave, subprocess
import numpy as np
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import load, shots

SR = 48000
scenes, words, TOTAL = load()
N = int(SR * (TOTAL + 0.3)); t = np.arange(N) / SR
rng = np.random.default_rng(5)

def lp(x, a): return lfilter([a], [1, a - 1], x)
def midi(m): return 440 * 2 ** ((m - 69) / 12)

L = np.zeros(N); R = np.zeros(N)
def add(x, g=1.0, pan=0.0):
    global L, R
    L += x * g * (1 - pan); R += x * g * (1 + pan)

# Progresión lenta y luminosa (ambiente submarino): Am - F - C - G (4 s por acorde, 60 BPM)
CH = [[45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [48, 55, 60, 64, 67], [43, 50, 55, 59, 62]]
BAR = 4.0
ci = (t // BAR).astype(int) % 4
# Pad: varias sinusoides desafinadas con fundido suave en cada cambio de acorde
pad = np.zeros(N)
for k in range(4):
    m = (ci == k).astype(float)
    m = lp(lp(m, 0.0004), 0.0004)                      # transiciones suaves
    for j, n in enumerate(CH[k]):
        f = midi(n)
        for det in (-0.12, 0.12):
            pad += m * np.sin(2 * np.pi * f * (1 + det / 100) * t + j) * (0.5 if j == 0 else 0.28)
pad *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.08 * t)
add(lp(pad, 0.25), 0.07, -0.15); add(lp(pad, 0.25), 0.07, 0.15)

# Arpegio tipo campana/marimba suave (corcheas a 60 BPM), entra tras el gancho
def bell(at, f, g):
    i0 = int(at * SR); n = min(int(1.8 * SR), N - i0)
    if n <= 0: return
    tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.01 * tt) * np.exp(-tt * 6)) * np.exp(-tt * 2.6)
    x *= np.minimum(1, tt / 0.004)
    pan = rng.uniform(-0.5, 0.5)
    L[i0:i0 + n] += x * g * (1 - pan); R[i0:i0 + n] += x * g * (1 + pan)
pattern = [0, 2, 3, 4, 3, 2, 1, 2]
step = 0.5; k = 0; at = 2.0
while at < TOTAL - 1.0:
    chord = CH[int(at // BAR) % 4]
    note = chord[pattern[k % 8]] + 12
    bell(at, midi(note), 0.05 * (0.8 + 0.2 * rng.random()))
    k += 1; at += step

# Pulso grave muy suave (latido) en cada tiempo
def thump(at, g):
    i0 = int(at * SR); n = min(int(0.4 * SR), N - i0)
    if n <= 0: return
    tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(45 + 40 * np.exp(-tt * 25)) / SR
    x = np.sin(ph) * np.exp(-tt * 8)
    L[i0:i0 + n] += x * g; R[i0:i0 + n] += x * g
b = 6.0
while b < TOTAL - 2:
    thump(b, 0.12); b += 1.0

# Aire/ambiente de selva muy bajo
air = lp(rng.standard_normal(N), 0.02) * 0.6
add(air * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t)), 0.05)

music = np.stack([L, R], 1)
music /= np.abs(music).max()

# ---- voz
voice = np.zeros(N)
for sc in scenes:
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "assets", "voice", sc["file"]),
                                   "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"])
    v = np.frombuffer(raw, np.float32).astype(float)
    i0 = int(round(sc["audio_at"] * SR)); i0 = max(i0, 0)
    n = min(len(v), N - i0); voice[i0:i0 + n] += v[:n]
voice /= np.abs(voice).max() / 0.85

# ---- ducking: la música baja ~11 dB mientras hay voz (ataque rápido, suelta lenta)
env = np.abs(voice)
env = lfilter([0.002], [1, -0.998], env)
active = (env > 0.01).astype(float)
duck_tgt = 1 - 0.72 * active
duck = np.empty(N); g = 1.0
a_att, a_rel = 1 - np.exp(-1 / (0.06 * SR)), 1 - np.exp(-1 / (0.45 * SR))
for i in range(0, N, 48):             # cálculo por bloques de 1 ms
    tg = duck_tgt[i]; g += (tg - g) * (1 - (1 - (a_att if tg < g else a_rel)) ** 48)
    duck[i:i + 48] = g
fade = np.clip(t / 1.0, 0, 1) * np.clip((TOTAL + 0.2 - t) / 1.5, 0, 1)
mix = music * (0.42 * duck * fade)[:, None] + voice[:, None] * 0.95
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix /= np.abs(mix).max() / 0.92
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("audio ok", round(N / SR, 2), "s")
