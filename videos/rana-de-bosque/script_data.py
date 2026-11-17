# Guion del vídeo "La rana de bosque" (v2: con voz en off).
#
# Cada escena tiene:
#   lines: frases que lee la voz -> (texto para la voz, [bloques de subtítulo], pausa después en s)
#   shots: planos visuales que se reparten la duración de la escena (peso opcional: ("nombre", 1.5))
#   sfx:   efectos atados al inicio de una frase -> (índice de frase, "boom" | "crack" | "riser" | ...)
# Las palabras entre *asteriscos* se resaltan en el subtítulo.
# Los tiempos NO se escriben a mano: los calcula voice.py a partir de la duración real de la voz
# y los guarda en build/timing.json.

import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = os.path.join(HERE, "build", "timing.json")

LEAD_IN = 0.1     # silencio antes de la primera palabra (el gancho entra ya)
TAIL = 1.6        # cola final (música + cartel) tras la última palabra

SCENES = [
    dict(name="gancho",
         lines=[("Este animal se congela por completo…", ["ESTE ANIMAL", "SE *CONGELA*", "POR COMPLETO…"], 0.25),
                ("y meses después, vuelve a la vida.", ["Y MESES DESPUÉS…", "VUELVE", "A LA *VIDA*"], 0.45)],
         shots=["frozen_frog", ("ice_grow", "@POR COMPLETO"), ("frog_eye", "@VUELVE")],
         sfx=[(0, "boom"), (0, "crack"), (1, "riser_end")]),
    dict(name="presentacion",
         lines=[("Es la rana de bosque.", ["ES LA", "*RANA DE BOSQUE*"], 0.2),
                ("Vive en los bosques de Norteamérica, y llega más al norte que ningún otro anfibio del continente: "
                 "más allá del Círculo Polar Ártico.",
                 ["VIVE EN", "*NORTEAMÉRICA*", "Y LLEGA", "MÁS AL NORTE", "QUE NINGÚN", "OTRO *ANFIBIO*",
                  "MÁS ALLÁ DEL", "*CÍRCULO POLAR*", "*ÁRTICO*"], 0.35)],
         shots=["frog_hero", ("frog_side", "@*NORTEAMÉRICA*"), ("boreal", "@MÁS AL NORTE"), ("aurora", "@MÁS ALLÁ DEL")],
         sfx=[(0, "hit")]),
    dict(name="invierno",
         lines=[("Cuando llega el invierno, no huye, ni se esconde bajo el agua.",
                 ["CUANDO LLEGA", "EL *INVIERNO*", "NO HUYE", "NI SE ESCONDE", "BAJO EL AGUA"], 0.2),
                ("Se queda entre las hojas del suelo del bosque… y deja que el hielo la atrape.",
                 ["SE QUEDA", "ENTRE LAS *HOJAS*", "DEL BOSQUE…", "Y DEJA QUE", "EL *HIELO*", "LA ATRAPE"], 0.3)],
         shots=["snow_forest", ("snowfall_close", "@NO HUYE"), ("frog_leaves", "@SE QUEDA"), ("frost_leaves", "@Y DEJA QUE")],
         sfx=[(1, "crack")]),
    dict(name="congelacion",
         lines=[("El hielo empieza en su piel, y avanza hacia dentro.",
                 ["EL HIELO", "EMPIEZA", "EN SU *PIEL*", "Y AVANZA", "HACIA DENTRO"], 0.2),
                ("Hasta el sesenta y cinco por ciento del agua de su cuerpo se convierte en hielo.",
                 ["HASTA EL", "*65 %*", "DEL AGUA", "DE SU CUERPO", "SE VUELVE *HIELO*"], 0.35)],
         shots=["frog_freeze", ("ice_macro", "@Y AVANZA"), ("stat_65", "@*65 %*")],
         sfx=[(0, "crack"), (1, "boom")]),
    dict(name="muerta",
         lines=[("Su corazón deja de latir.", ["SU *CORAZÓN*", "DEJA DE LATIR"], 0.25),
                ("No respira. No circula la sangre.", ["NO RESPIRA", "NO CIRCULA", "LA *SANGRE*"], 0.25),
                ("A todos los efectos… parece muerta.", ["A TODOS", "LOS EFECTOS…", "PARECE…", "*MUERTA*"], 0.5)],
         shots=["heartbeat", ("frozen_frog_2", "@NO RESPIRA"), ("frog_eye_still", "@A TODOS")],
         sfx=[(0, "heart_stop"), (2, "boom")]),
    dict(name="truco",
         lines=[("¿El truco? En cuanto nota el hielo, su hígado inunda el cuerpo de glucosa.",
                 ["¿EL *TRUCO*?", "EN CUANTO", "NOTA EL HIELO", "SU *HÍGADO*", "INUNDA EL CUERPO", "DE *GLUCOSA*"], 0.2),
                ("Ese azúcar funciona como un anticongelante: el hielo se queda fuera de las células, "
                 "y las células sobreviven.",
                 ["ESE AZÚCAR", "FUNCIONA COMO UN", "*ANTICONGELANTE*", "EL HIELO", "SE QUEDA *FUERA*",
                  "DE LAS CÉLULAS", "Y LAS CÉLULAS", "*SOBREVIVEN*"], 0.35)],
         shots=["frog_macro", ("glucose", "@SU *HÍGADO*"), ("frog_antifreeze", "@ESE AZÚCAR"), ("cells", "@EL HIELO"), ("frog_hero_2", "@Y LAS CÉLULAS")],
         sfx=[(0, "hit"), (1, "shimmer")]),
    dict(name="alaska",
         lines=[("En Alaska, los científicos siguieron a ranas en plena naturaleza.",
                 ["EN *ALASKA*", "LOS CIENTÍFICOS", "SIGUIERON", "A RANAS", "EN LIBERTAD"], 0.2),
                ("Pasaron, de media, ciento noventa y tres días seguidos congeladas… "
                 "con mínimas de hasta dieciocho grados bajo cero.",
                 ["PASARON", "DE MEDIA", "*193 DÍAS*", "SEGUIDOS", "CONGELADAS…", "CON MÍNIMAS", "DE *–18 °C*"], 0.3),
                ("Y sobrevivieron todas.", ["Y SOBREVIVIERON…", "*TODAS*"], 0.5)],
         shots=["alaska", ("frog_track", "@A RANAS"), ("stat_193", "@*193 DÍAS*"), ("stat_18", "@CON MÍNIMAS"), ("frog_survive", "@Y SOBREVIVIERON")],
         sfx=[(0, "riser_end"), (1, "boom"), (2, "boom")]),
    dict(name="deshielo",
         lines=[("Y en primavera, con el deshielo, su corazón vuelve a latir por sí solo.",
                 ["Y EN *PRIMAVERA*", "CON EL DESHIELO", "SU CORAZÓN", "VUELVE A *LATIR*", "POR SÍ SOLO"], 0.2),
                ("En pocas horas respira, se mueve… y salta hacia la charca.",
                 ["EN POCAS HORAS", "*RESPIRA*", "SE MUEVE…", "Y SALTA", "A LA *CHARCA*"], 0.3)],
         shots=["thaw", ("heartbeat_back", "@VUELVE A *LATIR*"), ("frog_spring", "@*RESPIRA*"), ("pond", "@Y SALTA")],
         sfx=[(0, "drips"), (0, "heart_back")]),
    dict(name="ciencia",
         lines=[("Hoy, los científicos la estudian para aprender a conservar órganos humanos para trasplantes.",
                 ["HOY LA ESTUDIAN", "PARA CONSERVAR", "*ÓRGANOS*", "HUMANOS", "PARA *TRASPLANTES*"], 0.35)],
         shots=["lab", ("frog_portrait", "@*ÓRGANOS*")],
         sfx=[(0, "hit")]),
    dict(name="final",
         lines=[("Y ahora, piénsalo: ¿te dejarías congelar… si supieras que vas a despertar?",
                 ["Y AHORA…", "PIÉNSALO", "¿TE DEJARÍAS", "*CONGELAR*…", "SI SUPIERAS", "QUE VAS A *DESPERTAR*?"], 0.3),
                ("Te leo en comentarios.", ["TE LEO EN", "*COMENTARIOS*"], 0.0)],
         shots=["frog_eye_end", ("end_card", "@QUE VAS A")],
         sfx=[(0, "riser_end"), (1, "boom")]),
]


def narration_text():
    return " ".join(l[0] for s in SCENES for l in s["lines"])


def load_timing():
    with open(TIMING, encoding="utf-8") as f:
        return json.load(f)


def scene_bounds(tm=None):
    """[(inicio, fin)] de cada escena; los cortes caen en mitad de la pausa entre escenas."""
    tm = tm or load_timing()
    out = []
    for i, sc in enumerate(tm["scenes"]):
        a = 0.0 if i == 0 else out[-1][1]
        if i + 1 < len(tm["scenes"]):
            nxt = tm["scenes"][i + 1]["lines"][0]["start"]
            b = (sc["lines"][-1]["end"] + nxt) / 2
        else:
            b = tm["total"]
        out.append((a, b))
    return out


def caption_timeline(tm=None):
    tm = tm or load_timing()
    return [(c["start"], c["end"], c["text"]) for sc in tm["scenes"] for l in sc["lines"] for c in l["chunks"]]


def shot_timeline(tm=None):
    """Planos de cada escena. ("plano", "@TEXTO") hace que el plano empiece justo cuando la voz dice ese
    bloque de subtítulo; los planos sin ancla se reparten por igual el hueco que queda."""
    tm = tm or load_timing()
    out = []
    for (a, b), sc, tsc in zip(scene_bounds(tm), SCENES, tm["scenes"]):
        chunks = [c for l in tsc["lines"] for c in l["chunks"]]
        starts = []
        for s in sc["shots"]:
            if isinstance(s, tuple) and str(s[1]).startswith("@"):
                key = s[1][1:]
                c = next(c for c in chunks if c["text"].startswith(key))
                starts.append((s[0], max(a, c["start"] - 0.12)))
            else:
                starts.append((s if isinstance(s, str) else s[0], None))
        starts[0] = (starts[0][0], a)
        # rellena los inicios sin ancla interpolando entre anclas
        i = 0
        while i < len(starts):
            if starts[i][1] is None:
                j = i
                while j < len(starts) and starts[j][1] is None: j += 1
                t0 = starts[i - 1][1]; t1 = starts[j][1] if j < len(starts) else b
                for k in range(i, j):
                    starts[k] = (starts[k][0], t0 + (t1 - t0) * (k - i + 1) / (j - i + 1))
                i = j
            i += 1
        for k, (name, t0) in enumerate(starts):
            t1 = starts[k + 1][1] if k + 1 < len(starts) else b
            out.append((t0, t1, name))
    return out


def sfx_events(tm=None):
    tm = tm or load_timing()
    ev = []
    for sc, tsc in zip(SCENES, tm["scenes"]):
        for li, kind in sc["sfx"]:
            ln = tsc["lines"][li]
            ev.append((ln["start"], ln["end"], kind))
    return ev


def heart_beats(tm=None):
    """Latidos compartidos por audio y vídeo: (latidos que se apagan, instante de línea plana, latidos que vuelven)."""
    tm = tm or load_timing()
    names = [s["name"] for s in SCENES]
    a, _ = scene_bounds(tm)[names.index("muerta")]
    stop_end = tm["scenes"][names.index("muerta")]["lines"][0]["end"]
    stop, t, gap = [], a + 0.12, 0.62
    while t < stop_end - 0.1:
        stop.append(round(t, 3)); t += gap; gap *= 1.28
    flat = round(stop[-1] + 0.45, 3)
    ln = tm["scenes"][names.index("deshielo")]["lines"][0]
    c = next(c for c in ln["chunks"] if "LATIR" in c["text"])
    back, t = [], c["start"] - 0.1
    for g in (1.05, 0.9, 0.78, 0.7, 0.64, 0.6, 0.58):
        back.append(round(t, 3)); t += g
    return stop, flat, back


def write_srt(path, tm=None):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(tm), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c.replace('*', '')}\n\n")
