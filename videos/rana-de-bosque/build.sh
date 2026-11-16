#!/usr/bin/env bash
# Genera el vídeo completo: voz -> tiempos -> música/efectos + ducking -> escenas -> final_9x16.mp4
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build
# imágenes con IA (solo genera las que falten en assets/ai/; AI_BACKEND=local|openai)
HF_HUB_DISABLE_XET=1 python3 ai_images.py
python3 voice.py                         # build/voice.wav + build/timing.json (tiempos reales de la voz)
python3 audio.py                         # build/music_sfx.wav + build/mix.wav (voz + música con ducking)
python3 -c "from script_data import write_srt; write_srt('subtitulos.srt')"
ffmpeg -y -loglevel error -i subtitulos.srt web/subtitulos.vtt
N=$(python3 -c "from script_data import SCENES; print(len(SCENES))")
JOBS=${JOBS:-$(nproc)}
# render de escenas en paralelo
seq 0 $((N-1)) | xargs -P "$JOBS" -I{} python3 render.py video {}
for i in $(seq 0 $((N-1))); do printf "file 'scene_%02d.mp4'\n" "$i"; done > build/list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i build/list.txt -c copy build/video_only.mp4
ffmpeg -y -loglevel error -i build/video_only.mp4 -i build/mix.wav -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 19 -profile:v high -level 4.2 -maxrate 7M -bufsize 14M -pix_fmt yuv420p \
  -r 30 -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart final_9x16.mp4
ffmpeg -y -loglevel error -i final_9x16.mp4 -vf scale=720:1280 -c:v libx264 -preset veryfast -crf 26 \
  -maxrate 2.5M -bufsize 5M -c:a aac -b:a 128k -movflags +faststart web/rana.mp4
rm -f build/scene_*.mp4 build/video_only.mp4 build/list.txt build/mix_pre.wav build/voice_raw.wav
echo "Listo: final_9x16.mp4, subtitulos.srt y web/rana.mp4"
