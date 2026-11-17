#!/usr/bin/env python3
"""Edit final GTA V (v3): apertura de ~7 s con el logo sobre Vinewood y después clips rápidos.
≤25 s, sin música, sin textos añadidos, sin logos de YouTube/TikTok ni marcas de agua.
Uso: python3 render_final.py <carpeta_clips> <salida_dir>"""
import glob, subprocess, sys
U, OUT = sys.argv[1], sys.argv[2]
clip = lambda p: glob.glob(f"{U}/{p}*")[0]
LOGO, MID = clip("acf84400"), clip("c79d5017")
DRV, DRF, NGT = clip("852102bd"), clip("fabf07a8"), clip("f63f2ab1")
# Recortes 2.35:1 que dejan fuera la interfaz de TikTok/YouTube, el 2x y las marcas de agua
CL = "crop=1100:1990:0:300,transpose=2,crop=1990:846:0:130"   # TikTok girado (logo y escenas)
CM = "crop=1090:464:0:1011"                                     # TikTok horizontal "Midnight City"
CA = "crop=2264:962:266:200"
CB = "crop=2264:962:266:164"
CC = "crop=2070:880:300:110"
SHOTS = [  # (clip, inicio, fin, recorte, factor tiempo)
    (LOGO, 0.00, 5.00, CL, 1.4),   # logo GTA V sobre el cartel de Vinewood
    (LOGO, 5.06, 5.60, CL, 2.0),   # palmeras al atardecer
    (MID,  2.56, 3.10, CM, 2.0),   # río con skyline
    (MID,  3.73, 4.24, CM, 2.0),   # playa con palmeras
    (MID,  4.30, 4.80, CM, 2.0),   # lancha
    (LOGO, 7.13, 7.65, CL, 2.2),   # canales
    (MID,  5.46, 5.97, CM, 2.0),   # calle con sol
    (MID,  2.00, 2.50, CM, 2.0),   # lowrider
    (DRV,  3.00, 4.40, CB, 1.0),   # coche blanco
    (DRF,  4.80, 6.40, CC, 1.2),   # derrape
    (MID,  7.13, 7.67, CM, 2.0),   # Michael
    (MID,  4.86, 5.25, CM, 2.2),   # Trevor
    (MID,  6.03, 6.50, CM, 2.2),   # Franklin
    (LOGO, 6.30, 7.07, CL, 1.6),   # skyline con torre eléctrica
    (MID,  6.56, 7.07, CM, 2.0),   # edificios al sol
    (MID,  1.43, 1.94, CM, 2.0),   # piscina de noche
    (MID,  3.16, 3.67, CM, 2.0),   # torres de noche
    (NGT,  4.00, 6.50, CA, 1.2),   # ciudad de noche (final)
]
XF = 0.3
G = ("scale=1920:816:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.7:5:5:0.0,"
     "eq=contrast=1.06:saturation=1.1,setsar=1,fps=60,format=yuv420p")
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
f.append(f"[{last}]fade=t=in:d=0.6,fade=t=out:st={total-1.3:.3f}:d=1.3,split[w][v]")
f.append("[v]scale=1080:460:flags=lanczos,pad=1080:1920:0:(oh-ih)/2:black,setsar=1[vert]")
enc = ["-an", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-profile:v", "high",
       "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", f"{total:.3f}"]
cmd += ["-filter_complex", ";".join(f), "-map", "[w]", *enc, f"{OUT}/final_cine.mp4",
        "-map", "[vert]", *enc, f"{OUT}/final_9x16.mp4"]
print(f"{len(SHOTS)} escenas, {total:.1f} s")
subprocess.run(cmd, check=True)
