"""Un Claude de mentira para probar sin gastar llamadas a la API."""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field


@dataclass
class Texto:
    text: str
    type: str = "text"

    def model_dump(self, **_):
        return asdict(self)


@dataclass
class UsoHerramienta:
    name: str
    input: dict
    id: str
    type: str = "tool_use"

    def model_dump(self, **_):
        return asdict(self)


@dataclass
class Mensaje:
    content: list
    stop_reason: str


@dataclass
class _Mensajes:
    guion: list
    peticiones: list = field(default_factory=list)
    retraso: float = 0.0

    async def create(self, **kwargs):
        # Copia del historial tal y como se envió
        self.peticiones.append({**kwargs, "messages": [dict(m) for m in kwargs["messages"]]})
        if self.retraso:
            await asyncio.sleep(self.retraso)
        paso = self.guion.pop(0)
        if isinstance(paso, Exception):
            raise paso
        return paso


class FalsoClaude:
    def __init__(self, guion, retraso: float = 0.0):
        self.messages = _Mensajes(list(guion), retraso=retraso)
        self.beta = self


def texto(t: str) -> Mensaje:
    return Mensaje([Texto(t)], "end_turn")


def herramienta(nombre: str, datos: dict, id_: str = "t1") -> Mensaje:
    return Mensaje([UsoHerramienta(nombre, datos, id_)], "tool_use")
