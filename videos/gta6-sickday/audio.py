# Original cartoon score (bouncy 110 BPM ukulele-style plucks + bass + glockenspiel, C major; turns minor on the delays)
# + cartoon SFX (boing, pop, sad trombone, sob, static, scream, ding) + voice with ducking. All synthesised here.
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json"))); TOTAL = TM["total"]
N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(8)
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
def ks(f, d=.5):                                  # Karplus-Strong pluck (ukulele-ish)
    n = int(d * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n): out[i] = buf[i % p]; buf[i % p] = .5 * (buf[i % p] + buf[(i + 1) % p]) * .996
    return out
def glock(f, d=.8): n = int(d * SR); tt = np.arange(n) / SR; return (np.sin(2 * np.pi * f * tt) + .3 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 6)
def bassn(f, d): n = int(d * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5) * np.minimum(1, tt / .005)
BPM = 110; beat = 60 / BPM; bar = 4 * beat
major = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]; minor = [(57, 60, 64), (53, 56, 60), (55, 58, 62), (52, 55, 59)]
d0, d1 = -10, -10
mus = np.zeros(N)
for b in range(int(TOTAL / bar) + 2):
    a0 = b * bar; ch = (minor if d0 - .1 <= a0 < d1 else major)[b % 4]
    for k, m in enumerate([0, 1, 2, 1, 0, 2, 1, 2]): put(mus, ks(mtof(ch[m])), a0 + k * beat / 2, .16)
    put(mus, bassn(mtof(ch[0] - 24), beat * 1.5), a0, .35); put(mus, bassn(mtof(ch[2] - 24), beat * 1.5), a0 + 2 * beat, .3)
    if b % 2 == 0: put(mus, glock(mtof(ch[2] + 12)), a0 + 3 * beat, .06)
def boing(d=.35):
    n = int(d * SR); tt = np.arange(n) / SR; f = 220 + 180 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 6)
    return np.sin(2 * np.pi * np.cumsum(f + 200 * tt) / SR) * np.exp(-tt * 5)
def pop(): n = int(.08 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(900 + 6000 * tt) / SR) * np.exp(-tt * 40)
def whoosh(d=.25):
    n = int(d * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    return (lp(x, 1600) * (1 - tt / d) + hp(x, 3000) * tt / d) * np.sin(np.pi * tt / d) ** 2
def trombone():
    out = []
    for m, d in ((58, .3), (57, .3), (56, .3), (55, 1.0)):
        n = int(d * SR); tt = np.arange(n) / SR; f = mtof(m - 12) * (1 + .03 * np.sin(2 * np.pi * 6 * tt) * (d > .5))
        x = sum(np.sin(2 * np.pi * np.cumsum(f * h) / SR) / h for h in range(1, 7))
        out.append(lp(x, 1400) * np.minimum(1, tt / .02) * np.minimum(1, (d - tt) / .05))
    return np.concatenate(out) * .5
def sob():
    out = np.zeros(int(1.2 * SR))
    for k in range(4):
        n = int(.18 * SR); tt = np.arange(n) / SR; f = 520 - 120 * tt / .18
        out[int(k * .26 * SR):int(k * .26 * SR) + n] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / .18) * (1 + .5 * np.sin(2 * np.pi * 30 * tt))
    return out * .4
def static(d): n = int(d * SR); return hp(rng.standard_normal(n), 2000) * .25
def scream(d=1.2):
    n = int(d * SR); tt = np.arange(n) / SR; f = 600 + 250 * np.sin(2 * np.pi * 5 * tt)
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * .35 * np.minimum(1, tt / .05) * np.minimum(1, (d - tt) / .2)
def ding(): n = int(.9 * SR); tt = np.arange(n) / SR; return (np.sin(2 * np.pi * 1568 * tt) + .4 * np.sin(2 * np.pi * 2093 * tt)) * np.exp(-tt * 4)
def stampsnd(): n = int(.35 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(70 + 120 * np.exp(-tt * 35)) / SR) * np.exp(-tt * 12) + lp(rng.standard_normal(n), 1200) * np.exp(-tt * 30)
def alarm_bell(d=1.6):
    n = int(d * SR); tt = np.arange(n) / SR; on = ((tt % .12) < .07).astype(float)
    return (np.sin(2 * np.pi * 2200 * tt) + .6 * np.sin(2 * np.pi * 3100 * tt)) * on * .3 * np.exp(-tt * .6)
def cough():
    out = np.zeros(int(.6 * SR))
    for k in range(2):
        n = int(.16 * SR); tt = np.arange(n) / SR; x = lp(rng.standard_normal(n), 1800) * np.exp(-tt * 18) + np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 25) * .5
        out[int(k * .25 * SR):int(k * .25 * SR) + n] += x
    return out * .7
def ringback(d=1.0):
    n = int(d * SR); tt = np.arange(n) / SR; on = ((tt % .5) < .3).astype(float)
    return (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * .12 * on
def tumble(d=2.0): n = int(d * SR); return lp(rng.standard_normal(n), 600) * .15 + hp(rng.standard_normal(n), 3000) * .03
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(whoosh(), .25, rng.uniform(-.4, .4), a - .08); sfx(boing(), .15, 0, a + .05)
sfx(pop(), .4, 0, .15)
sfx(alarm_bell(), .6, 0, st("alarm") + .05)
sfx(ringback(1.0), .5, .3, st("call") + .05)
sfx(cough(), .8, -.2, RD.word_time("call", "cough,") - .05)
sfx(cough(), .8, .3, RD.word_time("boss", "cough,") - .05)
sfx(ding(), .35, 0, RD.word_time("boss", "me") - .05)
sfx(tumble(), .5, 0, st("office")); sfx(trombone(), .35, 0, st("office") + .3)
sfx(pop(), .4, 0, st("outro") + .05); sfx(ding(), .3, 0, st("outro") + .3)
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + .25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * .9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
envv = lfilter([1 - .9993], [1, -.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([.002], [1, -.998], act) * 1.4, 0, 1)
mg = (1 - .7 * duck) * .6
outL = mus * mg + SL * (1 - .3 * duck) + voice; outR = mus * mg + SR_ * (1 - .3 * duck) + voice
fade = np.clip((TOTAL - t) / .3, 0, 1) * np.clip(t / .01, 0, 1)
s = np.stack([outL, outR], 1) * fade[:, None]; s = np.tanh(s * 1.2) / np.tanh(1.2); s /= np.abs(s).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), s.astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 2))
