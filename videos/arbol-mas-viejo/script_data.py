# Guion del vídeo "El árbol más viejo del mundo" (aprobado por el usuario)
# Cada escena: narración (lo que dice la voz) e imágenes IA (nombre, prompt) que se muestran mientras se narra.
# Los tiempos y los subtítulos palabra a palabra se calculan a partir del audio real (timeline.py).

SCENES = [
    dict(text="Hay un árbol vivo que ya estaba aquí cuando se construyeron las pirámides de Egipto. Y su ubicación exacta es secreta.",
         images=[
             ("hook_tree", "ancient twisted bristlecone pine tree on a rocky mountain slope at sunset, gnarled silver wood, epic"),
             ("hook_pyramids", "ancient egyptian pyramids under construction with workers and ramps, golden desert light, cinematic"),
         ]),
    dict(text="Se llama Matusalén. Es un pino de las Montañas Blancas de California, y tiene unos cuatro mil ochocientos cincuenta años.",
         images=[
             ("white_mountains", "barren white limestone mountains in california with scattered ancient pine trees, clear blue sky, wide shot"),
             ("methuselah", "a single very old gnarled pine tree with twisted trunk and few green branches, mountain background, majestic"),
         ]),
    dict(text="Cuando empezó a crecer, aún no existía la escritura en casi ningún lugar del mundo. Cuando se levantó la Gran Pirámide, él ya tenía unos trescientos años.",
         images=[
             ("seedling", "tiny pine seedling sprouting from rocky ground in the mountains, morning light, macro"),
             ("great_pyramid", "the great pyramid of giza newly built with smooth white limestone shining in the sun, ancient egypt"),
         ]),
    dict(text="Ha sobrevivido al Imperio romano, a la Edad Media, a todas las guerras… y sigue vivo.",
         images=[
             ("rome", "roman legionaries marching in formation, ancient rome, cinematic, dramatic sky"),
             ("medieval", "medieval stone castle on a hill at dusk with knights, cinematic"),
             ("still_alive", "ancient twisted pine tree under a starry night sky with the milky way, timeless, epic"),
         ]),
    dict(text="¿Por qué su ubicación es secreta? Para protegerlo: el Servicio Forestal de Estados Unidos no la revela, para que nadie pueda dañarlo.",
         images=[
             ("secret_forest", "misty forest of ancient bristlecone pines with no signs or paths, mysterious, early morning"),
             ("ranger", "forest ranger seen from behind looking at an ancient pine forest on a mountain, protective"),
         ]),
    dict(text="Y hay motivos. En mil novecientos sesenta y cuatro, un estudiante que investigaba los pinos taló uno de ellos para contar sus anillos.",
         images=[
             ("student_1964", "young researcher in 1960s clothes standing next to an ancient pine tree in the mountains, vintage photo"),
             ("chainsaw", "old chainsaw cutting into the trunk of an ancient gnarled tree, sawdust, dramatic"),
         ]),
    dict(text="Era Prometeo, y tenía más de cuatro mil ochocientos años. Era el ser vivo más viejo conocido… y nadie lo sabía hasta que fue demasiado tarde.",
         images=[
             ("tree_rings", "extreme close-up of thousands of tiny tree rings on a cut trunk cross section, detailed wood texture"),
             ("stump", "lonely tree stump on a rocky mountain slope, melancholic grey light, loss"),
         ]),
    dict(text="El secreto de su longevidad: viven en montañas altísimas, con frío, viento y muy poca agua, y crecen lentísimo. Su madera es tan densa que ni insectos ni hongos pueden con ella.",
         images=[
             ("harsh_mountain", "ancient pine tree in a snowstorm on a high windy mountain ridge, harsh conditions"),
             ("dense_wood", "macro of very dense twisted silver pine wood grain, polished by wind, detailed texture"),
         ]),
    dict(text="Además, sus raíces alimentan solo la parte del árbol que tienen justo encima. Si una parte muere, el resto sigue viviendo. Por eso parecen muertos… pero tienen una tira de corteza viva que los mantiene en pie.",
         images=[
             ("roots", "twisted exposed roots of an ancient pine gripping white rocks, macro, golden light"),
             ("dead_looking", "mostly dead looking silver pine tree with a single living branch of green needles, mountain"),
             ("bark_strip", "narrow strip of living brown bark running up a silver dead trunk of an ancient pine, close-up"),
         ]),
    dict(text="Este árbol ya era anciano cuando nació Cleopatra. ¿Qué crees que habrá visto en todo este tiempo? Te leo en comentarios.",
         images=[
             ("cleopatra", "ancient egyptian queen portrait in golden jewelry, cinematic, dramatic light, no text"),
             ("final_tree", "majestic ancient bristlecone pine silhouetted against a glowing sunset sky with stars appearing, poster"),
         ]),
]

# Palabras a resaltar en amarillo en los subtítulos (sin acentos ni mayúsculas)
HIGHLIGHT = {"arbol", "piramides", "egipto", "secreta", "matusalen", "california", "cuatro", "ochocientos", "cincuenta",
             "años", "escritura", "trescientos", "romano", "media", "vivo", "protegerlo", "mil", "novecientos",
             "sesenta", "estudiante", "anillos", "prometeo", "tarde", "frio", "viento", "agua", "lentisimo", "densa",
             "raices", "muertos", "corteza", "cleopatra", "comentarios"}
