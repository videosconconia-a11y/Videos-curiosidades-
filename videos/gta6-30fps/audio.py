# Original dark trap score (140 BPM half-time, C minor 808 + bell) + glitch/UI SFX + voice with ducking. All synthesised.
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json"))); TOTAL = TM["total"]
N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(30)
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
BPM = 140; beat = 60 / BPM; bar = 4 * beat
roots = [36, 36, 32, 34]; bells = [(72, 75, 79), (72, 75, 79), (68, 72, 75), (70, 74, 77)]
def e808(f, d):
    n = int(d * SR); tt = np.arange(n) / SR
    return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * np.exp(-tt * 40))) / SR)) * np.exp(-tt * 1.6)
def bell(f, d=.6):
    n = int(d * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 9)) * np.exp(-tt * 5)
def clap():
    n = int(.2 * SR); x = hp(rng.standard_normal(n), 1100) * np.exp(-np.arange(n) / SR * 22)
    for dl in (.01, .02): k = int(dl * SR); x[k:] += x[:-k] * .5
    return x * .7
def hat(): n = int(.03 * SR); return hp(rng.standard_normal(n), 8000) * np.exp(-np.arange(n) / 200)
bass = np.zeros(N); mel = np.zeros(N); drums = np.zeros(N)
quiet0, quiet1 = st("beauty"), st("outro")
for b in range(int(TOTAL / bar) + 2):
    a0 = b * bar
    put(bass, e808(mtof(roots[b % 4]), bar * .9), a0, .5)
    for k, m in enumerate([0, 1, 2, 1, 0, 2, 1, 2]):
        put(mel, bell(mtof(bells[b % 4][m])), a0 + k * beat / 2, .08)
    if a0 < st("split") - .1: continue
    put(drums, clap(), a0 + 2 * beat, .5)
    for k in range(16):
        x = a0 + k * beat / 4
        if k % 3 == 0 or (b % 2 and k > 12): put(drums, hat(), x, .25)
music = bass + mel + drums
g = np.ones(N); g[(t >= quiet0) & (t < quiet1)] = .55
music *= lfilter([.002], [1, -.998], g) / max(lfilter([.002], [1, -.998], g).max(), 1e-6)
musL = music + .2 * mel; musR = music - .2 * mel
def glitch(d=.18):
    n = int(d * SR); x = np.zeros(n)
    for k in range(0, n, int(.015 * SR)):
        m = min(int(.012 * SR), n - k); x[k:k + m] = np.sign(np.sin(2 * np.pi * rng.uniform(200, 3000) * np.arange(m) / SR)) * rng.uniform(.3, 1)
    return x * .5
def thud():
    n = int(.6 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 8) + lp(rng.standard_normal(n), 900) * np.exp(-tt * 30)
def alarm(d=1.0):
    n = int(d * SR); tt = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * (650 + 200 * (np.sin(2 * np.pi * 4 * tt) > 0)) * tt)) * .2 * np.exp(-tt * 1.5)
def beep(f=1800, d=.07): n = int(d * SR); return np.sin(2 * np.pi * f * np.arange(n) / SR) * np.minimum(1, (n - np.arange(n)) / 200)
def down(d=1.5):
    n = int(d * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-tt * 1.8) + 60) / SR) * .4 * np.exp(-tt * .8)
def chime():
    n = int(2 * SR); tt = np.arange(n) / SR; return sum(np.sin(2 * np.pi * mtof(m) * tt) * np.exp(-tt * 2) for m in (72, 76, 79)) * .3
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(glitch(), .25, rng.uniform(-.4, .4), a - .02)
k = RD.word_time("hook", "one") - .1; sfx(alarm(), .5, 0, k); sfx(thud(), .7, 0, k + .1)
a = st("consoles")
for i in range(3): sfx(beep(1500 + i * 200), .3, 0, a + .3 + i * .35); sfx(thud(), .35, 0, a + .3 + i * .35)
for w in ("sixty", "forty"): x = RD.word_time("s2", w); sfx(thud(), .5, 0, x); sfx(glitch(.25), .3, 0, x + .2)
a = st("dip"); sfx(down(2.0), .4, 0, a + .8); sfx(thud(), .6, 0, a + 1.6)
a = st("cpu"); sfx(thud(), .6, 0, a)
for w in ("traffic", "crowds", "physics"): sfx(beep(1200), .3, 0, RD.word_time("s4", w)); sfx(thud(), .35, 0, RD.word_time("s4", w))
sfx(chime(), .4, 0, st("beauty") + .4)
y = RD.word_time("outro", "yes"); sfx(beep(1400), .35, -.4, y); sfx(beep(900), .35, .4, y + .35)
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + .25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * .9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
envv = lfilter([1 - .9993], [1, -.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([.002], [1, -.998], act) * 1.4, 0, 1)
mg = (1 - .75 * duck) * .55
outL = musL * mg + SL * (1 - .3 * duck) + voice; outR = musR * mg + SR_ * (1 - .3 * duck) + voice
fade = np.clip((TOTAL - t) / .3, 0, 1) * np.clip(t / .01, 0, 1)
s = np.stack([outL, outR], 1) * fade[:, None]; s = np.tanh(s * 1.2) / np.tanh(1.2); s /= np.abs(s).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), s.astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 2))
