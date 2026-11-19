#!/usr/bin/env bash
# Builds final_9x16.mp4: original score (no voice) + frames (4 workers) + mux with loudnorm.
set -euo pipefail
cd "$(dirname "$0")"
python3 audio.py
NW=${NW:-4}
pids=(); for w in $(seq 0 $((NW-1))); do python3 render.py video $w $NW & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
for w in $(seq 0 $((NW-1))); do echo "file 'part_$w.mp4'"; done > parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -c copy video_only.mp4
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 18 -maxrate 10M -bufsize 20M -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.0:LRA=9" -ar 48000 -c:a aac -b:a 256k -shortest -movflags +faststart final_9x16.mp4
rm -f part_*.mp4 parts.txt video_only.mp4
echo "Done: final_9x16.mp4"
