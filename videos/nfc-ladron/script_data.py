# "¿TÚ SABES LO QUE ES UNA NFC?" · anuncio de etiquetas NFC (30 €) · sketch de humor absurdo en Melilla
TOTAL = 40.0
PRICE = "30 €"
PHONE = "+34 603 11 45 26"

SCENES = [
    (0.0, 1.95, "gancho"), (1.95, 5.75, "calma"), (5.75, 10.0, "explicacion"), (10.0, 18.3, "usos"),
    (18.3, 24.4, "nada"), (24.4, 26.3, "vuelta"), (26.3, 34.0, "a_camara"), (34.0, 40.0, "cierre"),
]

# Voz: (inicio, personaje, texto que se locuta, texto del subtítulo)
VOICE = [
    (0.2,  "cliente",    "¡Que se está llevando las cosas!", "¡Que se está llevando las *cosas*!"),
    (2.05, "dependiente", "Espera, espera… ¿Tú sabes lo que es una NFC?", "Espera, espera… ¿Tú sabes lo que es una *NFC*?"),
    (5.05, "cliente",    "¿¡Ahora!?", "¿¡*AHORA*!?"),
    (5.8,  "dependiente", "Acercas el móvil a una etiqueta compatible… y se abre lo que tú quieras.", "Acercas el *móvil* a una *etiqueta* compatible… y se abre lo que tú *quieras*."),
    (10.1, "dependiente", "Tu web.", "Tu *web*."),
    (11.75, "dependiente", "Tu catálogo.", "Tu *catálogo*."),
    (13.4, "dependiente", "Tus promociones.", "Tus *promociones*."),
    (15.05, "dependiente", "Tu contacto.", "Tu *contacto*."),
    (16.6, "dependiente", "Vídeos, redes… todo.", "*Vídeos*, *redes*… *todo*."),
    (18.4, "cliente",    "¿Y no vas a hacer nada?", "¿Y no vas a hacer *nada*?"),
    (20.05, "dependiente", "¿Para qué? Se ha llevado los folletos de papel. Mi catálogo cabe en una pegatina.", "¿Para qué? Se ha llevado los *folletos de papel*. Mi catálogo cabe en una *pegatina*."),
    (24.6, "ladron",     "Oiga… ¿y esto cuánto vale?", "Oiga… ¿y esto *cuánto vale*?"),
    (26.45, "dependiente", "Las etiquetas NFC cuestan treinta euros. Ideales para comercios y profesionales: acercas el móvil y compartes tu información digital.",
                          "Las etiquetas NFC cuestan *30 €*. Ideales para *comercios* y *profesionales*: acercas el móvil y compartes tu *información digital*."),
    (34.5, "dependiente", "Llama al seis, cero, tres. Once. Cuarenta y cinco. Veintiséis.", "Llama al *603 11 45 26*"),
]

SHOTS = [
    (0.0, 1.95, "hook"),            # el ladrón cruza la tienda, la clienta grita
    (1.95, 5.0, "paco_calm"),       # zoom de golpe al dependiente, tranquilísimo con su café
    (5.0, 5.75, "loli_ahora"),      # «¿¡Ahora!?»
    (5.75, 10.0, "freeze"),         # se congela el tiempo: explicación con holograma
    (10.0, 11.65, "u_web"),         # Plaza de España
    (11.65, 13.3, "u_catalogo"),    # La Avenida
    (13.3, 14.95, "u_promo"),       # La Avenida, 25
    (14.95, 16.5, "u_contacto"),    # Casa Tortosa (modernismo)
    (16.5, 18.3, "u_video"),        # Melilla la Vieja
    (18.3, 20.0, "loli_nada"),
    (20.0, 22.5, "paco_shrug"),
    (22.5, 24.4, "thief_out"),      # mientras tanto, el ladrón… (Plaza de España)
    (24.4, 26.3, "thief_back"),
    (26.3, 29.4, "paco_cam"),       # a cámara: 30 €
    (29.4, 31.0, "m_reconquista"),  # comercios y profesionales (modernismo)
    (31.0, 32.6, "m_asamblea"),
    (32.6, 34.0, "paco_cam2"),
    (34.0, 40.0, "endcard"),
]

HITS = [0.0, 1.95, 5.0, 5.75, 10.0, 18.3, 22.5, 24.4, 26.3, 27.55, 34.0]

def write_srt(path, blocks):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(blocks, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c}\n\n")
TITLES = []
