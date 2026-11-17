# Guion del Short "Cómo ganar dinero en GTA 6" (mecánicas confirmadas por Rockstar).
# tts:   texto que lee la voz (con ajustes de pronunciación: "GTA seis").
# caps:  subtítulos palabra a palabra; *palabra* = clave en amarillo. Mismo nº de palabras que tts.
# shots: planos. img = archivo en img/, fx = centro horizontal del encuadre (0–1),
#        efecto = zoom | pan | hook | step | circle | arrow | counter_down | counter_up | warn | end,
#        t = objetivo (x, y) en fracción de la imagen para círculos/flechas, w = palabra en la que empieza el plano.
import json, os

LINES = [
 dict(tts="Todo lo que tienes que saber para hacerte rico en GTA seis.",
      caps="*Todo* lo que tienes que *saber* para hacerte *rico* en *GTA* *6.*",
      shots=[dict(img="mediaDesktop", fx=0.5, e="hook"),
             dict(img="Vice_City_18", fx=0.12, e="counter_up", w=8)]),
 dict(tts="Y quédate hasta el final, porque hay un error que te puede dejar sin nada.",
      caps="Y *quédate* hasta el *final,* porque hay un *error* que te puede dejar *sin* *nada.*",
      shots=[dict(img="Vice_City_27", fx=0.5, e="pan"),
             dict(img="Jason_Duval_Video_Clip", fx=0.68, e="counter_down", w=8)]),
 dict(tts="Paso uno: empieza por lo pequeño. Tiendas y gasolineras... dinero en efectivo, directo al bolsillo.",
      caps="*PASO* *1:* empieza por lo pequeño. *Tiendas* y *gasolineras...* dinero en *efectivo,* directo al bolsillo.",
      shots=[dict(img="Jason_and_Lucia_15", fx=0.55, e="step", n=1),
             dict(img="Vice_City_22", fx=0.72, e="circle", t=(0.79, 0.24), w=8),
             dict(img="VINTAGE_VICE_CITY_WEAPON_PATTERN", fx=0.3, e="circle", t=(0.27, 0.68), w=11)]),
 dict(tts="Paso dos: apunta más alto. En los golpes grandes no siempre hay billetes: hay joyas, lingotes de oro... o droga.",
      caps="*PASO* *2:* apunta más alto. En los *golpes* *grandes* no siempre hay billetes: hay *joyas,* *lingotes* *de* *oro...* o *droga.*",
      shots=[dict(img="Raul_Bautista_01", fx=0.55, e="step", n=2),
             dict(img="Raul_Bautista_04", fx=0.45, e="zoom", w=5),
             dict(img="Raul_Bautista_02", fx=0.42, e="zoom", w=12),
             dict(img="Port_Gellhorn_03", fx=0.42, e="circle", t=(0.41, 0.47), w=17)]),
 dict(tts="Paso tres: ese botín no vale nada hasta que se lo vendes a un perista. Hay uno para joyas, otro para el oro, otro para la droga... y se desbloquean con la historia.",
      caps="*PASO* *3:* ese *botín* no vale *nada* hasta que se lo vendes a un *perista.* Hay uno para *joyas,* otro para el *oro,* otro para la *droga...* y se *desbloquean* con la *historia.*",
      shots=[dict(img="Port_Gellhorn_02", fx=0.42, e="step", n=3),
             dict(img="Boobie_Ike_01", fx=0.66, e="circle", t=(0.66, 0.76), w=9),
             dict(img="Brian_Heder_03", fx=0.55, e="pan", w=15),
             dict(img="Ambrosia_04", fx=0.5, e="zoom", w=21),
             dict(img="Jason_Lucia_Rooftop_portrait", fx=0.5, e="zoom", w=27)]),
 dict(tts="Paso cuatro: roba coches por encargo. Te llegan al móvil... y te pagan según cómo llegue el coche. Si está destrozado, cobras menos.",
      caps="*PASO* *4:* roba *coches* por *encargo.* Te llegan al *móvil...* y te *pagan* según cómo llegue el coche. Si está *destrozado,* cobras *menos.*",
      shots=[dict(img="ULTIMATE_EDITION_GROTTI_CHEETAH_01", fx=0.45, e="step", n=4),
             dict(img="Jason_Duval_04", fx=0.33, e="circle", t=(0.32, 0.53), w=6),
             dict(img="ULTIMATE_EDITION_GROTTI_CHEETAH_02", fx=0.52, e="arrow", t=(0.60, 0.66), w=10),
             dict(img="Jason_Duval_18", fx=0.3, e="zoom", w=18)]),
 dict(tts="Y ojo al error que te puede arruinar: si mueres con mucho efectivo encima, puedes perder buena parte... o todo. Pasa antes por el cajero.",
      caps="Y *ojo* al *error* que te puede *arruinar:* si *mueres* con mucho *efectivo* encima, puedes perder buena parte... o *TODO.* Pasa antes por el *cajero.*",
      shots=[dict(img="Vice_City_17", fx=0.45, e="warn"),
             dict(img="Lucia_Caminos_14", fx=0.4, e="zoom", w=8),
             dict(img="Jason_Duval_11", fx=0.45, e="counter_down", w=14),
             dict(img="Vice_City_18", fx=0.12, e="zoom", w=20)]),
 dict(tts="¿Cuánto dinero llevas tú? Te leo en comentarios.",
      caps="¿Cuánto *dinero* llevas *tú?* Te leo en *comentarios.*",
      shots=[dict(img="Jason_Lucia_Lock_And_Load_phone", fx=0.5, e="end")]),
]
GAP = 0.30    # silencio entre frases (s)
LEAD = 0.15   # silencio inicial
TAIL = 1.6    # cola final con la tarjeta de cierre
FPS = 30

HERE = os.path.dirname(os.path.abspath(__file__))

def timeline():
    """Devuelve (frases, palabras, planos, total) con tiempos absolutos."""
    tim = json.load(open(os.path.join(HERE, "voz", "timings.json"), encoding="utf-8"))
    t = LEAD; lines = []; words = []; shots = []
    for li, (L, T) in enumerate(zip(LINES, tim)):
        caps = L["caps"].split()
        assert len(caps) == len(T["words"]), (li, len(caps), len(T["words"]))
        speech_end = T["words"][-1][1] + 0.12
        lines.append(dict(i=li, start=t, end=t + speech_end))
        for (a, b, _w), c in zip(T["words"], caps):
            words.append(dict(line=li, a=t + a, b=t + b, text=c.replace("*", ""), key=c.count("*") >= 2))
        t += speech_end + GAP
    total = lines[-1]["end"] + TAIL
    for li, L in enumerate(LINES):
        lw = [w for w in words if w["line"] == li]
        starts = []
        for si, s in enumerate(L["shots"]):
            starts.append(lines[li]["start"] if si == 0 else lw[s["w"]]["a"] - 0.05)
        ends = starts[1:] + [lines[li + 1]["start"] if li + 1 < len(LINES) else total]
        for s, a, b in zip(L["shots"], starts, ends):
            shots.append(dict(s, a=a, b=b, line=li))
    return lines, words, shots, total

def write_srt(path):
    _l, words, _s, _t = timeline()
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    # Bloques de hasta 4 palabras, cortando en puntuación
    blocks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or w["text"][-1] in ".,:?…" or w is words[-1] or words[words.index(w) + 1]["line"] != w["line"]:
            blocks.append(cur); cur = []
    with open(path, "w", encoding="utf-8") as f:
        for i, b in enumerate(blocks, 1):
            end = b[-1]['b'] + 0.1
            if i < len(blocks): end = min(end, blocks[i][0]['a'] - 0.01)
            f.write(f"{i}\n{ts(b[0]['a'])} --> {ts(end)}\n{' '.join(w['text'] for w in b)}\n\n")

if __name__ == "__main__":
    l, w, s, t = timeline()
    print("total", round(t, 2))
    for x in s: print(round(x["a"], 2), round(x["b"] - x["a"], 2), x["img"], x["e"])
