# Música electrónica (124 BPM, Fa menor) + efectos + mezcla con la voz y ducking. Salida: mix.wav
import os, sys, wave
import numpy as np
from scipy.signal import lfilter, butter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import TOTAL, SHOTS

SR = 48000
N = int(SR * (TOTAL + 0.3))
t = np.arange(N) / SR
rng = np.random.default_rng(11)
BPM = 124; BEAT = 60 / BPM; BAR = 4 * BEAT
L = np.zeros(N); R = np.zeros(N)

def add(x, g=1.0, pan=0.0, at=0.0):
    i0 = int(at * SR); n = min(len(x), N - i0)
    if n <= 0: return
    L[i0:i0 + n] += x[:n] * g * (1 - pan); R[i0:i0 + n] += x[:n] * g * (1 + pan)
def lp(x, fc, order=2): b, a = butter(order, min(fc, SR / 2 - 100) / (SR / 2)); return lfilter(b, a, x)
def hp(x, fc, order=2): b, a = butter(order, fc / (SR / 2), "high"); return lfilter(b, a, x)
def tt(d): return np.arange(int(d * SR)) / SR
def note(m): return 440 * 2 ** ((m - 69) / 12)
def saw(f, d, det=0.0):
    x = tt(d); return 2 * ((x * f * (1 + det)) % 1) - 1

# ------------------------------------------------ sección / energía
#  (inicio, fin, kick, hats, bass, stabs, pad)
SECT = [(0.0, 3.0, 0, 0, 0, 0, 1), (3.0, 6.0, 0, 1, 1, 0, 1), (6.0, 10.0, 1, 1, 1, 1, 1), (10.0, 11.4, 0, 0, 0, 0, 1),
        (11.4, 19.0, 1, 1, 1, 1, 1), (19.0, 24.0, 0, 1, 1, 0, 1), (24.0, 30.0, 1, 1, 1, 1, 1), (30.0, 33.0, 0, 0, 0, 0, 1),
        (33.0, 34.8, 1, 1, 1, 1, 1)]
def on(x, idx): return any(a <= x < b and s[idx] for (a, b, *s) in SECT for s in [s] if True)
def active(x, k): return any(a <= x < b and fl[k] for (a, b, *fl) in SECT)

CHORDS = [[53, 56, 60, 65], [49, 53, 56, 61], [56, 60, 63, 68], [51, 55, 58, 63]]   # Fm  Db  Ab  Eb
ROOTS = [29, 25, 32, 27]
music = np.zeros((2, N))
def m_add(x, g, pan, at):
    i0 = int(at * SR); n = min(len(x), N - i0)
    if n > 0:
        music[0, i0:i0 + n] += x[:n] * g * (1 - pan); music[1, i0:i0 + n] += x[:n] * g * (1 + pan)

# pad (supersaw filtrado)
for bi in range(int(TOTAL / BAR) + 1):
    at = bi * BAR; ch = CHORDS[bi % 4]
    if at >= TOTAL: break
    x = np.zeros(int(BAR * SR) + 2000)
    for m in ch:
        for det in (-0.006, 0, 0.007):
            s = saw(note(m), BAR + 2000 / SR, det); x[:len(s)] += s
    env = np.minimum(1, tt(len(x) / SR) / 0.05) * np.minimum(1, (len(x) / SR - tt(len(x) / SR)) / 0.05)
    bright = 900 + 2500 * (1 if active(at + 0.1, 2) else 0.2)
    m_add(lp(x * env, bright), 0.035, -0.3 if bi % 2 else 0.3, at)

step = BEAT / 4
k = 0
while k * step < TOTAL - 0.4:
    at = k * step; pos = k % 16
    if active(at, 0) and pos % 4 == 0:
        d = tt(0.4); f = 45 + 110 * np.exp(-d * 28)
        kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-d * 7) + 0.4 * np.exp(-d * 400) * rng.standard_normal(len(d))
        m_add(kick, 0.9, 0, at)
    if active(at, 0) and pos in (4, 12):
        d = tt(0.25); clap = hp(rng.standard_normal(len(d)), 900) * (np.exp(-d * 25) + 0.5 * np.exp(-((d - 0.012) * 300) ** 2))
        m_add(clap, 0.32, 0.1, at)
    if active(at, 1) and pos % 2 == 0:
        d = tt(0.06 if pos % 4 else 0.12); hat = hp(rng.standard_normal(len(d)), 7000) * np.exp(-d * (60 if pos % 4 else 25))
        m_add(hat, 0.10 if pos % 4 == 2 else 0.06, 0.35, at)
    if active(at, 2) and pos % 4 == 2:
        bi = int(at / BAR) % 4; d = tt(BEAT * 0.45)
        b_ = saw(note(ROOTS[bi]), BEAT * 0.45) * 0.6 + np.sin(2 * np.pi * note(ROOTS[bi]) * d)
        m_add(lp(b_, 400 + 600 * np.exp(-d * 10).mean()) * np.minimum(1, (BEAT * 0.45 - d) / 0.02), 0.5, 0, at)
    if active(at, 3) and pos in (3, 6, 10, 14):
        bi = int(at / BAR) % 4; d = tt(0.22); x = np.zeros(len(d))
        for m in CHORDS[bi]: x += saw(note(m + 12), 0.22, rng.uniform(-0.004, 0.004))
        m_add(lp(x * np.exp(-d * 14), 3500), 0.06, rng.uniform(-0.4, 0.4), at)
    if active(at, 3) and pos % 2 == 1:   # arpegio pluck
        bi = int(at / BAR) % 4; m = CHORDS[bi][(k // 2) % 4] + 24; d = tt(0.14)
        x = np.sign(np.sin(2 * np.pi * note(m) * d)) * np.exp(-d * 30)
        m_add(lp(x, 4000), 0.025, 0.5 if k % 4 == 1 else -0.5, at)
    k += 1

# sidechain (bombeo) ligado al bombo
sc = np.ones(N)
k = 0
while k * BEAT < TOTAL:
    at = k * BEAT
    if active(at, 0):
        i0 = int(at * SR); d = tt(BEAT); n = min(len(d), N - i0)
        sc[i0:i0 + n] = np.minimum(sc[i0:i0 + n], 1 - 0.55 * np.exp(-d[:n] * 9))
    k += 1
music *= sc[None]

# ------------------------------------------------ efectos
def chime(freqs, d=0.9, g=1.0, gap=0.0):
    x = np.zeros(int((d + gap * len(freqs)) * SR))
    for i, f in enumerate(freqs):
        dd = tt(d); s = (np.sin(2 * np.pi * f * dd) + 0.3 * np.sin(2 * np.pi * 2 * f * dd)) * np.exp(-dd * 6) * np.minimum(1, dd / 0.004)
        i0 = int(i * gap * SR); x[i0:i0 + len(s)] += s
    return x * g
def whoosh(d=0.45, up=True):
    x = rng.standard_normal(int(d * SR)); e = np.sin(np.pi * tt(d) / d) ** 2
    y = np.zeros_like(x); seg = 2400
    for i in range(0, len(x), seg):
        fr = i / len(x); fc = 400 + 5000 * (fr if up else 1 - fr)
        y[i:i + seg] = lp(x[i:i + seg], fc)
    return y * e
def boom(d=2.0):
    dd = tt(d); f = 30 + 70 * np.exp(-dd * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-dd * 2.2) + lp(rng.standard_normal(len(dd)), 300) * np.exp(-dd * 6) * 2
def riser(d):
    dd = tt(d); x = rng.standard_normal(len(dd)); y = np.zeros_like(x); seg = 2400
    for i in range(0, len(x), seg): y[i:i + seg] = hp(lp(x[i:i + seg], 600 + 9000 * (i / len(x)) ** 2), 300)
    s = np.sin(2 * np.pi * np.cumsum(300 + 1500 * (dd / d) ** 2) / SR) * 0.3
    return (y + s) * (dd / d) ** 2
def click(): d = tt(0.03); return hp(rng.standard_normal(len(d)), 2000) * np.exp(-d * 250) + np.sin(2 * np.pi * 2200 * d) * np.exp(-d * 200)
def glitch_burst(d=0.25):
    x = np.zeros(int(d * SR)); i = 0
    while i < len(x):
        n = int(rng.uniform(0.008, 0.04) * SR); f = rng.choice([220, 440, 880, 1760, 3520]) * rng.uniform(0.9, 1.1)
        seg = np.sign(np.sin(2 * np.pi * f * np.arange(n) / SR)); m = len(x[i:i + n])
        x[i:i + m] = seg[:m] * rng.uniform(0.3, 1); i += n
    return x
def powerup():   # arpegio de videojuego (onda cuadrada)
    out = []
    for m in [65, 69, 72, 77, 81, 84, 89]:
        d = tt(0.055); out.append(np.sign(np.sin(2 * np.pi * note(m) * d)) * 0.6)
    x = np.concatenate(out); return x * np.minimum(1, (len(x) / SR - tt(len(x) / SR)) / 0.05)
def shutter(): d = tt(0.12); return hp(rng.standard_normal(len(d)), 1500) * (np.exp(-d * 120) + 0.6 * np.exp(-((d - 0.06) * 200) ** 2))

# notificación tecnológica + golpe inicial
add(chime([note(88), note(95)], 1.0, 0.35, 0.11), 1.0, 0, 0.08)
add(boom(1.8), 0.5, 0, 0.05)
# whoosh en cada corte
for (a, b, n) in SHOTS[1:]:
    add(whoosh(0.4), 0.14, rng.uniform(-0.5, 0.5), max(0, a - 0.28))
# caja: temblor, apertura y destello
d = tt(1.4); add(lp(rng.standard_normal(len(d)), 160) * (d / 1.4) * 3 * (1 + np.sin(2 * np.pi * 9 * d)), 0.25, 0, 3.1)
add(boom(1.2), 0.35, 0, 4.5)
add(chime([note(84), note(88), note(91), note(96)], 1.2, 0.18, 0.06), 1.0, 0.2, 4.6)
# toque NFC: clic + ding satisfactorio
TAP = 7.72
add(click(), 0.6, 0, TAP)
add(chime([note(84), note(91), note(96)], 1.1, 0.4, 0.05), 1.0, 0, TAP + 0.02)
add(chime([note(103)], 0.5, 0.15), 1.0, 0.3, TAP + 0.32)        # brillo al abrirse el enlace
add(click(), 0.3, 0, 8.45)
# portal / videojuego
add(riser(1.4), 0.25, 0, 10.0)
for at in (10.65, 10.95, 11.2): add(glitch_burst(0.18), 0.07, rng.uniform(-0.6, 0.6), at)
add(boom(1.6), 0.55, 0, 11.4)
add(powerup(), 0.1, 0, 11.45)
# toques en cada negocio
for (a, b, n) in SHOTS:
    if n.startswith("biz_") and n != "biz_any":
        p = a + 0.56 * (b - a)
        add(click(), 0.22, 0, p); add(chime([note(91), note(96)], 0.6, 0.13, 0.04), 1.0, 0, p + 0.01)
    if n == "biz_any":
        for i in range(9): add(chime([note(96 + (i % 3) * 2)], 0.25, 0.07), 1.0, (i % 3 - 1) * 0.4, a + i * 0.09)
# flotación
add(chime([note(77), note(84), note(89)], 2.5, 0.1, 0.15), 1.0, -0.2, 19.05)
add(riser(1.5), 0.22, 0, 22.5)
add(boom(1.5), 0.5, 0, 24.0)
# montaje: obturador en cada corte
for (a, b, n) in SHOTS:
    if n.startswith("m_"): add(shutter(), 0.25, rng.uniform(-0.4, 0.4), a)
# final
add(riser(1.6), 0.25, 0, 28.4)
add(boom(2.5), 0.65, 0, 30.0)
add(chime([note(77), note(84), note(89), note(93), note(96)], 2.5, 0.16, 0.09), 1.0, 0, 30.05)
add(boom(2.0), 0.55, 0, 33.0)
add(chime([note(84), note(91), note(96)], 1.6, 0.32, 0.05), 1.0, 0, 33.02)

# ------------------------------------------------ voz + ducking
with wave.open(os.path.join(HERE, "voice.wav")) as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
v = np.pad(v, (0, max(0, N - len(v))))[:N]
env = lfilter([1 - 0.9995], [1, -0.9995], np.abs(v))
env = np.convolve(env, np.ones(int(0.15 * SR)) / int(0.15 * SR), "same")
duck = 1 - 0.72 * np.clip(env / (env.max() * 0.25), 0, 1)
mus = music * duck[None]
sfx = np.stack([L, R]) * (1 - 0.5 * np.clip(env / (env.max() * 0.25), 0, 1))[None]
mix = mus * 0.75 + sfx * 0.7 + v[None] * 1.0
import json
for a, b, _ in json.load(open(os.path.join(HERE, "tmp", "voice_timing.json"))):
    i0, i1 = int(a * SR), int(b * SR)
    rv = np.sqrt(np.mean((v[i0:i1] * 1.0) ** 2)); rb = np.sqrt(np.mean(((mus * 0.75 + sfx * 0.7)[:, i0:i1]) ** 2))
    print(f"  voz/fondo {a:5.1f}s: {20*np.log10(rv/rb):+.1f} dB")
fade = np.clip((TOTAL + 0.1 - t) / 0.5, 0, 1)
mix *= fade[None]
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
mix /= np.abs(mix).max() / 0.92
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix.T * 32767).astype(np.int16).tobytes())
print("ok", N / SR)
