#!/usr/bin/env bash
# Genera el anuncio completo: voz (Kokoro) -> música+efectos+ducking -> vídeo en 4 partes paralelas -> final.
set -euo pipefail
cd "$(dirname "$0")"
if [ -f voices/model.onnx ] || [ -n "${KOKORO_DIR:-}" ]; then python3 voice.py; else echo "Sin modelo Kokoro: se usa vo/ existente"; fi
python3 audio.py
python3 -c "from script_data import write_srt; write_srt('subtitulos.srt')"
P=4
seq 0 $((P-1)) | xargs -P $P -I{} python3 render.py video {} $P
for i in $(seq 0 $((P-1))); do printf "file 'part_%02d.mp4'\n" "$i"; done > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy video_only.mp4
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow \
  -crf 19 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart final_9x16.mp4
ffmpeg -y -loglevel error -i final_9x16.mp4 -vf scale=720:1280 -c:v libx264 -preset veryfast -crf 26 -maxrate 2.2M \
  -bufsize 4.4M -c:a aac -b:a 128k -movflags +faststart web/misterio.mp4
rm -f part_*.mp4 video_only.mp4 list.txt
echo "Listo: final_9x16.mp4, subtitulos.srt y web/misterio.mp4"
