# Narración, subtítulos y planos del vídeo "El paso Diátlov" (historia real, 1959)
# Cada escena: (narración, [bloques de subtítulo], [planos visuales])
# Los tiempos salen de la duración real de la voz (voz/timings.json, generado por tts.py).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

RAW = [
    ("Nueve jóvenes rajaron su tienda desde dentro… y huyeron descalzos, de noche, a treinta grados bajo cero.",
     ["NUEVE JÓVENES", "*RAJARON* SU TIENDA", "DESDE *DENTRO*…", "Y HUYERON", "*DESCALZOS*", "DE NOCHE", "A *-30 °C*"],
     ["tent_slash", "footprints"]),
    ("Unión Soviética, mil novecientos cincuenta y nueve. Diez estudiantes expertos cruzan los Urales en pleno invierno.",
     ["URSS", "*1959*", "DIEZ ESTUDIANTES", "EXPERTOS", "CRUZAN LOS *URALES*", "EN PLENO INVIERNO"],
     ["title_1959", "hikers"]),
    ("Uno de ellos enferma y se da la vuelta. Acaba de salvarse.",
     ["UNO DE ELLOS", "*ENFERMA*", "Y SE DA LA VUELTA", "ACABA DE *SALVARSE*"],
     ["survivor"]),
    ("El uno de febrero, los otros nueve acampan en un monte que los mansis llaman… la Montaña Muerta.",
     ["EL 1 DE *FEBRERO*", "ACAMPAN EN UN MONTE", "QUE LOS MANSIS LLAMAN…", "*LA MONTAÑA*", "*MUERTA*"],
     ["mountain", "tent_night"]),
    ("Nunca volvieron. Semanas después, hallan la tienda vacía. Con las botas y los abrigos dentro.",
     ["NUNCA *VOLVIERON*", "SEMANAS DESPUÉS", "HALLAN LA TIENDA", "*VACÍA*", "CON LAS *BOTAS*", "Y LOS ABRIGOS", "*DENTRO*"],
     ["searchers", "tent_empty"]),
    ("Las huellas bajaban al bosque. Junto a un cedro, una hoguera… y dos cuerpos en ropa interior.",
     ["LAS *HUELLAS*", "BAJABAN AL BOSQUE", "JUNTO A UN *CEDRO*", "UNA *HOGUERA*…", "Y DOS CUERPOS", "EN *ROPA INTERIOR*"],
     ["footprints_down", "cedar"]),
    ("Los últimos cuatro aparecieron en mayo, en un barranco. Costillas rotas, un cráneo fracturado… y a una chica le faltaba la lengua.",
     ["LOS ÚLTIMOS *CUATRO*", "EN *MAYO*", "EN UN BARRANCO", "COSTILLAS *ROTAS*", "CRÁNEO *FRACTURADO*", "A UNA CHICA", "LE FALTABA", "*LA LENGUA*"],
     ["ravine", "xray"]),
    ("Algunas ropas tenían radiactividad. Y el informe se cerró con tres palabras: fuerza natural irresistible.",
     ["SUS ROPAS TENÍAN", "*RADIACTIVIDAD*", "Y EL INFORME", "SE CERRÓ ASÍ:", "FUERZA NATURAL", "*IRRESISTIBLE*"],
     ["geiger", "file"]),
    ("En dos mil veinte, Rusia dijo que fue un alud. Pero ni los científicos lo dan por resuelto.",
     ["EN *2020*", "RUSIA DIJO:", "UN *ALUD*", "PERO NI LOS", "CIENTÍFICOS", "LO DAN POR *RESUELTO*"],
     ["avalanche", "mountain_fog"]),
    ("¿Qué asusta tanto a nueve expertos… como para preferir el frío a esa tienda? Te leo en comentarios.",
     ["¿QUÉ *ASUSTA* TANTO", "A NUEVE EXPERTOS…", "PARA PREFERIR", "*EL FRÍO*", "A ESA *TIENDA*?", "TE LEO EN", "*COMENTARIOS*"],
     ["tent_glow", "end_card"]),
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
    fa, fb = shot_start("file")
    return [0.05, SCENES[4][0], caption_start("LENGUA"), fa + (fb - fa) * 0.3, SCENES[8][0] + 0.2,
            shot_start("end_card")[0]]
