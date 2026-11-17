"""Prueba el asistente escribiendo en la terminal, sin teléfono.

    python -m agente_voz.chat                 # simula una llamada desde +34600111222
    python -m agente_voz.chat --telefono ""   # simula número oculto
"""
from __future__ import annotations

import argparse
import asyncio
import uuid

from .agente import Agente, saludo_inicial
from .config import Ajustes, cargar_env, cargar_restaurante
from .reservas import Reservas


async def principal(telefono: str) -> None:
    cargar_env()
    ajustes = Ajustes()
    r = cargar_restaurante()
    agente = Agente(r, Reservas(r, ajustes.base_datos), ajustes)
    sid = "CHAT-" + uuid.uuid4().hex[:10]
    print(f"Asistente: {saludo_inicial(r, ajustes.grabar_llamadas)}")
    while True:
        try:
            texto = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not texto:
            continue
        resp = await agente.responder(sid, texto, telefono)
        print(f"Asistente: {resp.texto}")
        if resp.accion == "transferir":
            print(f"   [→ Se pasaría la llamada al {r.telefono_personal}]")
        if resp.accion in ("colgar", "transferir"):
            print("   [Llamada terminada]")
            return


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--telefono", default="+34600111222")
    asyncio.run(principal(p.parse_args().telefono))
