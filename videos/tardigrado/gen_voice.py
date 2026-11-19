# Voz en castellano de España (Microsoft Edge neural TTS, es-ES-AlvaroNeural: masculina, tono medio, natural)
# con la marca de tiempo de cada palabra para sincronizar los subtítulos.
import os, sys, ssl, json, asyncio, subprocess
import edge_tts, edge_tts.communicate as ec
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES
CA = "/root/.ccr/ca-bundle.crt"            # CA del proxy del entorno (si existe)
if os.path.exists(CA): ec._SSL_CTX = ssl.create_default_context(cafile=CA)

VOICE = os.environ.get("VOICE", "es-ES-AlvaroNeural")
RATE = os.environ.get("RATE", "+4%")
OUT = os.path.join(HERE, "assets", "voice"); os.makedirs(OUT, exist_ok=True)

async def one(i, text):
    mp3, js = os.path.join(OUT, f"s{i:02}.mp3"), os.path.join(OUT, f"s{i:02}.json")
    if os.path.exists(js) and not os.environ.get("FORCE"): return
    words = []
    c = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append(dict(w=ch["text"], a=ch["offset"] / 1e7, b=(ch["offset"] + ch["duration"]) / 1e7))
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3]))
    json.dump(dict(text=text, dur=dur, words=words), open(js, "w"), ensure_ascii=False, indent=1)
    print(i, f"{dur:.2f}s", len(words), "palabras", flush=True)

async def main():
    for i, s in enumerate(SCENES): await one(i, s["text"])
asyncio.run(main())
