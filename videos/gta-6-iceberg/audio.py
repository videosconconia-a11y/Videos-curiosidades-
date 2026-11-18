# Música original estilo synthwave (sintetizada aquí, sin muestras de terceros) + efectos + voz IA con "ducking":
# la música baja automáticamente mientras habla la voz.
import numpy as np, wave, sys, os
from scipy.signal import lfilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import TOTAL, VOICE_AT, shot_timeline, hits

SR = 48000
N = int(SR * (TOTAL + 0.3))
t = np.arange(N) / SR
rng = np.random.default_rng(7)
def lp(x, a): return lfilter([a], [1, a - 1], x)
def seg(a, b, fade=0.3): return np.clip(np.minimum((t - a) / fade, (b - t) / fade), 0, 1)
L = np.zeros(N); R = np.zeros(N)
def add(x, g=1.0, pan=0.0):
    global L, R
    L += x * g * (1 - pan); R += x * g * (1 + pan)
def place(x, at):
    out = np.zeros(N); i0 = int(at * SR); n = min(len(x), N - i0)
    if n > 0: out[i0:i0 + n] = x[:n]
    return out

BPM = 104; beat = 60 / BPM; bar = 4 * beat
# Progresión Am – F – C – G (frecuencias raíz)
ROOTS = [110.0, 87.31, 130.81, 98.0]
CHORDS = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
chord_i = (t // bar).astype(int) % 4

def saw(f, ph=0.0, n=8):
    return sum(np.sin(2 * np.pi * f * k * t + ph * k) / k for k in range(1, n + 1))

# Pad (cuerdas analógicas, desafinadas)
pad = np.zeros(N)
for ci, ch in enumerate(CHORDS):
    m = (chord_i == ci).astype(float)
    m = lp(m, 0.0006)
    for f in ch:
        pad += m * (saw(f * 0.999, 0.3, 5) + saw(f * 1.003, 1.1, 5)) * 0.5
pad = lp(pad, 0.06)
add(pad, 0.035, 0.0)

# Bajo en corcheas con envolvente "pluck"
bass = np.zeros(N); step = beat / 2; k = 0.0
while k < TOTAL:
    ci = int(k // bar) % 4; f = ROOTS[ci] / 2 * (2 if int(k / step) % 4 == 3 else 1)
    n = int(step * SR); tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * j * tt) / j for j in range(1, 7)) * np.exp(-tt * 9)
    bass += place(x, k); k += step
add(lp(bass, 0.12), 0.22)

# Arpegio brillante (semicorcheas) a partir del nivel 1
arp = np.zeros(N); step = beat / 4; k = VOICE_AT[1] - 0.2; j = 0
while k < TOTAL - 0.5:
    ci = int(k // bar) % 4; f = CHORDS[ci][j % 3] * 2
    n = int(step * SR); tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 22)
    arp += place(x, k); k += step; j += 1
add(arp, 0.035, 0.35)

# Batería: bombo a negras, caja en 2 y 4 con "gated reverb", hi-hat en corcheas
def kick(at):
    n = int(0.35 * SR); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(45 + 110 * np.exp(-tt * 30)) / SR
    return place(np.sin(ph) * np.exp(-tt * 9), at)
def snare(at):
    n = int(0.28 * SR); tt = np.arange(n) / SR
    nz = rng.standard_normal(n); nz = nz - lp(nz, 0.15)
    env = np.where(tt < 0.2, 1.0, np.exp(-(tt - 0.2) * 60)) * np.exp(-tt * 4)
    return place(nz * env * 0.8 + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 25), at)
def hat(at):
    n = int(0.05 * SR); tt = np.arange(n) / SR; nz = rng.standard_normal(n)
    return place((nz - lp(nz, 0.5)) * np.exp(-tt * 90), at)
k = 0.0; b = 0
while k < TOTAL - 1.0:
    add(kick(k), 0.30)
    if b % 4 in (1, 3) and k > 1.0: add(snare(k), 0.12)
    if k > VOICE_AT[1] - 0.2:
        add(hat(k), 0.03, -0.3); add(hat(k + beat / 2), 0.02, 0.3)
    k += beat; b += 1

# Impactos (boom) en cada nivel / cifra, "whoosh" en cada cambio de plano, riser antes del final
def boom(at):
    n = int(1.6 * SR); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(32 + 90 * np.exp(-tt * 14)) / SR
    nz = lp(rng.standard_normal(n), 0.05) * np.exp(-tt * 6) * 3
    return place(np.sin(ph) * np.exp(-tt * 3) + nz, at)
for h in hits(): add(boom(h), 0.35)
for (a, b2, s) in shot_timeline()[1:]:
    x = rng.standard_normal(N); m = np.exp(-((t - a) / 0.10) ** 2)
    add((x - lp(x, 0.1)) * m, 0.05, rng.uniform(-0.5, 0.5))
end_a = VOICE_AT[-1]
x = rng.standard_normal(N); m = seg(end_a - 1.6, end_a + 0.02, 0.02) * np.clip((t - end_a + 1.6) / 1.6, 0, 1) ** 2
add((x - lp(x, 0.2)) * m, 0.06)

music = np.stack([L, R], 1)
music = np.tanh(music * 1.4) / np.tanh(1.4)
music /= np.abs(music).max()

# ---- voz IA
voice = np.zeros(N)
for i, at in enumerate(VOICE_AT):
    p = os.path.join(HERE, "voice", f"scene_{i:02}.wav")
    if not os.path.exists(p): continue
    with wave.open(p) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    if sr != SR: x = np.interp(np.arange(int(len(x) * SR / sr)) * sr / SR, np.arange(len(x)), x)
    voice += place(x, at)
if np.abs(voice).max() > 0:
    # un poco de presencia: realce de agudos + compresión suave
    voice = voice + 0.35 * (voice - lp(voice, 0.25))
    voice = np.tanh(voice / np.abs(voice).max() * 1.8) / np.tanh(1.8)

# ---- ducking: envolvente de la voz (ataque rápido, relajación lenta) → ganancia de la música
env = np.abs(voice)
ar = 1 - 1 / (0.25 * SR)
# relajación ~250 ms (vectorizado por bloques para no ir muestra a muestra)
blk = 480; e_blk = env[: N // blk * blk].reshape(-1, blk).max(1)
r_blk = np.empty_like(e_blk); a = 0.0
for i, v in enumerate(e_blk):
    a = v if v > a else a * (ar ** blk); r_blk[i] = a
rel = np.repeat(r_blk, blk); rel = np.pad(rel, (0, N - len(rel)), "edge")
speaking = np.clip(rel / 0.05, 0, 1)
duck = 1 - 0.80 * speaking                      # −14 dB mientras habla
music_d = music * duck[:, None]

mix = music_d * 0.55 + voice[:, None] * 0.95
fade = np.clip((TOTAL - t) / 0.6, 0, 1) * np.clip(t / 0.02, 0, 1)
mix *= fade[:, None]
mix /= max(1.0, np.abs(mix).max() / 0.95)

def save(path, st):
    with wave.open(os.path.join(HERE, path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
save("music_sfx.wav", music * 0.55 * fade[:, None])
save("mix.wav", mix)
print("ok", round(N / SR, 2), "s · voz:", "sí" if np.abs(voice).max() > 0 else "NO (ejecuta tts.py)")
