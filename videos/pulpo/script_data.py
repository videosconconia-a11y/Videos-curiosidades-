# Guion del vídeo "El pulpo: el animal más extraterrestre de la Tierra"
# Cada escena: narración (lo que dice la voz) e imágenes IA (nombre, prompt) que se muestran mientras se narra.
# Los tiempos y los subtítulos palabra a palabra se calculan a partir del audio real (timeline.py).

SCENES = [
    dict(text="Este animal tiene tres corazones, sangre azul… y piensa con los brazos. Y no, no es un extraterrestre.",
         images=[
             ("hook_eye", "extreme close-up of an octopus eye with horizontal pupil, alien looking skin texture, dark ocean, dramatic light"),
             ("hook_alien", "octopus floating in the dark deep ocean with tentacles spread like an alien creature, glowing rim light"),
         ]),
    dict(text="Es el pulpo. Dos de sus corazones bombean sangre a las branquias, y el tercero, al resto del cuerpo.",
         images=[
             ("octopus_reef", "common octopus on a colorful coral reef, clear blue water, sun rays, beautiful wildlife photo"),
             ("hearts", "translucent octopus body with three glowing red hearts visible inside, x-ray style, dark background"),
         ]),
    dict(text="Su sangre es azul porque, en vez de hierro, usa cobre para llevar el oxígeno. Así respira mejor en aguas frías.",
         images=[
             ("blue_blood", "glowing blue liquid flowing through translucent veins, macro, dark background, scientific"),
             ("cold_deep", "octopus swimming in cold dark blue deep water, ice blue light, particles, cinematic"),
         ]),
    dict(text="Pero lo más alucinante está en sus brazos: unos dos tercios de sus neuronas no están en la cabeza… sino repartidas por sus ocho brazos.",
         images=[
             ("neurons", "glowing network of neurons inside octopus tentacles, bioluminescent blue lines, dark background"),
             ("arms_spread", "octopus with eight arms spread wide seen from below, symmetrical, dramatic backlight"),
         ]),
    dict(text="Cada brazo puede explorar y tocar por su cuenta. Y con sus ventosas no solo agarra: también saborea todo lo que toca.",
         images=[
             ("arm_explore", "single octopus tentacle curling and exploring a rock crevice, macro, underwater"),
             ("suckers", "extreme macro of octopus suckers touching a seashell, detailed texture, underwater light"),
         ]),
    dict(text="Además, cambia de color y de textura en menos de un segundo para camuflarse. Aunque, curiosamente, se cree que no distingue los colores.",
         images=[
             ("camo", "octopus perfectly camouflaged on a rocky reef, skin matching the rocks and algae texture"),
             ("color_change", "octopus skin flashing bright red and white patterns, macro, vivid colors, underwater"),
         ]),
    dict(text="Y no tiene huesos. Puede colarse por cualquier agujero por el que quepa su pico, lo único duro de su cuerpo.",
         images=[
             ("squeeze", "octopus squeezing its soft body through a tiny hole in a rock, underwater macro"),
             ("bottle", "small octopus hiding inside a glass bottle on the sandy sea floor, underwater photo"),
         ]),
    dict(text="Pero su historia más impresionante es la de una madre. En California, a mil cuatrocientos metros de profundidad, unos científicos encontraron a una pulpo cuidando sus huevos.",
         images=[
             ("rov", "underwater remotely operated vehicle with bright lights descending in the pitch black deep sea"),
             ("deep_mom", "pale purple deep sea octopus mother wrapped around her eggs on a dark rock wall, lit by a spotlight"),
             ("eggs", "cluster of translucent octopus eggs attached to a rock in the deep sea, tiny embryos visible, macro"),
         ]),
    dict(text="Volvieron dieciocho veces. Y siempre estaba allí, protegiéndolos, sin que nunca la vieran comer. Durante cuatro años y medio. El récord de cualquier animal.",
         images=[
             ("guarding", "deep sea octopus mother guarding her eggs in the darkness, protective pose, spotlight, emotional"),
             ("time_pass", "dark deep sea rock wall with an octopus brooding eggs, marine snow falling, long passage of time"),
             ("record", "close-up of a thin pale octopus mother with cloudy eyes still holding her eggs, deep sea, moving"),
         ]),
    dict(text="Cuando los bebés nacieron, ella ya no estaba. La madre pulpo lo da todo… hasta el final. ¿Sabías que el pulpo era tan increíble? Te leo en comentarios.",
         images=[
             ("hatch", "tiny baby octopuses hatching from eggs and swimming away into the deep sea, glowing, hopeful"),
             ("final_octo", "majestic octopus portrait in the dark ocean, tentacles flowing, cinematic rim light, poster"),
         ]),
]

# Palabras a resaltar en amarillo en los subtítulos (sin acentos ni mayúsculas)
HIGHLIGHT = {"tres", "corazones", "azul", "brazos", "extraterrestre", "pulpo", "branquias", "cobre", "hierro",
             "neuronas", "tercios", "ocho", "saborea", "ventosas", "color", "colores", "huesos", "pico",
             "madre", "huevos", "dieciocho", "comer", "cuatro", "medio", "record", "final", "comentarios",
             "mil", "cuatrocientos", "metros", "segundo", "cabeza"}
