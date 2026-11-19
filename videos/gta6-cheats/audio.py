# Original lo-fi doodle beat (92 BPM, Rhodes-like chords + soft kick/snap) + pencil scribbles, buzzer on every ✗,
# stamp thuds, typing, phone ring + dead tone, pops + voice with ducking. All synthesised here.
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json"))); TOTAL = TM["total"]
N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(15)
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
BPM = 92; beat = 60 / BPM; bar = 4 * beat
chords = [(57, 60, 64, 67), (53, 57, 60, 64), (55, 59, 62, 65), (52, 55, 59, 62)]
def rhodes(f, d):
    n = int(d * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt + .8 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3))) * np.exp(-tt * 1.8)
def kick(): n = int(.3 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9)
def snap(): n = int(.12 * SR); return hp(rng.standard_normal(n), 2000) * np.exp(-np.arange(n) / SR * 40) * .5
mus = np.zeros(N)
for b in range(int(TOTAL / bar) + 2):
    a0 = b * bar
    for m in chords[b % 4]: put(mus, rhodes(mtof(m), bar), a0, .06); put(mus, rhodes(mtof(m), beat * 1.5), a0 + 2.5 * beat, .04)
    put(mus, rhodes(mtof(chords[b % 4][0] - 24), bar), a0, .12)
    for k in range(4):
        if k in (0, 2): put(mus, kick(), a0 + k * beat + (.02 if k == 2 else 0), .5)
        else: put(mus, snap(), a0 + k * beat, .35)
mus = lp(mus, 5000)
def scribble(d=.5):
    n = int(d * SR); tt = np.arange(n) / SR; env = (.5 + .5 * np.sin(2 * np.pi * 9 * tt)) ** 2
    return hp(rng.standard_normal(n), 1500) * env * .3
def buzzer(d=.45): n = int(d * SR); tt = np.arange(n) / SR; return np.sign(np.sin(2 * np.pi * 140 * tt)) * .25 * np.exp(-tt * 2)
def thud(): n = int(.4 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(60 + 110 * np.exp(-tt * 35)) / SR) * np.exp(-tt * 10) + lp(rng.standard_normal(n), 1200) * np.exp(-tt * 30)
def key(): n = int(.02 * SR); return hp(rng.standard_normal(n), 2500) * np.exp(-np.arange(n) / 150)
def pop(): n = int(.08 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(900 + 6000 * tt) / SR) * np.exp(-tt * 40)
def ring(d=1.2):
    n = int(d * SR); tt = np.arange(n) / SR; on = ((tt % .4) < .25).astype(float)
    return (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * .15 * on
def dead(d=.9): n = int(d * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * 480 * tt) * np.sin(2 * np.pi * 620 * tt) * .25 * ((tt % .3) < .15)
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(scribble(.35), .5, rng.uniform(-.4, .4), a - .05)
sfx(thud(), .7, 0, .05); sfx(buzzer(), .4, 0, RD.word_time("hook", "don't"))
a = st("search")
for k in range(12): sfx(key(), .4, rng.uniform(-.3, .3), a + k / 12)
for i in range(3): sfx(pop(), .3, 0, a + .8 + i * .25)
a = st("list")
for i in range(6): sfx(scribble(.15), .4, 0, a + i * .15)
sfx(thud(), .6, 0, RD.word_time("s2", "old"))
a = st("dial"); sfx(ring(1.4), .5, .3, a + .1); sfx(dead(), .5, .3, a + 1.5); sfx(buzzer(), .45, 0, RD.word_time("s2", "nothing"))
sfx(thud(), .6, 0, RD.word_time("s3", "yet.") - .2)
sfx(thud(), .8, 0, RD.word_time("s4", "fake.") - .15); sfx(buzzer(.6), .5, 0, RD.word_time("s4", "fake.") - .1)
sfx(pop(), .4, 0, st("outro") + .1); sfx(thud(), .5, 0, RD.word_time("outro", "cheats.") - .2)
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
