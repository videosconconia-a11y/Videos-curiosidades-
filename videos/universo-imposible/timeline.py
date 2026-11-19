# Construye la línea de tiempo real a partir de la voz generada:
# inicio de cada escena, palabras con tiempo global, bloques de subtítulos y planos de imagen.
import os, json, re, unicodedata
from script_data import SCENES, HIGHLIGHT
HERE = os.path.dirname(os.path.abspath(__file__))
LEAD, GAP, TAIL = 0.15, float(os.environ.get('GAP', 0.22)), 1.2   # silencio inicial, pausa entre escenas, cola final

def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-zñ0-9]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))

def load():
    scenes, words, t = [], [], LEAD
    for i, s in enumerate(SCENES):
        d = json.load(open(os.path.join(HERE, "assets", "voice", f"s{i:02}.json")))
        w0 = d["words"][0]["a"]; end = d["words"][-1]["b"]
        start = t - w0                       # desplazamiento del archivo de audio
        scenes.append(dict(i=i, audio_at=start, a=t, b=t + end - w0, file=f"s{i:02}.mp3"))
        toks = s["text"].replace("…", "… ").split(); ti = 0
        for w in d["words"]:
            punct = False                    # ¿la palabra termina en signo de puntuación en el guion?
            for tj in range(ti, min(ti + 4, len(toks))):
                if norm(w["w"]) and norm(w["w"]) in norm(toks[tj]):
                    punct = bool(re.search(r"[.,:;?!…]$", toks[tj])) and norm(toks[tj]).endswith(norm(w["w"]))
                    ti = tj + 1; break
            words.append(dict(w=w["w"], a=start + w["a"], b=start + w["b"], scene=i, p=punct))
        t = t + (end - w0) + GAP
    total = scenes[-1]["b"] + TAIL
    # cada escena visual dura hasta que empieza la siguiente
    for k, sc in enumerate(scenes):
        sc["va"] = 0.0 if k == 0 else sc["a"] - GAP / 2
        sc["vb"] = total if k == len(scenes) - 1 else scenes[k + 1]["a"] - GAP / 2
    return scenes, words, total

def captions(words, maxw=3, maxc=16):
    """Bloques de 1-3 palabras; se corta en signos de puntuación. Devuelve (a, b, [(palabra, a, b, resaltar)])."""
    out, cur = [], []
    def flush():
        if cur: out.append(cur.copy()); cur.clear()
    for k, w in enumerate(words):
        if cur and (len(cur) >= maxw or sum(len(x["w"]) + 1 for x in cur) + len(w["w"]) > maxc or w["scene"] != cur[-1]["scene"]):
            flush()
        cur.append(w)
        if w.get("p") or re.search(r"[.,:;?!…]$", w["w"]): flush()
    flush()
    blocks = []
    for k, g in enumerate(out):
        a = g[0]["a"] - 0.05
        b = out[k + 1][0]["a"] - 0.05 if k + 1 < len(out) else g[-1]["b"] + 0.6
        b = min(b, g[-1]["b"] + 0.7)
        blocks.append((a, b, [(x["w"].rstrip(".,;:"), x["a"], x["b"], norm(x["w"]) in HIGHLIGHT) for x in g]))
    return blocks

def shots(scenes, words):
    """Reparte las imágenes de cada escena cortando en la palabra más cercana al reparto equitativo."""
    out = []
    for sc in scenes:
        imgs = [n for n, _ in SCENES[sc["i"]]["images"]]
        ws = [w for w in words if w["scene"] == sc["i"]]
        cuts = [sc["va"]]
        for j in range(1, len(imgs)):
            target = sc["a"] + (sc["b"] - sc["a"]) * j / len(imgs)
            cuts.append(min(ws, key=lambda w: abs(w["a"] - target))["a"] - 0.05)
        cuts.append(sc["vb"])
        for j, n in enumerate(imgs):
            out.append((cuts[j], cuts[j + 1], n))
    return out

def write_srt(path):
    scenes, words, total = load()
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, ws) in enumerate(captions(words), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{' '.join(w[0] for w in ws)}\n\n")

if __name__ == "__main__":
    sc, w, T = load()
    print("total", round(T, 2))
    for s in shots(sc, w): print(f"{s[0]:6.2f} {s[1]:6.2f} {s[1]-s[0]:4.1f} {s[2]}")
    print(len(captions(w)), "bloques de subtítulos")
