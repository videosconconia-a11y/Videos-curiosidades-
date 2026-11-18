# Original emotional score + nostalgic sound design + voice with ducking. All synthesised here.
# Music: 76 BPM felt-piano arpeggios over a warm pad in A minor → C (Am F C G), lo-fi tape wobble; on "it's finally here"
# it lifts into a bright full-band swell in C major. SFX: projector rattle, typewriter, stamps, counters, film burns.
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json"))); TOTAL = TM["total"]
N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(9)
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
st = RD.st; HERE_T = RD.COLOR_AT

BPM = 76; beat = 60 / BPM; bar = 4 * beat
prog = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]   # Am F C G
bright = [(48, 52, 55), (55, 59, 62), (57, 60, 64), (53, 57, 60)]  # C G Am F
def piano(f, dur=1.6):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * h * tt) * np.exp(-tt * (2.2 + h * 1.4)) / h ** 1.3 for h in range(1, 6))
    return lp(x * np.minimum(1, tt / .004), 3200)
def padv(ch, dur):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for m in ch:
        for det in (-.12, .12): x += np.sin(2 * np.pi * mtof(m - 12) * (1 + det / 100) * tt)
    return lp(x, 900) * np.minimum(1, tt / .8) * np.minimum(1, (dur - tt) / .5)
pno = np.zeros(N); pad = np.zeros(N); band = np.zeros(N)
nb = int(TOTAL / bar) + 2
for b in range(nb):
    at0 = b * bar; br = at0 >= HERE_T - .05
    ch = (bright if br else prog)[b % 4]
    put(pad, padv(ch, bar + .5), at0, .05 if not br else .08)
    seq = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1], ch[0] + 12, ch[2]]
    for k, m in enumerate(seq):
        put(pno, piano(mtof(m + 12)), at0 + k * beat / 2, .12 if not br else .15)
    put(pno, piano(mtof(ch[0] - 12), 3), at0, .16)
# tape wobble on the sad part
wob = 1 + .003 * np.sin(2 * np.pi * .6 * t)
idx = np.clip(np.cumsum(wob) - wob[0], 0, N - 1).astype(int)
pno = np.where(t < HERE_T, pno[idx], pno)
# full-band lift at "here"
def kick():
    n = int(.35 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(50 + 110 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 7)
x = HERE_T
while x < TOTAL:
    put(band, kick(), x, .5)
    n = int(.2 * SR); put(band, hp(rng.standard_normal(n), 1500) * np.exp(-np.arange(n) / SR * 20) * .3, x + beat)
    x += beat
music = pno + pad + band
musL = music + .2 * pno; musR = music - .2 * pno

def projector(dur):
    n = int(dur * SR); x = np.zeros(n); k = int(SR / 24)
    for i in range(0, n - 200, k): x[i:i + 200] += hp(rng.standard_normal(200), 2000) * np.exp(-np.arange(200) / 40)
    return x + lp(rng.standard_normal(n), 300) * .15
def typekey():
    n = int(.03 * SR); return hp(rng.standard_normal(n), 1800) * np.exp(-np.arange(n) / 120) + np.sin(2 * np.pi * 180 * np.arange(n) / SR) * np.exp(-np.arange(n) / 200) * .5
def stamp():
    n = int(.5 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(60 + 120 * np.exp(-tt * 40)) / SR) * np.exp(-tt * 12) + lp(rng.standard_normal(n), 1500) * np.exp(-tt * 35) * .8
def tick():
    n = int(.012 * SR); return hp(rng.standard_normal(n), 3000) * np.exp(-np.arange(n) / 70)
def burn(dur=.35):
    n = int(dur * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    return lp(x, 2500) * np.sin(np.pi * tt / dur) ** 2
def swell(dur=2.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (lp(rng.standard_normal(n), 600 + 0) * (tt / dur) ** 2 * .5 + np.sin(2 * np.pi * np.cumsum(100 + 500 * (tt / dur) ** 2) / SR) * (tt / dur) ** 3 * .3)
def chime():
    n = int(2.5 * SR); tt = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * mtof(m) * tt) * np.exp(-tt * 1.6) for m in (72, 76, 79, 84)) * .3

sfx(projector(HERE_T), .05, 0, 0)
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(burn(), .2, rng.uniform(-.3, .3), a - .1)
sfx(stamp(), .5, 0, RD.word_time("hook", "officially") + .1); sfx(stamp(), .55, 0, RD.word_time("hook", "officially") + .4)
a = st("date2013")
for k in range(len("September 17, 2013")): sfx(typekey(), .35, rng.uniform(-.2, .2), a + k / 16)
a = st("confirm"); sfx(stamp(), .55, 0, a + .9)
a = RD.word_time("s3", "ninety") - .2
for k in range(28): sfx(tick(), .15, rng.uniform(-.3, .3), a + k * .05)
a = st("record"); sfx(chime(), .3, 0, a)
a = st("delays"); sfx(stamp(), .6, 0, a + .05)
for w in ("fall", "may"): sfx(stamp(), .35, 0, RD.word_time("s4", w) + .25)
a = st("wall")
for k in range(10): sfx(burn(.15), .12, rng.uniform(-.5, .5), a + k * .22)
for k in range(50): sfx(tick(), .12, rng.uniform(-.3, .3), a + k * .052)
sfx(swell(2.0), .35, 0, HERE_T - 2.0); sfx(chime(), .45, 0, HERE_T)

v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + .2 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * .9; voice = np.tanh(voice * 1.6) / np.tanh(1.6)
envv = lfilter([1 - .9993], [1, -.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([.002], [1, -.998], act) * 1.4, 0, 1)
mg = (1 - .65 * duck) * .8
outL = musL * mg + SL * (1 - .3 * duck) + voice; outR = musR * mg + SR_ * (1 - .3 * duck) + voice
fade = np.clip((TOTAL - t) / .5, 0, 1) * np.clip(t / .01, 0, 1)
s = np.stack([outL, outR], 1) * fade[:, None]; s = np.tanh(s * 1.15) / np.tanh(1.15); s /= np.abs(s).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), s.astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 2))
