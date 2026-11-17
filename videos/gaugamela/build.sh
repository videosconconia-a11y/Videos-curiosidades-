#!/usr/bin/env bash
# Genera el vídeo completo: voz → tiempos → escena 3D → audio → posproducción → medición.
set -euo pipefail
cd "$(dirname "$0")"
python3 voz.py                       # Piper TTS es_ES (modelo en ~/voces o $PIPER_VOICE)
python3 script_data.py               # tiempos reales → escena3d/timeline.json
python3 -c "from script_data import write_srt; write_srt('subtitulos.srt')"
(cd escena3d && [ -d node_modules ] || npm install --silent)
(cd escena3d && node render.cjs video ../escena3d.mp4)
python3 audio.py
python3 post.py
python3 ../../tools/medir.py final_9x16.mp4 --json medidas.json
echo "Listo: final_9x16.mp4, subtitulos.srt, PUBLICAR.md"
