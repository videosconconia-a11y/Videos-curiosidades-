# Banda sonora: música cinematográfica sintetizada + efectos + voz IA, con ducking
# (la música baja automáticamente cuando habla el narrador). Salida: mix.wav
import os, sys, json, wave
import numpy as np
from scipy.signal import butter, sosfilt, lfilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS, segment_times, shot_timeline, total, load_timings

SR = 48000
T = total() + 0.3
N = int(SR * T)
t = np.arange(N) / SR
rng = np.random.default_rng(11)
SEG = {sid: (a, e, b) for sid, a, e, b in segment_times()}
TM = load_timings()

def word_t(sid, word, default=0.0):
    for w in TM[sid]["words"]:
        if w["w"].strip(".,;:¡!¿?…").lower() == word: return SEG[sid][0] + w["start"]
    return SEG[sid][0] + default

def lp(x, fc, order=2): return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, order=2): return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)
def midi(m): return 440 * 2 ** ((m - 69) / 12)

ML = np.zeros(N); MR = np.zeros(N)      # música
FL = np.zeros(N); FR = np.zeros(N)      # efectos
def put(buf, x, at, gain=1.0, pan=0.0):
    i0 = int(at * SR)
    if i0 >= N: return
    x = x[: N - max(i0, 0)]
    if i0 < 0: x = x[-i0:]; i0 = 0
    L, R = buf
    L[i0:i0 + len(x)] += x * gain * (1 - pan) ** 0.5
    R[i0:i0 + len(x)] += x * gain * (1 + pan) ** 0.5
MUS = (ML, MR); SFX = (FL, FR)

# ---------------------------------------------------------------- instrumentos
def piano(f, dur=3.0, vel=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for h in range(1, 9):
        fh = f * h * (1 + 0.0004 * h * h)
        x += np.sin(2 * np.pi * fh * tt) * (0.7 ** h) * np.exp(-tt * (1.2 + 0.9 * h))
    x *= np.minimum(1, tt / 0.004)
    return lp(x, 2600 + 1800 * vel) * vel

def bell(f, dur=4.0, vel=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    mod = np.sin(2 * np.pi * f * 3.5 * tt) * 2.2 * np.exp(-tt * 2)
    return np.sin(2 * np.pi * f * tt + mod) * np.exp(-tt * 1.3) * np.minimum(1, tt / 0.003) * vel

def pad(freqs, a, b, gain, bright=900, att=1.5, rel=2.0):
    i0, i1 = int(a * SR), min(N, int((b + rel) * SR)); tt = np.arange(i1 - i0) / SR
    x = np.zeros(i1 - i0)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ph = rng.uniform(0, 1)
            saw = 2 * ((tt * f * 2 ** (det / 12) + ph) % 1) - 1
            x += saw
    x = lp(x / (len(freqs) * 3), bright, 2)
    env = np.minimum(1, tt / att) * np.clip((b + rel - (a + tt)) / rel, 0, 1)
    out = np.zeros(N); out[i0:i1] = x * env * gain
    return out

def sub_boom(dur=2.5, f0=70, f1=32):
    n = int(dur * SR); tt = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt * 6)) / SR
    x = np.sin(ph) * np.exp(-tt * 1.6)
    nz = lp(rng.standard_normal(n), 400) * np.exp(-tt * 9) * 0.6
    return (x + nz) * np.minimum(1, tt / 0.002)

def heartbeat(at, g=1.0):
    for d, a in ((0, 1.0), (0.17, 0.75)):
        n = int(0.3 * SR); tt = np.arange(n) / SR
        x = np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 16) * a
        put(SFX, lp(x, 180), at + d, 0.9 * g)

def whoosh(at, dur=0.55, g=1.0, pan=0.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    lo = hp(x, 300); y = bp(lo, 600, 5000) * env
    put(SFX, y, at - dur * 0.6, 0.10 * g, pan)

def riser(end, dur=2.2, g=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR; p = tt / dur
    x = rng.standard_normal(n)
    y = bp(x, 800, 7000) * p ** 2.5
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * p ** 2) / SR) * p ** 3 * 0.25
    put(SFX, y + tone, end - dur, 0.16 * g)

def sniff(at, g=1.0):
    for k, d in enumerate((0.0, 0.16, 0.3)):
        n = int(0.12 * SR); tt = np.arange(n) / SR
        x = bp(rng.standard_normal(n), 1800, 6500) * np.sin(np.pi * tt / 0.12) ** 1.5
        put(SFX, x, at + d, 0.22 * g * (1 - 0.15 * k), -0.1)

def shimmer(at, g=1.0):
    for k, m in enumerate([86, 90, 93, 98, 102]):
        put(SFX, bell(midi(m), 2.5, 0.5), at + k * 0.07, 0.05 * g, -0.6 + 0.3 * k)

def blip(at, f=1400, g=1.0):
    n = int(0.09 * SR); tt = np.arange(n) / SR
    put(SFX, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 40), at, 0.06 * g, 0.3)

def pop(at):
    n = int(0.15 * SR); tt = np.arange(n) / SR
    put(SFX, np.sin(2 * np.pi * (300 + 900 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 30), at, 0.25)

# ---------------------------------------------------------------- música
BPM = 76; beat = 60 / BPM
A = SEG
t_sci = A["s05"][0]; t_olf = A["s07"][0]; t_emo = A["s10"][0]; t_warm = A["s11"][0]; t_end = A["s13"][0]

# 1) dron grave misterioso todo el vídeo (Re menor), se abre al final
drone = np.zeros(N)
for f, g in [(midi(38), 0.30), (midi(45), 0.16), (midi(50), 0.10)]:
    drone += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * g * (0.75 + 0.25 * np.sin(2 * np.pi * 0.09 * t + f))
dr_env = np.interp(t, [0, 0.3, t_end, T - 1.5, T], [0.0, 1.0, 0.9, 0.5, 0.0])
put(MUS, drone * dr_env, 0, 0.55)

# 2) pads por secciones: misterio (Dm–Bb), ciencia (Dm–F–C–Bb), emoción (Bb–F–Gm–Dm), cálido (D–A–Bm–G)
def chord_seq(start, end, chords, bar, gain, bright):
    k = 0; s = start
    while s < end:
        e = min(end, s + bar)
        put(MUS, pad([midi(m) for m in chords[k % len(chords)]], s, e, gain, bright, att=0.8, rel=1.2), 0)
        s = e; k += 1
bar = beat * 4
chord_seq(0.0, t_sci, [[50, 53, 57], [46, 50, 53]], bar, 0.10, 700)
chord_seq(t_sci, t_emo, [[50, 53, 57], [53, 57, 60], [48, 52, 55], [46, 50, 53]], bar, 0.11, 1100)
chord_seq(t_emo, t_warm, [[46, 50, 53], [53, 57, 60], [43, 46, 50], [50, 53, 57]], bar, 0.10, 900)
chord_seq(t_warm, T - 1.0, [[50, 54, 57], [45, 49, 52], [47, 50, 54], [43, 47, 50]], bar, 0.12, 1500)

# 3) piano: motivo misterioso de inicio, arpegios en la parte científica, melodía emotiva al final
motif = [(0.35, 74), (0.9, 77), (1.45, 76), (2.3, 69)]
for at, m in motif: put(MUS, bell(midi(m), 3.5, 0.9), at, 0.07, 0.2)
ARP = {0: [62, 65, 69, 74], 1: [58, 62, 65, 70], 2: [65, 69, 72, 77], 3: [60, 64, 67, 72]}
def arps(start, end, prog, vel, eighth=True):
    s = start; k = 0; step = beat / 2 if eighth else beat
    while s < end:
        notes = ARP[prog[(k // (8 if eighth else 4)) % len(prog)]]
        m = notes[k % 4] + (12 if (k // 4) % 2 and eighth else 0)
        put(MUS, piano(midi(m), 2.0, vel * (0.85 + 0.15 * (k % 2 == 0))), s, 0.16)
        s += step; k += 1
arps(A["s01"][0], t_sci, [0, 1], 0.55, eighth=False)
arps(t_sci, t_emo - 0.2, [0, 2, 3, 1], 0.65, eighth=True)
mel = [70, 69, 65, 67, 69, 62, 65, 64]
for k, m in enumerate(mel):
    put(MUS, piano(midi(m), 3.0, 0.8), t_emo + 0.2 + k * beat, 0.22)
warm_mel = [74, 73, 71, 69, 71, 74, 76, 78, 76, 74, 73, 74]
for k, m in enumerate(warm_mel):
    at = t_warm + 0.3 + k * beat * 1.0
    if at < T - 2: put(MUS, piano(midi(m), 3.5, 0.85), at, 0.24); put(MUS, piano(midi(m - 12), 3.5, 0.5), at, 0.12)
put(MUS, piano(midi(50), 6, 0.9), T - 4.8, 0.25); put(MUS, piano(midi(57), 6, 0.7), T - 4.8, 0.18)
put(MUS, piano(midi(62), 6, 0.7), T - 4.75, 0.18); put(MUS, piano(midi(66), 6, 0.6), T - 4.7, 0.16)

# 4) pulso grave (latido musical) en la parte científica
s = t_sci
while s < t_emo - 0.3:
    n = int(0.4 * SR); tt = np.arange(n) / SR
    k = np.sin(2 * np.pi * (45 + 40 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 8)
    put(MUS, k, s, 0.35 if s < t_olf else 0.45); s += beat

# ---------------------------------------------------------------- efectos
put(SFX, sub_boom(3.0), 0.02, 0.85)                       # impacto inicial
for k in range(4): heartbeat(0.55 + k * 0.85, 0.7 - 0.1 * k)
put(SFX, bell(midi(86), 3, 1.0), 0.05, 0.05, 0.4)         # brillo misterioso
for a, b, name in shot_timeline()[1:]:
    whoosh(a, g=0.8, pan=float(rng.uniform(-0.5, 0.5)))
for sid in ("s02", "s03", "s05", "s10", "s12"):
    put(SFX, sub_boom(1.6, 80, 38), A[sid][0], 0.30)
riser(t_olf, 2.2); put(SFX, sub_boom(2.5), t_olf, 0.6)
olf = word_t("s07", "olfato", 2.5); sniff(olf - 0.1, 1.0)
for sh in shot_timeline():
    if sh[2] in ("dog_sniff_hand", "nose_side"): sniff(sh[0] + 0.25, 0.8)
mri = [s for s in shot_timeline() if s[2] in ("dog_mri", "mri_monitor")]
for a, b, _ in mri:
    k = a + 0.2
    while k < b: blip(k, 1300 + 200 * ((k * 3) % 2)); k += 0.5
st = word_t("s07", "trescientos", 3.6); put(SFX, sub_boom(1.2, 90, 45), st, 0.3)
pct = A["s08"][0] + 3.7; riser(pct, 1.0, 0.6); put(SFX, sub_boom(1.2, 90, 45), pct, 0.3)
shimmer(word_t("s11", "oxitocina", 6.0) - 0.1, 1.2)
shimmer(A["s13"][0] + 0.1, 0.8)
pop(A["s14"][0] + 2.1)

# ---------------------------------------------------------------- voz + ducking
VO = np.zeros(N)
for sid, a, e, b in segment_times():
    with wave.open(os.path.join(HERE, "voice", f"{sid}.wav")) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    i0 = int(a * SR); VO[i0:i0 + len(v)] += v[: N - i0]
VO = VO / (np.abs(VO).max() + 1e-9) * 0.92

env = np.abs(VO)
env = lfilter([1 - np.exp(-1 / (0.02 * SR))], [1, -np.exp(-1 / (0.02 * SR))], env)   # ataque rápido
# relajación lenta: máximo deslizante para que la música no "bombee" entre palabras
from scipy.ndimage import maximum_filter1d, uniform_filter1d
env = maximum_filter1d(env, int(0.35 * SR)); env = uniform_filter1d(env, int(0.15 * SR))
env = np.clip(env / (np.percentile(env[env > 1e-3], 90) + 1e-9), 0, 1)
duck = 1 - 0.68 * env                      # ≈ -10 dB de música mientras habla la voz

music_L = ML * duck; music_R = MR * duck
peak_m = max(np.abs(music_L).max(), np.abs(music_R).max()) + 1e-9
music_L /= peak_m; music_R /= peak_m
sfx_L, sfx_R = FL * (1 - 0.35 * env), FR * (1 - 0.35 * env)
peak_s = max(np.abs(sfx_L).max(), np.abs(sfx_R).max()) + 1e-9

MG, SG = 0.30, 0.42                         # niveles relativos (la voz manda siempre)
L = VO + music_L * MG + sfx_L / peak_s * SG
R = VO + music_R * MG + sfx_R / peak_s * SG
fade = np.clip((T - 0.25 - t) / 1.2, 0, 1)
st = np.stack([L, R], 1) * fade[:, None]
st = np.tanh(st * 1.2) / np.tanh(1.2)
st /= np.abs(st).max() / 0.95

def save(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1] if x.ndim > 1 else 1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
save(os.path.join(HERE, "mix_raw.wav"), st)
save(os.path.join(HERE, "music_only.wav"), np.stack([music_L, music_R], 1) * 0.8)
print("ok", round(T, 2), "s")
