# «LA RESEÑA QUE DESTRUYÓ UNA FAMILIA» — telenovela absurda para vender tarjetas NFC (9:16, 40 s)

Parodia de telenovela turca: drama exagerado, primerísimos planos, triple zoom de «¡NO PUEDE SER!», lluvia, relámpagos,
pétalos, cámara lenta y coro celestial… para enseñar cómo funciona la tarjeta NFC de reseñas (la tarjeta real del cliente).

## Archivos
- `final_9x16.mp4` — vídeo final 1080×1920, 30 fps, audio a −14 LUFS.
- `subtitulos.srt` — subtítulos de los diálogos (también van grabados en el vídeo).
- `build.sh` — lo regenera todo: `voice.py` → `audio.py` → `render.py` (planos) → unión.
- `characters.py` (personajes ilustrados) · `nfc_common.py` (tarjeta 3D, móvil, efectos).

## Reparto (ilustrado, personajes ficticios)
- **Rafa**, el barbero (voz Piper `es_ES-sharvard` masculina).
- **Sofía**, «la del restaurante de enfrente» (voz `es_ES-sharvard` femenina).
- **La abuela Carmen** y **Nacho**, el camarero (aparecen adorando la tarjeta).
- Narrador dramático (voz `es_ES-davefx`, más grave y con eco).

## Escaleta
| s | Plano | Texto / diálogo |
|---|---|---|
| 0–4 | Faro de Melilla y entrada al puerto (fotos reales) + cabecera del culebrón | «MELILLA… NADIE ESTABA PREPARADO PARA ESTA TRAICIÓN» · Narrador: «En una ciudad donde todos se conocen… una reseña lo cambiaría todo». |
| 4–9 | Rafa en la barbería mirando el móvil; zoom a la cara y lágrima | Rafa: «Llevo meses esperando que mis clientes encuentren mi perfil de Google…» |
| 9–14 | Sofía aparece a contraluz en la puerta con la tarjeta; triple zoom a Rafa; Sofía levanta la ceja | Sofía: «¿Todavía no tienes una tarjeta NFC?» · «¡NO PUEDE SER!» |
| 14–20 | La tarjeta con rayos dorados; el móvil la toca, sale el aviso NFC y la página para valorar | Sofía: «Solo tienes que acercar el móvil… y tus clientes podrán acceder directamente a tus reseñas». |
| 20–26 | Murallas Reales, Rafa gritando al cielo bajo la tormenta, Puerto Noray, centro modernista, Melilla la Vieja | Rafa: «¡¿POR QUÉ NADIE ME LO HABÍA CONTADO ANTES?!» (con eco) |
| 26–33 | Todos alrededor de la tarjeta en un altar, pétalos y coro | «LA TECNOLOGÍA HA LLEGADO A MELILLA» · «PARA BARBERÍAS, RESTAURANTES Y COMERCIOS» |
| 33–40 | Plano cinematográfico de la tarjeta; Rafa mira a cámara llorando; cierre | Rafa: «Yo solo quería que mis clientes pudieran dejar su opinión más fácilmente…» · «NO ESPERES AL PRÓXIMO CAPÍTULO» · «CONSIGUE TU TARJETA NFC» · «ESCRÍBENOS POR PRIVADO» · «Continuará…» |

## Comprobaciones
- Sin reseñas, cifras ni resultados inventados. La página que se abre en el móvil aparece **vacía** (las estrellas sin marcar):
  el cliente es quien escribe su opinión.
- Lo que hace la tarjeta: abre el enlace de reseñas al acercar el móvil (en iPhone aparece un aviso que hay que tocar;
  en Android el NFC tiene que estar activado). Por eso el vídeo enseña ese aviso.
- Google permite pedir reseñas, pero no ofrecer nada a cambio ni pedirlas solo a los clientes contentos.
- La barbería, el restaurante y los personajes son ficticios; no representan negocios reales de Melilla.

## Música y sonido
Banda sonora original generada por código: cuerdas en modo Hicaz (sonido «turco»), flauta ney, piano triste, darbuka,
timbales, golpes «DUN DUN DUN» en el triple zoom, coro celestial, arpa, lluvia, truenos y el «ding» del toque NFC.
La música baja automáticamente cuando hablan los personajes (ducking).

## Fotografías
Ver `assets/photos/CREDITOS.md` (CC BY / CC BY‑SA de Flickr). Hay que citar a los autores al publicar.
Los modelos de voz no se suben al repo: se descargan de https://huggingface.co/rhasspy/piper-voices
(`es/es_ES/davefx/medium` y `es/es_ES/sharvard/medium`) en `voices/`.

## Texto para publicar
**Título:** LA RESEÑA QUE DESTRUYÓ UNA FAMILIA 🌹📲 (Capítulo 1)

**Descripción:**
En una ciudad donde todos se conocen… Rafa descubrió el secreto demasiado tarde 😭
Tarjetas NFC para que tus clientes lleguen a tu perfil de reseñas de Google con solo acercar el móvil.
Barberías, restaurantes, cafeterías y comercios de Melilla: no esperes al próximo capítulo. Escríbenos por privado 💌

Fotos: YuriyGen, Yeray Díaz, fernand0 y Miguel González Novo (Flickr, CC BY / CC BY‑SA).

**Hashtags:** #Melilla #Telenovela #NFC #ReseñasGoogle #NegociosMelilla #ComercioLocal #Barbería #Humor #Drama #TikTokMelilla
