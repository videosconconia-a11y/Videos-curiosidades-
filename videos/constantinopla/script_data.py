# Guion de "Constantinopla 1453" (vídeo largo, 16:9; estilo: personajes 2D en un mundo 3D)
# Cada entrada: (plano, frase). Varias frases seguidas con el mismo plano forman una escena 3D.
# Marcado en la frase:
#   *palabra*        → resaltada en el subtítulo
#   {pantalla|voz}   → en el subtítulo se ve "pantalla"; la voz dice "voz" (números, siglas)
# Los subtítulos se generan solos (bloques de 2–4 palabras) y los tiempos salen de la voz real.
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = 0.32      # respiro entre frases (vídeo largo)
INTRO = 0.2
OUTRO = 4.0
SAY = {"Mehmed": "Mejmed", "Giustiniani": "Yustiniani", "Kerkoporta": "Kerko-porta"}

LINES = [
    ("gancho", "La ciudad con las *murallas* más famosas del mundo cayó en {1453|mil cuatrocientos cincuenta y tres}."),
    ("gancho", "Y el *cañón* gigante que las derribó… se lo habían ofrecido *primero a ella*."),
    ("gancho2", "Antes de eso hubo barcos que *navegaron por tierra*, un sultán de *veintiún años*… y una puerta que alguien dejó *abierta*."),
    ("gancho2", "Esta es la historia de cómo terminó, de verdad, el *Imperio romano*."),
    ("ciudad", "*Constantinopla*, la actual *Estambul*, fue durante más de mil años la capital del Imperio romano de Oriente."),
    ("ciudad", "La fundó el emperador *Constantino el Grande* en el año {330|trescientos treinta}, y durante siglos fue la ciudad más *rica* de Europa."),
    ("ciudad", "Hoy lo llamamos *bizantino*, pero ellos nunca se llamaron así: se llamaban a sí mismos *romanos*."),
    ("ciudad", "La ciudad estaba rodeada de *agua* por tres lados… y el cuarto lo cerraba una muralla *legendaria*."),
    ("murallas", "Las murallas de *Teodosio*: un foso, una muralla exterior y, detrás, una muralla interior con *noventa y seis torres*."),
    ("murallas", "La muralla interior medía más de *diez metros* de alto y unos *cinco* de grosor."),
    ("murallas", "Lo intentaron los *ávaros*, los *árabes* y los *búlgaros*."),
    ("murallas", "Durante *mil años*, ningún ejército consiguió atravesarlas *por tierra*."),
    ("imperio", "Pero en {1453|mil cuatrocientos cincuenta y tres}, del gran imperio apenas quedaba nada: la ciudad, unas pocas tierras en Grecia… y muchas *deudas*."),
    ("imperio", "En {1204|mil doscientos cuatro} la habían saqueado... los propios *cruzados cristianos*, entrando por el lado del mar. Nunca se recuperó."),
    ("imperio", "Los otomanos la rodeaban por todas partes: Constantinopla era una *isla* en medio de su imperio."),
    ("imperio", "Su emperador, *Constantino {XI|once}*, gobernaba una ciudad medio vacía."),
    ("sultan", "Enfrente estaba el sultán otomano *Mehmed {II|segundo}*."),
    ("sultan", "Tenía solo *veintiún años*… y una obsesión: *Constantinopla*."),
    ("sultan", "Su padre y su abuelo ya lo habían intentado… y habían *fracasado*."),
    ("sultan", "Mehmed admiraba a *Alejandro Magno*… y quería conquistar lo que nadie había podido."),
    ("fortaleza", "Su primer movimiento fue levantar una *fortaleza* junto al Bósforo en apenas *cuatro meses*."),
    ("fortaleza", "Los otomanos la llamaron *Bogazkesen*: la que corta el estrecho."),
    ("fortaleza", "Desde allí, sus cañones podían hundir cualquier barco que intentara llevar *ayuda* a la ciudad."),
    ("fortaleza", "Un barco veneciano que no quiso detenerse fue *hundido* a cañonazos."),
    ("orban", "Y entonces apareció un personaje inesperado: *Orbán*, un ingeniero experto en fundir *cañones*."),
    ("orban", "Orbán fue primero a Constantinopla y ofreció sus servicios al *emperador*."),
    ("orban", "Pero el emperador *no podía pagarle* lo que pedía."),
    ("orban", "Así que Orbán cruzó al otro lado… y le ofreció su cañón al *sultán*."),
    ("orban", "Mehmed le preguntó si podía fabricar un cañón capaz de derribar aquellas murallas."),
    ("orban", "Y Orbán respondió: *podría derribar hasta las murallas de Babilonia*."),
    ("canon", "El resultado fue un monstruo de bronce de unos *ocho metros* de largo, que disparaba bolas de piedra de *cientos de kilos*."),
    ("canon", "Para moverlo hacían falta *decenas de bueyes* y cientos de hombres."),
    ("canon", "El viaje hasta Constantinopla, de unos *doscientos kilómetros*, duró *semanas*."),
    ("canon", "Solo podía disparar unas pocas veces al día… pero cada disparo hacía *temblar* la muralla."),
    ("asedio", "El *seis de abril* de {1453|mil cuatrocientos cincuenta y tres} empezó el asedio."),
    ("asedio", "Frente a la muralla se desplegaron entre *cincuenta y ochenta mil* soldados otomanos."),
    ("asedio", "Dentro, para defender toda la ciudad, había unos *siete mil* hombres."),
    ("asedio", "Entre ellos, *setecientos genoveses* al mando de un experto en asedios: *Giovanni Giustiniani*."),
    ("asedio", "Mehmed plantó su tienda *roja y dorada* frente a la parte más débil de la muralla."),
    ("bombardeo", "Durante semanas, los cañones machacaron la muralla *día y noche*."),
    ("bombardeo", "Fue uno de los primeros grandes asedios de la historia decididos por la *pólvora*."),
    ("reparar", "Y cada noche, los defensores tapaban los huecos con lo que tenían: tierra, madera, piedras… hasta *barriles*."),
    ("reparar", "Por la mañana, la muralla volvía a estar *en pie*."),
    ("cadena", "Mientras tanto, el puerto de la ciudad, el *Cuerno de Oro*, estaba cerrado con una enorme *cadena* sobre el agua."),
    ("cadena", "La cadena flotaba sobre *troncos* y unía la ciudad con *Gálata*, al otro lado del agua."),
    ("cadena", "Ningún barco otomano podía *entrar*."),
    ("genoveses", "El *veinte de abril*, cuatro barcos cristianos atravesaron toda la flota otomana y entraron en el puerto."),
    ("genoveses", "Mehmed, *furioso*, lo vio desde la orilla… y se metió con su caballo en el *mar*."),
    ("truco", "¿El *truco*? Si sus barcos no podían cruzar la cadena… cruzarían *por tierra*."),
    ("truco", "Mehmed mandó construir un camino de *troncos engrasados* por encima de una colina."),
    ("truco", "Bueyes y hombres tiraron de ellos colina arriba… y según los cronistas, con las *velas desplegadas*, como si navegaran sobre la tierra."),
    ("truco", "Y en una sola noche, unos *setenta barcos* fueron arrastrados por tierra hasta el otro lado."),
    ("cuerno", "Al amanecer, los defensores vieron algo *imposible*: barcos enemigos *dentro* de su propio puerto."),
    ("cuerno", "Ahora tenían que vigilar también esas murallas… con todavía *menos hombres*."),
    ("cuerno", "Intentaron quemar esos barcos en un ataque nocturno… pero alguien avisó a los otomanos, y el plan *fracasó*."),
    ("minas", "Los otomanos también excavaron *túneles* bajo la muralla."),
    ("minas", "Pero los defensores los descubrían… y los inundaban o los llenaban de *humo*."),
    ("minas", "Llegaron a encontrar más de *una docena* de túneles."),
    ("presagios", "A finales de mayo, la ciudad estaba *agotada*."),
    ("presagios", "Una antigua profecía decía que Constantinopla no caería mientras la *luna* estuviera creciendo."),
    ("presagios", "Y el *veintidós de mayo*, la luna llena se oscureció en un *eclipse*."),
    ("presagios", "Días después, durante una procesión, el icono más sagrado de la ciudad se *cayó al suelo*… y una *tormenta* inundó las calles."),
    ("presagios", "Mehmed ofreció a Constantino *rendirse* y salvar la vida."),
    ("presagios", "El emperador contestó que entregar la ciudad no estaba en su mano… y que preferían *morir*."),
    ("presagios", "La última noche, cristianos de Oriente y de Occidente rezaron *juntos* en Santa Sofía."),
    ("asalto", "En la madrugada del *veintinueve de mayo* empezó el ataque final."),
    ("asalto", "Primero, oleadas de soldados mal armados para *agotar* a los defensores."),
    ("asalto", "Después, tropas mejor entrenadas. Y al final, la élite: los *jenízaros*."),
    ("giustiniani", "En lo peor del combate, *Giustiniani* fue herido y se retiró."),
    ("giustiniani", "Al ver marcharse a su comandante, muchos defensores pensaron que todo estaba *perdido*."),
    ("kerkoporta", "Y según un cronista de la época, en otra parte de la muralla alguien había dejado abierta una pequeña puerta: la *Kerkoporta*."),
    ("kerkoporta", "Unos pocos otomanos entraron por ella… y colgaron su *bandera* en una torre."),
    ("kerkoporta", "Nadie sabe si fue un descuido, una traición… o solo una *leyenda*."),
    ("emperador", "El emperador *Constantino* se quitó sus insignias y se lanzó a la lucha como un *soldado más*."),
    ("emperador", "Su cuerpo *nunca* se identificó con seguridad."),
    ("caida", "Así terminó el *Imperio romano*: casi *mil quinientos años* después de Augusto, su primer emperador."),
    ("caida", "Mehmed entró en la ciudad y fue directo a *Santa Sofía*, la mayor iglesia de la cristiandad… y la convirtió en *mezquita*."),
    ("caida", "Desde entonces lo llamaron *el Conquistador*."),
    ("despues", "Constantinopla fue la capital otomana durante casi *cinco siglos*."),
    ("despues", "Su nombre actual, *Estambul*, viene probablemente del griego: *a la ciudad*."),
    ("despues", "Muchos sabios griegos huyeron a *Italia* con sus libros… y ayudaron a impulsar el *Renacimiento*."),
    ("despues", "Y solo *treinta y nueve años* después, *Colón* llegaba a América."),
    ("final", "Una ciudad que resistió *mil años* cayó por un cañón que pudo haber sido *suyo*… y quizá por una puerta mal *cerrada*."),
    ("final", "¿Qué crees que habría pasado si el emperador hubiera podido *pagar a Orbán*? Te leo en *comentarios*."),
    ("final", "Y si te ha gustado, suscríbete a *Paradojas de la Historia*."),
]


def screen_text(s):
    return re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", s)


def voice_text(s):
    s = re.sub(r"\{[^|}]*\|([^}]*)\}", r"\1", s).replace("*", "")
    for a, b in SAY.items():
        s = s.replace(a, b)
    return s


# formato compatible con voz.py: (narración_para_voz, [bloques], plano)
def chunks(s):
    """Parte la frase (con *marcas*) en bloques de subtítulo de 2–4 palabras, cortando en la puntuación.
    Si una expresión resaltada queda partida entre dos bloques, el resaltado sigue en el siguiente."""
    words = screen_text(s).split()
    groups, cur = [], []
    for w in words:
        cur.append(w)
        n = len(cur); clean = w.replace("*", "")
        if (n >= 3 and len(" ".join(cur)) > 14) or n >= 4 or (n >= 2 and clean[-1:] in ",.:;?…"):
            groups.append(cur); cur = []
    if cur:
        if groups and len(cur) == 1: groups[-1] += cur
        else: groups.append(cur)
    out, open_hl = [], False
    for g in groups:
        txt = " ".join(g)
        if open_hl: txt = "*" + txt
        open_hl = (txt.count("*") % 2 == 1)
        if open_hl: txt = txt + "*"
        txt = txt.rstrip(".,;:").replace(".*", "*").replace(",*", "*")
        out.append(txt.upper())
    return out


SCENES = [(voice_text(s), chunks(s), name) for name, s in LINES]


def _durations():
    p = os.path.join(HERE, "voz", "duraciones.json")
    if os.path.exists(p):
        return json.load(open(p))
    return [len(s[0].split()) / 2.9 for s in SCENES]


def timeline():
    out, t = [], 0.0
    for i, d in enumerate(_durations()):
        a = t
        v = a + (INTRO if i == 0 else 0.0)
        b = v + d + GAP
        out.append((a, b, v)); t = b
    a, b, v = out[-1]
    out[-1] = (a, b + OUTRO, v)
    return out


TIMES = timeline()
TOTAL = TIMES[-1][1]


def caption_timeline():
    out = []
    durs = _durations()
    for i, ((a, b, v), (_n, chs, _s)) in enumerate(zip(TIMES, SCENES)):
        w = [len(c.replace("*", "")) + 4 for c in chs]
        tot = sum(w); t = v; span = durs[i]
        for c, wi in zip(chs, w):
            dd = span * wi / tot
            out.append((t, t + dd, c)); t += dd
    return out


def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(caption_timeline(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c.replace('*', '')}\n\n")


def story_keys():
    """Planos para la escena 3D: frases consecutivas con el mismo plano se funden en una escena."""
    out = []
    for (a, b, v), s in zip(TIMES, SCENES):
        if out and out[-1]["name"] == s[2]:
            out[-1]["b"] = round(b, 3)
        else:
            out.append({"name": s[2], "a": round(a, 3), "b": round(b, 3), "v": round(v, 3)})
    return out


if __name__ == "__main__":
    json.dump({"total": round(TOTAL, 3), "scenes": story_keys()},
              open(os.path.join(HERE, "escena3d", "timeline.json"), "w"), indent=1)
    print(f"total {TOTAL:.2f} s ({TOTAL / 60:.1f} min) · {len(story_keys())} planos · {len(SCENES)} frases")
