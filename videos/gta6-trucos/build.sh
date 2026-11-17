#!/usr/bin/env bash
# Genera el vídeo completo: voz (Piper) + tiempos por palabra, música/efectos con ducking,
# fotogramas, subtítulos y la unión final.
#   ./build.sh           -> rehace todo
#   SKIP_VOICE=1 ./build.sh -> reutiliza cache/voz.wav y cache/timing.json
set -euo pipefail
cd "$(dirname "$0")"
export HF_HUB_DISABLE_XET=1
if [[ "${SKIP_VOICE:-0}" != "1" || ! -f cache/timing.json ]]; then
  python3 voice.py
fi
python3 audio.py
python3 -c "from script_data import write_srt, write_word_srt; write_srt('subtitulos.srt'); write_word_srt('subtitulos_palabra_a_palabra.srt')"
python3 render.py video
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -preset medium \
  -crf 19 -maxrate 12M -bufsize 24M -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -ar 48000 -shortest \
  -movflags +faststart final_9x16.mp4
rm -f video_only.mp4
echo "Listo: final_9x16.mp4, subtitulos.srt, subtitulos_palabra_a_palabra.srt"
