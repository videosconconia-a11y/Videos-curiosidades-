#!/usr/bin/env bash
# Genera el vídeo completo: voz, (imágenes), música+ducking, montaje, subtítulos.
# Requisitos: ffmpeg, python3 con numpy pillow scipy edge-tts (y torch+diffusers para las imágenes locales).
set -euo pipefail
cd "$(dirname "$0")"
python3 gen_voice.py                       # voz es-ES + tiempos por palabra (cacheado en assets/voice)
N_IMG=$(python3 -c "from script_data import SCENES; print(sum(len(s['images']) for s in SCENES))")
if [ "$(ls assets/img/*.png 2>/dev/null | grep -v -E '_[ab]\.png$' | wc -l)" -lt "$N_IMG" ]; then
  HF_HUB_DISABLE_XET=1 IMG_W=640 IMG_H=1024 python3 gen_images_local.py   # imágenes IA que falten
fi
python3 audio.py                           # música suave + voz con ducking -> mix.wav
python3 -c "from timeline import write_srt; write_srt('subtitulos_venus.srt')"
python3 render.py video                    # -> video_only.mp4
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 21 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -c:a aac -b:a 192k \
  -shortest -movflags +faststart final_9x16.mp4
rm -f video_only.mp4 mix.wav
echo "Listo: final_9x16.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 final_9x16.mp4) s)"
