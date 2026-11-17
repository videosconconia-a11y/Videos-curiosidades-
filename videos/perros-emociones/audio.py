# Música (sintetizada), efectos y voz con "ducking": la música baja mientras habla la voz.
import numpy as np, wave, sys, os
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import TOTAL, shot_timeline, PHRASE_TIMES

SR = 48000
N = int(SR * (TOTAL + 0.3))
t = np.arange(N) / SR
rng = np.random.default_rng(7)
SHOTS = shot_timeline()
def shot_start(name): return next(s[0] for s in SHOTS if s[2] == name)
def shot_end(name): return next(s[1] for s in SHOTS if s[2] == name)

def lp(x, a): return lfilter([a], [1, a - 1], x)
def seg(a, b, fade=0.5): return np.clip(np.minimum((t - a) / fade, (b - t) / fade), 0, 1)

L = np.zeros(N); R = np.zeros(N)
def add(x, gain=1.0, pan=0.0):
    global L, R
    L += x * gain * (1 - pan); R += x * gain * (1 + pan)

# ---------------- música: progresión emotiva Am – F – C – G (y final en F – G – C)
BPM = 84; beat = 60 / BPM; bar = 4 * beat
def mid(n): return 440 * 2 ** ((n - 69) / 12)
PROG = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
END_PROG = [[53, 57, 60], [55, 59, 62], [48, 52, 55]]
tension = seg(shot_start("fear_sweat"), shot_end("dog_owner"), 0.8)
warm_end = np.clip((t - shot_start("gaze")) / 2.0, 0, 1)

def pluck(at, f, dur=1.4, g=1.0):
    i0 = int(at * SR); n = min(int(dur * SR), N - i0)
    if n <= 0: return
    tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.12 * np.sin(6 * np.pi * f * tt))
    x *= np.exp(-tt * 3.2) * np.minimum(1, tt / 0.004)
    pan = rng.uniform(-0.4, 0.4)
    L[i0:i0 + n] += x * g * (1 - pan); R[i0:i0 + n] += x * g * (1 + pan)

pad = np.zeros(N)
nb = int(TOTAL / bar) + 2
for k in range(nb):
    t0 = k * bar
    end_zone = t0 > shot_start("sunset_pair") - bar
    ch = END_PROG[min(2, int((t0 - (shot_start("sunset_pair") - bar)) / bar))] if end_zone else PROG[k % 4]
    if t0 > TOTAL: break
    m = seg(t0 - 0.2, t0 + bar + 0.3, 0.4)
    for n in ch:
        f = mid(n - 12)
        pad += (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t) + 0.25 * np.sin(4 * np.pi * f * t)) * m
    # arpegio en corcheas (empieza tras el gancho)
    if t0 >= 2 * beat:
        notes = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12]
        for j, n in enumerate(notes):
            at = t0 + j * beat / 2
            if at < TOTAL - 1.0:
                pluck(at, mid(n), g=0.055 * (1.0 if j % 2 == 0 else 0.7))
    # bajo
    i0 = int(t0 * SR); nn = min(int(bar * SR), N - i0)
    if nn > 0:
        tt = np.arange(nn) / SR
        bass = np.sin(2 * np.pi * mid(ch[0] - 24) * tt) * np.exp(-tt * 0.8) * np.minimum(1, tt / 0.01)
        L[i0:i0 + nn] += bass * 0.16; R[i0:i0 + nn] += bass * 0.16
pad = lp(pad, 0.08)
add(pad, 0.05 * (1 - 0.4 * tension) + 0.03 * warm_end)

# pulso suave (bombo) desde el plano de los receptores; más intenso en la parte de estrés
def thump(at, f0=80, f1=42, dur=0.35, g=1.0):
    i0 = int(at * SR); n = min(int(dur * SR), N - i0)
    x = np.zeros(N)
    if n <= 0: return x
    tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt * 18)) / SR
    x[i0:i0 + n] = np.sin(ph) * np.exp(-tt * 9) * g; return x
kick = np.zeros(N)
k = shot_start("stat_300")
while k < shot_start("sunset_pair"):
    kick += thump(k, g=0.6)
    k += beat
add(kick, 0.35)

# drone de tensión en la parte del miedo
for f in (55, 55.6, 82.4):
    add(np.sin(2 * np.pi * f * t) * tension, 0.09)

# ---------------- efectos
def boom(at, g=1.0):
    x = thump(at, 95, 30, 2.2, 1.0)
    i0 = int(at * SR); n = min(int(1.2 * SR), N - i0); tt = np.arange(n) / SR
    nz = np.zeros(N); nz[i0:i0 + n] = lp(rng.standard_normal(n), 0.05) * np.exp(-tt * 5) * 3
    return (x + nz) * g
for nm in ("stat_300", "stat_94", "fear_sweat", "gaze", "sunset_pair"):
    add(boom(shot_start(nm)), 0.45)
add(boom(0.05), 0.55)

def riser(end, dur=1.4):
    a = end - dur; m = seg(a, end + 0.05, 0.05) * np.clip((t - a) / dur, 0, 1) ** 2
    x = rng.standard_normal(N); return (x - lp(x, 0.05)) * m
for nm in ("stat_300", "stat_94", "sunset_pair"):
    add(riser(shot_start(nm)), 0.06)

def sniff(at, g=1.0):   # olfateo: ráfagas cortas de ruido filtrado
    x = np.zeros(N)
    for j in range(3):
        i0 = int((at + j * 0.17) * SR); n = int(0.11 * SR)
        if i0 + n >= N: break
        tt = np.arange(n) / SR
        nz = rng.standard_normal(n); nz = nz - lp(nz, 0.15)
        x[i0:i0 + n] += nz * np.sin(np.pi * tt / 0.11) ** 2
    return lp(x, 0.35) * g
for at in (0.9, 3.0, 4.0, shot_start("dog_sniff") + 0.5, shot_start("dog_sniff") + 1.7, shot_start("airflow") + 0.3,
           shot_start("dog_lineup") + 0.8):
    add(sniff(at), 0.5)

# latidos que se aceleran (mismo ritmo que el electro del plano)
a, b = shot_start("heart_fast"), shot_end("heart_fast")
bt, iv = a - 3, 0.75
def ease(p): p = min(max(p, 0.0), 1.0); return p * p * (3 - 2 * p)
while bt < b:
    if bt >= a - 0.1:
        add(thump(bt, 60, 40, 0.25, 1.0), 0.55); add(thump(bt + 0.15, 55, 38, 0.25, 0.7), 0.45)
    iv = 0.75 - 0.37 * ease((bt - a) / (b - a)); bt += iv

# latido tranquilo y compartido en la oxitocina
a, b = shot_start("oxytocin"), shot_end("oxytocin")
bt = a + 0.1
while bt < b:
    add(thump(bt, 55, 38, 0.25, 0.8), 0.35); add(thump(bt + 0.15, 50, 36, 0.25, 0.5), 0.3); bt += 1 / 1.3

# campanilla en los aciertos
def chime(at, f=1318.5, g=1.0):
    i0 = int(at * SR); n = min(int(1.5 * SR), N - i0); tt = np.arange(n) / SR
    x = np.zeros(N); x[i0:i0 + n] = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 3)
    return x * g
add(chime(shot_start("stat_94") + 1.0), 0.06)
add(chime(shot_start("faces") + 1.6, 1046.5), 0.05)

# whoosh en cada corte
for (sa, sb, s) in SHOTS[1:]:
    x = rng.standard_normal(N); m = np.exp(-((t - sa) / 0.12) ** 2)
    add((x - lp(x, 0.1)) * m, 0.05, rng.uniform(-0.5, 0.5))

# ---------------- mezcla con la voz y ducking
music = np.stack([L, R], 1)
music /= np.abs(music).max() / 0.8
voice = np.zeros(N)
for i, (pa, pb) in enumerate(PHRASE_TIMES):
    v = np.load(os.path.join(HERE, "voice", f"p_{i:02}.npy")).astype(float)
    i0 = int(pa * SR); n = min(len(v), N - i0)
    voice[i0:i0 + n] += v[:n]
voice = voice / (np.abs(voice).max() + 1e-9) * 0.92
# suaviza la voz: leve realce de presencia y compresión suave
voice = np.tanh(voice * 1.6) / np.tanh(1.6)
active = np.zeros(N)
for (pa, pb) in PHRASE_TIMES:
    active[int(pa * SR):int(pb * SR)] = 1
# envolvente: ataque 120 ms, relajación 400 ms
k_att = 1 - np.exp(-1 / (0.12 * SR)); k_rel = 1 - np.exp(-1 / (0.40 * SR))
env = np.empty(N); e = 0.0
for i in range(0, N, 48):          # cálculo por bloques de 1 ms
    target = active[i]
    e += (target - e) * (1 - (1 - (k_att if target > e else k_rel)) ** 48)
    env[i:i + 48] = e
duck = 1 - 0.72 * env              # la música baja a ~28 % mientras habla la voz
mix = music * duck[:, None] * 0.55 + voice[:, None] * 0.85
fade = np.clip((TOTAL + 0.2 - t) / 1.2, 0, 1) * np.clip(t / 0.02, 0, 1)
mix *= fade[:, None]
# (sin saturación final: el volumen se normaliza a -14 LUFS en build.sh)
mix /= np.abs(mix).max() / 0.95
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("audio ok", round(N / SR, 2), "s")
