# GTA V · «Crecí en estas calles» (edit cinemático, sin música)

Inspirado en el formato del vídeo de referencia: escenas nocturnas y de atardecer de Los Santos,
imagen 16:9 centrada en pantalla vertical con bandas negras, un título con letras espaciadas,
fundido a negro al final. **Diferencias pedidas:** escenas distintas, **menos planos y más largos/continuos**
(con coche) y **sin música** (solo sonido del juego, o silencio con `--silencio`).

## Planos que hay que grabar (Rockstar Editor, 1080p o más, 60 fps)
Cada clip de 6–10 s, cámara lenta y estable, sin HUD (oculta el radar/HUD en el editor).
1. **Amanecer en la autopista** — coche deportivo por la Del Perro Fwy hacia el centro, cámara trasera baja siguiendo el coche; el sol sale entre los rascacielos.
2. **Interior del coche de noche** — cámara en el asiento del copiloto mirando al conductor, luces de la ciudad desenfocadas por la ventanilla (lleva el título «Crecí en estas calles»).
3. **Costa al atardecer** — descapotable por la Great Ocean Hwy junto al mar, cámara lateral en paralelo al coche.
4. **Mirador de noche** — coche aparcado en Vinewood Hills/Mirror Park, cámara detrás del coche mirando a la ciudad iluminada; fundido a negro.

Guarda los clips en `clips/` con esos nombres (o edita `planos.txt`).

## Montaje
```bash
python3 editar.py planos.txt                 # bandas negras como la referencia, sonido del juego
python3 editar.py planos.txt --silencio      # sin audio
python3 editar.py planos.txt --vertical      # pantalla completa 9:16
```
Etalonaje cinematográfico (sombras frías, luces cálidas), viñeta, grano suave, fundidos de 0,6 s entre planos,
H.264 CRF 16 a 60 fps → `final_9x16.mp4`.

## Texto para publicar
- **Título:** Crecí en estas calles 🌆
- **Descripción:** Los Santos de noche nunca pasa de moda. ¿Cuántas horas le echaste a GTA V? 👇
- **Hashtags:** #gta5 #gtav #nostalgia #lossantos #gtaedit #foryoupage #parati
