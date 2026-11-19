# Guion del vídeo "¿Qué te pasaría si cayeras en un agujero negro?"
# Cada escena: narración (lo que dice la voz) e imágenes IA (nombre, prompt) que se muestran mientras se narra.
# Los tiempos y los subtítulos palabra a palabra se calculan a partir del audio real (timeline.py).

SCENES = [
    dict(text="Imagina que caes en un agujero negro. Lo que te pasaría es mucho más extraño de lo que crees.",
         images=[
             ("hook_bh", "giant black hole with a glowing orange accretion disk bending light around it, deep space, epic"),
             ("hook_astronaut", "lone astronaut floating toward a huge black hole with glowing ring, seen from behind, cinematic"),
         ]),
    dict(text="Un agujero negro es una región donde la gravedad es tan fuerte que nada puede escapar. Ni siquiera la luz.",
         images=[
             ("gravity", "light rays bending and being swallowed by a black sphere in space, glowing lines, dramatic"),
             ("light_trap", "beams of light spiraling into a black hole, dark space, swirling glowing gas"),
         ]),
    dict(text="Su frontera se llama horizonte de sucesos: el punto de no retorno. Una vez lo cruzas, ya no hay vuelta atrás.",
         images=[
             ("horizon", "close view of a black hole event horizon, perfect black circle edged by a thin ring of light"),
             ("no_return", "spaceship approaching the dark edge of a black hole, tiny against the huge glowing ring"),
         ]),
    dict(text="Si cayeras en uno pequeño, del tamaño de una estrella, la gravedad tiraría mucho más de tus pies que de tu cabeza. Te estiraría como un espagueti. Los científicos lo llaman, literalmente, espaguetización.",
         images=[
             ("small_bh", "small stellar black hole pulling gas from a nearby star in a bright stream, space"),
             ("stretch", "astronaut being stretched long and thin toward a black hole, motion streaks, surreal, cinematic"),
             ("spaghetti", "a stream of glowing matter stretched into a long thin noodle spiraling into a black hole"),
         ]),
    dict(text="Pero en uno gigante, como el del centro de nuestra galaxia, con más de cuatro millones de veces la masa del Sol, cruzarías el horizonte… sin notar nada especial.",
         images=[
             ("galaxy_center", "center of the milky way galaxy with dense stars and glowing gas, supermassive black hole in the middle"),
             ("calm_cross", "astronaut calmly floating across the edge of an enormous black hole, the dark horizon filling the view"),
         ]),
    dict(text="Y aquí viene lo más raro. Un amigo que te mirara desde lejos te vería caer cada vez más despacio, cada vez más rojo… hasta quedarte casi congelado en el borde, apagándote poco a poco.",
         images=[
             ("friend_ship", "spaceship window view of a distant black hole with a tiny astronaut silhouette near its edge"),
             ("redshift", "astronaut silhouette glowing deep red and fading near the black edge of a black hole, frozen in time"),
             ("frozen_time", "a clock frozen and stretched near a black hole event horizon, red light, surreal"),
         ]),
    dict(text="Para ti, en cambio, el tiempo pasaría con normalidad. Cruzarías la frontera en un instante.",
         images=[
             ("inside_view", "astronaut helmet visor reflecting a swirling black hole, inside view, cinematic close-up"),
         ]),
    dict(text="Una vez dentro, todos los caminos llevan al centro. Ir hacia la singularidad sería tan inevitable como avanzar hacia el mañana.",
         images=[
             ("tunnel", "tunnel of warped light and darkness leading to a bright point, inside a black hole, surreal"),
             ("singularity", "infinitely dense glowing point at the center of darkness, warped space grid, cosmic"),
         ]),
    dict(text="Según una simulación de la NASA, en un agujero negro como ese, desde que cruzas el horizonte hasta que te destroza pasarían unos trece segundos.",
         images=[
             ("simulation", "scientific visualization of a black hole on supercomputer screens in a dark control room"),
             ("countdown", "astronaut falling into darkness with streaks of light, last moments, dramatic"),
         ]),
    dict(text="Tranquilo: el agujero negro supermasivo más cercano, Sagitario A asterisco, está a unos veintisiete mil años luz. Pero dime… ¿tú te asomarías al borde? Te leo en comentarios.",
         images=[
             ("milky_way", "the milky way galaxy seen from above with a bright center, earth location marked by a small glow"),
             ("final_bh", "majestic black hole with a bright golden accretion disk and lensed light, poster composition"),
         ]),
]

# Palabras a resaltar en amarillo en los subtítulos (sin acentos ni mayúsculas)
HIGHLIGHT = {"agujero", "negro", "extraño", "gravedad", "luz", "horizonte", "sucesos", "retorno", "espagueti",
             "espaguetizacion", "pies", "cabeza", "gigante", "galaxia", "millones", "nada", "despacio", "rojo",
             "congelado", "normalidad", "instante", "centro", "singularidad", "mañana", "nasa", "trece",
             "segundos", "sagitario", "asterisco", "veintisiete", "años", "comentarios", "borde"}
