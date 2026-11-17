# Guion del vídeo "GTA 6: haz esto YA" (9:16, ~28 s, TikTok / Shorts)
#
# Cada frase: texto que se ve en subtítulos (display), texto que lee la voz (tts, con
# grafías fonéticas para que Piper pronuncie bien) y planos que acompañan a esa frase.
# Las imágenes cambian a la vez que la frase; dentro de la frase hay un corte cada 1–2 s.
#
# >>> TRUCOS: GTA 6 sale el 19/11/2026 y todavía no hay trucos verificados. Cuando los tengas,
# >>> cambia TRUCO_DINERO / TRUCO_COCHE (display y tts) y ejecuta ./build.sh: voz, subtítulos,
# >>> tiempos y cortes se recalculan solos.

TRUCO_DINERO = dict(display="DINERO a lo bestia, te lo dejo paso a paso en pantalla",
                    tts="dinero a lo bestia, te lo dejo paso a paso en pantalla")
TRUCO_COCHE = dict(display="un coche de lujo GRATIS, sin pagar ni un dólar",
                   tts="un coche de lujo gratis, sin pagar ni un dólar")

SENTENCES = [
    dict(display="Si tienes GTA 6, haz esto YA, antes de que Rockstar lo PARCHEE.",
         tts="Si tienes GTA seis, haz esto ya, antes de que Rokstar lo parchee.",
         shots=["alarm", "alarm_zoom"], start=0.0),
    dict(display="Ha salido hace nada y YA hay trucos que no van a durar ni una semana.",
         tts="Ha salido hace nada, y ya hay trucos que no van a durar ni una semana.",
         shots=["city_night", "street_cars", "palms_neon"], start=2.0),
    dict(display=f"El primero: {TRUCO_DINERO['display']}. Hazlo ahora, que esto vuela.",
         tts=f"El primero: {TRUCO_DINERO['tts']}. Hazlo ahora, que esto vuela.",
         shots=["title_money", "money_bags", "cash_rain", "money_counter", "cash_rain_close"], start=5.0),
    dict(display=f"Y este es una locura: {TRUCO_COCHE['display']}. Me hice con un deportivo en dos minutos.",
         tts=f"Y este es una locura: {TRUCO_COCHE['tts']}. Me hice con un deportivo en dos minutos.",
         shots=["title_car", "car_spin", "car_spin_close", "coast_drive", "coast_drive_close"], start=13.0),
    dict(display="Rockstar ya está avisada, así que no lo dejes para mañana.",
         tts="Rokstar ya está avisada, así que no lo dejes para mañana.",
         shots=["limited", "hourglass", "limited_zoom"], start=21.0),
    dict(display="Sígueme, que mañana subo uno todavía más bestia… y si tienes GTA 6, haz esto YA.",
         tts="Sígueme, que mañana subo uno todavía más bestia... y si tienes GTA seis, haz esto ya.",
         shots=["follow_pan", "follow_close", "alarm_tease"], start=25.0),
]

# Palabras clave en amarillo y más grandes (se comparan sin tildes ni signos; "PARCHE*" = prefijo)
KEYWORDS = ["DINERO", "GRATIS", "YA", "PARCHE*"]
# Palabras que disparan el "cha-ching"
MONEY_WORDS = ["DINERO", "GRATIS", "DOLAR"]

TARGET_TOTAL = 28.0
LEAD_IN = 0.08          # la voz arranca casi en el fotograma 0 (gancho inmediato)
GAP = 0.30              # pausa entre frases
VOICE_END_MAX = 27.75   # la última palabra cae justo antes del final (bucle)

TIMING_FILE = "cache/timing.json"


def load_timing():
    """Devuelve dict con 'total', 'sentences' [(a,b)], 'words' [(a,b,texto,idx_frase)] generado por voice.py."""
    import json, os
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, TIMING_FILE), encoding="utf-8") as f:
        return json.load(f)


def norm(w):
    import unicodedata, re
    w = unicodedata.normalize("NFD", w.upper())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9Ñ]", "", w)


def is_keyword(w):
    """Palabra clave = escrita en MAYÚSCULAS en el guion y presente en KEYWORDS."""
    letters = "".join(c for c in w if c.isalpha())
    if not letters or not letters.isupper():
        return False
    n = norm(w)
    for k in KEYWORDS:
        if k.endswith("*") and n.startswith(k[:-1]):
            return True
        if n == k:
            return True
    return False


def caption_groups(tm):
    """Agrupa palabras en bloques de 1–3 para subtítulos grandes; cada bloque = (a, b, [(a,b,word)])."""
    groups = []
    words = tm["words"]
    i = 0
    while i < len(words):
        g = [words[i]]
        j = i + 1
        while j < len(words) and (len(g) < 3 or norm(words[j][2]).isdigit()):
            prev, cur = words[j - 1], words[j]
            if cur[3] != prev[3]:
                break
            if prev[2].rstrip()[-1:] in ",.:…?!":
                break
            if is_keyword(cur[2]) or is_keyword(prev[2]):
                if len(g) >= 2:
                    break
            if sum(len(x[2]) for x in g) + len(cur[2]) > 16 and not norm(cur[2]).isdigit():
                break
            g.append(cur); j += 1
        groups.append(g); i = j
    out = []
    for k, g in enumerate(groups):
        a = g[0][0]
        b = groups[k + 1][0][0] if k + 1 < len(groups) and groups[k + 1][0][3] == g[0][3] else g[-1][1] + 0.25
        out.append((a, b, g))
    return out


def shot_timeline(tm):
    """Planos: cada frase se reparte entre sus planos, cortando en límites de palabra."""
    out = []
    sents = tm["sentences"]
    for si, s in enumerate(SENTENCES):
        a = 0.0 if si == 0 else sents[si][0]
        b = tm["total"] if si == len(SENTENCES) - 1 else sents[si + 1][0]
        n = len(s["shots"])
        wstarts = [w[0] for w in tm["words"] if w[3] == si]
        cuts = [a]
        for k in range(1, n):
            ideal = a + (b - a) * k / n
            c = min(wstarts, key=lambda x: abs(x - ideal)) if wstarts else ideal
            if c <= cuts[-1] + 0.6:
                c = ideal
            cuts.append(c)
        cuts.append(b)
        for k, name in enumerate(s["shots"]):
            out.append((cuts[k], cuts[k + 1], name, si))
    return out


def write_srt(path):
    tm = load_timing()

    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, g) in enumerate(caption_groups(tm), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{' '.join(w[2] for w in g)}\n\n")


def write_word_srt(path):
    """SRT palabra a palabra (para CapCut / editores que lo admitan)."""
    tm = load_timing()

    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, w, _s) in enumerate(tm["words"], 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{w}\n\n")
