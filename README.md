# Vídeos de curiosidades

Generador de vídeos verticales (9:16) de curiosidades para TikTok, Instagram Reels y YouTube Shorts.
Cada vídeo vive en su carpeta dentro de `videos/` y se genera con código: imágenes animadas, música,
efectos de sonido y subtítulos sincronizados.

## Vídeos

| Carpeta | Tema | Duración |
|---|---|---|
| `videos/rana-de-bosque` | La rana que se congela… y vuelve a la vida | 58,5 s |
| `videos/gaugamela` | Alejandro Magno venció a un ejército el doble de grande… alejándose de él (2D en un mundo 3D) | 56,1 s |
| `videos/cleopatra` | Cleopatra vivió más cerca del iPhone… que de las pirámides (camino del tiempo en 3D) | 61,1 s |
| `videos/troya` | Diez años de batallas no abrieron Troya… un regalo lo hizo en una noche (2D en un mundo 3D) | 61,5 s |

## Estructura de cada vídeo

- `script_data.py` — guion: narración, tiempos de cada escena, bloques de subtítulos y planos.
- `render.py` — dibuja cada plano (Python + Pillow + NumPy) y codifica las escenas con ffmpeg.
- `audio.py` — sintetiza música de tensión, golpes, crujidos de hielo, latidos, etc.
- `build.sh` — genera todo: `final_9x16.mp4`, `subtitulos.srt` y la versión web.
- `web/index.html` — reproductor con narración por voz del navegador (`speechSynthesis`) sincronizada por escenas.

## Estilo «personajes 2D en un mundo 3D» (`videos/gaugamela`)

- `escena3d/`: escena en Three.js. Los personajes son recortes 2D dibujados con código (`sprites.js`) que
  reciben la luz del mundo y proyectan sombras reales. El terreno, las montañas, las rocas y los
  estandartes son geometría 3D con contorno de tinta. La cámara es una única curva continua, sin cortes,
  y la luz cambia con la historia (cálida → azul en la explicación → fuego → noche).
- `render.cjs`: renderiza cuadro a cuadro en Chromium sin ventana (Playwright) y lo pasa a ffmpeg.
- `voz.py`: narración con Piper TTS (voz `es_ES-davefx-medium`). Los tiempos de cada escena salen de la
  duración real de la voz.
- `audio.py`: música sintetizada, efectos y ducking. `post.py`: subtítulos, cifras discretas y tarjeta final.
- Requisitos: `npm install` en `escena3d/`, `pip install piper-tts numpy scipy pillow` y el modelo de voz
  en `~/voces/`.

## Guía de estilo y medición

- `GUIA_ESTILO.md`: reglas de guion, cámara y luz, con cifras objetivo.
- `tools/medir.py`: mide un vídeo cuadro por cuadro (movimiento de cámara con correlación de fase, cortes,
  brillo, contraste, saturación) y crea hojas de contactos. Sirve para comparar tu vídeo con un original.
- `tools/ritmo.py`: palabras por segundo de cada escena del guion.

## Uso

```bash
pip install numpy pillow scipy
cd videos/rana-de-bosque
./build.sh
```

Necesita `ffmpeg`. Usa Poppins Bold si está instalada y, si no, Inter ExtraBold o DejaVu Sans Bold.

## Voz con IA

El vídeo final no lleva narración grabada. Opciones:
1. Generar la voz (ElevenLabs, CapCut, Piper TTS…) con el texto de `script_data.py` y mezclarla con ffmpeg.
2. Usar `web/index.html`, que narra con la voz del navegador.
