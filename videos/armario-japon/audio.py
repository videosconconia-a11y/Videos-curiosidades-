# Música de terror + efectos + voz con ducking -> mix.wav
import numpy as np, wave, sys, os
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import TOTAL, SCENES, shot_timeline, scene_start

SR = 48000
N = int(SR * (TOTAL + 0.5)); t = np.arange(N) / SR
rng = np.random.default_rng(7)
def lp(x, a): return lfilter([a], [1, a - 1], x)
def seg(a, b, f=0.5): return np.clip(np.minimum((t - a) / f, (b - t) / f), 0, 1)
L = np.zeros(N); R = np.zeros(N)
def add(x, g=1.0, pan=0.0):
    global L, R
    L += x * g * (1 - pan); R += x * g * (1 + pan)

S = {n: scene_start(n) for n in ["cctv_hook", "house_ext", "fridge", "camera", "phone_alert", "police", "closet_closed",
                                 "stat_58", "door", "case_file", "end_card"]}
closet_reveal = S["closet_closed"] + 2.45
# curva de tensión
key = [(0, .7), (S["house_ext"], .35), (S["fridge"], .45), (S["phone_alert"] - .3, .55), (S["phone_alert"], .85),
       (S["police"], .7), (closet_reveal - 0.6, 1.0), (closet_reveal - 0.05, 0.0), (closet_reveal, .9), (S["stat_58"] + 3, .6),
       (S["door"], .4), (S["case_file"], .8), (S["end_card"] - 3, .5), (TOTAL, .6)]
I = np.interp(t, [k[0] for k in key], [k[1] for k in key])

# Dron grave disonante (re + la bemol = tritono)
for f, g in [(36.7, .35), (36.9, .25), (73.4, .18), (103.8, .10), (146.8, .05), (207.6, .03)]:
    add(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t + f)), g * 0.5 * (0.5 + 0.7 * I))
# aire / ruido de habitación
for p in (-0.3, 0.3):
    add(lp(rng.standard_normal(N), 0.003) * 9 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t + p * 5)), 0.04, p)
# notas de "caja de música" desafinadas, esporádicas
for k in range(16):
    at = 1.0 + k * 3.9 + rng.uniform(-0.3, 0.3)
    if at > TOTAL - 1: break
    f = rng.choice([587.3, 622.3, 830.6, 880.0, 554.4]); i0 = int(at * SR); n = int(2.5 * SR)
    n = min(n, N - i0); tt = np.arange(n) / SR
    x = np.zeros(N); x[i0:i0 + n] = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.01 * tt)) * np.exp(-tt * 2.2)
    add(x, 0.035, rng.uniform(-0.6, 0.6))

def thump(at, f0=70, f1=38, dur=0.35, g=1.0):
    i0 = int(at * SR); n = min(int(dur * SR), N - i0); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt * 18)) / SR
    x = np.zeros(N); x[i0:i0 + n] = np.sin(ph) * np.exp(-tt * 9) * g; return x
def boom(at, g=1.0):
    x = thump(at, 90, 28, 2.5, 1.0); i0 = int(at * SR); n = min(int(1.5 * SR), N - i0); tt = np.arange(n) / SR
    nz = np.zeros(N); nz[i0:i0 + n] = lp(rng.standard_normal(n), 0.04) * np.exp(-tt * 4) * 3
    return (x + nz) * g
def riser(end, dur=2.0):
    a = end - dur; m = seg(a, end + 0.02, 0.02) * np.clip((t - a) / dur, 0, 1) ** 2
    x = rng.standard_normal(N); return (x - lp(x, 0.05)) * m

# latido que acelera durante la búsqueda policial
hb, k = [], S["police"]
while k < closet_reveal - 0.3:
    hb.append(k); k += max(0.42, 0.95 - (k - S["police"]) * 0.06)
for at in hb:
    add(thump(at, 58, 38, 0.25), 0.55); add(thump(at + 0.17, 52, 36, 0.25, 0.7), 0.45)

for at in [0.05, S["phone_alert"] + 0.1, closet_reveal, S["stat_58"], S["case_file"] + 0.75, S["end_card"]]:
    add(boom(at), 0.6)
for e in [S["phone_alert"] + 0.1, closet_reveal]:
    add(riser(e), 0.12)

# zumbido de nevera
hum = (np.sin(2 * np.pi * 100 * t) + 0.4 * np.sin(2 * np.pi * 200 * t)) * seg(S["fridge"], S["camera"], 0.4)
add(hum, 0.025)
# notificación del móvil
for k2, f in enumerate([1318.5, 1760.0]):
    at = S["phone_alert"] + 0.25 + k2 * 0.12
    add(np.sin(2 * np.pi * f * t) * seg(at, at + 0.25, 0.005) * np.exp(-np.clip(t - at, 0, None) * 12), 0.12)
# clic de cámara al instalarla
for at in [S["camera"] + 0.6, S["camera"] + 0.75]:
    i0 = int(at * SR); x = np.zeros(N); x[i0:i0 + 400] = rng.standard_normal(400) * np.exp(-np.arange(400) / 60); add(x, 0.25)
# puerta corredera del armario
a0 = S["closet_closed"] + 2.45; x = rng.standard_normal(N)
add((lp(x, 0.08) - lp(x, 0.01)) * seg(a0, a0 + 1.6, 0.2) * 6, 0.25, 0.2)
# sirena lejana
siren = np.sin(2 * np.pi * np.cumsum(700 + 250 * np.sin(2 * np.pi * 0.4 * t)) / SR) * seg(S["police"], S["police"] + 3, 0.8)
add(lp(siren, 0.2), 0.03, -0.4)
# golpe de sello
add(thump(S["case_file"] + 0.75, 160, 60, 0.2), 0.6)
# whoosh en cada corte
for (a, b, s) in shot_timeline()[1:]:
    x = rng.standard_normal(N); m = np.exp(-((t - a) / 0.12) ** 2)
    add((x - lp(x, 0.1)) * m, 0.05, rng.uniform(-0.5, 0.5))

music = np.stack([L, R], 1)
music = np.tanh(music * 1.4) / np.tanh(1.4); music /= np.abs(music).max()

# ---- voz
clips = np.load(os.path.join(HERE, "voice_clips.npy"), allow_pickle=True)
vo = np.zeros(N)
for (a, b, _n, _c, _s, v0, vd), x in zip(SCENES, clips):
    i0 = int(v0 * SR); x = np.asarray(x, float)[: N - i0]; vo[i0:i0 + len(x)] += x
# ducking: la música baja cuando habla la voz
env = np.convolve(np.abs(vo), np.ones(2400) / 2400, "same")
env = lfilter([0.0008], [1, -0.9992], (env > 0.02).astype(float))
env = np.clip(env * 1.6, 0, 1)
duck = 1 - 0.62 * env
mix = music * 0.55 * duck[:, None] + vo[:, None] * 0.95
fade = np.clip((TOTAL + 0.4 - t) / 1.0, 0, 1) * np.clip(t / 0.02, 0, 1)
mix *= fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix /= np.abs(mix).max() / 0.93
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("audio ok", round(N / SR, 1))
