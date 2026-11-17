#!/usr/bin/env bash
# Genera el vídeo completo. Las imágenes (assets/) y la voz (voz/) ya están en el repositorio;
# para regenerarlas: python3 gen_images.py   y   python3 tts.py
set -euo pipefail
cd "$(dirname "$0")"
python3 -c "from timeline import write_srt; write_srt('subtitulos.srt')"
python3 audio.py
python3 render.py video
ffmpeg -y -loglevel error -i video_only.mp4 -i mezcla.wav -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 20 -maxrate 8M -bufsize 16M -profile:v high -pix_fmt yuv420p -r 30 \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart final_9x16.mp4
rm -f video_only.mp4
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 final_9x16.mp4
echo "Listo: final_9x16.mp4 + subtitulos.srt"
