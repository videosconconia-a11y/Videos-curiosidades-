"""Servidor web: recibe las llamadas de Twilio y sirve el panel del restaurante.

Flujo de una llamada:
  Twilio → POST /voz/entrante     → saludo + <Gather> (escucha al cliente)
  Twilio → POST /voz/respuesta    → texto reconocido → Claude → <Say> + <Gather>
                                     (si Claude tarda, dice "un momento" y sigue en /voz/continuar)
  Twilio → POST /voz/estado       → la llamada ha terminado
"""
from __future__ import annotations

import asyncio
import logging
import secrets
from contextlib import asynccontextmanager
from urllib.parse import parse_qsl

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Gather, VoiceResponse

from . import panel
from .agente import Agente, Respuesta, saludo_inicial
from .config import Ajustes, cargar_env, cargar_restaurante
from .notificaciones import creador_notificador
from .reservas import Reservas

log = logging.getLogger("agente_voz")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ESPERA_DIRECTA = 3.5     # segundos que esperamos a Claude antes de decir "un momento"
ESPERA_MAXIMA = 11.0     # Twilio corta a los 15 s: no pasarse
FRASES_ESPERA = ["Un momento, por favor.", "Lo compruebo, un segundo.", "Sigo con ello, un momento."]


class Estado:
    def __init__(self, ajustes: Ajustes | None = None, agente: Agente | None = None):
        cargar_env()
        self.ajustes = ajustes or Ajustes()
        self.restaurante = cargar_restaurante()
        self.reservas = Reservas(self.restaurante, self.ajustes.base_datos)
        self.agente = agente or Agente(self.restaurante, self.reservas, self.ajustes,
                                       al_reservar=creador_notificador(self.restaurante, self.ajustes))
        self.pendientes: dict[str, asyncio.Task] = {}
        self.esperas: dict[str, int] = {}
        self.silencios: dict[str, int] = {}


def crear_app(estado: Estado | None = None) -> FastAPI:
    @asynccontextmanager
    async def vida(app: FastAPI):
        app.state.e = estado or Estado()
        e = app.state.e
        if not e.ajustes.twilio_auth_token:
            log.warning("TWILIO_AUTH_TOKEN vacío: no se comprueba que las peticiones vengan de Twilio.")
        yield

    app = FastAPI(title="Asistente de voz del restaurante", lifespan=vida)
    seguridad = HTTPBasic(auto_error=True)

    # ── utilidades ────────────────────────────────────────────────────────
    async def formulario_twilio(request: Request) -> dict[str, str]:
        cuerpo = (await request.body()).decode()
        datos = dict(parse_qsl(cuerpo, keep_blank_values=True))
        e: Estado = request.app.state.e
        if e.ajustes.twilio_auth_token and e.ajustes.validar_firma_twilio:
            url = str(request.url)
            if e.ajustes.url_publica:
                url = e.ajustes.url_publica + request.url.path + (f"?{request.url.query}" if request.url.query else "")
            firma = request.headers.get("X-Twilio-Signature", "")
            if not RequestValidator(e.ajustes.twilio_auth_token).validate(url, datos, firma):
                log.warning("Firma de Twilio no válida para %s", url)
                raise HTTPException(status_code=403, detail="Firma no válida")
        return datos

    def xml(vr: VoiceResponse) -> Response:
        return Response(content=str(vr), media_type="application/xml")

    def escuchar(e: Estado, vr: VoiceResponse, texto: str | None) -> VoiceResponse:
        g = Gather(input="speech", language=e.ajustes.idioma, speech_timeout="auto",
                   action="/voz/respuesta", method="POST", action_on_empty_result=True, timeout=6)
        if texto:
            g.say(texto, voice=e.ajustes.voz, language=e.ajustes.idioma)
        vr.append(g)
        return vr

    def twiml_respuesta(e: Estado, call_sid: str, resp: Respuesta) -> VoiceResponse:
        vr = VoiceResponse()
        if resp.accion == "seguir":
            return escuchar(e, vr, resp.texto)
        vr.say(resp.texto, voice=e.ajustes.voz, language=e.ajustes.idioma)
        if resp.accion == "transferir" and e.restaurante.telefono_personal:
            vr.dial(e.restaurante.telefono_personal, timeout=25)
            vr.say("Ahora mismo no podemos atenderle. Por favor, llame más tarde. Gracias.",
                   voice=e.ajustes.voz, language=e.ajustes.idioma)
        vr.hangup()
        return vr

    async def esperar_turno(e: Estado, call_sid: str, segundos: float) -> VoiceResponse:
        tarea = e.pendientes.get(call_sid)
        if tarea is None:
            return escuchar(e, VoiceResponse(), "Perdone, ¿me lo puede repetir?")
        try:
            resp = await asyncio.wait_for(asyncio.shield(tarea), timeout=segundos)
        except asyncio.TimeoutError:
            n = e.esperas.get(call_sid, 0)
            e.esperas[call_sid] = n + 1
            vr = VoiceResponse()
            if n >= 3:  # demasiado tiempo: no dejamos al cliente colgado
                tarea.cancel()
                e.pendientes.pop(call_sid, None)
                return twiml_respuesta(e, call_sid, Respuesta(
                    texto="Perdone, el sistema va lento ahora mismo." + (
                        " Le paso con una persona." if e.restaurante.telefono_personal else
                        " Por favor, llame de nuevo en unos minutos."),
                    accion="transferir" if e.restaurante.telefono_personal else "colgar"))
            vr.say(FRASES_ESPERA[min(n, len(FRASES_ESPERA) - 1)], voice=e.ajustes.voz, language=e.ajustes.idioma)
            vr.redirect("/voz/continuar", method="POST")
            return vr
        e.pendientes.pop(call_sid, None)
        e.esperas.pop(call_sid, None)
        return twiml_respuesta(e, call_sid, resp)

    # ── webhooks de Twilio ───────────────────────────────────────────────
    @app.post("/voz/entrante")
    async def entrante(request: Request):
        datos = await formulario_twilio(request)
        e: Estado = request.app.state.e
        sid, tel = datos.get("CallSid", ""), datos.get("From", "")
        e.reservas.guardar_llamada(sid, tel)
        log.info("Llamada entrante %s de %s", sid, tel)
        if e.ajustes.grabar_llamadas and e.ajustes.twilio_account_sid:
            asyncio.get_running_loop().run_in_executor(None, _grabar, e.ajustes, sid)
        return xml(escuchar(e, VoiceResponse(), saludo_inicial(e.restaurante, e.ajustes.grabar_llamadas)))

    @app.post("/voz/respuesta")
    async def respuesta(request: Request):
        datos = await formulario_twilio(request)
        e: Estado = request.app.state.e
        sid, tel = datos.get("CallSid", ""), datos.get("From", "")
        texto = (datos.get("SpeechResult") or "").strip()
        if not texto:
            n = e.silencios.get(sid, 0) + 1
            e.silencios[sid] = n
            if n >= 3:
                vr = VoiceResponse()
                vr.say("Parece que no le escucho bien. Llámenos de nuevo cuando quiera. Hasta luego.",
                       voice=e.ajustes.voz, language=e.ajustes.idioma)
                vr.hangup()
                e.reservas.guardar_llamada(sid, tel, resultado="sin_audio", terminada=True)
                return xml(vr)
            return xml(escuchar(e, VoiceResponse(), "¿Sigue ahí? No le he oído bien." if n == 1
                                else "Perdone, sigo sin oírle. ¿Me lo puede repetir?"))
        e.silencios.pop(sid, None)
        log.info("[%s] cliente: %s (confianza %s)", sid, texto, datos.get("Confidence"))
        anterior = e.pendientes.get(sid)
        if anterior and not anterior.done():
            anterior.cancel()
        e.pendientes[sid] = asyncio.create_task(e.agente.responder(sid, texto, tel))
        e.esperas.pop(sid, None)
        return xml(await esperar_turno(e, sid, ESPERA_DIRECTA))

    @app.post("/voz/continuar")
    async def continuar(request: Request):
        datos = await formulario_twilio(request)
        e: Estado = request.app.state.e
        return xml(await esperar_turno(e, datos.get("CallSid", ""), ESPERA_MAXIMA))

    @app.post("/voz/estado")
    async def estado_llamada(request: Request):
        datos = await formulario_twilio(request)
        e: Estado = request.app.state.e
        sid = datos.get("CallSid", "")
        if datos.get("CallStatus") in ("completed", "busy", "failed", "no-answer", "canceled"):
            e.reservas.guardar_llamada(sid, datos.get("From", ""), terminada=True)
            e.silencios.pop(sid, None)
            e.esperas.pop(sid, None)
            tarea = e.pendientes.pop(sid, None)
            # Si el cliente cuelga mientras Claude piensa, se deja terminar (puede estar guardando una reserva).
            if tarea and not tarea.done():
                log.info("[%s] colgó con un turno en curso", sid)
        return Response(status_code=204)

    @app.get("/salud")
    async def salud():
        return {"ok": True}

    # ── panel del restaurante ────────────────────────────────────────────
    def autorizado(request: Request, cred: HTTPBasicCredentials = Depends(seguridad)) -> Estado:
        e: Estado = request.app.state.e
        if not e.ajustes.panel_clave:
            raise HTTPException(503, "Panel desactivado: define PANEL_CLAVE en el archivo .env")
        ok = (secrets.compare_digest(cred.username, e.ajustes.panel_usuario)
              and secrets.compare_digest(cred.password, e.ajustes.panel_clave))
        if not ok:
            raise HTTPException(401, "Usuario o clave incorrectos", headers={"WWW-Authenticate": "Basic"})
        return e

    panel.registrar(app, autorizado)
    return app


def _grabar(ajustes: Ajustes, call_sid: str) -> None:
    import time
    time.sleep(2)  # se espera a que la llamada esté descolgada
    try:
        from twilio.rest import Client
        Client(ajustes.twilio_account_sid, ajustes.twilio_auth_token).calls(call_sid).recordings.create()
    except Exception:
        log.exception("No se pudo iniciar la grabación de %s", call_sid)


app = crear_app()
