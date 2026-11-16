# Música de tensión + efectos de sonido sintetizados, sincronizados con build/timing.json,
# y mezcla final con la voz (la música baja automáticamente mientras habla la voz: "ducking").
# Salidas: build/music_sfx.wav (sin voz) y build/mix.wav (mezcla final, -14 LUFS).
import numpy as np, wave, sys, os, subprocess
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, load_timing, scene_bounds, shot_timeline, sfx_events, heart_beats

TM = load_timing(); TOTAL = TM["total"]
BUILD = os.path.join(HERE, "build")
SR = 48000
N = int(SR * (TOTAL + 0.3))
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def lp(x, a): return lfilter([a], [1, a - 1], x)
def seg(a, b, fade=0.5): return np.clip(np.minimum((t - a) / fade, (b - t) / fade), 0, 1)


L = np.zeros(N); R = np.zeros(N)
def add(x, gain=1.0, pan=0.0):
    global L, R
    L += x * gain * (1 - pan); R += x * gain * (1 + pan)


# ---------------------------------------------------------------- curva de intensidad por escena
B = scene_bounds(TM)
PROFILE = {  # (intensidad al inicio, al final) de cada escena
    "gancho": (0.75, 0.6), "presentacion": (0.45, 0.55), "invierno": (0.5, 0.75), "congelacion": (0.8, 1.0),
    "muerta": (0.3, 0.02), "truco": (0.5, 0.85), "alaska": (0.7, 1.0), "deshielo": (0.45, 0.65),
    "ciencia": (0.6, 0.75), "final": (0.85, 1.0),
}
kx, ky = [], []
for (a, b), sc in zip(B, SCENES):
    i0, i1 = PROFILE[sc["name"]]
    kx += [a + 0.01, b - 0.01]; ky += [i0, i1]
kx += [TOTAL - 0.8, TOTAL]; ky += [0.9, 0.0]
I = np.interp(t, kx, ky)
names = [s["name"] for s in SCENES]
DEAD = B[names.index("muerta")]
THAW = B[names.index("deshielo")]

# Dron frío (La menor): senos desafinados + viento
for f, g in [(55, 0.30), (55.4, 0.22), (82.4, 0.16), (110, 0.10), (164.8, 0.05)]:
    add(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t + f)), g * 0.55 * (0.5 + 0.6 * I))
for pan in (0.25, -0.25):
    wind = lp(rng.standard_normal(N), 0.004) * 8 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t + pan * 9))
    add(wind, 0.05 * (0.6 + 0.6 * I), pan)

# Pad de hielo (brillo agudo con trémolo)
for f, p in [(880, -0.5), (1318.5, 0.5), (1760, -0.2), (1046.5, 0.3)]:
    add(np.sin(2 * np.pi * f * t) * (0.5 + 0.5 * np.sin(2 * np.pi * (0.3 + f / 5000) * t)), 0.011 * (0.3 + I), p)

# Arpegio ostinato (tensión tipo documental) — se oye cuando la intensidad es alta
arp = [220.0, 261.6, 329.6, 261.6, 220.0, 196.0, 220.0, 329.6]
step = 60 / 104 / 2; k = 0
while k * step < TOTAL:
    at = k * step; ii = float(np.interp(at, t, I))
    if ii > 0.55 and not (DEAD[0] < at < DEAD[1]):
        f = arp[k % len(arp)] * (2 if ii > 0.85 else 1)
        i0 = int(at * SR); n = min(int(0.32 * SR), N - i0); tt = np.arange(n) / SR
        x = np.zeros(N); x[i0:i0 + n] = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 9)
        add(x, 0.035 * ii, 0.35 if k % 2 else -0.35)
    k += 1

# Acorde cálido para el deshielo y el final
warm = seg(THAW[0] - 0.2, B[-1][0] + 1.0, 1.2) * (1 - seg(DEAD[0], DEAD[1], 0.1))
for f in [130.8, 164.8, 196.0, 261.6, 329.6]:
    add(np.sin(2 * np.pi * f * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.5 * t + f)), 0.045 * warm)


def thump(at, f0=70, f1=38, dur=0.35, g=1.0):
    i0 = int(at * SR); x = np.zeros(N)
    if i0 >= N or i0 < 0: return x
    n = min(int(dur * SR), N - i0); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt * 18)) / SR
    x[i0:i0 + n] = np.sin(ph) * np.exp(-tt * 9) * g; return x


# Pulso de percusión: densidad según intensidad
beat = 60 / 104; k = 0.0
while k < TOTAL - 1:
    ii = float(np.interp(k, t, I))
    if ii > 0.45 and not (DEAD[0] - 0.2 < k < DEAD[1]):
        add(thump(k, g=ii), 0.32)
        if ii > 0.8: add(thump(k + beat / 2, g=ii * 0.6), 0.22)
    k += beat


def boom(at, g=1.0):
    x = thump(at, 95, 30, 2.2, 1.0)
    i0 = int(at * SR); n = min(int(1.2 * SR), N - i0); tt = np.arange(n) / SR
    nz = np.zeros(N); nz[i0:i0 + n] = lp(rng.standard_normal(n), 0.05) * np.exp(-tt * 5) * 3
    return (x + nz) * g


def riser(end, dur=1.5):
    a = end - dur; m = seg(a, end + 0.03, 0.03) * np.clip((t - a) / dur, 0, 1) ** 2
    x = rng.standard_normal(N); return (x - lp(x, 0.05)) * m


def crack(at, g=1.0):
    x = np.zeros(N)
    for j in range(40):
        i = int((at + rng.exponential(0.06) * j * 0.3) * SR); n = int(0.01 * SR)
        if i + n < N: x[i:i + n] += rng.standard_normal(n) * np.exp(-np.arange(n) / 40) * rng.uniform(0.3, 1)
    return (x - lp(x, 0.2)) * g


def beep(at, dur=0.12): return np.sin(2 * np.pi * 1000 * t) * seg(at, at + dur, 0.005)


def shimmer(at):
    x = np.zeros(N)
    for j, f in enumerate([1568, 2093, 2637, 3136, 4186]):
        x += np.sin(2 * np.pi * f * t) * seg(at + j * 0.07, at + 1.6, 0.02) * np.exp(-np.clip(t - at, 0, None) * 1.5)
    return x


HITS = []   # instantes de impacto (también los usa render.py para el destello)
stop, flat, back = heart_beats(TM)
for (a, b, kind) in sfx_events(TM):
    if kind == "boom": add(boom(a), 0.55); HITS.append(a)
    elif kind == "hit": add(boom(a), 0.3)
    elif kind == "riser_end": add(riser(a), 0.10)
    elif kind == "crack":
        for j, p in enumerate((-0.3, 0.3)): add(crack(a + 0.3 + j * 0.9), 0.32, p)
    elif kind == "shimmer": add(shimmer(a), 0.03)
    elif kind == "drips":
        for j in range(12):
            at = a + j * 0.5 + rng.uniform(0, 0.2); f = rng.uniform(900, 1500)
            i0 = int(at * SR); n = int(0.15 * SR); tt = np.arange(n) / SR
            x = np.zeros(N); x[i0:i0 + n] = np.sin(2 * np.pi * (f + f * 2 * tt) * tt) * np.exp(-tt * 30)
            add(x, 0.07, rng.uniform(-0.6, 0.6))
for at in stop + back:
    add(thump(at, 60, 40, 0.25, 1.0), 0.7); add(thump(at + 0.16, 55, 38, 0.25, 0.7), 0.55)
for at in stop + back[:3]:
    add(beep(at), 0.045)
add(np.sin(2 * np.pi * 1000 * t) * seg(flat, flat + 2.2, 0.02) * np.clip((flat + 2.2 - t) / 2.2, 0, 1), 0.045)

# Whoosh en cada corte de plano
for (a, b, s) in shot_timeline(TM)[1:]:
    x = rng.standard_normal(N); m = np.exp(-((t - a) / 0.12) ** 2)
    add((x - lp(x, 0.1)) * m, 0.05, rng.uniform(-0.5, 0.5))

# Master de música+efectos
fade = np.clip((TOTAL - t) / 1.2, 0, 1) * np.clip(t / 0.02, 0, 1)
st = np.stack([L, R], 1) * fade[:, None]
st = np.tanh(st * 1.6) / np.tanh(1.6)
st /= np.abs(st).max() / 0.89


def wav_write(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


wav_write(os.path.join(BUILD, "music_sfx.wav"), st)

# ---------------------------------------------------------------- ducking + mezcla con la voz
with wave.open(os.path.join(BUILD, "voice.wav")) as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
v = np.pad(v, (0, max(0, N - len(v))))[:N]
# envolvente de la voz: ataque rápido (40 ms) y suelta lenta (350 ms)
e = np.abs(v); e = lp(e, 1 - np.exp(-1 / (0.01 * SR)))
act = np.clip(e / 0.03, 0, 1)
env = np.zeros(N); g = 0.0
aa, rr = 1 - np.exp(-1 / (0.04 * SR)), 1 - np.exp(-1 / (0.35 * SR))
# (bucle por bloques de 1 ms para que sea rápido)
blk = SR // 1000
for i in range(0, N, blk):
    target = act[i:i + blk].max()
    c = aa if target > g else rr
    g += (target - g) * (1 - (1 - c) ** blk)
    env[i:i + blk] = g
duck = 10 ** (-8.0 * env / 20)          # hasta -8 dB mientras habla la voz
music = st * duck[:, None]
voice = np.stack([v, v], 1) * 1.0
mix = music * 0.75 + voice * 0.95
wav_write(os.path.join(BUILD, "mix_pre.wav"), mix / max(1e-9, np.abs(mix).max()) * 0.9)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(BUILD, "mix_pre.wav"),
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), os.path.join(BUILD, "mix.wav")], check=True)
with open(os.path.join(BUILD, "hits.txt"), "w") as f:
    f.write(" ".join(f"{h:.3f}" for h in sorted(HITS)))
print("audio ok", TOTAL, "s; booms en", [round(h, 2) for h in sorted(HITS)])
