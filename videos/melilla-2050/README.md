# MELILLA 2050 – El futuro ha llegado

Anuncio vertical (9:16, 40 s, 1080×1920, 30 fps) para TikTok de tarjetas NFC para conseguir reseñas de Google,
de una empresa de Melilla. La tarjeta que aparece es **el producto real** (placa cuadrada «¡Apreciaríamos tu reseña en Google!»,
foto en `producto/placa_nfc_original.jpg`), enderezada y animada en 3D; su trasera muestra el adhesivo 3M de doble cara. Mezcla ciencia ficción, informativo de última hora, HUD de videojuego, documental de
Melilla, publicidad de lujo y humor absurdo.

- `final_9x16.mp4` — vídeo final con voz, música y efectos.
- `subtitulos.srt` — subtítulos de la locución (súbelos en TikTok o actívalos como subtítulos automáticos).
- `web/melilla2050.mp4` — versión ligera 720p.

## Estructura (8 escenas)

| Tiempo | Escena | Qué se ve |
|---|---|---|
| 0–3 s | Gancho | Vista aérea real de Melilla con alarma roja, HUD futurista, rótulo «ÚLTIMA HORA: ¡MELILLA HA ENTRADO EN EL FUTURO!» |
| 3–6 s | Caos | Restaurante, mercado, barbería y comercios; buscador escribiendo torpemente, «?» volando y ventanas de error absurdas («Cliente.exe ha dejado de responder») |
| 6–10 s | Aparición | Plaza de España de noche: un haz de luz y la tarjeta NFC desciende girando; ondas al aterrizar |
| 10–14 s | El poder | La mano acerca el móvil a la tarjeta → anillos de escáner, «bip» NFC, se abre la página de reseñas y se rellenan las estrellas |
| 14–19 s | Montage | Playa de los Cárabos, Puerta de la Marina, Casa Tortosa, barbería, restaurante, tienda, tarjeta — con «MÁS FÁCIL / MÁS CÓMODO / MÁS TECNOLÓGICO» |
| 19–25 s | Giro | Plató «M50 NOTICIAS» con presentadora holográfica, rótulo de última hora y un rótulo inferior absurdo; corte brusco con glitch a la tarjeta |
| 25–32 s | Orgullo local | Melilla la Vieja, Palacio de la Asamblea, Faro, Parque Hernández, Casino Militar, playa de Trápana, con la tarjeta integrada |
| 32–40 s | Final | La tarjeta gira, llena la pantalla: «EL FUTURO DE TU NEGOCIO ESTÁ A UN TOQUE» + «CONSIGUE TU TARJETA NFC» + «ESCRÍBENOS POR PRIVADO» |

25 planos en 40 s (un cambio de plano o de texto cada 0,6–2,5 s), 22 fotos reales distintas, ninguna repetida.

## Voz
- Narrador: Piper TTS `es_ES-davefx-medium` (español de España), bajado de tono, comprimido y con reverberación → grave y misterioso.
- Presentadora del informativo: Piper `es_ES-sharvard-medium` (voz F), ecualizada como de plató.
- La música baja ~8,5 dB mientras habla la voz (ducking).

## Texto para publicar

**Título:** 🚨 ÚLTIMA HORA: MELILLA HA ENTRADO EN EL FUTURO

**Descripción:**
Un toque con el móvil y tu cliente llega directo a tu página de reseñas de Google. Sin buscar, sin complicaciones. 📲✨
Somos de Melilla y apostamos por los negocios de aquí: cafeterías, barberías, restaurantes, tiendas…
👉 Consigue tu tarjeta NFC: escríbenos por privado.

**Hashtags:** #Melilla #NegociosDeMelilla #NFC #ReseñasGoogle #ComercioLocal #Melilla2050 #Emprendedores #MarketingLocal #TarjetaNFC #fyp

## Notas importantes
- **No hay estadísticas ni promesas de resultados**: el anuncio solo dice que facilita dejar reseñas.
- La pantalla del móvil es una **maqueta** («TU NEGOCIO», enlace de ejemplo `g.page/r/tu-negocio/review`), no una captura real de Google.
- La presentadora es un holograma inventado; no representa a ninguna persona real ni cadena de televisión.
- Lectura NFC: funciona con móviles con NFC (Android con NFC activado; iPhone XS o posterior lee etiquetas NFC sin abrir ninguna app).
  Recomendable que la tarjeta lleve también un código QR para móviles sin NFC.
- La placa se recorta de `producto/placa_nfc_original.jpg` con las esquinas de `PLATE_CORNERS` en `render.py`; para usar otra foto del producto, cambia la imagen y esas 4 esquinas.
- Si la empresa tiene nombre/logo, se puede añadir en el plano final.
- Google no permite ofrecer incentivos a cambio de reseñas: conviene recordárselo a los clientes del negocio.

## Fotos (todas de Wikimedia Commons, licencias libres)
Ver [FUENTES.md](FUENTES.md) — autor y licencia de cada foto. Las licencias CC BY / CC BY-SA obligan a citar al autor:
pon «Fotos: Wikimedia Commons (autores en el enlace)» en la descripción o en un comentario fijado.
Dos fotos de barberías no son de Melilla (Palma y Oporto), porque Commons no tiene barberías de Melilla con licencia libre;
si tienes fotos propias de barberías o cafeterías de Melilla, sustitúyelas en `PHOTO` de `render.py`.

## Regenerar
```bash
pip install scipy piper-tts pillow numpy
python3 fetch_images.py            # solo si falta img/
# voces Piper en voices/ (o PIPER_VOICES=/ruta): es_ES-davefx-medium y es_ES-sharvard-medium (.onnx + .onnx.json)
./build.sh
python3 render.py stills 2.0 9.0   # fotogramas de prueba en stills/
```
