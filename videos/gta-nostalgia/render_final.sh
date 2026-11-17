#!/usr/bin/env bash
# Monta el edit final (≤25 s, sin música, sin textos) a partir de las grabaciones de pantalla.
# Uso: ./render_final.sh <carpeta_con_clips> [salida_dir]
set -euo pipefail
U="$1"; OUT="${2:-.}"
C4="$(ls "$U"/b3f3085c*)"   # Vinewood (letrero por detrás) – grabado a 2x
C2="$(ls "$U"/852102bd*)"   # Conducción por carretera – 2x
C1="$(ls "$U"/fabf07a8*)"   # Derrape en el puerto – 1x
C5="$(ls "$U"/f63f2ab1*)"   # Ciudad de noche – 2x
# Recortes: solo la imagen del juego (fuera barras, indicador "2x", marcas de agua y controles)
CROP_A="crop=2264:1120:266:166"        # clips con barras laterales
CROP_B="crop=2260:956:268:168"         # intro con bandas propias
CROP_C="crop=2400:990:80:150"          # derrape (evita logo inferior derecho)
G="scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,setsar=1,eq=contrast=1.05:saturation=1.08,fps=60,format=yuv420p"
XF=0.7
ffmpeg -y -hide_banner -loglevel error -stats \
  -ss 0.5 -to 4.5 -i "$C4" \
  -ss 3.2 -to 6.4 -i "$C2" \
  -ss 4.6 -to 6.4 -i "$C1" \
  -ss 3.8 -to 7.2 -i "$C5" \
  -filter_complex "\
[0:v]$CROP_A,setpts=2*(PTS-STARTPTS),$G[a];\
[1:v]$CROP_B,setpts=2*(PTS-STARTPTS),$G[b];\
[2:v]$CROP_C,setpts=1.7*(PTS-STARTPTS),$G[c];\
[3:v]$CROP_A,setpts=2*(PTS-STARTPTS),$G[d];\
[a][b]xfade=transition=fade:duration=$XF:offset=7.3[ab];\
[ab][c]xfade=transition=smoothleft:duration=$XF:offset=12.98[abc];\
[abc][d]xfade=transition=fade:duration=$XF:offset=15.34[v];\
[v]fade=t=in:d=0.6,fade=t=out:st=20.6:d=1.5[out]" \
  -map "[out]" -an -t 22.1 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart "$OUT/final_16x9.mp4"
# Versión vertical 9:16 con la imagen centrada (como el vídeo de referencia en TikTok)
ffmpeg -y -hide_banner -loglevel error -i "$OUT/final_16x9.mp4" \
  -vf "scale=1080:608:flags=lanczos,pad=1080:1920:0:(oh-ih)/2:black,setsar=1" \
  -an -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart "$OUT/final_9x16.mp4"
