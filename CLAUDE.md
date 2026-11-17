# Instrucciones para Claude

Este repositorio genera vídeos cortos de curiosidades en español de España (9:16, 45–60 s).

## Al crear un vídeo nuevo
1. Copia `videos/rana-de-bosque` a `videos/<tema>` y reescribe `script_data.py`.
2. Estructura obligatoria: gancho impactante en los 3 primeros segundos (sin saludos), desarrollo con datos
   reales y verificados, cambio visual cada 3–5 s, final con dato sorprendente o pregunta para comentar.
   Sigue `GUIA_ESTILO.md` (paradoja en la primera frase, giro con muletilla fija, cámara siempre en
   movimiento, imagen oscura y con contraste) y comprueba el ritmo con `python3 tools/ritmo.py videos/<tema>`.
3. Verifica cada dato científico en fuentes fiables antes de usarlo y anota las fuentes en el README del vídeo.
   Si el tema pedido contiene un dato falso, corrígelo y avisa.
4. Adapta los planos de `render.py` al tema y comprueba algunos fotogramas antes del render completo.
5. Si hay acceso a red, intenta añadir voz de IA en español (p. ej. Piper TTS con una voz es_ES) y mézclala
   con la música bajando la música mientras habla la voz (ducking).
6. Ejecuta `./build.sh` (al final mide el vídeo con `tools/medir.py`; ajusta hasta cumplir los objetivos de
   `GUIA_ESTILO.md`) y entrega `final_9x16.mp4`, los subtítulos y el texto para publicar (título, descripción, hashtags).
