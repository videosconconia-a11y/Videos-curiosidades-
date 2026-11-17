#!/usr/bin/env python3
"""Ritmo del guion: palabras por segundo de cada escena de script_data.py.

Uso: python3 tools/ritmo.py videos/<tema>
Objetivo (GUIA_ESTILO.md): 3–3,5 palabras/s en español, sin huecos.
"""
import os, re, sys

d = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, d)
import script_data  # noqa: E402

# dos formatos: (inicio, fin, narración, …) o (narración, …) con TIMES calculados de la voz
if hasattr(script_data, "TIMES"):
    ROWS = [(a, b, s[0]) for (a, b, _v), s in zip(script_data.TIMES, script_data.SCENES)]
else:
    ROWS = [(s[0], s[1], s[2]) for s in script_data.SCENES]

tot_w = tot_s = 0
print(f"{'escena':>6} {'seg':>5} {'palabras':>8} {'pal/s':>6}")
for i, (a, b, narr) in enumerate(ROWS):
    w = len(re.findall(r"[\wáéíóúüñÁÉÍÓÚÜÑ%]+", narr))
    tot_w += w; tot_s += b - a
    flag = "  ← lento" if w / (b - a) < 3.0 else ("  ← muy rápido" if w / (b - a) > 4.0 else "")
    print(f"{i:>6} {b - a:>5.1f} {w:>8} {w / (b - a):>6.2f}{flag}")
print(f"{'total':>6} {tot_s:>5.1f} {tot_w:>8} {tot_w / tot_s:>6.2f}")
