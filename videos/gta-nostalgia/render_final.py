#!/usr/bin/env python3
"""Edit final GTA V: 10 escenas cortas, ≤25 s, sin música, sin textos ni logos.
Uso: python3 render_final.py <carpeta_clips> <salida_dir>"""
import glob, subprocess, sys
U, OUT = sys.argv[1], sys.argv[2]
clip = lambda p: glob.glob(f"{U}/{p}*")[0]
VW, DRV, DRF, DRN, NGT = (clip(x) for x in ("b3f3085c", "852102bd", "fabf07a8", "3e73524f", "f63f2ab1"))
# Recortes 2.35:1 que dejan fuera barras, indicador 2x, marcas de agua y controles de YouTube
CA = "crop=2264:962:266:200"     # clips con barras laterales
CB = "crop=2264:962:266:164"     # intro con bandas
CC = "crop=2070:880:300:110"     # cinemática del puerto (fuera logo y barra)
CD = "crop=1718:730:551:150"     # dron skyline (fuera reloj y botones)
# (clip, inicio, fin, recorte, factor de tiempo: <1 acelera, >1 ralentiza)
SHOTS = [
    (VW,  0.5, 3.5, CA, 1.0),   # Vinewood por detrás
    (DRV, 0.0, 1.5, CB, 2.0),   # skyline al atardecer
    (DRV, 3.0, 4.4, CB, 2.0),   # coche blanco en carretera
    (DRF, 1.1, 1.7, CC, 2.5),   # salto a cámara lenta
    (DRF, 3.0, 4.4, CC, 1.5),   # derrape en el STOP
    (DRN, 2.6, 4.6, CA, 1.5),   # dron sobre la piscina
    (DRV, 5.0, 6.4, CB, 2.0),   # carretera del pueblo
    (DRF, 4.8, 6.4, CC, 1.7),   # derrape lateral
    (DRN, 10.0, 11.3, CD, 2.0), # skyline con torre eléctrica
    (NGT, 4.0, 6.0, CA, 1.5),   # ciudad de noche
]
XF = 0.4
G = ("scale=1920:816:flags=lanczos,setsar=1,eq=contrast=1.05:saturation=1.08,"
     "fps=60,format=yuv420p")
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"]
f, durs = [], []
for i, (c, a, b, cr, k) in enumerate(SHOTS):
    cmd += ["-ss", str(a), "-to", str(b), "-i", c]
    f.append(f"[{i}:v]{cr},setpts={k}*(PTS-STARTPTS),{G}[s{i}]")
    durs.append((b - a) * k)
last, off = "s0", durs[0]
for i in range(1, len(SHOTS)):
    off -= XF
    f.append(f"[{last}][s{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]")
    last, off = f"x{i}", off + durs[i]
total = off
f.append(f"[{last}]fade=t=in:d=0.5,fade=t=out:st={total-1.3:.3f}:d=1.3,split[w][v]")
f.append("[v]scale=1080:460:flags=lanczos,pad=1080:1920:0:(oh-ih)/2:black,setsar=1[vert]")
enc = ["-an", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
       "-movflags", "+faststart", "-t", f"{total:.3f}"]
cmd += ["-filter_complex", ";".join(f), "-map", "[w]", *enc, f"{OUT}/final_cine.mp4",
        "-map", "[vert]", *enc, f"{OUT}/final_9x16.mp4"]
print(f"{len(SHOTS)} escenas, {total:.1f} s")
subprocess.run(cmd, check=True)
