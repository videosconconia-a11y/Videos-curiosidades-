# El misterio de Melilla

Anuncio vertical (9:16, 40 s, 1080×1920, 30 fps) para TikTok de placas/tarjetas NFC para reseñas de Google.
Película de extraterrestres + documental de naturaleza + terror + ciencia ficción, con humor absurdo.

- `final_9x16.mp4` — vídeo final con voz, música y efectos.
- `subtitulos.srt` — subtítulos de toda la locución.
- `web/misterio.mp4` — versión ligera 720p.

## Estructura

| Tiempo | Escena | Qué se ve |
|---|---|---|
| 0–3 s | Gancho | Pantalla negra con alarma → vista aérea real de Melilla con un ovni en el cielo. «MELILLA, ESTO NO ES UN SIMULACRO» entre bandas de peligro. Voz: «Algo acaba de aterrizar en Melilla…» |
| 3–7 s | Invasión | El ovni sobrevuela el Puerto Deportivo, barre la ciudad con su haz y aterriza en la Plaza de España con luces y humo. «LOS EXTRATERRESTRES HAN VENIDO A BUSCAR ALGO» |
| 7–11,5 s | Descubrimiento | Un marciano entra en una barbería, ve la placa NFC en el mostrador → zoom exagerado + escáner. «¿QUÉ ES ESTE OBJETO?» |
| 11,5–16 s | Revelación | La mano verde acerca el móvil → «bip», explosión de luz, se abre la página de reseñas. «¡Increíble! ¡Un solo toque…!» |
| 16–25 s | Documental | «EL COMERCIANTE MELILLENSE (Homo commercialis melillensis)»: restaurante, barbería, hostelería, mercado, calle comercial y tienda, cada uno con su placa NFC y su rótulo de «HÁBITAT» |
| 25–30 s | Giro | «TRANSMISIÓN INTERCEPTADA»: el marciano mira a cámara: «En nuestro planeta llevamos 500 años buscando algo así». «LA TECNOLOGÍA YA ESTÁ EN MELILLA» |
| 30–35 s | Orgullo local | Puerta de la Marina, Almacenes La Reconquista, Plaza de las Culturas, Sagrado Corazón, playa de los Cárabos y el Faro (con el ovni marchándose) |
| 35–40 s | Venta | La placa NFC flota en el espacio: «DA EL SALTO AL FUTURO» · «TARJETAS NFC PARA TU NEGOCIO» · «ESCRÍBENOS POR PRIVADO» |

Los tiempos se han ajustado respecto al guion original (documental de 16 a 25 s) porque la frase del narrador
del documental dura 8,6 s a velocidad natural y no cabía en 6 s. Total: 40 s exactos.

## Voz
- Narrador y documental: Kokoro `em_alex` (masculina, natural, fonética de España). El arranque lleva un poco de sala («misteriosa»).
- Extraterrestre: Kokoro `em_santa`, más aguda y ondulada. Lleva subtítulos «TRADUCCIÓN DEL MARCIANO» para que se entienda siempre.
- La música baja ~8,5 dB mientras hay voz (ducking).

## Texto para publicar

**Título:** 👽 MELILLA, ESTO NO ES UN SIMULACRO

**Descripción:**
Algo ha aterrizado en Melilla… y ha venido a buscar nuestras placas NFC 😳
Un toque con el móvil y tus clientes llegan directos a tu página de reseñas de Google. Sin buscar, sin complicaciones.
No hace falta venir de otro planeta: somos de Melilla. 👉 Escríbenos por privado y consigue la tuya.

**Hashtags:** #Melilla #ExtraterrestresEnMelilla #NegociosDeMelilla #NFC #ReseñasGoogle #ComercioLocal #Ovni #Humor #TarjetaNFC #fyp

Créditos de fotos: «Fotos: Wikimedia Commons (autores en FUENTES.md)» en la descripción o en un comentario fijado.

## Notas
- Sin estadísticas, resultados ni reseñas inventadas. La página del móvil es una maqueta con «TU NEGOCIO».
- El extraterrestre, el ovni y el documental son ficción humorística.
- Lectura NFC: móviles con NFC (Android con NFC activado; iPhone XS o posterior).

## Regenerar
```bash
pip install scipy pillow numpy kokoro-onnx soundfile
# en voices/ (o KOKORO_DIR=/ruta): onnx/model.onnx, voices/em_alex.bin y voices/em_santa.bin de
# https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX
./build.sh
python3 render.py stills 2.0 9.5    # fotogramas de prueba en stills/
```
`base.py` es el motor compartido con `videos/melilla-2050` (placa 3D, móvil, HUD, efectos).
