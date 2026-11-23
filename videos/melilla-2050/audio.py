# Música electrónica cinematográfica + efectos + locución con ducking -> mix.wav
# Todo sintetizado con numpy (sin samples externos). 120 BPM, La menor.
import numpy as np, wave, sys, os, json
from scipy.signal import lfilter, butter, sosfilt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import TOTAL, SHOTS, HITS

SR = 48000
N = int(SR * (TOTAL + 0.6))
t = np.arange(N) / SR
rng = np.random.default_rng(2050)
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

# ------------------------------------------------------------- arreglo
AM, F, C, G = [57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]

# 1 · GANCHO 0–3: braam + alarma + sub
put(braam(33, 2.8), 0.0, 0.55); put(boom(), 0.0, 0.8)
put(siren(2.9), 0.05, 0.12, 0.25, sfx=True)
put(pad([45, 52, 57, 60], 3.0, cut=900), 0.0, 0.25)
for k in range(6): put(kick(0.7), 0.0 + k * 0.5)
put(braam(33, 1.6), 1.45, 0.4); put(glitch(0.25), 1.35, 0.35, sfx=True)
put(riser(1.0), 2.0, 0.25)

# 2 · CAOS 3–6: ritmo nervioso + gags sonoros
for k in range(12):
    tk = 3.0 + k * 0.25
    put(hat(0.25), tk, pan=0.3)
    if k % 2 == 0: put(kick(0.8), tk)
    if k % 4 == 2: put(clap(0.5), tk)
for k, n in enumerate([45, 45, 48, 45, 50, 48]):
    put(bassnote(n, 0.45, 0.45), 3.0 + k * 0.5)
for x, tk, g in [(boing(), 3.25, 0.25), (buzzer(), 4.25, 0.18), (boing(), 4.85, 0.22), (buzzer(0.55), 5.45, 0.22)]:
    put(x, tk, g, sfx=True)
put(scratch(), 5.75, 0.35, sfx=True)

# 3 · APARICIÓN 6–10: silencio mágico, pad etéreo, gran golpe al revelar
put(pad([69, 72, 76, 81], 4.0, 0.22, cut=3500, att=1.2), 6.0)
put(pad([45, 57], 4.0, 0.2, cut=500, att=0.8), 6.0)
put(chime([81, 84, 88], 0.25, 2.5), 6.3, sfx=True)
put(riser(1.9, 0.35), 6.25)
put(braam(33, 2.0), 8.15, 0.55); put(boom(), 8.15, 0.7); put(chime([76, 81, 88, 93], 0.3), 8.15, sfx=True)

# 4 · PODER 10–14: pulso + escáner + "bip" de NFC
for k in range(8):
    put(kick(0.75), 10.0 + k * 0.5); put(hat(0.18), 10.25 + k * 0.5)
for k, n in enumerate([45, 45, 45, 45, 41, 41, 43, 43]):
    put(bassnote(n, 0.48, 0.4, 600), 10.0 + k * 0.5)
put(scan(1.1, 0.12), 10.1, sfx=True)
put(beep(1568, 0.09, 0.22), 11.2, sfx=True); put(beep(2093, 0.16, 0.22), 11.3, sfx=True)
put(chime([84, 88, 91], 0.25, 1.4), 11.3, sfx=True)
put(riser(1.6, 0.35), 12.4)

# 5 · MONTAGE 14–19: drop
for k in range(20):
    tk = 14.0 + k * 0.25
    if k % 2 == 0: put(kick(1.0), tk)
    if k % 4 == 2: put(snare(0.6), tk); put(clap(0.35), tk)
    put(hat(0.22, open_=(k % 2 == 1)), tk + (0.125 if k % 2 else 0), pan=-0.2)
riff = [45, 57, 45, 55, 45, 57, 48, 52]
for k in range(40):
    tk = 14.0 + k * 0.125
    put(bassnote(riff[k % 8] - 12 if k % 2 == 0 else riff[k % 8] - 12, 0.12, 0.33, 700 + 900 * (k / 40)), tk)
arp = [69, 72, 76, 81, 76, 72]
for k in range(40):
    put(pluck(arp[k % 6] + (0 if k < 20 else 2), 0.2, 0.16, 3200), 14.0 + k * 0.125, pan=0.3 * ((k % 2) * 2 - 1))
put(pad([57, 64, 69, 72], 5.0, 0.16, cut=2500, att=0.05), 14.0)
put(riser(0.8, 0.3), 18.2)

# 6 · GIRO 19–25: sintonía de informativo + cama de noticias
for k, ch in enumerate([[64, 69, 73], [66, 69, 74], [64, 68, 71], [64, 69, 73]]):
    put(pad(ch, 0.22 if k < 3 else 0.6, 0.3, cut=5000, att=0.005), 19.0 + k * 0.18)
put(boom(0.6, 1.5), 19.0)
for k in range(21):                     # tic-tac de redacción
    put(beep(1200 if k % 4 == 0 else 900, 0.025, 0.05), 19.6 + k * 0.25, sfx=True)
for k in range(10):
    put(kick(0.35), 19.6 + k * 0.5)
put(pad([45, 52, 57], 4.9, 0.12, cut=700, att=0.5), 19.5)
put(glitch(0.6, 0.5), 24.4, sfx=True); put(boom(0.7, 1.2), 24.4)

# 7 · ORGULLO 25–32: épico, Am–F–C–G
for k, ch in enumerate([AM, F, C, G]):
    tk = 25.0 + k * 1.75
    put(pad([n - 12 for n in ch] + ch, 1.8, 0.28, cut=2600, att=0.15), tk)
    put(bassnote(ch[0] - 24, 1.7, 0.45, 400), tk)
for k in range(14):
    tk = 25.0 + k * 0.5
    put(kick(0.75), tk)
    if k % 2 == 1: put(snare(0.5), tk)
    put(hat(0.15), tk + 0.25)
for k in range(28):
    ch = [AM, F, C, G][k // 7]; put(pluck(ch[k % 3] + 12, 0.25, 0.1, 4000), 25.0 + k * 0.25, pan=0.4)
put(riser(1.5, 0.4), 30.5)

# 8 · FINAL 32–40
put(braam(33, 3.0), 32.0, 0.6); put(boom(), 32.0, 0.9)
put(pad([45, 57, 64, 69, 72], 8.0, 0.28, cut=2200, att=0.6), 32.0)
put(whoosh(1.2, 0.5), 32.4, sfx=True); put(whoosh(1.0, 0.45), 33.6, sfx=True)
for k in range(6): put(kick(0.6), 32.0 + k * 0.5)
put(riser(1.2, 0.35), 34.1)
put(braam(33, 3.5), 35.3, 0.55); put(boom(), 35.3, 0.8); put(chime([81, 88, 93], 0.3, 2.5), 35.3, sfx=True)
for k in range(8):
    put(kick(0.8), 35.3 + k * 0.5)
    if k % 2: put(snare(0.4), 35.3 + k * 0.5)
for k in range(8): put(bassnote([45, 45, 53, 55][k // 2], 0.48, 0.4, 700), 35.3 + k * 0.5)
put(boom(1.0, 1.8), 39.3); put(chime([69, 76, 81], 0.35, 1.2), 39.3, sfx=True)

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
