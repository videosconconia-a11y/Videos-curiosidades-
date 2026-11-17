#!/usr/bin/env bash
# 20 s GTA VI edit (no music; silent AAC). Outputs:
#   gta6_edit_4K.mp4      2160x3840, ~16 Mb/s  (< 50 MB, easy to download)
#   gta6_edit_1080p.mp4   1080x1920, ~10 Mb/s  (backup, very light)
set -euo pipefail
cd "$(dirname "$0")"
NW=${NW:-4}
pids=(); for w in $(seq 0 $((NW-1))); do python3 render.py video $w $NW & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
for w in $(seq 0 $((NW-1))); do echo "file 'part_$w.mp4'"; done > parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -c copy master.mp4
for pass in 1 2; do
  ffmpeg -y -loglevel error -i master.mp4 -c:v libx264 -preset slow -b:v 16M -maxrate 24M -bufsize 32M -profile:v high -level 5.2 \
    -pix_fmt yuv420p -tune film -pass $pass -passlogfile x264_4k -an -f mp4 $( [ $pass = 1 ] && echo /dev/null || echo v4k.mp4 )
done
ffmpeg -y -loglevel error -i v4k.mp4 -f lavfi -i anullsrc=r=48000:cl=stereo -map 0:v -map 1:a -c:v copy -c:a aac -b:a 96k -shortest -movflags +faststart gta6_edit_4K.mp4
ffmpeg -y -loglevel error -i master.mp4 -f lavfi -i anullsrc=r=48000:cl=stereo -map 0:v -map 1:a -vf scale=1080:1920:flags=lanczos \
  -c:v libx264 -preset slow -crf 17 -maxrate 10M -bufsize 20M -pix_fmt yuv420p -c:a aac -b:a 96k -shortest -movflags +faststart gta6_edit_1080p.mp4
rm -f part_*.mp4 parts.txt v4k.mp4 x264_4k*
echo "Done"
