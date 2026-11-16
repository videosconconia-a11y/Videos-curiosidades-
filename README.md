# Vídeos de curiosidades

Generador de vídeos verticales (9:16) de curiosidades para TikTok, Instagram Reels y YouTube Shorts.
Cada vídeo vive en su carpeta dentro de `videos/` y se genera con código: imágenes animadas, música,
efectos de sonido y subtítulos sincronizados.

## Vídeos

| Carpeta | Tema | Duración |
|---|---|---|
| `videos/rana-de-bosque` | La rana que se congela… y vuelve a la vida (con voz IA y fotos reales) | ~72 s |

## Estructura de cada vídeo

- `script_data.py` — guion: frases de la voz, bloques de subtítulo, planos (anclados a palabras) y efectos.
- `voice.py` — voz en off con **Piper TTS** (voz es_ES «davefx»); mide la duración real de cada frase y de cada
  bloque de subtítulo y guarda `build/timing.json`. Todo el montaje se ajusta a esos tiempos.
- `audio.py` — música de tensión y efectos sintetizados, sincronizados con la voz; *ducking* (la música baja
  mientras habla la voz) y normalización a −14 LUFS.
- `ai_images.py` + `assets/ai/` — una imagen generada con IA por plano, según la narración (SDXL + SDXL-Lightning en
  local, o la API de OpenAI con `AI_BACKEND=openai`). Los planos de la rana parten de fotos reales (img2img).
- `media.py` + `assets/photos/` — fotos reales con licencia libre (Wikimedia Commons) usadas como base, con su punto de interés.
- `render.py` — monta cada plano (foto con movimiento de cámara, etalonaje, escarcha animada, nieve, gráficos)
  y los subtítulos dinámicos; codifica las escenas con ffmpeg.
- `build.sh` — genera todo: `final_9x16.mp4`, `subtitulos.srt` y `web/`.
- `FUENTES.md` — fuentes científicas y créditos/licencias de las fotos. `PUBLICAR.md` — título, descripción y hashtags.

## Uso

```bash
pip install numpy pillow scipy piper-tts torch diffusers transformers accelerate
cd videos/rana-de-bosque
./build.sh
```

Necesita `ffmpeg` (con `rubberband`). La voz se descarga sola la primera vez desde las *releases* de
sherpa-onnx en GitHub (modelos Piper). Las fuentes Poppins (OFL) están en `assets/fonts/`.
Variables opcionales: `VOICE=sharvard` (otra voz es_ES), `VOICE_SPEED=0.9` (menor = más rápido), `JOBS=4`.
