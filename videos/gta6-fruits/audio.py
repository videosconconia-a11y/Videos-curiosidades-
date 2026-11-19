# Original reality-show "fruit drama" score: lounge Rhodes + soft beat in F, a ticking clock under the night skips,
# dramatic "dun-dun-DUN" stinger on the twist, upbeat ending. SFX: time-skip whoosh, clock ticks, record scratch,
# gasp-like riser, pops. Voice with ducking. All synthesised here.
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json"))); TOTAL = TM["total"]
N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(21)
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
BPM = 96; beat = 60 / BPM; bar = 4 * beat
chords = [(65, 69, 72, 76), (62, 65, 69, 72), (58, 62, 65, 69), (60, 64, 67, 70)]
def rhodes(f, d): n = int(d * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * f * tt + .7 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3)) * np.exp(-tt * 1.6)
def kick(): n = int(.3 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9)
def snap(): n = int(.12 * SR); return hp(rng.standard_normal(n), 2000) * np.exp(-np.arange(n) / SR * 40) * .5
tw0, tw1 = st("twist"), st("outro")
mus = np.zeros(N)
for b in range(int(TOTAL / bar) + 2):
    a0 = b * bar
    if tw0 - .2 <= a0 < tw1 - .2: continue
    for m in chords[b % 4]: put(mus, rhodes(mtof(m), bar), a0, .05)
    put(mus, rhodes(mtof(chords[b % 4][0] - 24), bar), a0, .12)
    for k in range(4):
        put(mus, kick() if k in (0, 2) else snap(), a0 + k * beat, .45 if k in (0, 2) else .3)
def tick(): n = int(.015 * SR); return hp(rng.standard_normal(n), 3000) * np.exp(-np.arange(n) / 80)
def whoosh(d=.35):
    n = int(d * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    return (lp(x, 1600) * (1 - tt / d) + hp(x, 3000) * tt / d) * np.sin(np.pi * tt / d) ** 2
def stinger():
    out = np.zeros(int(2.6 * SR))
    for k, (m, d) in enumerate(((50, .25), (50, .25), (47, 1.6))):
        n = int(d * SR); tt = np.arange(n) / SR; x = sum(np.sin(2 * np.pi * mtof(mm) * tt * (1 + .002 * h)) for mm in (m, m + 3, m + 7, m - 12) for h in (0, 1))
        x = lp(x, 1800) * np.minimum(1, tt / .01) * np.exp(-tt * (1.2 if d > 1 else 6))
        i0 = int([0, .35, .7][k] * SR); out[i0:i0 + n] += x
    return out * .18
def scratch(d=.35): n = int(d * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(300 + 900 * np.sin(2 * np.pi * 6 * tt)) / SR) * .3 * np.exp(-tt * 4) + hp(rng.standard_normal(n), 2000) * .1
def pop(): n = int(.08 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(900 + 6000 * tt) / SR) * np.exp(-tt * 40)
def ding(): n = int(.9 * SR); tt = np.arange(n) / SR; return (np.sin(2 * np.pi * 1568 * tt) + .4 * np.sin(2 * np.pi * 2093 * tt)) * np.exp(-tt * 4)
def boing(d=.35):
    n = int(d * SR); tt = np.arange(n) / SR; f = 220 + 180 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 6)
    return np.sin(2 * np.pi * np.cumsum(f + 200 * tt) / SR) * np.exp(-tt * 5)
for name in ("pm7", "pm11", "am3"):
    a = st(name); sfx(whoosh(), .4, 0, a - .1); sfx(ding(), .25, 0, a + .05)
    for k in range(int(1.2 / .5)): sfx(tick(), .35, .4, a + .3 + k * .5)
for name in ("pm7b", "pm7c", "pm11b"): sfx(pop(), .35, 0, st(name) + .05)
sfx(pop(), .35, 0, .15)
sfx(scratch(), .5, 0, st("twist") - .05); sfx(stinger(), .9, 0, st("twist") + .3)
sfx(boing(), .35, 0, st("twist2") + .05); sfx(ding(), .3, 0, st("twist2") + .6)
sfx(pop(), .4, 0, st("outro") + .05); sfx(ding(), .35, 0, RD.word_time("outro", "follow"))
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + .25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * .9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
envv = lfilter([1 - .9993], [1, -.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([.002], [1, -.998], act) * 1.4, 0, 1)
mg = (1 - .7 * duck) * .65
outL = mus * mg + SL * (1 - .3 * duck) + voice; outR = mus * mg + SR_ * (1 - .3 * duck) + voice
fade = np.clip((TOTAL - t) / .3, 0, 1) * np.clip(t / .01, 0, 1)
s = np.stack([outL, outR], 1) * fade[:, None]; s = np.tanh(s * 1.2) / np.tanh(1.2); s /= np.abs(s).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), s.astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 2))
