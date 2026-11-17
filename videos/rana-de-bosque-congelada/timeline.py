"""Línea de tiempo del vídeo a partir de la narración real (tiempos por palabra de la voz).

Cada frase de narracion.py se sintetiza por separado (tts.py) y se coloca en el tiempo con la pausa
indicada. De ahí salen: el montaje de la voz, los subtítulos palabra a palabra y el inicio de cada plano.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
START = 0.30          # la voz empieza casi al instante (gancho en los 3 primeros segundos)
TAIL = 1.6            # cola final (música + cartel)
PAD_IN, PAD_OUT = 0.04, 0.10

def _punct(text, words):
    """Devuelve las palabras con la puntuación del texto original (la voz no la incluye)."""
    toks = text.split(); out = []; j = 0
    for (w0, w1, w) in words:
        k = j
        while k < len(toks) and _n(toks[k]) != _n(w): k += 1
        if k < len(toks): out.append((w0, w1, toks[k])); j = k + 1
        else: out.append((w0, w1, w))
    return out

def _n(s): return re.sub(r"[¿?¡!.,:;…]", "", s).lower()

def load():
    clips = json.load(open(os.path.join(HERE, "voz", "words.json"), encoding="utf-8"))
    t = START; sentences = []
    for i, c in enumerate(clips):
        a = max(0.0, c["words"][0][0] - PAD_IN); b = min(c["dur"], c["words"][-1][1] + PAD_OUT)
        words = [(t + w0 - a, t + w1 - a, txt) for (w0, w1, txt) in _punct(c["text"], c["words"])]
        sentences.append(dict(i=i, text=c["text"], clip_in=a, clip_out=b, start=t, end=t + (b - a), words=words))
        t += (b - a) + c["pause"]
    total = sentences[-1]["end"] + TAIL
    return sentences, total

SENTENCES, TOTAL = load()

def word_time(i, k=0):
    """Inicio de la palabra k de la frase i (k puede ser texto: primera palabra que lo contiene)."""
    ws = SENTENCES[i]["words"]
    if isinstance(k, str):
        k = next(j for j, w in enumerate(ws) if k.lower() in w[2].lower())
    return ws[k][0]

# ------------------------------------------------------------------ subtítulos
# Sustituciones para mostrar cifras (la voz las dice en palabras).
SUBS = [
    (["sesenta", "y", "cinco", "por", "ciento"], "65 %"),
    (["doscientos"], "200"),
    (["dieciocho", "grados", "bajo", "cero"], "−18 °C"),
]
# Palabras resaltadas en amarillo (raíces, sin tildes no importa: se comparan en minúsculas)
HIGHLIGHT = ["congelad", "meses", "corazón", "detenido", "vida", "rana de bosque", "bosque", "norteamérica",
             "alaska", "polar", "ártico", "hielo", "65 %", "detiene", "respirar", "muerta", "no lo está",
             "hígado", "glucosa", "200", "anticongelante", "fuera", "dentro", "sobreviven", "días",
             "−18 °c", "primavera", "derrite", "latir", "salta", "increíble", "invierno", "calor", "escapar"]

def _norm(s): return re.sub(r"[¿?¡!.,:;…]", "", s).lower()

def caption_words():
    """Lista de (inicio, fin, texto_mostrado, frase) con sustituciones aplicadas."""
    out = []
    for s in SENTENCES:
        ws = s["words"]; j = 0
        while j < len(ws):
            hit = None
            for seq, rep in SUBS:
                if [_norm(w[2]) for w in ws[j:j + len(seq)]] == seq:
                    hit = (len(seq), rep); break
            if hit:
                n, rep = hit; out.append((ws[j][0], ws[j + n - 1][1], rep, s["i"])); j += n
            else:
                out.append((ws[j][0], ws[j][1], ws[j][2], s["i"])); j += 1
    return out

FUNC = {"a", "la", "el", "de", "del", "que", "y", "en", "los", "las", "por", "con", "se", "su", "sus", "un", "una", "lo", "al", "hasta", "no"}

def caption_chunks(max_chars=16, max_words=3):
    """Agrupa palabras en bloques cortos estilo TikTok; corta en signos de puntuación."""
    words = caption_words(); chunks = []; cur = []
    def flush():
        if cur: chunks.append(cur.copy()); cur.clear()
    for k, w in enumerate(words):
        if cur and (cur[-1][3] != w[3] or len(" ".join(x[2] for x in cur + [w])) > max_chars or len(cur) >= max_words):
            carry = []
            if cur[-1][3] == w[3]:
                while len(cur) > 1 and _norm(cur[-1][2]) in FUNC: carry.insert(0, cur.pop())
            flush(); cur.extend(carry)
        cur.append(w)
        if re.search(r"[.,:;…?!]$", w[2]) or w[2] in ("65 %",):
            flush()
    flush()
    out = []
    for n, c in enumerate(chunks):
        a = c[0][0]; b = c[-1][1] + 0.25
        if n + 1 < len(chunks): b = min(b + 0.35, chunks[n + 1][0][0])
        out.append(dict(start=a, end=b, words=[(w[0], w[1], w[2]) for w in c]))
    return out

def is_highlight(text, chunk_text):
    t = _norm(text)
    if not t: return False
    for h in HIGHLIGHT:
        if " " in h:
            if h in _norm(chunk_text) and t in h.split(): return True
        elif t.startswith(h) or t == h: return True
    return False

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, c in enumerate(caption_chunks(), 1):
            f.write(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{' '.join(w[2] for w in c['words'])}\n\n")

if __name__ == "__main__":
    for s in SENTENCES: print(f"{s['start']:6.2f}-{s['end']:6.2f}  {s['text']}")
    print("TOTAL", round(TOTAL, 2))
    for c in caption_chunks()[:12]: print(round(c["start"], 2), [w[2] for w in c["words"]])
