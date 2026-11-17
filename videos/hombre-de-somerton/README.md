# El hombre de Somerton (1948) — misterio real sin resolver

Vídeo vertical 9:16 de ~75 s con voz en off masculina en español de España, música de misterio, efectos y subtítulos.
Misma estructura que `videos/paso-dyatlov` (ver su README): `script_data.py`, `tts.py`, `audio.py`, `render.py`, `build.sh`.

## Usar otra voz (p. ej. la de CapCut/ElevenLabs de tus otros vídeos)
Genera cada frase de `script_data.py` (lista `RAW`, en orden) con tu herramienta, guárdalas como
`voz/escena_00.wav` … `voz/escena_09.wav` y ejecuta:
```bash
python3 tts.py --solo-medir   # mide las duraciones nuevas y reajusta los tiempos
./build.sh
```
