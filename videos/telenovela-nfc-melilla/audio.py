# Banda sonora de telenovela turca (modo Hicaz en Re), golpes dramáticos, efectos y mezcla con las voces (ducking). Salida: mix.wav
import os, sys, wave, json
import numpy as np
from scipy.signal import lfilter, butter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import TOTAL, SHOTS

SR = 48000
N = int(SR * (TOTAL + 0.5))
T = np.arange(N) / SR
rng = np.random.default_rng(21)
mus = np.zeros((2, N)); sfx = np.zeros((2, N))
def put(buf, x, at, g=1.0, pan=0.0):
    i0 = int(at * SR); n = min(len(x), N - i0)
    if n > 0 and i0 >= 0:
        buf[0, i0:i0 + n] += x[:n] * g * (1 - pan); buf[1, i0:i0 + n] += x[:n] * g * (1 + pan)
def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, fc, o=2): b, a = butter(o, min(fc, SR / 2 - 100) / (SR / 2)); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), "high"); return lfilter(b, a, x)
def mid(m): return 440 * 2 ** ((m - 69) / 12)
def adsr(d, a=0.05, r=0.3):
    x = tt(d); return np.minimum(1, x / a) * np.minimum(1, np.maximum(0, (d - x) / r))

def strings(notes, d, bright=2500, vib=5.0):
    x = np.zeros(int(d * SR)); s = tt(d)
    for m in notes:
        for det in (-0.004, 0, 0.005):
            f = mid(m) * (1 + det) * (1 + 0.004 * np.sin(2 * np.pi * vib * s + rng.uniform(0, 6)))
            ph = np.cumsum(f) / SR
            x += 2 * (ph % 1) - 1
    return lp(x * adsr(d, 0.35, 0.5), bright) / (len(notes) * 3)

def ney(notes_durs, at, g=0.12):   # flauta ney: seno + aire, vibrato y glissandos
    cur = at
    for m, d in notes_durs:
        s = tt(d); f = mid(m) * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * s) * np.minimum(1, s / 0.3))
        ph = np.cumsum(f) / SR
        x = np.sin(2 * np.pi * ph) + 0.25 * np.sin(4 * np.pi * ph) + lp(rng.standard_normal(len(s)), 2500) * 0.25
        put(mus, x * adsr(d, 0.12, 0.25), cur, g, -0.2); cur += d

def piano(m, at, g=0.12, d=2.0):
    s = tt(d); f = mid(m)
    x = sum(np.sin(2 * np.pi * f * k * s) * np.exp(-s * (1.5 + k)) / k for k in (1, 2, 3, 4))
    put(mus, x * np.minimum(1, s / 0.005), at, g, 0.15)

def timpani(at, g=0.5, f0=55, d=1.6):
    s = tt(d); f = f0 * (1 + 0.15 * np.exp(-s * 8))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-s * 2.5) + lp(rng.standard_normal(len(s)), 400) * np.exp(-s * 15) * 0.6
    put(mus, x, at, g)

def roll(at, d, g=0.25):
    s = tt(d); x = np.zeros(len(s))
    for k in np.arange(0, d, 0.045):
        i = int(k * SR); n = min(int(0.2 * SR), len(s) - i); ss = tt(n / SR)
        x[i:i + n] += np.sin(2 * np.pi * 60 * ss) * np.exp(-ss * 18) * (0.4 + 0.6 * k / d)
    put(mus, x, at, g)

def stab(at, notes, g=0.55, d=1.4):   # «DUN»: orquesta + timbal + platillo
    x = strings([m - 12 for m in notes] + notes, d, 5000) * 3
    s = tt(d); x *= np.exp(-s * 1.3) * 2.5
    put(mus, x, at, g); timpani(at, g * 0.9, 49)
    cy = hp(rng.standard_normal(int(1.5 * SR)), 5000) * np.exp(-tt(1.5) * 3)
    put(sfx, cy, at, 0.1, 0.3)

def darbuka(at, kind):
    s = tt(0.25)
    if kind == "D": x = np.sin(2 * np.pi * np.cumsum(90 + 80 * np.exp(-s * 30)) / SR) * np.exp(-s * 12)
    elif kind == "T": x = hp(rng.standard_normal(len(s)), 2500) * np.exp(-s * 45) + np.sin(2 * np.pi * 700 * s) * np.exp(-s * 40) * 0.5
    else: x = hp(rng.standard_normal(len(s)), 4000) * np.exp(-s * 70) * 0.6
    put(mus, x, at, 0.3, 0.1 if kind == "T" else 0)

def choir(notes, at, d, g=0.1):   # coro «aaah»: sierras + formantes
    x = strings(notes, d, 4000)
    for fc, q in ((700, 0.6), (1150, 0.4)):
        b, a = butter(2, [fc * 0.8 / (SR / 2), fc * 1.25 / (SR / 2)], "band"); x = x + lfilter(b, a, x) * 3 * q
    put(mus, x * adsr(d, 0.6, 0.8), at, g)

def harp_gliss(at, g=0.12):
    for i, m in enumerate([62, 63, 66, 67, 69, 70, 72, 74, 75, 78, 79, 81, 82, 84, 86]):
        s = tt(1.2); x = np.sin(2 * np.pi * mid(m) * s) * np.exp(-s * 3.5)
        put(mus, x, at + i * 0.045, g, -0.5 + i / 15)

# Hicaz en Re: Re Mib Fa# Sol La Sib Do Re
D, Eb, Fs, G, A, Bb, Cc = 62, 63, 66, 67, 69, 70, 72
Dm = [50, 57, 62, 65]; Gm = [55, 62, 67, 70]; Eb_ = [51, 58, 63, 67]; DM = [50, 57, 62, 66]; Cm = [48, 55, 60, 63]

# 0–4: apertura épica
stab(0.05, [D, A, D + 12]); roll(1.4, 0.85, 0.3); put(mus, strings(Dm, 2.3, 2200), 0.2, 0.5)
put(mus, strings(Eb_, 1.9, 2600), 2.25, 0.5); stab(2.25, [Eb, Bb, Eb + 12], 0.45)
ney([(A, 0.5), (Bb, 0.35), (A, 0.35), (Fs, 0.4), (G, 0.3)], 2.3, 0.10)
# 4–9: pena (piano + ney + cuerdas suaves)
put(mus, strings(Dm, 2.5, 1500), 4.0, 0.35); put(mus, strings(Gm, 2.6, 1500), 6.5, 0.35)
for i, m in enumerate([D + 12, A, Fs + 12, A, G + 12, A, Fs + 12, Eb + 12, D + 12, A]):
    piano(m, 4.1 + i * 0.48, 0.10)
ney([(D + 12, 0.8), (Eb + 12, 0.4), (D + 12, 0.4), (Cc, 0.5), (Bb, 0.5), (A, 1.2)], 4.6, 0.07)
# 9–10.8: tensión (trémolo)
tr = strings([D, Eb, A], 1.8, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * tt(1.8)))
put(mus, tr, 9.0, 0.45); roll(9.9, 0.9, 0.2)
# 10.8–12.4: DUN DUN DUN en cada zoom
for k, at in enumerate([10.8, 11.33, 11.87]): stab(at, [D + k, A + k, D + 12 + k], 0.55 + 0.1 * k)
# 12.4–14: suspense
for i in range(6): piano([D, Eb, D, Cc - 12, D, Eb][i] + 12, 12.45 + i * 0.26, 0.09, 0.6)
put(mus, strings([D - 12, Eb - 12], 1.6, 900), 12.4, 0.4)
# 14–20: épica (coro + darbuka)
choir([D, Fs, A], 14.0, 3.0, 0.14); choir([G - 12, Bb, D + 12], 17.0, 3.0, 0.14)
put(mus, strings(DM, 3.0, 3000), 14.0, 0.35); put(mus, strings(Gm, 3.0, 3000), 17.0, 0.35)
pat = "D.T.D.TTD.T.D.T."
for bar in range(6):
    for j, c in enumerate(pat):
        at = 14.0 + bar * 1.0 + j * 0.0625
        if c != "." and at < 20: darbuka(at, c)
stab(14.0, [D, Fs, A], 0.4)
# 20–26: drama máximo
put(mus, strings([50, 57, 62, 66, 69], 2.0, 5000), 20.0, 0.6); put(mus, strings([51, 58, 63, 67, 70], 2.0, 5000), 22.0, 0.6)
put(mus, strings([50, 57, 62, 66, 69, 74], 2.0, 6000), 24.0, 0.65)
ney([(D + 12, 0.25), (Eb + 12, 0.25), (Fs + 12, 0.25), (G + 12, 0.25), (A + 12, 0.9), (G + 12, 0.25), (Fs + 12, 0.25), (Eb + 12, 0.3), (D + 12, 1.5)], 20.1, 0.12)
for bar in range(6):
    for j, c in enumerate("DTTDTTDTDTTDT.TT"):
        at = 20.0 + bar * 1.0 + j * 0.0625
        if c != "." and at < 26: darbuka(at, c)
for at in (20.0, 21.2, 22.9, 23.9, 24.9): timpani(at, 0.5, 46)
# 26–33: revelación celestial
harp_gliss(26.0, 0.12); choir([D, Fs, A, D + 12], 26.0, 3.5, 0.18); choir([G - 12, Bb, D + 12, G + 12], 29.5, 3.5, 0.18)
for i in range(14): piano([A + 12, D + 24, Fs + 12][i % 3], 26.1 + i * 0.5, 0.05, 1.2)   # campanitas
# 33–38.4: melodía emotiva
put(mus, strings(Gm, 2.0, 2200), 33.0, 0.4); put(mus, strings(Dm, 3.4, 1800), 35.0, 0.38)
ney([(G + 12, 0.6), (A + 12, 0.6), (Bb + 12, 0.8), (A + 12, 0.6), (G + 12, 0.5), (Fs + 12, 0.6), (G + 12, 1.4)], 33.1, 0.08)
for i, m in enumerate([D + 12, A, Fs + 12, A, G + 12, Bb, A, Fs]): piano(m, 35.1 + i * 0.42, 0.08)
# 38.4–40: cierre + «continuará»
stab(38.4, [D, Fs, A, D + 12], 0.65, 1.6); harp_gliss(38.5, 0.1)

# ---------------- efectos
def whoosh(d=0.5):
    x = rng.standard_normal(int(d * SR)); y = np.zeros_like(x); seg = 2400
    for i in range(0, len(x), seg): y[i:i + seg] = lp(x[i:i + seg], 300 + 4000 * np.sin(np.pi * i / len(x)))
    return y * np.sin(np.pi * tt(d) / d) ** 2
for (a, b, n) in SHOTS[1:]: put(sfx, whoosh(0.45), a - 0.3, 0.12, rng.uniform(-0.4, 0.4))
def thunder(at, g=0.6):
    s = tt(3.0); x = lp(rng.standard_normal(len(s)), 250) * (np.exp(-s * 1.2) + 0.6 * np.exp(-((s - 0.4) * 4) ** 2)) * 4
    put(sfx, x + hp(rng.standard_normal(len(s)), 2000) * np.exp(-s * 25), at, g)
thunder(21.25, 0.5); thunder(22.0, 0.35)
s = tt(4.8); put(sfx, hp(lp(rng.standard_normal(len(s)), 6000), 800) * 0.35 * np.minimum(1, s / 0.3) * np.minimum(1, (4.8 - s) / 0.3), 20.0, 0.25)   # lluvia
s = tt(0.8); put(sfx, lp(rng.standard_normal(len(s)), 900) * np.exp(-s * 4) * (1 + np.sin(2 * np.pi * 30 * s)), 9.0, 0.35)  # puerta
s = tt(0.6); put(sfx, np.sin(2 * np.pi * (300 + 900 * s) * s) * np.exp(-s * 5), 13.0, 0.08)  # ceja «tiiing»
TAP = 17.15
s = tt(0.03); put(sfx, hp(rng.standard_normal(len(s)), 2000) * np.exp(-s * 250), TAP, 0.5)
for i, m in enumerate([84, 88, 91, 96]):
    s = tt(1.0); put(sfx, np.sin(2 * np.pi * mid(m) * s) * np.exp(-s * 5), TAP + 0.03 + i * 0.05, 0.12)
s = tt(0.5); put(sfx, np.sin(2 * np.pi * 1800 * s) * np.exp(-s * 8) * (s < 0.15), 9.6, 0.06)   # destello tarjeta

# ---------------- mezcla con voces y ducking
with wave.open(os.path.join(HERE, "voice.wav")) as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
v = np.pad(v, (0, max(0, N - len(v))))[:N]
env = lfilter([1 - 0.9995], [1, -0.9995], np.abs(v)); env = np.convolve(env, np.ones(7200) / 7200, "same")
k = np.clip(env / (env.max() * 0.2), 0, 1)
music = mus * (1 - 0.8 * k)[None] * 0.7 + sfx * (1 - 0.4 * k)[None] * 0.8
for a, b, who, _ in json.load(open(os.path.join(HERE, "tmp", "voice_timing.json"))):
    i0, i1 = int(a * SR), int(b * SR)
    print(f"  voz/fondo {a:5.1f}s: {20 * np.log10(np.sqrt(np.mean(v[i0:i1] ** 2)) / (np.sqrt(np.mean(music[:, i0:i1] ** 2)) + 1e-9)):+.1f} dB")
mix = music + v[None] * 1.0
mix *= np.clip((TOTAL + 0.2 - T) / 0.6, 0, 1)[None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix /= np.abs(mix).max() / 0.92
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix.T * 32767).astype(np.int16).tobytes())
print("ok", N / SR)
