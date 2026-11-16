#!/usr/bin/env bash
# Genera el vídeo completo: imágenes IA (si faltan), voz IA, música+efectos, montaje y mezcla final.
# Requisitos: pip install torch diffusers transformers accelerate piper-tts faster-whisper scipy pillow numpy
set -euo pipefail
cd "$(dirname "$0")"
[ "${SKIP_IMAGES:-0}" = 1 ] || python3 images.py                 # RealVisXL Lightning (CPU ~70 s/imagen)
[ -f voice/timings.json ] && [ "${REDO_VOICE:-0}" = 0 ] || python3 voice.py   # Piper es_ES + Whisper
python3 audio.py
python3 -c "from script_data import write_srt; write_srt('subtitulos.srt')"
N=${PARTS:-4}
for k in $(seq 0 $((N-1))); do python3 render.py video "$N" "$k" & done; wait
for k in $(seq 0 $((N-1))); do printf "file 'part_%02d.mp4'\n" "$k"; done > list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy video_only.mp4
ffmpeg -y -loglevel error -i mix_raw.wav -af "loudnorm=I=-14:TP=-1.0:LRA=9" -ar 48000 mix.wav
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 18 \
  -maxrate 14M -bufsize 28M -pix_fmt yuv420p -profile:v high -level 4.2 -r 30 \
  -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart final_9x16.mp4
rm -f part_*.mp4 video_only.mp4 list.txt mix_raw.wav music_only.wav
echo "Listo: final_9x16.mp4 + subtitulos.srt"
