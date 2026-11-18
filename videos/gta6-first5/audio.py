# Original light comedic score + phone-UI sound design + voice with side-chain ducking. All synthesised here.
# Music: 104 BPM bouncy pluck/marimba groove in F major, claps and a round bass; drops out on "fail".
# Output: mix.wav (48 kHz stereo)
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]
N = int(SR * TOTAL); t = np.arange(N) / SR
rng = np.random.default_rng(5)
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

BPM = 104; beat = 60 / BPM; bar = 4 * beat
prog = [(65, 69, 72), (62, 65, 69), (58, 62, 65), (60, 64, 67)]   # F Dm Bb C
roots = [41, 38, 34, 36]
def marimba(f, dur=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) + .25 * np.sin(2 * np.pi * f * 4 * tt) * np.exp(-tt * 40)) * np.exp(-tt * 11)
def bassn(f, dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / .005) * np.exp(-tt * 4)
def kick():
    n = int(0.3 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(50 + 100 * np.exp(-tt * 35)) / SR) * np.exp(-tt * 9)
def clap():
    n = int(0.18 * SR); tt = np.arange(n) / SR; x = hp(rng.standard_normal(n), 1200) * np.exp(-tt * 25)
    for d in (0.008, 0.016): k = int(d * SR); x[k:] += x[:-k] * .6
    return x * .6
def hat():
    n = int(0.04 * SR); return hp(rng.standard_normal(n), 7000) * np.exp(-np.arange(n) / 250)
mel = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N)
pattern = [0, 2, 1, 2, 0, 1, 2, 1]
fail0, fail1 = st("fail"), st("fail") + 1.1
for b in range(int(TOTAL / bar) + 2):
    c = prog[b % 4]
    for k in range(8):
        at = b * bar + k * beat / 2
        if fail0 <= at < fail1: continue
        put(mel, marimba(mtof(c[pattern[k]] + (12 if k in (3, 7) else 0))), at, .16)
        if k % 2 == 0: put(drums, hat(), at + beat / 2, .1)
    for k in (0, 3, 4, 6):
        at = b * bar + k * beat / 2
        if fail0 <= at < fail1: continue
        put(bass, bassn(mtof(roots[b % 4]), beat * .5), at, .35)
    for k in range(4):
        at = b * bar + k * beat
        if fail0 <= at < fail1 or at < st("settings") - .05: continue
        put(drums, kick(), at, .55 if k in (0, 2) else 0)
        if k in (1, 3): put(drums, clap(), at, .35)
gate = np.ones(N); gate[: int(st("settings") * SR)] = .55
music = (mel + bass) * gate + drums
musL = music + .25 * mel; musR = music - .25 * mel

def whoosh(dur=0.3):
    n = int(dur * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    return (lp(x, 1800) * (1 - tt / dur) + hp(x, 3000) * tt / dur) * np.sin(np.pi * tt / dur) ** 2
def note_ping():   # original 2-note notification chime
    out = np.zeros(int(.5 * SR))
    for f, d in ((1568, 0), (2093, .09)):
        n = int(.4 * SR); tt = np.arange(n) / SR; i0 = int(d * SR)
        out[i0:i0 + n] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9)
    return out
def msg_pop():
    n = int(0.09 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(600 + 2600 * tt / .09) / SR) * np.exp(-tt * 30)
def tick_ding():
    n = int(.6 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1760 * tt) + .5 * np.sin(2 * np.pi * 2637 * tt)) * np.exp(-tt * 7)
def tap():
    n = int(0.012 * SR); return hp(rng.standard_normal(n), 2500) * np.exp(-np.arange(n) / 80)
def siren(dur):
    n = int(dur * SR); tt = np.arange(n) / SR; f = 750 + 300 * np.sin(2 * np.pi * 1.6 * tt)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * .4 * np.minimum(1, tt / .1) * np.minimum(1, (dur - tt) / .2)
def wahwah():
    out = []
    for m, d in ((58, .32), (57, .32), (56, .32), (55, .9)):
        n = int(d * SR); tt = np.arange(n) / SR; f = mtof(m) * (1 + .02 * np.sin(2 * np.pi * 6 * tt) * (d > .5))
        x = sum(np.sin(2 * np.pi * np.cumsum(f * h) / SR) / h for h in range(1, 7))
        wah = .5 + .5 * np.sin(np.pi * np.minimum(1, tt / d * 1.5))
        out.append((lp(x, 700) * (1 - wah) + lp(x, 2400) * wah) * np.minimum(1, tt / .02) * np.minimum(1, (d - tt) / .05))
    return np.concatenate(out) * .5
def splash():
    n = int(1.0 * SR); tt = np.arange(n) / SR
    return lp(rng.standard_normal(n), 2500) * np.exp(-tt * 4) + np.sin(2 * np.pi * np.cumsum(90 + 60 * np.exp(-tt * 20)) / SR) * np.exp(-tt * 10)
def bubbles(dur=2.5):
    x = np.zeros(int(dur * SR))
    for k in range(18):
        n = int(.06 * SR); tt = np.arange(n) / SR; f0 = rng.uniform(500, 1400)
        b = np.sin(2 * np.pi * np.cumsum(f0 + f0 * 3 * tt / .06) / SR) * np.exp(-tt * 50)
        i0 = int(rng.uniform(0, dur - .07) * SR); x[i0:i0 + n] += b
    return x
def zoom_out(dur=2.4):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-tt * 1.4) + 120) / SR) * .3 * np.sin(np.pi * tt / dur) + lp(rng.standard_normal(n), 1200) * .3 * np.sin(np.pi * tt / dur)

for (a, b, name, seg) in RD.SHOTS[1:]: sfx(whoosh(.28), .25, rng.uniform(-.4, .4), a - .08)
for at in (.25, 1.25, 2.35): sfx(note_ping(), .35, 0, at)
sfx(whoosh(.3), .25, .5, 3.25)                                   # swipe mom away
for tk in RD.TICK: sfx(tick_ding(), .32, 0, tk); sfx(tap(), .5, 0, tk)
a = st("settings")
for k in range(16): sfx(tap(), .25, rng.uniform(-.3, .3), a + .2 + k * .19)
sfx(msg_pop(), .45, -.3, st("car2") + .25)
sfx(siren(st("fail") - st("cops") + .2), .22, 0, st("cops"))
sfx(wahwah(), .55, 0, st("fail") + .2)
sfx(splash(), .55, 0, st("water")); sfx(bubbles(), .18, 0, st("water") + .2)
sfx(zoom_out(), .35, 0, st("map"))
a = st("outro")
for j in range(6): sfx(msg_pop(), .3, (j - 2.5) / 3, a + 1.0 + j * .09)
sfx(note_ping(), .35, 0, RD.LOOP + .05)

v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + 0.25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * 0.9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
envv = lfilter([1 - 0.9993], [1, -0.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([0.002], [1, -0.998], act) * 1.4, 0, 1)
mg = (1 - 0.75 * duck) * 0.6
outL = musL * mg + SL * (1 - 0.3 * duck) + voice
outR = musR * mg + SR_ * (1 - 0.3 * duck) + voice
fade = np.clip((TOTAL - t) / 0.3, 0, 1) * np.clip(t / 0.01, 0, 1)
stt = np.stack([outL, outR], 1) * fade[:, None]
stt = np.tanh(stt * 1.2) / np.tanh(1.2); stt /= np.abs(stt).max() / 0.95
sf.write(os.path.join(HERE, "mix.wav"), stt.astype(np.float32), SR, subtype="PCM_24")
print("mix ok", round(N / SR, 2))
