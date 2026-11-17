# El chico que vivía dentro de las paredes (Pepperell, EE. UU., 1986)

Historia real · 74,2 s · 9:16 · voz IA masculina es_ES (Piper `davefx`) · imágenes recreadas por código.
**Novedad:** el guion va frase a frase (`LINES` en `script_data.py`): cada frase se sintetiza aparte y su plano empieza
exactamente cuando empieza esa frase, así la imagen siempre muestra lo que dice la voz.

## Generar
```bash
pip install numpy pillow scipy piper-tts
./build.sh
```

## Fuentes verificadas
- Daniel LaPlante, 16 años, se escondió dentro de las paredes/huecos de la casa de la familia Bowen en Pepperell (Massachusetts)
  en 1986; comida desaparecida, objetos movidos, mensajes en las paredes del sótano "como escritos con sangre" —
  https://en.wikipedia.org/wiki/Daniel_LaPlante · https://allthatsinteresting.com/daniel-laplante
- 8 de diciembre de 1986: el padre lo encontró en un armario, con la cara pintada y un hacha; persiguió a las chicas hasta un
  dormitorio; la familia escapó por la ventana; la policía lo encontró escondido entre dos paredes —
  UPI, 3/12/1987: https://www.upi.com/Archives/1987/12/03/A-teenager-accused-of-holding-a-man-and-his/7669565506000/
- Centro de menores hasta octubre de 1987, salió bajo fianza —
  https://wikiwand.com/en/articles/Daniel_LaPlante · https://thecinemaholic.com/where-is-phrogging-survivor-tina-bowen-now/
- 1 de diciembre de 1987: asesinó a Priscilla Gustafson y a sus dos hijos (7 y 5 años) en Townsend; condenado en 1988 a tres
  cadenas perpetuas; en 2017 y 2019 los tribunales mantuvieron la condena y sigue en prisión —
  https://www.oxygen.com/crime-news/daniel-laplante-murder-priscilla-gustafson-family ·
  https://m.washingtontimes.com/news/2019/jun/6/sjc-sentence-fair-for-man-convicted-of-3-killings-/ ·
  https://www.cbsnews.com/boston/news/daniel-laplante-priscilla-gustafson-murder-1987-townsend

## Correcciones y decisiones
- Muchas webs dicen que la familia se llamaba "Benson": es falso, eran los **Bowen**.
- La duración del escondite varía según la fuente (semanas / "más de 6 meses"): el guion dice "durante semanas".
- No se usa la historia de la ouija ni otros detalles que solo aparecen en webs poco fiables.
- No se nombra a las víctimas ni a las hijas; el crimen se cuenta sin detalles explícitos (normas de TikTok).
- El periódico es una recreación genérica (no imita a ningún diario real).
