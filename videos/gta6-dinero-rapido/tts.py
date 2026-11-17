"""Genera la voz (Edge TTS, es-ES-AlvaroNeural) frase a frase con tiempos por palabra."""
import asyncio, json, ssl, subprocess, os
import certifi
CA = os.environ.get("CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
if os.path.exists(CA):
    certifi.where = lambda: CA
    import edge_tts.communicate as c
    c._SSL_CTX = ssl.create_default_context(cafile=CA)
import edge_tts
from script_data import LINES
VOICE, RATE, PITCH = "es-ES-AlvaroNeural", "+22%", "+3Hz"
os.makedirs("voz", exist_ok=True)

async def one(i, text):
    com = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
    words = []
    with open(f"voz/l{i}.mp3", "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"voz/l{i}.mp3","-ar","48000","-ac","1",f"voz/l{i}.wav"], check=True)
    dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"voz/l{i}.wav"]))
    return {"dur": dur, "words": words}

async def main():
    out = [await one(i, l["tts"]) for i, l in enumerate(LINES)]
    json.dump(out, open("voz/timings.json", "w"), ensure_ascii=False, indent=1)
    for i, o in enumerate(out): print(i, round(o["dur"], 2), len(o["words"]))
asyncio.run(main())
