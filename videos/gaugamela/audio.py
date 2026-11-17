"""Música épica sintetizada + efectos + voz con ducking (la música baja mientras habla la voz).
Salida: mezcla.wav (48 kHz, estéreo)."""
import json, os, sys, wave
import numpy as np
from scipy.signal import lfilter, butter, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import TIMES, TOTAL, SCENES  # noqa: E402

SR = 48000
N = int(SR * (TOTAL + 0.3))
t = np.arange(N) / SR
rng = np.random.default_rng(11)
SC = {s[2]: (a, b, v) for (a, b, v), s in zip(TIMES, SCENES)}

def lp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2)); return lfilter(b, a, x)
def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), 'high'); return lfilter(b, a, x)
def seg(a, b, fade=0.6):
    return np.clip(np.minimum((t - a) / fade, (b - t) / fade), 0, 1)

L = np.zeros(N); R = np.zeros(N)
def add(x, gain=1.0, pan=0.0, at=0.0):
    i0 = int(at * SR); n = min(len(x), N - i0)
    if n <= 0: return
    L[i0:i0 + n] += x[:n] * gain * (1 - pan); R[i0:i0 + n] += x[:n] * gain * (1 + pan)

# ------------------------------------------------------------------ intensidad de la historia (0..1)
KEYS = [(0, 0.55), (SC['macedonios'][0], 0.5), (SC['persas'][0], 0.7), (SC['carros'][0], 0.8),
        (SC['diagonal'][0], 0.35), (SC['hueco'][0], 0.5), (SC['pasillos'][0], 0.95), (SC['cuna'][0], 1.0),
        (SC['huida'][0], 0.8), (SC['final'][0], 0.25), (TOTAL, 0.15)]
inten = np.interp(t, [k[0] for k in KEYS], [k[1] for k in KEYS])

# ------------------------------------------------------------------ bordón y cuerdas (re menor)
def saw(f, ph=0): return 2 * ((t * f + ph) % 1) - 1
drone = lp(saw(36.71) + 0.6 * saw(55.0, 0.3) + 0.4 * saw(73.42, 0.6), 220)
add(drone * (0.25 + 0.35 * inten), 0.30)
CHORDS = [[146.83, 174.61, 220.0], [116.54, 146.83, 174.61], [174.61, 220.0, 261.63], [130.81, 164.81, 196.0]]
bar = 60 / 92 * 4
pad = np.zeros(N)
for k in range(int(TOTAL / bar) + 1):
    ch = CHORDS[k % 4]; a = k * bar
    env = seg(a - 0.3, a + bar + 0.3, 0.5)
    for j, f in enumerate(ch):
        pad += env * (saw(f * 1.003, j * 0.1) + saw(f * 0.997, j * 0.2 + 0.5)) * 0.5
pad = lp(pad, 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 6) ** 2)
add(pad * (0.08 + 0.12 * inten), 1.0, -0.15); add(pad * (0.08 + 0.12 * inten), 1.0, 0.15)

# ------------------------------------------------------------------ tambores de guerra
def taiko(dur=0.9, f0=95, f1=42, noise=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 18)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 5.5)
    x += lp(rng.standard_normal(n), 900) * np.exp(-tt * 30) * noise
    return x
beat = 60 / 92
PATTERN = [0, 1.5, 2, 3, 3.5]
tk = taiko(); tk2 = taiko(0.5, 160, 80, 0.5)
for k in range(int(TOTAL / beat / 4) + 1):
    for p in PATTERN:
        at = (k * 4 + p) * beat
        if at > TOTAL - 1.5: continue
        I = float(np.interp(at, t, inten))
        if I < 0.3 and p not in (0,): continue
        add(tk, 0.55 * I, -0.2 if p % 2 else 0.2, at)
        if I > 0.75: add(tk2, 0.25 * I, 0.4 if p % 2 else -0.4, at + beat / 2)

# ------------------------------------------------------------------ golpes, barridos y estruendo
def boom(dur=2.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(30 + 50 * np.exp(-tt * 6)) / SR) * np.exp(-tt * 1.6)
    x += lp(rng.standard_normal(n), 400) * np.exp(-tt * 4) * 0.6
    return x
def whoosh(dur=1.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n); out = np.zeros(n); blk = 1024
    for i in range(0, n, blk):
        fc = 300 + 3500 * np.sin(np.pi * i / n) ** 2
        out[i:i + blk] = lp(x[i:i + blk], fc, 1)
    return out * np.sin(np.pi * tt / dur) ** 2
for name, g in [('gancho', 0.9), ('persas', 0.7), ('pasillos', 1.0), ('cuna', 1.0), ('final', 0.8)]:
    add(boom(), g * 0.8, 0, max(0, SC[name][0] - 0.02))
for name in ['macedonios', 'persas', 'carros', 'diagonal', 'hueco', 'pasillos', 'cuna', 'huida', 'final']:
    add(whoosh(), 0.18, 0, SC[name][0] - 0.6)
a, b, _ = SC['pasillos']
rumble = lp(rng.standard_normal(N), 140) * seg(a - 0.5, b + 0.5, 1.0)
add(rumble, 0.9)
clank = np.zeros(N)
for k in range(40):
    at = a + rng.random() * (b - a); i0 = int(at * SR); n = int(0.15 * SR)
    if i0 + n < N: clank[i0:i0 + n] += hp(rng.standard_normal(n), 2500) * np.exp(-np.arange(n) / SR * 40)
add(clank, 0.12, 0.3)
a, b, _ = SC['cuna']
hooves = np.zeros(N)
for k in range(int((b - a) / 0.11)):
    at = a + k * 0.11 + rng.random() * 0.02; i0 = int(at * SR); n = int(0.08 * SR)
    if i0 + n < N: hooves[i0:i0 + n] += lp(rng.standard_normal(n), 300) * np.exp(-np.arange(n) / SR * 50)
add(hooves, 0.6)

music = np.stack([L, R], 1)
music = np.tanh(music / (np.abs(music).max() + 1e-9) * 1.6) * 0.55   # saturación suave
music[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))[:, None]

# ------------------------------------------------------------------ voz + ducking
voice = np.zeros(N)
for i, (a, b, v) in enumerate(TIMES):
    p = os.path.join(HERE, 'voz', f'frase_{i:02}.wav')
    with wave.open(p) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768
    x = resample_poly(x, SR, sr); i0 = int(v * SR); n = min(len(x), N - i0)
    voice[i0:i0 + n] += x[:n]
voice = hp(voice, 90)
voice = voice / (np.abs(voice).max() + 1e-9) * 0.9
env = np.abs(voice)
att, rel = np.exp(-1 / (0.02 * SR)), np.exp(-1 / (0.35 * SR))
# seguidor de envolvente (ataque rápido, relajación lenta)
e = np.zeros(N); acc = 0.0
blk = 240
for i in range(0, N, blk):
    m = env[i:i + blk].max()
    acc = m if m > acc else acc * rel ** blk
    e[i:i + blk] = acc
e = np.clip(e / 0.25, 0, 1)
duck = 1 - 0.72 * e
mix = music * duck[:, None] + voice[:, None] * 1.0
mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
with wave.open(os.path.join(HERE, 'mezcla.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print(f"mezcla.wav {TOTAL:.2f} s · ducking medio con voz: {20 * np.log10(np.mean(duck[e > 0.5])):.1f} dB")
