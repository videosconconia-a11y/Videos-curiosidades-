# Original chiptune/retro score that changes per console (all synthesised): Atari harsh pulse beeps, Game Boy pulse
# arpeggios, NES square lead + triangle bass + noise drums, PS1 lush pad + breakbeat, N64 bouncy synth, PS5 cinematic boom.
# SFX: TV static on each channel change, power-on, "30 FPS" stamp thud. Voice ducking.
import os, sys, json
import numpy as np
from scipy.signal import butter, sosfilt, lfilter, resample_poly
import soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = [sys.argv[0], "none"]
import render as RD
SR = 48000; TOTAL = RD.TOTAL; N = int(SR * TOTAL); t = np.arange(N) / SR; rng = np.random.default_rng(4)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
M = np.zeros(N); FX = np.zeros(N)
def put(buf, x, at, g=1.0):
    i0 = int(at * SR)
    if i0 < 0: x = x[-i0:]; i0 = 0
    if i0 >= N: return
    k = min(len(x), N - i0); buf[i0:i0 + k] += x[:k] * g
def sq(f, d, duty=.5):
    n = int(d * SR); tt = np.arange(n) / SR; x = np.where((f * tt) % 1 < duty, 1.0, -1.0); return x * np.minimum(1, (n - np.arange(n)) / 300)
def tri(f, d): n = int(d * SR); tt = np.arange(n) / SR; return 2 * np.abs(2 * ((f * tt) % 1) - 1) - 1
def noise(d, dec=30): n = int(d * SR); return rng.uniform(-1, 1, n) * np.exp(-np.arange(n) / SR * dec)
MEL = [72, 76, 79, 84, 83, 79, 76, 74]; BASS = [48, 48, 45, 45, 41, 41, 43, 43]
def section(con, a, b):
    bpm = {"intro": 100, "atari": 120, "gameboy": 140, "nes": 150, "ps1": 96, "n64": 128, "ps5": 80, "outro": 140}[con]; st = 60 / bpm / 2
    k = 0; x = a
    while x < b:
        m = MEL[k % 8] + (0 if con != "atari" else -12); bm = BASS[k % 8]
        if con == "atari": put(M, sq(mtof(m) * (1 + .03 * rng.uniform(-1, 1)), st * .9, .5), x, .09)
        elif con == "gameboy":
            for j, o in enumerate((0, 4, 7)): put(M, sq(mtof(m + o), st / 3, .25), x + j * st / 3, .06)
            put(M, sq(mtof(bm), st, .5) * .5, x, .07)
        elif con == "nes":
            put(M, sq(mtof(m), st * .8, .25), x, .07); put(M, tri(mtof(bm), st), x, .12)
            if k % 2 == 0: put(M, noise(.06, 60), x, .15)
        elif con == "ps1":
            if k % 8 == 0:
                d = st * 8; n = int(d * SR); tt = np.arange(n) / SR
                pad = sum(np.sin(2 * np.pi * mtof(q) * tt) for q in (60, 64, 67, 71)) * np.minimum(1, tt / .5) * np.minimum(1, (d - tt) / .5)
                put(M, lp(pad, 1500), x, .05)
            if k % 4 == 0: put(M, np.sin(2 * np.pi * np.cumsum(50 + 100 * np.exp(-np.arange(int(.3 * SR)) / SR * 30)) / SR) * np.exp(-np.arange(int(.3 * SR)) / SR * 8), x, .5)
            if k % 4 == 2: put(M, hp(noise(.15, 25), 1500), x, .35)
        elif con == "n64":
            put(M, lp(sq(mtof(m), st * .7, .4), 2500), x, .07); put(M, np.sin(2 * np.pi * mtof(bm) * np.arange(int(st * SR)) / SR) * np.exp(-np.arange(int(st * SR)) / SR * 6), x, .2)
        elif con in ("ps5",):
            if k == 0:
                n = int(3 * SR); tt = np.arange(n) / SR
                put(M, np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-tt * 5)) / SR) * np.exp(-tt * 1.5), x, .8)
                put(M, lp(sum(np.sin(2 * np.pi * mtof(q) * tt) for q in (50, 57, 62, 66)) * np.exp(-tt * .6), 1800), x, .07)
        elif con in ("intro", "outro"):
            put(M, sq(mtof(m), st * .6, .25), x, .05)
            if k % 2 == 0: put(M, tri(mtof(bm), st), x, .1)
        x += st; k += 1
for a, b, con, sid in RD.WIN: section(con, a, b)
for a, b, con, sid in RD.WIN[1:]: put(FX, hp(noise(.2, 8), 800), a - .02, .25)
put(FX, hp(noise(.8, 3), 600), 0, .2)
tw = RD.word_time("ps5", "thirty"); n = int(.5 * SR); tt = np.arange(n) / SR
put(FX, np.sin(2 * np.pi * np.cumsum(60 + 100 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9), tw - .1, .7)
v, vsr = sf.read(os.path.join(HERE, "voice.wav")); v = resample_poly(v, SR, vsr)
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 90); voice = voice + .25 * hp(voice, 3000)
voice = voice / np.abs(voice).max() * .9; voice = np.tanh(voice * 1.8) / np.tanh(1.8)
envv = lfilter([1 - .9993], [1, -.9993], np.abs(voice))
act = np.clip(envv / (np.percentile(envv[envv > 1e-4], 60) + 1e-9), 0, 1)
duck = np.clip(lfilter([.002], [1, -.998], act) * 1.4, 0, 1)
out = M * (1 - .65 * duck) * .8 + FX * .8 + voice
fade = np.clip((TOTAL - t) / .3, 0, 1) * np.clip(t / .01, 0, 1)
out = np.tanh(out * fade * 1.2) / np.tanh(1.2); out /= np.abs(out).max() / .95
sf.write(os.path.join(HERE, "mix.wav"), np.stack([out, out], 1).astype(np.float32), SR, subtype="PCM_24"); print("mix ok", round(TOTAL, 2))
