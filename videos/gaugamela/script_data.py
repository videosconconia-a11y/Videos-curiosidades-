# Guion de "Gaugamela: ganar alejándose" (estilo: personajes 2D en un mundo 3D)
# Cada escena: (narración, [bloques de subtítulo], estado de la historia para la escena 3D)
# Los tiempos NO se escriben a mano: salen de la duración real de la voz (voz/duraciones.json).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = 0.12      # respiro mínimo entre frases (casi sin silencios, ver GUIA_ESTILO.md)
INTRO = 0.15    # la voz arranca casi en el primer cuadro
OUTRO = 1.6     # cola para la tarjeta final

SCENES = [
    ("Alejandro Magno venció a un ejército el doble de grande que el suyo… alejándose de él.",
     ["ALEJANDRO MAGNO", "VENCIÓ A UN EJÉRCITO", "EL *DOBLE*", "DE GRANDE…", "*ALEJÁNDOSE*", "DE ÉL"],
     "gancho"),
    ("Gaugamela, año 331 antes de Cristo. Alejandro llega con unos cuarenta y siete mil hombres.",
     ["*GAUGAMELA*", "AÑO 331 a. C.", "ALEJANDRO LLEGA", "CON UNOS", "*47.000*", "HOMBRES"],
     "macedonios"),
    ("Enfrente le espera el rey persa Darío. Los historiadores calculan unos cien mil soldados… y los textos antiguos hablaban de un millón.",
     ["ENFRENTE", "EL REY *DARÍO*", "UNOS *100.000*", "SOLDADOS…", "LOS TEXTOS ANTIGUOS", "DECÍAN", "*UN MILLÓN*"],
     "persas"),
    ("Darío trae doscientos carros con cuchillas en las ruedas. Incluso ha mandado allanar la llanura para que corran sin frenos.",
     ["*200 CARROS*", "CON *CUCHILLAS*", "EN LAS RUEDAS", "MANDÓ *ALLANAR*", "LA LLANURA", "PARA QUE CORRIERAN", "SIN FRENOS"],
     "carros"),
    ("¿El truco? Alejandro no carga de frente. Mueve a su ejército en diagonal, hacia la derecha, fuera del terreno allanado.",
     ["¿EL *TRUCO*?", "NO CARGA", "DE FRENTE", "SE MUEVE", "EN *DIAGONAL*", "A LA DERECHA", "FUERA DEL", "TERRENO *ALLANADO*"],
     "diagonal"),
    ("Los persas lo siguen para no ser rodeados… y su línea se estira tanto que se abre un hueco en el centro.",
     ["LOS PERSAS", "LO SIGUEN…", "SU LÍNEA", "SE *ESTIRA*", "Y SE ABRE", "UN *HUECO*", "EN EL CENTRO"],
     "hueco"),
    ("Los carros atacan. Pero los macedonios abren pasillos, los dejan pasar… y los rodean por detrás.",
     ["LOS CARROS", "*ATACAN*", "PERO ABREN", "*PASILLOS*", "LOS DEJAN PASAR…", "Y LOS RODEAN", "POR DETRÁS"],
     "pasillos"),
    ("Entonces Alejandro gira. Lanza su caballería en cuña, directa al hueco… directa a Darío.",
     ["ENTONCES", "ALEJANDRO *GIRA*", "SU CABALLERÍA", "EN *CUÑA*", "DIRECTA AL HUECO…", "DIRECTA A *DARÍO*"],
     "cuna"),
    ("Darío huye. Y el mayor imperio de su tiempo empieza a derrumbarse.",
     ["DARÍO *HUYE*", "Y EL MAYOR", "IMPERIO", "DE SU TIEMPO", "SE *DERRUMBA*"],
     "huida"),
    ("Pero a Darío no lo mató Alejandro. Lo mataron sus propios hombres. ¿Quién fue su peor enemigo?",
     ["PERO A DARÍO", "NO LO MATÓ", "ALEJANDRO", "LO MATARON", "SUS *PROPIOS* HOMBRES", "¿QUIÉN FUE", "SU PEOR *ENEMIGO*?"],
     "final"),
]


def _durations():
    p = os.path.join(HERE, "voz", "duraciones.json")
    if os.path.exists(p):
        return json.load(open(p))
    # estimación si aún no hay voz: ~2,9 palabras/s
    return [len(s[0].split()) / 2.9 for s in SCENES]


def timeline():
    """[(inicio, fin, inicio_voz)] por escena, encadenadas sin huecos."""
    out, t = [], 0.0
    for i, d in enumerate(_durations()):
        a = t
        v = a + (INTRO if i == 0 else 0.0)
        b = v + d + GAP
        out.append((a, b, v)); t = b
    a, b, v = out[-1]
    out[-1] = (a, b + OUTRO, v)
    return out


TIMES = timeline()
TOTAL = TIMES[-1][1]


def caption_timeline():
    out = []
    durs = _durations()
    for i, ((a, b, v), (_n, chunks, _s)) in enumerate(zip(TIMES, SCENES)):
        w = [len(c.replace("*", "")) + 4 for c in chunks]
        tot = sum(w); t = v; span = durs[i]
        for c, wi in zip(chunks, w):
            dd = span * wi / tot
            out.append((t, t + dd, c)); t += dd
    return out


def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c.replace('*', '')}\n\n")


def story_keys():
    """Escenas con sus tiempos para la escena 3D (se exporta a escena3d/timeline.json)."""
    return [{"name": s[2], "a": round(a, 3), "b": round(b, 3), "v": round(v, 3)} for (a, b, v), s in zip(TIMES, SCENES)]


if __name__ == "__main__":
    json.dump({"total": round(TOTAL, 3), "scenes": story_keys()},
              open(os.path.join(HERE, "escena3d", "timeline.json"), "w"), indent=1)
    print(f"total {TOTAL:.2f} s")
