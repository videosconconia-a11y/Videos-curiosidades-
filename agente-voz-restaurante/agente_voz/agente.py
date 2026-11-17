"""El "cerebro": conversación con Claude y herramientas de reservas.

Cada vez que el cliente dice algo, `Agente.responder()`:
  1. recupera el historial de esa llamada,
  2. llama a Claude con las herramientas de reservas,
  3. ejecuta las herramientas que Claude pida (consultar, reservar, cancelar…),
  4. devuelve el texto que hay que decir por teléfono y la acción (seguir, colgar, transferir).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable

import anthropic

from .config import DIAS_BONITOS, MESES, Ajustes, Restaurante
from .reservas import ErrorReserva, Reservas, normalizar_telefono

log = logging.getLogger("agente_voz")

FRASE_ERROR = ("Perdone, estoy teniendo un problema técnico. "
               "Le paso con una persona del restaurante.")
FRASE_ERROR_SIN_PERSONAL = ("Perdone, estoy teniendo un problema técnico. "
                            "¿Puede llamar de nuevo en unos minutos? Disculpe las molestias.")

HERRAMIENTAS: list[dict[str, Any]] = [
    {
        "name": "consultar_disponibilidad",
        "description": (
            "Consulta las horas con mesa libre para una fecha y un número de personas. "
            "Úsala SIEMPRE antes de ofrecer o confirmar una hora; nunca supongas que hay sitio. "
            "Si se indica 'hora', dice si esa hora concreta está libre y da las alternativas más cercanas."),
        "input_schema": {
            "type": "object",
            "properties": {
                "fecha": {"type": "string", "description": "Fecha en formato AAAA-MM-DD."},
                "personas": {"type": "integer", "description": "Número de comensales, bebés incluidos si ocupan silla."},
                "hora": {"type": "string", "description": "Hora de llegada deseada, HH:MM en 24 h (opcional)."},
                "zona": {"type": "string", "description": "Zona preferida (opcional), por ejemplo 'terraza' o 'salon'."},
            },
            "required": ["fecha", "personas"],
            "additionalProperties": False,
        },
    },
    {
        "name": "crear_reserva",
        "description": (
            "Crea la reserva. Úsala solo cuando el cliente haya confirmado de forma explícita fecha, hora, "
            "número de personas y nombre. Devuelve el código de reserva."),
        "input_schema": {
            "type": "object",
            "properties": {
                "fecha": {"type": "string", "description": "AAAA-MM-DD"},
                "hora": {"type": "string", "description": "HH:MM en 24 h"},
                "personas": {"type": "integer"},
                "nombre": {"type": "string", "description": "Nombre de la persona que reserva."},
                "telefono": {"type": "string", "description": "Teléfono de contacto. Normalmente el número desde el que llama."},
                "notas": {"type": "string", "description": "Alergias, trona, silla de ruedas, celebración, perro… (opcional)."},
                "zona": {"type": "string", "description": "Zona preferida (opcional)."},
            },
            "required": ["fecha", "hora", "personas", "nombre", "telefono"],
            "additionalProperties": False,
        },
    },
    {
        "name": "buscar_reservas",
        "description": "Busca las reservas futuras de un teléfono, o una reserva por su código de cinco cifras.",
        "input_schema": {
            "type": "object",
            "properties": {
                "telefono": {"type": "string"},
                "codigo": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "modificar_reserva",
        "description": (
            "Cambia fecha, hora, personas, notas o zona de una reserva existente. Pasa solo lo que cambia. "
            "Úsala solo tras confirmar con el cliente el cambio exacto."),
        "input_schema": {
            "type": "object",
            "properties": {
                "codigo": {"type": "string"},
                "fecha": {"type": "string"},
                "hora": {"type": "string"},
                "personas": {"type": "integer"},
                "notas": {"type": "string"},
                "zona": {"type": "string"},
            },
            "required": ["codigo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cancelar_reserva",
        "description": "Cancela una reserva. Úsala solo tras confirmar con el cliente qué reserva quiere cancelar.",
        "input_schema": {
            "type": "object",
            "properties": {"codigo": {"type": "string"}},
            "required": ["codigo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "transferir_llamada",
        "description": (
            "Pasa la llamada a una persona del restaurante. Úsala si el cliente lo pide, para grupos grandes, "
            "eventos, quejas, encargos para llevar, o cuando no sepas resolver algo. "
            "Después di una frase corta avisando de que le pasas."),
        "input_schema": {
            "type": "object",
            "properties": {"motivo": {"type": "string"}},
            "required": ["motivo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "colgar",
        "description": (
            "Termina la llamada. Úsala cuando el cliente se despida o ya no necesite nada más. "
            "Después escribe la despedida final."),
        "input_schema": {
            "type": "object",
            "properties": {"motivo": {"type": "string"}},
            "required": ["motivo"],
            "additionalProperties": False,
        },
    },
]


def saludo_inicial(r: Restaurante, grabar: bool = False) -> str:
    """Primer mensaje. Avisa de que es una IA (obligación de transparencia del Reglamento europeo de IA)."""
    texto = f"Hola, ha llamado a {r.nombre}. Le atiende un asistente virtual con inteligencia artificial."
    if grabar:
        texto += " La llamada se graba para gestionar su reserva."
    return texto + " ¿En qué puedo ayudarle?"


def construir_sistema(r: Restaurante) -> str:
    """Instrucciones fijas (no cambian entre llamadas, así se aprovecha la caché)."""
    horario = []
    for dia, turnos in zip(DIAS_BONITOS, r.horario.values()):
        if turnos:
            horario.append(f"- {dia}: " + "; ".join(
                f"{t.nombre}, llegadas de {t.desde:%H:%M} a {t.hasta:%H:%M}" for t in turnos))
        else:
            horario.append(f"- {dia}: cerrado")
    zonas = ", ".join(r.zonas)
    personal = ("Puedes pasar la llamada a una persona con la herramienta transferir_llamada."
                if r.telefono_personal else
                "No hay nadie disponible para pasar la llamada: si no puedes resolver algo, "
                f"pide que llamen en horario de servicio al {r.telefono_publico} o que escriban por la web.")
    return f"""Eres el asistente telefónico del restaurante {r.nombre}. Atiendes llamadas en español de España.
Ya has saludado al cliente, has dicho el nombre del restaurante y que eres un asistente virtual con inteligencia artificial.
Si el cliente pregunta si eres una persona, di con naturalidad que eres un asistente de inteligencia artificial.

# Cómo hablas (es una llamada de teléfono: todo lo que escribes se lee en voz alta)
- Frases cortas y naturales, de una a tres frases por turno. Trato de usted, cálido y profesional.
- Nada de listas, emojis, asteriscos, símbolos ni formato. Solo texto hablado.
- Las horas, dichas como se dicen: "a las nueve y media de la noche", "a las dos del mediodía". Nunca "21:30".
- Las fechas, como "el sábado veintiuno de noviembre". Los códigos y teléfonos, cifra a cifra separadas por comas.
- Si das varias horas libres, ofrece como mucho tres, las más cercanas a lo que pidió.
- Haz una sola pregunta cada vez. No repitas el saludo.
- El reconocimiento de voz puede equivocarse: si algo suena raro (un nombre, un número, una fecha imposible), pregunta.

# Cómo gestionas una reserva
1. Averigua día, hora aproximada y número de personas. Si falta algo, pregúntalo.
2. Llama a consultar_disponibilidad. Nunca afirmes que hay o no hay sitio sin consultarlo.
3. Si no hay a esa hora, ofrece las alternativas más cercanas o la otra zona.
4. Pide el nombre. Como teléfono usa el número desde el que llama, salvo que el cliente diga otro
   o que el número sea oculto (entonces pídelo y repítelo para confirmarlo).
5. Pregunta brevemente si hay alguna alergia, trona o algo que debamos saber (solo una vez).
6. Resume y pide confirmación: "Entonces, mesa para cuatro el sábado a las nueve y media a nombre de Laura, ¿la confirmo?"
7. Solo con un sí claro, llama a crear_reserva. Luego confirma y di el código de reserva.
- Para cambiar o cancelar: busca con buscar_reservas (por el número desde el que llama o por el código),
  confirma de qué reserva se trata (día, hora y nombre) y pide confirmación antes de modificar o cancelar.
- No des datos de reservas de otras personas: si el teléfono no coincide, pide el código de reserva y el nombre.
- Grupos de más de {r.max_personas_telefono} personas, eventos, menús cerrados, quejas y encargos para llevar: pásalo a una persona.

# Reglas
- Usa solo la información de este mensaje y de las herramientas. Si no sabes algo, dilo y ofrece pasar con una persona.
- Nunca inventes precios, platos, horarios ni disponibilidad.
- No hables de temas que no tengan que ver con el restaurante; reconduce con amabilidad.
- {personal}
- Cuando el cliente se despida o no necesite nada más, usa colgar y luego di una despedida breve.
- Si el cliente insulta o la llamada no tiene sentido después de dos intentos, despídete con educación y usa colgar.

# Datos del restaurante
Nombre: {r.nombre}
Dirección: {r.direccion}. {r.como_llegar}
Teléfono: {r.telefono_publico}. Web: {r.web}
Zonas: {zonas}.
Horario de reservas (hora de llegada):
{chr(10).join(horario)}
Una reserva ocupa la mesa unos {r.duracion_minutos} minutos.

Información:
{r.informacion}
"""


def _fecha_hablada(d) -> str:
    return f"{DIAS_BONITOS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def construir_contexto(reservas: Reservas, telefono: str) -> str:
    """Contexto variable de cada llamada (fecha, calendario, quién llama)."""
    ahora = reservas.ahora()
    hoy = ahora.date()
    calendario = "\n".join(
        f"- {_fecha_hablada(hoy + timedelta(days=i))} = {(hoy + timedelta(days=i)).isoformat()}"
        + (" (cerrado)" if not reservas.turnos_del_dia(hoy + timedelta(days=i)) else "")
        for i in range(15))
    tel = normalizar_telefono(telefono)
    oculto = not tel or len(re.sub(r"\D", "", tel)) < 9
    lineas = [
        "[Contexto de la llamada, no lo leas en voz alta]",
        f"Ahora: {_fecha_hablada(hoy)}, {ahora:%H:%M}.",
        "Próximos días:", calendario,
        "Número del cliente: " + ("oculto (pídele un teléfono si reserva)" if oculto else tel),
    ]
    if not oculto:
        existentes = reservas.buscar_reservas(telefono=tel)
        if existentes:
            lineas.append("Este número ya tiene reservas: " + "; ".join(
                f"código {x['codigo']}, {x['fecha']} a las {x['hora']}, {x['personas']} personas, a nombre de {x['nombre']}"
                for x in existentes))
    return "\n".join(lineas)


def limpiar_para_voz(texto: str) -> str:
    texto = re.sub(r"[*_#`>|\[\]]", "", texto)
    texto = re.sub(r"^\s*[-•]\s*", "", texto, flags=re.M)
    return re.sub(r"\s+", " ", texto).strip()


@dataclass
class Respuesta:
    texto: str
    accion: str = "seguir"           # seguir | colgar | transferir
    resultado: str | None = None     # reserva, modificacion, cancelacion, transferida, info…
    eventos: list[dict] = field(default_factory=list)


class Agente:
    def __init__(self, restaurante: Restaurante, reservas: Reservas, ajustes: Ajustes,
                 cliente: anthropic.AsyncAnthropic | None = None,
                 al_reservar: Callable[[dict, str], None] | None = None):
        self.r = restaurante
        self.reservas = reservas
        self.ajustes = ajustes
        self.cliente = cliente or anthropic.AsyncAnthropic(timeout=20.0, max_retries=1)
        self.sistema = construir_sistema(restaurante)
        self.al_reservar = al_reservar  # p. ej. enviar SMS de confirmación

    # ── herramientas ──────────────────────────────────────────────────────
    def _ejecutar(self, nombre: str, datos: dict, call_sid: str, telefono: str, resp: Respuesta) -> str:
        res = self.reservas
        if nombre == "consultar_disponibilidad":
            return json.dumps(res.consultar_disponibilidad(**datos), ensure_ascii=False)
        if nombre == "crear_reserva":
            reserva = res.crear_reserva(**datos, origen="telefono", call_sid=call_sid)
            resp.resultado = "reserva"
            resp.eventos.append({"tipo": "reserva", "reserva": reserva})
            if self.al_reservar:
                try:
                    self.al_reservar(reserva, "creada")
                except Exception:  # un fallo del SMS no debe romper la llamada
                    log.exception("Fallo al notificar la reserva")
            return json.dumps(_resumen(reserva), ensure_ascii=False)
        if nombre == "buscar_reservas":
            encontradas = res.buscar_reservas(**datos)
            mismo_tel = normalizar_telefono(datos.get("telefono", "")) == normalizar_telefono(telefono)
            if not encontradas:
                return "No se ha encontrado ninguna reserva futura."
            return json.dumps({
                "reservas": [_resumen(x) for x in encontradas],
                "aviso": None if (mismo_tel or datos.get("codigo")) else
                "Este teléfono no es el del llamante: confirma el nombre antes de dar detalles.",
            }, ensure_ascii=False)
        if nombre == "modificar_reserva":
            reserva = res.modificar_reserva(**datos)
            resp.resultado = "modificacion"
            resp.eventos.append({"tipo": "modificacion", "reserva": reserva})
            if self.al_reservar:
                try:
                    self.al_reservar(reserva, "modificada")
                except Exception:
                    log.exception("Fallo al notificar la modificación")
            return json.dumps(_resumen(reserva), ensure_ascii=False)
        if nombre == "cancelar_reserva":
            reserva = res.cancelar_reserva(**datos)
            resp.resultado = "cancelacion"
            resp.eventos.append({"tipo": "cancelacion", "reserva": reserva})
            return json.dumps(_resumen(reserva), ensure_ascii=False)
        if nombre == "transferir_llamada":
            if not self.r.telefono_personal:
                return "No hay ningún teléfono para transferir. Explica al cliente otra forma de contactar."
            resp.accion, resp.resultado = "transferir", "transferida"
            return "De acuerdo. Ahora di una frase corta avisando de que le pasas con una persona."
        if nombre == "colgar":
            resp.accion = "colgar"
            resp.resultado = resp.resultado or "colgada"
            return "De acuerdo. Ahora di una despedida breve."
        raise ErrorReserva(f"Herramienta desconocida: {nombre}")

    # ── un turno de conversación ──────────────────────────────────────────
    async def responder(self, call_sid: str, texto_cliente: str, telefono: str = "") -> Respuesta:
        llamada = self.reservas.cargar_llamada(call_sid)
        mensajes: list[dict] = llamada["mensajes"] if llamada else []
        transcripcion: list[dict] = llamada["transcripcion"] if llamada else []
        if not llamada:
            transcripcion.append({"quien": "asistente", "texto": saludo_inicial(self.r, self.ajustes.grabar_llamadas)})

        texto_cliente = (texto_cliente or "").strip() or "(silencio)"
        transcripcion.append({"quien": "cliente", "texto": texto_cliente})
        if not mensajes:
            contenido = construir_contexto(self.reservas, telefono) + "\n\nCliente: " + texto_cliente
        else:
            contenido = texto_cliente
        longitud_previa = len(mensajes)
        mensajes.append({"role": "user", "content": contenido})

        resp = Respuesta(texto="")
        try:
            resp.texto = await self._bucle(mensajes, call_sid, telefono, resp)
        except Exception:
            log.exception("Error hablando con Claude en la llamada %s", call_sid)
            # Se deshace el turno para que el historial quede válido.
            del mensajes[longitud_previa:]
            if self.r.telefono_personal:
                resp.texto, resp.accion, resp.resultado = FRASE_ERROR, "transferir", "error"
            else:
                resp.texto, resp.accion, resp.resultado = FRASE_ERROR_SIN_PERSONAL, "colgar", "error"

        transcripcion.append({"quien": "asistente", "texto": resp.texto})
        self.reservas.guardar_llamada(call_sid, telefono, mensajes=mensajes, transcripcion=transcripcion,
                                      resultado=resp.resultado)
        return resp

    async def _bucle(self, mensajes: list[dict], call_sid: str, telefono: str, resp: Respuesta) -> str:
        for _ in range(8):
            r = await self.cliente.beta.messages.create(
                model=self.ajustes.modelo,
                max_tokens=4096,
                system=self.sistema,
                tools=HERRAMIENTAS,
                messages=mensajes,
                output_config={"effort": self.ajustes.esfuerzo},
                cache_control={"type": "ephemeral"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            if r.stop_reason == "refusal":
                # Se quita el turno rechazado del historial y se pasa con una persona.
                while mensajes and not (mensajes[-1]["role"] == "user" and isinstance(mensajes[-1]["content"], str)):
                    mensajes.pop()
                if mensajes:
                    mensajes.pop()
                if self.r.telefono_personal:
                    resp.accion, resp.resultado = "transferir", "transferida"
                    return "Eso prefiero que se lo resuelva una persona del restaurante. Le paso ahora mismo."
                resp.accion = "colgar"
                return f"Eso no se lo puedo resolver yo. Puede llamar al {self.r.telefono_publico}. Gracias."
            mensajes.append({"role": "assistant",
                             "content": [b.model_dump(mode="json", exclude_none=True) for b in r.content]})
            usos = [b for b in r.content if b.type == "tool_use"]
            if r.stop_reason == "pause_turn":
                continue
            if r.stop_reason != "tool_use" or not usos:
                texto = limpiar_para_voz(" ".join(b.text for b in r.content if b.type == "text"))
                return texto or ("Hasta luego, gracias por llamar." if resp.accion == "colgar" else
                                 "Perdone, ¿me lo puede repetir?")
            resultados = []
            for uso in usos:
                try:
                    contenido = self._ejecutar(uso.name, dict(uso.input), call_sid, telefono, resp)
                    resultados.append({"type": "tool_result", "tool_use_id": uso.id, "content": contenido})
                except (ErrorReserva, TypeError, ValueError) as e:
                    resultados.append({"type": "tool_result", "tool_use_id": uso.id,
                                       "content": f"Error: {e}", "is_error": True})
                log.info("[%s] herramienta %s %s", call_sid, uso.name, json.dumps(uso.input, ensure_ascii=False))
            mensajes.append({"role": "user", "content": resultados})
        raise RuntimeError("Demasiadas llamadas a herramientas en un turno")


def _resumen(reserva: dict) -> dict:
    return {k: reserva[k] for k in ("codigo", "fecha", "hora", "personas", "nombre", "telefono", "notas", "zona", "estado")}
