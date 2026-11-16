import numpy as np, wave, sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import TOTAL, shot_timeline

SR = 48000
N = int(SR * (TOTAL + 0.5))
t = np.arange(N) / SR
rng = np.random.default_rng(7)

def lp(x, a):  # one-pole lowpass
    y = np.empty_like(x); acc = 0.0
    from scipy.signal import lfilter
    return lfilter([a], [1, a - 1], x)

def env(start, dur, attack=0.01, curve=4.0):
    e = np.zeros(N); i0 = int(start * SR); n = int(dur * SR)
    n = min(n, N - i0)
    tt = np.arange(n) / SR
    a = np.minimum(1, tt / attack) * np.exp(-curve * tt / dur)
    e[i0:i0 + n] = a; return e

def seg(a, b, fade=0.5):
    return np.clip(np.minimum((t - a) / fade, (b - t) / fade), 0, 1)

L = np.zeros(N); R = np.zeros(N)
def add(x, gain=1.0, pan=0.0):
    global L, R
    L += x * gain * (1 - pan) ; R += x * gain * (1 + pan)

# --- intensity curve of the music (0..1)
key = [(0,0.55),(4.5,0.45),(10,0.5),(15.5,0.75),(17,0.9),(21.5,0.7),(25.5,0.25),(28.4,0.05),(29.5,0.5),
       (36,0.85),(37.5,0.7),(43.2,1.0),(44.5,0.55),(50.5,0.6),(56.5,0.95),(58.2,0.0),(59,0.0)]
I = np.interp(t, [k[0] for k in key], [k[1] for k in key])

# Drone (A minor, cold): detuned sines + wind
for f, g in [(55,0.30),(55.4,0.22),(82.4,0.16),(110,0.10),(164.8,0.05)]:
    add(np.sin(2*np.pi*f*t + rng.uniform(0,6)) * (0.6+0.4*np.sin(2*np.pi*0.07*t+f)), g*0.55, 0.0)
wind = lp(rng.standard_normal(N), 0.004) * 8
wind *= 0.5 + 0.5*np.sin(2*np.pi*0.11*t)
add(wind, 0.05*(0.6+0.6*I), 0.2); add(lp(rng.standard_normal(N),0.004)*8, 0.05*(0.6+0.6*I), -0.2)

# Shimmer pad (ice): high partials with slow tremolo
for f, p in [(880,-0.5),(1318.5,0.5),(1760,-0.2),(1046.5,0.3)]:
    add(np.sin(2*np.pi*f*t) * (0.5+0.5*np.sin(2*np.pi*(0.3+f/5000)*t)), 0.012*(0.3+I), p)

# Warm chord for the thaw (C major-ish over A) 44.5–50.5
warm = seg(44.3, 50.8, 1.2)
for f in [130.8, 164.8, 196.0, 261.6, 329.6]:
    add(np.sin(2*np.pi*f*t)*(0.7+0.3*np.sin(2*np.pi*0.5*t+f)), 0.05*warm, 0.0)

# Pulse (tension) — low tom-like hits on a grid, density grows with intensity
def thump(at, f0=70, f1=38, dur=0.35, g=1.0):
    i0 = int(at*SR); n = min(int(dur*SR), N-i0); tt = np.arange(n)/SR
    ph = 2*np.pi*np.cumsum(f1 + (f0-f1)*np.exp(-tt*18))/SR
    x = np.zeros(N); x[i0:i0+n] = np.sin(ph)*np.exp(-tt*9)*g; return x
beat = 60/96
k = 0.0
while k < TOTAL:
    ii = np.interp(k, t, I)
    if ii > 0.45 and not (25.5 < k < 29.4):
        add(thump(k, g=ii), 0.35)
        if ii > 0.8:
            add(thump(k + beat/2, g=ii*0.6), 0.25)
    k += beat

# Booms on key reveals
def boom(at, g=1.0):
    x = thump(at, 95, 30, 2.2, 1.0)
    i0 = int(at*SR); n = min(int(1.2*SR), N-i0); tt=np.arange(n)/SR
    nz = np.zeros(N); nz[i0:i0+n] = lp(rng.standard_normal(n),0.05)*np.exp(-tt*5)*3
    return (x + nz)*g
for at in [0.05, 17.0, 28.6, 39.4, 44.5, 54.6]:
    add(boom(at), 0.55)

# Risers before reveals
def riser(end, dur=1.6):
    a = end-dur; m = seg(a, end+0.05, 0.05) * np.clip((t-a)/dur, 0, 1)**2
    x = rng.standard_normal(N); y = x - lp(x, 0.02 + 0.3*np.clip((t-a)/dur,0,1).mean())
    return y*m
for e in [17.0, 37.5, 44.5, 54.6]:
    add(riser(e), 0.10, 0.0)

# Ice cracks
def crack(at, g=1.0):
    x = np.zeros(N)
    for j in range(40):
        tt = at + rng.exponential(0.06)*j*0.3
        i = int(tt*SR); n = int(0.01*SR)
        if i+n < N: x[i:i+n] += rng.standard_normal(n)*np.exp(-np.arange(n)/40)*rng.uniform(0.3,1)
    return (x - lp(x, 0.2))*g
for at, p in [(1.0,-0.3),(2.4,0.3),(15.2,0.2),(19.1,-0.2),(20.5,0.4),(41.0,0.0)]:
    add(crack(at), 0.35, p)

# Heartbeats (lub-dub) and monitor beeps — same times as the picture
HB1 = [22.2, 23.0, 23.95, 25.1]
HB2 = [46.9, 47.9, 48.75, 49.5, 50.2]
for at in HB1 + HB2:
    add(thump(at, 60, 40, 0.25, 1.0), 0.6); add(thump(at+0.16, 55, 38, 0.25, 0.7), 0.5)
def beep(at, dur=0.12, g=1.0):
    return np.sin(2*np.pi*1000*t) * seg(at, at+dur, 0.005) * g
for at in HB1 + [46.9, 47.9]:
    add(beep(at), 0.05)
add(np.sin(2*np.pi*1000*t)*seg(25.5, 27.6, 0.02)*np.clip((27.6-t)/2.1,0,1), 0.05)  # flatline

# Whooshes on every cut
for (a, b, s) in shot_timeline()[1:]:
    x = rng.standard_normal(N); m = np.exp(-((t-a)/0.12)**2)
    add((x - lp(x, 0.1))*m, 0.06, rng.uniform(-0.5,0.5))

# Drips during thaw
for j in range(10):
    at = 44.6 + j*0.55 + rng.uniform(0,0.2)
    f = rng.uniform(900, 1500)
    i0=int(at*SR); n=int(0.15*SR); tt=np.arange(n)/SR
    x=np.zeros(N); x[i0:i0+n]=np.sin(2*np.pi*(f+f*2*tt)*tt)*np.exp(-tt*30)
    add(x, 0.08, rng.uniform(-0.6,0.6))

# Master: fade out, soft limit
fade = np.clip((TOTAL + 0.4 - t)/1.0, 0, 1) * np.clip(t/0.02, 0, 1)
st = np.stack([L, R], 1) * fade[:, None]
st = np.tanh(st * 1.6) / np.tanh(1.6)
st /= np.abs(st).max() / 0.89
with wave.open(os.path.join(HERE, "music_sfx.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st*32767).astype(np.int16).tobytes())
print("ok", st.shape[0]/SR)
