# Guion del vídeo "Los secretos de GTA 6 (y el homenaje a Tommy Vercetti)"
# Cada escena: (narración, [planos]). Los tiempos salen de la locución real (voice.py -> voice_timing.json).
# Plano: (imagen en img/, foco_x 0..1, zoom inicial, zoom final, superposición)
# Superposiciones: None | ("stat", "TEXTO GRANDE", "texto pequeño") | ("end",)
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = "es-ES-AlvaroNeural"
RATE = "+12%"
TAG = "GTA VI · SECRETOS"
END_TOP = "¿CUÁL NO CONOCÍAS?"

SCENES = [
    ("Rockstar ha escondido un homenaje a Tommy Vercetti en GTA 6… y no es el único secreto.",
     [("revolver1", 0.40, 1.25, 1.08, ("stat", "VERCETTI", "en GTA 6")),
      ("ocean_hotel", 0.50, 1.05, 1.2, None)]),
    ("Según Rockstar, estos revólveres vienen de la finca Vercetti. Y hay un estampado para las armas inspirado en su mítica camisa de palmeras.",
     [("revolver2", 0.55, 1.0, 1.15, ("stat", "FINCA VERCETTI", "origen oficial de los revólveres")),
      ("estampado", 0.42, 1.15, 1.0, None),
      ("palmeras", 0.42, 1.0, 1.15, ("stat", "CAMISA", "de palmeras de Tommy Vercetti"))]),
    ("Porque Vice City vuelve, veinticuatro años después del GTA Vice City original, de 2002.",
     [("ciudad_aerea", 0.45, 1.0, 1.18, ("stat", "VICE CITY", "vuelve")),
      ("keyart", 0.55, 1.2, 1.05, ("stat", "2002 → 2026", "24 años después"))]),
    ("El estado donde pasa todo, Leonida, tiene apodo oficial: el Goodtime State. El estado de los buenos ratos.",
     [("goodtime", 0.55, 1.0, 1.15, ("stat", "LEONIDA", "el estado del juego")),
      ("gasolinera", 0.60, 1.15, 1.0, ("stat", "GOODTIME STATE", "el estado de los buenos ratos"))]),
    ("En este estudio de tatuajes hay más de cincuenta diseños hechos por FAILE, un colectivo de artistas real.",
     [("tattoo1", 0.30, 1.0, 1.15, ("stat", "+50 TATUAJES", "exclusivos")),
      ("tattoo2", 0.55, 1.15, 1.0, ("stat", "FAILE", "artistas de verdad"))]),
    ("La canción del tráiler de lanzamiento es inédita: Justice, con Tame Impala, SZA y King Gizzard.",
     [("musica", 0.50, 1.0, 1.12, ("stat", "JUSTICE", "+ Tame Impala, SZA, King Gizzard")),
      ("poster_collage", 0.50, 1.0, 1.12, None)]),
    ("Y el primer tráiler hizo noventa y tres millones de visitas en YouTube en 24 horas. Récord para un vídeo no musical.",
     [("jason_pistola", 0.45, 1.0, 1.15, ("stat", "93 M", "visitas en 24 horas")),
      ("lucia_noche", 0.45, 1.15, 1.0, ("stat", "RÉCORD", "vídeo no musical en YouTube"))]),
    ("¿Cuál de estos secretos no conocías? Te leo en comentarios.",
     [("palmeras", 0.62, 1.2, 1.05, None),
      ("keyart", 0.50, 1.25, 1.1, ("end",))]),
]

HIGHLIGHT = {"VERCETTI", "TOMMY", "GTA", "6", "VICE", "CITY", "24", "2002", "LEONIDA", "GOODTIME", "STATE", "50", "FAILE",
             "JUSTICE", "TAME", "IMPALA", "SZA", "93", "MILLONES", "RÉCORD", "PALMERAS", "SECRETO", "SECRETOS", "REAL",
             "INÉDITA", "YOUTUBE", "ROCKSTAR", "CINCUENTA", "VEINTICUATRO"}

# Cómo se escriben en pantalla los números que la voz dice en letra
DISPLAY = {"veinticuatro": "24", "cincuenta": "50"}
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
        if low == "noventa" and i + 2 < len(words) and words[i + 2]["text"].lower().startswith("tres"):
            w["text"] = "93"; w["end"] = words[i + 2]["end"]; i += 3; out.append(w); continue
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
