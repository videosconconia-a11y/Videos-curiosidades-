# Short: Cómo ganar dinero en GTA 6 (versión pre-lanzamiento)

- **Formato:** MP4 vertical 1080×1920, 30 fps, ~52 s, voz en castellano de España, subtítulos palabra a palabra.
- **Generar:** `./build.sh` → `final_9x16.mp4` + `subtitulos_gta6_dinero.srt`.
- **Archivos:** `script_data.py` (guion, subtítulos y planos), `tts.py` (voz), `audio.py` (música, efectos y ducking),
  `render.py` (fotogramas), `img/` (capturas oficiales; no se suben al repositorio).

## Importante: hecho ANTES del lanzamiento
Se hizo el 17/11/2026, dos días antes de que salga el juego (19/11/2026). Todavía no existen guías de jugadores,
así que el vídeo **solo cuenta mecánicas que Rockstar ya ha enseñado** (tráiler "An Extended Look", textos de
rockstargames.com y entrevistas con prensa). No da cifras de dinero, misiones ni ubicaciones concretas porque no se
han publicado. Los contadores ($1.000.000 → $0 y $0 → $1.000.000) son animaciones de ejemplo y no prometen ninguna
cantidad ni ningún plazo. Si al jugar algún dato cambia, hay que actualizar el guion.

**Corrección del encargo:** el título pedido ("Haz tu primer millón en menos de una hora", etc.) no se puede cumplir
sin inventar datos, así que el gancho es "Si no haces esto en GTA 6 puedes perder TODO tu dinero". Ese gancho sí se
cumple: el error de morir con el efectivo encima.

## Datos usados y fuentes
| Dato del vídeo | Fuentes |
|---|---|
| Robos en tiendas y gasolineras; las tiendas pequeñas dan efectivo | GamesRadar (cobertura de "An Extended Look", 2026); Kotaku, "10 New Details We Learned From GTA 6's Big Info Dump"; Kotaku, "GTA 6 Will Give You A New Way To Avoid Killing Cops And Civilians" (Rob Nelson, Rockstar: robos de tiendas) |
| Los golpes grandes pueden dar joyas, lingotes de oro o droga en vez de billetes | GamesRadar, "New GTA 6 activities, customization, and gameplay details revealed"; Vice, "GTA 6 Just Revealed a Massive Number of New Gameplay Details" |
| El botín hay que venderlo a un perista; hay peristas distintos (joyas, droga, oro) y se desbloquean con la historia | GamesRadar (íd.); Vice (íd.) |
| Robar coches por encargo: los detalles llegan por una app del móvil y se cobra según el estado del coche | GamesRadar, "Rockstar says GTA 6 won't let you magically hotwire every car"; Vice (íd.) |
| Al morir con mucho efectivo encima se pierde una buena parte o todo; conviene ingresarlo en un cajero | GamesRadar (cobertura de "An Extended Look"); Kotaku (íd.) |
| Lanzamiento: 19 de noviembre de 2026 (PS5 y Xbox Series X\|S) | rockstargames.com/VI; Tom's Guide |

Enlaces:
- https://www.rockstargames.com/VI
- https://www.gamesradar.com/news/live/gta-6-extended-look-showcase-live-coverage-2026-everything-announced/
- https://www.gamesradar.com/games/grand-theft-auto/gta-6-new-gameplay-details-activities-customization-confirmed-63-screenshots/
- https://www.gamesradar.com/games/grand-theft-auto/rockstar-says-gta-6-wont-let-you-magically-hotwire-every-car-you-acquire-certain-tools-to-get-into-them/
- https://kotaku.com/10-new-details-we-learned-from-gta-6s-big-info-dump-2000710519
- https://kotaku.com/gta-6-will-give-you-a-new-way-to-avoid-killing-cops-and-civilians-2000729112
- https://www.vice.com/en/article/gta-6-new-gameplay-features-details-revealed/

Nota de verificación: desde el entorno de trabajo no se pudo abrir GamesRadar, Kotaku ni GameSpot (red bloqueada).
Los datos se contrastaron con los extractos de varios buscadores, y todas las fuentes coinciden. Antes de publicar
conviene abrir al menos un artículo para confirmarlo.

**Lo que NO está confirmado y por eso no sale en el vídeo:** negocios que den dinero de forma pasiva (las tiendas de
la Ultimate Edition solo dan acceso, no se pueden comprar), trucos de dinero y cantidades por robo.

## Imágenes
Solo hay capturas y arte oficiales descargados de rockstargames.com/VI (galería, personajes, "Only in Leonida",
Ultimate Edition). No se ha usado nada del hackeo de 2022. En pantalla aparece siempre el crédito
"Imágenes © Rockstar Games · vídeo fan, no afiliado".

## Voz y audio
- Voz: Microsoft Edge TTS `es-ES-AlvaroNeural` (masculina, castellano peninsular) a velocidad +22 %. "GTA 6" se
  escribe "GTA seis" para que lo lea bien. La voz de OpenAI no se pudo usar porque la cuenta no tenía crédito, y no
  había clave de ElevenLabs.
- Música: base trap oscura sintetizada (Do menor, 140 BPM), de creación propia y sin derechos de terceros.
- Efectos: impacto en el gancho y en cada PASO, whoosh en cada corte, caja registradora en las palabras de dinero.
- Ducking: la música baja 15 dB mientras habla la voz y queda unos 10–11 dB por debajo. Volumen final normalizado
  a −14 LUFS.

## Texto para publicar
Ver `PUBLICAR.md`.
