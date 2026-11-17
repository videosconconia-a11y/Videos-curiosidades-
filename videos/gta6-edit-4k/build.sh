#!/usr/bin/env bash
# 20 s vertical 4K beauty edit (no music; silent AAC track) -> gta6_edit_4k.mp4
set -euo pipefail
cd "$(dirname "$0")"
NW=${NW:-4}
pids=(); for w in $(seq 0 $((NW-1))); do python3 render.py video $w $NW & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
for w in $(seq 0 $((NW-1))); do echo "file 'part_$w.mp4'"; done > parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -f lavfi -i anullsrc=r=48000:cl=stereo -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 14 -profile:v high -level 5.2 -pix_fmt yuv420p -c:a aac -b:a 128k -shortest -movflags +faststart gta6_edit_4k.mp4
rm -f part_*.mp4 parts.txt
echo "Done: gta6_edit_4k.mp4"
