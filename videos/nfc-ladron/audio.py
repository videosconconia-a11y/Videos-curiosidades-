# Música y efectos cómicos (persecución, ascensor, tape-stop, pop, trombón triste, caja registradora) + voces con ducking -> mix.wav
# Todo sintetizado con numpy (sin samples externos). 120 BPM, La menor.
import numpy as np, wave, sys, os, json
from scipy.signal import lfilter, butter, sosfilt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import TOTAL, SHOTS, HITS

SR = 48000
N = int(SR * (TOTAL + 0.6))
t = np.arange(N) / SR
rng = np.random.default_rng(603)
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

def rhodes(notes, d, g=1.0):
    s = tt(d); x = 0
    for n in notes:
        f = hz(n); x = x + (np.sin(2 * np.pi * f * s) + 0.35 * np.sin(2 * np.pi * 2 * f * s) * np.exp(-s * 3)) * np.exp(-s * 1.2)
    trem = 0.85 + 0.15 * np.sin(2 * np.pi * 5 * s)
    return x / len(notes) * trem * np.minimum(1, s / 0.01) * np.minimum(1, (d - s) / 0.1) * g
def bell(f=1800, d=0.6, g=1.0):
    s = tt(d); return sum(np.sin(2 * np.pi * f * r * s) * np.exp(-s * k) for r, k in ((1, 5), (2.76, 9), (5.4, 14))) / 3 * g
def alarm_bell(d, g=1.0):
    s = tt(d); x = np.sin(2 * np.pi * 2300 * s) * (np.sin(2 * np.pi * 22 * s) > 0) + 0.5 * np.sin(2 * np.pi * 3100 * s) * (np.sin(2 * np.pi * 22 * s) > 0)
    return x * np.minimum(1, (d - s) / 0.1) * g
def step(g=1.0):
    d = tt(0.12); return lp(rng.standard_normal(len(d)), 600) * np.exp(-d * 40) * g + np.sin(2 * np.pi * 80 * d) * np.exp(-d * 30) * g
def tape_stop(d=0.7, g=1.0):
    s = tt(d); f = 220 * (1 - s / d) ** 2 + 20
    return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR)) * (1 - s / d) * g
def tick(g=1.0):
    d = tt(0.03); return hp(rng.standard_normal(len(d)), 3000) * np.exp(-d * 200) * g
def trombone(n, d, g=1.0, bend=0.0):
    s = tt(d); f = hz(n) * (1 + bend * s / d) * (1 + 0.02 * np.sin(2 * np.pi * 6 * s) * (s / d))
    x = 2 * ((np.cumsum(f) / SR) % 1) - 1
    y = np.zeros_like(x)
    for i in range(0, len(x), 960):
        cut = 500 + 1500 * np.sin(np.pi * min(1, s[i] / d)) ** 0.5
        y[i:i + 960] = lp(x[max(0, i - 400):i + 960], cut)[-len(x[i:i + 960]):]
    return y * np.minimum(1, s / 0.03) * np.minimum(1, (d - s) / 0.08) * g
def register(g=1.0):
    return bell(2600, 0.9, 1.0) * g + np.concatenate([np.zeros(int(0.05 * SR)), bell(3300, 0.85, 0.8)])[:int(0.9 * SR)] * g
def paper(d=0.25, g=1.0):
    s = tt(d); return hp(rng.standard_normal(len(s)), 2500) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 30 * s))) * np.sin(np.pi * s / d) * g

# ------------------------------------------------------------- arreglo
# 0–1,95 · GANCHO: campanilla de la puerta, alarma, pasos, persecución
put(bell(1800, 0.5, 0.25), 0.0, sfx=True); put(bell(2200, 0.5, 0.2), 0.08, sfx=True)
put(alarm_bell(1.9, 0.07), 0.0, sfx=True)
for k in range(10): put(step(0.35), 0.05 + k * 0.17, pan=-0.6 + k * 0.13, sfx=True)
for k in range(8):
    tk = k * 0.25; put(kick(0.8), tk); put(hat(0.2), tk + 0.125)
    if k % 2: put(snare(0.5), tk)
for k, n in enumerate([40, 40, 43, 40, 45, 43, 40, 38]): put(bassnote(n, 0.24, 0.4, 900), k * 0.25)
put(braam(40, 0.9), 0.0, 0.35)
for k in range(6): put(paper(0.2, 0.12), 0.3 + k * 0.22, pan=0.4, sfx=True)
# 1,95 · scratch + música de ascensor (calma absurda)
put(scratch(), 1.85, 0.5, sfx=True)
JZ = [[60, 64, 67, 71], [57, 60, 64, 67], [62, 65, 69, 72], [55, 59, 62, 65]]
def elevator(t0, t1, g=0.16):
    k = 0; tk = t0
    while tk < t1 - 0.2:
        ch = JZ[k % 4]; dur = min(1.33, t1 - tk)
        put(rhodes(ch, dur, g), tk); put(bassnote(ch[0] - 24, dur * 0.9, 0.18, 300), tk)
        for j in range(4):
            if tk + j * 0.333 < t1: put(hat(0.05), tk + j * 0.333 + 0.166)
        k += 1; tk += 1.333
elevator(2.05, 5.0)
# 5,0 · «¿¡Ahora!?»: golpe
put(boom(0.7, 1.0), 5.0); put(braam(36, 0.7), 5.0, 0.3)
# 5,75 · PAUSA: tape-stop, reloj, pad etéreo
put(tape_stop(0.6, 0.35), 5.7, sfx=True)
put(pad([60, 67, 72, 76], 4.2, 0.12, cut=2500, att=0.8), 5.8)
for k in range(16): put(tick(0.18), 6.0 + k * 0.25, sfx=True)
put(chime([84, 88, 91], 0.2, 1.4), 7.3, sfx=True); put(chime([84, 88, 91], 0.2, 1.4), 8.3, sfx=True)
put(riser(0.8, 0.25), 9.2)
# 10–18,3 · USOS: pop alegre + «bip» NFC en cada toque
for k in range(33):
    tk = 10.0 + k * 0.25
    if k % 2 == 0: put(kick(0.85), tk)
    if k % 4 == 2: put(clap(0.45), tk)
    put(hat(0.14, open_=(k % 2 == 1)), tk + 0.125, pan=-0.2)
POP = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
for k in range(33):
    ch = POP[(k // 8) % 4]; put(pluck(ch[k % 3] + 12, 0.18, 0.1, 3500), 10.0 + k * 0.25, pan=0.3)
    if k % 2 == 0: put(bassnote(ch[0] - 12, 0.24, 0.3, 800), 10.0 + k * 0.25)
for tk in (10.35, 12.0, 13.65, 15.3, 16.85):
    put(beep(1568, 0.08, 0.2), tk, sfx=True); put(beep(2093, 0.13, 0.2), tk + 0.09, sfx=True); put(whoosh(0.3, 0.2), tk - 0.3, sfx=True)
# 18,3 · «¿Y no vas a hacer nada?»: frenazo
put(scratch(), 18.25, 0.5, sfx=True); put(boom(0.5, 0.8), 18.3)
elevator(20.0, 22.5, 0.15)
# 22,5 · el ladrón lanza los folletos
put(whoosh(0.6, 0.4), 22.5, sfx=True)
for k in range(10): put(paper(0.3, 0.15), 22.55 + k * 0.13, pan=rng.uniform(-0.7, 0.7), sfx=True)
put(boing(0.25), 23.2, sfx=True)
# 24,4 · vuelve el ladrón: trombón triste
for k, (n, dd, bd) in enumerate([(58, 0.32, 0), (57, 0.32, 0), (56, 0.32, 0), (55, 0.9, -0.06)]):
    put(trombone(n - 12, dd, 0.25, bd), 24.45 + k * 0.36)
# 26,3 · a cámara: ritmo seguro + caja registradora en «30 €»
LO = [[57, 60, 64, 67], [53, 57, 60, 64], [60, 64, 67, 71], [55, 59, 62, 67]]
for k in range(31):
    tk = 26.3 + k * 0.25
    if k % 4 == 0: put(kick(0.75), tk)
    if k % 4 == 2: put(snare(0.4), tk)
    put(hat(0.1), tk + 0.125)
for k in range(4):
    ch = LO[k % 4]; put(rhodes(ch, 1.95, 0.14), 26.3 + k * 1.95); put(bassnote(ch[0] - 24, 1.9, 0.3, 350), 26.3 + k * 1.95)
put(register(0.35), 27.55, sfx=True)
put(riser(0.8, 0.3), 33.2)
# 34–40 · cierre: sintonía
put(boom(0.8, 1.5), 34.0); put(chime([72, 76, 79, 84], 0.3, 1.6), 34.0, sfx=True)
for k in range(24):
    tk = 34.0 + k * 0.25
    if k % 2 == 0: put(kick(0.7), tk)
    if k % 4 == 2: put(clap(0.35), tk)
    put(hat(0.12), tk + 0.125)
for k in range(24):
    ch = POP[(k // 8) % 4]; put(pluck(ch[k % 3] + 12, 0.18, 0.09, 3500), 34.0 + k * 0.25, pan=0.3)
    if k % 2 == 0: put(bassnote(ch[0] - 12, 0.24, 0.28, 800), 34.0 + k * 0.25)
put(chime([72, 79, 84], 0.3, 1.0), 39.2, sfx=True); put(boom(0.6, 1.0), 39.2)

for (a, b, s) in SHOTS[1:]:
    put(whoosh(0.25, 0.12), a - 0.12, pan=rng.uniform(-0.6, 0.6), sfx=True)

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
