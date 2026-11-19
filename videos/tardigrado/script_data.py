# Guion del vídeo "El tardígrado: el animal casi indestructible"
# Cada escena: narración (lo que dice la voz) e imágenes IA (nombre, prompt) que se muestran mientras se narra.
# Los tiempos y los subtítulos palabra a palabra se calculan a partir del audio real (timeline.py).

SCENES = [
    dict(text="Este animal ha sobrevivido al vacío del espacio… y probablemente vive ahora mismo en el musgo de tu jardín.",
         images=[
             ("hook_space", "tiny chubby tardigrade water bear floating in outer space with planet earth behind it, cinematic, epic"),
             ("hook_moss", "close-up of green moss on a garden wall with water droplets, macro, soft morning light"),
         ]),
    dict(text="Es el tardígrado, también llamado oso de agua. Mide menos de un milímetro, tiene ocho patas con garras… y es casi indestructible.",
         images=[
             ("tardigrade_portrait", "tardigrade water bear under the microscope, chubby translucent body, eight stubby legs with claws, detailed"),
             ("claws", "extreme macro of tardigrade legs with tiny hooked claws gripping a moss leaf, microscope"),
         ]),
    dict(text="Cuando se queda sin agua, hace algo increíble: expulsa casi toda el agua de su cuerpo, se encoge como un barril… y se apaga.",
         images=[
             ("drying", "dry cracked moss under harsh sun, tiny tardigrade shrinking, desiccation, macro"),
             ("tun", "tiny shriveled barrel shaped tardigrade tun in dormant state on a dry surface, microscope image"),
         ]),
    dict(text="En ese estado, su metabolismo baja a casi cero. Parece muerto. Pero no lo está: solo está esperando.",
         images=[
             ("dormant", "lifeless looking dry tardigrade lying on a grain of sand, microscope, cold dim light, stillness"),
             ("waiting", "tiny dormant tardigrade inside a dry moss forest, macro, dust particles floating, timeless"),
         ]),
    dict(text="En dos mil siete, científicos europeos lanzaron tardígrados al espacio, expuestos directamente al vacío y a la radiación. Al volver, muchos revivieron… e incluso tuvieron crías.",
         images=[
             ("rocket", "rocket launching into the sky with a bright fire trail, cinematic"),
             ("capsule", "small satellite capsule orbiting earth in space, sunlight, realistic"),
             ("revive", "tardigrade waking up and moving in a drop of water under the microscope, glowing, alive"),
         ]),
    dict(text="En Japón despertaron a unos tardígrados que llevaban más de treinta años congelados en una muestra de musgo de la Antártida.",
         images=[
             ("antarctica", "frozen moss in antarctica covered in ice crystals, blue cold light, macro"),
             ("frozen", "tardigrade trapped inside clear ice, frozen, microscope view, blue light"),
         ]),
    dict(text="Y su secreto es tan bueno que lo estamos copiando: tiene una proteína que protege su ADN. Al añadirla a células humanas, sufrieron mucho menos daño por radiación.",
         images=[
             ("dna_shield", "glowing dna double helix protected by a translucent shield of light, dark background, scientific"),
             ("lab", "scientist in a modern laboratory looking at cells under a microscope, blue light, cinematic"),
         ]),
    dict(text="Existen desde hace cientos de millones de años y han sobrevivido a las grandes extinciones. Los encuentras en las montañas, en el fondo del mar… y en los hielos polares.",
         images=[
             ("dinosaurs", "giant asteroid hitting earth with dinosaurs silhouettes, mass extinction, dramatic sky"),
             ("everywhere", "tardigrade walking on a moss leaf with mountains in the background, double exposure, epic"),
         ]),
    dict(text="Y lo más loco: desde dos mil diecinueve hay tardígrados en la Luna. Viajaban en una sonda que se estrelló allí.",
         images=[
             ("moon_crash", "small space probe crashing onto the grey lunar surface, dust plume, earth in the black sky"),
             ("moon_tardigrade", "tiny tardigrade on grey moon dust with earth rising in the black sky, surreal, cinematic"),
         ]),
    dict(text="Así que la próxima vez que veas musgo, piénsalo: ahí abajo hay un pequeño superviviente. ¿Lo conocías? Te leo en comentarios.",
         images=[
             ("garden_moss", "lush green moss on old stones in a garden after rain, soft golden light, peaceful"),
             ("final_tardigrade", "cute tardigrade water bear portrait on a moss leaf, glowing rim light, dark background, poster"),
         ]),
]

# Palabras a resaltar en amarillo en los subtítulos (sin acentos ni mayúsculas)
HIGHLIGHT = {"espacio", "musgo", "jardin", "tardigrado", "oso", "agua", "milimetro", "ocho", "indestructible",
             "barril", "apaga", "cero", "muerto", "esperando", "vacio", "radiacion", "revivieron", "crias",
             "japon", "treinta", "congelados", "antartida", "proteina", "adn", "humanas", "millones",
             "extinciones", "luna", "estrello", "superviviente", "comentarios", "dos", "siete", "diecinueve"}
