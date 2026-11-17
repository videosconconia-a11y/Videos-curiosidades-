# Guion del vídeo "La medusa inmortal"
# Cada escena: narración (lo que dice la voz) e imágenes IA (nombre, prompt) que se muestran mientras se narra.
# Los tiempos y los subtítulos palabra a palabra se calculan a partir del audio real (timeline.py).

SCENES = [
    dict(text="Existe un animal que, cuando se hace viejo… vuelve a ser un bebé. Y puede hacerlo una y otra vez.",
         images=[
             ("hook_jelly", "tiny glowing translucent jellyfish floating in the dark deep ocean, bioluminescent, mysterious, red stomach inside"),
             ("hook_reverse", "a jellyfish dissolving into glowing particles that swirl backwards in time, dark ocean, magical light"),
         ]),
    dict(text="Es la medusa inmortal: Turritopsis dohrnii. Mide unos cuatro milímetros y medio. Más pequeña que la uña de tu meñique.",
         images=[
             ("jelly_portrait", "macro photo of a tiny transparent bell jellyfish with a bright red center and many thin white tentacles, black background"),
             ("jelly_finger", "tiny transparent jellyfish floating next to a human fingertip underwater, macro, blue light, scale comparison"),
         ]),
    dict(text="Cuando está herida, enferma o pasa hambre, en vez de morir… hace algo que parece imposible. Se hunde hasta el fondo del mar.",
         images=[
             ("jelly_hurt", "damaged fragile jellyfish with torn tentacles drifting in murky dark water, sad melancholic light"),
             ("jelly_sink", "small jellyfish slowly sinking down toward the dark sea floor, light rays from far above, deep blue"),
         ]),
    dict(text="Allí se encoge sobre sí misma: sus tentáculos desaparecen, su cuerpo se reabsorbe… y se convierte en una bolita pegada a una roca.",
         images=[
             ("jelly_shrink", "jellyfish curling inward and shrinking, tentacles retracting, on a dark rock, macro underwater"),
             ("cyst_rock", "a tiny glowing translucent blob attached to a dark underwater rock, macro, mysterious soft light"),
         ]),
    dict(text="Y de esa bolita nace un pólipo: la fase bebé de la medusa. Es como si una mariposa volviera a ser oruga.",
         images=[
             ("polyp", "tiny white branching hydroid polyp colony with little tentacles growing on an underwater rock, macro photo"),
             ("butterfly", "a blue butterfly on a leaf next to a green caterpillar, macro photo, soft magical light"),
         ]),
    dict(text="El truco se llama transdiferenciación: sus células cambian de función. Una célula de músculo, por ejemplo, puede transformarse en otra completamente distinta.",
         images=[
             ("cells", "microscope view of glowing cells transforming and changing shape, blue and pink fluorescent, dark background"),
             ("cells_morph", "fluorescent muscle fiber cells morphing into round nerve cells, microscopy, glowing, scientific"),
         ]),
    dict(text="De ese pólipo brotan medusas nuevas, idénticas a la original. Y el ciclo puede repetirse. En Japón, un investigador vio a una rejuvenecer diez veces en solo dos años.",
         images=[
             ("budding", "many tiny baby jellyfish budding and swimming away from a white polyp colony, underwater macro, glowing"),
             ("cycle", "several tiny jellyfish floating in a circle in the dark ocean, glowing, symmetrical, magical"),
             ("japan_lab", "small aquarium tanks with tiny jellyfish in a dim japanese marine biology lab, blue light, microscope"),
         ]),
    dict(text="Y lo mejor: su genoma se descifró en España, en la Universidad de Oviedo. Tiene el doble de genes para reparar y proteger su ADN que una especie pariente que no rejuvenece.",
         images=[
             ("oviedo", "historic stone university building in oviedo spain at dusk, warm light, cinematic"),
             ("dna", "glowing blue dna double helix floating in dark space, being repaired by tiny lights, scientific"),
             ("two_jellies", "two tiny jellyfish side by side in the dark ocean, one glowing bright, the other faded and dim"),
         ]),
    dict(text="Ojo: no es indestructible. Muchas acaban devoradas por peces o por enfermedades. Pero si nadie se la come… en teoría, podría no morir nunca de vieja.",
         images=[
             ("fish_eat", "a fish about to eat a tiny glowing jellyfish in the ocean, dramatic underwater light"),
             ("eternal", "a single tiny glowing jellyfish floating in an endless dark ocean, stars of plankton around, timeless, epic"),
         ]),
    dict(text="Ahora piénsalo: si pudieras volver a tener diez años, con todo lo que sabes hoy… ¿lo harías? Te leo en comentarios.",
         images=[
             ("child", "a child seen from behind standing on a beach at sunset looking at the sea, nostalgic warm light, cinematic"),
             ("final_jelly", "tiny glowing jellyfish with red center in the dark ocean, light rays, poster composition, beautiful"),
         ]),
]

# Palabras a resaltar en amarillo en los subtítulos (sin acentos ni mayúsculas)
HIGHLIGHT = {"bebe", "inmortal", "turritopsis", "dohrnii", "milimetros", "meñique", "morir", "imposible", "fondo",
             "bolita", "roca", "polipo", "mariposa", "oruga", "transdiferenciacion", "celulas", "musculo",
             "diez", "veces", "dos", "años", "españa", "oviedo", "doble", "adn", "indestructible", "nunca",
             "vieja", "comentarios", "otra", "vez"}
