#!/usr/bin/env bash
# Builds final_16x9.mp4 (1920x1080, 24 fps): Kokoro voice-over -> original score + ducking -> frames (4 workers) -> mux.
set -euo pipefail
cd "$(dirname "$0")"
export HF_HUB_DISABLE_XET=1
[ -f voice.wav ] && [ -f timings.json ] || VOICE=am_michael python3 voice.py
python3 audio.py
python3 subs.py
NW=${NW:-4}
pids=(); for w in $(seq 0 $((NW-1))); do python3 render.py video $w $NW & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
for w in $(seq 0 $((NW-1))); do echo "file 'part_$w.mp4'"; done > parts.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -c copy video_only.mp4
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 21 -maxrate 3M -bufsize 6M -tune film -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.0:LRA=11" -ar 48000 -c:a aac -b:a 192k -shortest -movflags +faststart final_16x9.mp4
rm -f part_*.mp4 parts.txt video_only.mp4
echo "Done: final_16x9.mp4"
