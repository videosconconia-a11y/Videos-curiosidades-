#!/usr/bin/env bash
# Genera el Short completo: voz (Edge TTS), mezcla con música/efectos, fotogramas y MP4 final.
set -euo pipefail
cd "$(dirname "$0")"
[ -f voz/timings.json ] || python3 tts.py
python3 audio.py
python3 -c "from script_data import write_srt; write_srt('subtitulos_gta6_dinero.srt')"
python3 render.py video
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset medium -crf 20 \
  -maxrate 12M -bufsize 24M -pix_fmt yuv420p -r 30 -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 \
  -shortest -movflags +faststart final_9x16.mp4
rm -f video_only.mp4
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 final_9x16.mp4
echo "Listo: final_9x16.mp4"
