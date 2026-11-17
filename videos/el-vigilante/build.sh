#!/usr/bin/env bash
# Genera el vídeo completo: voz IA, música+efectos con ducking, escenas, unión.
set -euo pipefail
cd "$(dirname "$0")"
[ -f timings.json ] && [ "${REVOZ:-0}" = 0 ] || python3 voice.py
python3 audio.py
python3 -c "from script_data import write_srt; write_srt('subtitulos_el_vigilante.srt')"
N=$(python3 -c "from script_data import SCENES; print(len(SCENES))")
seq 0 $((N-1)) | xargs -P "$(nproc)" -I{} python3 render.py video {}
for i in $(seq 0 $((N-1))); do printf "file 'scene_%02d.mp4'\n" "$i"; done > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy video_only.mp4
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset veryfast \
  -crf 21 -maxrate 10M -bufsize 20M -pix_fmt yuv420p -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -ar 48000 \
  -shortest -movflags +faststart final_9x16.mp4
rm -f scene_*.mp4 video_only.mp4 list.txt still_*.jpg
echo "Listo: final_9x16.mp4"
