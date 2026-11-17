"""Banda sonora: música cinematográfica sintetizada + efectos sincronizados + voz con ducking.
Salida: mezcla.wav (48 kHz estéreo)."""
import os, sys, subprocess, math
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, fftconvolve
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from timeline import SENTENCES, TOTAL, word_time
import render as R

SR = 48000
N = int(SR * (TOTAL + 0.2))
t = np.arange(N) / SR
rng = np.random.default_rng(11)

def hz(note):  # 'D3', 'F#4'...
    names = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    n, o = note[:-1], int(note[-1]); return 440 * 2 ** ((names[n] + 12 * (o + 1) - 69) / 12)

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)

def seg(a, b, fade_in=0.5, fade_out=0.5):
    return np.clip(np.minimum((t - a) / max(fade_in, 1e-3), (b - t) / max(fade_out, 1e-3)), 0, 1)

def place(x, at, buf):
    i = int(at * SR); n = min(len(x), N - i)
    if n > 0 and i >= 0: buf[i:i + n] += x[:n]

MUS_L = np.zeros(N); MUS_R = np.zeros(N); SFX_L = np.zeros(N); SFX_R = np.zeros(N)
def mus(x, g=1.0, pan=0.0):
    global MUS_L, MUS_R
    MUS_L += x * g * math.sqrt(0.5 * (1 - pan)); MUS_R += x * g * math.sqrt(0.5 * (1 + pan))
def sfx(x, g=1.0, pan=0.0, at=None):
    buf = np.zeros(N)
    if at is None: buf[:len(x)] += x[:N]
    else: place(x, at, buf)
    global SFX_L, SFX_R
    SFX_L += buf * g * math.sqrt(0.5 * (1 - pan)); SFX_R += buf * g * math.sqrt(0.5 * (1 + pan))

# ------------------------------------------------------------------ secciones (desde la narración)
T_FREEZE = SENTENCES[5]["start"] - 0.3        # llega el invierno
T_STOP = SENTENCES[9]["start"] - 0.1          # el corazón se detiene
T_SILENT = SENTENCES[11]["end"]               # "parece muerta"
T_HOPE = SENTENCES[12]["start"]               # "pero no lo está"
T_ALASKA = SENTENCES[16]["start"] - 0.2
T_SPRING = SENTENCES[17]["start"] - 0.25
T_FINAL = SENTENCES[20]["start"] - 0.2
T_LAST = SENTENCES[23]["start"]

# ------------------------------------------------------------------ instrumentos
def pad(freqs, a, b, g=0.1, bright=1200, fi=1.5, fo=1.5, pan=0.0):
    """Cuerdas/pad: sierras desafinadas filtradas con vibrato lento."""
    i0, i1 = int(max(0, a - fo) * SR), int(min(TOTAL + 0.2, b + fo) * SR)
    tt = t[i0:i1]; x = np.zeros(len(tt))
    for f in freqs:
        for det in (-0.25, 0.0, 0.27):
            ff = f * 2 ** (det / 100 * 12 / 12) * (1 + 0.002 * np.sin(2 * np.pi * 5.1 * tt + f))
            ph = np.cumsum(ff) / SR
            x += (2 * (ph % 1) - 1) * 0.33
    x = lp(x, bright, 2)
    env = seg(a, b, fi, fo)[i0:i1]
    full = np.zeros(N); full[i0:i1] = x * env
    mus(full, g / max(1, len(freqs)) * 2.2, pan)

def bell(f, at, g=0.2, dec=2.5, pan=0.0):
    n = int(SR * dec * 1.5); tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * tt + 1.8 * np.sin(2 * np.pi * f * 3.5 * tt) * np.exp(-tt * 3))
         + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 2)) * np.exp(-tt / dec * 2.2) * np.minimum(1, tt / 0.003)
    buf = np.zeros(N); place(x, at, buf); mus(buf, g, pan)

def pluck(f, at, g=0.15, pan=0.0):
    n = int(SR * 1.6); tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * k * tt) * np.exp(-tt * (2 + 2.5 * k)) / k for k in range(1, 6)) * np.minimum(1, tt / 0.002)
    buf = np.zeros(N); place(x, at, buf); mus(buf, g, pan)

def boom(at, g=1.0, f0=110, f1=32, dur=2.5):
    n = int(SR * dur); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt * 14)) / SR
    x = np.sin(ph) * np.exp(-tt * 2.2) + lp(rng.standard_normal(n), 900) * np.exp(-tt * 9) * 0.8
    buf = np.zeros(N); place(x, at, buf); mus(buf, g)

def tom(at, g=0.5, f=70):
    n = int(SR * 0.6); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * np.exp(-tt * 30))) / SR) * np.exp(-tt * 7)
    buf = np.zeros(N); place(x, at, buf); mus(buf, g)

def riser(end, dur=2.0, g=0.15):
    n = int(SR * dur); tt = np.arange(n) / SR; p = tt / dur
    x = rng.standard_normal(n); out = np.zeros(n)
    for k in range(8):  # barrido de filtro por tramos
        a, b = k * n // 8, (k + 1) * n // 8
        out[a:b] = bp(x, 300 + 5000 * (k / 8) ** 2, 800 + 9000 * ((k + 1) / 8) ** 2)[a:b]
    out *= p ** 2.5
    buf = np.zeros(N); place(out, end - dur, buf); mus(buf, g)

def reverse_swell(end, f, dur=1.4, g=0.12):
    n = int(SR * dur); tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * k * tt) / k for k in (1, 2, 3)) * (tt / dur) ** 3
    buf = np.zeros(N); place(x, end - dur, buf); mus(buf, g)

# ------------------------------------------------------------------ música
# 1) Misterio frío (gancho + presentación): Re menor con 2ª menor inquietante
pad([hz("D2"), hz("A2"), hz("D3")], 0, T_FREEZE + 1, 0.16, 700, fi=0.3)
pad([hz("F3"), hz("A3")], 2.0, T_FREEZE, 0.07, 1500)
pad([hz("Bb3")], 4.3, 6.0, 0.05, 1800)                       # tensión en "corazón detenido"
for k, n_ in enumerate(["D5", "A5", "F5", "E5", "D5", "A4", "F5", "D6"]):
    bell(hz(n_), 0.4 + k * 1.05, 0.06, 3.0, pan=-0.4 + 0.1 * k)
boom(0.02, 0.9)
riser(SENTENCES[2]["start"] + 0.05, 1.6, 0.10)
boom(SENTENCES[2]["start"] + 0.05, 0.5)
reverse_swell(SENTENCES[3]["start"] + 0.05, hz("D4"), 1.0, 0.10)

# 2) Congelación: progresión Dm – Bb – Gm – A, el pulso crece
prog = [("D2", ["D3", "F3", "A3"]), ("Bb1", ["Bb2", "D3", "F3"]), ("G1", ["G2", "Bb2", "D3"]), ("A1", ["A2", "C#3", "E3"])]
bar = 60 / 84 * 4
x0 = T_FREEZE; k = 0
while x0 < T_STOP - 0.2:
    root, ch = prog[k % 4]; x1 = min(x0 + bar, T_STOP)
    pad([hz(root)], x0, x1, 0.14, 500, 0.3, 0.3)
    pad([hz(n_) for n_ in ch], x0, x1, 0.09 + 0.02 * min(k, 3), 1300 + 300 * k, 0.4, 0.4)
    for s in range(8):                                       # arpegio de hielo
        at = x0 + s * bar / 8
        if at < x1: pluck(hz(ch[s % 3][:-1] + str(int(ch[s % 3][-1]) + 2)), at, 0.035 + 0.01 * min(k, 3), pan=0.5 * math.sin(s))
    for s in range(4 if k < 2 else 8):                       # pulso de tambor
        at = x0 + s * bar / (4 if k < 2 else 8)
        if at < x1 - 0.05: tom(at, 0.18 + 0.05 * k * (s % 2 == 0))
    x0 += bar; k += 1
riser(T_STOP, 2.2, 0.14)
boom(T_STOP, 1.0)

# 3) Silencio dramático: corazón parado → casi nada (un drone muy grave y viento)
pad([hz("D1"), hz("A1")], T_STOP, T_HOPE, 0.10, 220, 0.2, 0.4)

# 4) "Pero no lo está": la ciencia, esperanza tensa (F – C – Dm – Bb), pulso de corcheas
prog2 = [("F1", ["F3", "A3", "C4"]), ("C2", ["C3", "E3", "G3"]), ("D2", ["D3", "F3", "A3"]), ("Bb1", ["Bb2", "D3", "F3"])]
boom(T_HOPE, 0.8, 140, 40); reverse_swell(T_HOPE + 0.02, hz("F4"), 0.8, 0.12)
x0 = T_HOPE + 0.05; k = 0
while x0 < T_ALASKA - 0.1:
    root, ch = prog2[k % 4]; x1 = min(x0 + bar, T_ALASKA)
    pad([hz(root)], x0, x1, 0.14, 500, 0.3, 0.3)
    pad([hz(n_) for n_ in ch], x0, x1, 0.11, 2000, 0.3, 0.4)
    for s in range(8):
        at = x0 + s * bar / 8
        if at < x1: pluck(hz(ch[(s * 2) % 3][:-1] + str(int(ch[(s * 2) % 3][-1]) + 2)), at, 0.05, pan=0.4 * math.cos(s))
        if at < x1 - 0.05: tom(at, 0.14 if s % 2 else 0.26, 60)
    x0 += bar; k += 1
riser(T_ALASKA, 1.8, 0.10)

# 5) Alaska: frío inmenso, pad grave y campanas lejanas
pad([hz("D2"), hz("A2"), hz("E3"), hz("A3")], T_ALASKA, T_SPRING, 0.13, 900, 0.5, 0.6)
for k, n_ in enumerate(["A5", "E5", "D6", "A5", "E6"]):
    bell(hz(n_), T_ALASKA + 0.3 + k * 1.1, 0.05, 3.5, pan=0.6 - 0.3 * k)
boom(word_time(16, "dieciocho") - 0.05, 0.6)

# 6) Primavera y asombro: Re MAYOR (D – A – Bm – G), cuerdas que crecen y arpegios brillantes
riser(T_SPRING, 1.5, 0.12); reverse_swell(T_SPRING, hz("A4"), 1.5, 0.12)
prog3 = [("D2", ["D3", "F#3", "A3", "D4"]), ("A1", ["A2", "C#3", "E3", "A3"]), ("B1", ["B2", "D3", "F#3", "B3"]), ("G1", ["G2", "B2", "D3", "G3"])]
x0 = T_SPRING; k = 0
while x0 < T_LAST:
    root, ch = prog3[k % 4]; x1 = min(x0 + bar, T_LAST + 0.3)
    lift = min(1.0, (x0 - T_SPRING) / (T_LAST - T_SPRING))
    pad([hz(root)], x0, x1, 0.16, 600, 0.3, 0.4)
    pad([hz(n_) for n_ in ch], x0, x1, 0.10 + 0.08 * lift, 1600 + 2500 * lift, 0.4, 0.5)
    for s in range(8):
        at = x0 + s * bar / 8
        nn = ch[s % 4]; f = hz(nn[:-1] + str(int(nn[-1]) + 2))
        if at < x1: pluck(f, at, 0.05 + 0.03 * lift, pan=0.5 * math.sin(s * 1.3))
        if at < x1 - 0.05 and x0 > T_SPRING + bar: tom(at, (0.12 if s % 2 else 0.24) * (0.6 + 0.6 * lift), 65)
    bell(hz(ch[-1][:-1] + "6"), x0, 0.05, 3.0)
    x0 += bar; k += 1
boom(SENTENCES[17]["start"] + 0.0, 0.5, 120, 40)
riser(T_LAST, 1.6, 0.14)
# Final: acorde de Re mayor enorme y cola
boom(T_LAST, 1.1, 120, 30, 3.5)
pad([hz("D2"), hz("A2"), hz("D3"), hz("F#3"), hz("A3"), hz("D4"), hz("F#4")], T_LAST, TOTAL - 0.2, 0.28, 3500, 0.05, 1.6)
for k, n_ in enumerate(["D5", "F#5", "A5", "D6", "F#6", "A6"]):
    bell(hz(n_), T_LAST + 0.08 * k, 0.06, 4.0, pan=-0.5 + 0.2 * k)

# ------------------------------------------------------------------ efectos (sincronizados con los planos)
def crack_sfx(dur=0.6, dens=60):
    n = int(SR * dur); x = np.zeros(n)
    for j in range(dens):
        i = int(rng.uniform(0, 1) ** 1.8 * (n - 600)); m = int(SR * rng.uniform(0.002, 0.012))
        x[i:i + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / (m / 4)) * rng.uniform(0.2, 1)
    x = hp(x, 1200) + 0.4 * bp(x, 200, 900)
    return x

def whoosh(dur=0.6):
    n = int(SR * dur); tt = np.arange(n) / SR; p = tt / dur
    x = rng.standard_normal(n); env = np.sin(np.pi * p) ** 2
    return bp(x, 400, 4000) * env

def heartbeat():
    n = int(SR * 0.5); tt = np.arange(n) / SR
    def thump(f, d): return np.sin(2 * np.pi * np.cumsum(f * (1 + 1.2 * np.exp(-tt * 25))) / SR) * np.exp(-tt / d)
    x = thump(55, 0.07); y = np.zeros(n); k = int(0.17 * SR); y[k:] = thump(50, 0.08)[:n - k] * 0.75
    return lp(x + y, 300)

def beep(f=1000, dur=0.11):
    n = int(SR * dur); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * tt) * np.minimum(1, np.minimum(tt, dur - tt) / 0.005)

def drip():
    n = int(SR * 0.18); tt = np.arange(n) / SR; f = rng.uniform(900, 1600)
    return np.sin(2 * np.pi * f * (1 + 2.5 * tt) * tt) * np.exp(-tt * 28)

def shimmer(dur=1.5):
    n = int(SR * dur); tt = np.arange(n) / SR; x = np.zeros(n)
    for j in range(25):
        f = rng.uniform(3000, 8000); a = rng.uniform(0, dur * 0.8)
        x += np.sin(2 * np.pi * f * tt) * np.exp(-np.maximum(0, tt - a) * 9) * (tt > a) * 0.1
    return x

def wind(a, b, g):
    x = lp(rng.standard_normal(N), 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t))
    sfx(hp(x, 120) * seg(a, b, 1.0, 1.0), g, -0.3)
    x = lp(rng.standard_normal(N), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * t + 1))
    sfx(hp(x, 120) * seg(a, b, 1.0, 1.0), g, 0.3)

starts = {s[1].__name__: s[0] for s in R.SHOTS}
nexts = {R.SHOTS[i][1].__name__: (R.SHOTS[i + 1][0] if i + 1 < len(R.SHOTS) else TOTAL) for i in range(len(R.SHOTS))}

# whoosh / impacto en cada cambio de plano
for (a, fn, _y, kind) in R.SHOTS[1:]:
    if kind in ("fade", "zoom", "flash"):
        sfx(whoosh(0.55 if kind != "flash" else 0.35), 0.10 if kind == "fade" else 0.16, rng.uniform(-0.5, 0.5), at=a - 0.3)
# hielo
sfx(crack_sfx(1.0, 90), 0.55, 0.0, at=0.0)
sfx(crack_sfx(0.5, 30), 0.35, 0.3, at=starts["p_hook_side"] + 0.05)
sfx(shimmer(2.0), 0.25, -0.2, at=starts["p_hook_side"])
for k in range(5):
    sfx(crack_sfx(0.45, 25), 0.30, rng.uniform(-0.6, 0.6), at=starts["p_freeze"] + 0.3 + k * 0.55)
sfx(shimmer(2.5), 0.3, 0.2, at=starts["p_frost_leaves"])
sfx(shimmer(2.0), 0.25, 0.0, at=starts["p_tissue"] + 0.5)
for k in range(4):
    sfx(crack_sfx(0.3, 14), 0.18, rng.uniform(-0.6, 0.6), at=starts["p_cells"] + 0.8 + k * 0.6)
wind(starts["p_hide"], starts["p_freeze"] + 1, 0.10)
wind(starts["p_dead"] - 0.2, starts["p_not_dead"], 0.13)
wind(starts["p_alaska"], starts["p_spring"] + 0.5, 0.14)
# ECG + latidos (mismos tiempos que la imagen)
a = starts["p_flatline"]
for b in (0.0, 0.85):
    tb = a + b - 0.6 + 0.0
    if tb >= a - 0.05: sfx(beep(), 0.07, 0, at=tb)
sfx(beep(1000, starts["p_revive"] - a - 0.05) * np.linspace(1, 0.3, int(SR * (starts["p_revive"] - a - 0.05))), 0.05, 0, at=a + 0.3)
a = starts["p_heart_stop"]
for b in (0.0, 0.75):
    sfx(heartbeat(), 0.9, 0, at=a + b); sfx(beep(), 0.05, 0, at=a + b)
sfx(beep(1000, 1.6) * np.linspace(1, 0, int(SR * 1.6)), 0.05, 0, at=a + 1.5)   # línea plana
a = starts["p_heart_back"]; t_l = word_time(18, "latir") - a
for k in range(6):
    tb = a + t_l - 0.15 + k * 0.8
    if tb < nexts["p_heart_back"] + 0.4:
        sfx(heartbeat(), 0.9, 0, at=tb); sfx(beep(), 0.06, 0, at=tb)
# latido lejano en "pero no lo está"
sfx(heartbeat(), 0.7, 0, at=starts["p_not_dead"] + 0.5)
# deshielo: gotas
a = starts["p_thaw"]
for k in range(16):
    sfx(drip(), 0.12, rng.uniform(-0.7, 0.7), at=a + rng.uniform(0, nexts["p_thaw"] - a + 0.5))
for k in range(8):
    sfx(drip(), 0.07, rng.uniform(-0.7, 0.7), at=starts["p_spring"] + rng.uniform(0, 1.5))
# salto: chapoteo
n = int(SR * 0.7); tt = np.arange(n) / SR
splash = bp(rng.standard_normal(n), 500, 6000) * np.exp(-tt * 6) * np.minimum(1, tt / 0.01)
sfx(whoosh(0.4), 0.25, 0.3, at=starts["p_leap"] - 0.1)
sfx(splash, 0.25, 0.2, at=starts["p_leap"] + 0.45)
# pájaros de primavera (gorjeos sintéticos suaves)
for k in range(10):
    at = starts["p_pond"] - 1 + k * rng.uniform(0.6, 1.4)
    n = int(SR * 0.25); tt = np.arange(n) / SR; f0 = rng.uniform(2800, 4200)
    ch = np.sin(2 * np.pi * np.cumsum(f0 + 900 * np.sin(2 * np.pi * 18 * tt)) / SR) * np.sin(np.pi * tt / 0.25) ** 2
    sfx(ch, 0.025, rng.uniform(-0.8, 0.8), at=at)

# ------------------------------------------------------------------ voz
def load_voice():
    v = np.zeros(N)
    for s in SENTENCES:
        p = os.path.join(HERE, "voz", f"{s['i']:02d}.mp3")
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
        x = np.frombuffer(raw, np.float32).astype(np.float64)
        x = x[int(s["clip_in"] * SR):int(s["clip_out"] * SR)]
        fade = np.ones(len(x)); m = int(0.012 * SR); fade[:m] = np.linspace(0, 1, m); fade[-m:] = np.linspace(1, 0, m)
        place(x * fade, s["start"], v)
    v = hp(v, 75)
    # ligera presencia (+2 dB ~3 kHz) y calidez
    v = v + 0.25 * bp(v, 2500, 5000) + 0.15 * bp(v, 150, 350)
    # compresión suave
    env = np.sqrt(lfilter([0.002], [1, -0.998], v ** 2) + 1e-9)
    gain = np.minimum(1.0, (0.12 / env) ** 0.35)
    v = v * gain
    return v / (np.abs(v).max() + 1e-9) * 0.9

V = load_voice()
# reverb corta de sala (muy sutil) para que no suene "seca"
n = int(0.6 * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 9); ir[0] = 0
Vrev = fftconvolve(V, ir)[:N] * 0.025

# ducking: la música baja ~9 dB mientras habla la voz
env = np.abs(V); att = lfilter([1 - 0.995], [1, -0.995], env)
env_s = np.maximum.accumulate(np.zeros(1))  # placeholder
k_rel = math.exp(-1 / (0.35 * SR)); k_att = math.exp(-1 / (0.03 * SR))
e = np.zeros(N); acc = 0.0
envd = lp(env, 30)
for i in range(0, N, 48):      # envolvente a 1 kHz y luego interpolada (rápido)
    x = envd[i]
    acc = x + (acc - x) * (k_att ** 48 if x > acc else k_rel ** 48)
    e[i:i + 48] = acc
e = np.clip(e / (np.percentile(e[e > 1e-4], 90) + 1e-9), 0, 1)
duck_m = 1 - 0.62 * e     # ≈ −8.5 dB
duck_s = 1 - 0.35 * e

# reverb larga para la música (sensación cinematográfica)
def big_reverb(x, dur=3.0, mix=0.35, seed=0):
    r = np.random.default_rng(seed); n = int(dur * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR * (6.9 / dur)); ir = lp(ir, 6000)
    ir /= np.sqrt((ir ** 2).sum())
    return x * (1 - mix) + fftconvolve(x, ir)[:len(x)] * mix * 1.2

ML = big_reverb(MUS_L, seed=1); MR = big_reverb(MUS_R, seed=2)
SL = big_reverb(SFX_L, 1.5, 0.2, 3); SR_ = big_reverb(SFX_R, 1.5, 0.2, 4)
m_norm = max(np.abs(ML).max(), np.abs(MR).max()) + 1e-9
s_norm = max(np.abs(SL).max(), np.abs(SR_).max()) + 1e-9
L = ML / m_norm * 0.55 * duck_m + SL / s_norm * 0.45 * duck_s + V * 0.95 + Vrev
Rr = MR / m_norm * 0.55 * duck_m + SR_ / s_norm * 0.45 * duck_s + V * 0.95 + Vrev
out = np.stack([L, Rr], 1)
fade = np.clip((TOTAL - t) / 0.8, 0, 1)[:, None] * np.clip(t / 0.01, 0, 1)[:, None]
out = np.tanh(out * fade * 1.1) / np.tanh(1.1)
out /= np.abs(out).max() / 0.95

import wave
with wave.open(os.path.join(HERE, "mezcla.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
# también la voz sola (útil para revisar / subtitular en otras apps)
with wave.open(os.path.join(HERE, "voz_sola.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((V * 32767 * 0.95).astype(np.int16).tobytes())
print("mezcla.wav", round(len(out) / SR, 2), "s")

if os.environ.get("AUDIO_DEBUG"):
    bed = (ML / m_norm * 0.55 * duck_m + SL / s_norm * 0.45 * duck_s)
    sp = e > 0.3
    db = lambda z: 20 * np.log10(np.sqrt((z ** 2).mean()) + 1e-9)
    print("voz (hablando) %.1f dB | fondo bajo la voz %.1f dB | fondo en pausas %.1f dB" % (db(V[sp]), db(bed[sp]), db(bed[~sp])))
