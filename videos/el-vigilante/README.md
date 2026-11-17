# El Vigilante (Westfield, Nueva Jersey, 2014) — caso real sin resolver

89,3 s · 9:16 · voz neuronal es-ES **Álvaro** (Microsoft Edge TTS) · subtítulos karaoke palabra a palabra · sin etiqueta en pantalla.

## Novedades respecto a los vídeos anteriores
- **Voz más natural:** `voice.py` usa `es-ES-AlvaroNeural` (la típica "voz de IA que suena normal"). Las citas de la carta
  van más lentas y graves, con algo de eco, para distinguirlas del narrador.
- **Subtítulos sincronizados por palabra:** la voz devuelve el tiempo exacto de cada palabra; las palabras se encienden
  cuando se dicen, y las cifras se muestran con números (657, 1,3 MILLONES $, 400.000 $).
- **Interacción:** encuesta a mitad del vídeo ("1 = me quedo / 2 = me voy") y cierre pidiendo teorías para una parte 2.
- La carta se escribe en pantalla a la vez que la voz la lee (con sonido de máquina de escribir).

## Generar
```bash
pip install numpy pillow scipy edge-tts
./build.sh            # REVOZ=1 ./build.sh para volver a generar la voz
```

## Fuentes verificadas
- Compra en junio de 2014 por 1.355.657 $; primera carta pocos días después; nunca vivieron allí; venta en 2019 por
  ~959.000 $ (pérdida de ~400.000 $); investigación de la policía de Westfield y la fiscalía del condado de Union sin resolver —
  https://en.wikipedia.org/wiki/The_Watcher_of_Westfield,_New_Jersey ·
  https://www.nbcnewyork.com/news/local/new-jersey-westfield-watcher-house-owners-sell-creepy-property-loss-report/1510750/ ·
  https://www.boston.com/real-estate/real-estate-news/2019/08/09/nj-watcher-house-creepy-letters-fame-sold/
- Citas de las cartas (traducidas): bienvenida al barrio; "sangre joven que pedí"; "¿sabéis lo que hay dentro de las
  paredes?"; padre y abuelo vigilaron la casa; "cientos de coches… quizá yo esté en uno"; ventanas; "Que empiece la fiesta";
  "pedí a los Woods [antiguos dueños] que me trajeran sangre joven y parece que me han hecho caso" —
  https://www.newsweek.com/watcher-real-letters-netflix-brannock-1751435 ·
  https://www.today.com/popculture/tv/the-watcher-real-letters-read-rcna51754

## Correcciones y decisiones
- Circula que "el abuelo vigiló en los años 20 y el padre en los 60": no lo pude confirmar; el guion solo dice que padre
  y abuelo vigilaron la casa.
- Otras frases virales ("¿quién tiene los dormitorios que dan a la calle?") no aparecen en fuentes fiables: no se usan.
- No se dan los nombres de la familia ni de los hijos.
