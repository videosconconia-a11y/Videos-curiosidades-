# Narración, tiempos y subtítulos del vídeo "La rana de bosque"
# Cada escena: (inicio, fin, narración, [bloques de subtítulo], [planos visuales])
# Palabras entre *asteriscos* = resaltadas en el subtítulo.

SCENES = [
    (0.0, 4.5,
     "Este animal se congela por completo… y en primavera, vuelve a la vida.",
     ["ESTE ANIMAL", "SE *CONGELA*", "POR COMPLETO…", "Y VUELVE", "A LA *VIDA*"],
     ["eye_frost", "ice_grow"]),
    (4.5, 10.0,
     "Es la rana de bosque. Vive en Norteamérica, incluso por encima del Círculo Polar Ártico.",
     ["ES LA", "*RANA DE BOSQUE*", "VIVE EN", "NORTEAMÉRICA", "MÁS ALLÁ DEL", "*CÍRCULO POLAR*"],
     ["forest_night", "aurora"]),
    (10.0, 17.0,
     "Cuando llega el invierno, no huye ni se esconde bajo el agua. Se queda en el suelo del bosque, bajo las hojas… y deja que el hielo la atrape.",
     ["CUANDO LLEGA", "EL *INVIERNO*", "NO HUYE", "SE QUEDA", "BAJO LAS HOJAS…", "Y DEJA QUE", "EL *HIELO*", "LA ATRAPE"],
     ["leaves_snow", "snowfall_close", "ice_grow"]),
    (17.0, 22.0,
     "Hasta el sesenta y cinco por ciento del agua de su cuerpo se convierte en hielo.",
     ["HASTA EL", "*65 %*", "DEL AGUA", "DE SU CUERPO", "SE VUELVE *HIELO*"],
     ["stat_65", "ice_grow"]),
    (22.0, 29.5,
     "Su corazón deja de latir. No respira. Su cerebro, sin actividad. A todos los efectos… parece muerta.",
     ["SU *CORAZÓN*", "DEJA DE LATIR", "NO RESPIRA", "SIN ACTIVIDAD", "CEREBRAL", "PARECE…", "*MUERTA*"],
     ["heartbeat", "eye_frost"]),
    (29.5, 37.5,
     "¿El truco? Su hígado inunda el cuerpo de glucosa. Ese azúcar actúa como anticongelante y protege sus células del hielo.",
     ["¿EL TRUCO?", "SU HÍGADO", "LIBERA", "*GLUCOSA*", "UN AZÚCAR", "QUE ACTÚA COMO", "*ANTICONGELANTE*", "Y PROTEGE", "SUS CÉLULAS"],
     ["glucose", "cells"]),
    (37.5, 44.5,
     "En Alaska, los científicos midieron ciento noventa y tres días seguidos congelada… a dieciocho grados bajo cero.",
     ["EN *ALASKA*", "SE MIDIERON", "*193 DÍAS*", "SEGUIDOS", "CONGELADA…", "A *-18 °C*"],
     ["aurora", "stat_193", "stat_18"]),
    (44.5, 50.5,
     "Y con el deshielo, su corazón vuelve a latir… y en pocas horas, respira otra vez.",
     ["Y CON EL", "*DESHIELO*", "SU CORAZÓN", "VUELVE A *LATIR*", "Y EN HORAS", "*RESPIRA*"],
     ["thaw", "heartbeat_back", "eye_open"]),
    (50.5, 58.5,
     "Hoy, los científicos la estudian para aprender a conservar órganos para trasplantes. ¿Te dejarías congelar… si supieras que vas a despertar?",
     ["HOY LA ESTUDIAN", "PARA CONSERVAR", "*ÓRGANOS*", "PARA TRASPLANTES", "¿TE DEJARÍAS", "*CONGELAR*…", "SI SUPIERAS", "QUE VAS A *DESPERTAR*?"],
     ["lab", "forest_spring", "end_card"]),
]
TOTAL = 58.5

def caption_timeline():
    out = []
    for (a, b, _n, chunks, _v) in SCENES:
        w = [len(c.replace("*", "")) + 4 for c in chunks]
        tot = sum(w); t = a + 0.1; span = (b - a) - 0.25
        for c, wi in zip(chunks, w):
            d = span * wi / tot
            out.append((t, t + d, c)); t += d
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
