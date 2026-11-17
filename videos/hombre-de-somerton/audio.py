# Música de misterio + efectos sincronizados + voz en off con "ducking" (la música baja cuando habla la voz).
# Salida: music_sfx.wav (sin voz) y mix.wav (mezcla final).
import numpy as np, wave, sys, os, subprocess
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import TOTAL, SCENES, shot_timeline, shot_start, hits, voice_starts

SR = 48000
N = int(SR * (TOTAL + 0.5))
t = np.arange(N) / SR
rng = np.random.default_rng(9)

def lp(x, a): return lfilter([a], [1, a - 1], x)
def hp(x, a): return x - lp(x, a)
def seg(a, b, fade=0.5): return np.clip(np.minimum((t - a) / fade, (b - t) / fade), 0, 1)

L = np.zeros(N); R = np.zeros(N)
def add(x, gain=1.0, pan=0.0):
    global L, R
    L += x * gain * (1 - pan); R += x * gain * (1 + pan)

def at(x0, sig):
    x = np.zeros(N); i0 = int(x0 * SR); n = min(len(sig), N - i0)
    if n > 0: x[i0:i0 + n] = sig[:n]
    return x

# --- drone disonante (Re menor con segunda menor) + viento helado
for f, g in [(41.2, 0.34), (41.45, 0.26), (82.4, 0.14), (87.3, 0.06), (123.5, 0.05)]:
    add(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t + f)), g * 0.6)
for pan in (-0.4, 0.4):
    w = lp(rng.standard_normal(N), 0.006) * 10
    w *= 0.4 + 0.6 * (0.5 + 0.5 * np.sin(2 * np.pi * (0.08 + pan * 0.03) * t + pan * 3)) ** 2
    add(hp(w, 0.0005), 0.07, pan)

# --- caja de música desafinada (melodía en Re menor, muy lejana)
mel = [76, 79, 83, 82, 79, 76, 75, 76, 0, 76, 79, 83, 84, 83, 79, 78]
step = 0.62
def bell(f, dur=1.6):
    tt = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 6)) * np.exp(-tt * 3.2)
k, x = 0, 3.5
while x < TOTAL - 4:
    m = mel[k % len(mel)]
    if m: add(at(x, bell(440 * 2 ** ((m - 69) / 12) * (1 + 0.004 * np.sin(k)))), 0.022, 0.3 * np.sin(k))
    k += 1; x += step

# --- latido grave que acelera hacia el final
def thump(f0=60, f1=38, dur=0.3, g=1.0):
    tt = np.arange(int(dur * SR)) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt * 18)) / SR
    return np.sin(ph) * np.exp(-tt * 10) * g
x = 6.0
while x < TOTAL - 1.5:
    add(at(x, thump()), 0.35); add(at(x + 0.17, thump(55, 36, 0.3, 0.7)), 0.3)
    x += 1.15 - 0.45 * (x / TOTAL)

# --- golpes (boom) en las revelaciones + subidas previas
def boom():
    tt = np.arange(int(2.4 * SR)) / SR
    ph = 2 * np.pi * np.cumsum(28 + 70 * np.exp(-tt * 6)) / SR
    nz = lp(rng.standard_normal(len(tt)), 0.06) * np.exp(-tt * 5) * 3
    return np.sin(ph) * np.exp(-tt * 1.6) + nz
for h in hits():
    add(at(h, boom()), 0.6)
    a = max(0, h - 1.5); dd = h - a
    if dd > 0.5:
        r = rng.standard_normal(N); m = seg(a, h + 0.02, 0.02) * np.clip((t - a) / dd, 0, 1) ** 2
        add(hp(r, 0.05) * m, 0.07)

# --- olas del mar (playa)
for name in ("beach_body", "beach_fog", "title_1948", "end_card"):
    a0, b0 = shot_start(name)
    sw = lp(rng.standard_normal(N), 0.02) * 6 * (0.4 + 0.6 * np.clip(np.sin(2 * np.pi * t / 4.2), 0, 1) ** 2)
    add(sw * seg(a0 - 0.2, b0 + 0.3, 0.4), 0.16, -0.2)

# --- tirón de la etiqueta (descosido)
a0, b0 = shot_start("label_tear")
for j in range(14):
    x0 = a0 + (b0 - a0) * (0.28 + 0.4 * j / 14)
    add(at(x0, hp(rng.standard_normal(int(0.03 * SR)), 0.2) * np.exp(-np.arange(int(0.03 * SR)) / 300)), 0.35, 0.2)

# --- papel desenrollándose
a0, b0 = shot_start("pocket")
pp = hp(rng.standard_normal(N), 0.25) * (rng.random(N) > 0.8) * seg(a0 + (b0 - a0) * 0.3, a0 + (b0 - a0) * 0.7, 0.1)
add(lp(pp, 0.6), 0.25)

# --- máquina de escribir (informes)
for name, s0, s1 in (("autopsy", 0.0, 0.55), ("name", 0.0, 0.35)):
    a0, b0 = shot_start(name); n = 22
    for j in range(n):
        x0 = a0 + (b0 - a0) * (s0 + (s1 - s0) * j / n) + rng.uniform(0, 0.02)
        add(at(x0, hp(rng.standard_normal(int(0.02 * SR)), 0.4) * np.exp(-np.arange(int(0.02 * SR)) / 150)), 0.28)
for name, f in (("autopsy", 0.62), ("name", 0.5)):   # sello
    a0, b0 = shot_start(name); add(at(a0 + (b0 - a0) * f, thump(120, 50, 0.25, 1.0)), 0.6)

# --- disco del teléfono (clics al volver)
a0, b0 = shot_start("phone")
for s0, e0 in ((0.05, 0.25), (0.3, 0.5), (0.55, 0.8)):
    x0 = a0 + (b0 - a0) * (s0 + e0) / 2
    while x0 < a0 + (b0 - a0) * e0:
        add(at(x0, hp(rng.standard_normal(int(0.006 * SR)), 0.3)), 0.35); x0 += 0.055

# --- lluvia (coche y casa)
for name in ("car", "house"):
    a0, b0 = shot_start(name)
    rn = hp(rng.standard_normal(N), 0.2) * (0.6 + 0.4 * rng.random(N))
    add(rn * seg(a0, b0, 0.15), 0.05, 0.1); add(lp(rng.standard_normal(N), 0.05) * seg(a0, b0, 0.15), 0.03)

# --- zumbido eléctrico en el código
for name in ("code_zoom", "code_glow"):
    a0, b0 = shot_start(name)
    add(np.sign(np.sin(2 * np.pi * 50 * t)) * 0.3 * seg(a0, b0, 0.05) * (0.6 + 0.4 * (rng.random(N) > 0.5)), 0.05)

# --- cierres de la maleta
a0, b0 = shot_start("suitcase")
for f in (0.2, 0.26):
    add(at(a0 + (b0 - a0) * f, hp(rng.standard_normal(int(0.012 * SR)), 0.3) * np.exp(-np.arange(int(0.012 * SR)) / 100)), 0.6)

# --- woosh en cada corte
for (a, b, s) in shot_timeline()[1:]:
    x = rng.standard_normal(N); m = np.exp(-((t - a) / 0.13) ** 2)
    add(hp(x, 0.1) * m, 0.05, rng.uniform(-0.5, 0.5))

# --- máster de la música
fade = np.clip((TOTAL + 0.4 - t) / 1.2, 0, 1) * np.clip(t / 0.02, 0, 1)
music = np.stack([L, R], 1) * fade[:, None]
music = np.tanh(music * 1.5) / np.tanh(1.5)
music /= np.abs(music).max() / 0.85

def write(path, st):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
write(os.path.join(HERE, "music_sfx.wav"), music)

# --- voz + ducking
voice = np.zeros(N)
for i, s0 in enumerate(voice_starts()):
    p = os.path.join(HERE, "voz", f"escena_{i:02}.wav")
    if not os.path.exists(p): print("sin voz:", p); continue
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"])
    v = np.frombuffer(raw, np.int16) / 32768
    voice += at(s0, v)
if np.abs(voice).max() > 0:
    voice /= np.abs(voice).max() / 0.95
    envv = lp(lp(np.abs(voice), 0.0015), 0.0015)
    envv = np.clip(envv / (envv.max() * 0.25), 0, 1)
    duck = 1 - 0.68 * envv                         # música a ~-10 dB bajo la voz
    mix = music * duck[:, None] * 0.75 + voice[:, None] * 0.9
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    mix /= np.abs(mix).max() / 0.95
else:
    mix = music
write(os.path.join(HERE, "mix.wav"), mix)
print("ok", N / SR)
