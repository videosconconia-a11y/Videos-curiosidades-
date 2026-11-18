# Guion del vídeo "El iceberg de GTA 6"
# Cada escena: (narración que lee la voz, [bloques de subtítulo], [planos visuales])
# Los tiempos NO se escriben a mano: salen de la duración real de la voz (voice/timings.json, lo crea tts.py).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

SCRIPT = [
    ("Trece años. Es lo que ha tardado GTA 6… y su iceberg esconde datos que casi nadie conoce.",
     ["*13 AÑOS*", "ES LO QUE", "HA TARDADO", "*GTA 6*", "Y SU *ICEBERG*", "ESCONDE DATOS", "QUE CASI NADIE", "*CONOCE*"],
     ["hook_13", "iceberg_reveal"]),
    ("Nivel uno. Sale el diecinueve de noviembre, en PlayStation 5 y Xbox Series. ¿Y en PC? Ni fecha.",
     ["*NIVEL 1*", "SALE EL", "*19 DE NOVIEMBRE*", "DE 2026", "PS5 Y", "XBOX SERIES", "¿EN PC?", "*NI FECHA*"],
     ["level_1", "calendar", "consoles"]),
    ("Nivel dos. Vuelve Vice City, pero dentro de Leonida, un estado inventado inspirado en Florida.",
     ["*NIVEL 2*", "VUELVE", "*VICE CITY*", "DENTRO DE", "*LEONIDA*", "UN ESTADO", "INVENTADO", "COMO *FLORIDA*"],
     ["level_2", "city", "map"]),
    ("Nivel tres. Por primera vez, una pareja protagonista: Lucía y Jason, dos criminales al estilo Bonnie y Clyde.",
     ["*NIVEL 3*", "POR PRIMERA VEZ", "UNA *PAREJA*", "PROTAGONISTA", "*LUCÍA* Y *JASON*", "DOS CRIMINALES", "AL ESTILO", "*BONNIE Y CLYDE*"],
     ["level_3", "duo"]),
    ("Nivel cuatro. La espera más larga de la saga: del tres al cuatro, siete años; del cuatro al cinco, cinco… y ahora, trece.",
     ["*NIVEL 4*", "LA ESPERA", "MÁS *LARGA*", "DEL III AL IV", "*7 AÑOS*", "DEL IV AL V", "*5 AÑOS*", "Y AHORA…", "*13 AÑOS*"],
     ["level_4", "timeline", "timeline_13"]),
    ("Nivel cinco. Su primer tráiler se filtró y salió antes de hora… y aun así batió un récord mundial: noventa millones de visitas en YouTube en un día.",
     ["*NIVEL 5*", "SU PRIMER TRÁILER", "SE *FILTRÓ*", "Y SALIÓ ANTES", "Y AUN ASÍ", "*RÉCORD MUNDIAL*", "*90 MILLONES*", "EN YOUTUBE", "EN UN DÍA"],
     ["level_5", "leak", "stat_90"]),
    ("Nivel seis. El segundo, según Rockstar: cuatrocientos setenta y cinco millones de visitas en veinticuatro horas, sumando todas las plataformas.",
     ["*NIVEL 6*", "EL SEGUNDO,", "SEGÚN ROCKSTAR:", "*475 MILLONES*", "DE VISITAS", "*EN 24 HORAS*", "SUMANDO TODAS", "LAS PLATAFORMAS"],
     ["level_6", "stat_475", "stat_475b"]),
    ("Y nivel siete, el fondo: el GTA 5 ha vendido más de doscientos treinta millones de copias. Ese es el listón que tiene que superar.",
     ["Y *NIVEL 7*", "EL *FONDO*", "GTA V", "HA VENDIDO", "*+230 MILLONES*", "DE COPIAS", "ESE ES", "EL *LISTÓN*", "A SUPERAR"],
     ["level_7", "stat_230", "boxes"]),
    ("¿Lo jugarás el primer día… o esperarás al PC? Te leo en comentarios.",
     ["¿LO JUGARÁS", "EL *PRIMER DÍA*…", "O ESPERARÁS", "AL *PC*?", "TE LEO EN", "*COMENTARIOS*"],
     ["end_q", "end_card"]),
]

LEAD, GAP, TAIL = 0.15, 0.26, 0.85   # silencio al principio, entre escenas y al final

def _durations():
    p = os.path.join(HERE, "voice", "timings.json")
    if os.path.exists(p):
        return json.load(open(p))["durations"]
    return [len(n) / 15.0 for n, _c, _v in SCRIPT]   # estimación si aún no hay voz

def build_scenes():
    out, t = [], 0.0
    for i, ((n, c, v), d) in enumerate(zip(SCRIPT, _durations())):
        a = t
        voice_at = a + (LEAD if i == 0 else GAP / 2)
        b = voice_at + d + (TAIL if i == len(SCRIPT) - 1 else GAP / 2)
        out.append((a, b, n, c, v, voice_at))
        t = b
    return out

_S = build_scenes()
SCENES = [s[:5] for s in _S]
VOICE_AT = [s[5] for s in _S]
TOTAL = round(_S[-1][1], 3)

def caption_timeline():
    out = []
    for i, ((a, b, _n, chunks, _v), va) in enumerate(zip(SCENES, VOICE_AT)):
        w = [len(c.replace("*", "")) + 4 for c in chunks]
        end = b - (TAIL - 0.4 if i == len(SCENES) - 1 else 0.05)
        tot = sum(w); t = va; span = end - va
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

def hits():
    # golpes de sonido/flash: inicio de cada nivel y de cada cifra grande
    return [round(a, 3) for (a, b, s) in shot_timeline()
            if s.startswith("level_") or s.startswith("stat_") or s in ("hook_13", "leak", "timeline_13")]

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c.replace('*','')}\n\n")

if __name__ == "__main__":
    for s, va in zip(SCENES, VOICE_AT):
        print(f"{s[0]:6.2f}-{s[1]:6.2f} voz@{va:6.2f} ({s[1]-s[0]:4.1f}s, {len(s[4])} planos) {s[2][:50]}")
    print("TOTAL", TOTAL)
