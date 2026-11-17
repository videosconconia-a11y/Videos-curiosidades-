#!/usr/bin/env python3
"""Short de trucos (formato «si te pasa X, marca este número») con voz Piper es_ES.
Uso: python3 hacer_video.py <carpeta_clips> <carpeta_voces_piper> <salida_dir>
Para GTA 6: cambia SEGMENTOS (texto, rótulo, código y clips) por los trucos reales verificados."""
import glob, json, subprocess, sys, wave
U, VOC, OUT = sys.argv[1:4]
clip = lambda p: glob.glob(f"{U}/{p}*")[0]
LOGO, MID, DRF, DRN, NGT = (clip(x) for x in ("acf84400", "c79d5017", "fabf07a8", "3e73524f", "f63f2ab1"))
CL = "crop=1100:1990:0:300,transpose=2,crop=1990:846:0:130"
CM = "crop=1090:464:0:1011"
CA = "crop=2264:962:266:200"
CC = "crop=2070:880:300:110"
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
# (voz, rótulo, código, clips[(archivo, inicio, fin, recorte)])
SEGMENTOS = [
    ("Si todavía juegas a GTA 5, prueba estos trucos antes de que salga GTA 6... porque el último es una locura.",
     "TRUCOS DE GTA 5", "ANTES DE GTA 6",
     [(DRF, 4.8, 6.4, CC), (MID, 4.30, 4.80, CM), (MID, 2.00, 2.50, CM)]),
    ("Si la policía te está friendo a tiros y te queda poca vida, marca este número en el móvil. Vida y blindaje al máximo, al instante.",
     "VIDA Y BLINDAJE AL MÁXIMO", "1-999-887-853",
     [(MID, 4.86, 5.25, CM), (MID, 6.03, 6.50, CM), (DRF, 3.0, 4.4, CC)]),
    ("Y si quieres que no te toquen ni las balas, este otro te hace invencible durante cinco minutos.",
     "INVENCIBLE 5 MINUTOS", "1-999-724-654-5537",
     [(DRF, 1.1, 1.7, CC), (MID, 7.13, 7.67, CM)]),
    ("¿Te aburres de ir en coche? Llama a este número y te aparece un helicóptero de ataque al lado.",
     "HELICÓPTERO DE ATAQUE", "1-999-2899-633",
     [(LOGO, 6.30, 7.07, CL), (MID, 6.56, 7.07, CM), (MID, 2.56, 3.10, CM)]),
    ("Y el último. Marca este número... y caes desde el cielo, en mitad de Los Santos.",
     "CAES DESDE EL CIELO", "1-999-759-3255",
     [(DRN, 2.6, 4.6, CA), (MID, 3.16, 3.67, CM)]),
    ("Ojo, solo funcionan en el modo historia. ¿Cuál vas a probar primero? Te leo en comentarios.",
     "¿CUÁL PRUEBAS PRIMERO?", "",
     [(NGT, 4.0, 6.5, CA)]),
]
NOMBRE, BORRADOR = "final_9x16", False
if len(sys.argv) > 4:  # guion alternativo: define SEGMENTOS, NOMBRE y BORRADOR
    exec(open(sys.argv[4], encoding="utf-8").read())
PAUSA = 0.25
# 1) Voz por segmento
durs, wavs = [], []
for i, (txt, *_r) in enumerate(SEGMENTOS):
    w = f"{OUT}/voz_{i}.wav"
    subprocess.run([sys.executable, "-m", "piper", "-m", f"{VOC}/es_ES-davefx-medium.onnx",
                    "--length-scale", "0.92", "-f", w], input=txt.encode(), check=True,
                   capture_output=True)
    with wave.open(w) as ww:
        durs.append(ww.getnframes() / ww.getframerate() + PAUSA)
    wavs.append(w)
total = sum(durs)
# 2) Vídeo: cada segmento reparte su duración entre sus clips (cortes rápidos)
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"]
f, n, labels = [], 0, []
G = ("scale=1920:816:flags=lanczos,hqdn3d=1.5:1.5:3:3,unsharp=5:5:0.7:5:5:0.0,"
     "eq=contrast=1.06:saturation=1.1,setsar=1,fps=60,format=yuv420p")
for si, (_t, _r, _c, clips) in enumerate(SEGMENTOS):
    slot = durs[si] / len(clips)
    for (c, a, b, cr) in clips:
        k = slot / (b - a)
        cmd += ["-ss", str(a), "-to", str(b), "-i", c]
        f.append(f"[{n}:v]{cr},setpts={k:.4f}*(PTS-STARTPTS),{G},trim=duration={slot:.4f}[c{n}]")
        labels.append(f"[c{n}]"); n += 1
f.append("".join(labels) + f"concat=n={n}:v=1:a=0[cine]")
# 3) Composición vertical + rótulos grandes
t0, txt = 0.0, []
esc = lambda s: s.replace("\\", "\\\\").replace(":", r"\:").replace("'", "’")
for si, (_t, rot, cod, _c) in enumerate(SEGMENTOS):
    t1 = t0 + durs[si]
    en = f"enable='between(t,{t0:.3f},{t1:.3f})'"
    pop = f"fontsize='if(lt(t-{t0:.3f},0.15),{{s}}*(0.7+2*(t-{t0:.3f})),{{s}})'"
    txt.append(f"drawtext=fontfile={F}:text='{esc(rot)}':fontcolor=#FFD400:borderw=6:bordercolor=black:"
               f"fontsize={min(64, int(1550/max(1,len(rot))))}:x=(w-tw)/2:y=330:{en}")
    if cod:
        txt.append(f"drawtext=fontfile={F}:text='{esc(cod)}':fontcolor=white:borderw=8:bordercolor=black:"
                   f"fontsize={min(88, int(1550/max(1,len(cod))))}:x=(w-tw)/2:y=420:{en}")
    t0 = t1
f.append("[cine]split[a][b];[a]scale=-2:1920:flags=bicubic,crop=1080:1920,boxblur=30:3,"
         "eq=brightness=-0.15:saturation=1.1[bg];[b]scale=-2:680:flags=lanczos,crop=1080:680,"
         "unsharp=5:5:0.4[fg];[bg][fg]overlay=0:(H-h)/2," + ",".join(txt) +
         (f",drawtext=fontfile={F}:text='BORRADOR':fontcolor=white@0.55:fontsize=34:x=w-tw-30:y=h-80"
            if BORRADOR else "") +
         f",fade=t=out:st={total-0.6:.3f}:d=0.6,setsar=1,format=yuv420p[v]")
# 4) Audio de voz (con pausas) y masterizado
for i, w in enumerate(wavs):
    cmd += ["-i", w]
    f.append(f"[{n+i}:a]aresample=48000,apad=pad_dur={PAUSA}[a{i}]")
f.append("".join(f"[a{i}]" for i in range(len(wavs))) + f"concat=n={len(wavs)}:v=0:a=1,"
         "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,"
         "equalizer=f=3500:t=q:w=1:g=2,loudnorm=I=-14:TP=-1[aout]")
cmd += ["-filter_complex", ";".join(f), "-map", "[v]", "-map", "[aout]", "-c:v", "libx264",
        "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-t", f"{total:.3f}", f"{OUT}/{NOMBRE}.mp4"]
print(f"{len(SEGMENTOS)} segmentos, {total:.1f} s")
subprocess.run(cmd, check=True)
# 5) Subtítulos .srt
def ts(x):
    h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
    return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")
t0, out = 0.0, []
for i, (txt_, *_r) in enumerate(SEGMENTOS):
    out.append(f"{i+1}\n{ts(t0)} --> {ts(t0+durs[i]-PAUSA)}\n{txt_}\n")
    t0 += durs[i]
open(f"{OUT}/{NOMBRE}.srt", "w").write("\n".join(out))
