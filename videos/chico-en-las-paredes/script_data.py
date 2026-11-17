# Guion de "El chico que vivía dentro de las paredes" (Pepperell, EE. UU., 1986) — historia real.
# Una entrada por FRASE: (texto para la voz, [bloques de subtítulo], [planos], pausa_después_s)
# Cada frase tiene sus propios planos -> la imagen cambia exactamente cuando cambia lo que se narra.
# Los tiempos salen de la duración real de la voz (timings.json, generado por voice.py).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

LINES = [
    ("Durante semanas, esta familia oyó ruidos dentro de las paredes.",
     ["DURANTE *SEMANAS*", "ESTA FAMILIA", "OYÓ *RUIDOS*", "DENTRO DE", "LAS *PAREDES*"], ["wall_noise"], 0.15),
    ("Pensaban que era un fantasma.", ["PENSABAN QUE ERA", "UN *FANTASMA*"], ["ghost"], 0.2),
    ("Pero era un chico de dieciséis años… viviendo dentro de su casa.",
     ["PERO ERA", "UN *CHICO*", "DE *16 AÑOS*…", "VIVIENDO *DENTRO*", "DE SU CASA"], ["eye_gap"], 0.35),
    ("Pépperel, Massachusets. Mil novecientos ochenta y seis.",
     ["*PEPPERELL*", "MASSACHUSETTS", "*1986*"], ["house_ne"], 0.1),
    ("Un padre vive allí con sus hijas.", ["UN *PADRE*", "VIVE ALLÍ", "CON SUS *HIJAS*"], ["family_window"], 0.1),
    ("Y en la casa empiezan a pasar cosas.", ["Y EN LA CASA", "EMPIEZAN A PASAR", "*COSAS*"], ["living_dark"], 0.1),
    ("Desaparece comida.", ["DESAPARECE", "*COMIDA*"], ["fridge"], 0.05),
    ("Los objetos cambian de sitio.", ["LOS OBJETOS", "CAMBIAN DE *SITIO*"], ["objects_moved"], 0.1),
    ("Y en las paredes del sótano aparecen mensajes, escritos como si fuera sangre.",
     ["EN EL *SÓTANO*", "APARECEN", "*MENSAJES*", "ESCRITOS COMO", "SI FUERA *SANGRE*"], ["basement_msg"], 0.25),
    ("Lo que no saben es que alguien se mueve por huecos tan estrechos que nadie se fija en ellos.",
     ["LO QUE NO SABEN", "ES QUE *ALGUIEN*", "SE MUEVE POR", "*HUECOS*", "TAN ESTRECHOS", "QUE NADIE", "SE FIJA EN ELLOS"],
     ["cutaway"], 0.3),
    ("Diciembre de mil novecientos ochenta y seis. Las chicas vuelven a casa.",
     ["*DICIEMBRE* 1986", "LAS CHICAS", "VUELVEN A *CASA*"], ["date_card", "front_door"], 0.1),
    ("El padre registra las habitaciones.", ["EL PADRE", "REGISTRA", "LAS *HABITACIONES*"], ["hallway"], 0.1),
    ("Abre un armario.", ["ABRE UN", "*ARMARIO*"], ["closet_door"], 0.45),
    ("Y dentro hay un chico con la cara pintada… y un hacha en la mano.",
     ["Y DENTRO HAY", "UN *CHICO*", "CON LA CARA", "*PINTADA*…", "Y UN *HACHA*", "EN LA MANO"], ["closet_hatchet"], 0.2),
    ("Persigue a las chicas hasta un dormitorio.", ["PERSIGUE", "A LAS CHICAS", "HASTA UN", "*DORMITORIO*"], ["chase"], 0.1),
    ("La familia escapa saltando por la ventana.", ["LA FAMILIA", "*ESCAPA*", "SALTANDO POR", "LA *VENTANA*"], ["window_escape"], 0.15),
    ("La policía registra la casa. No hay nadie.", ["LA *POLICÍA*", "REGISTRA LA CASA", "NO HAY", "*NADIE*"], ["police"], 0.3),
    ("Hasta que lo encuentran escondido entre dos paredes.",
     ["HASTA QUE", "LO *ENCUENTRAN*", "ESCONDIDO", "ENTRE *DOS PAREDES*"], ["cutaway_found"], 0.3),
    ("Se llama Daniel La Plant.", ["SE LLAMA", "*DANIEL LAPLANTE*"], ["name_card"], 0.15),
    ("Pasa unos meses en un centro de menores. Pero en octubre de mil novecientos ochenta y siete sale bajo fianza.",
     ["PASA UNOS MESES", "EN UN CENTRO", "DE *MENORES*", "PERO EN", "*OCTUBRE* DE 1987", "SALE BAJO", "*FIANZA*"],
     ["bars", "bail"], 0.25),
    ("Menos de dos meses después, en el pueblo de al lado, mata a una madre y a sus dos hijos pequeños.",
     ["MENOS DE", "*DOS MESES*", "DESPUÉS", "EN EL PUEBLO", "DE AL LADO", "*MATA* A UNA MADRE", "Y A SUS", "*DOS HIJOS*"],
     ["newspaper", "candles"], 0.3),
    ("Hoy sigue en prisión, condenado a cadena perpetua.",
     ["HOY SIGUE", "EN *PRISIÓN*", "CONDENADO A", "*CADENA PERPETUA*"], ["prison"], 0.4),
    ("Así que esta noche, si oyes algo dentro de la pared… ¿seguro que es la casa?",
     ["ESTA *NOCHE*", "SI OYES ALGO", "DENTRO DE", "LA *PARED*…", "¿SEGURO QUE ES", "LA *CASA*?"], ["wall_end", "end_card"], 1.6),
]

LEAD = 0.2
_tj = os.path.join(HERE, "timings.json")
VOICE = json.load(open(_tj)) if os.path.exists(_tj) else [len(l[0]) / 15 for l in LINES]

SCENES = []   # (inicio, fin, texto, bloques, planos, inicio_voz, dur_voz)
_t = 0.0
for i, (n, c, s, pause) in enumerate(LINES):
    a = _t; v0 = a + (LEAD if i == 0 else 0.06); b = v0 + VOICE[i] + pause
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
            end = t + d if k < len(chunks) - 1 else b
            out.append((t, end, c)); t += d
    return out

def shot_timeline():
    """Con 2 planos en una frase, el corte cae en el límite de bloque de subtítulo más cercano a la mitad."""
    caps = caption_timeline(); out = []
    for (a, b, _n, chunks, shots, v0, vd) in SCENES:
        if len(shots) == 1: out.append((a, b, shots[0])); continue
        mine = [c for c in caps if a <= c[0] < b]
        cut = min((c[0] for c in mine[1:]), key=lambda x: abs(x - (a + b) / 2))
        out += [(a, cut, shots[0]), (cut, b, shots[1])]
    return out

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c.replace('*','')}\n\n")
