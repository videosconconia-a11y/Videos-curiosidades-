# El gadget que Melilla no sabía que necesitaba — anuncio TikTok (9:16, ~35 s)

Anuncio estilo «gadget viral» para tarjetas NFC de reseñas de Google de una empresa local de Melilla.
El producto que aparece es la tarjeta real del cliente (`assets/tarjeta_nfc.png`, foto enderezada).

## Archivos
- `final_9x16.mp4` — vídeo final 1080×1920, 30 fps, audio normalizado a −14 LUFS.
- `subtitulos.srt` — subtítulos de la locución.
- `build.sh` — lo regenera todo (`voice.py` → `audio.py` → `render.py`).

## Estructura (segundos)
| Tramo | Escena | Texto en pantalla |
|---|---|---|
| 0–3 | Faro de Melilla + notificación «Nuevo gadget detectado» | MELILLA, DEJA DE HACER ESTO EN TU NEGOCIO |
| 3–6 | Caja misteriosa que se abre y deja salir la tarjeta | PARECE UNA TARJETA NORMAL… PERO NO LO ES |
| 6–10 | Mano con el móvil, toque, aviso NFC y página de reseña | ACERCAS. TOCAS. ACCEDES. |
| 10–14 | La tarjeta vuela a cámara → Murallas Reales con HUD de videojuego | TECNOLOGÍA PARA LOS NEGOCIOS DE AQUÍ |
| 14–19 | Barbería, restaurante, tienda, cualquier negocio (ilustración neón) | PARA BARBERÍAS / RESTAURANTES / TIENDAS / CUALQUIER NEGOCIO |
| 19–24 | Parque Hernández y Puerto Noray con la tarjeta flotando | MENOS PASOS. MÁS COMODIDAD. |
| 24–30 | Montaje rápido: faro, playa, Melilla la Vieja, Hernández, centro modernista, calles | MELILLA TIENE FUTURO / TALENTO / TECNOLOGÍA |
| 30–35 | Tarjeta en plató de lujo + llamada a la acción | TU NEGOCIO TAMBIÉN PUEDE DAR EL SALTO · TARJETAS NFC · ESCRÍBENOS POR PRIVADO |

## Comprobaciones (sin cifras ni testimonios inventados)
- No se usan cifras, testimonios ni resultados. Solo se describe lo que hace la tarjeta: abrir un enlace al tocarla con el móvil.
- Funcionamiento real del NFC: en iPhone (XS y posteriores) la lectura de etiquetas es en segundo plano y aparece un aviso que hay que tocar
  para abrir el enlace (por eso el vídeo muestra ese aviso). En Android hace falta tener el NFC activado y la pantalla desbloqueada.
  Algunos móviles no tienen NFC; conviene tener también un código QR.
- Las políticas de Google permiten pedir reseñas, pero no ofrecer incentivos por ellas ni pedirlas solo a los clientes contentos.
  El anuncio no promete reseñas positivas: solo facilita el acceso al enlace.
- Las escenas de negocios son ilustraciones genéricas, no negocios reales concretos.
  Si tenéis clientes que ya usan la tarjeta, sustituirlas por clips reales (con su permiso) le dará aún más fuerza.

## Fotografías y licencias
Ver `assets/photos/CREDITOS.md`. Son fotos CC BY‑SA 2.0 de Flickr: hay que citar a los autores (por ejemplo, en la descripción o en un comentario fijado).

## Voz y música
- Voz: Piper TTS, voz `es_ES-davefx-medium` (español de España), con ecualización y compresión. El modelo no se sube al repo;
  se descarga de https://huggingface.co/rhasspy/piper-voices (es/es_ES/davefx/medium) en `voices/`.
- Música electrónica original a 124 BPM generada por código, con efectos (notificación, caja, «toque» NFC, glitch, power‑up de videojuego)
  y la música bajando mientras habla la voz (ducking).

## Texto para publicar
**Título:** El gadget que Melilla no sabía que necesitaba 📲

**Descripción:**
Parece una tarjeta normal… pero no lo es. Tus clientes acercan el móvil, tocan y llegan directamente a tu enlace de reseñas de Google. Sin buscar tu negocio, sin pasos de más.
Para barberías, restaurantes, cafeterías, tiendas… cualquier negocio de Melilla.
👉 Escríbenos por privado y te contamos.

Fotos: Miguel González Novo y fernand0 (CC BY‑SA 2.0, Flickr).

**Hashtags:** #Melilla #NegociosMelilla #NFC #ReseñasGoogle #Gadget #ComercioLocal #Emprendedores #Tecnología #MarketingLocal #TikTokMelilla
