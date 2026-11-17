# Tu perro huele tus emociones

Vídeo vertical 9:16 · **78,8 s** · voz de IA en español de España (Piper TTS, `es_ES-davefx-medium`) con música
sintetizada que baja mientras habla la voz (ducking) · volumen normalizado a −14 LUFS.

```bash
pip install numpy pillow scipy piper-tts
# modelo de voz: es_ES-davefx-medium.onnx (+ .onnx.json) de huggingface.co/rhasspy/piper-voices → /opt/piper/
./build.sh                 # REVOICE=1 ./build.sh para regenerar la voz
```

Los tiempos de cada escena salen de la duración real de cada frase de la voz (`voice/durations.json`): la narración
nunca se acelera y cada frase deja su pausa natural (0,34 s entre frases, 0,6 s entre escenas, pausas dramáticas más largas).

## Guion

| Tiempo | Narración | Plano |
|---|---|---|
| 0:00 | Tu perro sabe cuándo tienes miedo. Y no lo adivina. Lo huele. | Trufa en macro, partículas de olor |
| 0:04 | Cuando sientes estrés, tu cuerpo cambia por dentro. Tu sudor y tu aliento liberan sustancias distintas. Tú no las notas. Él, sí. | Silueta con aura roja · moléculas · perro olfateando |
| 0:13 | Su nariz tiene hasta 300 millones de receptores olfativos. La tuya, unos 6 millones. | Contador 300 M · barras perro vs. humano |
| 0:19 | Y al olfatear, el aire se divide en dos caminos: uno para respirar, y otro solo para oler. | Corte de la cabeza con dos flujos · zona olfativa |
| 0:25 | En Belfast tomaron sudor y aliento de personas antes y después de un examen estresante. Cuatro perros debían encontrar la del estrés. | Muestras antes/después · 4 perros |
| 0:34 | Acertaron casi el 94 % de las veces. | Anillo 94 % |
| 0:38 | En Italia, perros que olieron el sudor de personas asustadas se estresaron: su corazón se aceleró, y buscaron más a su dueño. | Gotas de sudor · electro acelerándose · perro junto al dueño |
| 0:45 | Con el olor de personas felices, en cambio, se acercaron más a un desconocido. | Perro acercándose a un extraño |
| 0:50 | Y no solo usan la nariz. Su cerebro reacciona al tono emocional de tu voz. Si oyen una voz alegre, miran más la cara que expresa esa misma emoción. | Cerebro y onda de voz · caras alegre/enfadada |
| 1:00 | Y cuando os miráis a los ojos, los dos producís más oxitocina: la hormona del vínculo. | Ojo de perro y ojo humano · bucle de oxitocina |
| 1:06 | En Suecia descubrieron que el estrés acumulado en el pelo de los perros se parece al de sus dueños. Puedes disimular delante de cualquiera… pero no delante de él. | Pelos con medidores de cortisol · atardecer |
| 1:15 | ¿Tu perro ha venido alguna vez a consolarte? | Cierre «COMENTA TU HISTORIA» |

## Fuentes verificadas

- **Estrés en sudor y aliento (Belfast, 2022)** — Wilson, Campbell, Petzel y Reeve, *PLOS ONE* 17(9): e0274143.
  Muestras de 36 personas antes/después de una tarea de aritmética estresante; 4 perros; 93,75 % de aciertos
  (675 de 720 pruebas). https://pmc.ncbi.nlm.nih.gov/articles/PMC9518869 ·
  https://www.sciencedaily.com/releases/2022/09/220929133419.htm
- **Sudor de miedo y de felicidad (Italia)** — D'Aniello et al., *Animal Cognition* 21(1): 67–78 (2018).
  Con olor de miedo: más conductas de estrés y mayor frecuencia cardiaca; con olor de felicidad: menos conductas
  hacia el dueño y más hacia el desconocido. https://core.ac.uk/download/389459404.pdf
- **300 millones vs. ~6 millones de receptores; el aire se divide en dos flujos (olfato y respiración)** —
  NOVA/PBS (cita a Brent Craven, Penn State). https://www.pbs.org/wgbh/nova/article/dogs-sense-of-smell
- **Áreas cerebrales sensibles a la voz y a su tono emocional** — Andics et al., *Current Biology* 24(5) (2014).
  https://www.sciencedaily.com/releases/2014/02/140220132152.htm
- **Relacionan voz y cara con la misma emoción** — Albuquerque et al., *Biology Letters* 12(1): 20150883 (2016).
  https://pubmed.ncbi.nlm.nih.gov/26763220/
- **Mirada mutua y oxitocina** — Nagasawa et al., *Science* 348: 333–336 (2015).
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4663257
- **Cortisol del pelo sincronizado perro–dueño (Suecia, Linköping)** — Sundman et al., *Scientific Reports* 9: 7391 (2019).
  https://liu.se/en/news-item/hunden-speglar-agarens-stress

Matices: el 94 % es el acierto global en un experimento con perros entrenados, no la capacidad de cualquier perro;
el número de receptores no se traduce directamente en «X veces mejor olfato» (por eso el vídeo no da esa cifra);
el estudio sueco es correlacional (no prueba qué causa la sincronía). No se usó la cifra del «12 % del aire» que circula
por internet porque no se pudo verificar en la fuente original.

## Texto para publicar

**Título:** Tu perro HUELE tus emociones 🐶👃

**Descripción:**
Tu perro sabe cuándo tienes miedo… y no lo adivina: lo huele. En 2022, unos perros detectaron el olor del estrés
en el sudor y el aliento con casi un 94 % de acierto. Y eso no es todo: reaccionan al tono de tu voz, comparten
oxitocina contigo cuando os miráis y hasta su nivel de estrés se parece al tuyo. ¿Tu perro ha venido alguna vez a
consolarte? Cuéntamelo en comentarios 👇

**Hashtags:** #perros #curiosidades #ciencia #sabiasque #perrostiktok #amorperruno #mascotas #olfato #emociones #datoscuriosos
