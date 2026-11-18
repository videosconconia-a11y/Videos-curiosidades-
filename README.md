# Vídeos de curiosidades

Generador de vídeos verticales (9:16) de curiosidades para TikTok, Instagram Reels y YouTube Shorts.
Cada vídeo vive en su carpeta dentro de `videos/` y se genera con código: imágenes animadas, música,
efectos de sonido y subtítulos sincronizados.

## Vídeos

| Carpeta | Tema | Duración |
|---|---|---|
| `videos/rana-de-bosque` | La rana que se congela… y vuelve a la vida | 58,5 s |
| `videos/gta-6-iceberg` | El iceberg de GTA 6 (formato iceberg, voz IA Piper es_ES con ducking) | 59,8 s |

## Estructura de cada vídeo

- `script_data.py` — guion: narración, tiempos de cada escena, bloques de subtítulos y planos.
- `render.py` — dibuja cada plano (Python + Pillow + NumPy) y codifica las escenas con ffmpeg.
- `audio.py` — sintetiza música de tensión, golpes, crujidos de hielo, latidos, etc.
- `build.sh` — genera todo: `final_9x16.mp4`, `subtitulos.srt` y la versión web.
- `web/index.html` — reproductor con narración por voz del navegador (`speechSynthesis`) sincronizada por escenas.

## Uso

```bash
pip install numpy pillow scipy
cd videos/rana-de-bosque
./build.sh
```

Necesita `ffmpeg` y la fuente Poppins Bold (cambia la ruta `FONT` en `render.py` si está en otro sitio).

## Voz con IA

`videos/gta-6-iceberg` ya lleva voz: `tts.py` la genera con Piper (`pip install piper-tts`, voz `es_ES-davefx-medium`,
se descarga sola), los tiempos de cada escena se ajustan a la duración real de la voz y `audio.py` baja la música
mientras habla (ducking). Copia esa carpeta como plantilla para vídeos con voz.

Análisis de estrategia en `analisis/`.

El vídeo final no lleva narración grabada. Opciones:
1. Generar la voz (ElevenLabs, CapCut, Piper TTS…) con el texto de `script_data.py` y mezclarla con ffmpeg.
2. Usar `web/index.html`, que narra con la voz del navegador.
