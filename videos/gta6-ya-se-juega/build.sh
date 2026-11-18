#!/usr/bin/env bash
# Genera el vídeo completo: voz, música con ducking, imagen, unión y subtítulos.
set -euo pipefail
cd "$(dirname "$0")"
python3 voice.py                 # locución + tiempos por palabra (necesita red)
python3 audio.py                 # música synthwave + efectos + voz, -14 LUFS
python3 -c "from script_data import write_srt; write_srt('subtitulos_gta6_ya_se_juega.srt')"
python3 render.py video
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart final_9x16.mp4
rm -rf video_only.mp4 mix.wav tmp_voice check_*.png
echo "Listo: final_9x16.mp4"
