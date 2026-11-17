"""Carga y valida la configuración del restaurante (restaurante.yaml) y del entorno (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
DIAS_BONITOS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

RAIZ = Path(__file__).resolve().parent.parent


def _hora(texto: str) -> time:
    h, m = str(texto).split(":")
    return time(int(h), int(m))


@dataclass(frozen=True)
class Turno:
    nombre: str
    desde: time
    hasta: time


@dataclass(frozen=True)
class Mesa:
    id: str
    min: int
    max: int
    zona: str
    componentes: tuple[str, ...]  # mesas físicas que ocupa (1 si es una mesa normal)


@dataclass
class Restaurante:
    nombre: str
    direccion: str
    como_llegar: str
    telefono_publico: str
    web: str
    zona_horaria: ZoneInfo
    telefono_personal: str
    horario: dict[str, list[Turno]]
    dias_cerrados: set[str]
    intervalo_minutos: int
    duracion_minutos: int
    duracion_grupo_minutos: int
    max_personas_telefono: int
    antelacion_minima_minutos: int
    antelacion_maxima_dias: int
    mesas: list[Mesa]
    informacion: str
    zonas: list[str] = field(default_factory=list)

    def duracion_para(self, personas: int) -> int:
        return self.duracion_grupo_minutos if personas >= 7 else self.duracion_minutos


def cargar_restaurante(ruta: str | os.PathLike | None = None) -> Restaurante:
    ruta = Path(ruta or os.environ.get("RESTAURANTE_CONFIG", RAIZ / "restaurante.yaml"))
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    r = datos["restaurante"]
    res = datos["reservas"]

    horario: dict[str, list[Turno]] = {}
    for dia in DIAS:
        turnos = datos.get("horario", {}).get(dia) or []
        horario[dia] = [Turno(t["nombre"], _hora(t["desde"]), _hora(t["hasta"])) for t in turnos]

    mesas: list[Mesa] = []
    ids_fisicas = set()
    for m in res["mesas"]:
        mesas.append(Mesa(str(m["id"]), int(m["min"]), int(m["max"]), str(m["zona"]), (str(m["id"]),)))
        ids_fisicas.add(str(m["id"]))
    for c in res.get("combinaciones") or []:
        comps = tuple(str(x) for x in c["mesas"])
        desconocidas = set(comps) - ids_fisicas
        if desconocidas:
            raise ValueError(f"Combinación con mesas que no existen: {desconocidas}")
        mesas.append(Mesa("+".join(comps), int(c["min"]), int(c["max"]), str(c["zona"]), comps))

    zonas = sorted({m.zona for m in mesas})
    return Restaurante(
        nombre=r["nombre"],
        direccion=r.get("direccion", ""),
        como_llegar=r.get("como_llegar", ""),
        telefono_publico=r.get("telefono_publico", ""),
        web=r.get("web", ""),
        zona_horaria=ZoneInfo(r.get("zona_horaria", "Europe/Madrid")),
        telefono_personal=str(datos.get("telefono_personal") or ""),
        horario=horario,
        dias_cerrados={str(d) for d in (datos.get("dias_cerrados") or [])},
        intervalo_minutos=int(res.get("intervalo_minutos", 15)),
        duracion_minutos=int(res.get("duracion_minutos", 105)),
        duracion_grupo_minutos=int(res.get("duracion_grupo_minutos", 135)),
        max_personas_telefono=int(res.get("max_personas_telefono", 10)),
        antelacion_minima_minutos=int(res.get("antelacion_minima_minutos", 30)),
        antelacion_maxima_dias=int(res.get("antelacion_maxima_dias", 60)),
        mesas=mesas,
        informacion=str(datos.get("informacion", "")).strip(),
        zonas=zonas,
    )


def _env(nombre: str, defecto: str = "") -> str:
    return os.environ.get(nombre, defecto)


@dataclass
class Ajustes:
    """Variables de entorno (ver .env.example). Se leen al crear el objeto."""
    modelo: str = field(default_factory=lambda: _env("CLAUDE_MODELO", "claude-opus-5-5"))
    esfuerzo: str = field(default_factory=lambda: _env("CLAUDE_ESFUERZO", "low"))
    base_datos: str = field(default_factory=lambda: _env("BASE_DATOS", str(RAIZ / "datos" / "reservas.db")))
    twilio_auth_token: str = field(default_factory=lambda: _env("TWILIO_AUTH_TOKEN"))
    twilio_account_sid: str = field(default_factory=lambda: _env("TWILIO_ACCOUNT_SID"))
    twilio_numero: str = field(default_factory=lambda: _env("TWILIO_NUMERO"))
    validar_firma_twilio: bool = field(default_factory=lambda: _env("VALIDAR_FIRMA_TWILIO", "1") != "0")
    url_publica: str = field(default_factory=lambda: _env("URL_PUBLICA").rstrip("/"))
    voz: str = field(default_factory=lambda: _env("VOZ_TWILIO", "Polly.Lucia-Neural"))
    idioma: str = field(default_factory=lambda: _env("IDIOMA", "es-ES"))
    enviar_sms: bool = field(default_factory=lambda: _env("ENVIAR_SMS_CONFIRMACION", "0") == "1")
    panel_usuario: str = field(default_factory=lambda: _env("PANEL_USUARIO", "admin"))
    panel_clave: str = field(default_factory=lambda: _env("PANEL_CLAVE"))
    grabar_llamadas: bool = field(default_factory=lambda: _env("GRABAR_LLAMADAS", "0") == "1")


def cargar_env(ruta: Path = RAIZ / ".env") -> None:
    """Lee un archivo .env sencillo (CLAVE=valor) sin pisar variables ya definidas."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))
