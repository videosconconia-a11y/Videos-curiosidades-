# Música épica de ciencia ficción + documental + efectos (ovni, alarma, luz) + locución con ducking -> mix.wav
# Todo sintetizado con numpy (sin samples externos). 120 BPM, La menor.
import numpy as np, wave, sys, os, json
from scipy.signal import lfilter, butter, sosfilt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import TOTAL, SHOTS, HITS

SR = 48000
N = int(SR * (TOTAL + 0.6))
t = np.arange(N) / SR
rng = np.random.default_rng(1497)
BEAT = 0.5

def hz(n): return 440.0 * 2 ** ((n - 69) / 12)          # MIDI -> Hz
def lp(x, fc):
    return sosfilt(butter(2, min(fc, SR / 2 - 100) / (SR / 2), "low", output="sos"), x)
def hp(x, fc):
    return sosfilt(butter(2, fc / (SR / 2), "high", output="sos"), x)
def seg(a, b, fade=0.05):
    return np.clip(np.minimum((t - a) / fade, (b - t) / fade), 0, 1)
def at(x, start, buf):
    i0 = int(start * SR)
    if i0 >= N: return
    n = min(len(x), N - i0); buf[i0:i0 + n] += x[:n]
def tt(d): return np.arange(int(d * SR)) / SR

MUS_L = np.zeros(N); MUS_R = np.zeros(N)   # música (se duckea)
SFX_L = np.zeros(N); SFX_R = np.zeros(N)   # efectos (no se duckean tanto)
def put(x, start, g=1.0, pan=0.0, sfx=False):
    L, R = (SFX_L, SFX_R) if sfx else (MUS_L, MUS_R)
    at(x * g * (1 - pan) , start, L); at(x * g * (1 + pan), start, R)

# ------------------------------------------------------------- instrumentos
def kick(g=1.0):
    d = tt(0.45); f = 45 + 130 * np.exp(-d * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-d * 7.5)
    x[:240] += rng.standard_normal(240) * 0.4 * np.linspace(1, 0, 240)
    return np.tanh(x * 1.8) * g
def snare(g=1.0):
    d = tt(0.32); n = hp(rng.standard_normal(len(d)), 1500) * np.exp(-d * 14)
    b = np.sin(2 * np.pi * 190 * d) * np.exp(-d * 22)
    return (n * 0.7 + b * 0.6) * g
def hat(g=1.0, open_=False):
    d = tt(0.25 if open_ else 0.06); return hp(rng.standard_normal(len(d)), 7000) * np.exp(-d * (12 if open_ else 70)) * g
def clap(g=1.0):
    d = tt(0.3); n = hp(rng.standard_normal(len(d)), 1100)
    e = sum(np.exp(-np.clip(d - o, 0, None) * 60) * (d >= o) for o in (0, 0.012, 0.024)) * 0.5 + np.exp(-d * 9) * 0.5
    return lp(n * e, 6000) * g
def saw(f, d, det=0.0):
    ph = (f * (1 + det)) * tt(d); return 2 * (ph % 1) - 1
def supersaw(f, d, voices=5, spread=0.012):
    x = sum(saw(f, d, spread * (k - voices // 2) / (voices // 2)) for k in range(voices)); return x / voices
def pluck(n, d=0.22, g=1.0, cut=2500):
    x = supersaw(hz(n), d, 3, 0.006); e = np.exp(-tt(d) * 14)
    return lp(x * e, cut) * g
def bassnote(n, d, g=1.0, cut=900):
    x = saw(hz(n), d) * 0.6 + np.sin(2 * np.pi * hz(n - 12) * tt(d)) * 0.8
    e = np.minimum(1, tt(d) / 0.005) * np.exp(-tt(d) * 3)
    return np.tanh(lp(x, cut) * e * 1.5) * g
def pad(notes, d, g=1.0, cut=1800, att=0.4):
    x = sum(supersaw(hz(n), d, 5, 0.01) for n in notes) / len(notes)
    e = np.minimum(1, tt(d) / att) * np.minimum(1, (d - tt(d)) / 0.3)
    return lp(x, cut) * e * g
def braam(n=33, d=2.6, g=1.0):
    x = sum(supersaw(hz(m), d, 7, 0.02) for m in (n, n + 12, n + 19)) / 3
    sweep = 300 + 2200 * np.exp(-tt(d) * 2.2)
    y = np.zeros_like(x); # filtro variable aproximado en bloques
    B = 2400
    for i in range(0, len(x), B):
        y[i:i + B] = lp(x[max(0, i - 600):i + B], sweep[i])[-len(x[i:i + B]):]
    e = np.minimum(1, tt(d) / 0.02) * np.exp(-tt(d) * 1.1)
    return np.tanh(y * e * 2.2) * g
def boom(g=1.0, d=2.5):
    s = tt(d); f = 28 + 70 * np.exp(-s * 6)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-s * 1.6)
    n = lp(rng.standard_normal(len(s)), 400) * np.exp(-s * 4) * 1.5
    return np.tanh((x + n) * 1.6) * g
def riser(d=2.0, g=1.0):
    s = tt(d); p = s / d
    n = rng.standard_normal(len(s)); y = np.zeros_like(n)
    for i in range(0, len(n), 2400):
        y[i:i + 2400] = hp(lp(n[i:i + 2400], 600 + 9000 * p[i] ** 2), 200)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * p ** 2) / SR) * 0.3
    return (y + tone) * p ** 2 * g
def whoosh(d=0.35, g=1.0):
    s = tt(d); n = rng.standard_normal(len(s)); y = np.zeros_like(n)
    for i in range(0, len(n), 960):
        y[i:i + 960] = lp(n[i:i + 960], 400 + 6000 * np.sin(np.pi * s[i] / d))
    return y * np.sin(np.pi * s / d) ** 2 * g
def glitch(d=0.3, g=1.0):
    s = tt(d); out = np.zeros(len(s)); i = 0
    while i < len(s):
        L = int(rng.uniform(0.008, 0.04) * SR)
        kind = rng.integers(3); seg_t = s[i:i + L] - s[i]
        if kind == 0: piece = np.sign(np.sin(2 * np.pi * rng.uniform(80, 1500) * seg_t))
        elif kind == 1: piece = rng.standard_normal(len(seg_t))
        else: piece = np.zeros(len(seg_t))
        out[i:i + L] = piece[:len(out[i:i + L])] * 0.6; i += L
    return lp(out, 7000) * g
def siren(d=2.8, g=1.0):
    s = tt(d); f = 760 + 380 * (0.5 + 0.5 * np.sin(2 * np.pi * 1.6 * s - np.pi / 2))
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
    return lp(x, 3500) * np.minimum(1, s / 0.05) * np.minimum(1, (d - s) / 0.3) * g
def beep(f, d, g=1.0):
    s = tt(d); return np.sin(2 * np.pi * f * s) * np.minimum(1, s / 0.003) * np.minimum(1, (d - s) / 0.01) * g
def buzzer(d=0.35, g=1.0):   # "error" cómico
    s = tt(d); x = np.sign(np.sin(2 * np.pi * 110 * s)) + np.sign(np.sin(2 * np.pi * 116 * s))
    return lp(x * 0.4, 2500) * np.minimum(1, (d - s) / 0.02) * g
def boing(g=1.0):
    s = tt(0.45); f = 180 + 500 * np.exp(-s * 6) * (1 + 0.3 * np.sin(2 * np.pi * 18 * s))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-s * 6) * g
def scratch(g=1.0):
    s = tt(0.35); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3 * s))
    return lp(rng.standard_normal(len(s)) * np.sin(2 * np.pi * np.cumsum(f) / SR), 3000) * np.exp(-s * 5) * g
def scan(d=1.2, g=1.0):
    s = tt(d); f = 400 + 2600 * (s / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 22 * s)) * np.sin(np.pi * s / d) * g
def chime(notes, g=1.0, d=1.6):
    s = tt(d); x = sum(np.sin(2 * np.pi * hz(n) * s) * np.exp(-s * 3) + 0.3 * np.sin(4 * np.pi * hz(n) * s) * np.exp(-s * 6) for n in notes)
    return x / len(notes) * g

def theremin(f0, d, g=1.0, glide=0.0):
    s = tt(d); f = f0 * (1 + glide * np.sin(np.pi * s / d)) * (1 + 0.018 * np.sin(2 * np.pi * 5.5 * s))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return x * np.minimum(1, s / 0.15) * np.minimum(1, (d - s) / 0.3) * g
def ufo_hum(d, g=1.0):
    s = tt(d); x = sum(np.sin(2 * np.pi * f * s + k) for k, f in enumerate((55, 55.7, 110.3, 165.2)))
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * 7 * s)
    return lp(x / 4, 600) * np.minimum(1, s / 0.3) * np.minimum(1, (d - s) / 0.4) * g
def choir(notes, d, g=1.0, att=0.5):      # "aah" sintético: supersierra + formantes
    x = sum(supersaw(hz(n), d, 5, 0.008) for n in notes) / len(notes)
    y = sum(sosfilt(butter(2, [fc * 0.85 / (SR / 2), fc * 1.15 / (SR / 2)], "band", output="sos"), x) * gg
            for fc, gg in ((750, 1.0), (1150, 0.6), (2600, 0.25)))
    return y * np.minimum(1, tt(d) / att) * np.minimum(1, (d - tt(d)) / 0.4) * g * 2.2
def marimba(n, g=1.0):
    s = tt(0.6); f = hz(n)
    return (np.sin(2 * np.pi * f * s) * np.exp(-s * 9) + 0.25 * np.sin(2 * np.pi * f * 4 * s) * np.exp(-s * 30)) * g
def taiko(g=1.0):
    d = tt(0.9); f = 50 + 70 * np.exp(-d * 18)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-d * 4.5) + lp(rng.standard_normal(len(d)), 900) * np.exp(-d * 20) * 0.6
    return np.tanh(x * 1.6) * g
def warble(d=0.5, g=1.0):                  # "bip-bup" de marciano
    s = tt(d); f = 900 + 600 * np.sin(2 * np.pi * 9 * s) + 400 * s / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * s / d) * g

# ------------------------------------------------------------- arreglo (Re menor)
DM, BB, F_, C_ = [50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]

# 1 · 0–3: pantalla negra + alarma, braam al aparecer Melilla, theremin del ovni
put(siren(2.9), 0.0, 0.14, 0.2, sfx=True)
for k in range(4): put(beep(880, 0.12, 0.12), 0.05 + k * 0.11, sfx=True)
put(braam(38, 2.6), 0.45, 0.55); put(boom(), 0.45, 0.8)
put(theremin(hz(74), 2.4, 0.09, 0.25), 0.6, pan=0.3)
put(ufo_hum(2.5, 0.35), 0.5)
put(riser(0.9, 0.25), 2.1)

# 2 · 3–7: invasión — tambores épicos + coro + ovni pasando
put(choir([62, 65, 69], 4.0, 0.22, 0.3), 3.0)
put(pad([38, 50, 57], 4.0, 0.25, cut=700, att=0.1), 3.0)
for k in range(8):
    tk = 3.0 + k * 0.5
    put(taiko(0.9 if k % 2 == 0 else 0.6), tk); put(hat(0.12), tk + 0.25)
put(whoosh(0.9, 0.5), 3.05, pan=-0.6, sfx=True); put(whoosh(0.9, 0.5), 3.6, pan=0.6, sfx=True)
put(ufo_hum(3.0, 0.5), 4.0); put(theremin(hz(69), 1.6, 0.1, -0.3), 4.2)
put(riser(1.0, 0.3), 5.05)
put(boom(1.0, 2.5), 6.05); put(braam(38, 1.6), 6.05, 0.5)
put(lp(rng.standard_normal(int(2.0 * SR)), 800) * np.exp(-tt(2.0) * 1.8), 6.05, 0.35, sfx=True)   # humo / aterrizaje

# 3 · 7–11,5: barbería — suspense cómico
put(pad([50, 53, 56], 4.5, 0.2, cut=900, att=0.6), 7.0)
for k in range(9): put(pluck(62 if k % 2 == 0 else 61, 0.25, 0.08, 1800), 7.0 + k * 0.25, pan=0.2)
for k, n in enumerate([50, 50, 49, 49]): put(bassnote(n - 12, 0.48, 0.3, 300), 7.0 + k * 0.5)
put(warble(0.5, 0.08), 7.4, sfx=True); put(warble(0.4, 0.07), 8.5, sfx=True)
put(braam(36, 1.4), 9.1, 0.6); put(boom(0.9), 9.1)                 # ¡zoom! (dun-dun)
put(braam(35, 1.2), 9.55, 0.35)
put(scan(1.6, 0.08), 9.6, sfx=True)
put(riser(1.0, 0.3), 11.6)

# 4 · 11,5–16: el toque — bip NFC + explosión de luz + coro triunfal
for k in range(2): put(kick(0.6), 11.5 + k * 0.5)
put(beep(1568, 0.09, 0.22), 12.6, sfx=True); put(beep(2093, 0.16, 0.22), 12.7, sfx=True)
put(boom(1.0, 2.0), 12.6); put(chime([86, 90, 93, 98], 0.35, 2.0), 12.6, sfx=True)
put(whoosh(0.6, 0.4), 12.55, sfx=True)
put(choir([62, 66, 69, 74], 3.3, 0.3, 0.1), 12.7)
put(pad([50, 57, 62, 66], 3.3, 0.22, cut=3000, att=0.05), 12.7)
for k in range(6): put(taiko(0.6), 12.9 + k * 0.5)

# 5 · 16–25: documental de naturaleza — marimba y cuerdas suaves (contraste cómico)
put(pad([53, 57, 60, 65], 9.0, 0.14, cut=1400, att=1.0), 16.0)
mel = [65, 69, 72, 69, 67, 65, 64, 65, 69, 72, 74, 72, 69, 67, 65, 67, 69, 65]
for k in range(36):
    put(marimba(mel[k % len(mel)], 0.16), 16.0 + k * 0.25, pan=0.25 * ((k % 2) * 2 - 1))
for k, n in enumerate([41, 41, 46, 46, 48, 48, 41, 41, 46]): put(bassnote(n, 0.98, 0.18, 300), 16.0 + k * 1.0)
put(warble(0.3, 0.05), 19.0, sfx=True)                              # pájaro exótico
put(glitch(0.5, 0.4), 24.9, sfx=True)

# 6 · 25–30: transmisión interceptada
put(ufo_hum(5.0, 0.3), 25.0)
put(pad([50, 53, 57], 5.0, 0.16, cut=800, att=0.4), 25.0)
for k in range(10): put(beep(1400, 0.03, 0.04), 25.1 + k * 0.5, sfx=True)
put(braam(38, 2.2), 27.6, 0.45); put(boom(0.7), 27.6)
put(riser(1.3, 0.35), 28.7)

# 7 · 30–35: épico — Dm Bb F C
for k, ch in enumerate([DM, BB, F_, C_]):
    tk = 30.0 + k * 1.25
    put(choir([n + 12 for n in ch], 1.3, 0.24, 0.1), tk)
    put(pad([n for n in ch] + [ch[0] + 12], 1.3, 0.24, cut=2600, att=0.05), tk)
    put(bassnote(ch[0] - 12, 1.2, 0.45, 400), tk)
for k in range(10):
    tk = 30.0 + k * 0.5
    put(taiko(0.85), tk)
    if k % 2: put(snare(0.45), tk)
    put(hat(0.14), tk + 0.25)
put(theremin(hz(81), 1.0, 0.07, -0.4), 34.0, pan=0.4)
put(riser(0.9, 0.35), 34.1)

# 8 · 35–40: espacio — gran final
put(braam(38, 3.0), 35.0, 0.6); put(boom(), 35.0, 0.9)
put(choir([62, 65, 69, 74], 5.0, 0.26, 0.4), 35.0)
put(pad([38, 50, 57, 62, 65], 5.0, 0.24, cut=2200, att=0.5), 35.0)
put(chime([86, 93, 98], 0.3, 2.5), 35.35, sfx=True)
for k in range(9):
    put(kick(0.7), 35.5 + k * 0.5)
    if k % 2: put(snare(0.35), 35.5 + k * 0.5)
for k in range(9): put(bassnote([38, 38, 46, 48][min(3, k // 2)], 0.48, 0.35, 600), 35.5 + k * 0.5)
put(whoosh(1.2, 0.35), 35.7, pan=-0.5, sfx=True)
put(boom(0.9, 1.6), 39.2); put(chime([74, 81, 86], 0.3, 1.2), 39.2, sfx=True)

# whooshes en cada corte de plano
for (a, b, s) in SHOTS[1:]:
    put(whoosh(0.3, 0.16), a - 0.15, pan=rng.uniform(-0.6, 0.6), sfx=True)

# ------------------------------------------------------------- locución + ducking
VO = np.zeros(N)
meta = json.load(open(os.path.join(HERE, "vo", "voice.json")))
for m in meta:
    with wave.open(m["file"]) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    at(x, m["start"], VO)
env = np.abs(VO); env = lfilter([1 - 0.9995], [1, -0.9995], env)          # seguidor de envolvente
env = np.clip(env / 0.05, 0, 1)
k = int(0.12 * SR); env = np.convolve(env, np.ones(k) / k, mode="same")      # suavizado (ataque/caída)
duck_m = 1 - 0.62 * np.clip(env, 0, 1)        # música  ~ -8,5 dB bajo la voz
duck_s = 1 - 0.35 * np.clip(env, 0, 1)        # efectos ~ -3,7 dB

ML = MUS_L * duck_m + SFX_L * duck_s; MR = MUS_R * duck_m + SFX_R * duck_s
pk = max(np.abs(ML).max(), np.abs(MR).max()); ML /= pk; MR /= pk
ML = np.tanh(ML * 1.5) / np.tanh(1.5) * 0.55; MR = np.tanh(MR * 1.5) / np.tanh(1.5) * 0.55
L = ML + VO * 0.95; R = MR + VO * 0.95
fade = np.clip((TOTAL + 0.5 - t) / 0.7, 0, 1) * np.clip(t / 0.01, 0, 1)
st = np.stack([L, R], 1) * fade[:, None]
st = np.tanh(st * 1.3) / np.tanh(1.3)
st /= np.abs(st).max() / 0.93
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok mix.wav", st.shape[0] / SR, "s")
