# Guion de "Troya: el regalo que ganó la guerra" (estilo: personajes 2D en un mundo 3D)
# Cada escena: (narración, [bloques de subtítulo], estado de la historia para la escena 3D)
# Los tiempos NO se escriben a mano: salen de la duración real de la voz (voz/duraciones.json).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = 0.12      # respiro mínimo entre frases (casi sin silencios, ver GUIA_ESTILO.md)
INTRO = 0.15    # la voz arranca casi en el primer cuadro
OUTRO = 1.6     # cola para la tarjeta final
# pronunciación solo para la voz (no cambia los subtítulos)
SAY = {"Laocoonte": "Lao-coonte"}

SCENES = [
    ("Diez años de batallas no lograron abrir las murallas de Troya… y un regalo lo consiguió en una sola noche.",
     ["*DIEZ AÑOS*", "DE BATALLAS", "NO ABRIERON", "SUS MURALLAS…", "Y UN *REGALO*", "LO LOGRÓ", "EN UNA *NOCHE*"],
     "gancho"),
    ("Según la leyenda, los griegos sitiaron Troya durante diez años para recuperar a Helena.",
     ["SEGÚN LA *LEYENDA*", "LOS GRIEGOS", "SITIARON *TROYA*", "DIEZ AÑOS", "POR *HELENA*"],
     "asedio"),
    ("Pero sus murallas eran tan altas que ningún ejército consiguió cruzarlas.",
     ["PERO SUS *MURALLAS*", "ERAN TAN ALTAS", "QUE NADIE", "LAS *CRUZÓ*"],
     "murallas"),
    ("Una mañana, los troyanos vieron algo imposible: el campamento griego, vacío… y sus barcos, alejándose.",
     ["UNA MAÑANA", "ALGO *IMPOSIBLE*", "EL CAMPAMENTO", "*VACÍO*…", "Y LOS BARCOS", "*ALEJÁNDOSE*"],
     "retirada"),
    ("En la playa había un enorme caballo de madera. Un regalo para los dioses, juraba un prisionero griego llamado Sinón.",
     ["EN LA PLAYA", "UN ENORME", "*CABALLO*", "DE MADERA", "UN REGALO", "PARA LOS DIOSES", "JURABA *SINÓN*"],
     "caballo"),
    ("El sacerdote Laocoonte avisó: temo a los griegos incluso cuando traen regalos. Nadie le hizo caso.",
     ["EL SACERDOTE", "*LAOCOONTE*", "«TEMO A LOS GRIEGOS", "INCLUSO CUANDO", "TRAEN *REGALOS*»", "NADIE", "LE HIZO *CASO*"],
     "aviso"),
    ("¿El truco? Los griegos no tuvieron que entrar en Troya. Fueron los propios troyanos quienes metieron el caballo… derribando parte de su muralla para que cupiera.",
     ["¿EL *TRUCO*?", "LOS GRIEGOS", "NO ENTRARON", "LOS *TROYANOS*", "LO METIERON", "*DERRIBANDO*", "SU PROPIA", "*MURALLA*"],
     "brecha"),
    ("Esa noche, mientras la ciudad celebraba, los soldados escondidos dentro salieron y abrieron las puertas.",
     ["ESA *NOCHE*", "MIENTRAS", "CELEBRABAN", "LOS *ESCONDIDOS*", "SALIERON", "Y ABRIERON", "LAS *PUERTAS*"],
     "noche"),
    ("Los barcos, que solo se habían escondido tras una isla, volvieron. Y Troya ardió.",
     ["LOS BARCOS", "SOLO SE", "*ESCONDÍAN*", "TRAS UNA ISLA", "VOLVIERON…", "Y TROYA *ARDIÓ*"],
     "incendio"),
    ("Lo más curioso: Troya existió. Sus ruinas están en Turquía, y muestran una ciudad arrasada por el fuego hace más de tres mil años.",
     ["LO MÁS CURIOSO", "TROYA *EXISTIÓ*", "SUS RUINAS", "ESTÁN EN *TURQUÍA*", "ARRASADA", "POR EL *FUEGO*", "HACE MÁS DE", "*3.000 AÑOS*"],
     "ruinas"),
    ("Pero la Ilíada, el gran poema de Troya, termina antes de que aparezca el caballo. ¿Crees que existió?",
     ["PERO LA *ILÍADA*", "EL GRAN POEMA", "DE TROYA", "TERMINA *ANTES*", "DEL CABALLO", "¿CREES QUE", "*EXISTIÓ*?"],
     "final"),
]


def _durations():
    p = os.path.join(HERE, "voz", "duraciones.json")
    if os.path.exists(p):
        return json.load(open(p))
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
    return [{"name": s[2], "a": round(a, 3), "b": round(b, 3), "v": round(v, 3)} for (a, b, v), s in zip(TIMES, SCENES)]


if __name__ == "__main__":
    json.dump({"total": round(TOTAL, 3), "scenes": story_keys()},
              open(os.path.join(HERE, "escena3d", "timeline.json"), "w"), indent=1)
    print(f"total {TOTAL:.2f} s")
