"""Sintetiza la narración frase a frase con una voz neural de castellano peninsular (es-ES-AlvaroNeural)
y guarda los tiempos de cada palabra en voz/words.json (usados para subtítulos y montaje)."""
import ssl, asyncio, json, os, sys, subprocess
import edge_tts, edge_tts.communicate as c
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from narracion import NARR
CA = "/root/.ccr/ca-bundle.crt"          # proxy del entorno en la nube; en local se usa el certificado normal
if os.path.exists(CA): c._SSL_CTX = ssl.create_default_context(cafile=CA)
VOICE, RATE, PITCH = "es-ES-AlvaroNeural", "+5%", "-3Hz"
OUT = os.path.join(HERE, "voz")

async def one(i, text):
    com = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
    words = []; path = os.path.join(OUT, f"{i:02d}.mp3")
    with open(path, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))
    return dict(text=text, words=words, dur=d)

async def main():
    os.makedirs(OUT, exist_ok=True); out = []
    for i, (t, p) in enumerate(NARR):
        r = await one(i, t); r["pause"] = p; out.append(r); print(i, round(r["dur"], 2), t)
    json.dump(out, open(os.path.join(OUT, "words.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    asyncio.run(main())
