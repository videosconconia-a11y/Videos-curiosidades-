# Guion de "Julio César y los piratas" (estilo: personajes 2D en un mundo 3D)
# Cada escena: (narración, [bloques de subtítulo], estado de la historia para la escena 3D)
# Los tiempos NO se escriben a mano: salen de la duración real de la voz (voz/duraciones.json).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = 0.12      # respiro mínimo entre frases (casi sin silencios, ver GUIA_ESTILO.md)
INTRO = 0.15    # la voz arranca casi en el primer cuadro
OUTRO = 2.4     # cola para la tarjeta final
# pronunciación solo para la voz (no cambia los subtítulos)
SAY = {}

SCENES = [
    ("Unos piratas secuestraron a Julio César… y él se enfadó porque pedían muy poco rescate por él.",
     ["UNOS *PIRATAS*", "SECUESTRARON", "A *JULIO CÉSAR*…", "Y ÉL SE *ENFADÓ*", "PORQUE PEDÍAN", "*POCO* RESCATE"],
     "gancho"),
    ("Hacia el año setenta y cinco antes de Cristo, un joven romano navega por el mar Egeo… cuando su barco es atacado por piratas.",
     ["HACIA EL", "*75 a. C.*", "UN JOVEN ROMANO", "NAVEGA POR", "EL *EGEO*…", "CUANDO LE ATACAN", "*PIRATAS*"],
     "ataque"),
    ("Los piratas piden veinte talentos de plata. César se echa a reír: ¿veinte? Yo valgo por lo menos cincuenta.",
     ["PIDEN", "*20 TALENTOS*", "DE PLATA", "CÉSAR SE *RÍE*", "«¿VEINTE?", "YO VALGO", "*CINCUENTA*»"],
     "rescate"),
    ("Envía a sus hombres a reunir el dinero… y se queda en una isla, con los piratas, durante treinta y ocho días. Solo con un amigo y dos sirvientes.",
     ["ENVÍA A SUS HOMBRES", "A POR EL DINERO…", "Y SE QUEDA", "CON LOS PIRATAS", "*38 DÍAS*", "SOLO CON UN AMIGO", "Y DOS *SIRVIENTES*"],
     "isla"),
    ("¿El truco? César no se comporta como un prisionero… se comporta como su jefe.",
     ["¿EL *TRUCO*?", "NO SE PORTA", "COMO *PRISIONERO*…", "SE PORTA", "COMO SU *JEFE*"],
     "jefe"),
    ("Cuando quiere dormir, les manda callar. Hace ejercicio con ellos… y les lee sus poemas.",
     ["SI QUIERE DORMIR", "LES MANDA *CALLAR*", "ENTRENA CON ELLOS…", "Y LES LEE", "SUS *POEMAS*"],
     "poemas"),
    ("Si no le aplauden, los llama bárbaros. Y entre risas, les promete que un día los crucificará a todos.",
     ["SI NO APLAUDEN", "LOS LLAMA", "*BÁRBAROS*", "Y LES *PROMETE*", "QUE UN DÍA", "LOS *CRUCIFICARÁ*"],
     "amenaza"),
    ("Los piratas se ríen. Creen que es una broma.",
     ["LOS PIRATAS", "SE *RÍEN*", "CREEN QUE ES", "UNA *BROMA*"],
     "risas"),
    ("Cuando llega el rescate, lo liberan. César va al puerto más cercano, reúne barcos… y vuelve a por ellos.",
     ["LLEGA EL RESCATE", "LO *LIBERAN*", "REÚNE *BARCOS*…", "Y *VUELVE*", "A POR ELLOS"],
     "vuelta"),
    ("Los captura, recupera su dinero… y cumple su promesa.",
     ["LOS *CAPTURA*", "RECUPERA", "SU DINERO…", "Y *CUMPLE*", "SU PROMESA"],
     "captura"),
    ("Lo que ellos tomaron por una broma era un aviso. ¿Tú le habrías tomado en serio? Te leo en comentarios.",
     ["NO ERA", "UNA BROMA:", "ERA UN *AVISO*", "¿TÚ LE HABRÍAS", "TOMADO EN *SERIO*?", "TE LEO EN", "*COMENTARIOS*"],
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
