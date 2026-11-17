# Audio: base trap/phonk oscura sintetizada (808 con glide, cencerro, hats, palmas), whoosh en cada
# corte, "cha-ching" con el dinero y la voz por encima con ducking (la música baja cuando habla).
# Salida: mix.wav (48 kHz estéreo).
import os, sys, wave, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, lfilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import load_timing, shot_timeline, norm, MONEY_WORDS

SR = 48000
TM = load_timing()
TOTAL = TM["total"]
N = int(SR * TOTAL)
t = np.arange(N) / SR
rng = np.random.default_rng(13)

def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def lpf(x, f, order=2): return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)
def hpf(x, f, order=2): return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)

def place(buf, x, at, gain=1.0):
    i0 = int(at * SR)
    if i0 >= len(buf): return
    if i0 < 0: x = x[-i0:]; i0 = 0
    n = min(len(x), len(buf) - i0); buf[i0:i0 + n] += x[:n] * gain

# ---------------------------------------------------------------- instrumentos
def kick808(f0, dur=0.55, glide_to=None):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = 45 + 160 * np.exp(-tt * 40)
    if f0: f = f0 + 150 * np.exp(-tt * 45)
    if glide_to: f = f + (glide_to - f0) * np.clip((tt - dur * 0.45) / (dur * 0.35), 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-tt * 2.6)
    x = np.tanh(x * 2.2) / np.tanh(2.2)          # saturación del 808
    return x * np.minimum(1, tt / 0.002)

def clap():
    n = int(0.25 * SR); tt = np.arange(n) / SR
    e = np.zeros(n)
    for k in range(3): e += (tt >= k * 0.011) * np.exp(-np.maximum(tt - k * 0.011, 0) * 60)
    e += np.exp(-tt * 18) * 0.5
    return bp(rng.standard_normal(n), 900, 3500) * e * 0.8

def hat(dur=0.05, open_=False):
    n = int((0.25 if open_ else dur) * SR); tt = np.arange(n) / SR
    return hpf(rng.standard_normal(n), 7000) * np.exp(-tt * (12 if open_ else 70)) * 0.35

def cowbell(freq, dur=0.22):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = (np.sign(np.sin(2 * np.pi * freq * tt)) + np.sign(np.sin(2 * np.pi * freq * 1.48 * tt))) * 0.5
    x = bp(x, 500, 4500) * np.exp(-tt * 14)
    return np.tanh(x * 2.5) * 0.5

def whoosh(dur=0.4, up=True):
    n = int(dur * SR); tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    out = np.zeros(n); seg = 512
    for i in range(0, n, seg):
        p = i / n; fc = 300 + (5000 if up else 3000) * (p if up else 1 - p) ** 1.5
        out[i:i + seg] = bp(nz[i:i + seg], max(80, fc * 0.6), min(18000, fc * 1.6), 1)
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    return out * env * 1.6

def impact():
    n = int(1.2 * SR); tt = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-tt * 8)) / SR) * np.exp(-tt * 2.5)
    nz = lpf(rng.standard_normal(n), 1500) * np.exp(-tt * 9) * 0.6
    return np.tanh((sub + nz) * 1.8) * 0.8

def cha_ching():
    """'Ka' mecánico de caja registradora + campanilla 'ching' + monedas."""
    n = int(1.1 * SR); tt = np.arange(n) / SR
    ka = bp(rng.standard_normal(n), 1500, 6000) * np.exp(-tt * 90) * 0.9
    ka += bp(rng.standard_normal(n), 400, 1500) * np.exp(-np.maximum(tt - 0.045, 0) * 120) * (tt > 0.045) * 0.6
    t2 = np.maximum(tt - 0.09, 0); on = tt > 0.09
    bell = sum(a * np.sin(2 * np.pi * f * t2) * np.exp(-t2 * dcy)
               for f, a, dcy in [(2093, 1.0, 4.5), (2637, 0.7, 5.0), (3136, 0.6, 6.0), (4186, 0.4, 7.0), (5274, 0.25, 9.0)])
    coins = np.zeros(n)
    for k in range(9):
        c0 = 0.12 + k * 0.045 + rng.uniform(0, 0.02); i0 = int(c0 * SR); m = int(0.08 * SR)
        if i0 + m < n:
            tc = np.arange(m) / SR
            coins[i0:i0 + m] += np.sin(2 * np.pi * rng.uniform(3500, 6000) * tc) * np.exp(-tc * 60) * 0.25
    return ka + bell * on * 0.45 + coins

# ---------------------------------------------------------------- música (phonk, 130 BPM)
BPM = 130; beat = 60 / BPM; bar = 4 * beat
M = np.zeros(N); B = np.zeros(N)            # M = batería+melodía, B = 808
# progresión oscura en Fa# menor: F#  D  E  C#
roots = [46.25, 36.71, 41.20, 34.65]       # Hz (F#1, D1, E1, C#1)
bell_scale = [740, 880, 988, 1109, 1175, 1319, 1480]  # F#5 A5 B5 C#6 D6 E6 F#6
cow_pat = [0, 2, 0, 4, 3, 2, 0, 1, 0, 2, 0, 4, 5, 4, 3, 2]
n_bars = int(TOTAL / bar) + 2
for b_ in range(n_bars):
    t0 = b_ * bar; r = roots[b_ % 4]
    intro = t0 < 0.3     # el primer compás arranca ya fuerte (gancho)
    # 808: patrón trap
    for pos, dur, gl in [(0, 0.75, None), (1.5, 0.5, None), (2.5, 0.5, r * 1.5), (3.25, 0.4, None)]:
        place(B, kick808(r * (2 if pos == 3.25 else 1), dur * beat * 1.9, gl), t0 + pos * beat, 0.9)
    # palmada en 2 y 4
    for pos in (1, 3):
        place(M, clap(), t0 + pos * beat, 0.55)
    # hats con redobles en tresillos al final de cada 2 compases
    for k in range(8):
        place(M, hat(), t0 + k * beat / 2, 0.5 if k % 2 == 0 else 0.3)
    if b_ % 2 == 1:
        for k in range(6):
            place(M, hat(0.03), t0 + 3 * beat + k * beat / 6, 0.35)
    place(M, hat(open_=True), t0 + 3.5 * beat, 0.25)
    # cencerro phonk (semicorcheas)
    for k in range(16):
        if k % 4 == 3 and b_ % 2 == 0: continue
        place(M, cowbell(bell_scale[cow_pat[k]] / (1 if b_ % 4 < 2 else 1.122)), t0 + k * beat / 4, 0.22 if k % 2 == 0 else 0.15)

# pad oscuro
pad = np.zeros(N)
for b_ in range(n_bars):
    t0 = b_ * bar; r = roots[b_ % 4] * 4
    i0 = int(t0 * SR); n = min(int(bar * SR), N - i0)
    if n <= 0: break
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) for f in (r, r * 1.19, r * 1.5, r * 2.005))
    pad[i0:i0 + n] += x * np.minimum(1, tt / 0.3) * np.minimum(1, (bar - tt) / 0.3) * 0.05
pad = lpf(pad, 1200)

music = M + B * 0.85 + pad
# "drop" corto antes de los dos trucos y al final (silencio de batería medio compás)
for at in (TM["sentences"][2][0], TM["sentences"][3][0]):
    g = np.ones(N); i0 = int((at - 0.45) * SR); i1 = int(at * SR); g[max(0, i0):i1] = 0.25
    music *= g
music = lpf(music, 14000)

# ---------------------------------------------------------------- efectos
FX = np.zeros(N)
cuts = [a for (a, b, n, si) in shot_timeline(TM)][1:]
for c in cuts:
    place(FX, whoosh(0.38, up=True), c - 0.28, 0.5)
place(FX, impact(), 0.0, 0.9)
for si in (2, 3):
    place(FX, impact(), TM["sentences"][si][0], 0.6)
money_t = [w[0] for w in TM["words"] if norm(w[2]) in MONEY_WORDS]
shots = shot_timeline(TM)
money_t += [a + 0.15 for (a, b, n, si) in shots if n in ("money_counter", "cash_rain_close")]
for mt in sorted(set(round(x, 2) for x in money_t)):
    place(FX, cha_ching(), mt - 0.05, 0.55)

# ---------------------------------------------------------------- voz + ducking
vproc = os.path.join(HERE, "cache", "voz_proc.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(HERE, "cache", "voz.wav"), "-af",
                "highpass=f=85,equalizer=f=220:t=q:w=1:g=2,equalizer=f=3200:t=q:w=1.2:g=3.5,"
                "acompressor=threshold=-20dB:ratio=3.5:attack=4:release=90:makeup=4,alimiter=limit=0.9",
                "-ar", str(SR), "-ac", "1", vproc], check=True)
with wave.open(vproc) as w:
    v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
v = np.pad(v, (0, max(0, N - len(v))))[:N]
v = v / (np.abs(v).max() + 1e-9) * 0.95

env = np.abs(v)
a_att = 1 - np.exp(-1 / (0.015 * SR)); a_rel = 1 - np.exp(-1 / (0.30 * SR))
sm = np.zeros(N); acc = 0.0
# seguidor de envolvente (ataque rápido, caída lenta)
env_ds = env.reshape(-1, 48).max(axis=1) if N % 48 == 0 else np.pad(env, (0, 48 - N % 48)).reshape(-1, 48).max(axis=1)
sm_ds = np.zeros_like(env_ds)
aa = 1 - np.exp(-1 / (0.015 * 1000)); ar = 1 - np.exp(-1 / (0.30 * 1000))
for i, e in enumerate(env_ds):
    acc += (e - acc) * (aa if e > acc else ar); sm_ds[i] = acc
sm = np.repeat(sm_ds, 48)[:N]
duck = 1 - 0.68 * np.clip(sm / 0.25, 0, 1)        # hasta ~-10 dB bajo la voz

music_l = music * duck * 0.36
fx_l = FX * (1 - 0.35 * np.clip(sm / 0.25, 0, 1))
L = v * 1.0 + music_l * 0.95 + fx_l * 0.9
R = v * 1.0 + music_l * 1.05 + fx_l * 0.9
fade = np.minimum(1, (TOTAL - t) / 0.04)            # sin clic en el bucle
st = np.stack([L * fade, R * fade], 1)
st = np.tanh(st * 1.1) / np.tanh(1.1)
with wave.open(os.path.join(HERE, "mix_raw.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(HERE, "mix_raw.wav"), "-af",
                "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", str(SR), os.path.join(HERE, "mix.wav")], check=True)
os.remove(os.path.join(HERE, "mix_raw.wav"))
print("mix.wav listo")
