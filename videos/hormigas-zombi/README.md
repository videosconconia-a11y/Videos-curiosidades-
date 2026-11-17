# El hongo que convierte hormigas en zombis

Vídeo vertical 9:16 (~1:22) para TikTok / Reels / Shorts. Voz en castellano de España, imágenes generadas
con IA que siguen lo que se narra, subtítulos palabra a palabra y música suave de fondo con *ducking*.

## Archivos

| Archivo | Qué es |
|---|---|
| `final_9x16.mp4` | Vídeo final 1080×1920, 30 fps (no se sube al repo por tamaño; se genera con `./build.sh`) |
| `subtitulos_hormigas_zombi.srt` | Subtítulos sincronizados con la voz |
| `PUBLICAR.md` | Título, descripción y hashtags |
| `script_data.py` | Guion (narración por escena) y prompts de las imágenes |
| `gen_voice.py` | Voz `es-ES-AlvaroNeural` (masculina, tono medio, España) + tiempos de cada palabra |
| `gen_images_local.py` | Imágenes IA con SDXL-Turbo en local (CPU); las elegidas están en `assets/img` |
| `stalk_img2img.py` | Planos del tallo del hongo: esbozo pintado + img2img para hacerlo realista |
| `timeline.py` | Calcula escenas, cortes de imagen y bloques de subtítulos a partir de la voz real |
| `audio.py` | Música sintetizada (pad + arpegio suave + latido) y mezcla con *ducking* |
| `render.py` | Montaje: movimiento de cámara, fundidos y subtítulos |
| `build.sh` | Lo genera todo |

## Fuentes (datos verificados)

- **Ophiocordyceps unilateralis s.l. y hormigas carpinteras (*Camponotus*)**: el hongo manipula el comportamiento;
  las hormigas mueren mordiendo el nervio del envés de una hoja a ~25 cm del suelo, con la mordida sincronizada
  hacia el mediodía solar, y sufren convulsiones que las hacen caer. Hughes et al. (2011), *BMC Ecology* 11:13.
  https://bmcecol.biomedcentral.com/articles/10.1186/1472-6785-11-13 · https://pmc.ncbi.nlm.nih.gov/articles/PMC3118224
- **El hongo no invade el cerebro**: las células del hongo invaden y rodean las fibras musculares formando redes,
  pero el cerebro queda intacto. Fredericksen et al. (2017), *PNAS* 114(47):12590–12595.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5703306 ·
  https://www.nationalgeographic.com/animals/article/controlling-zombie-ants-fungus-spd
- **Fósil de 48 millones de años**: hoja de Messel (Alemania) con las cicatrices de la "mordida de la muerte".
  Hughes, Wappler & Labandeira (2010), *Biology Letters*, doi:10.1098/rsbl.2010.0521.
  https://www.sciencedaily.com/releases/2010/08/100818105730.htm
- **No infecta a humanos**: *Ophiocordyceps unilateralis* es específico de hormigas; no se conocen infecciones en
  personas (la temperatura corporal de los mamíferos es una barrera para la mayoría de hongos).

Matices: lo del tallo "de la cabeza" es la descripción habitual (sale de la parte posterior de la cabeza / cuello).
El mecanismo químico exacto de la manipulación aún se investiga; el vídeo dice solo lo demostrado.

## Notas técnicas

- La cuenta de OpenAI conectada no tenía saldo, así que la voz se hizo con Microsoft Edge TTS
  (`es-ES-AlvaroNeural`) y las imágenes con SDXL-Turbo en local. Con saldo en OpenAI se podrían usar
  `gpt-image` y `gpt-4o-mini-tts` para imágenes más detalladas.
- Música 100 % sintetizada en `audio.py` (sin derechos de autor).
