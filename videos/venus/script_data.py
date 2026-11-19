# Guion del vídeo "Venus: el planeta donde un día dura más que un año"
# Cada escena: narración (lo que dice la voz) e imágenes IA (nombre, prompt) que se muestran mientras se narra.
# Los tiempos y los subtítulos palabra a palabra se calculan a partir del audio real (timeline.py).

SCENES = [
    dict(text="En este planeta, un día dura más que un año. Y no es un error. Es Venus.",
         images=[
             ("hook_venus", "planet Venus glowing yellow orange in black space, thick swirling clouds, dramatic sunlight, epic"),
             ("hook_clock", "melting golden clock floating in front of a glowing yellow planet in space, surreal, cinematic"),
         ]),
    dict(text="Venus tarda doscientos veinticinco días en dar la vuelta al Sol… pero doscientos cuarenta y tres en girar una sola vez sobre sí misma.",
         images=[
             ("orbit", "small yellow planet orbiting a huge bright sun in space, glowing orbit line, solar system view"),
             ("rotation", "close view of planet Venus slowly rotating, cloud bands, terminator line between day and night, space"),
         ]),
    dict(text="Y además gira al revés que casi todos los planetas. Allí, el Sol sale por el oeste y se pone por el este.",
         images=[
             ("sunrise", "huge blurry sun rising through thick orange hazy sky over a volcanic rocky plain, alien planet surface"),
             ("sunset_west", "orange alien sky with a dim sun setting behind volcanic mountains, thick haze, otherworldly"),
         ]),
    dict(text="Pero no te lo recomiendo para vivir. En su superficie hay unos cuatrocientos sesenta y cinco grados: suficiente para fundir el plomo.",
         images=[
             ("surface", "scorching hot surface of Venus, flat cracked basalt rocks, glowing orange sky, heat haze, desolate"),
             ("lead_melt", "metal lead bar melting into glowing liquid on a hot rock, macro, orange heat glow"),
         ]),
    dict(text="Y es más caliente que Mercurio, aunque esté casi el doble de lejos del Sol. ¿El motivo? Un efecto invernadero descontrolado.",
         images=[
             ("mercury", "small grey cratered planet Mercury close to the blazing sun, space, dramatic"),
             ("greenhouse", "thick glowing atmosphere trapping sunlight around a yellow planet, heat waves, greenhouse effect, space"),
         ]),
    dict(text="Su atmósfera es casi todo dióxido de carbono, y es tan densa que la presión es noventa veces la de la Tierra. Como estar a casi un kilómetro bajo el mar.",
         images=[
             ("atmosphere", "dense swirling yellow orange clouds of a planet atmosphere seen from inside, crushing pressure, cinematic"),
             ("deep_sea", "submarine in the crushing dark deep ocean, pressure, deep blue darkness, particles, cinematic"),
         ]),
    dict(text="Y por si fuera poco, sus nubes son de ácido sulfúrico. Esas nubes reflejan tanta luz del Sol que, después de la Luna, Venus es lo más brillante del cielo nocturno.",
         images=[
             ("acid_clouds", "toxic yellow sulfuric acid clouds raining corrosive drops, alien sky, dramatic lightning"),
             ("bright_sky", "very bright star Venus shining in the twilight sky above a calm landscape, crescent moon nearby, beautiful"),
         ]),
    dict(text="En mil novecientos ochenta y dos, la Unión Soviética logró posar allí la sonda Venera trece. Envió las primeras fotos en color desde la superficie de otro planeta.",
         images=[
             ("launch", "soviet rocket launching at night with bright fire trail, 1980s, cinematic"),
             ("lander", "round soviet space probe lander descending with a parachute through thick orange clouds of Venus"),
             ("lander_surface", "retro soviet space lander standing on orange rocky surface of Venus, glowing sky, heat haze"),
         ]),
    dict(text="Estaba diseñada para resistir solo treinta y dos minutos. Pero aguantó dos horas y siete… antes de quedar en silencio para siempre.",
         images=[
             ("lander_heat", "retro space probe on a burning orange alien surface, heat haze distortion, glowing hot metal, dramatic"),
             ("lander_dead", "abandoned damaged retro space probe on scorching orange alien rocks, silent, lonely, haze"),
         ]),
    dict(text="Lo más inquietante: algunos estudios sugieren que, hace miles de millones de años, Venus pudo tener océanos como la Tierra. ¿Podría pasarnos lo mismo? Te leo en comentarios.",
         images=[
             ("ancient_ocean", "alien planet with blue oceans and white clouds under a bright sun, ancient Venus, earth-like, space view"),
             ("earth_venus", "planet Earth blue and planet Venus yellow side by side in space, comparison, cinematic"),
             ("final_venus", "glowing yellow planet Venus in black space with the sun behind it, epic poster composition"),
         ]),
]

# Palabras a resaltar en amarillo en los subtítulos (sin acentos ni mayúsculas)
HIGHLIGHT = {"dia", "año", "venus", "doscientos", "veinticinco", "cuarenta", "tres", "reves", "oeste", "este",
             "cuatrocientos", "sesenta", "cinco", "grados", "plomo", "mercurio", "doble", "invernadero",
             "noventa", "kilometro", "acido", "sulfurico", "venera", "trece", "color", "horas", "siete",
             "minutos", "silencio", "oceanos", "tierra", "comentarios", "carbono", "brillante", "luna", "treinta", "dos"}
