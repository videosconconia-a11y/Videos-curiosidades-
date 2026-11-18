# Guion del vídeo "GTA 6: ya hay gente jugando (y tú todavía no)"
# Cada escena: (narración, [planos]). Los tiempos salen de la locución real (voice.py -> voice_timing.json).
# Plano: (imagen en img/, foco_x 0..1, zoom inicial, zoom final, superposición)
# Superposiciones: None | ("stat", "TEXTO GRANDE", "texto pequeño") | ("clocks", [(lugar, hora), ...]) | ("end",)
# En los subtítulos, las palabras de HIGHLIGHT salen en amarillo.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = "es-ES-AlvaroNeural"
RATE = "+12%"

SCENES = [
    ("Ahora mismo ya hay gente jugando a GTA 6… y tú todavía no. Te explico por qué.",
     [("pareja_coche", 0.35, 1.25, 1.10, ("stat", "YA SE JUEGA", "en otra parte del mundo")),
      ("gasolinera", 0.62, 1.05, 1.20, None)]),
    ("Rockstar lo ha confirmado: GTA 6 sale el diecinueve de noviembre, a medianoche hora local, en PlayStation 5 y Xbox Series.",
     [("poster_fecha", 0.66, 1.0, 1.12, ("stat", "19 NOV", "00:00 · hora local")),
      ("hotel", 0.50, 1.15, 1.0, ("stat", "PS5 · XBOX", "Series X|S"))]),
    ("Hora local significa que se desbloquea país por país, según su reloj. Y el primero en llegar a medianoche es Nueva Zelanda.",
     [("ciudad_aerea", 0.45, 1.0, 1.18, None),
      ("noche_ciudad", 0.50, 1.15, 1.0, ("stat", "NUEVA ZELANDA", "el primer país en jugar"))]),
    ("Allí llegó a las doce del mediodía, hora peninsular. Doce horas antes que tú.",
     [("barco", 0.45, 1.05, 1.22, ("clocks", [("NUEVA ZELANDA", "00:00"), ("ESPAÑA", "12:00")])),
      ("cheetah", 0.55, 1.2, 1.05, ("stat", "12 HORAS", "de ventaja"))]),
    ("En la península podrás jugar a las doce de la noche. En Canarias, una hora después.",
     [("neon", 0.50, 1.0, 1.15, ("clocks", [("PENÍNSULA", "00:00")])),
      ("taxi", 0.45, 1.15, 1.0, ("clocks", [("PENÍNSULA", "00:00"), ("CANARIAS", "01:00")]))]),
    ("Y ojo: pide hasta doscientos doce gigas libres. La precarga está abierta desde el diez de noviembre si lo reservaste. Si aún no lo has precargado, hazlo ya, o a medianoche te tocará esperar.",
     [("coche_rojo", 0.40, 1.0, 1.15, ("stat", "212 GB", "de espacio libre")),
      ("keyart_preload", 0.50, 1.15, 1.0, ("stat", "PRECARGA", "abierta desde el 10 nov")),
      ("lucia", 0.42, 1.0, 1.18, ("bar", "DESCARGANDO…")),]),
    ("¿Y en PC? De momento, a esperar: Rockstar no ha anunciado versión para ordenador.",
     [("jason", 0.52, 1.25, 1.05, ("stat", "¿Y EN PC?", "")),
      ("palmeras", 0.45, 1.0, 1.15, ("stat", "PC", "sin fecha anunciada"))]),
    ("Así que dime: ¿te quedas despierto a las doce… o lo empiezas mañana con calma?",
     [("poster_collage", 0.50, 1.0, 1.12, None),
      ("keyart_preload", 0.50, 1.25, 1.1, ("end",))]),
]

HIGHLIGHT = {"GTA", "6", "6…", "ROCKSTAR", "19", "DIECINUEVE", "MEDIANOCHE", "NUEVA", "ZELANDA", "DOCE", "CANARIAS",
             "212", "DOSCIENTOS", "GIGAS", "PRECARGA", "PC", "DESPIERTO", "PS5", "XBOX", "MEDIODÍA", "PRIMERO",
             "YA", "PRECARGADO", "DIEZ"}

# Cómo se escriben en pantalla los números que la voz dice en letra
DISPLAY = {"diecinueve": "19", "doce": "12", "doscientos": "212", "diez": "10", "PlayStation": "PS5"}
DROP = {"(doce)", "gigas_skip"}

def timing():
    with open(os.path.join(HERE, "voice_timing.json"), encoding="utf-8") as f:
        return json.load(f)

def total():
    return timing()["total"]

def scene_bounds():
    return [(s["start"], s["end"]) for s in timing()["scenes"]]

def shot_timeline():
    out = []
    for (a, b), (_n, shots) in zip(scene_bounds(), SCENES):
        d = (b - a) / len(shots)
        for i, s in enumerate(shots):
            out.append((a + i * d, a + (i + 1) * d, s))
    return out

def _fix_words(words):
    """Convierte números dichos en letra a cifra para la pantalla (doscientos doce -> 212)."""
    out = []; i = 0
    while i < len(words):
        w = dict(words[i]); t = w["text"]; low = t.lower().strip(",.:;¿?…")
        if low == "doscientos" and i + 1 < len(words) and words[i + 1]["text"].lower().startswith("doce"):
            w["text"] = "212"; w["end"] = words[i + 1]["end"]; i += 2; out.append(w); continue
        if low == "playstation" and i + 1 < len(words) and words[i + 1]["text"].startswith("5"):
            w["text"] = "PS5"; w["end"] = words[i + 1]["end"]; i += 2; out.append(w); continue
        if low in DISPLAY:
            punct = t[len(t.rstrip(",.:;?…")):]
            w["text"] = DISPLAY[low] + punct
        out.append(w); i += 1
    return out

FUNC = {"a", "el", "la", "las", "los", "de", "del", "por", "en", "y", "o", "que", "lo", "no", "para", "si", "ha", "es", "te", "un", "una"}

def caption_timeline():
    """Bloques de 1-3 palabras sincronizados con la voz."""
    out = []
    for s in timing()["scenes"]:
        words = _fix_words(s["words"]); chunk = []
        for j, w in enumerate(words):
            chunk.append(w)
            txt = w["text"]
            brk = len(chunk) >= 3 or txt.endswith((",", ".", ":", "?", "…")) or \
                  (len(chunk) >= 2 and sum(len(c["text"]) for c in chunk) > 13)
            if brk and len(chunk) > 1 and j < len(words) - 1 and chunk[-1]["text"].lower() in FUNC:
                carry = [chunk.pop()]       # no cortar en "a", "de", "por"...: pasa al bloque siguiente
            else:
                carry = []
            if brk or j == len(words) - 1:
                out.append([chunk[0]["start"], chunk[-1]["end"], " ".join(c["text"] for c in chunk)]); chunk = carry
    for i in range(len(out) - 1):            # cada bloque se queda hasta que entra el siguiente (máx. 0,6 s de hueco)
        out[i][1] = min(out[i + 1][0], out[i][1] + 0.6)
    return [tuple(c) for c in out]

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c.upper()}\n\n")
