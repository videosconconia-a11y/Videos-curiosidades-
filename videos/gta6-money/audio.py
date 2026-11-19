# Original upbeat "money" trap-pop score (128 BPM, F minor, plucks + 808 + claps) + cash SFX + voice ducking. All synthesised.
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json"))); TOTAL = TM["total"]
N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(12)
SL, SR_ = np.zeros(N), np.zeros(N)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
def put(buf, x, at, g=1.0):
    i0 = int(at * SR)
    if i0 < 0: x = x[-i0:]; i0 = 0
    if i0 >= N: return
    k = min(len(x), N - i0); buf[i0:i0 + k] += x[:k] * g
def sfx(x, g=1.0, pan=0.0, at=0.0): put(SL, x, at, g * (1 - pan) ** .5); put(SR_, x, at, g * (1 + pan) ** .5)
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
sys.argv = [sys.argv[0], "none"]
import render as RD
st = RD.st
BPM = 128; beat = 60 / BPM; bar = 4 * beat
chords = [(65, 68, 72), (61, 65, 68), (63, 67, 70), (60, 63, 67)]; roots = [41, 37, 39, 36]
def pluck(f, d=.25):
    n = int(d * SR); tt = np.arange(n) / SR; x = 2 * ((f * tt) % 1) - 1
    return lp(x, 2600) * np.exp(-tt * 14)
def e808(f, d):
    n = int(d * SR); tt = np.arange(n) / SR
    return np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f * (1 + 1.2 * np.exp(-tt * 40))) / SR)) * np.exp(-tt * 2.2)
def kick():
    n = int(.3 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(50 + 110 * np.exp(-tt * 35)) / SR) * np.exp(-tt * 9)
def clap():
    n = int(.18 * SR); x = hp(rng.standard_normal(n), 1200) * np.exp(-np.arange(n) / SR * 24)
    for dl in (.01, .02): k = int(dl * SR); x[k:] += x[:-k] * .5
    return x * .6
def hat(): n = int(.03 * SR); return hp(rng.standard_normal(n), 8000) * np.exp(-np.arange(n) / 200)
mus = np.zeros(N)
for b in range(int(TOTAL / bar) + 2):
    a0 = b * bar; c = chords[b % 4]
    put(mus, e808(mtof(roots[b % 4]), beat * 1.8), a0, .4); put(mus, e808(mtof(roots[b % 4]), beat * 1.2), a0 + 2.5 * beat, .3)
    for k, m in enumerate([0, 2, 1, 2, 0, 1, 2, 1]): put(mus, pluck(mtof(c[m] + 12)), a0 + k * beat / 2, .1)
    for k in range(4):
        put(mus, kick(), a0 + k * beat, .55 if k in (0, 2) else 0)
        if k in (1, 3): put(mus, clap(), a0 + k * beat, .35)
    for k in range(8): put(mus, hat(), a0 + k * beat / 2 + beat / 4, .18)
def whoosh(d=.25):
    n = int(d * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    return (lp(x, 1600) * (1 - tt / d) + hp(x, 3000) * tt / d) * np.sin(np.pi * tt / d) ** 2
def ding(f, d): n = int(d * SR); tt = np.arange(n) / SR; return (np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * f * 2.01 * tt)) * np.exp(-tt * 8)
def register():
    x = np.concatenate([ding(2600, .12) * .6, ding(3300, .7)])
    n = int(.12 * SR); x[:n] += hp(rng.standard_normal(n), 4000) * np.exp(-np.arange(n) / 900) * .5
    return x
def pop():
    n = int(.08 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(900 + 6000 * tt) / SR) * np.exp(-tt * 40)
def tick(): n = int(.012 * SR); return hp(rng.standard_normal(n), 3000) * np.exp(-np.arange(n) / 70)
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(whoosh(), .28, .4, a - .08)
sfx(register(), .45, 0, .1)
for k in range(10): sfx(tick(), .1, rng.uniform(-.5, .5), .3 + k * .12)
sfx(pop(), .4, 0, RD.word_time("hook", "four"))
for name in ("m1", "m2", "m3", "m4"): sfx(pop(), .45, -.3, st(name) + .3)
for name in ("m2b", "m3b", "m4b"):
    s = st(name)
    for k in range(14): sfx(tick(), .12, rng.uniform(-.3, .3), s + .2 + k * .055)
    sfx(register(), .45, .2, s + 1.0)
a = st("outro")
for k in range(4): sfx(pop(), .3, (k - 1.5) / 2, a + .6 + k * .15)
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + .25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * .9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
envv = lfilter([1 - .9993], [1, -.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([.002], [1, -.998], act) * 1.4, 0, 1)
mg = (1 - .75 * duck) * .55
outL = mus * mg + SL * (1 - .3 * duck) + voice; outR = mus * mg + SR_ * (1 - .3 * duck) + voice
fade = np.clip((TOTAL - t) / .3, 0, 1) * np.clip(t / .01, 0, 1)
s = np.stack([outL, outR], 1) * fade[:, None]; s = np.tanh(s * 1.2) / np.tanh(1.2); s /= np.abs(s).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), s.astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 2))
