# Guion de "Hiroo Onoda: 29 años en una guerra que ya había terminado" (estilo: personajes 2D en un mundo 3D)
# Cada escena: (narración, [bloques de subtítulo], estado de la historia para la escena 3D)
# Los tiempos NO se escriben a mano: salen de la duración real de la voz (voz/duraciones.json).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = 0.12      # respiro mínimo entre frases (casi sin silencios, ver GUIA_ESTILO.md)
INTRO = 0.15    # la voz arranca casi en el primer cuadro
OUTRO = 2.4     # cola para la tarjeta final
# pronunciación solo para la voz (no cambia los subtítulos)
SAY = {"Hiroo": "Jiroo", "Yeti": "Yeti"}

SCENES = [
    ("Este soldado siguió luchando en una guerra que había terminado hacía veintinueve años.",
     ["ESTE SOLDADO", "SIGUIÓ *LUCHANDO*", "EN UNA GUERRA", "QUE HABÍA *TERMINADO*", "HACÍA *29 AÑOS*"],
     "gancho"),
    ("Hiroo Onoda, teniente japonés. En mil novecientos cuarenta y cuatro le envían a una isla de Filipinas con una orden: no rendirse jamás.",
     ["*HIROO ONODA*", "TENIENTE JAPONÉS", "EN *1944*", "A UNA ISLA", "DE *FILIPINAS*", "SU ORDEN:", "NO *RENDIRSE* JAMÁS"],
     "orden"),
    ("En mil novecientos cuarenta y cinco, Japón se rinde. La guerra termina.",
     ["EN *1945*", "JAPÓN SE *RINDE*", "LA GUERRA", "*TERMINA*"],
     "fin"),
    ("Pero en su selva caen panfletos diciéndolo… y él cree que son una trampa del enemigo.",
     ["EN SU SELVA", "CAEN *PANFLETOS*…", "Y ÉL CREE", "QUE SON", "UNA *TRAMPA*"],
     "panfletos"),
    ("¿El truco? Para él, una orden solo puede anularla quien la dio.",
     ["¿EL *TRUCO*?", "UNA ORDEN", "SOLO LA ANULA", "*QUIEN LA DIO*"],
     "truco"),
    ("Y pasan los años. Llegan los aviones a reacción, la televisión… y el hombre pisa la Luna. Él sigue escondido.",
     ["Y PASAN", "LOS *AÑOS*", "AVIONES A REACCIÓN", "TELEVISIÓN…", "EL HOMBRE", "PISA LA *LUNA*", "ÉL SIGUE", "*ESCONDIDO*"],
     "anos"),
    ("Sus compañeros se rinden o mueren. En sus ataques también mueren vecinos de la isla. En mil novecientos setenta y dos, Onoda se queda solo.",
     ["SUS COMPAÑEROS", "SE RINDEN", "O *MUEREN*", "Y MUEREN VECINOS", "DE LA ISLA", "EN *1972*", "SE QUEDA *SOLO*"],
     "solo"),
    ("En mil novecientos setenta y cuatro le encuentra un joven aventurero que buscaba a Onoda, a un oso panda y al Yeti… en ese orden.",
     ["EN *1974*", "LE ENCUENTRA", "UN *AVENTURERO*", "QUE BUSCABA", "A ONODA,", "UN *PANDA*", "Y EL *YETI*…", "EN ESE ORDEN"],
     "suzuki"),
    ("Pero Onoda no se rinde: exige la orden de su antiguo comandante.",
     ["PERO NO", "SE *RINDE*", "EXIGE LA ORDEN", "DE SU *COMANDANTE*"],
     "exige"),
    ("Y aquel comandante, que ya trabajaba de librero, viaja a la selva y le lee la orden. Solo entonces, Onoda entrega su espada.",
     ["EL COMANDANTE", "YA ERA *LIBRERO*", "VIAJA A LA SELVA", "LE LEE", "LA *ORDEN*", "Y ONODA", "ENTREGA", "SU *ESPADA*"],
     "rendicion"),
    ("¿Tú habrías seguido esperando la orden? Te leo en comentarios.",
     ["¿TÚ HABRÍAS", "SEGUIDO", "*ESPERANDO*?", "TE LEO EN", "*COMENTARIOS*"],
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
