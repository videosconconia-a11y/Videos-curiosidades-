#!/usr/bin/env bash
# Genera el vídeo completo: música+efectos, escenas, unión y versión web.
set -euo pipefail
cd "$(dirname "$0")"
python3 audio.py
python3 -c "from script_data import write_srt; write_srt('subtitulos.srt')"
N=$(python3 -c "from script_data import SCENES; print(len(SCENES))")
python3 render.py video $(seq 0 $((N-1)))
for i in $(seq 0 $((N-1))); do printf "file 'scene_%02d.mp4'\n" "$i"; done > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy video_only.mp4
ffmpeg -y -loglevel error -i video_only.mp4 -i music_sfx.wav -map 0:v -map 1:a -c:v libx264 -preset veryfast \
  -crf 22 -maxrate 10M -bufsize 20M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart final_9x16.mp4
ffmpeg -y -loglevel error -i final_9x16.mp4 -vf scale=720:1280 -c:v libx264 -preset veryfast -crf 27 -maxrate 1.9M \
  -bufsize 3.8M -c:a aac -b:a 128k -movflags +faststart web/rana.mp4
rm -f scene_*.mp4 video_only.mp4 list.txt
echo "Listo: final_9x16.mp4 y web/index.html"
