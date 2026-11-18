# Genera la locución (voz neuronal es-ES de Microsoft vía edge-tts) escena a escena,
# con marcas de tiempo por palabra, y la une en voice.wav + voice_timing.json.
import asyncio, json, os, ssl, subprocess, sys
import edge_tts, edge_tts.communicate as _c

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import SCENES, VOICE, RATE

# El proxy de salida re-firma TLS: usamos su paquete de CA (si existe) en lugar del de certifi.
CA = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    _c._SSL_CTX = ssl.create_default_context(cafile=CA)

LEAD, GAP, TAIL = 0.15, 0.22, 1.4   # silencio inicial, pausa entre escenas, colita final
SR = 48000

async def synth(text, mp3):
    com = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"text": ch["text"], "start": ch["offset"] / 1e7, "end": (ch["offset"] + ch["duration"]) / 1e7})
    # Recupera la puntuación del texto original (el motor la quita)
    cur = 0
    for w in words:
        k = text.find(w["text"], cur)
        if k < 0: continue
        a, b = k, k + len(w["text"])
        while a > 0 and text[a - 1] in "¿¡": a -= 1
        while b < len(text) and text[b] in ",.:;?!…": b += 1
        w["text"] = text[a:b]; cur = b
    return words

def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))

async def main():
    os.makedirs(os.path.join(HERE, "tmp_voice"), exist_ok=True)
    scenes = []; t = LEAD; parts = []
    for i, (text, _shots) in enumerate(SCENES):
        mp3 = os.path.join(HERE, "tmp_voice", f"s{i:02}.mp3"); wav = mp3[:-4] + ".wav"
        words = await synth(text, mp3)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", wav], check=True)
        d = dur(wav)
        scenes.append({"start": round(t - (LEAD if i == 0 else GAP / 2), 3), "voice_start": round(t, 3), "voice_end": round(t + d, 3),
                       "words": [{"text": w["text"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in words]})
        parts.append((t, wav)); t += d + GAP
    total = round(t - GAP + TAIL, 3)
    for i, s in enumerate(scenes):
        s["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
    scenes[0]["start"] = 0.0
    # Mezcla de todos los trozos en su sitio
    inputs = []; filt = []
    for k, (st, wav) in enumerate(parts):
        inputs += ["-i", wav]; filt.append(f"[{k}:a]adelay={int(st*1000)}|{int(st*1000)}[a{k}]")
    filt.append("".join(f"[a{k}]" for k in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{total}[out]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]",
                    "-ar", str(SR), "-ac", "1", os.path.join(HERE, "voice.wav")], check=True)
    with open(os.path.join(HERE, "voice_timing.json"), "w", encoding="utf-8") as f:
        json.dump({"total": total, "scenes": scenes}, f, ensure_ascii=False, indent=1)
    print("voz ok", total, "s")

asyncio.run(main())
