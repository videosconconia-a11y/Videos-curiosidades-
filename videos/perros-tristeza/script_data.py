# Guion de "¿Cómo saben los perros que estás triste?"
# Cada segmento: (id, narración con *palabras destacadas*, [planos IA], pausa tras la frase en s)
# Los tiempos reales salen de la voz generada (voice/timings.json), así imagen, voz y
# subtítulos van siempre sincronizados.
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

SEGMENTS = [
    ("s00", "Tu perro podría saber que estás *triste*… ¡incluso antes de que tú mismo te des *cuenta*!",
     ["hook_eyes", "sad_woman_dog"], 0.35),
    ("s01", "Aunque sonrías. Aunque digas que estás *bien*.",
     ["fake_smile", "dog_watching_man"], 0.25),
    ("s02", "No es magia. Es *ciencia*. Y te lee por *tres vías* a la vez.",
     ["dog_tilt", "eye_reflection"], 0.3),
    ("s03", "Primera: tu *cara*. Distinguen un rostro *feliz* de uno *enfadado*… viendo solo la *mitad*: los ojos, o la boca.",
     ["dog_face_human", "angry_face_dog", "human_eyes"], 0.25),
    ("s04", "Y al mirarte, suelen fijarse en el lado *derecho* de tu cara… el que más *delata* las emociones.",
     ["dog_eye_macro", "dog_gaze_profile"], 0.35),
    ("s05", "Segunda: tu *voz*. En escáneres cerebrales, su cerebro separa *qué* dices… de *cómo* lo dices.",
     ["dog_ears", "dog_mri", "mri_monitor"], 0.3),
    ("s07", "Y la tercera, la más asombrosa: el *olfato*. Tiene hasta *trescientos millones* de receptores olfativos. Tú, unos *seis millones*.",
     ["nose_macro", "nose_particles", "dog_sniff_hand"], 0.3),
    ("s08", "En dos mil veintidós, unos perros detectaron el olor del *estrés* humano, en sudor y aliento, con casi un *noventa y cuatro por ciento* de acierto.",
     ["lab_dog_sample", "lab_samples", "stress_sweat"], 0.3),
    ("s09", "Puedes fingir una sonrisa… pero tu *olor* no finge.",
     ["mirror_smile", "nose_side"], 0.35),
    ("s10", "¿Y por qué se acercan? En un experimento, los perros acudían más a alguien que *lloraba* que a alguien que hablaba o tarareaba… aunque fuera un *desconocido*.",
     ["crying_dog_approach", "dog_head_knee", "stranger_crying"], 0.3),
    ("s11", "Influye el *contagio emocional*… y miles de años juntos. Cuando os miráis a los ojos, a los dos os sube la *oxitocina*, la hormona del *vínculo*.",
     ["prehistoric_fire", "mutual_gaze", "hug_dog"], 0.3),
    ("s12", "No leen tu *mente*. Pero leen *todo lo demás*.",
     ["dog_dark_portrait"], 0.4),
    ("s13", "Así que la próxima vez que tu perro se acerque a ti cuando estés teniendo un *mal día*… quizá haya notado *mucho más* de lo que imaginas.",
     ["rainy_stairs", "dog_lap_close", "bed_comfort"], 0.5),
    ("s14", "¿Tu perro también sabe cuándo estás *triste*? Cuéntamelo en los *comentarios*.",
     ["final_look"], 1.2),
]

LEAD_IN = 0.15     # silencio antes de la primera palabra

def plain(txt):
    return txt.replace("*", "")

def load_timings():
    p = os.path.join(HERE, "voice", "timings.json")
    return json.load(open(p, encoding="utf-8"))

def segment_times():
    """[(id, start, end_of_speech, end_with_pause)]"""
    tm = load_timings(); out = []; t = LEAD_IN
    for sid, _txt, _shots, pause in SEGMENTS:
        d = tm[sid]["dur"]
        out.append((sid, t, t + d, t + d + pause)); t += d + pause
    return out

def total():
    return segment_times()[-1][3]

def shot_timeline():
    """Reparte los planos de cada segmento según la posición de sus palabras."""
    out = []
    tm = load_timings()
    for (sid, a, e, b), (_, txt, shots, _p) in zip(segment_times(), SEGMENTS):
        n = len(shots)
        words = tm[sid].get("words") or []
        cuts = [a + (b - a) * k / n for k in range(n + 1)]
        if words and n > 1:  # corta en el inicio de palabra más cercano al reparto uniforme
            starts = [a + w["start"] for w in words]
            for k in range(1, n):
                cuts[k] = min(starts, key=lambda s: abs(s - cuts[k]))
        for k, s in enumerate(shots):
            out.append((cuts[k], cuts[k + 1], s))
    out[0] = (0.0, out[0][1], out[0][2])
    return out

def _norm(w):
    return re.sub(r"[^a-z0-9ñáéíóúü]", "", plain(w).lower())

def align(toks, words, dur):
    """Empareja tokens del guion con palabras de Whisper (difflib) e interpola huecos."""
    import difflib
    A = [_norm(t) for t in toks]; B = [_norm(w["w"]) for w in words]
    res = [None] * len(toks)
    for blk in difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            res[blk.a + k] = dict(words[blk.b + k])
    known = [i for i, r in enumerate(res) if r]
    for i in range(len(res)):
        if res[i] is None:
            prev = max([k for k in known if k < i], default=None); nxt = min([k for k in known if k > i], default=None)
            s0 = res[prev]["end"] if prev is not None else 0.0
            s1 = res[nxt]["start"] if nxt is not None else dur
            res[i] = {"start": s0, "end": max(s0 + 0.05, s1)}
    return res

def caption_timeline():
    """Bloques de 1–3 palabras sincronizados con la voz (tiempos por palabra de Whisper)."""
    out = []
    tm = load_timings()
    for (sid, a, e, b), (_, txt, _s, _p) in zip(segment_times(), SEGMENTS):
        toks = txt.split()
        words = tm[sid]["words"]
        # emparejar tokens del guion con palabras reconocidas (mismo número tras normalizar)
        if len(words) != len(toks) and words:
            words = align(toks, words, e - a)
        if len(words) != len(toks):
            # reparto proporcional a la longitud si no coinciden
            L = [len(plain(w)) + 2 for w in toks]; S = sum(L); acc = 0; words = []
            for l in L:
                words.append({"start": (e - a) * acc / S, "end": (e - a) * (acc + l) / S}); acc += l
        chunks, cur, clen = [], [], 0
        for tok, w in zip(toks, words):
            cur.append((tok, w)); clen += len(plain(tok)) + 1
            brk = re.search(r"[.,:;!?…]$", plain(tok).rstrip("¡¿")) is not None
            if brk or clen > 14 or len(cur) == 3:
                chunks.append(cur); cur, clen = [], 0
        if cur: chunks.append(cur)
        for i, ch in enumerate(chunks):
            s = a + ch[0][1]["start"] - 0.05
            nxt = a + chunks[i + 1][0][1]["start"] - 0.05 if i + 1 < len(chunks) else None
            en = a + ch[-1][1]["end"] + 0.25
            if nxt is not None: en = min(max(en, nxt), nxt)
            text = " ".join(t for t, _ in ch).upper()
            out.append((s, en, text))
    return out

def write_srt(path):
    def ts(x):
        ms = int(round(max(0, x) * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{plain(c)}\n\n")
