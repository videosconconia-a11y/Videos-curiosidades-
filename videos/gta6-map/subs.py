# Writes subtitles.srt (phrase-level, from the TTS word timings) for upload to YouTube.
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
TM = json.load(open(os.path.join(HERE, "timings.json")))
def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
fix = lambda s: s.replace("G T A", "GTA").replace("P S 5", "PS5").replace("U S ", "US ")
cues = []
for seg in TM["segments"]:
    ws = seg["words"]; cur = []
    for i, w in enumerate(ws):
        cur.append(w)
        if w["w"][-1] in ".?!," and len(cur) >= 3 or len(cur) >= 7 or i == len(ws) - 1:
            cues.append((cur[0]["a"], cur[-1]["b"] + 0.1, fix(" ".join(x["w"] for x in cur)))); cur = []
with open(os.path.join(HERE, "subtitles.srt"), "w") as f:
    for i, (a, b, s) in enumerate(cues, 1):
        nb = cues[i][0] if i < len(cues) else b
        f.write(f"{i}\n{ts(a)} --> {ts(min(b, nb))}\n{s}\n\n")
print(len(cues), "cues")
