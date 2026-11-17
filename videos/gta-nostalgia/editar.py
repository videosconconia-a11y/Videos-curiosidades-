#!/usr/bin/env python3
"""Monta un edit cinemático de GTA V (estilo "Crecí en estas calles") con TUS clips.

Uso:
    python3 editar.py planos.txt                 # sonido del juego, formato con bandas (como la referencia)
    python3 editar.py planos.txt --silencio      # sin ningún audio
    python3 editar.py planos.txt --vertical      # recorta a pantalla completa 9:16

planos.txt: una línea por plano ->  ruta_clip | inicio_seg | duración_seg | texto opcional
"""
import argparse, subprocess, sys, shlex
from pathlib import Path

W, H = 1080, 1920
FPS = 60
XF = 0.6  # crossfade entre planos (s)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

def leer_planos(path):
    planos = []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        p = [x.strip() for x in ln.split("|")]
        planos.append(dict(clip=p[0], ini=float(p[1]), dur=float(p[2]),
                           texto=p[3] if len(p) > 3 else ""))
    return planos

def tiene_audio(clip):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                        "stream=index", "-of", "csv=p=0", clip], capture_output=True, text=True)
    return bool(r.stdout.strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("planos")
    ap.add_argument("--silencio", action="store_true")
    ap.add_argument("--vertical", action="store_true")
    ap.add_argument("-o", "--out", default="final_9x16.mp4")
    a = ap.parse_args()
    planos = leer_planos(a.planos)
    if not planos:
        sys.exit("planos.txt está vacío")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"]
    for p in planos:
        cmd += ["-ss", str(p["ini"]), "-t", str(p["dur"]), "-i", p["clip"]]

    grade = ("eq=contrast=1.08:saturation=1.12:gamma=0.97,"
             "colorbalance=rs=-0.06:bs=0.08:rh=0.07:bh=-0.05,"
             "vignette=PI/5,noise=alls=5:allf=t")
    f = []
    for i, p in enumerate(planos):
        if a.vertical:
            geo = f"scale=-2:{H}:flags=lanczos,crop={W}:{H}"
        else:  # 16:9 centrado con bandas negras, igual que la referencia
            fh = round(W * 9 / 16 / 2) * 2
            geo = (f"scale={W}:{fh}:flags=lanczos:force_original_aspect_ratio=increase,"
                   f"crop={W}:{fh},pad={W}:{H}:0:(oh-ih)/2:black")
        txt = ""
        if p["texto"]:
            t = " ".join(p["texto"].upper()).replace(":", r"\:").replace("'", "’")
            txt = (f",drawtext=fontfile={FONT}:text='{t}':fontsize=38:fontcolor=white@0.92:"
                   f"x=(w-tw)/2:y=(h-th)/2+40:shadowcolor=black@0.6:shadowx=2:shadowy=2:"
                   f"alpha='if(lt(t,0.6),t/0.6,if(gt(t,{p['dur']-0.8}),max(0,({p['dur']}-t)/0.8),1))'")
        f.append(f"[{i}:v]fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS,{grade},{geo},"
                 f"setsar=1,format=yuv420p{txt}[v{i}]")

    # Encadenar crossfades
    last, off = "v0", planos[0]["dur"]
    for i in range(1, len(planos)):
        off -= XF
        f.append(f"[{last}][v{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]")
        last, off = f"x{i}", off + planos[i]["dur"]
    total = off
    f.append(f"[{last}]fade=t=in:st=0:d=0.5,fade=t=out:st={total-1.2:.3f}:d=1.2[vout]")

    usar_audio = not a.silencio and all(tiene_audio(p["clip"]) for p in planos)
    if usar_audio:
        for i, p in enumerate(planos):
            f.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a{i}]")
        la = "a0"
        for i in range(1, len(planos)):
            f.append(f"[{la}][a{i}]acrossfade=d={XF}[ac{i}]")
            la = f"ac{i}"
        f.append(f"[{la}]afade=t=in:d=0.5,afade=t=out:st={total-1.2:.3f}:d=1.2,loudnorm=I=-16:TP=-1.5[aout]")

    cmd += ["-filter_complex", ";".join(f), "-map", "[vout]"]
    cmd += (["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"] if usar_audio else ["-an"])
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", a.out]
    print(f"{len(planos)} planos, {total:.1f} s, audio: {'juego' if usar_audio else 'ninguno'}")
    subprocess.run(cmd, check=True)
    print("Listo ->", a.out)

if __name__ == "__main__":
    main()
