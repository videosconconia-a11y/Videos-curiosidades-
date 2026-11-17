# Asistente telefónico con IA para restaurantes

Cuando alguien llama al restaurante, contesta un asistente con voz natural en español de España que:

- **dice qué mesas hay libres** consultando la disponibilidad real (no se la inventa),
- **reserva, cambia y cancela** reservas, y da un código de reserva,
- **responde dudas**: horario, dirección, carta, alérgenos, terraza, parking, mascotas, formas de pago…
- **pasa la llamada a una persona** cuando hace falta (grupos grandes, eventos, quejas, o si el cliente lo pide),
- avisa al principio de que es una IA y, si se activa, **manda un SMS de confirmación**,
- deja todo en un **panel web** para el personal: reservas del día, reservas manuales y conversaciones de cada llamada.

```
Cliente ─llama─▶ Número de Twilio ─▶ este servidor ─▶ Claude (entiende y decide)
                  (voz ↔ texto)          │                    │
                                         └── reservas.db ◀────┘ (consulta mesas, reserva…)
```

Twilio pone el número de teléfono, convierte la voz del cliente en texto y lee las respuestas con una voz
española (Polly Lucía). Claude lleva la conversación y usa las herramientas de reservas de este programa.

---

## 1. Qué necesitas

| Cosa | Para qué | Dónde |
|---|---|---|
| Clave de la API de Claude | El "cerebro" del asistente | https://platform.claude.com → API Keys |
| Cuenta de Twilio + un número | Recibir las llamadas | https://www.twilio.com |
| Un servidor siempre encendido | Ejecutar este programa | Railway, Render, Fly.io, un VPS… (o tu ordenador con ngrok para probar) |

> **Número español en Twilio:** para comprar un número +34, Twilio pide un *Regulatory Bundle* (datos y
> documentación de la empresa o autónomo con dirección en España). Hazlo con tiempo: la aprobación puede tardar días.
> Mientras tanto puedes probar con un número de otro país o con el modo chat (paso 3).

## 2. Configurar el restaurante

Ahora mismo **`restaurante.yaml` está preparado para La Posada de Paco Benítez (Melilla)**. Los datos marcados
✅ salen de fuentes públicas y los marcados ⚠️ PENDIENTE (horario, mesas, móvil del encargado, días de cierre,
precios…) **hay que confirmarlos con el restaurante** antes de atender llamadas reales. Mientras un dato no
esté en el archivo, el asistente dice que no lo sabe en vez de inventárselo.

En `ejemplos/casa-ejemplo.yaml` hay otro ejemplo completo (con terraza y precios) que sirve de plantilla.
Para usar otro archivo: `RESTAURANTE_CONFIG=ejemplos/casa-ejemplo.yaml`.

Edita **`restaurante.yaml`**. Ahí van:

- nombre, dirección, teléfono y web,
- **horario** de cada día (turnos de comida y cena, con la primera y la última hora de llegada),
- **días cerrados** (festivos, vacaciones),
- **mesas**: cuántas, para cuántas personas y en qué zona (salón, terraza…), y qué mesas se pueden **juntar**,
- duración de una reserva, máximo de personas por teléfono y antelación,
- el **teléfono del encargado** al que se pasan las llamadas,
- un bloque de **información** libre (carta, precios, alérgenos, parking…). Todo lo que el asistente sabe sale de aquí.

El asistente asigna automáticamente la mesa más pequeña que sirve, nunca reserva dos veces la misma mesa
(aunque entren dos llamadas a la vez) y tiene en cuenta la duración de cada comida.

## 3. Probarlo en tu ordenador sin teléfono

```bash
cd agente-voz-restaurante
python -m venv .venv && source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env          # y pon tu ANTHROPIC_API_KEY
python -m agente_voz.chat     # conversación escrita, como si fuera una llamada
```

Ejemplo de lo que puedes probar con La Posada: *"Hola, quería mesa para cuatro el sábado por la noche"*,
*"¿cuál es el plato estrella?"* (debe decir el rape a la Rusadir), *"¿tenéis menú del día?"* (debe decir que no
tiene ese dato, sin inventárselo), *"quiero cancelar mi reserva"*, *"somos quince personas"*.

Pruebas automáticas (no gastan API): `pytest -q`.

## 4. Conectarlo a un teléfono real

1. **Arranca el servidor**
   ```bash
   uvicorn agente_voz.app:app --host 0.0.0.0 --port 8000
   ```
   Para probar desde tu ordenador, abre otra terminal y ejecuta `ngrok http 8000`. Copia la dirección
   `https://….ngrok-free.app` en `URL_PUBLICA` dentro de `.env` y reinicia el servidor.

2. **En la consola de Twilio** → Phone Numbers → tu número → *Voice Configuration*:
   - *A call comes in*: **Webhook**, `https://TU-URL/voz/entrante`, método **POST**.
   - *Call status changes*: `https://TU-URL/voz/estado`, método **POST**.

3. Rellena en `.env`: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` (así el servidor rechaza peticiones que no
   vengan de Twilio), `TWILIO_NUMERO` y `PANEL_CLAVE`.

4. **Llama al número.** Deberías oír: *"Hola, ha llamado a Casa Ejemplo. Le atiende un asistente virtual con
   inteligencia artificial. ¿En qué puedo ayudarle?"*

5. **Panel del personal:** `https://TU-URL/panel` (usuario y clave de `.env`). Desde el móvil también se ve bien.

### Usar el número de siempre del restaurante

No hace falta cambiar de número. Se configura un **desvío** del número actual al de Twilio:
- **Siempre** (todas las llamadas las coge la IA), o
- **Si no contestáis o está comunicando** (la IA solo atiende cuando el personal no puede). Suele ser la mejor opción.

En móviles se hace con códigos como `**61*NÚMERO#` (si no contesta) o `**67*NÚMERO#` (si comunica); en fijos
y centralitas depende del operador, así que pregunta a tu operador cómo activar el "desvío condicional".

## 5. Ponerlo en producción

Con Docker (por ejemplo en Railway, Render o Fly.io):

```bash
docker build -t asistente-restaurante .
docker run -p 8000:8000 --env-file .env -v $(pwd)/datos:/datos asistente-restaurante
```

- Usa **un solo proceso** (ya viene así): los turnos en curso de cada llamada se guardan en memoria.
- Guarda la carpeta `datos/` en un **disco persistente** (ahí está `reservas.db`) y haz copias de seguridad.
- El servidor tiene que estar siempre encendido: los planes "gratis que se duermen" no sirven para atender llamadas.

## 6. Ajustes útiles (`.env`)

| Variable | Qué hace |
|---|---|
| `CLAUDE_MODELO` | Modelo de Claude. Por defecto `claude-opus-5-5` (el más fiable). `claude-haiku-5-5` cuesta mucho menos por llamada, pero conviene probarlo antes. |
| `CLAUDE_ESFUERZO` | `low` (por defecto) responde más rápido, que es lo importante al teléfono. |
| `VOZ_TWILIO` | Voz: `Polly.Lucia-Neural` (mujer), `Polly.Sergio-Neural` (hombre), voces `Google.es-ES-…` |
| `ENVIAR_SMS_CONFIRMACION=1` | Envía un SMS con el resumen y el código a los móviles españoles. |
| `GRABAR_LLAMADAS=1` | Graba las llamadas en Twilio y lo avisa en el saludo. |

## 7. Cómo funciona por dentro

| Archivo | Qué hace |
|---|---|
| `agente_voz/reservas.py` | Mesas, horarios, disponibilidad y reservas en SQLite (con transacciones para evitar dobles reservas). |
| `agente_voz/agente.py` | Instrucciones del asistente, herramientas y conversación con Claude. |
| `agente_voz/app.py` | Webhooks de Twilio. Si Claude tarda más de 3,5 s, dice "un momento, por favor" para que no haya silencios largos. Si algo falla, pasa la llamada a una persona. |
| `agente_voz/panel.py` | Panel web del personal. |
| `agente_voz/chat.py` | Modo de prueba por escrito. |

Seguridad y fiabilidad que ya trae:
- La disponibilidad la calcula el programa, no la IA; Claude solo puede reservar mediante las herramientas.
- No da datos de reservas de otros teléfonos sin código y nombre, y pide confirmación antes de reservar, cambiar o cancelar.
- Si la API de Claude falla o tarda demasiado, la llamada pasa al encargado (o se pide volver a llamar).
- Si el cliente no habla, se lo pregunta dos veces y después cuelga con educación.
- Comprueba la firma de Twilio, y el panel lleva usuario y clave.
- Si Claude rechaza una petición, la llamada pasa a una persona. Además está activado el modelo de respaldo
  automático de Anthropic (`fallbacks: "default"`): si un modelo rechaza la petición, la API la repite con otro.

## 8. Costes orientativos

- **Twilio:** número mensual + minutos de llamada entrante + reconocimiento de voz + SMS si los activas.
  Mira los precios actuales de España en twilio.com/pricing (Voice y Programmable SMS).
- **Claude:** se paga por tokens. Con `claude-opus-5-5` una llamada típica de reserva (8–10 turnos) cuesta
  del orden de unos céntimos a pocas decenas de céntimos; con `claude-haiku-5-5`, mucho menos.
  Puedes ver el gasto real en platform.claude.com.

## 9. Aspectos legales (España / UE)

*No es asesoramiento legal; revisadlo con vuestra gestoría o asesoría de protección de datos.*

- **Transparencia de la IA:** el Reglamento europeo de IA obliga a informar de que se habla con una IA.
  El saludo ya lo dice.
- **RGPD:** se guardan el nombre, el teléfono y las notas de la reserva (las alergias son datos de salud: guardadlas solo
  para la reserva). Incluid el asistente en vuestro registro de actividades de tratamiento y en la política de privacidad.
  Anthropic y Twilio actúan como encargados del tratamiento: revisad y aceptad sus acuerdos de tratamiento de datos (DPA).
- **Grabación:** si activáis `GRABAR_LLAMADAS`, el aviso se añade al saludo. Definid cuánto tiempo se conservan las grabaciones.
- Borrad las transcripciones y reservas antiguas cada cierto tiempo.

## 10. Ideas para mejorar

- Conectarlo al sistema de reservas que ya uséis (CoverManager, TheFork…) cambiando `reservas.py` por llamadas a su API.
- Llamar o enviar un SMS el día antes para recordar la reserva.
- Lista de espera cuando no hay mesa.
- Voz todavía más natural y con menos espera usando audio en tiempo real (Twilio Media Streams con ElevenLabs o similar).
