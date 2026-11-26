# «LA RESEÑA QUE DESTRUYÓ UNA FAMILIA» — telenovela absurda (40 s) para vender tarjetas NFC en Melilla
# VOICE: (inicio, personaje, texto, ajustes)   personaje: narr | rafa | sofia
# TITLES: (inicio, fin, líneas, estilo, y_centro)   *palabra* = resaltada
# SHOTS: (inicio, fin, plano)

VOICE = [
    (0.30, "narr", "En una ciudad donde todos se conocen… una reseña lo cambiaría todo."),
    (4.90, "rafa", "Llevo meses esperando que mis clientes encuentren mi perfil de Google…"),
    (9.35, "sofia", "¿Todavía no tienes una tarjeta NFC?"),
    (14.30, "sofia", "Solo tienes que acercar el móvil… y tus clientes podrán acceder directamente a tus reseñas."),
    (21.40, "rafa_grito", "¡¿Por qué nadie me lo había contado antes?!"),
    (26.40, "narr", "La tecnología ha llegado a Melilla."),
    (29.60, "narr", "Para barberías, restaurantes y comercios."),
    (35.20, "rafa", "Yo solo quería que mis clientes pudieran dejar su opinión más fácilmente…"),
]
SPEAKER = {"narr": "Narrador", "rafa": "RAFA", "rafa_grito": "RAFA", "sofia": "SOFÍA"}

TITLES = [
    (0.25, 2.25, ["MELILLA…", "NADIE ESTABA PREPARADO", "PARA *ESTA TRAICIÓN*"], "drama", 860),
    (2.3, 4.0, ["LA RESEÑA", "QUE DESTRUYÓ", "UNA FAMILIA"], "logo", 820),
    (10.9, 12.4, ["¡NO PUEDE SER!"], "shock", 330),
    (26.3, 29.4, ["LA TECNOLOGÍA", "HA LLEGADO", "A *MELILLA*"], "drama", 330),
    (29.4, 33.0, ["PARA BARBERÍAS,", "RESTAURANTES", "Y *COMERCIOS*"], "drama", 330),
    (35.4, 38.4, ["NO ESPERES", "AL *PRÓXIMO CAPÍTULO*"], "drama", 300),
    (38.4, 40.0, ["CONSIGUE TU", "*TARJETA NFC*", "ESCRÍBENOS", "POR PRIVADO"], "cta", 1430),
]

# rótulos de personaje (estilo telenovela)
LOWER = [
    (4.4, 7.2, "RAFA", "el barbero"),
    (9.2, 10.8, "SOFÍA", "la del restaurante de enfrente"),
]

SHOTS = [
    (0.0, 2.25, "faro_acantilado"),
    (2.25, 4.0, "faro_puerto"),
    (4.0, 6.6, "rafa_movil"),
    (6.6, 9.0, "rafa_lagrima"),
    (9.0, 10.8, "puerta_sofia"),
    (10.8, 12.4, "zoom_shock"),
    (12.4, 14.0, "sofia_ceja"),
    (14.0, 16.0, "tarjeta_epica"),
    (16.0, 20.0, "demo_toque"),
    (20.0, 21.2, "murallas"),
    (21.2, 22.9, "grito_cielo"),
    (22.9, 23.9, "noray"),
    (23.9, 24.9, "calle"),
    (24.9, 26.0, "rocas"),
    (26.0, 29.5, "familia_altar"),
    (29.5, 33.0, "familia_caras"),
    (33.0, 35.0, "tarjeta_final"),
    (35.0, 38.4, "rafa_camara"),
    (38.4, 40.0, "continuara"),
]
TOTAL = 40.0

def write_srt(path, timing):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, who, c) in enumerate(timing, 1):
            name = SPEAKER[who]
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{'' if who == 'narr' else name + ': '}{c}\n\n")
