# Original "investigation" score + sound design + voice with side-chain ducking. All synthesised here.
# Music: 96 BPM dark trap/synth pulse in D minor — tense intro, groove from the map reveal, a breakdown
# before "Here's the problem", full drop on the punchline. Output: mix.wav (48 kHz stereo)
import os, sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
N = int(SR * TOTAL); t = np.arange(N) / SR
rng = np.random.default_rng(21)
SL, SR_ = np.zeros(N), np.zeros(N)

def lp(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
def env(n, a=0.003, d=0.2): tt = np.arange(n) / SR; return np.minimum(1, tt / a) * np.exp(-tt / d)
def saw(f, n, ph=0.0): tt = np.arange(n) / SR; return 2 * ((f * tt + ph) % 1) - 1
def put(buf, x, at, g=1.0):
    i0 = int(at * SR)
    if i0 < 0: x = x[-i0:]; i0 = 0
    if i0 >= N: return
    k = min(len(x), N - i0); buf[i0:i0 + k] += x[:k] * g
def sfx(x, g=1.0, pan=0.0, at=0.0):
    put(SL, x, at, g * (1 - pan) ** .5); put(SR_, x, at, g * (1 + pan) ** .5)
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)

sys.argv = [sys.argv[0], "none"]
import render as RD
def shot(name):
    for s in RD.SHOTS:
        if s[2] == name: return s[0], s[1]

BPM = 100; beat = 60 / BPM; bar = 4 * beat
groove_in = shot("n1")[0]
brk0, brk1 = shot("n5")[0], shot("her_name")[0]               # breakdown before the big reveal
drop = shot("her_name")[0]
outro = shot("question")[0]

def section(x):
    if x < groove_in: return 0     # tense intro (no snare)
    if brk0 <= x < brk1: return 2  # breakdown
    if x >= drop and x < outro: return 3  # drop
    return 1

# --- pads: Dm - Bb - F - C (dark), long detuned saws
prog = [(62, 65, 69), (58, 62, 65), (57, 60, 65), (55, 60, 64)]
roots = [38, 34, 41, 36]
pad = np.zeros(N); bass = np.zeros(N); lead = np.zeros(N); drums = np.zeros(N)
nb = int(TOTAL / bar) + 2
for b in range(nb):
    a0 = b * bar; n = int(bar * SR); x = np.zeros(n)
    for m in prog[b % 4]:
        for det in (-0.12, 0, 0.11): x += saw(mtof(m) * (1 + det / 100), n, rng.random())
    e = np.minimum(1, np.arange(n) / (0.3 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.1 * SR))
    put(pad, lp(x * e, 1400) * 0.045, a0)
# 808-style bass on 1 and the "and" of 2
def b808(f, dur=0.7):
    n = int(dur * SR); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.8 * np.exp(-tt * 40))) / SR
    return np.tanh(np.sin(ph) * 2.2) * np.exp(-tt * 2.6)
for b in range(nb):
    f = mtof(roots[b % 4])
    for off in (0, 1.5 * beat, 2.5 * beat):
        put(bass, b808(f), b * bar + off, 0.5)
# plucky arp (investigation "ticking") 8ths
for b in range(nb):
    c = prog[b % 4]
    for k in range(8):
        m = c[[0, 2, 1, 2, 0, 2, 1, 2][k]] + 12
        n = int(beat / 2 * SR); tt = np.arange(n) / SR
        x = (np.sin(2 * np.pi * mtof(m) * tt) + 0.4 * np.sin(4 * np.pi * mtof(m) * tt)) * env(n, 0.002, 0.09)
        put(lead, x * 0.05, b * bar + k * beat / 2)
# drums
def kick():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(45 + 120 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 6) + .25 * rng.standard_normal(n) * np.exp(-tt * 250)
def snare():
    n = int(0.3 * SR); tt = np.arange(n) / SR
    return hp(rng.standard_normal(n), 1800) * np.exp(-tt * 15) * .8 + np.sin(2 * np.pi * 200 * tt) * np.exp(-tt * 30) * .4
def hat():
    n = int(0.04 * SR); return hp(rng.standard_normal(n), 8000) * np.exp(-np.arange(n) / (0.008 * SR))
K, S_, HT = kick(), snare(), hat()
x = 0.0; k = 0
while x < TOTAL:
    sec = section(x)
    if sec in (1, 3):
        if k % 4 == 0 or (k % 8 == 6): put(drums, K, x, 0.9)
        if k % 4 == 2: put(drums, S_, x, 0.6)
        for j in range(4 if sec == 3 else 2): put(drums, HT, x + j * beat / (4 if sec == 3 else 2), 0.12)
    elif sec == 0:
        if k % 4 == 0: put(drums, K, x, 0.55)
        put(drums, HT, x + beat / 2, 0.06)
    x += beat; k += 1
sect = np.array([section(v) for v in np.arange(0, TOTAL, 0.01)])
S = np.interp(t, np.arange(len(sect)) * 0.01, sect)
g_pad = np.interp(S, [0, 1, 2, 3], [0.8, 0.8, 1.0, 1.0])
g_bass = np.interp(S, [0, 1, 2, 3], [0.6, 1.0, 0.0, 1.15])
g_lead = np.interp(S, [0, 1, 2, 3], [0.7, 1.0, 0.0, 1.0])
smooth = lambda g: lfilter([0.0008], [1, -0.9992], g)
music = pad * smooth(g_pad) + bass * smooth(g_bass) + lead * smooth(g_lead) + drums
# intro low-pass (muffled) opening up at the groove
pre = int(groove_in * SR); music[:pre] = lp(music[:pre], 900) * 1.3
musL = music + 0.3 * lead * smooth(g_lead); musR = music - 0.3 * lead * smooth(g_lead)

# --- SFX library
def whoosh(dur=0.32):
    n = int(dur * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n)
    return (lp(x, 1500) * (1 - tt / dur) + hp(x, 3000) * tt / dur) * np.sin(np.pi * tt / dur) ** 2
def boom(dur=1.8):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(28 + 80 * np.exp(-tt * 8)) / SR) * np.exp(-tt * 2.4) + lp(rng.standard_normal(n), 300) * np.exp(-tt * 5) * .7
def riser(dur=1.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(150 + 1500 * (tt / dur) ** 2) / SR) * (tt / dur) ** 2 * .4 + hp(rng.standard_normal(n), 2000) * (tt / dur) ** 3 * .4
def ping(f=1760, dur=0.9):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5)
    return x + 0.35 * np.concatenate([np.zeros(int(0.18 * SR)), x[: n - int(0.18 * SR)]])  # echo
def beep(f=2000, dur=0.06):
    n = int(dur * SR); return np.sin(2 * np.pi * f * np.arange(n) / SR) * np.minimum(1, (n - np.arange(n)) / 200)
def click():
    n = int(0.01 * SR); return hp(rng.standard_normal(n), 3000) * np.exp(-np.arange(n) / 70)
def pop():
    n = int(0.08 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(1000 - 7000 * tt) / SR) * np.exp(-tt * 45)
def thud():
    n = int(0.6 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9) + lp(rng.standard_normal(n), 900) * np.exp(-tt * 30)
def alarm(dur=1.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * (700 + 250 * (np.sin(2 * np.pi * 3 * tt) > 0)) * tt)) * 0.25 * np.exp(-tt * 1.2)
def glitch(dur=0.3):
    n = int(dur * SR); x = np.zeros(n)
    for k in range(0, n, int(0.02 * SR)):
        if rng.random() < .7:
            m = min(int(0.015 * SR), n - k); x[k:k + m] = np.sign(np.sin(2 * np.pi * rng.uniform(200, 3000) * np.arange(m) / SR)) * rng.uniform(.3, 1)
    return x * .5
def sweep_sonar(dur=1.6):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 1200 * tt) * np.exp(-tt * 3) * (1 + 0.5 * np.sin(2 * np.pi * 9 * tt))

def gun_cock():
    n = int(0.45 * SR); x = np.zeros(n)
    for at, f, g in [(0.0, 2600, 1.0), (0.18, 1800, 0.8)]:
        i0 = int(at * SR); m = int(0.05 * SR); tt = np.arange(m) / SR
        x[i0:i0 + m] += (hp(rng.standard_normal(m), 1500) * np.exp(-tt * 120) + np.sin(2 * np.pi * f * tt) * np.exp(-tt * 90) * 0.5) * g
    return x
def shot_sfx():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    return (lp(rng.standard_normal(n), 3000) * np.exp(-tt * 22) * 0.9 + np.sin(2 * np.pi * np.cumsum(60 + 120 * np.exp(-tt * 40)) / SR) * np.exp(-tt * 12))
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(whoosh(), 0.2, rng.uniform(-.5, .5), a - 0.15)
sfx(boom(), 0.7, 0, 0.0); sfx(glitch(), 0.15, 0, 0.0)
a, b = shot("hook_five"); sfx(thud(), 0.6, 0, a + 0.05); sfx(thud(), 0.5, 0, a + 0.3)
for n in range(1, 6):
    a, b = shot(f"n{n}"); sfx(riser(0.7), 0.15, 0, a - 0.75); sfx(boom(), 0.7, 0, a)
a, b = shot("father"); sfx(ping(1320, 0.7), 0.12, 0, a + 0.2)
a, b = shot("punch")
for k in range(3):
    n_ = int(0.25 * SR); sfx(lp(rng.standard_normal(n_), 1200) * np.exp(-np.arange(n_) / 1800) + thud()[:n_], 0.5, (-1) ** k * .3, a + 0.1 + k * 0.28)
a, b = shot("prison"); sfx(thud(), 0.6, 0, a + 0.2); sfx(thud(), 0.8, 0, a + 0.45)
n_ = int(0.5 * SR); sfx(hp(rng.standard_normal(n_), 2500) * np.exp(-np.arange(n_) / 3000) * 0.6, 0.3, 0, a + 0.85)
a, b = shot("luck"); sfx(ping(1760, 1.0), 0.15, 0, a + 0.65); sfx(thud(), 0.5, 0, a + 0.65)
a, b = shot("liberty"); sfx(thud(), 0.6, 0, a + 0.05); sfx(sweep_sonar(1.2), 0.08, 0, a)
a, b = shot("pool"); sfx(ping(1320, 0.7), 0.1, 0, a + 0.1)
a, b = shot("duo"); sfx(ping(1320, 0.7), 0.1, 0, a + 0.1)
a, b = shot("worst"); sfx(thud(), 0.5, 0, a + 0.05); sfx(boom(1.2), 0.6, 0, a + 0.45)
a, b = shot("plan"); sfx(thud(), 0.5, 0, a + 0.2)
a, b = shot("n5"); sfx(riser(b - a + 0.3), 0.25, 0, a)
a, b = shot("trailer1"); sfx(glitch(0.3), 0.15, 0, a); sfx(thud(), 0.5, 0, a + 0.3)
a, b = shot("her_name"); sfx(boom(2.2), 0.9, 0, a); sfx(glitch(0.4), 0.18, 0, a + 0.45)
for k in range(6): sfx(beep(2400, 0.04), 0.08, 0, a + 0.3 + k * 0.07)
a, b = shot("female_lead"); sfx(boom(1.6), 0.7, 0, a); sfx(thud(), 0.5, 0, a + 0.4)
a, b = shot("question"); sfx(thud(), 0.5, 0, a + 0.1); sfx(thud(), 0.4, 0, a + 0.35)

# --- voice + ducking
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + 0.25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * 0.9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
envv = lfilter([1 - 0.9993], [1, -0.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([0.002], [1, -0.998], act) * 1.4, 0, 1)
mg = (1 - 0.72 * duck) * 0.6
outL = musL * mg + SL * (1 - 0.35 * duck) + voice
outR = musR * mg + SR_ * (1 - 0.35 * duck) + voice
fade = np.clip((TOTAL - t) / 0.6, 0, 1) * np.clip(t / 0.01, 0, 1)
st = np.stack([outL, outR], 1) * fade[:, None]
st = np.tanh(st * 1.2) / np.tanh(1.2); st /= np.abs(st).max() / 0.95
sf.write(os.path.join(HERE, "mix.wav"), st.astype(np.float32), SR, subtype="PCM_24")
print("mix ok", round(N / SR, 2))
