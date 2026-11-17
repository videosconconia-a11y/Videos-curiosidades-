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

key = [(0, .35), (S("mailbox"), .5), (S("letter1"), .6), (S("house_day"), .35), (S("kids_room"), .85), (S("wall"), .9),
       (S("generations"), .6), (S("street_cars"), .7), (S("signature") - 0.1, 1.0), (S("poll"), .3), (S("letter2"), .9),
       (S("house_empty"), .5), (S("case_file"), .7), (S("sold"), .4), (S("watcher_street"), .9), (TOTAL, .7)]
I = np.interp(t, [k[0] for k in key], [k[1] for k in key])
# dron disonante + pad
for f, g in [(43.65, .32), (43.9, .22), (87.3, .16), (123.5, .09), (174.6, .05), (246.9, .03)]:
    add(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t + f)), g * 0.5 * (0.4 + 0.8 * I))
for p in (-0.3, 0.3):
    add(lp(rng.standard_normal(N), 0.003) * 9 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t + p * 5)), 0.035, p)
# caja de música (vecindario "perfecto" que se tuerce)
mel = [659.3, 587.3, 523.3, 493.9, 523.3, 440.0, 415.3, 440.0]
k, at = 0, 0.2
while at < TOTAL - 1:
    f = mel[k % len(mel)] * (1 if at < S("kids_room") else 0.985)
    i0 = int(at * SR); n = min(int(1.6 * SR), N - i0); tt = np.arange(n) / SR
    x = np.zeros(N); x[i0:i0 + n] = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * f * 3.01 * tt)) * np.exp(-tt * 3)
    add(x, 0.03 if not (S("poll") <= at < S("letters_pile")) else 0.0, 0.3 * math.sin(k) if False else 0.0)
    at += 0.75; k += 1
# máquina de escribir sincronizada con el texto que aparece en las cartas
for (a, b, _n, _k, shots, v0, vd, words) in SCENES:
    if shots[0] in ("letter1", "letter2") and words:
        end = words[-1][1]; n_chars = int((end - v0) * 14)
        for j in range(n_chars):
            add(click(v0 + j * (end - v0) / n_chars + rng.uniform(-0.01, 0.01), rng.uniform(0.5, 1)), 0.12, rng.uniform(-0.3, 0.3))
        add(thump(end + 0.05, 1200, 900, 0.05, 1), 0.05)   # "ding"
# buzón, coches, sello, encuesta
add(thump(S("mailbox") + 0.3, 180, 110, 0.25) + click(S("mailbox") + 0.3, 2), 0.3)
for kk in range(3):
    u0 = (0.2 - kk * 0.37) / 0.55
    for rep in range(3):
        at = S("street_cars") + ((0.2 + 0.2 - kk * 0.37) % 1.4) / 0.55 + rep * 1.4 / 0.55
        if S("street_cars") < at < SH["street_cars"][1]:
            x = rng.standard_normal(N); add((lp(x, 0.03)) * np.exp(-((t - at) / 0.5) ** 2) * 6, 0.12, 0.0)
add(thump(S("case_file") + 0.35 * (SH["case_file"][1] - S("case_file")), 160, 60, 0.2), 0.6)
for j in range(int((SH["poll"][1] - S("poll")) / 0.5)):
    add(click(S("poll") + j * 0.5, 1.2 if j % 2 == 0 else 0.7), 0.15)          # tic-tac
# latido mientras lee la carta 2 y al final
for (a0, a1) in [(S("letter2"), SH["letter2"][1]), (S("watcher_street"), TOTAL - 1)]:
    k = a0
    while k < a1:
        add(thump(k, 58, 38, 0.25), 0.5); add(thump(k + 0.17, 52, 36, 0.25, 0.7), 0.4); k += 0.85
for at in [S("kids_room"), S("wall"), S("signature"), S("case_file"), S("watcher_street"), S("end_card")]:
    add(boom(at), 0.55)
for e in [S("kids_room"), S("signature")]: add(riser(e), 0.1)
for (a, b, s) in shot_timeline()[1:]:
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
