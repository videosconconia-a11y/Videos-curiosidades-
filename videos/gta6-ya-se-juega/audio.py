# Música synthwave original (generada aquí, sin derechos de terceros) + efectos en cada corte,
# mezclada con la voz y con "ducking": la música baja mientras habla la voz.
import numpy as np, wave, os, sys, subprocess
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import total, shot_timeline, scene_bounds

SR = 48000
TOTAL = total()
N = int(SR * (TOTAL + 0.3))
t = np.arange(N) / SR
rng = np.random.default_rng(11)
L = np.zeros(N); R = np.zeros(N)

def add(x, g=1.0, pan=0.0):
    global L, R
    L += x * g * (1 - pan); R += x * g * (1 + pan)

def lp(x, a): return lfilter([a], [1, a - 1], x)
def hp(x, a): return x - lp(x, a)
def note(m): return 440 * 2 ** ((m - 69) / 12)
def saw(f, tt, det=0.0):
    ph = (f * (1 + det)) * tt
    return 2 * (ph - np.floor(ph + 0.5))

BPM = 104; B = 60 / BPM; BAR = 4 * B
# Progresión La menor – Fa – Do – Sol (muy "Vice City")
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
ROOTS = [45, 41, 36, 43]

def place(x_local, at, g=1.0, pan=0.0):
    i0 = int(at * SR)
    if i0 >= N: return
    n = min(len(x_local), N - i0)
    y = np.zeros(N); y[i0:i0 + n] = x_local[:n]; add(y, g, pan)

# Intensidad: suave en el gancho, sube a partir de los datos, cae en el final
s = scene_bounds()
key = [(0, 0.55), (s[1][0], 0.8), (s[5][0], 1.0), (s[6][0], 0.75), (s[7][0], 0.9), (TOTAL - 1.5, 0.9), (TOTAL, 0.0)]
I = np.interp(t, [k[0] for k in key], [k[1] for k in key])

nb = int(TOTAL / B) + 2
for b in range(nb):
    at = b * B; bar = int(at / BAR); ch = CHORDS[bar % 4]; root = ROOTS[bar % 4]
    # Bombo
    n = int(0.35 * SR); tt = np.arange(n) / SR
    kick = np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9)
    place(kick, at, 0.55)
    # Caja en 2 y 4 con cola
    if b % 2 == 1:
        n = int(0.6 * SR); tt = np.arange(n) / SR
        sn = hp(rng.standard_normal(n), 0.15) * np.exp(-tt * 9) + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 25) * 0.5
        place(sn, at, 0.22)
    # Hi-hats en corcheas
    for h in (0, 0.5):
        n = int(0.05 * SR); tt = np.arange(n) / SR
        place(hp(rng.standard_normal(n), 0.6) * np.exp(-tt * 70), at + h * B, 0.05 + 0.03 * (h > 0), 0.3)
    # Bajo en corcheas (octavas)
    for k, h in enumerate((0, 0.5)):
        n = int(B / 2 * SR); tt = np.arange(n) / SR
        f = note(root + (12 if k else 0))
        bs = lp(saw(f, tt) + saw(f, tt, 0.006), 0.12) * np.minimum(1, tt / 0.005) * np.exp(-tt * 5)
        place(bs, at + h * B, 0.30)
    # Arpegio en semicorcheas
    for q in range(4):
        n = int(B / 4 * SR); tt = np.arange(n) / SR
        m = ch[(b * 4 + q) % 3] + 12 * (1 + (q == 3))
        ar = (saw(note(m), tt) * 0.6 + np.sign(np.sin(2 * np.pi * note(m) * tt)) * 0.4) * np.exp(-tt * 14)
        place(lp(ar, 0.25), at + q * B / 4, 0.05, 0.35 * (1 if q % 2 else -1))

# Pad por compás (acordes con desafinación)
for bar in range(int(TOTAL / BAR) + 1):
    n = int(BAR * SR); tt = np.arange(n) / SR
    pad = sum(saw(note(m), tt, d) for m in CHORDS[bar % 4] for d in (-0.004, 0.004))
    env = np.minimum(1, tt / 0.4) * np.minimum(1, (BAR - tt) / 0.3)
    place(lp(pad, 0.04) * env, bar * BAR, 0.05, 0.0)

L *= I; R *= I

# Efectos: whoosh en cada corte, golpe grave en las cifras
for (a, b, shot) in shot_timeline()[1:]:
    n = int(0.5 * SR); tt = np.arange(n) / SR
    w = hp(rng.standard_normal(n), 0.08) * np.exp(-((tt - 0.25) / 0.09) ** 2)
    place(w, a - 0.25, 0.10, rng.uniform(-0.4, 0.4))
for (a, b, shot) in shot_timeline():
    if shot[4] and shot[4][0] in ("stat", "clocks"):
        n = int(1.4 * SR); tt = np.arange(n) / SR
        boom = np.sin(2 * np.pi * np.cumsum(32 + 70 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 3.5)
        place(boom, a + 0.05, 0.45)

music = np.stack([L, R], 1)
music = np.tanh(music * 1.4) / np.tanh(1.4)
music /= np.abs(music).max() / 0.8

# Voz + ducking
w = wave.open(os.path.join(HERE, "voice.wav")); vs = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
voice = np.zeros(N); voice[:min(N, len(vs))] = vs[:N]
env = np.sqrt(lfilter([0.002], [1, -0.998], voice ** 2))           # envolvente de la voz
from scipy.ndimage import maximum_filter1d
speaking = maximum_filter1d(np.clip(env / 0.03, 0, 1), int(0.35 * SR))   # mantiene la bajada entre palabras
speaking = lfilter([0.0005], [1, -0.9995], speaking)                      # transición suave (~40 ms)
duck = 1.0 - 0.72 * np.clip(speaking * 1.5, 0, 1)                  # unos -11 dB bajo la voz
mix = music * duck[:, None] * 0.55 + voice[:, None] * 1.25
fade = np.clip((TOTAL + 0.2 - t) / 1.2, 0, 1) * np.clip(t / 0.03, 0, 1)
mix *= fade[:, None]
mix /= max(1.0, np.abs(mix).max() / 0.95)
raw = os.path.join(HERE, "mix_raw.wav")
with wave.open(raw, "wb") as o:
    o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((mix * 32767).astype(np.int16).tobytes())
# Sonoridad estándar de redes (-14 LUFS)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR),
                os.path.join(HERE, "mix.wav")], check=True)
os.remove(raw)
print("audio ok", TOTAL)
