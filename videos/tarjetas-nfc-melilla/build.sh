#!/usr/bin/env bash
# Genera el anuncio completo: voz (Piper), música+efectos con ducking, planos, unión y versión ligera.
set -euo pipefail
cd "$(dirname "$0")"
python3 voice.py
python3 audio.py
N=$(python3 -c "from script_data import SHOTS; print(len(SHOTS))")
seq 0 $((N-1)) | xargs -P "${JOBS:-4}" -I{} python3 render.py video {}
for i in $(seq 0 $((N-1))); do printf "file 'shot_%02d.mp4'\n" "$i"; done > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy video_only.mp4
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 -maxrate 12M \
  -bufsize 24M -pix_fmt yuv420p -af loudnorm=I=-14:TP=-1.5:LRA=9 -ar 48000 -c:a aac -b:a 192k -shortest -movflags +faststart final_9x16.mp4
rm -f shot_*.mp4 video_only.mp4 list.txt
echo "Listo: final_9x16.mp4 + subtitulos.srt"
