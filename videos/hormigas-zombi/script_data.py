# Guion del vídeo "El hongo que convierte hormigas en zombis"
# Cada escena: narración (lo que dice la voz) e imágenes IA que se muestran mientras se narra.
# Los tiempos y los subtítulos palabra a palabra se calculan a partir del audio real (gen_assets.py).

STYLE = ("Ultra-realistic cinematic macro photograph, National Geographic style, dramatic moody lighting, "
         "dark tropical rainforest atmosphere, shallow depth of field, rich detail, vertical 9:16 composition. "
         "Absolutely no text, letters, captions, logos or watermarks in the image.")

SCENES = [
    dict(text="En la selva hay un hongo que convierte a las hormigas en zombis. Y no es una forma de hablar.",
         images=[
             ("hook_zombie", "zombie ant infected by cordyceps fungus, dead ant clamped on a leaf, long thin brown fungal spike sprouting out of the back of its head, eerie green light, horror"),
             ("hook_jungle", "dark misty tropical rainforest at dawn, giant trees, light rays, ominous mysterious"),
         ]),
    dict(text="Se llama Ophiocordyceps. Todo empieza cuando una espora microscópica cae sobre una hormiga carpintera… y atraviesa su caparazón.",
         images=[
             ("spore_fall", "tiny glowing fungal spores falling through dark rainforest air, light beam, bokeh particles"),
             ("spore_ant", "extreme macro of a black ant head, tiny white fungal spores stuck on its shiny exoskeleton"),
         ]),
    dict(text="Durante días, el hongo crece dentro de ella en silencio. Y la hormiga sigue trabajando como si nada.",
         images=[
             ("inside_ant", "x-ray view of a translucent ant body filled with glowing white fungal threads, dark background, bioluminescent"),
             ("ant_working", "line of black carpenter ants walking on a branch carrying food, rainforest, warm light"),
         ]),
    dict(text="Pero de repente, empieza a comportarse de forma extraña. Abandona su colonia, camina sin rumbo, y sufre convulsiones que la hacen caer de las plantas.",
         images=[
             ("ant_shaking", "sick black ant twitching on wet forest floor leaves, legs contorted, unsettling dark light"),
             ("ant_alone", "one lonely black ant wandering on a mossy log, isolation, cold blue light"),
             ("ant_falling", "black ant falling from a green leaf in mid air, motion blur, water droplets, dark jungle"),
         ]),
    dict(text="Y aquí viene lo inquietante. La hormiga trepa por una planta hasta unos veinticinco centímetros del suelo: justo donde la humedad y la temperatura son perfectas… para el hongo.",
         images=[
             ("ant_climbing", "single black ant climbing up a thin green plant stem, low angle, misty rainforest, dew"),
             ("height_25", "small rainforest seedling with one tiny ant on top, low mist over the forest floor, volumetric light"),
             ("humid_leaf", "underside of a big tropical leaf covered in water droplets, humid green haze"),
         ]),
    dict(text="Busca la parte de abajo de una hoja y, hacia el mediodía, muerde el nervio central con todas sus fuerzas… y ya nunca lo suelta. Muere ahí, colgada.",
         images=[
             ("bite_vein", "extreme macro of black ant jaws biting the central vein under a green leaf"),
             ("noon_sun", "looking up through jungle canopy at the bright midday sun, leaf silhouette with a small ant hanging underneath"),
             ("death_grip", "dead ant hanging upside down under a leaf, jaws locked on the leaf vein, legs stiff, white fungal fuzz on its joints, dim eerie light"),
         ]),
    dict(text="Lo más escalofriante: los científicos descubrieron que el hongo ni siquiera entra en su cerebro. Envuelve sus músculos con una red de filamentos… y la maneja como a una marioneta.",
         images=[
             ("brain_scan", "microscope image of an ant head, glowing blue brain inside, white fungal cells surrounding it, dark lab"),
             ("muscle_net", "microscopic muscle fibers wrapped in a glowing web of white fungal filaments, electron microscope style"),
             ("puppet", "black ant on a leaf with thin glowing threads rising from its legs into darkness like puppet strings, surreal"),
         ]),
    dict(text="Días después, de su cabeza brota un tallo. Y desde ahí, el hongo suelta una lluvia de esporas sobre el camino de sus compañeras… y el ciclo vuelve a empezar.",
         images=[
             ("stalk_grow", "ophiocordyceps fungus, dead ant on a leaf with a single long thin pale stalk growing straight up from its head, night jungle, rim light"),
             ("spore_rain", "glowing spores raining down from a cordyceps fungus stalk in a dark rainforest, light beams"),
             ("ants_below", "trail of black ants on the forest floor under a shower of tiny glowing spores, ground level macro"),
         ]),
    dict(text="Y esto no es nuevo. En Alemania se halló una hoja fósil con las mismas marcas de mordisco. Tiene cuarenta y ocho millones de años.",
         images=[
             ("fossil_leaf", "fossil leaf imprint in grey shale stone, visible veins, museum lighting, macro"),
             ("ancient_forest", "prehistoric eocene jungle beside a volcanic lake, mist, lush giant ferns, cinematic wide"),
         ]),
    dict(text="Tranquilo: este hongo no puede infectar a los humanos. Pero dime… ¿te imaginas que algún día pudiera? Te leo en comentarios.",
         images=[
             ("human_city", "person seen from behind on a night city street under a streetlight, tiny glowing spores floating in the air"),
             ("final_ant", "cordyceps zombie ant portrait, dead ant on a leaf, tall thin fungal stalk rising from its head, glowing spores floating, dark background"),
         ]),
]

# Palabras a resaltar en amarillo en los subtítulos (sin acentos ni mayúsculas para comparar)
HIGHLIGHT = {"zombis", "ophiocordyceps", "espora", "caparazon", "silencio", "convulsiones", "colonia",
             "veinticinco", "centimetros", "hongo", "mediodia", "nervio", "suelta", "colgada", "cerebro",
             "musculos", "marioneta", "tallo", "esporas", "ciclo", "fosil", "cuarenta", "ocho",
             "millones", "humanos", "comentarios", "escalofriante", "inquietante"}
