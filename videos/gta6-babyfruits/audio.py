# NO background music (as requested): voices + light SFX only. Tiptoe plinks, pops on lines, whoosh on step cards,
# gasp riser on 99%, door slam/flash on Mom, crash, cheer pops, snores. Loudness-normalised by build.sh.
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json"))); TOTAL = TM["total"]
N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(31)
SL, SR_ = np.zeros(N), np.zeros(N)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
def put(buf, x, at, g=1.0):
    i0 = int(at * SR)
    if i0 < 0: x = x[-i0:]; i0 = 0
    if i0 >= N: return
    k = min(len(x), N - i0); buf[i0:i0 + k] += x[:k] * g
def sfx(x, g=1.0, pan=0.0, at=0.0): put(SL, x, at, g * (1 - pan) ** .5); put(SR_, x, at, g * (1 + pan) ** .5)
sys.argv = [sys.argv[0], "none"]
import render as RD
st = RD.st
def pop(): n = int(.08 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(900 + 6000 * tt) / SR) * np.exp(-tt * 40)
def plink(f): n = int(.12 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 30)
def whoosh(d=.3):
    n = int(d * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    return (lp(x, 1600) * (1 - tt / d) + hp(x, 3000) * tt / d) * np.sin(np.pi * tt / d) ** 2
def riser(d=.8): n = int(d * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(200 + 1400 * (tt / d) ** 2) / SR) * (tt / d) ** 2 * .5
def slam(): n = int(.6 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(60 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 8) + lp(rng.standard_normal(n), 900) * np.exp(-tt * 20)
def crash(): n = int(.9 * SR); tt = np.arange(n) / SR; x = hp(rng.standard_normal(n), 800) * np.exp(-tt * 5) * .6; s_ = slam(); x[:len(s_)] += s_ * .7; return x
def ding(): n = int(.8 * SR); tt = np.arange(n) / SR; return (np.sin(2 * np.pi * 1568 * tt) + .4 * np.sin(2 * np.pi * 2093 * tt)) * np.exp(-tt * 4)
def snore(d=1.4): n = int(d * SR); tt = np.arange(n) / SR; return lp(rng.standard_normal(n), 300) * (np.sin(np.pi * tt / d) ** 2) * .5
def squeak(): n = int(.25 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(700 + 500 * np.sin(2 * np.pi * 8 * tt)) / SR) * np.exp(-tt * 6) * .4
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(pop(), .25, rng.uniform(-.3, .3), a)
for name in ("sneak", "ctrl", "tv", "hide"): sfx(whoosh(), .5, 0, st(name) - .05)
sfx(snore(), .5, 0, .2); sfx(snore(), .5, 0, 2.0)
a = st("sneak"); e = st("ctrl")
k = 0; x = a + .1
while x < e - .1: sfx(plink(1200 + 300 * (k % 2)), .25, -.3 + .6 * (k % 2), x); x += .2; k += 1
sfx(squeak(), .6, 0, st("sneak2") - .1)
sfx(riser(), .5, 0, st("pct") - .6); sfx(slam(), .6, 0, st("pct"))
sfx(slam(), .9, 0, st("mom")); sfx(whoosh(.4), .5, 0, st("mom") + .05)
sfx(ding(), .5, 0, st("done")); [sfx(pop(), .4, (i - 2) / 3, st("done2") + i * .12) for i in range(5)]
sfx(crash(), .7, 0, st("crash") + .2)
sfx(ding(), .3, 0, st("morning")); sfx(snore(), .5, 0, st("asleep") + .2); sfx(snore(), .5, 0, st("asleep") + 2.0)
sfx(ding(), .4, 0, RD.word_time("n7", "follow"))
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + .25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * .9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
outL = SL * .8 + voice; outR = SR_ * .8 + voice
fade = np.clip((TOTAL - t) / .3, 0, 1) * np.clip(t / .01, 0, 1)
s = np.stack([outL, outR], 1) * fade[:, None]; s = np.tanh(s * 1.2) / np.tanh(1.2); s /= np.abs(s).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), s.astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 2))
