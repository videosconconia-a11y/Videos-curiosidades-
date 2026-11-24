# "EL MISTERIO DE MELILLA" · anuncio TikTok de placas/tarjetas NFC para reseñas de Google
TOTAL = 40.0

SCENES = [
    (0.0, 3.0, "gancho"), (3.0, 7.0, "invasion"), (7.0, 11.5, "descubrimiento"), (11.5, 16.0, "revelacion"),
    (16.0, 25.0, "documental"), (25.0, 30.0, "giro"), (30.0, 35.0, "orgullo"), (35.0, 40.0, "venta"),
]

# Voz: (inicio, papel, texto). Papeles: misterio / narrador / alien / documental
VOICE = [
    (0.55, "misterio", "Algo acaba de aterrizar en Melilla…"),
    (3.55, "narrador", "Los extraterrestres han venido a buscar algo."),
    (9.55, "alien", "¿Qué es este objeto?"),
    (12.85, "alien", "¡Increíble! ¡Un solo toque y puedes acceder a las reseñas!"),
    (16.25, "documental", "Aquí observamos al comerciante melillense en su hábitat natural. Ahora dispone de tecnología NFC para facilitar las opiniones de sus clientes."),
    (25.35, "alien", "En nuestro planeta llevamos quinientos años buscando algo así."),
    (30.25, "narrador", "No hace falta venir de otro planeta. El futuro está aquí. Somos de Melilla."),
    (35.15, "narrador", "Da el salto al futuro. Tarjetas NFC para tu negocio. Escríbenos por privado."),
]

SHOTS = [
    (0.0, 0.45, "black"),
    (0.45, 3.0, "aerial_ufo"),
    (3.0, 4.0, "fly_puerto"),
    (4.0, 5.0, "fly_search"),
    (5.0, 7.0, "landing"),
    (7.0, 9.1, "barber_enter"),
    (9.1, 11.5, "barber_zoom"),
    (11.5, 16.0, "tap"),
    (16.0, 17.6, "doc_pergola"),
    (17.6, 19.0, "doc_barber"),
    (19.0, 20.4, "doc_cafe"),
    (20.4, 21.8, "doc_mercado"),
    (21.8, 23.3, "doc_calle"),
    (23.3, 25.0, "doc_tienda"),
    (25.0, 30.0, "alien_cam"),
    (30.0, 30.8, "o_marina"),
    (30.8, 31.6, "o_reconquista"),
    (31.6, 32.4, "o_culturas"),
    (32.4, 33.2, "o_sagrado"),
    (33.2, 34.0, "o_playa"),
    (34.0, 35.0, "o_faro"),
    (35.0, 40.0, "space"),
]

TITLES = [
    (0.6, 2.95, ["MELILLA,", "ESTO NO ES", "UN SIMULACRO"], "alert"),
    (3.2, 6.95, ["LOS EXTRATERRESTRES", "HAN VENIDO A", "BUSCAR ALGO"], "invade"),
    (9.25, 11.45, ["¿QUÉ ES", "ESTE OBJETO?"], "question"),
    (12.75, 15.95, ["¡UN SOLO", "TOQUE!"], "hero"),
    (27.6, 29.95, ["LA TECNOLOGÍA", "YA ESTÁ", "EN MELILLA"], "hero_low"),
    (30.05, 31.6, ["NO HACE FALTA VENIR", "DE OTRO PLANETA"], "cine"),
    (31.6, 33.3, ["EL FUTURO", "ESTÁ AQUÍ"], "cine"),
    (33.3, 34.95, ["SOMOS", "DE MELILLA"], "cine"),
]

# Subtítulos del marciano (su voz va procesada): (inicio, fin, texto)
ALIEN_SUBS = [
    (9.55, 11.4, "¿Qué es este objeto?"),
    (12.85, 14.4, "¡Increíble!"), (14.4, 16.0, "¡Un solo toque y puedes acceder a las reseñas!"),
    (25.35, 27.3, "En nuestro planeta llevamos"), (27.3, 29.1, "500 años buscando algo así."),
]

HITS = [0.45, 3.0, 5.0, 6.05, 9.1, 12.6, 25.0, 30.0, 35.0, 35.35]

def subtitle_blocks():
    return [
        (0.55, 2.9, "Algo acaba de aterrizar en Melilla…"),
        (3.55, 6.4, "Los extraterrestres han venido a buscar algo."),
        (9.55, 11.0, "[Extraterrestre] ¿Qué es este objeto?"),
        (12.85, 14.4, "[Extraterrestre] ¡Increíble!"), (14.4, 16.0, "¡Un solo toque y puedes acceder a las reseñas!"),
        (16.25, 18.3, "Aquí observamos al comerciante melillense"), (18.3, 20.3, "en su hábitat natural."),
        (20.3, 22.6, "Ahora dispone de tecnología NFC"), (22.6, 24.9, "para facilitar las opiniones de sus clientes."),
        (25.35, 27.3, "[Extraterrestre] En nuestro planeta llevamos"), (27.3, 29.1, "500 años buscando algo así."),
        (30.25, 32.0, "No hace falta venir de otro planeta."), (32.0, 33.4, "El futuro está aquí."), (33.4, 34.8, "Somos de Melilla."),
        (35.15, 36.6, "Da el salto al futuro."), (36.6, 38.2, "Tarjetas NFC para tu negocio."), (38.2, 39.7, "Escríbenos por privado."),
    ]

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(subtitle_blocks(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c}\n\n")
