#!/usr/bin/env python3
"""Renderiza la escena 3D de un vídeo en tramos reanudables y los une en escena3d.mp4.

Cada tramo (10 s por defecto) se renderiza con su propio navegador y solo se da por bueno cuando termina,
así que si el contenedor se reinicia basta con volver a lanzar el script: continúa donde se quedó.

Uso: python3 tools/render_tramos.py videos/<tema> [--tramo 10] [--procesos 3]
"""
import argparse, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--tramo", type=float, default=10.0)
ap.add_argument("--procesos", type=int, default=3)
a = ap.parse_args()

V = os.path.abspath(a.video); E = os.path.join(V, "escena3d"); T = os.path.join(V, "tramos")
os.makedirs(T, exist_ok=True)
total = json.load(open(os.path.join(E, "timeline.json")))["total"]
FPS = 30
n = int((total * FPS + a.tramo * FPS - 1) // (a.tramo * FPS))
chunks = [(i, i * a.tramo, min(total, (i + 1) * a.tramo)) for i in range(n)]


def render(c):
    i, t0, t1 = c
    out = os.path.join(T, f"tramo_{i:03}.mp4")
    if os.path.exists(out):
        return i, "ya estaba"
    part = out.replace(".mp4", ".part.mp4")
    for intento in range(3):
        r = subprocess.run(["node", "render.cjs", "video", part, f"{t0:.4f}", f"{t1:.4f}"], cwd=E,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        want = round(t1 * FPS) - round(t0 * FPS)
        got = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", part],
                             capture_output=True, text=True).stdout.strip()
        if r.returncode == 0 and got.isdigit() and int(got) == want:
            os.replace(part, out)
            return i, f"ok ({want} cuadros)"
        print(f"tramo {i}: intento {intento + 1} falló ({got} de {want} cuadros) {r.stderr[-300:]}", flush=True)
        time.sleep(3)
    return i, "FALLÓ"


start = time.time()
done = sum(os.path.exists(os.path.join(T, f"tramo_{i:03}.mp4")) for i, _, _ in chunks)
print(f"{n} tramos de {a.tramo:g} s · {done} ya hechos · {a.procesos} procesos", flush=True)
with ThreadPoolExecutor(a.procesos) as ex:
    for i, msg in ex.map(render, chunks):
        print(f"tramo {i + 1}/{n}: {msg} · {(time.time() - start) / 60:.1f} min", flush=True)

missing = [i for i, _, _ in chunks if not os.path.exists(os.path.join(T, f"tramo_{i:03}.mp4"))]
if missing:
    sys.exit(f"faltan tramos: {missing}")
lst = os.path.join(T, "lista.txt")
open(lst, "w").write("".join(f"file 'tramo_{i:03}.mp4'\n" for i, _, _ in chunks))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                os.path.join(V, "escena3d.mp4")], check=True)
print("escena3d.mp4 listo", flush=True)
