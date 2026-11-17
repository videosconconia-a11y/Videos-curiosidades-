# Música de terror + efectos sincronizados con cada frase + voz con ducking -> mix.wav
import numpy as np, wave, sys, os
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import TOTAL, SCENES, shot_timeline, scene_start

SR = 48000
N = int(SR * (TOTAL + 0.5)); t = np.arange(N) / SR
rng = np.random.default_rng(11)
def lp(x, a): return lfilter([a], [1, a - 1], x)
def seg(a, b, f=0.3): return np.clip(np.minimum((t - a) / f, (b - t) / f), 0, 1)
L = np.zeros(N); R = np.zeros(N)
def add(x, g=1.0, pan=0.0):
    global L, R
    L += x * g * (1 - pan); R += x * g * (1 + pan)
S = lambda n: scene_start(n)
def thump(at, f0=70, f1=38, dur=0.35, g=1.0):
    i0 = int(at * SR); n = min(int(dur * SR), N - i0); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt * 18)) / SR
    x = np.zeros(N); x[i0:i0 + n] = np.sin(ph) * np.exp(-tt * 9) * g; return x
def boom(at, g=1.0):
    x = thump(at, 90, 28, 2.5); i0 = int(at * SR); n = min(int(1.5 * SR), N - i0); tt = np.arange(n) / SR
    nz = np.zeros(N); nz[i0:i0 + n] = lp(rng.standard_normal(n), 0.04) * np.exp(-tt * 4) * 3
    return (x + nz) * g
def riser(end, dur=1.8):
    a = end - dur; m = seg(a, end + 0.02, 0.02) * np.clip((t - a) / dur, 0, 1) ** 2
    x = rng.standard_normal(N); return (x - lp(x, 0.05)) * m
def knock(at, g=1.0):
    return thump(at, 140, 80, 0.12, g) + thump(at, 300, 150, 0.04, g * 0.5)
def scrape(a, b, g=1.0):
    x = rng.standard_normal(N); y = lp(x, 0.05) - lp(x, 0.005)
    return y * seg(a, b, 0.2) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t) ** 2) * g * 5

# tensión
key = [(0, .7), (S("house_ne"), .35), (S("basement_msg"), .55), (S("cutaway"), .7), (S("date_card"), .5),
       (S("closet_door"), .95), (S("closet_hatchet") - 0.05, 0.0), (S("closet_hatchet"), 1.0), (S("police"), .6),
       (S("name_card"), .8), (S("bars"), .4), (S("newspaper"), .8), (S("prison"), .5), (S("wall_end"), .8), (TOTAL, .6)]
I = np.interp(t, [k[0] for k in key], [k[1] for k in key])
for f, g in [(32.7, .35), (32.9, .25), (65.4, .18), (92.5, .10), (130.8, .05), (185.0, .03)]:
    add(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t + f)), g * 0.5 * (0.45 + 0.75 * I))
for p in (-0.3, 0.3):
    add(lp(rng.standard_normal(N), 0.003) * 9 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t + p * 5)), 0.04, p)
# viento de invierno en los planos exteriores
for n in ["house_ne", "family_window", "front_door", "window_escape", "police", "candles"]:
    a, b = [(x[0], x[1]) for x in shot_timeline() if x[2] == n][0]
    w = lp(rng.standard_normal(N), 0.01) * 6 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t))
    add(w * seg(a, b, 0.4), 0.07, 0.3)
# golpes y arañazos dentro de la pared
for k, at in enumerate([0.4, 1.1, 1.5, 2.6]): add(knock(at), 0.35, -0.3 + 0.2 * k)
add(scrape(S("wall_noise") + 2.0, S("ghost") - 0.1), 0.05, 0.4)
add(scrape(S("cutaway") + 1.0, S("cutaway") + 3.5), 0.06, -0.3)
for k, at in enumerate([0.3, 0.7, 1.6]): add(knock(S("wall_end") + at, 0.8), 0.3, 0.3 - 0.3 * k)
# fantasma: susurro
wh = rng.standard_normal(N); add((lp(wh, 0.2) - lp(wh, 0.05)) * seg(S("ghost"), S("eye_gap"), 0.3), 0.05)
# pasos (persecución) y cristal/ventana
for k in range(8): add(thump(S("chase") + 0.1 + k * 0.27, 90, 50, 0.15), 0.4, (-1) ** k * 0.2)
x = rng.standard_normal(N); add((x - lp(x, 0.3)) * seg(S("window_escape") + 0.1, S("window_escape") + 0.6, 0.05), 0.1)
# puerta del armario chirriando
cr = np.sin(2 * np.pi * np.cumsum(400 + 180 * np.sin(2 * np.pi * 1.3 * t) + 30 * rng.standard_normal(N)) / SR)
add(cr * seg(S("closet_door") + 0.1, S("closet_hatchet") - 0.15, 0.1), 0.03)
# máquina de escribir
for k in range(15): 
    at = S("name_card") + 0.05 + k * 0.06
    i0 = int(at * SR); x = np.zeros(N); x[i0:i0 + 300] = rng.standard_normal(300) * np.exp(-np.arange(300) / 40); add(x, 0.25)
# sello y reja
add(thump(S("bail") + 0.45 * ([x for x in shot_timeline() if x[2] == "bail"][0][1] - S("bail")), 160, 60, 0.2), 0.6)
add(thump(S("bars") + 0.1, 220, 120, 0.6) + thump(S("prison") + 0.1, 220, 120, 0.6), 0.4)
# sirena
siren = np.sin(2 * np.pi * np.cumsum(700 + 250 * np.sin(2 * np.pi * 0.4 * t)) / SR) * seg(S("police"), S("cutaway_found"), 0.6)
add(lp(siren, 0.2), 0.035, -0.4)
# latidos durante el registro de la casa
k = S("date_card") + 3
while k < S("closet_hatchet") - 0.3:
    add(thump(k, 58, 38, 0.25), 0.55); add(thump(k + 0.17, 52, 36, 0.25, 0.7), 0.45); k += 0.7
for at in [0.05, S("eye_gap"), S("closet_hatchet"), S("cutaway_found"), S("name_card"), S("newspaper"), S("end_card")]:
    add(boom(at), 0.6)
for e in [S("eye_gap"), S("closet_hatchet"), S("cutaway_found")]:
    add(riser(e), 0.12)
for (a, b, s) in shot_timeline()[1:]:
    x = rng.standard_normal(N); m = np.exp(-((t - a) / 0.1) ** 2)
    add((x - lp(x, 0.1)) * m, 0.05, rng.uniform(-0.5, 0.5))

music = np.stack([L, R], 1)
music = np.tanh(music * 1.4) / np.tanh(1.4); music /= np.abs(music).max()
clips = np.load(os.path.join(HERE, "voice_clips.npy"), allow_pickle=True)
vo = np.zeros(N)
for (a, b, _n, _c, _s, v0, vd), x in zip(SCENES, clips):
    i0 = int(v0 * SR); x = np.asarray(x, float)[: N - i0]; vo[i0:i0 + len(x)] += x
env = np.convolve(np.abs(vo), np.ones(2400) / 2400, "same")
env = lfilter([0.0008], [1, -0.9992], (env > 0.02).astype(float))
duck = 1 - 0.62 * np.clip(env * 1.6, 0, 1)
mix = music * 0.55 * duck[:, None] + vo[:, None] * 0.95
mix *= (np.clip((TOTAL + 0.4 - t) / 1.0, 0, 1) * np.clip(t / 0.02, 0, 1))[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix /= np.abs(mix).max() / 0.93
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("audio ok", round(N / SR, 1))
