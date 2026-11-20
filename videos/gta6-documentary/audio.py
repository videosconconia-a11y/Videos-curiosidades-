# Original documentary score (all synthesised): slow evolving pads (D minor → F → Bb → C), soft piano motif every 2 bars,
# a heartbeat-like low pulse, sub "boom" + reverse swell into each chapter card, gentle lift for launch week; ducked
# hard under the narration. Output mix.wav (48 kHz stereo).
import os, sys, json
import numpy as np
from scipy.signal import butter, sosfilt, lfilter, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "none"]
import render as RD
SR = 48000; TOTAL = RD.TOTAL; N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(12)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
L = np.zeros(N); R = np.zeros(N)
def put(x, at, g=1.0, pan=0.0):
    i0 = int(at * SR)
    if i0 < 0: x = x[-i0:]; i0 = 0
    if i0 >= N: return
    k = min(len(x), N - i0); L[i0:i0 + k] += x[:k] * g * (1 - pan) ** .5; R[i0:i0 + k] += x[:k] * g * (1 + pan) ** .5
BAR = 4 * 60 / 72
prog = [(50, 57, 62, 65), (53, 60, 65, 69), (46, 53, 58, 62), (48, 55, 60, 64)]
for b in range(int(TOTAL / BAR) + 2):
    ch = prog[b % 4]; n = int(BAR * 1.3 * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for m in ch:
        for det in (-.2, .2): x += np.sin(2 * np.pi * mtof(m) * (1 + det / 100) * tt + rng.uniform(0, 6))
    e = np.minimum(1, tt / 1.6) * np.minimum(1, (n / SR - tt) / 1.4)
    put(lp(x, 1200) * e * .035, b * BAR, 1, rng.uniform(-.3, .3))
    if b % 2 == 0:
        for k, m in enumerate((ch[3] + 12, ch[2] + 12, ch[1] + 12)):
            nn = int(2.5 * SR); tt2 = np.arange(nn) / SR
            put((np.sin(2 * np.pi * mtof(m) * tt2) + .3 * np.sin(4 * np.pi * mtof(m) * tt2)) * np.exp(-tt2 * 1.8) * .05, b * BAR + k * .55, 1, .2)
    for k in range(4):
        nn = int(.4 * SR); tt2 = np.arange(nn) / SR
        put(np.sin(2 * np.pi * np.cumsum(45 + 30 * np.exp(-tt2 * 20)) / SR) * np.exp(-tt2 * 9) * .12, b * BAR + k * BAR / 4)
def boom(d=3.0):
    n = int(d * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(32 + 60 * np.exp(-tt * 5)) / SR) * np.exp(-tt * 1.5) + lp(rng.standard_normal(n), 300) * np.exp(-tt * 3) * .5
def swell(d=1.5):
    n = int(d * SR); tt = np.arange(n) / SR; return hp(rng.standard_normal(n), 2000) * (tt / d) ** 3 * .25
for a, b, sd, sg in RD.WIN:
    if sd["chapter"]: put(swell(), a - 1.4, .5); put(boom(), a + .05, .55)
put(boom(4), 0.0, .5)
mus = np.stack([L, R], 1)
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 80); voice = voice + .2 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * .9; voice = np.tanh(voice * 1.5) / np.tanh(1.5)
envv = lfilter([1 - .9993], [1, -.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([.0015], [1, -.9985], act) * 1.4, 0, 1)
mus = mus * ((1 - .6 * duck) * .9)[:, None]
out = mus + voice[:, None]
fade = np.clip((TOTAL - t) / 1.5, 0, 1) * np.clip(t / .05, 0, 1)
out = np.tanh(out * fade[:, None] * 1.1) / np.tanh(1.1); out /= np.abs(out).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), out.astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 1))
