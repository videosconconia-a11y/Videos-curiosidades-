# Música tensa sintetizada (trap oscuro, Do menor) + efectos + voz con ducking -> mix.wav
import numpy as np, wave, os, sys
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import timeline
LINES, WORDS, SHOTS, TOTAL = timeline()
SR = 48000; N = int(SR * (TOTAL + 0.3)); t = np.arange(N) / SR
rng = np.random.default_rng(6)

def lp(x, a): return lfilter([a], [1, a - 1], x)
def hp(x, a): return x - lp(x, a)
def place(buf, x, at, g=1.0):
    i0 = int(at * SR)
    if i0 >= N: return
    n = min(len(x), N - i0); buf[i0:i0 + n] += x[:n] * g

M = np.zeros(N)         # música
FX = np.zeros(N)        # efectos
BPM = 140; beat = 60 / BPM; bar = 4 * beat

# --- instrumentos
def kick808(f0=55, dur=0.9):
    tt = np.arange(int(dur * SR)) / SR
    f = f0 + 120 * np.exp(-tt * 40)
    return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2))
def snare():
    tt = np.arange(int(0.25 * SR)) / SR
    return hp(rng.standard_normal(len(tt)), 0.3) * np.exp(-tt * 22) * 0.8 + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 30) * 0.5
def hat(open_=False):
    tt = np.arange(int((0.18 if open_ else 0.05) * SR)) / SR
    return hp(rng.standard_normal(len(tt)), 0.7) * np.exp(-tt * (18 if open_ else 90))
K, S, Ho, Hc = kick808(), snare(), hat(True), hat()

# progresión Do menor: Cm - Ab - Fm - G
roots = [130.81, 103.83, 87.31, 98.0]
chords = [[130.81, 155.56, 196.0], [103.83, 130.81, 155.56], [87.31, 103.83, 130.81], [98.0, 123.47, 146.83]]
music_start = 0.0
nbars = int(TOTAL / bar) + 2
for b in range(nbars):
    t0 = music_start + b * bar
    ci = b % 4
    # pad oscuro
    n = int(bar * SR); tt = np.arange(n) / SR
    pad = sum(np.sign(np.sin(2 * np.pi * f * 1.003 * tt)) * 0.3 + np.sin(2 * np.pi * f * tt) for f in chords[ci])
    pad = lp(pad, 0.05) * np.minimum(1, tt / 0.05) * np.minimum(1, (bar - tt) / 0.05)
    place(M, pad, t0, 0.07)
    # campana/pluck de tensión (arpegio)
    for k in range(8):
        f = chords[ci][k % 3] * (4 if k % 2 else 2)
        m = int(0.25 * SR); tt2 = np.arange(m) / SR
        place(M, np.sin(2 * np.pi * f * tt2) * np.exp(-tt2 * 14), t0 + k * beat / 2, 0.05)
    # batería (patrón trap a medio tiempo)
    for k in (0, 1.75, 2.5):
        place(M, kick808(roots[ci] / 2), t0 + k * beat, 0.55)
    place(M, S, t0 + 2 * beat, 0.35)
    for k in range(16):
        roll = (b % 2 == 1 and k >= 12)
        place(M, Hc, t0 + k * beat / 4, 0.10 if k % 2 == 0 else 0.06)
        if roll: place(M, Hc, t0 + k * beat / 4 + beat / 8, 0.06)
    place(M, Ho, t0 + 3.5 * beat, 0.06)

# --- efectos
def whoosh(dur=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n); env = np.sin(np.pi * tt / dur) ** 2
    out = np.zeros(n); a = 0.02
    for i in range(0, n, 512):  # barrido de filtro
        a = 0.02 + 0.4 * (i / n); out[i:i + 512] = lp(x[i:i + 512], a)
    return hp(out, 0.05) * env * 3
def impact():
    n = int(1.4 * SR); tt = np.arange(n) / SR
    f = 40 + 90 * np.exp(-tt * 12)
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3)) + lp(rng.standard_normal(n), 0.08) * np.exp(-tt * 8) * 2
def register():
    # "ka-ching": golpe mecánico + campanilla
    n = int(0.9 * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    click = hp(rng.standard_normal(int(0.03 * SR)), 0.4) * np.exp(-np.arange(int(0.03 * SR)) / 300)
    x[:len(click)] += click; x[int(0.06 * SR):int(0.06 * SR) + len(click)] += click * 0.8
    i = int(0.12 * SR); tb = tt[:n - i]
    bell = sum(np.sin(2 * np.pi * f * tb) * g for f, g in [(2093, 1), (2637, 0.7), (3136, 0.5), (4186, 0.3)])
    x[i:] += bell * np.exp(-tb * 5) * 0.5
    return x
def riser(dur=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    return hp(rng.standard_normal(n), 0.1) * (tt / dur) ** 2 * 0.8
WH, IM, REG = whoosh(), impact(), register()

for s in SHOTS[1:]:
    place(FX, WH, s["a"] - 0.15, 0.22)
place(FX, IM, 0.0, 0.9)                      # drop del gancho
for s in SHOTS:
    if s["e"] in ("step", "warn"): place(FX, IM, s["a"], 0.6)
    if s["e"] == "end": place(FX, IM, s["a"], 0.45)
    if s["e"] in ("counter_up",): place(FX, REG, s["a"] + 1.3, 0.5)
    if s["e"] == "counter_down": place(FX, riser(1.2)[::-1], s["a"], 0.25)
money_words = {"DINERO.", "EFECTIVO,", "BILLETES:", "PAGAN", "RICO", "DINERO"}
for w in WORDS:
    if w["text"].upper() in money_words: place(FX, REG, w["a"], 0.35)
for L in LINES[1:]:
    place(FX, riser(0.6), L["start"] - 0.6, 0.08)

# --- voz
V = np.zeros(N)
for i, L in enumerate(LINES):
    with wave.open(os.path.join(HERE, "voz", f"l{i}.wav")) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    place(V, x, L["start"])
# compresión suave y realce de presencia
V = np.tanh(V * 2.2) / np.tanh(2.2)
V = V + 0.25 * hp(V, 0.25)
V /= np.abs(V).max() / 0.95

# --- ducking: la música baja mientras habla la voz
# actividad de voz a partir de los tiempos de cada frase, con rampas suaves (ataque 80 ms, salida 250 ms)
act = np.zeros(N)
for L in LINES:
    act[int((L["start"] - 0.05) * SR):int((L["end"] + 0.05) * SR)] = 1
env = lfilter([1 - np.exp(-1 / (0.08 * SR))], [1, -np.exp(-1 / (0.08 * SR))], act)
env = np.maximum(env, lfilter([1 - np.exp(-1 / (0.25 * SR))], [1, -np.exp(-1 / (0.25 * SR))], act))
env = np.clip(env, 0, 1)
duck = 10 ** (-15 * env / 20)          # -15 dB bajo la voz
intensity = np.interp(t, [0, 0.4, 1.0, TOTAL - 4.5, TOTAL - 0.3, TOTAL + 1], [1.0, 1.0, 0.9, 0.9, 1.0, 0.0])
music = M * duck * intensity * 0.75
fx = FX * 0.7 * 10 ** (-9 * env / 20)
mix = V * 0.95 + music + fx
fade = np.clip((TOTAL + 0.2 - t) / 0.6, 0, 1)
mix = np.tanh(mix * fade * 1.2) / np.tanh(1.2)
mix /= np.abs(mix).max() / 0.93
st = np.stack([mix, mix], 1)
with wave.open(os.path.join(HERE, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("mix.wav", round(N / SR, 2), "s")
if os.environ.get("AUDIO_DEBUG"):
    def r(x, a, b): s = x[int(a * SR):int(b * SR)]; return 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9)
    for L in LINES:
        a, b = L["start"] + 0.4, L["end"] - 0.3
        print(f"voz {r(V*0.95,a,b):6.1f} dB | música+fx {r(music+fx,a,b):6.1f} dB")
