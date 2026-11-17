# Guion de "El Vigilante" (Westfield, Nueva Jersey, 2014) — caso real sin resolver.
# Una entrada por FRASE: (texto para la voz, {palabras clave en rojo}, [planos], pausa_después_s, estilo)
# estilo "n" = narrador · "c" = cita de la carta (voz más lenta y grave, con eco)
# Los tiempos de cada palabra salen de la voz (timings.json, generado por voice.py).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

LINES = [
    ("Te compras la casa de tus sueños.", {"SUEÑOS"}, ["dream_house"], 0.1, "n"),
    ("Y tres días después, te llega esta carta.", {"CARTA"}, ["mailbox"], 0.25, "n"),
    ("Querido nuevo vecino del seiscientos cincuenta y siete de Boulevard. Permíteme darte la bienvenida al barrio.",
     {"657", "BIENVENIDA"}, ["letter1"], 0.3, "c"),
    ("Nueva Jersey, junio de 2014. Una familia con niños pequeños acaba de pagar más de un millón trescientos mil dólares por esta casa.",
     {"JERSEY", "NIÑOS", "MILLÓN"}, ["house_day", "price"], 0.15, "n"),
    ("Pero la carta sigue.", {"SIGUE"}, ["letter_close"], 0.2, "n"),
    ("¿Habéis traído la sangre joven que pedí?", {"SANGRE", "JOVEN"}, ["kids_room"], 0.35, "c"),
    ("¿Sabéis lo que hay dentro de las paredes del seiscientos cincuenta y siete de Boulevard?", {"PAREDES"}, ["wall"], 0.3, "c"),
    ("Dice que su padre y su abuelo ya vigilaron esa casa antes que él. Y que ahora le toca a él.",
     {"PADRE", "ABUELO", "VIGILARON", "TOCA"}, ["generations"], 0.2, "n"),
    ("Cientos de coches pasan cada día por delante. Quizá yo esté en uno.", {"COCHES", "UNO"}, ["street_cars"], 0.2, "c"),
    ("Mira todas las ventanas que se ven desde la casa. Quizá yo esté en una.", {"VENTANAS", "UNA"}, ["windows_watch"], 0.25, "c"),
    ("Y firma así: Que empiece la fiesta. El Vigilante.", {"FIESTA", "VIGILANTE"}, ["signature"], 0.4, "n"),
    ("Antes de seguir: ¿tú te quedarías en esa casa? Escribe uno si te quedas, y dos si te vas.",
     {"QUEDARÍAS", "UNO", "DOS"}, ["poll"], 0.4, "n"),
    ("Llegaron más cartas. En una decía:", {"MÁS"}, ["letters_pile"], 0.1, "n"),
    ("Pedí a los antiguos dueños que me trajeran sangre joven. Y parece que me han hecho caso.",
     {"SANGRE", "JOVEN", "CASO"}, ["letter2"], 0.3, "c"),
    ("La familia nunca llegó a vivir allí.", {"NUNCA"}, ["house_empty"], 0.15, "n"),
    ("La policía lo investigó, pero nunca descubrió quién era.", {"POLICÍA", "NUNCA"}, ["case_file"], 0.15, "n"),
    ("En 2019 vendieron la casa, perdiendo unos cuatrocientos mil dólares.", {"VENDIERON", "CUATROCIENTOS"}, ["sold"], 0.2, "n"),
    ("Y el Vigilante sigue sin tener nombre.", {"VIGILANTE", "NOMBRE"}, ["watcher_street"], 0.3, "n"),
    ("¿Quién crees que era? Déjame tu teoría en los comentarios. Las mejores, las leo en la parte dos.",
     {"TEORÍA", "COMENTARIOS", "PARTE"}, ["end_card"], 1.4, "n"),
]

LEAD = 0.15
_tj = os.path.join(HERE, "timings.json")
TIM = json.load(open(_tj)) if os.path.exists(_tj) else [{"dur": len(l[0]) / 14, "words": []} for l in LINES]

SCENES = []   # (inicio, fin, texto, claves, planos, inicio_voz, dur_voz, palabras[(t0,t1,txt)])
_t = 0.0
for i, (n, keys, s, pause, sty) in enumerate(LINES):
    a = _t; v0 = a + (LEAD if i == 0 else 0.05); b = v0 + TIM[i]["dur"] + pause
    words = [(v0 + w0, v0 + w0 + wd, wt) for (w0, wd, wt) in TIM[i]["words"]]
    SCENES.append((round(a, 3), round(b, 3), n, keys, s, v0, TIM[i]["dur"], words)); _t = b
TOTAL = round(_t, 3)

def scene_start(name):
    for sc in SCENES:
        if name in sc[4]: return sc[0]

def _clean(w): return w.upper().strip("¿?¡!.,:;«»\"")

# Cifras que la voz dice con palabras y el subtítulo enseña con números
MERGE = [("SEISCIENTOS CINCUENTA Y SIETE", "657"), ("UN MILLÓN TRESCIENTOS MIL DÓLARES", "1,3 MILLONES $"),
         ("CUATROCIENTOS MIL DÓLARES", "400.000 $")]
def _merge(words):
    out, i = [], 0
    while i < len(words):
        for src, dst in MERGE:
            n = len(src.split())
            if " ".join(_clean(w[2]) for w in words[i:i + n]) == src:
                out.append((words[i][0], words[i + n - 1][1], dst, words[i + n - 1][3], True)); i += n; break
        else:
            out.append(words[i]); i += 1
    return out

def caption_timeline(max_chars=16):
    """Agrupa las palabras de la voz en bloques cortos. Cada bloque: (inicio, fin, [(palabra, t0, clave)])."""
    out = []
    for (a, b, _n, keys, _s, v0, vd, words) in SCENES:
        # ¿la palabra va seguida de puntuación en el guion? -> el bloque se corta ahí
        brk, pos, low = set(), 0, _n.lower()
        for j, w in enumerate(words):
            k = low.find(w[2].lower(), pos); w = tuple(w)
            if k < 0: continue
            pos = k + len(w[2])
            if low[pos:pos + 1] in (".", "?", ":", ",", "!"): brk.add(j)
            if low[pos:pos + 1] == "?": words[j] = (w[0], w[1], w[2] + "?")
            if k > 0 and low[k - 1] == "¿": words[j] = (words[j][0], words[j][1], "¿" + words[j][2])
        words = [tuple(w) + (j in brk,) for j, w in enumerate(words)]
        words = _merge(words)
        groups, cur = [], []
        for w in words:
            txt = w[2].upper()
            if cur and (sum(len(x[2]) + 1 for x in cur) + len(txt) > max_chars or cur[-1][3]):
                groups.append(cur); cur = []
            cur.append(w)
        if cur: groups.append(cur)
        for k, g in enumerate(groups):
            t0 = g[0][0]; t1 = groups[k + 1][0][0] if k + 1 < len(groups) else b
            out.append((t0, t1, [(w[2].upper(), w[0], len(w) > 4 or _clean(w[2]) in keys) for w in g]))
    return out

def shot_timeline():
    out = []
    for (a, b, _n, _k, shots, v0, vd, words) in SCENES:
        if len(shots) == 1: out.append((a, b, shots[0])); continue
        cut = min((w[0] for w in words[1:]), key=lambda x: abs(x - (a + b) / 2))
        out += [(a, cut, shots[0]), (cut, b, shots[1])]
    return out

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, ws) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{' '.join(w[0] for w in ws)}\n\n")
