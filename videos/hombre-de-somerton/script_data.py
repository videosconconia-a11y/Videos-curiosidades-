# Narración, subtítulos y planos del vídeo "El hombre de Somerton" (caso real, Australia, 1948)
# Cada escena: (narración, [bloques de subtítulo], [planos visuales])
# Los tiempos salen de la duración real de la voz (voz/timings.json, generado por tts.py).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

RAW = [
    ("Un hombre aparece muerto en una playa. Sin nombre. Y alguien había arrancado todas las etiquetas de su ropa.",
     ["UN HOMBRE", "*MUERTO*", "EN UNA PLAYA", "SIN *NOMBRE*", "Y ALGUIEN", "ARRANCÓ LAS", "*ETIQUETAS*", "DE SU ROPA"],
     ["beach_body", "label_tear"]),
    ("Australia, mil novecientos cuarenta y ocho. Traje elegante… y ni una sola herida.",
     ["*AUSTRALIA*", "*1948*", "TRAJE ELEGANTE…", "NI UNA *HERIDA*"],
     ["title_1948", "suit"]),
    ("Los forenses buscan un veneno… y no encuentran nada.",
     ["LOS FORENSES", "BUSCAN UN *VENENO*…", "Y NO ENCUENTRAN *NADA*"],
     ["poison", "autopsy"]),
    ("Pero en un bolsillo secreto aparece un papelito. Dos palabras en persa: Tamám Shud. Se acabó.",
     ["EN UN BOLSILLO", "*SECRETO*", "UN PAPELITO", "DOS PALABRAS:", "*TAMÁM SHUD*", "«*SE ACABÓ*»"],
     ["pocket", "meaning"]),
    ("Arrancado de un libro de poemas que, meses después, aparece tirado en un coche.",
     ["ARRANCADO DE UN", "*LIBRO* DE POEMAS", "QUE MESES DESPUÉS", "APARECE EN", "UN *COCHE*"],
     ["book", "car"]),
    ("Dentro, el teléfono de una enfermera que vive a cuatrocientos metros de la playa. Jura que no lo conoce.",
     ["DENTRO…", "EL *TELÉFONO*", "DE UNA *ENFERMERA*", "QUE VIVE A", "*400* METROS", "JURA QUE", "*NO LO CONOCE*"],
     ["phone", "house"]),
    ("Y al final, cinco líneas de letras escritas a lápiz. Nadie ha conseguido descifrarlas.",
     ["Y AL FINAL…", "CINCO LÍNEAS", "DE *LETRAS*", "A LÁPIZ", "*NADIE*", "HA PODIDO", "DESCIFRARLAS"],
     ["code", "code_zoom"]),
    ("En dos mil veintidós, el ADN apuntó a un nombre: Carl Webb. Pero la policía no lo ha confirmado.",
     ["EN *2022*", "EL *ADN*", "APUNTÓ A", "*CARL WEBB*", "PERO…", "*SIN CONFIRMAR*"],
     ["dna", "name"]),
    ("Y sigue sin respuesta: quién lo mató… y qué dice ese código.",
     ["SIGUE SIN", "RESPUESTA:", "¿QUIÉN LO *MATÓ*?", "¿QUÉ DICE", "ESE *CÓDIGO*?"],
     ["bust", "code_glow"]),
    ("¿Espía, amante… o algo peor? Te leo en comentarios.",
     ["¿*ESPÍA*?", "¿*AMANTE*?…", "¿O ALGO *PEOR*?", "TE LEO EN", "*COMENTARIOS*"],
     ["beach_fog", "end_card"]),
]

GAP = 0.28      # silencio tras cada frase
LEAD = 0.15     # la voz entra a los 0,15 s

def _durations():
    p = os.path.join(HERE, "voz", "timings.json")
    if os.path.exists(p):
        return json.load(open(p))
    return [len(n) / 15.5 for n, _c, _v in RAW]   # estimación si aún no hay voz

def _build():
    scenes, t = [], 0.0
    durs = _durations()
    for i, ((n, c, v), d) in enumerate(zip(RAW, durs)):
        a = t; b = t + (LEAD if i == 0 else 0) + d + GAP
        if i == len(RAW) - 1: b += 1.3   # cola final
        scenes.append((round(a, 3), round(b, 3), n, c, v)); t = b
    return scenes, round(t, 3)

SCENES, TOTAL = _build()

def voice_starts():
    return [a + (LEAD if i == 0 else 0.0) for i, (a, *_r) in enumerate(SCENES)]

def caption_timeline():
    out = []
    starts = voice_starts(); durs = _durations()
    for (a, b, _n, chunks, _v), s0, d in zip(SCENES, starts, durs):
        w = [len(c.replace("*", "")) + 4 for c in chunks]
        tot = sum(w); t = s0; span = d
        for k, (c, wi) in enumerate(zip(chunks, w)):
            dd = span * wi / tot
            end = t + dd if k < len(chunks) - 1 else max(t + dd, b - 0.05)
            out.append((t, end, c)); t += dd
    return out

def shot_timeline():
    out = []
    for (a, b, _n, _c, shots) in SCENES:
        d = (b - a) / len(shots)
        for i, s in enumerate(shots):
            out.append((a + i * d, a + (i + 1) * d, s))
    return out

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c.replace('*','')}\n\n")

def shot_start(name):
    for a, b, s in shot_timeline():
        if s == name: return a, b
    raise KeyError(name)

def caption_start(word):
    for a, b, c in caption_timeline():
        if word in c: return a
    raise KeyError(word)

def hits():
    """Momentos de golpe (flash + boom), compartidos por imagen y sonido."""
    return [0.05, caption_start("ETIQUETAS"), caption_start("TAMÁM"), caption_start("400"), caption_start("NADIE"),
            caption_start("SIN CONFIRMAR"), shot_start("end_card")[0]]
