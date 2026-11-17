# GTA 6: "haz esto YA" — vídeo 9:16 de 28 s (TikTok / YouTube Shorts)

Entregables (tras `./build.sh`):
- `final_9x16.mp4` — 1080×1920, 30 fps, 28,0 s, H.264 + AAC, sonoridad −14 LUFS.
- `subtitulos.srt` — bloques de 1–3 palabras, exactamente lo que dice la voz.
- `subtitulos_palabra_a_palabra.srt` — una palabra por línea con su tiempo (para CapCut, etc.).

## ⚠️ Avisos antes de publicar

1. **GTA 6 aún no ha salido.** Rockstar lo lanza el **19 de noviembre de 2026** (PS5 y Xbox Series X|S).
   La frase "Ha salido hace nada" solo es cierta si publicas el vídeo a partir de ese día.
2. **Los trucos no existen todavía.** El guion original tenía huecos (`[TRUCO DE DINERO]`, `[TRUCO DEL COCHE]`).
   No me he inventado trucos falsos. Ahora mismo la voz dice:
   - "El primero: **dinero a lo bestia, te lo dejo paso a paso en pantalla**."
   - "Y este es una locura: **un coche de lujo gratis, sin pagar ni un dólar**."

   Cuando haya trucos reales y comprobados, cambia `TRUCO_DINERO` y `TRUCO_COCHE` en `script_data.py`
   y ejecuta `./build.sh`: la voz, los subtítulos palabra a palabra, los cortes y los "cha-ching" se recalculan.
   Publicar un vídeo que promete trucos que no enseña es clickbait engañoso: TikTok y YouTube lo penalizan
   (y la audiencia también).
3. **Imágenes:** no son capturas ni imágenes oficiales de GTA 6. Son ilustraciones neón generadas por código
   (skyline tipo Miami, palmeras, playa al atardecer, deportivo, billetes), sin logos de Rockstar ni del juego.
   La API de imágenes de OpenAI estaba sin crédito; si quieres imágenes de IA o gameplay propio, sustituye
   los planos en `render.py` (`SHOT_FUNCS`).
4. **Voz:** Piper TTS, voz masculina `es_ES-davefx-medium` (español de España). Es natural para un TTS local,
   pero no llega al nivel de ElevenLabs. Para una voz más humana, genera el audio fuera con el texto de
   la columna `tts` de `script_data.py`, guárdalo como `cache/voz.wav` y, si quieres, adapta `voice.py`
   para que solo calcule los tiempos con Whisper.

## Guion final (lo que dice la voz y lo que se ve)

| Tiempo | Voz | Imagen |
|---|---|---|
| 0,0–3,5 s | Si tienes GTA 6, haz esto **YA**, antes de que Rockstar lo **PARCHEE**. | Brillo rojo pulsante, cuenta atrás, "⚠️ LO VAN A QUITAR" |
| 3,5–7,3 s | Ha salido hace nada y **YA** hay trucos que no van a durar ni una semana. | Skyline neón de noche con coches a toda velocidad, avenida con faros, paseo de palmeras |
| 7,3–13,2 s | El primero: **DINERO** a lo bestia, te lo dejo paso a paso en pantalla. Hazlo ahora, que esto vuela. | "TRUCO 1: DINERO INFINITO", personaje con maletines de billetes, lluvia de billetes, contador subiendo |
| 13,2–19,9 s | Y este es una locura: un coche de lujo **GRATIS**, sin pagar ni un dólar. Me hice con un deportivo en dos minutos. | "TRUCO 2: COCHE GRATIS", deportivo girando en plataforma con destellos, conduciendo por la costa al atardecer |
| 19,9–23,0 s | Rockstar ya está avisada, así que no lo dejes para mañana. | "SOLO POR TIEMPO LIMITADO" parpadeando, cuenta atrás, reloj de arena sobre la ciudad |
| 23,0–28,0 s | Sígueme, que mañana subo uno todavía más bestia… y si tienes GTA 6, haz esto **YA**. | "SÍGUEME PARA MÁS 🔥" sobre panorámica, y vuelta a la alarma roja para enlazar con el inicio (bucle) |

Ritmo: 21 planos en 28 s (corte cada ~1,3 s), zoom brusco y destello en cada corte, mini-zoom en cada palabra clave.
Subtítulos: Anton, blancos con borde negro, centrados en la mitad inferior. DINERO, GRATIS, YA y PARCHEE van
en amarillo y un 28 % más grandes. Cada palabra aparece justo cuando se dice (tiempos medidos con Whisper).
Audio: base phonk a 130 BPM (808 con glide, cencerro, palmas, hats en tresillo), "whoosh" en cada corte,
"cha-ching" en DINERO, GRATIS, dólar y el contador, y ducking de ~11 dB bajo la voz.

## Texto para publicar

**Título (YouTube Shorts):** Haz esto YA en GTA 6 antes de que lo parcheen 😳💸

**Descripción / texto de TikTok:**
Estos trucos de GTA 6 no van a durar ni una semana… Rockstar ya está avisada 👀
¿Cuál pruebas primero, el del DINERO o el del coche GRATIS? Te leo en comentarios 👇
Sígueme, que mañana subo uno todavía más bestia 🔥

**Hashtags:** #GTA6 #GTAVI #ViceCity #GTA6Trucos #Leonida #Gaming #Videojuegos #TrucosGTA #Rockstar #GamingEspaña #fyp #parati

(Ajusta el texto a los trucos reales antes de publicar.)

## Fuentes

- Fecha de lanzamiento, 19/11/2026 (retrasado desde el 26/05/2026): Rockstar Newswire —
  https://www.rockstargames.com/newswire/article/ak3ak31a49a221/grand-theft-auto-vi-is-now-set-to-launch-november-19-2026
- Plataformas (PS5, Xbox Series X|S): https://www.xbox.com/en-US/games/grand-theft-auto-vi ·
  https://www.forbes.com/sites/brianmazique/2026/05/12/grand-theft-auto-6-release-date-and-everything-confirmed/
- Ambientación (Vice City, estado de Leonida): https://www.tomsguide.com/us/grand-theft-auto-6-release-date-rumors,news-25578.html

## Generación

```bash
pip install numpy pillow scipy piper-tts faster-whisper
./build.sh                 # rehace voz + tiempos + audio + vídeo
SKIP_VOICE=1 ./build.sh    # reutiliza la voz ya generada
python3 render.py frame 1.5 9 16   # fotogramas sueltos en previews/
```

La primera vez descarga la voz de Piper (~60 MB) y el modelo Whisper "small" desde Hugging Face.
La fuente Anton (SIL Open Font License) está en `fonts/`.
