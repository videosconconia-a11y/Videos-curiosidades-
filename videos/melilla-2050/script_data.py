# "MELILLA 2050 – EL FUTURO HA LLEGADO" · anuncio de tarjetas NFC para reseñas de Google
# Todo el guion, los tiempos y los textos en pantalla viven aquí.

TOTAL = 40.0

# Escenas: (inicio, fin, nombre)
SCENES = [
    (0.0, 3.0, "gancho"),
    (3.0, 6.0, "caos"),
    (6.0, 10.0, "aparicion"),
    (10.0, 14.0, "poder"),
    (14.0, 19.0, "montage"),
    (19.0, 25.0, "giro"),
    (25.0, 32.0, "orgullo"),
    (32.0, 40.0, "final"),
]

# Voz: (inicio, voz, texto). voz "narrador" = grave y misteriosa; "presentadora" = informativo.
VOICE = [
    (0.05, "narrador", "Atención, Melilla. La forma de conseguir reseñas está cambiando."),
    (3.78, "narrador", "¿Todavía pides reseñas a la antigua?"),
    (6.7, "narrador", "Hasta que llegó… esto."),
    (10.15, "narrador", "Un toque con el móvil… y se abre tu página de reseñas de Google."),
    (14.2, "narrador", "Más fácil."),
    (15.7, "narrador", "Más cómodo."),
    (17.25, "narrador", "Más tecnológico."),
    (19.12, "presentadora", "Última hora: los negocios de Melilla ya pueden utilizar tecnología NFC para facilitar las reseñas de sus clientes."),
    (25.62, "narrador", "No somos una multinacional. Somos de Melilla. Y apostamos por los negocios de aquí."),
    (32.6, "narrador", "El futuro de tu negocio está a un toque. Consigue tu tarjeta NFC. Escríbenos por privado."),
]

# Planos: (inicio, fin, plano). Cambio cada 0,5–2,5 s.
SHOTS = [
    # 1 · GANCHO
    (0.0, 1.45, "aerial"),
    (1.45, 3.0, "night_city"),
    # 2 · CAOS
    (3.0, 3.6, "shop_pergola"),
    (3.6, 4.2, "shop_mercado"),
    (4.2, 4.8, "shop_barber1"),
    (4.8, 5.4, "shop_avenida"),
    (5.4, 6.0, "error_screen"),
    # 3 · APARICIÓN
    (6.0, 10.0, "plaza_card"),
    # 4 · EL PODER
    (10.0, 14.0, "tap"),
    # 5 · MONTAGE LOCO
    (14.0, 14.7, "m_playa"),
    (14.7, 15.4, "m_marina"),
    (15.4, 16.1, "m_tortosa"),
    (16.1, 16.8, "m_barber2"),
    (16.8, 17.5, "m_restaurante"),
    (17.5, 18.2, "m_tienda"),
    (18.2, 19.0, "m_card"),
    # 6 · GIRO
    (19.0, 24.4, "news"),
    (24.4, 25.0, "card_glitch"),
    # 7 · ORGULLO LOCAL
    (25.0, 26.2, "o_vieja"),
    (26.2, 27.4, "o_asamblea"),
    (27.4, 28.6, "o_faro"),
    (28.6, 29.8, "o_parque"),
    (29.8, 31.0, "o_casino"),
    (31.0, 32.0, "o_cala"),
    # 8 · FINAL
    (32.0, 40.0, "finale"),
]

# Textos grandes en pantalla: (inicio, fin, líneas, estilo)
TITLES = [
    (0.25, 2.95, ["ÚLTIMA HORA", "¡MELILLA HA ENTRADO", "EN EL FUTURO!"], "alert"),
    (3.1, 5.95, ["¿TODAVÍA PIDES", "RESEÑAS", "A LA ANTIGUA?"], "chaos"),
    (7.6, 9.95, ["HA LLEGADO", "LA SOLUCIÓN"], "hero"),
    (10.2, 12.0, ["UN TOQUE."], "hero"),
    (12.0, 13.95, ["ACCESO DIRECTO", "A TUS RESEÑAS"], "hero"),
    (14.05, 15.6, ["MÁS FÁCIL"], "punch"),
    (15.6, 17.15, ["MÁS CÓMODO"], "punch"),
    (17.15, 18.95, ["MÁS", "TECNOLÓGICO"], "punch"),
    (25.1, 27.4, ["NO SOMOS UNA", "MULTINACIONAL"], "cine"),
    (27.4, 29.7, ["SOMOS", "DE MELILLA"], "cine"),
    (29.7, 31.95, ["Y APOSTAMOS POR", "LOS NEGOCIOS", "DE AQUÍ"], "cine"),
]

# Golpes visuales (flash + temblor) y cortes con glitch
HITS = [0.0, 1.45, 3.0, 6.0, 8.15, 10.0, 11.2, 14.0, 19.0, 24.4, 25.0, 32.0, 35.3]

# Subtítulos (SRT) = la locución, en bloques cortos
def subtitle_blocks():
    return [
        (0.05, 1.5, "Atención, Melilla."), (1.5, 3.0, "La forma de conseguir reseñas está cambiando."),
        (3.78, 6.1, "¿Todavía pides reseñas a la antigua?"),
        (6.7, 8.6, "Hasta que llegó… esto."),
        (10.15, 11.6, "Un toque con el móvil…"), (11.6, 13.9, "y se abre tu página de reseñas de Google."),
        (14.2, 15.6, "Más fácil."), (15.7, 17.1, "Más cómodo."), (17.25, 18.8, "Más tecnológico."),
        (19.12, 21.2, "Última hora: los negocios de Melilla"), (21.2, 22.9, "ya pueden utilizar tecnología NFC"),
        (22.9, 25.4, "para facilitar las reseñas de sus clientes."),
        (25.62, 27.4, "No somos una multinacional."), (27.4, 29.0, "Somos de Melilla."),
        (29.0, 31.8, "Y apostamos por los negocios de aquí."),
        (32.6, 35.0, "El futuro de tu negocio está a un toque."), (35.0, 37.0, "Consigue tu tarjeta NFC."),
        (37.0, 39.5, "Escríbenos por privado."),
    ]

def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(subtitle_blocks(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c}\n\n")
