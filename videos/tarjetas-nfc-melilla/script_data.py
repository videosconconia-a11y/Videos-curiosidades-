# Guion, tiempos y planos del anuncio "El gadget que Melilla no sabía que necesitaba"
# VOICE: (inicio, texto) — locución (Piper TTS, voz es_ES). TITLES: (inicio, fin, líneas, estilo)
# SHOTS: (inicio, fin, plano). Las fotos reales de Melilla se usan una sola vez cada una.

VOICE = [
    (0.35, "Hemos encontrado un pequeño gadget que puede facilitarte algo muy importante."),
    (4.30, "Parece una tarjeta normal… pero no lo es."),
    (6.45, "Acercas el móvil. Tocas. Y se abre la página de reseñas."),
    (10.95, "Tecnología para los negocios de aquí."),
    (14.20, "Barberías. Restaurantes. Tiendas. Cualquier negocio."),
    (19.10, "Tus clientes pueden acceder directamente a tu enlace de reseñas con un simple toque."),
    (24.40, "Melilla tiene futuro. Tiene talento. Y tiene tecnología."),
    (30.15, "Tu negocio también puede dar el salto. Tarjetas NFC. Escríbenos por privado."),
]

TITLES = [
    (0.15, 3.0, ["MELILLA,", "DEJA DE HACER", "*ESTO*", "EN TU NEGOCIO"], "hook"),
    (3.6, 6.0, ["PARECE UNA", "TARJETA NORMAL…", "*PERO NO LO ES*"], "mid", 1620),
    (6.2, 7.4, ["*ACERCAS.*"], "big"),
    (7.4, 8.6, ["*TOCAS.*"], "big"),
    (8.6, 10.0, ["*ACCEDES.*"], "big"),
    (11.0, 14.0, ["TECNOLOGÍA", "PARA LOS NEGOCIOS", "*DE AQUÍ*"], "mid"),
    (14.0, 15.25, ["PARA", "*BARBERÍAS*"], "mid"),
    (15.25, 16.5, ["PARA", "*RESTAURANTES*"], "mid"),
    (16.5, 17.75, ["PARA", "*TIENDAS*"], "mid"),
    (17.75, 19.0, ["PARA", "*CUALQUIER*", "*NEGOCIO*"], "mid"),
    (19.4, 24.0, ["MENOS PASOS.", "*MÁS COMODIDAD.*"], "mid"),
    (24.0, 26.0, ["MELILLA", "TIENE *FUTURO*"], "mid"),
    (26.0, 28.0, ["MELILLA", "TIENE *TALENTO*"], "mid"),
    (28.0, 30.0, ["MELILLA", "TIENE *TECNOLOGÍA*"], "mid"),
    (30.6, 33.0, ["TU NEGOCIO", "TAMBIÉN PUEDE", "*DAR EL SALTO*"], "hook", 420),
    (33.0, 35.4, ["*TARJETAS NFC*", "ESCRÍBENOS", "POR PRIVADO"], "cta"),
]

SHOTS = [
    (0.0, 3.0, "faro_hook"),
    (3.0, 4.5, "box_closed"),
    (4.5, 6.0, "box_open"),
    (6.0, 8.0, "tap_approach"),
    (8.0, 10.0, "tap_result"),
    (10.0, 11.4, "portal"),
    (11.4, 14.0, "murallas_game"),
    (14.0, 15.25, "biz_barber"),
    (15.25, 16.5, "biz_food"),
    (16.5, 17.75, "biz_shop"),
    (17.75, 19.0, "biz_any"),
    (19.0, 21.5, "hernandez_float"),
    (21.5, 24.0, "noray_float"),
    (24.0, 25.0, "m_faro"),
    (25.0, 26.0, "m_sanlorenzo"),
    (26.0, 27.0, "m_murallas"),
    (27.0, 28.0, "m_hernandez"),
    (28.0, 29.0, "m_calle1"),
    (29.0, 30.0, "m_calle2"),
    (30.0, 33.0, "hero_card"),
    (33.0, 35.4, "cta"),
]
TOTAL = 35.4

def write_srt(path, voice_timing):
    """voice_timing: lista de (inicio, fin, texto) ya medida con el audio real."""
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(voice_timing, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c}\n\n")
