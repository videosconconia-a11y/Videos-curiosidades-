# Guion de "La mujer del armario" (Japón, 2008) — historia real.
# Cada escena: (narración para la voz, [bloques de subtítulo], [planos visuales])
# Los tiempos salen de la duración real de la voz (timings.json, generado por voice.py).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

SCENES_TXT = [
    ("Durante casi un año, este hombre nunca estuvo solo en su casa. Y no tenía ni idea.",
     ["DURANTE CASI", "*UN AÑO*", "ESTE HOMBRE", "NUNCA ESTUVO", "*SOLO*", "EN SU CASA", "Y NO TENÍA", "*NI IDEA*"],
     ["cctv_hook", "closet_gap"]),
    ("Japón, dos mil ocho. Un hombre de cincuenta y siete años, que vive solo, empieza a notar algo raro.",
     ["*JAPÓN*, 2008", "UN HOMBRE", "DE *57 AÑOS*", "QUE VIVE *SOLO*", "EMPIEZA A NOTAR", "ALGO *RARO*"],
     ["house_ext", "man_table"]),
    ("Le desaparece comida de la nevera. Poca. Lo justo para pensar que se lo está imaginando.",
     ["LE *DESAPARECE*", "COMIDA", "DE LA *NEVERA*", "POCA…", "LO JUSTO", "PARA PENSAR", "QUE SE LO ESTÁ", "*IMAGINANDO*"],
     ["fridge", "fridge_shelf"]),
    ("Así que instala cámaras de seguridad que le envían imágenes al móvil.",
     ["ASÍ QUE INSTALA", "*CÁMARAS*", "QUE LE ENVÍAN", "IMÁGENES", "AL *MÓVIL*"],
     ["camera", "phone_idle"]),
    ("Un día, estando fuera, le llega una imagen. Su casa debería estar vacía. Pero hay alguien moviéndose dentro.",
     ["UN DÍA", "ESTANDO FUERA", "LE LLEGA", "UNA *IMAGEN*", "SU CASA", "DEBERÍA ESTAR", "*VACÍA*…", "PERO HAY *ALGUIEN*", "MOVIÉNDOSE", "*DENTRO*"],
     ["phone_alert", "cctv_figure", "cctv_zoom"]),
    ("Llama a la policía. Los agentes revisan la casa, habitación por habitación.",
     ["LLAMA A LA", "*POLICÍA*", "REVISAN", "LA CASA", "HABITACIÓN", "POR *HABITACIÓN*"],
     ["police", "hallway"]),
    ("Hasta que abren un armario. En el compartimento de arriba, en un hueco donde apenas cabe una persona, hay una mujer.",
     ["HASTA QUE ABREN", "UN *ARMARIO*", "EN EL HUECO", "DE *ARRIBA*", "DONDE APENAS", "CABE UNA PERSONA…", "HAY UNA", "*MUJER*"],
     ["closet_closed", "closet_open", "closet_top"]),
    ("Tiene cincuenta y ocho años. Había metido allí un colchón, y se mantenía aseada. Llevaba viviendo en ese armario cerca de un año.",
     ["TIENE", "*58 AÑOS*", "HABÍA METIDO", "UN *COLCHÓN*", "SE MANTENÍA", "ASEADA", "LLEVABA ALLÍ", "CERCA DE", "*UN AÑO*"],
     ["stat_58", "futon", "stat_year"]),
    ("A la policía le dijo que no tenía dónde vivir, y que entró un día que él se dejó la puerta sin cerrar.",
     ["NO TENÍA", "*DÓNDE VIVIR*", "ENTRÓ UN DÍA", "QUE ÉL SE DEJÓ", "LA *PUERTA*", "SIN *CERRAR*"],
     ["door", "door_close"]),
    ("La detuvieron por allanamiento de morada.",
     ["LA *DETUVIERON*", "POR ALLANAMIENTO", "DE *MORADA*"],
     ["case_file"]),
    ("Ahora piénsalo. ¿Cuándo fue la última vez que abriste ese armario que nunca usas?",
     ["AHORA", "*PIÉNSALO*…", "¿CUÁNDO FUE", "LA ÚLTIMA VEZ", "QUE ABRISTE", "ESE *ARMARIO*", "QUE *NUNCA* USAS?"],
     ["closet_gap", "end_card"]),
]

LEAD, GAP, TAIL = 0.25, 0.35, 1.6
_tj = os.path.join(HERE, "timings.json")
VOICE = json.load(open(_tj)) if os.path.exists(_tj) else [len(n) / 15 for n, _c, _s in SCENES_TXT]

SCENES = []   # (inicio, fin, narración, bloques, planos, inicio_voz, dur_voz)
_t = 0.0
for i, (n, c, s) in enumerate(SCENES_TXT):
    a = _t; v0 = a + (LEAD if i == 0 else 0.12); b = v0 + VOICE[i] + (TAIL if i == len(SCENES_TXT) - 1 else GAP)
    SCENES.append((round(a, 3), round(b, 3), n, c, s, v0, VOICE[i])); _t = b
TOTAL = round(_t, 3)

def scene_start(name):
    for sc in SCENES:
        if name in sc[4]: return sc[0]

def caption_timeline():
    out = []
    for (a, b, _n, chunks, _s, v0, vd) in SCENES:
        w = [len(c.replace("*", "")) + 5 for c in chunks]
        tot = sum(w); t = v0
        for k, (c, wi) in enumerate(zip(chunks, w)):
            d = vd * wi / tot
            end = t + d if k < len(chunks) - 1 else min(b, t + d + 0.25)
            out.append((t, end, c)); t += d
    return out

def shot_timeline():
    out = []
    for (a, b, _n, _c, shots, _v0, _vd) in SCENES:
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
