# El paso Diátlov (1959) — historia de miedo real

Vídeo vertical 9:16 de ~60 s con **voz en off masculina en español de España**, música de terror, efectos y subtítulos.

- `script_data.py` — guion, subtítulos y planos. Los tiempos se calculan con la duración real de la voz.
- `tts.py` — genera la voz por escena: intenta OpenAI `gpt-4o-mini-tts` (voz *onyx*, instrucciones de acento
  peninsular) y, si no hay acceso, usa **Piper** con `es_ES-davefx-medium` (+ ecualización y compresión de locutor).
  `TTS_ENGINE=piper python3 tts.py` fuerza Piper. El modelo .onnx no se sube al repo: descárgalo en `voz/modelo/`.
- `audio.py` — drone, viento, caja de música, latidos, desgarro de lona, pasos en la nieve, hoguera, Geiger,
  máquina de escribir, alud… y mezcla con la voz bajando la música mientras habla (ducking).
- `render.py` — planos (lona rajada, huellas, excursionistas, Montaña Muerta, cedro, rayos X, contador Geiger,
  expediente «ЗАКРЫТО», alud…). `python3 render.py stills 2 10 30` para revisar fotogramas.
- `build.sh` — todo junto → `final_9x16.mp4`, `subtitulos.srt`, `web/dyatlov.mp4`.
- `FUENTES.md` — fuentes y precisiones. `PUBLICAR.md` — título, descripción y hashtags.
