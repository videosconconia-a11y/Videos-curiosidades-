# Música de suspense + efectos sincronizados con cada plano + voz con ducking -> mix.wav
import numpy as np, wave, sys, os, math
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import TOTAL, SCENES, shot_timeline, scene_start

SR = 48000
N = int(SR * (TOTAL + 0.5)); t = np.arange(N) / SR
rng = np.random.default_rng(21)
def lp(x, a): return lfilter([a], [1, a - 1], x)
def seg(a, b, f=0.3): return np.clip(np.minimum((t - a) / f, (b - t) / f), 0, 1)
L = np.zeros(N); R = np.zeros(N)
def add(x, g=1.0, pan=0.0):
    global L, R
    L += x * g * (1 - pan); R += x * g * (1 + pan)
SH = {n: (a, b) for a, b, n in shot_timeline()}
S = lambda n: SH[n][0]
def thump(at, f0=70, f1=38, dur=0.35, g=1.0):
    i0 = int(at * SR); n = min(int(dur * SR), N - i0); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt * 18)) / SR
    x = np.zeros(N); x[i0:i0 + n] = np.sin(ph) * np.exp(-tt * 9) * g; return x
def boom(at, g=1.0):
    x = thump(at, 90, 28, 2.5); i0 = int(at * SR); n = min(int(1.5 * SR), N - i0); tt = np.arange(n) / SR
    nz = np.zeros(N); nz[i0:i0 + n] = lp(rng.standard_normal(n), 0.04) * np.exp(-tt * 4) * 3
    return (x + nz) * g
def riser(end, dur=1.6):
    a = end - dur; m = seg(a, end + 0.02, 0.02) * np.clip((t - a) / dur, 0, 1) ** 2
    x = rng.standard_normal(N); return (x - lp(x, 0.05)) * m
def click(at, g=1.0):
    i0 = int(at * SR); x = np.zeros(N); n = min(350, N - i0)
    x[i0:i0 + n] = rng.standard_normal(n) * np.exp(-np.arange(n) / 45); return (x - lp(x, 0.3)) * g

key = [(0, .6), (S("tracks_close"), .8), (S("farm_wide"), .4), (S("attic"), .8), (S("newspaper"), .6), (S("poll"), .3),
       (S("farm_night"), .6), (S("barn_door") - 0.1, 1.0), (S("window_dark"), .7), (S("kitchen_killer"), 1.0),
       (S("neighbors"), .6), (S("case_file"), .7), (S("field"), .4), (S("end_card"), .9), (TOTAL, .8)]
I = np.interp(t, [k[0] for k in key], [k[1] for k in key])
for f, g in [(36.7, .32), (36.95, .22), (73.4, .16), (110.0, .08), (155.6, .05), (220.0, .03)]:
    add(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t + f)), g * 0.5 * (0.4 + 0.8 * I))
# viento invernal constante, más fuerte en exteriores
outside = np.zeros(N)
for n in ["tracks_farm", "tracks_close", "farm_wide", "lantern_tracks", "maid_leaving", "farm_night", "new_maid", "chimney", "neighbors", "field", "memorial"]:
    a0, b0 = SH[n]; outside = np.maximum(outside, seg(a0, b0, 0.3))
for p_ in (-0.4, 0.4):
    w = lp(rng.standard_normal(N), 0.006) * 9 * (0.6 + 0.4 * np.sin(2 * np.pi * (0.13 + p_ * 0.05) * t))
    add(w, 0.03 + 0.06 * outside, p_)
# pisadas en la nieve
def crunch(at, g=1.0):
    i0 = int(at * SR); n = min(int(0.18 * SR), N - i0); x = np.zeros(N)
    x[i0:i0 + n] = rng.standard_normal(n) * np.exp(-np.arange(n) / (0.05 * SR)) * (rng.random(n) > 0.6)
    return (x - lp(x, 0.2)) * g
for n, step in [("tracks_farm", 0.55), ("tracks_close", 0.6), ("maid_leaving", 0.5), ("new_maid", 0.5), ("neighbors", 0.45)]:
    a0, b0 = SH[n]; k = a0 + 0.2
    while k < b0 - 0.1: add(crunch(k, rng.uniform(0.6, 1)), 0.1, rng.uniform(-0.3, 0.3)); k += step
# pasos en el desván (madera)
a0, b0 = SH["attic"]; k = a0 + 0.3
while k < b0: add(thump(k, 120, 60, 0.18, 1.0), 0.45, 0.2); k += 0.62
for k in range(3): add(thump(SH["end_card"][0] + 0.5 + k * 0.6, 120, 60, 0.18), 0.4, -0.2)
# crujido de madera
cr = np.sin(2 * np.pi * np.cumsum(260 + 120 * np.sin(2 * np.pi * 0.9 * t) + 40 * rng.standard_normal(N)) / SR)
add(cr * seg(SH["attic_lantern"][0], SH["attic_lantern"][1], 0.3), 0.02)
add(cr * seg(SH["barn_door"][0], SH["barn_door"][1] - 0.5, 0.2), 0.03)
# papel del periódico
x = rng.standard_normal(N); add((x - lp(x, 0.3)) * seg(S("newspaper"), S("newspaper") + 0.5, 0.05) * (rng.random(N) > 0.5), 0.05)
# tic-tac en la encuesta
for j in range(int((SH["poll"][1] - S("poll")) / 0.5)):
    add(click(S("poll") + j * 0.5, 1.2 if j % 2 == 0 else 0.7), 0.15)
# fuego crepitando (chimenea y cocina)
fire = np.zeros(N)
for j in range(400):
    at = rng.uniform(S("chimney"), SH["kitchen_killer"][1]); i0 = int(at * SR); n = 200
    if i0 + n < N: fire[i0:i0 + n] += rng.standard_normal(n) * np.exp(-np.arange(n) / 30) * rng.uniform(0.2, 1)
add((fire - lp(fire, 0.3)) + lp(rng.standard_normal(N), 0.01) * 4 * seg(S("chimney"), SH["kitchen_killer"][1], 0.4), 0.08)
# vacas (mugido grave y lejano)
for at in [S("stable") + 0.3]:
    f0 = 140 + 30 * np.sin(np.clip(t - at, 0, 1.4) * 2)
    add(np.sin(2 * np.pi * np.cumsum(f0) / SR) * seg(at, at + 1.4, 0.3) * (0.6 + 0.4 * np.sin(2 * np.pi * 280 * t)), 0.05)
# sello
add(thump(S("case_file") + 0.4 * (SH["case_file"][1] - S("case_file")), 160, 60, 0.2), 0.6)
# latidos
for (a1, b1) in [(S("new_maid"), SH["barn_door"][0]), (S("kitchen_killer"), SH["kitchen_killer"][1])]:
    k = a1
    while k < b1:
        add(thump(k, 58, 38, 0.25), 0.5); add(thump(k + 0.17, 52, 36, 0.25, 0.7), 0.4); k += 0.75
for at in [0.05, S("tracks_close") + 0.3, S("attic"), S("barn_door"), S("kitchen_killer"), S("case_file"), S("end_card")]:
    add(boom(at), 0.55)
for e in [S("barn_door"), S("kitchen_killer")]: add(riser(e), 0.1)
for (a, b, s_) in shot_timeline()[1:]:
    x = rng.standard_normal(N); m = np.exp(-((t - a) / 0.1) ** 2)
    add((x - lp(x, 0.1)) * m, 0.045, rng.uniform(-0.5, 0.5))

music = np.stack([L, R], 1)
music = np.tanh(music * 1.4) / np.tanh(1.4); music /= np.abs(music).max()
clips = np.load(os.path.join(HERE, "voice_clips.npy"), allow_pickle=True)
vo = np.zeros(N)
for sc, x in zip(SCENES, clips):
    i0 = int(sc[5] * SR); x = np.asarray(x, float)[: N - i0]; vo[i0:i0 + len(x)] += x
env = np.convolve(np.abs(vo), np.ones(2400) / 2400, "same")
env = lfilter([0.0008], [1, -0.9992], (env > 0.02).astype(float))
duck = 1 - 0.65 * np.clip(env * 1.6, 0, 1)
mix = music * 0.5 * duck[:, None] + vo[:, None] * 0.95
mix *= (np.clip((TOTAL + 0.4 - t) / 1.0, 0, 1) * np.clip(t / 0.02, 0, 1))[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2); mix /= np.abs(mix).max() / 0.93
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("audio ok", round(N / SR, 1))
