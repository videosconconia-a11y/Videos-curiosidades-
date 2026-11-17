"""SMS de confirmación por Twilio (opcional: ENVIAR_SMS_CONFIRMACION=1)."""
from __future__ import annotations

import logging
import threading

from .config import Ajustes, Restaurante

log = logging.getLogger("agente_voz")


def texto_sms(r: Restaurante, reserva: dict, tipo: str) -> str:
    a, m, d = reserva["fecha"].split("-")
    return (f"{r.nombre}: reserva {tipo} para {reserva['personas']} el {d}/{m} a las {reserva['hora']} "
            f"a nombre de {reserva['nombre']}. Código {reserva['codigo']}. "
            f"Para cambios llame al {r.telefono_publico}. {r.direccion}")


def creador_notificador(r: Restaurante, ajustes: Ajustes):
    """Devuelve una función (reserva, tipo) -> None que envía el SMS en segundo plano, o None si está desactivado."""
    if not (ajustes.enviar_sms and ajustes.twilio_account_sid and ajustes.twilio_auth_token and ajustes.twilio_numero):
        return None
    from twilio.rest import Client

    cliente = Client(ajustes.twilio_account_sid, ajustes.twilio_auth_token)

    def enviar(reserva: dict, tipo: str) -> None:
        tel = reserva["telefono"]
        if not tel.startswith("+34") or tel[3:4] not in ("6", "7"):
            return  # solo móviles españoles
        def _hilo():
            try:
                cliente.messages.create(to=tel, from_=ajustes.twilio_numero, body=texto_sms(r, reserva, tipo))
            except Exception:
                log.exception("No se pudo enviar el SMS a %s", tel)
        threading.Thread(target=_hilo, daemon=True).start()

    return enviar
