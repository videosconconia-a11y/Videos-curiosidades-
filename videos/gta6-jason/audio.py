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

BPM = 92; beat = 60 / BPM; bar = 4 * beat
drop = shot("f1_title")[0]                 # pulse enters on fact 01
brk0, brk1 = shot("f5_title")[0], shot("f5_duo")[0]
lift = shot("f4_harder")[0]
outro = shot("outro")[0]
def section(x):
    if x < drop: return 0
    if brk0 <= x < brk1: return 2
    if x >= outro: return 3
    return 1
# documentary bed in A minor: Am - F - C - G(sus)
prog = [(57, 60, 64), (53, 57, 60), (48, 55, 60), (55, 59, 62)]
roots = [45, 41, 48, 43]
pad = np.zeros(N); pl = np.zeros(N); sub = np.zeros(N); drums = np.zeros(N); tick = np.zeros(N)
nb = int(TOTAL / bar) + 2
for b in range(nb):                       # strings pad: slow-attack filtered saws
    a0 = b * bar; n = int(bar * SR); x = np.zeros(n)
    for m in prog[b % 4]:
        for det in (-0.15, 0.0, 0.14): x += saw(mtof(m - 12) * (1 + det / 100), n, rng.random())
    e_ = np.minimum(1, np.arange(n) / (0.6 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.2 * SR))
    put(pad, lp(x * e_, 900) * 0.05, a0)
    f0 = mtof(roots[b % 4] - 12); tt = np.arange(n) / SR
    put(sub, np.sin(2 * np.pi * f0 * tt) * e_ * 0.18, a0)
pat = [0, 2, 1, 2, 0, 2, 1, 3]            # piano-like pluck ostinato (8ths)
for b in range(nb):
    c = prog[b % 4] + (prog[b % 4][0] + 12,)
    for k in range(8):
        m = c[pat[k]] + 12; n = int(beat * 0.9 * SR); tt = np.arange(n) / SR; f = mtof(m)
        x = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.12 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt * 5.5) * np.minimum(1, tt / 0.003)
        put(pl, x * 0.07, b * bar + k * beat / 2)
def kick():
    n = int(0.45 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(42 + 90 * np.exp(-tt * 25)) / SR) * np.exp(-tt * 5.5)
def rim():
    n = int(0.06 * SR); tt = np.arange(n) / SR
    return (hp(rng.standard_normal(n), 2500) * 0.6 + np.sin(2 * np.pi * 1700 * tt)) * np.exp(-tt * 70)
K, RIM = kick(), rim()
x = 0.0; k = 0
while x < TOTAL:
    sec = section(x)
    if sec in (1, 3):
        if k % 2 == 0: put(drums, K, x, 0.85)
        if k % 4 == 3: put(drums, RIM, x, 0.35)
        for j in range(4): put(tick, rim()[: int(0.02 * SR)], x + j * beat / 4, 0.06 if j else 0.1)
    elif sec == 0:
        for j in range(2): put(tick, rim()[: int(0.02 * SR)], x + j * beat / 2, 0.05)
    x += beat; k += 1
sect = np.array([section(v) for v in np.arange(0, TOTAL, 0.01)])
S = np.interp(t, np.arange(len(sect)) * 0.01, sect)
smooth = lambda g: lfilter([0.0008], [1, -0.9992], g)
g_pl = smooth(np.interp(S, [0, 1, 2, 3], [0.6, 1.0, 0.3, 1.0]))
g_sub = smooth(np.interp(S, [0, 1, 2, 3], [0.5, 1.0, 1.2, 1.0]))
music = pad + sub * g_sub + pl * g_pl + drums + tick
music = music * smooth(np.where(t >= lift, 1.12, 1.0))
musL = music + 0.35 * pl * g_pl; musR = music - 0.35 * pl * g_pl

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
def shutter():
    n = int(0.12 * SR); x = np.zeros(n)
    for at in (0.0, 0.05):
        i0 = int(at * SR); m = int(0.03 * SR); x[i0:i0 + m] += hp(rng.standard_normal(m), 3000) * np.exp(-np.arange(m) / 200)
    return x
def typer(n_chars, dur):
    out = np.zeros(int((dur + 0.1) * SR))
    for j in range(n_chars):
        i0 = int(j * dur / max(1, n_chars) * SR); m = int(0.012 * SR)
        if i0 + m < len(out): out[i0:i0 + m] += hp(rng.standard_normal(m), 3500) * np.exp(-np.arange(m) / 60) * rng.uniform(.5, 1)
    return out
for (a, b, name, seg) in RD.SHOTS[1:]: sfx(whoosh(0.28), 0.18, rng.uniform(-.4, .4), a - 0.1)
sfx(boom(), 0.55, 0, 0.0); sfx(typer(18, 0.9), 0.2, 0, 0.1)
for n in range(1, 6):
    a, b = shot(f"f{n}_title"); sfx(riser(0.6), 0.12, 0, a - 0.62); sfx(boom(1.4), 0.6, 0, a); sfx(typer(16, 0.7), 0.18, 0, a + 0.15)
for nm in ("hook2", "f3_back", "f1_crooks", "f1_world", "f2_army", "f2_shirt", "f3_map", "f3_brian", "f3_house", "f4_split", "f5_duo", "f5_split", "f5_tell"):
    a, b = shot(nm); sfx(shutter(), 0.35, rng.uniform(-.3, .3), a + 0.05)
a, b = shot("f1_world"); sfx(shutter(), 0.3, .3, a + 0.3)
a, b = shot("f2_shirt"); sfx(riser(1.0), 0.1, 0, a + 0.1); sfx(thud(), 0.5, 0, a + 1.05); sfx(beep(1800, 0.06), 0.08, 0, a + 1.1)
a, b = shot("f3_map")
for k in range(16): sfx(pop() * 0.6, 0.12, -0.6 + k * 0.08, a + 0.3 + k * 0.075)
a, b = shot("f3_brian"); sfx(thud(), 0.4, 0, a + 0.4)
a, b = shot("f3_house"); sfx(thud(), 0.6, 0, a + 0.2); sfx(typer(30, 0.8), 0.15, 0, a + 0.9)
a, b = shot("f4_split"); sfx(shutter(), 0.35, .3, a + 0.95); sfx(glitch(0.2), 0.12, 0, a + 0.95)
a, b = shot("f4_harder"); sfx(boom(2.0), 0.8, 0, a + 0.8); sfx(thud(), 0.6, 0, a + 0.8)
a, b = shot("f5_split"); sfx(ping(1320, 0.8), 0.12, -.3, a + 0.2); sfx(thud(), 0.5, .3, a + 0.75)
a, b = shot("f5_tell"); sfx(thud(), 0.5, 0, a + 0.3); sfx(sweep_sonar(1.2), 0.08, 0, a + 0.3)
a, b = shot("outro"); sfx(boom(1.8), 0.5, 0, a); sfx(typer(22, 1.0), 0.15, 0, a + 0.1)

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
