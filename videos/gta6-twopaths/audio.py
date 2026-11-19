# Original score, no voice. Part 1: light plucky walking tune + crowd footsteps; record-scratch when "ME" breaks away;
# riser into the white flash. Part 2 (120 BPM, beat-synced to the cuts): BOOM, taiko/tom drums, kick on every beat,
# "braam" brass on each bar, 16th-note string ostinato, cymbal on each cut, double-time burst, final hit + tail.
import os, sys, math
import numpy as np
from scipy.signal import butter, sosfilt
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "none"]
import render as RD
SR = 48000; TOTAL = RD.TOTAL; N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(6)
L, R = np.zeros(N), np.zeros(N)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
def put(x, at, g=1.0, pan=0.0):
    i0 = int(at * SR)
    if i0 < 0: x = x[-i0:]; i0 = 0
    if i0 >= N: return
    k = min(len(x), N - i0); L[i0:i0 + k] += x[:k] * g * (1 - pan) ** .5; R[i0:i0 + k] += x[:k] * g * (1 + pan) ** .5
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
def env(n, a, d): tt = np.arange(n) / SR; return np.minimum(1, tt / a) * np.exp(-tt / d)
def saw(f, n): tt = np.arange(n) / SR; return 2 * ((f * tt) % 1) - 1
# ---- part 1
for k, m in enumerate([72, 76, 79, 76, 74, 77, 81, 77] * 3):
    at = k * .25
    if at > RD.T_SPLIT - .1: break
    n = int(.2 * SR); put(np.sin(2 * np.pi * mtof(m) * np.arange(n) / SR) * env(n, .003, .06), at, .12, .3 * math.sin(k))
for k in range(int(RD.T_PUSH / .18)):
    n = int(.05 * SR); put(lp(rng.standard_normal(n), 900) * env(n, .002, .02), k * .18, .05, rng.uniform(-.6, .6))
n = int(.35 * SR); tt = np.arange(n) / SR
put(np.sin(2 * np.pi * np.cumsum(300 + 900 * np.sin(2 * np.pi * 6 * tt)) / SR) * np.exp(-tt * 4) * .5, RD.T_SPLIT - .05, .5)
d = RD.T_EDIT - RD.T_PUSH + .3; n = int(d * SR); tt = np.arange(n) / SR
put((hp(rng.standard_normal(n), 1500) * (tt / d) ** 3 * .6 + np.sin(2 * np.pi * np.cumsum(120 + 1500 * (tt / d) ** 2) / SR) * (tt / d) ** 2 * .5), RD.T_PUSH, .6)
# ---- part 2
E0 = RD.T_EDIT; BEAT = RD.MUSIC_BEAT; END = RD.T_EDIT + RD.EDIT_LEN
def boom(dur=2.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-tt * 6)) / SR) * np.exp(-tt * 1.6) + lp(rng.standard_normal(n), 400) * np.exp(-tt * 4) * .8
def kick():
    n = int(.35 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(45 + 120 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 7)
def tom(f):
    n = int(.5 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(f * (1 + .7 * np.exp(-tt * 18))) / SR) * np.exp(-tt * 6) + lp(rng.standard_normal(n), 500) * np.exp(-tt * 25) * .4
def cym(d=1.4):
    n = int(d * SR); return hp(rng.standard_normal(n), 5000) * env(n, .002, .45) * .5
def braam(root, d=1.8):
    n = int(d * SR); x = np.zeros(n)
    for m in (root - 12, root, root + 7, root + 12):
        for det in (-.15, 0, .15): x += saw(mtof(m) * (1 + det / 100), n)
    e = env(n, .02, .9); return lp(np.tanh(x * .4), 1400) * e
roots = [38, 34, 36, 33]
put(boom(), E0, 1.0); put(cym(2.5), E0, .5)
b = 0; x = E0
FAST = E0 + sum(RD.CUTS[:4])
while x < END - .01:
    put(kick(), x, .9)
    if b % 2 == 1 or x > FAST: put(tom(110), x, .55, -.3); put(tom(80), x + BEAT / 2, .45, .3)
    if b % 4 == 0: put(braam(roots[(b // 4) % 4]), x, .35)
    for s16 in range(4):                                    # string ostinato
        n = int(BEAT / 4 * SR); m = roots[(b // 4) % 4] + 24 + [0, 7, 12, 7][s16]
        put(lp(saw(mtof(m), n), 2500) * env(n, .005, .08), x + s16 * BEAT / 4, .07, .4 if s16 % 2 else -.4)
    x += BEAT; b += 1
for st_ in RD.STARTS[1:]:
    put(cym(.6), st_, .25); put(hp(rng.standard_normal(int(.05 * SR)), 2000) * env(int(.05 * SR), .001, .01), st_, .3)
put(boom(3.0), END, 1.0); put(braam(38, 3.0), END, .45); put(cym(3.0), END, .5)
mix = np.stack([L, R], 1)
fade = np.clip((TOTAL - t) / .5, 0, 1)[:, None] * np.clip(t / .01, 0, 1)[:, None]
mix = np.tanh(mix * fade * 1.3) / np.tanh(1.3); mix /= np.abs(mix).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), mix.astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 2))
