#!/usr/bin/env bash
# Genera el vídeo completo: voz IA → música+efectos+ducking → escenas → unión → subtítulos → versión web.
set -euo pipefail
cd "$(dirname "$0")"
if python3 -c "import piper" 2>/dev/null; then python3 tts.py; else echo "AVISO: sin Piper (pip install piper-tts); vídeo sin voz"; fi
python3 audio.py
python3 -c "from script_data import write_srt; write_srt('subtitulos_gta6_iceberg.srt')"
N=$(python3 -c "from script_data import SCENES; print(len(SCENES))")
seq 0 $((N-1)) | xargs -P "$(nproc)" -I{} python3 render.py video {}
for i in $(seq 0 $((N-1))); do printf "file 'scene_%02d.mp4'\n" "$i"; done > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy video_only.mp4
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset veryfast \
  -crf 21 -maxrate 10M -bufsize 20M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart final_9x16.mp4
ffmpeg -y -loglevel error -i final_9x16.mp4 -vf scale=720:1280 -c:v libx264 -preset veryfast -crf 27 -maxrate 1.9M \
  -bufsize 3.8M -c:a aac -b:a 128k -movflags +faststart web/gta6.mp4
rm -f scene_*.mp4 video_only.mp4 list.txt
echo "Listo: final_9x16.mp4, subtitulos_gta6_iceberg.srt y web/index.html"
