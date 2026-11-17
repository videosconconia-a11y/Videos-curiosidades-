#!/usr/bin/env bash
# Renders the 70 s GTA VI highlights montage (no music; silent AAC track) -> gta6_highlights_9x16.mp4
set -euo pipefail
cd "$(dirname "$0")"
NW=${NW:-4}
pids=(); for w in $(seq 0 $((NW-1))); do python3 render.py video $w $NW & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
for w in $(seq 0 $((NW-1))); do echo "file 'part_$w.mp4'"; done > parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -f lavfi -i anullsrc=r=48000:cl=stereo \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 18 -maxrate 14M -bufsize 28M -pix_fmt yuv420p \
  -c:a aac -b:a 128k -shortest -movflags +faststart gta6_highlights_9x16.mp4
rm -f part_*.mp4 parts.txt
echo "Done: gta6_highlights_9x16.mp4"
