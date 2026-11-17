# Guía de estilo: medir, no opinar

Reglas sacadas del tutorial «Cómo hacer shorts animados virales con Claude» (canal Crea con LuisPa,
https://youtube.com/watch?v=inOeRPOuaQo). Ahí se analizaron 20 shorts virales cuadro por cuadro.
Las cifras de esta guía son las que da ese vídeo; no las hemos medido sobre aquellos originales.

## 1. Guion

- **Paradoja en la primera frase.** Sin intro, sin saludo y sin «¿sabías que…?». La primera línea ya
  tiene que chocar: «Este animal se congela por completo… y en primavera vuelve a la vida».
- **Estructura:** paradoja → escalada (cada dato es más fuerte que el anterior) → **giro** (la razón
  real) → remate → última línea con la sorpresa o la pregunta para comentar.
- **Muletilla de giro.** 14 de los 20 originales pasan a la explicación con las mismas dos palabras.
  Usamos siempre la misma fórmula, por ejemplo «¿El truco?» o «¿La razón?», para que el público la
  reconozca.
- **Ritmo:** los originales, en inglés, van a casi 4 palabras por segundo y prácticamente sin
  silencios. En español las palabras son más largas, así que apuntamos a **3–3,5 palabras/s** sin
  huecos. `tools/ritmo.py` calcula las palabras por segundo de cada escena de `script_data.py`.
- Datos verificados y fuentes en `FUENTES.md` (ver `CLAUDE.md`).

## 2. Imagen y cámara

- **La cámara nunca se queda quieta.** En los originales la cámara se mueve en el ~93 % de los
  cuadros: acercamientos lentos, tan lentos que a simple vista no se notan. Ningún plano debe estar
  fijo, tampoco las gráficas, los contadores ni la tarjeta final.
- **Movimientos largos y suaves** (más de 2 s cada uno), que empiezan y terminan con suavidad
  (ease-in/ease-out).
- **Viajar en vez de cortar.** 12 de los 20 originales tienen un corte o ninguno. Entre planos es
  mejor un fundido largo mientras la cámara sigue moviéndose que un corte seco.
- **La luz sigue a la historia:** cálida y brillante mientras se plantea, más fría y azul de noche al
  llegar la explicación.
- **Oscuro y con contraste.** Las primeras versiones del tutorial salían demasiado claras («parecía un
  día de campo»). Los originales son más oscuros, con más contraste y con colores saturados: luces
  cálidas y sombras azules frías.
- **Fondo desenfocado** detrás del sujeto, para llevar la mirada directamente a él.
- **Las cifras, discretas** y en la parte de arriba. Nada de recuadros ni subrayados con aire de
  presentación de clase.

## 3. Comprobar con números

No des por terminado un vídeo porque «ya se ve bien». Mídelo:

```bash
python3 tools/medir.py videos/<tema>/final_9x16.mp4 [referencia.mp4] --hojas hojas/
```

| Métrica | Objetivo |
|---|---|
| `camara_moviendose_pct` | ≥ 90 % |
| `movimiento_medio_s` | ≥ 2 s |
| `cortes` | lo menos posible (0–1 duros) |
| `brillo` (0–255) | igual o algo más oscuro que la referencia; sin referencia, entre 45 y 90 |
| `contraste` (desv. típica de luminancia) | ≥ 50 |

Ojo: «más oscuro» es relativo. La rana ya medía 54 de brillo, así que oscurecerla más la habría
apagado. Antes de tocar la luz, mide.

Si tienes un short de referencia, mídelo con la misma herramienta y compara las cifras. Cuando algo no
se parezca, no digas «se ve feo»: busca qué número no cuadra y arréglalo.
