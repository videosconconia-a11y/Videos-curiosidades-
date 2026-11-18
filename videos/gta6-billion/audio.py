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

BPM = 120; beat = 60 / BPM; bar = 4 * beat
q_start = shot("question")[0]; outro = shot("outro")[0]
def section(x):
    if x < shot("hook2")[0]: return 0
    if q_start <= x < shot("gta5")[0]: return 2
    return 1
# news bed in D minor: staccato string stabs, pulsing bass, ticking clock, toms
prog = [(62, 65, 69), (58, 62, 65), (60, 64, 67), (57, 61, 64)]
roots = [38, 34, 36, 33]
stabs = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N); tick = np.zeros(N); pad = np.zeros(N)
nb = int(TOTAL / bar) + 2
for b in range(nb):
    c = prog[b % 4]
    for k in range(8):
        if k in (0, 3, 6) or (k == 7 and b % 2):
            n = int(0.16 * SR); tt = np.arange(n) / SR; x = np.zeros(n)
            for m in c:
                for det in (-0.1, 0.1): x += saw(mtof(m) * (1 + det / 100), n, rng.random())
            put(stabs, lp(x, 2500) * np.exp(-tt * 18) * 0.05, b * bar + k * beat / 2)
    for k in range(8):
        n = int(beat / 2 * SR * .9); tt = np.arange(n) / SR
        put(bass, lp(saw(mtof(roots[b % 4]), n), 600) * env(n, 0.003, 0.12) * 0.22, b * bar + k * beat / 2)
    n = int(bar * SR); x = np.zeros(n)
    for m in c: x += saw(mtof(m - 12), n, rng.random())
    e_ = np.minimum(1, np.arange(n) / (0.4 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.2 * SR))
    put(pad, lp(x * e_, 700) * 0.03, b * bar)
def kick():
    n = int(0.35 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 7)
def tom(f=110):
    n = int(0.3 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(f * (1 + .6 * np.exp(-tt * 20))) / SR) * np.exp(-tt * 9)
def clk():
    n = int(0.015 * SR); return hp(rng.standard_normal(n), 4000) * np.exp(-np.arange(n) / 60)
K = kick(); x = 0.0; k = 0
while x < TOTAL:
    sec = section(x)
    if sec == 1:
        put(drums, K, x, 0.8)
        if k % 4 == 3: put(drums, tom(130), x + beat / 2, 0.35)
        for j in range(4): put(tick, clk(), x + j * beat / 4, 0.12 if j % 2 == 0 else 0.06)
    elif sec == 0:
        for j in range(2): put(tick, clk(), x + j * beat / 2, 0.1)
    else:
        put(tick, clk(), x, 0.12)
    x += beat; k += 1
sect = np.array([section(v) for v in np.arange(0, TOTAL, 0.01)])
S = np.interp(t, np.arange(len(sect)) * 0.01, sect)
smooth = lambda g: lfilter([0.0008], [1, -0.9992], g)
g_main = smooth(np.interp(S, [0, 1, 2], [0.5, 1.0, 0.35]))
music = (stabs + bass) * g_main + pad + drums + tick
musL = music + 0.3 * stabs * g_main; musR = music - 0.3 * stabs * g_main

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

def news_sting():
    n = int(1.6 * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for m, dl in ((62, 0), (69, .0), (74, .0), (81, 0.12)):
        i0 = int(dl * SR); nn = n - i0; ttt = np.arange(nn) / SR
        x[i0:] += (saw(mtof(m), nn) * .6 + np.sin(2 * np.pi * mtof(m) * ttt)) * np.exp(-ttt * 2.2)
    return lp(x, 4000) * 0.35 + boom(1.6)[:n] * 0.8
def register():
    x = np.concatenate([ding(2600, 0.12) * 0.6, ding(3300, 0.7)])
    n = int(0.12 * SR); x[:n] += hp(rng.standard_normal(n), 4000) * np.exp(-np.arange(n) / 900) * 0.5
    return x
def ding(f=1320, dur=0.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.01 * tt)) * np.exp(-tt * 8)
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(whoosh(0.3), 0.22, rng.uniform(-.4, .4), a - 0.12)
sfx(news_sting(), 0.45, 0, 0.0); sfx(glitch(0.2), 0.1, 0, 0.0)
a, b = shot("hook"); sfx(thud(), 0.5, 0, a + 0.9)
a, b = shot("hook2")
for k in range(24): sfx(click(), 0.12, 0, a + k * 0.05)
sfx(register(), 0.35, 0, a + 1.2)
a, b = shot("source"); sfx(ping(1568, 0.6), 0.12, 0, a + 0.2)
a, b = shot("preorders")
for k in range(36): sfx(click(), 0.11, rng.uniform(-.3, .3), a + k * 0.05)
sfx(beep(2000, 0.08), 0.1, 0, a + 1.8)
a, b = shot("dollars")
for k in range(32): sfx(click(), 0.11, rng.uniform(-.3, .3), a + k * 0.05)
sfx(register(), 0.5, 0, a + 1.6); sfx(thud(), 0.6, 0, a + 1.6)
a, b = shot("nobody"); sfx(thud(), 0.7, 0, a + 0.05); sfx(boom(1.2), 0.5, 0, a + 0.05)
a, b = shot("ps5"); sfx(riser(1.0), 0.15, 0, a); sfx(ping(1320, 0.6), 0.12, 0, a + 1.0)
a, b = shot("unconfirmed"); sfx(thud(), 0.8, 0, a + 0.1); sfx(thud(), 0.7, 0, a + 0.45); sfx(glitch(0.3), 0.12, 0, a + 0.1)
a, b = shot("taketwo"); sfx(whoosh(0.5), 0.3, 0, a); sfx(beep(1800, 0.06), 0.08, 0, a + 0.4)
a, b = shot("question"); sfx(riser(0.8), 0.18, 0, a - 0.8); sfx(boom(), 0.7, 0, a); sfx(thud(), 0.6, 0, a + 0.3)
a, b = shot("gta5"); sfx(riser(0.9), 0.12, 0, a)
a, b = shot("record"); sfx(boom(1.6), 0.4, 0, a); sfx(thud(), 0.6, 0, a + 0.6)
a, b = shot("outro"); sfx(news_sting(), 0.5, 0, a)
for k in range(3): sfx(pop(), 0.3, (k - 1) / 2, a + 0.3 + k * 0.15)

# --- voice + ducking
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + 0.25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * 0.9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
envv = lfilter([1 - 0.9993], [1, -0.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([0.002], [1, -0.998], act) * 1.4, 0, 1)
mg = (1 - 0.8 * duck) * 0.55
outL = musL * mg + SL * (1 - 0.35 * duck) + voice
outR = musR * mg + SR_ * (1 - 0.35 * duck) + voice
fade = np.clip((TOTAL - t) / 0.6, 0, 1) * np.clip(t / 0.01, 0, 1)
st = np.stack([outL, outR], 1) * fade[:, None]
st = np.tanh(st * 1.2) / np.tanh(1.2); st /= np.abs(st).max() / 0.95
sf.write(os.path.join(HERE, "mix.wav"), st.astype(np.float32), SR, subtype="PCM_24")
print("mix ok", round(N / SR, 2))
