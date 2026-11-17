# Original synthwave music + sound design + voice mix with side-chain ducking.
# Everything is synthesised here (no third-party samples) -> no licensing issues.
# Output: mix.wav (48 kHz stereo)
import os, sys, json, wave
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

SR = 48000
TM = json.load(open(os.path.join(HERE, "timings.json")))
TOTAL = TM["total"]; SEGT = {s["id"]: s for s in TM["segments"]}
N = int(SR * TOTAL); t = np.arange(N) / SR
rng = np.random.default_rng(11)
L = np.zeros(N); R = np.zeros(N)

def add(x, g=1.0, pan=0.0, at=0.0):
    i0 = int(at * SR)
    if i0 >= N: return
    x = x[: N - i0]
    L[i0:i0 + len(x)] += x * g * (1 - pan) ** 0.5 * 1.0
    R[i0:i0 + len(x)] += x * g * (1 + pan) ** 0.5 * 1.0

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)
def env(n, a=0.003, d=0.2):
    tt = np.arange(n) / SR; return np.minimum(1, tt / a) * np.exp(-tt / d)
def saw(f, n, ph=0.0):
    tt = np.arange(n) / SR; return 2 * ((f * tt + ph) % 1) - 1

def word_t(seg, w):
    for x in SEGT[seg]["words"]:
        if "".join(c for c in x["w"].lower() if c.isalnum()) == w: return x["a"]
    raise KeyError(w)

# ------------------------------------------------------------ music: 118 BPM synthwave
BPM = 118; beat = 60 / BPM; bar = 4 * beat
num_starts = [SEGT[s]["a"] for s in ("n5", "n4", "n3", "n2", "n1")]
drop = SEGT["n5"]["a"] - 0.06      # full beat kicks in at secret #5
# intensity: intro filtered, drops at each number, break before #1
def intensity(x):
    if x < drop: return 0.45
    if SEGT["n1"]["a"] - 0.06 <= x < SEGT["f1"]["a"]: return 0.25  # suspense break
    return 1.0
I = np.array([intensity(x) for x in np.arange(0, TOTAL, 0.01)])
I = np.interp(t, np.arange(len(I)) * 0.01, I)
I = lfilter([0.0005], [1, -0.9995], I) / 1.0  # smooth (~40 ms)

# chords: Am - F - C - G (i - VI - III - VII)
prog = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
roots = [45, 41, 48, 43]
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
music = np.zeros(N); musicS = np.zeros(N)
nbars = int(TOTAL / bar) + 2
# pad (detuned saws, lowpassed)
for b in range(nbars):
    c = prog[b % 4]; a0 = int(b * bar * SR); n = int(bar * SR)
    if a0 >= N: break
    seg = np.zeros(n)
    for m in c:
        for det in (-0.08, 0.0, 0.09):
            seg += saw(mtof(m + 12) * (1 + det / 100 * 10), n, rng.random())
    e = np.minimum(1, np.arange(n) / (0.08 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.05 * SR))
    seg = lp(seg * e, 2200) * 0.05
    k = min(n, N - a0); musicS[a0:a0 + k] += seg[:k]
# bass: 8th-note pumping octaves
for b in range(nbars):
    for k8 in range(8):
        at = b * bar + k8 * beat / 2
        if at >= TOTAL: break
        m = roots[b % 4] - 12 + (12 if k8 % 2 else 0)
        n = int(beat / 2 * SR * 0.9)
        x = lp(saw(mtof(m), n) + 0.5 * saw(mtof(m) * 1.005, n), 900) * env(n, 0.004, 0.18)
        i0 = int(at * SR); kk = min(n, N - i0); music[i0:i0 + kk] += x[:kk] * 0.22
# arpeggio (16ths) — only after the drop
for b in range(nbars):
    c = prog[b % 4]
    for k16 in range(16):
        at = b * bar + k16 * beat / 4
        if at >= TOTAL: break
        m = c[[0, 1, 2, 1][k16 % 4]] + 24
        n = int(beat / 4 * SR)
        tt = np.arange(n) / SR
        x = np.sign(np.sin(2 * np.pi * mtof(m) * tt)) * 0.5 + saw(mtof(m) * 1.003, n) * 0.5
        x = lp(x, 3500) * env(n, 0.002, 0.07)
        i0 = int(at * SR); kk = min(n, N - i0)
        g = 0.035 if at >= drop else 0.0
        musicS[i0:i0 + kk] += x[:kk] * g
# drums
def kick():
    n = int(0.35 * SR); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(45 + 110 * np.exp(-tt * 28)) / SR
    return np.sin(ph) * np.exp(-tt * 7) + 0.3 * rng.standard_normal(n) * np.exp(-tt * 200)
def snare():
    n = int(0.3 * SR); tt = np.arange(n) / SR
    return hp(rng.standard_normal(n), 1500) * np.exp(-tt * 14) * 0.7 + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 25) * 0.5
def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR); tt = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-tt * (18 if open_ else 80))
K, S_, Hc, Ho = kick(), snare(), hat(), hat(True)
drums = np.zeros(N)
def put(buf, x, at, g):
    i0 = int(at * SR)
    if 0 <= i0 < N: k = min(len(x), N - i0); buf[i0:i0 + k] += x[:k] * g
nb = 0; at = 0.0
while at < TOTAL:
    full = at >= drop and intensity(at) > 0.5
    if full or at < drop and int(at / beat) % 2 == 0 and at > 0.3:
        put(drums, K, at, 0.9 if full else 0.5)
    if full and nb % 4 in (1, 3): put(drums, S_, at, 0.55)
    if full:
        put(drums, Hc, at + beat / 2, 0.18); put(drums, Hc, at + beat / 4, 0.08); put(drums, Hc, at + 3 * beat / 4, 0.08)
    at += beat; nb += 1
# sidechain pump from kicks on the pad/bass
pump = np.ones(N)
at = drop
while at < TOTAL:
    i0 = int(at * SR); n = int(beat * SR); k = min(n, N - i0)
    pump[i0:i0 + k] = 0.45 + 0.55 * np.minimum(1, np.arange(k) / (0.18 * SR)); at += beat
# intro filter sweep (muffled -> open at the drop)
mus = (music + musicS) * pump
pre = int(drop * SR)
mus[:pre] = lp(mus[:pre], 700, 2) * 1.6
mus = mus * (0.55 + 0.45 * I)
drums = drums * np.where(t < drop, 0.6, 1.0)
mL = mus + drums; mR = mus + drums
# stereo width for pad/arp
mL += musicS * pump * 0.3; mR -= musicS * pump * 0.3
add_music_L, add_music_R = mL, mR

# ------------------------------------------------------------ SFX
def whoosh(dur=0.35, up=True):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    e = np.sin(np.pi * tt / dur) ** 2
    lo = lp(x, 1200); hi = hp(x, 2500)
    mix = lo * (1 - tt / dur if up else tt / dur)[...] + hi * (tt / dur if up else 1 - tt / dur)
    return mix * e
def boom(dur=1.8):
    n = int(dur * SR); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(30 + 90 * np.exp(-tt * 9)) / SR
    return np.sin(ph) * np.exp(-tt * 2.5) + lp(rng.standard_normal(n), 400) * np.exp(-tt * 6) * 0.8
def riser(dur=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n); out = np.zeros(n)
    for k in range(10):
        a, b = int(k * n / 10), int((k + 1) * n / 10)
        out[a:b] = hp(x[a:b], 300 + 5000 * (k / 10) ** 2)
    sweep = np.sin(2 * np.pi * np.cumsum(200 + 1400 * (tt / dur) ** 2) / SR) * 0.3
    return (out * 0.6 + sweep) * (tt / dur) ** 2
def glitch(dur=0.25):
    n = int(dur * SR); x = np.zeros(n)
    for k in range(0, n, int(0.02 * SR)):
        if rng.random() < 0.7:
            m = int(0.015 * SR); f = rng.uniform(200, 3000)
            x[k:k + m] = np.sign(np.sin(2 * np.pi * f * np.arange(min(m, n - k)) / SR)) * rng.uniform(0.3, 1)
    return x * 0.5
def ding(f=1320, dur=0.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.01 * tt)) * np.exp(-tt * 8)
def click():
    n = int(0.012 * SR); return hp(rng.standard_normal(n), 3000) * np.exp(-np.arange(n) / 80)
def cash():
    x = np.concatenate([ding(2600, 0.15) * 0.6, ding(3300, 0.6)])
    n = int(0.15 * SR); x[:n] += hp(rng.standard_normal(n), 4000) * np.exp(-np.arange(n) / 900) * 0.6
    return x
def thud():
    n = int(0.6 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(60 + 80 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9) + lp(rng.standard_normal(n), 900) * np.exp(-tt * 30)
def stamp_sfx():
    return thud() * 0.8 + np.concatenate([np.zeros(200), hp(rng.standard_normal(int(0.08 * SR)), 1500) * np.exp(-np.arange(int(0.08 * SR)) / 600)])[: int(0.6 * SR)] if False else thud()
def pop():
    n = int(0.08 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(900 - 6000 * tt) / SR) * np.exp(-tt * 50)

sys.argv = [sys.argv[0], "none"]
import render as RD   # reuse the exact shot timeline
for (a, b, name, seg) in RD.SHOTS[1:]:
    add(whoosh(0.32), 0.22, rng.uniform(-0.6, 0.6), a - 0.16)
for ns in num_starts:
    add(riser(0.9), 0.20, 0, ns - 0.95)
    add(boom(), 0.75, 0, ns - 0.06)
add(boom(), 0.55, 0, 0.0)                       # cold open impact
add(glitch(0.3), 0.18, 0, 0.0)
# shot specific sound design
def shot_t(name):
    for s in RD.SHOTS:
        if s[2] == name: return s[0], s[1]
a, b = shot_t("hook_five")
for k in range(5): add(pop(), 0.35, (k - 2) / 3, a + k * 0.1)
a, b = shot_t("film_strip")
for k in range(int((b - a) / 0.09)): add(click(), 0.12, 0.3, a + k * 0.09)
add(thud(), 0.5, 0, a + 0.9)
a, b = shot_t("split_half"); add(pop(), 0.4, -0.5, a); add(pop(), 0.4, 0.5, a + 0.25)
a, b = shot_t("leak_alert")
add(glitch(0.4), 0.25, 0, a); add(thud(), 0.6, 0, a + 0.15)
for k in range(3): add(ding(880, 0.25) * np.sign(np.sin(np.arange(int(0.25 * SR)) * 0.06)), 0.07, 0, a + 0.3 + k * 0.35)
add(whoosh(0.4), 0.3, 0.4, a + 0.95)
a, b = shot_t("views_counter")
for k in range(int(min(1.6, b - a) / 0.05)): add(click(), 0.10, rng.uniform(-.4, .4), a + k * 0.05)
add(ding(1760), 0.3, 0, a + 1.6)
a, b = shot_t("trophy"); add(ding(1320, 1.2), 0.25, -0.3, a); add(ding(1980, 1.2), 0.2, 0.3, a + 0.08)
a, b = shot_t("florida_map")
for k in range(5): add(pop(), 0.35, rng.uniform(-.5, .5), a + 0.5 + k * 0.18)
a, b = shot_t("phone_feed")
for k in range(4): add(ding(2093, 0.25), 0.10, 0.4, a + 0.2 + k * 0.4)
add(thud(), 0.5, 0, a + 0.7)
a, b = shot_t("hammers")
for hh in (0.35, 0.75, 1.15, 1.55):
    if a + hh < b:
        n = int(0.25 * SR); add(hp(rng.standard_normal(n), 2500) * np.exp(-np.arange(n) / 1500) + thud()[:n] * 0.6, 0.35, rng.uniform(-.5, .5), a + hh)
a, b = shot_t("box_open"); add(thud(), 0.6, 0, a + 0.7); add(ding(220, 0.4) * 0.5, 0.2, 0, a + 0.45)
a, b = shot_t("code_card")
for k in range(19): add(click(), 0.2, 0.2, a + k * 1.0 / 19)
add(ding(1568, 0.5), 0.25, 0, a + 1.0)
a, b = shot_t("hacker_terminal")
for k in range(int((b - a) / 0.07)): add(click(), 0.15 * rng.uniform(0.5, 1), rng.uniform(-.3, .3), a + k * 0.07 + rng.uniform(0, 0.03))
add(glitch(0.3), 0.2, 0, a); add(thud(), 0.5, 0, a + 0.9)
a, b = shot_t("clips_grid")
for k in range(int(min(1.4, b - a) / 0.06)): add(pop() * 0.5, 0.12, rng.uniform(-.6, .6), a + k * 0.06)
a, b = shot_t("hotel_tv"); add(thud(), 0.45, 0.3, a + 0.8)
a, b = shot_t("firestick"); add(whoosh(0.5, True), 0.3, 0, a + 0.4); add(ding(1046, 0.4), 0.15, 0, a + 0.9)
a, b = shot_t("money"); add(cash(), 0.35, 0, a + 1.3)
for k in range(int(min(1.3, b - a) / 0.05)): add(click(), 0.08, rng.uniform(-.4, .4), a + k * 0.05)
gt = word_t("f1", "guilty")
a, b = shot_t("gavel")
add(thud(), 1.0, 0, a + 0.45); add(boom(1.2), 0.6, 0, gt - 0.08); add(thud(), 0.7, 0, gt - 0.08)
a, b = shot_t("release_date"); add(ding(1320, 1.0), 0.2, 0, a + 0.1)
a, b = shot_t("comments")
for k in range(5): add(pop(), 0.3, (k - 2) / 3, a + k * 0.12)

sfxL, sfxR = L.copy(), R.copy()

# ------------------------------------------------------------ voice + ducking
v, vsr = sf.read(os.path.join(HERE, "voice.wav"))
v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
# light voice chain: HPF, presence lift, compression-ish, normalise
voice = hp(voice, 90)
voice = voice + 0.25 * hp(voice, 3000)
pk = np.max(np.abs(voice)); voice = voice / pk * 0.9
voice = np.tanh(voice * 1.8) / np.tanh(1.8)
# envelope follower for ducking
envv = np.abs(voice)
envv = lfilter([1 - 0.9993], [1, -0.9993], envv)
envv = np.maximum.accumulate(np.zeros(1)) if False else envv
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
# smooth attack/release
duck = lfilter([0.002], [1, -0.998], act)
duck = np.clip(duck * 1.4, 0, 1)
music_gain = 1.0 - 0.72 * duck        # about -11 dB under the voice

mL, mR = add_music_L * music_gain * 0.55, add_music_R * music_gain * 0.55
sL, sR = sfxL * (1 - 0.35 * duck), sfxR * (1 - 0.35 * duck)
outL = mL + sL + voice * 1.0
outR = mR + sR + voice * 1.0
# master fade + soft limit
fade = np.clip((TOTAL - t) / 0.6, 0, 1) * np.clip(t / 0.01, 0, 1)
st = np.stack([outL, outR], 1) * fade[:, None]
st = np.tanh(st * 1.2) / np.tanh(1.2)
st /= np.abs(st).max() / 0.95
sf.write(os.path.join(HERE, "mix.wav"), st.astype(np.float32), SR, subtype="PCM_24")
print("mix ok", st.shape[0] / SR)
