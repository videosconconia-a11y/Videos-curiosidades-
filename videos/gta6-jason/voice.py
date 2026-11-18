# AI voiceover with Kokoro-82M (open-weight TTS, Apache-2.0), American male voice.
# Writes voice.wav (24 kHz mono) and timings.json (segment + word timestamps).
import json, os, sys, re
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SEGMENTS

VOICE = os.environ.get("VOICE", "af_bella")  # warm, energetic US female (Kokoro grade A-)
SPEED = float(os.environ.get("SPEED", "1.08"))
SR = 24000
LEAD = 0.12   # silence before the first word

from kokoro import KPipeline
pipe = KPipeline(lang_code="a")

def norm(w):
    return re.sub(r"[^a-z0-9\-]", "", w.lower())

audio, segs, t = [np.zeros(int(LEAD * SR), np.float32)], [], LEAD
for s in SEGMENTS:
    chunks, words, off = [], [], 0.0
    for res in pipe(s["say"], voice=VOICE, speed=SPEED):
        a = res.audio.numpy() if hasattr(res.audio, "numpy") else np.asarray(res.audio)
        for tok in (res.tokens or []):
            if tok.start_ts is None: continue
            txt = tok.text
            if not norm(txt):  # punctuation -> attach to previous word
                if words: words[-1]["w"] += txt
                continue
            words.append(dict(w=txt, a=off + tok.start_ts, b=off + (tok.end_ts or tok.start_ts + 0.2)))
        chunks.append(a.astype(np.float32)); off += len(a) / SR
    seg = np.concatenate(chunks)
    # trim the model's lead/tail silence; pauses are controlled by `pause`
    c0 = max(0.0, words[0]["a"] - 0.04); c1 = min(len(seg) / SR, words[-1]["b"] + 0.08)
    seg = seg[int(c0 * SR):int(c1 * SR)]
    fade = np.minimum(1, np.minimum(np.arange(len(seg)), len(seg) - np.arange(len(seg))) / (0.006 * SR))
    seg = seg * fade
    for w in words:
        w["a"] = round(t + w["a"] - c0, 3); w["b"] = round(t + w["b"] - c0, 3)
    start = t; t += len(seg) / SR; end = t
    audio.append(seg.astype(np.float32))
    audio.append(np.zeros(int(s["pause"] * SR), np.float32)); t += s["pause"]
    segs.append(dict(id=s["id"], a=round(start, 3), b=round(end, 3), next=round(t, 3), words=words))
    print(f"{s['id']:6} {start:6.2f}-{end:6.2f}  {len(words)} words", flush=True)

wav = np.concatenate(audio)
sf.write(os.path.join(HERE, "voice.wav"), wav, SR)
json.dump(dict(total=round(t + 0.1, 3), segments=segs), open(os.path.join(HERE, "timings.json"), "w"), indent=1)
print("total", round(t, 2))
