# Guion de "Hinterkaifeck" (Baviera, Alemania, 1922) — caso real sin resolver.
# Una entrada por FRASE: (texto para la voz, {palabras clave en rojo}, [planos], pausa_después_s, estilo)
# estilo "n" = narrador · "c" = cita de la carta (voz más lenta y grave, con eco)
# Los tiempos de cada palabra salen de la voz (timings.json, generado por voice.py).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

LINES = [
    ("Unas huellas en la nieve llegaban hasta esta granja.", {"HUELLAS", "GRANJA"}, ["tracks_farm"], 0.25, "n"),
    ("Pero ninguna volvía.", {"NINGUNA"}, ["tracks_close"], 0.5, "n"),
    ("Alemania, 1922. Una granja aislada junto al bosque: Hinterkaifeck.", {"ALEMANIA", "HINTERKAIFECK"}, ["farm_wide"], 0.15, "n"),
    ("Allí vive una familia: los abuelos, su hija viuda y sus dos nietos pequeños.", {"FAMILIA", "NIETOS"}, ["family_lamp"], 0.15, "n"),
    ("Unos días antes del crimen, el abuelo encuentra esas huellas.", {"HUELLAS"}, ["lantern_tracks"], 0.15, "n"),
    ("Por la noche, oyen pasos en el desván.", {"PASOS", "DESVÁN"}, ["attic"], 0.25, "n"),
    ("Pero no encuentran a nadie.", {"NADIE"}, ["attic_lantern"], 0.2, "n"),
    ("Y aparece un periódico de Múnich que nadie en la casa ha comprado.", {"PERIÓDICO", "NADIE"}, ["newspaper"], 0.15, "n"),
    ("La criada anterior se había marchado meses antes, diciendo que en esa casa se oían cosas.", {"CRIADA", "OÍAN"}, ["maid_leaving"], 0.3, "n"),
    ("Antes de seguir: ¿tú dormirías una noche allí? Escribe uno si te quedas, y dos si te vas.", {"DORMIRÍAS", "UNO", "DOS"}, ["poll"], 0.4, "n"),
    ("Ellos se quedaron.", {"QUEDARON"}, ["farm_night"], 0.3, "n"),
    ("El 31 de marzo llega una criada nueva.", {"NUEVA"}, ["new_maid"], 0.15, "n"),
    ("Esa misma noche, alguien mata a las seis personas de la granja.", {"SEIS"}, ["barn_door"], 0.5, "n"),
    ("Pero lo más escalofriante viene después.", {"ESCALOFRIANTE"}, ["window_dark"], 0.2, "n"),
    ("Durante días, sale humo de la chimenea.", {"HUMO", "CHIMENEA"}, ["chimney"], 0.15, "n"),
    ("Alguien da de comer a los animales.", {"ANIMALES"}, ["stable"], 0.15, "n"),
    ("El asesino se queda a vivir en la casa.", {"ASESINO", "VIVIR"}, ["kitchen_killer"], 0.4, "n"),
    ("Cuatro días después, los vecinos entran y encuentran los cuerpos.", {"VECINOS", "CUERPOS"}, ["neighbors"], 0.2, "n"),
    ("La policía investigó el caso durante décadas, pero nunca encontró al culpable.", {"DÉCADAS", "NUNCA"}, ["case_file"], 0.2, "n"),
    ("Poco después, derribaron la granja.", {"DERRIBARON"}, ["field"], 0.15, "n"),
    ("Hoy, más de cien años después, sigue sin resolver.", {"CIEN", "RESOLVER"}, ["memorial"], 0.3, "n"),
    ("Así que dime: ¿quién estaba en el desván?", {"QUIÉN", "DESVÁN"}, ["end_card"], 2.2, "n"),
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
MERGE = [("MIL NOVECIENTOS VEINTIDÓS", "1922"), ("TREINTA Y UNO", "31")]
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
