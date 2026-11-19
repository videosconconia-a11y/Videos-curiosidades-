# Guion de "Cleopatra, más cerca del iPhone que de las pirámides" (estilo: personajes 2D en un mundo 3D)
# Cada escena: (narración, [bloques de subtítulo], estado de la historia para la escena 3D)
# Los tiempos NO se escriben a mano: salen de la duración real de la voz (voz/duraciones.json).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = 0.12      # respiro mínimo entre frases (casi sin silencios, ver GUIA_ESTILO.md)
INTRO = 0.15    # la voz arranca casi en el primer cuadro
OUTRO = 2.4     # cola para la tarjeta final
# pronunciación solo para la voz (no cambia los subtítulos)
SAY = {"iPhone": "aifon", "Guiza": "Guisa"}

SCENES = [
    ("Cleopatra vivió más cerca del iPhone… que de la construcción de las pirámides.",
     ["*CLEOPATRA*", "VIVIÓ MÁS CERCA", "DEL *IPHONE*…", "QUE DE LAS", "*PIRÁMIDES*"],
     "gancho"),
    ("La Gran Pirámide de Guiza se terminó hacia el año dos mil quinientos sesenta antes de Cristo, con más de dos millones de bloques de piedra.",
     ["LA GRAN *PIRÁMIDE*", "SE TERMINÓ", "HACIA EL", "*2560 a. C.*", "CON MÁS DE", "*2 MILLONES*", "DE BLOQUES"],
     "piramide"),
    ("Cleopatra nació casi dos mil quinientos años después.",
     ["CLEOPATRA NACIÓ", "CASI *2.500 AÑOS*", "*DESPUÉS*"],
     "viaje1"),
    ("Y entre su muerte y el primer iPhone hay solo unos dos mil años.",
     ["Y ENTRE", "SU MUERTE", "Y EL *IPHONE*", "SOLO HAY", "*2.000 AÑOS*"],
     "viaje2"),
    ("¿El truco? Imaginamos el antiguo Egipto como una sola época… pero duró unos tres mil años.",
     ["¿EL *TRUCO*?", "IMAGINAMOS", "EL ANTIGUO EGIPTO", "COMO *UNA* ÉPOCA…", "PERO DURÓ", "*3.000 AÑOS*"],
     "mapa"),
    ("Tutankamón, el faraón más famoso, vivió mil doscientos años después de la Gran Pirámide… y aun así, mil trescientos antes que Cleopatra.",
     ["*TUTANKAMÓN*", "VIVIÓ", "*1.200 AÑOS*", "DESPUÉS DE", "LA PIRÁMIDE…", "Y AUN ASÍ", "*1.300* ANTES", "QUE CLEOPATRA"],
     "tut"),
    ("Para Cleopatra, las pirámides ya eran ruinas antiguas. Griegos y romanos viajaban a verlas como turistas, y grababan sus nombres en los monumentos.",
     ["PARA ELLA", "YA ERAN", "*RUINAS* ANTIGUAS", "IBAN *TURISTAS*", "GRIEGOS", "Y ROMANOS", "Y GRABABAN", "SUS *NOMBRES*"],
     "turistas"),
    ("Y ella ni siquiera era de origen egipcio: descendía de Ptolomeo, un general de Alejandro Magno.",
     ["Y NI SIQUIERA", "ERA *EGIPCIA*", "DESCENDÍA", "DE *PTOLOMEO*", "GENERAL DE", "*ALEJANDRO MAGNO*"],
     "alejandro"),
    ("Según Plutarco, sus antepasados ni se molestaron en aprender egipcio. Ella sí lo aprendió.",
     ["SEGÚN *PLUTARCO*", "SUS ANTEPASADOS", "NO APRENDIERON", "*EGIPCIO*", "ELLA *SÍ*"],
     "plutarco"),
    ("Y hay más: mientras se construían las pirámides, en una isla del Ártico todavía vivían mamuts.",
     ["Y HAY MÁS", "MIENTRAS", "SE ALZABAN", "LAS PIRÁMIDES", "TODAVÍA VIVÍAN", "*MAMUTS*"],
     "mamuts"),
    ("El tiempo es mucho más largo de lo que parece. ¿Qué otra fecha crees que nos sorprendería? Te leo en comentarios.",
     ["EL *TIEMPO*", "ES MÁS LARGO", "DE LO QUE *PARECE*", "¿QUÉ OTRA *FECHA*", "NOS *SORPRENDERÍA*?", "TE LEO EN", "*COMENTARIOS*"],
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
