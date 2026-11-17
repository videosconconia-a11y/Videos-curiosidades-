# Vídeos de curiosidades

Generador de vídeos verticales (9:16) de curiosidades para TikTok, Instagram Reels y YouTube Shorts.
Cada vídeo vive en su carpeta dentro de `videos/` y se genera con código: imágenes animadas, música,
efectos de sonido y subtítulos sincronizados.

## Vídeos

| Carpeta | Tema | Duración |
|---|---|---|
| `videos/rana-de-bosque` | La rana que se congela… y vuelve a la vida | 58,5 s |

## Estructura de cada vídeo

- `script_data.py` — guion: narración, tiempos de cada escena, bloques de subtítulos y planos.
- `render.py` — dibuja cada plano (Python + Pillow + NumPy) y codifica las escenas con ffmpeg.
- `audio.py` — sintetiza música de tensión, golpes, crujidos de hielo, latidos, etc.
- `build.sh` — genera todo: `final_9x16.mp4`, `subtitulos.srt` y la versión web.
- `web/index.html` — reproductor con narración por voz del navegador (`speechSynthesis`) sincronizada por escenas.

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
