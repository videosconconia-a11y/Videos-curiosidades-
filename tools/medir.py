#!/usr/bin/env python3
"""Mide un vídeo cuadro por cuadro en vez de "opinar" sobre él.

Para cada vídeo calcula:
  - movimiento de cámara entre cuadros consecutivos (correlación de fase),
  - % de cuadros con la cámara en movimiento y duración media de cada movimiento,
  - cortes (saltos bruscos de imagen),
  - brillo, contraste y saturación medios.
Opcionalmente genera hojas de contactos (una imagen por cada N segundos).

Uso:
  python3 tools/medir.py video.mp4 [otro.mp4 ...] [--hojas carpeta] [--cada 2]
Compara siempre tu vídeo contra un original de referencia con la misma herramienta.
"""
import argparse, json, os, subprocess, sys
import numpy as np

AW, AH = 270, 480          # resolución de análisis (9:16)
MOVE_PX = 0.04             # desplazamiento/zoom mínimo (px a 270x480) para contar como "cámara moviéndose"
CUT_DIFF = 38.0            # diferencia media de luminancia que cuenta como corte


def frames(path, fps):
    cmd = ["ffmpeg", "-loglevel", "error", "-i", path, "-vf", f"fps={fps},scale={AW}:{AH}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = AW * AH * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(AH, AW, 3)
    p.wait()


def zoom_change(a, b):
    """Cambio de escala aproximado: compara el desplazamiento de las mitades izquierda/derecha y arriba/abajo."""
    h, w = a.shape
    (dyt, _, _), (dyb, _, _) = phase_shift(a[: h // 2], b[: h // 2]), phase_shift(a[h // 2:], b[h // 2:])
    (_, dxl, _), (_, dxr, _) = phase_shift(a[:, : w // 2], b[:, : w // 2]), phase_shift(a[:, w // 2:], b[:, w // 2:])
    return 0.5 * (abs(dyb - dyt) + abs(dxr - dxl))


def phase_shift(a, b):
    """Desplazamiento subpíxel (dy, dx) de b respecto a a por correlación de fase."""
    h, w = a.shape
    win = np.outer(np.hanning(h), np.hanning(w))
    A = np.fft.fft2(a * win); B = np.fft.fft2(b * win)
    R = A * np.conj(B); R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real
    py, px = np.unravel_index(np.argmax(r), r.shape)
    def sub(c, m, n):
        l, c0, rr = c[(m - 1) % n], c[m], c[(m + 1) % n]
        den = l - 2 * c0 + rr
        return m + (0.5 * (l - rr) / den if abs(den) > 1e-12 else 0)
    dy = sub(r[:, px], py, h); dx = sub(r[py, :], px, w)
    if dy > h / 2: dy -= h
    if dx > w / 2: dx -= w
    return dy, dx, r.max()


def analyse(path, fps=30, sheets=None, every=2.0):
    lum_prev = None
    motion, cuts, bright, contrast, sat = [], [], [], [], []
    sheet_buf, sheet_i = [], 0
    per_sheet = max(1, int(round(every * fps)))
    for i, f in enumerate(frames(path, fps)):
        x = f.astype(np.float32)
        lum = x @ np.array([0.299, 0.587, 0.114], np.float32)
        bright.append(float(lum.mean())); contrast.append(float(lum.std()))
        mx, mn = x.max(2), x.min(2)
        sat.append(float(np.mean((mx - mn) / (mx + 1e-3))))
        if lum_prev is not None:
            diff = float(np.abs(lum - lum_prev).mean())
            # un destello cambia el brillo pero conserva la estructura; un corte cambia la estructura
            ncc = float(np.corrcoef(lum_prev.ravel(), lum.ravel())[0, 1]) if lum.std() > 1 and lum_prev.std() > 1 else 1.0  # fundido desde/hacia negro: no es corte
            if diff > CUT_DIFF and ncc < 0.6:
                cuts.append(i / fps); motion.append(None)
            else:
                dy, dx, _ = phase_shift(lum_prev, lum)
                z = zoom_change(lum_prev, lum)
                motion.append(float(np.hypot(dx, dy) + z))
        lum_prev = lum
        if sheets:
            sheet_buf.append(f)
            if len(sheet_buf) == per_sheet:
                save_sheet(sheet_buf, os.path.join(sheets, f"{os.path.splitext(os.path.basename(path))[0]}_{sheet_i:03}.jpg"))
                sheet_buf, sheet_i = [], sheet_i + 1
    if sheets and sheet_buf:
        save_sheet(sheet_buf, os.path.join(sheets, f"{os.path.splitext(os.path.basename(path))[0]}_{sheet_i:03}.jpg"))
    m = [v for v in motion if v is not None]
    moving = [v >= MOVE_PX for v in m]
    runs, cur = [], 0
    for mv in moving:
        if mv: cur += 1
        elif cur: runs.append(cur); cur = 0
    if cur: runs.append(cur)
    # tramos quietos (inicio, fin) en segundos, para saber qué plano arreglar
    still, k, idx = [], 0, [i + 1 for i, v in enumerate(motion) if v is not None]
    flags = [v >= MOVE_PX for v in m]
    while k < len(flags):
        if not flags[k]:
            j = k
            while j + 1 < len(flags) and not flags[j + 1]: j += 1
            still.append((round(idx[k] / fps, 2), round((idx[j] + 1) / fps, 2))); k = j + 1
        else: k += 1
    n = len(bright)
    return {
        "video": os.path.basename(path), "segundos": round(n / fps, 2), "cuadros": n,
        "camara_moviendose_pct": round(100 * np.mean(moving), 1) if moving else 0.0,
        "movimiento_medio_s": round(float(np.mean(runs)) / fps, 2) if runs else 0.0,
        "tramos_quietos": int(sum(1 for k in range(1, len(moving)) if not moving[k] and moving[k - 1]) + (0 if not moving or moving[0] else 1)),
        "velocidad_media_px": round(float(np.mean(m)), 3) if m else 0.0,
        "quietos_s": still,
        "cortes": len(cuts), "cortes_s": [round(c, 2) for c in cuts],
        "brillo": round(float(np.mean(bright)), 1),
        "contraste": round(float(np.mean(contrast)), 1),
        "saturacion": round(float(np.mean(sat)), 3),
    }


def save_sheet(buf, out):
    from PIL import Image
    cols = 10; rows = (len(buf) + cols - 1) // cols
    tw, th = AW // 2, AH // 2
    sheet = Image.new("RGB", (cols * tw, rows * th))
    for k, f in enumerate(buf):
        sheet.paste(Image.fromarray(f).resize((tw, th)), ((k % cols) * tw, (k // cols) * th))
    sheet.save(out, quality=80)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--hojas", help="carpeta donde guardar hojas de contactos")
    ap.add_argument("--cada", type=float, default=2.0, help="segundos por hoja de contactos")
    ap.add_argument("--json", help="guardar resultados en este archivo")
    a = ap.parse_args()
    if a.hojas: os.makedirs(a.hojas, exist_ok=True)
    res = [analyse(v, a.fps, a.hojas, a.cada) for v in a.videos]
    keys = ["camara_moviendose_pct", "movimiento_medio_s", "tramos_quietos", "velocidad_media_px", "cortes", "brillo", "contraste", "saturacion"]
    w = max(len(r["video"]) for r in res) + 2
    print("métrica".ljust(24) + "".join(r["video"][:w].rjust(w) for r in res))
    for k in keys:
        print(k.ljust(24) + "".join(str(r[k]).rjust(w) for r in res))
    if a.json:
        json.dump(res, open(a.json, "w"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    sys.exit(main())
