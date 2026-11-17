# Guion del vídeo "Tu perro huele tus emociones"
# Cada escena: planos visuales + frases. Cada frase: (texto que lee la voz, [bloques de subtítulo]).
# Palabras entre *asteriscos* = resaltadas en el subtítulo.
# Los tiempos NO se escriben a mano: salen de la duración real de la voz (voice/durations.json),
# así la narración nunca se acelera y cada frase deja su pausa natural.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))

LEAD = 0.30          # silencio antes de la primera palabra
GAP = 0.34           # pausa entre frases de una misma escena
TAIL = 0.60          # pausa al final de cada escena (respiro + cambio visual)

SRC = [
    dict(shots=["nose_macro", "scent_in"], tail=0.55, phrases=[
        ("Tu perro sabe cuándo tienes miedo.", ["TU PERRO SABE", "CUÁNDO TIENES", "*MIEDO*"]),
        ("Y no lo adivina.", ["Y NO LO ADIVINA…"], 0.45),
        ("Lo huele.", ["LO *HUELE*"]),
    ]),
    dict(shots=["human_stress", "molecules", "dog_sniff"], phrases=[
        ("Cuando sientes estrés, tu cuerpo cambia por dentro.", ["CUANDO SIENTES", "*ESTRÉS*", "TU CUERPO", "CAMBIA POR DENTRO"]),
        ("Tu sudor y tu aliento liberan sustancias distintas.", ["TU *SUDOR*", "Y TU *ALIENTO*", "LIBERAN SUSTANCIAS", "*DISTINTAS*"]),
        ("Tú no las notas. Él, sí.", ["TÚ NO LAS NOTAS", "ÉL… *SÍ*"]),
    ]),
    dict(shots=["stat_300", "stat_6"], phrases=[
        ("Su nariz tiene hasta trescientos millones de receptores olfativos.", ["SU NARIZ TIENE", "HASTA", "*300 MILLONES*", "DE RECEPTORES", "OLFATIVOS"]),
        ("La tuya, unos seis millones.", ["LA TUYA…", "UNOS *6 MILLONES*"]),
    ]),
    dict(shots=["airflow", "receptors"], phrases=[
        ("Y al olfatear, el aire se divide en dos caminos: uno para respirar, y otro solo para oler.",
         ["AL OLFATEAR", "EL AIRE", "SE *DIVIDE*", "UNO PARA", "*RESPIRAR*", "Y OTRO", "SOLO PARA *OLER*"]),
    ]),
    dict(shots=["lab_vials", "dog_lineup"], phrases=[
        ("En Belfast tomaron sudor y aliento de personas antes y después de un examen estresante.",
         ["EN *BELFAST*", "TOMARON", "SUDOR Y ALIENTO", "ANTES Y DESPUÉS", "DE UN EXAMEN", "*ESTRESANTE*"]),
        ("Cuatro perros debían encontrar la del estrés.", ["CUATRO PERROS", "DEBÍAN ENCONTRAR", "LA DEL *ESTRÉS*"]),
    ]),
    dict(shots=["stat_94"], phrases=[
        ("Acertaron casi el noventa y cuatro por ciento de las veces.", ["ACERTARON", "CASI EL", "*94 %*", "DE LAS VECES"]),
    ]),
    dict(shots=["fear_sweat", "heart_fast", "dog_owner"], phrases=[
        ("En Italia, perros que olieron el sudor de personas asustadas se estresaron: su corazón se aceleró, y buscaron más a su dueño.",
         ["EN *ITALIA*", "PERROS QUE OLIERON", "SUDOR DE PERSONAS", "*ASUSTADAS*", "SE ESTRESARON", "SU *CORAZÓN*", "SE ACELERÓ", "Y BUSCARON", "A SU *DUEÑO*"]),
    ]),
    dict(shots=["happy_stranger"], phrases=[
        ("Con el olor de personas felices, en cambio, se acercaron más a un desconocido.",
         ["CON EL OLOR", "DE PERSONAS *FELICES*", "SE ACERCARON MÁS", "A UN *DESCONOCIDO*"]),
    ]),
    dict(shots=["brain_voice", "faces"], phrases=[
        ("Y no solo usan la nariz. Su cerebro reacciona al tono emocional de tu voz.",
         ["Y NO SOLO", "USAN LA NARIZ", "SU *CEREBRO*", "REACCIONA", "AL *TONO*", "DE TU VOZ"]),
        ("Si oyen una voz alegre, miran más la cara que expresa esa misma emoción.",
         ["SI OYEN", "UNA VOZ *ALEGRE*", "MIRAN MÁS", "LA CARA", "QUE EXPRESA", "ESA *EMOCIÓN*"]),
    ]),
    dict(shots=["gaze", "oxytocin"], phrases=[
        ("Y cuando os miráis a los ojos, los dos producís más oxitocina: la hormona del vínculo.",
         ["CUANDO OS MIRÁIS", "A LOS *OJOS*", "LOS DOS PRODUCÍS", "MÁS *OXITOCINA*", "LA HORMONA", "DEL *VÍNCULO*"]),
    ]),
    dict(shots=["hair_cortisol", "sunset_pair"], phrases=[
        ("En Suecia descubrieron que el estrés acumulado en el pelo de los perros se parece al de sus dueños.",
         ["EN *SUECIA*", "DESCUBRIERON QUE", "EL *ESTRÉS*", "GUARDADO EN SU PELO", "SE PARECE", "AL DE SU *DUEÑO*"]),
        ("Puedes disimular delante de cualquiera.", ["PUEDES DISIMULAR", "DELANTE DE", "*CUALQUIERA*…"], 0.55),
        ("Pero no delante de él.", ["PERO NO", "DELANTE DE *ÉL*"]),
    ]),
    dict(shots=["end_card"], tail=1.6, phrases=[
        ("¿Tu perro ha venido alguna vez a consolarte?", ["¿TU PERRO", "HA VENIDO", "ALGUNA VEZ", "A *CONSOLARTE*?"]),
    ]),
]

def all_phrases():
    return [p for s in SRC for p in s["phrases"]]

def _durations():
    path = os.path.join(HERE, "voice", "durations.json")
    if os.path.exists(path):
        with open(path) as f: d = json.load(f)
        if len(d) == len(all_phrases()): return d
    # sin voz generada: estimación ~14 caracteres/s
    return [len(p[0]) / 14.0 for p in all_phrases()]

def build():
    dur = _durations(); k = 0
    t = LEAD; scenes = []; phrase_times = []
    for si, s in enumerate(SRC):
        a = 0.0 if si == 0 else scenes[-1][1]
        ph = []
        for j, item in enumerate(s["phrases"]):
            say, chunks = item[0], item[1]
            gap = item[2] if len(item) > 2 else GAP
            d = dur[k]; k += 1
            ph.append((t, t + d, say, chunks)); phrase_times.append((t, t + d))
            t = t + d + gap
        t -= gap
        b = t + s.get("tail", TAIL)
        scenes.append((a, b, ph, s["shots"]))
        t = b + 0.12   # la voz empieza un pelín después del corte
    return scenes, phrase_times

SCENES, PHRASE_TIMES = build()
TOTAL = SCENES[-1][1]

def caption_timeline():
    out = []
    for (_a, _b, ph, _s) in SCENES:
        for (pa, pb, _say, chunks) in ph:
            w = [len(c.replace("*", "")) + 5 for c in chunks]
            tot = sum(w); t = pa - 0.05; span = (pb - pa) + 0.1
            for c, wi in zip(chunks, w):
                d = span * wi / tot
                out.append((t, t + d, c)); t += d
    # que cada bloque se quede en pantalla hasta que entre el siguiente (sin huecos cortos)
    fixed = []
    for i, (a, b, c) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else b + 0.4
        fixed.append((a, nxt if nxt - b < 0.6 else b + 0.3, c))
    return fixed

# Pesos opcionales de duración de cada plano dentro de su escena
SHOT_WEIGHTS = {"stat_300": 1.4, "human_stress": 1.1, "fear_sweat": 0.75, "heart_fast": 1.25, "sunset_pair": 0.9}

def shot_timeline():
    out = []
    for (a, b, _p, shots) in SCENES:
        w = [SHOT_WEIGHTS.get(s, 1.0) for s in shots]; tot = sum(w); t = a
        for s, wi in zip(shots, w):
            d = (b - a) * wi / tot
            out.append((t, t + d, s)); t += d
    return out

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c.replace('*','')}\n\n")

if __name__ == "__main__":
    for (a, b, ph, shots) in SCENES:
        print(f"{a:6.2f}-{b:6.2f} ({b-a:4.1f}s) {shots}")
    print("TOTAL", round(TOTAL, 2))
    for s in shot_timeline(): print(f"  {s[0]:6.2f} {s[1]-s[0]:4.1f}s {s[2]}")
