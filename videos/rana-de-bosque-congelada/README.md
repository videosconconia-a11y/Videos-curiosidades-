# La rana que se congela… y vuelve a la vida (v2, con narración)

Vídeo vertical 1080 × 1920, 30 fps, **≈ 79 s**, en español de España, listo para TikTok / Reels / Shorts.

- `final_9x16.mp4` — vídeo final (voz + música + efectos + subtítulos incrustados).
- `subtitulos.srt` — subtítulos sincronizados palabra a palabra con la voz.
- `PUBLICAR.md` — título, descripción y hashtags.
- `FUENTES.md` — datos científicos verificados y sus fuentes.

## Cómo está hecho

| Parte | Herramienta |
|---|---|
| Guion | `narracion.py` (24 frases con sus pausas) |
| Voz | `tts.py` — voz neural de castellano peninsular **es-ES-AlvaroNeural** (Microsoft Edge TTS), frase a frase, con tiempos por palabra |
| Línea de tiempo | `timeline.py` — coloca cada frase, genera subtítulos y da el inicio exacto de cada plano |
| Imágenes | `gen_images.py` + `prompts.json` — fotorrealistas generadas en local con RealVisXL V5.0 Lightning (SDXL). Las versiones congelada y viva de la misma rana se hacen por img2img, para que el animal no cambie al congelarse/deshelarse |
| Animaciones científicas | `fx.py` — escarcha que avanza, grietas, corte de piel y músculo con hielo, células con glucosa y hielo extracelular, hígado liberando glucosa, corazón y ECG, mapa de distribución (Natural Earth, dominio público) |
| Montaje | `render.py` — 28 planos (cambio cada 2–4 s), zooms, travellings, transiciones (fundido, zoom, destello), grano, viñeteado y subtítulos estilo TikTok (blancos con contorno/sombra negra, palabras clave en amarillo, colocados bajo el animal) |
| Audio | `audio.py` — música cinematográfica sintetizada (misterio en Re menor → tensión creciente → silencio cuando se para el corazón → Re mayor de asombro en el deshielo), efectos (hielo, latidos y pitidos sincronizados con el ECG, viento, goteo, salto) y ducking de la música bajo la voz (≈ −9 dB). Volumen final normalizado a −14 LUFS |

Las imágenes del animal son **recreaciones generadas por IA** (no hay vídeo libre de derechos de una rana de bosque congelándose); los gráficos interiores están rotulados como «Recreación científica».

## Regenerar

```bash
pip install numpy scipy pillow pyshp edge-tts
./build.sh                      # usa assets/ y voz/ ya incluidos
# opcional: python3 tts.py       (rehace la voz)   ·   python3 gen_images.py  (rehace las imágenes, ~7 GB de modelo)
```
