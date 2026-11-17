# Genera la narración con Piper TTS (voz masculina es_ES "davefx") y saca tiempos palabra a palabra
# con faster-whisper. Resultado: cache/voz.wav (48 kHz mono) y cache/timing.json.
import os, sys, json, wave, difflib, subprocess, urllib.request
import numpy as np
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SENTENCES, TARGET_TOTAL, LEAD_IN, GAP, VOICE_END_MAX, TIMING_FILE, norm

CACHE = os.path.join(HERE, "cache"); os.makedirs(CACHE, exist_ok=True)
VOICE = "es_ES-davefx-medium"
URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/"
SR = 48000


def get_model():
    d = os.path.join(CACHE, "piper"); os.makedirs(d, exist_ok=True)
    for ext in (".onnx", ".onnx.json"):
        p = os.path.join(d, VOICE + ext)
        if not os.path.exists(p):
            print("descargando", VOICE + ext); urllib.request.urlretrieve(URL + VOICE + ext, p)
    return os.path.join(d, VOICE + ".onnx")


def synth(voice, text, length_scale):
    from piper import SynthesisConfig
    cfg = SynthesisConfig(length_scale=length_scale, noise_scale=0.62, noise_w_scale=0.85)
    chunks = [c.audio_int16_array for c in voice.synthesize(text, syn_config=cfg)]
    a = np.concatenate(chunks).astype(np.float32) / 32768.0
    a = resample_poly(a, SR, voice.config.sample_rate).astype(np.float32)
    # recorta silencios de los extremos
    env = np.abs(a) > 0.01
    i0 = max(0, np.argmax(env) - int(0.02 * SR)); i1 = len(a) - np.argmax(env[::-1]) + int(0.06 * SR)
    return a[i0:i1]


def align(display, wwords):
    """Asigna (inicio, fin) de whisper a cada palabra del texto mostrado."""
    toks = display.split()
    nd = [norm(t).replace("6", "SEIS") for t in toks]
    nw = [norm(w[0]) for w in wwords]
    times = [None] * len(toks)
    sm = difflib.SequenceMatcher(a=nd, b=nw, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (wwords[j1 + k][1], wwords[j1 + k][2])
        elif tag == "replace" and j2 > j1:
            a, b = wwords[j1][1], wwords[j2 - 1][2]
            L = [len(x) + 1 for x in nd[i1:i2]]; tot = sum(L); t = a
            for k, l in enumerate(L):
                d = (b - a) * l / tot; times[i1 + k] = (t, t + d); t += d
    # huecos sin emparejar: interpola entre vecinos
    for i in range(len(toks)):
        if times[i] is None:
            j = i
            while j < len(toks) and times[j] is None: j += 1
            a = times[i - 1][1] if i > 0 else (wwords[0][1] if wwords else 0)
            b = times[j][0] if j < len(toks) else (wwords[-1][2] if wwords else a + 0.3 * (j - i))
            if b <= a: b = a + 0.12 * (j - i)
            n = j - i
            for k in range(n):
                times[i + k] = (a + (b - a) * k / n, a + (b - a) * (k + 1) / n)
    # monotonía
    for i in range(1, len(times)):
        s, e = times[i]
        s = max(s, times[i - 1][0] + 0.04); e = max(e, s + 0.06)
        times[i] = (s, e)
    return list(zip(toks, times))


def main():
    from piper import PiperVoice
    from faster_whisper import WhisperModel
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    voice = PiperVoice.load(get_model())
    asr = WhisperModel("small", device="cpu", compute_type="int8")
    def layout(clips):
        d = [len(c) / SR for c in clips]; n = len(d)
        latest = [0.0] * n; t = VOICE_END_MAX
        for i in range(n - 1, -1, -1):
            latest[i] = t - d[i]; t = latest[i] - GAP
        starts, t = [], LEAD_IN
        for i, s in enumerate(SENTENCES):
            st = min(max(t, s["start"] + (LEAD_IN if i == 0 else 0)), max(t, latest[i]))
            starts.append(st); t = st + d[i] + GAP
        return starts, t - GAP
    # sin huecos muertos: las frases van seguidas y se ajusta la velocidad hasta llenar ~28 s
    lo, hi = 0.80, 1.00     # nunca más lento que la velocidad natural
    best = None
    for attempt in range(7):
        ls = (lo + hi) / 2
        clips = [synth(voice, s["tts"], ls) for s in SENTENCES]
        d = [len(c) / SR for c in clips]
        end = LEAD_IN + sum(d) + GAP * (len(d) - 1)
        print(f"length_scale={ls:.3f} -> voz termina en {end:.2f} s")
        if end <= VOICE_END_MAX:
            best = (clips, ls); lo = ls
            if end > VOICE_END_MAX - 0.45: break
        else:
            hi = ls
        if hi - lo < 0.01: break
    if best is None or best[1] < 0.99 and LEAD_IN + sum(len(c) / SR for c in best[0]) + GAP * 5 < VOICE_END_MAX - 0.45:
        ls = 1.0; clips = [synth(voice, s["tts"], ls) for s in SENTENCES]
        if LEAD_IN + sum(len(c) / SR for c in clips) + GAP * (len(clips) - 1) <= VOICE_END_MAX: best = (clips, ls)
    clips, ls = best
    starts, t = [], LEAD_IN
    for c in clips:
        starts.append(t); t += len(c) / SR + GAP
    # la última frase se ancla al final para que el bucle sea limpio
    starts[-1] = max(starts[-1], VOICE_END_MAX - len(clips[-1]) / SR)
    out = np.zeros(int(TARGET_TOTAL * SR) + SR, np.float32)
    words = []; sents = []
    for si, (c, s, t) in enumerate(zip(clips, SENTENCES, starts)):
        i0 = int(t * SR); out[i0:i0 + len(c)] += c
        a16 = resample_poly(c, 16000, SR).astype(np.float32)
        segs, _ = asr.transcribe(a16, language="es", word_timestamps=True, beam_size=5,
                                 initial_prompt="GTA seis, Rockstar, Vice City.")
        ww = [(w.word.strip(), w.start, w.end) for sg in segs for w in sg.words]
        print(si, " ".join(w[0] for w in ww))
        for tok, (a, b) in align(s["display"], ww):
            words.append((round(t + a, 3), round(t + b, 3), tok, si))
        sents.append((round(t, 3), round(t + len(c) / SR, 3)))
    t = sents[-1][1]
    out = out[:int(TARGET_TOTAL * SR)]
    with wave.open(os.path.join(CACHE, "voz.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    with open(os.path.join(HERE, TIMING_FILE), "w", encoding="utf-8") as f:
        json.dump(dict(total=TARGET_TOTAL, voice_end=round(t, 3), sentences=sents, words=words),
                  f, ensure_ascii=False, indent=1)
    print("voz termina en", round(t, 2), "s")


if __name__ == "__main__":
    main()
