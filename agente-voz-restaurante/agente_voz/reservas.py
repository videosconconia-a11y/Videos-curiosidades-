"""Mesas, disponibilidad y reservas sobre SQLite.

Toda la lógica de negocio está aquí y es determinista: Claude nunca "inventa"
disponibilidad, siempre la pregunta a estas funciones. Las escrituras se hacen
en transacciones `BEGIN IMMEDIATE`, así dos llamadas simultáneas no pueden
reservar la misma mesa.
"""
from __future__ import annotations

import json
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterator

from .config import DIAS, Mesa, Restaurante

ESQUEMA = """
CREATE TABLE IF NOT EXISTS reservas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo        TEXT NOT NULL UNIQUE,
    fecha         TEXT NOT NULL,           -- AAAA-MM-DD
    hora          TEXT NOT NULL,           -- HH:MM
    inicio_min    INTEGER NOT NULL,        -- minutos desde las 00:00
    fin_min       INTEGER NOT NULL,
    personas      INTEGER NOT NULL,
    nombre        TEXT NOT NULL,
    telefono      TEXT NOT NULL,
    notas         TEXT NOT NULL DEFAULT '',
    mesa          TEXT NOT NULL,
    mesas_fisicas TEXT NOT NULL,           -- ids separados por comas
    zona          TEXT NOT NULL,
    estado        TEXT NOT NULL DEFAULT 'confirmada',  -- confirmada | cancelada
    origen        TEXT NOT NULL DEFAULT 'telefono',    -- telefono | panel
    call_sid      TEXT NOT NULL DEFAULT '',
    creada        TEXT NOT NULL,
    actualizada   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reservas_fecha ON reservas(fecha, estado);
CREATE INDEX IF NOT EXISTS idx_reservas_tel ON reservas(telefono, estado);

CREATE TABLE IF NOT EXISTS llamadas (
    call_sid      TEXT PRIMARY KEY,
    telefono      TEXT NOT NULL DEFAULT '',
    inicio        TEXT NOT NULL,
    fin           TEXT,
    resultado     TEXT NOT NULL DEFAULT '',     -- reserva, cancelacion, transferida, info, colgada…
    mensajes_json TEXT NOT NULL DEFAULT '[]',   -- historial para Claude
    transcripcion TEXT NOT NULL DEFAULT '[]'    -- [{"quien": "cliente|asistente", "texto": ...}]
);
"""


class ErrorReserva(Exception):
    """Error de negocio con un mensaje que se le puede explicar al cliente."""


def normalizar_telefono(tel: str) -> str:
    t = re.sub(r"[^\d+]", "", tel or "")
    if t.startswith("00"):
        t = "+" + t[2:]
    if re.fullmatch(r"[6789]\d{8}", t):
        t = "+34" + t
    return t


def _min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _hhmm(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def _parse_fecha(texto: str) -> date:
    try:
        return date.fromisoformat(str(texto).strip())
    except ValueError as e:
        raise ErrorReserva(f"Fecha no válida: {texto!r}. Usa el formato AAAA-MM-DD.") from e


def _parse_hora(texto: str) -> str:
    m = re.fullmatch(r"\s*(\d{1,2})[:.h](\d{2})\s*", str(texto))
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        raise ErrorReserva(f"Hora no válida: {texto!r}. Usa el formato HH:MM en 24 horas.")
    return f"{int(m.group(1)):02d}:{m.group(2)}"


class Reservas:
    def __init__(self, restaurante: Restaurante, ruta_db: str | Path):
        self.r = restaurante
        self.ruta_db = str(ruta_db)
        if self.ruta_db != ":memory:":
            Path(self.ruta_db).parent.mkdir(parents=True, exist_ok=True)
        self._memoria = sqlite3.connect(":memory:", check_same_thread=False, isolation_level=None) if self.ruta_db == ":memory:" else None
        with self._conexion() as c:
            c.executescript(ESQUEMA)

    # ── utilidades ─────────────────────────────────────────────────────────
    @contextmanager
    def _conexion(self) -> Iterator[sqlite3.Connection]:
        if self._memoria is not None:
            c = self._memoria
            c.row_factory = sqlite3.Row
            yield c
            return
        c = sqlite3.connect(self.ruta_db, timeout=10, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        try:
            yield c
        finally:
            c.close()

    @contextmanager
    def _transaccion(self) -> Iterator[sqlite3.Connection]:
        with self._conexion() as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                yield c
                c.execute("COMMIT")
            except BaseException:
                c.execute("ROLLBACK")
                raise

    def ahora(self) -> datetime:
        return datetime.now(self.r.zona_horaria).replace(tzinfo=None, second=0, microsecond=0)

    # ── calendario ─────────────────────────────────────────────────────────
    def turnos_del_dia(self, d: date):
        if d.isoformat() in self.r.dias_cerrados:
            return []
        return self.r.horario[DIAS[d.weekday()]]

    def _horas_del_dia(self, d: date) -> list[str]:
        horas = []
        for t in self.turnos_del_dia(d):
            m = t.desde.hour * 60 + t.desde.minute
            fin = t.hasta.hour * 60 + t.hasta.minute
            while m <= fin:
                horas.append(_hhmm(m))
                m += self.r.intervalo_minutos
        return horas

    def _validar_fecha_hora(self, d: date, hora: str | None, personas: int) -> None:
        if personas < 1:
            raise ErrorReserva("El número de personas tiene que ser al menos 1.")
        if personas > self.r.max_personas_telefono:
            raise ErrorReserva(
                f"Para más de {self.r.max_personas_telefono} personas la reserva la gestiona el encargado. "
                "Ofrece pasar la llamada a una persona.")
        hoy = self.ahora().date()
        if d < hoy:
            raise ErrorReserva("Esa fecha ya ha pasado.")
        if d > hoy + timedelta(days=self.r.antelacion_maxima_dias):
            raise ErrorReserva(f"Solo se aceptan reservas con un máximo de {self.r.antelacion_maxima_dias} días de antelación.")
        if not self.turnos_del_dia(d):
            raise ErrorReserva("El restaurante está cerrado ese día.")
        if hora is not None:
            if hora not in self._horas_del_dia(d):
                turnos = ", ".join(f"{t.nombre} de {t.desde:%H:%M} a {t.hasta:%H:%M}" for t in self.turnos_del_dia(d))
                raise ErrorReserva(
                    f"A las {hora} no se reserva ese día. Horas de llegada posibles: {turnos}, "
                    f"cada {self.r.intervalo_minutos} minutos.")
            inicio = datetime.combine(d, datetime.strptime(hora, "%H:%M").time())
            if inicio < self.ahora() + timedelta(minutes=self.r.antelacion_minima_minutos):
                raise ErrorReserva(
                    f"Hace falta reservar con al menos {self.r.antelacion_minima_minutos} minutos de antelación.")

    # ── ocupación ──────────────────────────────────────────────────────────
    def _ocupacion(self, c: sqlite3.Connection, fecha: str, excluir_codigo: str | None = None):
        filas = c.execute(
            "SELECT codigo, inicio_min, fin_min, mesas_fisicas FROM reservas WHERE fecha=? AND estado='confirmada'",
            (fecha,)).fetchall()
        return [(f["inicio_min"], f["fin_min"], set(f["mesas_fisicas"].split(",")))
                for f in filas if f["codigo"] != excluir_codigo]

    def _mesas_candidatas(self, personas: int, zona: str | None) -> list[Mesa]:
        cands = [m for m in self.r.mesas if m.min <= personas <= m.max and (not zona or m.zona == zona)]
        # Primero la mesa más ajustada; las mesas sueltas antes que las combinadas.
        return sorted(cands, key=lambda m: (m.max, len(m.componentes), m.id))

    def _mesa_libre(self, ocupacion, personas: int, zona: str | None, inicio: int) -> Mesa | None:
        fin = inicio + self.r.duracion_para(personas)
        for mesa in self._mesas_candidatas(personas, zona):
            if all(not (set(mesa.componentes) & fisicas and inicio < f_fin and f_ini < fin)
                   for f_ini, f_fin, fisicas in ocupacion):
                return mesa
        return None

    def _horas_libres(self, c, d: date, personas: int, zona: str | None, excluir: str | None = None) -> list[str]:
        ocup = self._ocupacion(c, d.isoformat(), excluir)
        limite = self.ahora() + timedelta(minutes=self.r.antelacion_minima_minutos)
        libres = []
        for h in self._horas_del_dia(d):
            if datetime.combine(d, datetime.strptime(h, "%H:%M").time()) < limite:
                continue
            if self._mesa_libre(ocup, personas, zona, _min(h)):
                libres.append(h)
        return libres

    # ── API pública (la usan las herramientas de Claude y el panel) ────────
    def consultar_disponibilidad(self, fecha: str, personas: int, hora: str | None = None,
                                 zona: str | None = None) -> dict:
        d = _parse_fecha(fecha)
        personas = int(personas)
        hora = _parse_hora(hora) if hora else None
        zona = zona or None
        if zona and zona not in self.r.zonas:
            raise ErrorReserva(f"Zona desconocida. Zonas: {', '.join(self.r.zonas)}.")
        self._validar_fecha_hora(d, None, personas)
        with self._conexion() as c:
            libres = self._horas_libres(c, d, personas, zona)
            otras_zonas = {}
            if zona:
                for z in self.r.zonas:
                    if z != zona:
                        otras_zonas[z] = self._horas_libres(c, d, personas, z)
        resultado: dict = {
            "fecha": d.isoformat(),
            "dia_semana": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][d.weekday()],
            "personas": personas,
            "zona": zona or "cualquiera",
        }
        if hora:
            try:
                self._validar_fecha_hora(d, hora, personas)
                resultado["hora_pedida"] = hora
                resultado["hora_pedida_disponible"] = hora in libres
            except ErrorReserva as e:
                resultado["hora_pedida"] = hora
                resultado["hora_pedida_disponible"] = False
                resultado["motivo"] = str(e)
            if not resultado["hora_pedida_disponible"]:
                cercanas = sorted(libres, key=lambda h: abs(_min(h) - _min(hora)))[:4]
                resultado["alternativas_mas_cercanas"] = sorted(cercanas)
        resultado["horas_libres"] = libres
        if otras_zonas:
            resultado["horas_libres_en_otras_zonas"] = otras_zonas
        if not libres:
            resultado["nota"] = "No queda ninguna mesa libre ese día para ese número de personas" + (
                " en esa zona." if zona else ".")
        return resultado

    def crear_reserva(self, fecha: str, hora: str, personas: int, nombre: str, telefono: str,
                      notas: str = "", zona: str | None = None, origen: str = "telefono",
                      call_sid: str = "") -> dict:
        d = _parse_fecha(fecha)
        hora = _parse_hora(hora)
        personas = int(personas)
        nombre = (nombre or "").strip()
        telefono = normalizar_telefono(telefono)
        if not nombre:
            raise ErrorReserva("Falta el nombre para la reserva.")
        if len(re.sub(r"\D", "", telefono)) < 9:
            raise ErrorReserva("Falta un teléfono de contacto válido.")
        if zona and zona not in self.r.zonas:
            raise ErrorReserva(f"Zona desconocida. Zonas: {', '.join(self.r.zonas)}.")
        self._validar_fecha_hora(d, hora, personas)
        inicio = _min(hora)
        fin = inicio + self.r.duracion_para(personas)
        with self._transaccion() as c:
            duplicada = c.execute(
                "SELECT codigo FROM reservas WHERE fecha=? AND telefono=? AND estado='confirmada' "
                "AND ABS(inicio_min-?) < 180", (d.isoformat(), telefono, inicio)).fetchone()
            if duplicada:
                raise ErrorReserva(
                    f"Este teléfono ya tiene una reserva ese día a una hora parecida (código {duplicada['codigo']}). "
                    "Pregunta si quiere modificarla en lugar de crear otra.")
            mesa = self._mesa_libre(self._ocupacion(c, d.isoformat()), personas, zona or None, inicio)
            if mesa is None:
                raise ErrorReserva("Esa hora ya no está disponible. Consulta la disponibilidad otra vez y ofrece alternativas.")
            codigo = self._nuevo_codigo(c)
            ahora = datetime.now().isoformat(timespec="seconds")
            c.execute(
                "INSERT INTO reservas (codigo, fecha, hora, inicio_min, fin_min, personas, nombre, telefono, notas,"
                " mesa, mesas_fisicas, zona, origen, call_sid, creada, actualizada)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (codigo, d.isoformat(), hora, inicio, fin, personas, nombre, telefono, (notas or "").strip(),
                 mesa.id, ",".join(mesa.componentes), mesa.zona, origen, call_sid, ahora, ahora))
        return self.obtener(codigo)

    def modificar_reserva(self, codigo: str, fecha: str | None = None, hora: str | None = None,
                          personas: int | None = None, notas: str | None = None, zona: str | None = None) -> dict:
        actual = self.obtener(codigo)
        if actual["estado"] != "confirmada":
            raise ErrorReserva("Esa reserva está cancelada.")
        d = _parse_fecha(fecha or actual["fecha"])
        hora = _parse_hora(hora or actual["hora"])
        personas = int(personas or actual["personas"])
        if zona and zona not in self.r.zonas:
            raise ErrorReserva(f"Zona desconocida. Zonas: {', '.join(self.r.zonas)}.")
        self._validar_fecha_hora(d, hora, personas)
        inicio = _min(hora)
        fin = inicio + self.r.duracion_para(personas)
        with self._transaccion() as c:
            ocup = self._ocupacion(c, d.isoformat(), excluir_codigo=actual["codigo"])
            # Si se puede, se mantiene la zona que tenía.
            mesa = self._mesa_libre(ocup, personas, zona or actual["zona"], inicio)
            if mesa is None and not zona:
                mesa = self._mesa_libre(ocup, personas, None, inicio)
            if mesa is None:
                raise ErrorReserva("No hay mesa libre para ese cambio. Consulta la disponibilidad y ofrece alternativas.")
            c.execute(
                "UPDATE reservas SET fecha=?, hora=?, inicio_min=?, fin_min=?, personas=?, notas=?, mesa=?,"
                " mesas_fisicas=?, zona=?, actualizada=? WHERE codigo=?",
                (d.isoformat(), hora, inicio, fin, personas, actual["notas"] if notas is None else notas.strip(),
                 mesa.id, ",".join(mesa.componentes), mesa.zona, datetime.now().isoformat(timespec="seconds"),
                 actual["codigo"]))
        return self.obtener(codigo)

    def cancelar_reserva(self, codigo: str) -> dict:
        actual = self.obtener(codigo)
        if actual["estado"] == "cancelada":
            raise ErrorReserva("Esa reserva ya estaba cancelada.")
        with self._transaccion() as c:
            c.execute("UPDATE reservas SET estado='cancelada', actualizada=? WHERE codigo=?",
                      (datetime.now().isoformat(timespec="seconds"), actual["codigo"]))
        return self.obtener(codigo)

    def obtener(self, codigo: str) -> dict:
        codigo = re.sub(r"\D", "", str(codigo))
        with self._conexion() as c:
            f = c.execute("SELECT * FROM reservas WHERE codigo=?", (codigo,)).fetchone()
        if not f:
            raise ErrorReserva(f"No existe ninguna reserva con el código {codigo}.")
        return dict(f)

    def buscar_reservas(self, telefono: str | None = None, codigo: str | None = None,
                        incluir_pasadas: bool = False) -> list[dict]:
        if codigo:
            try:
                return [self.obtener(codigo)]
            except ErrorReserva:
                return []
        if not telefono:
            raise ErrorReserva("Hace falta el teléfono o el código de la reserva.")
        tel = normalizar_telefono(telefono)
        hoy = self.ahora().date().isoformat()
        with self._conexion() as c:
            filas = c.execute(
                "SELECT * FROM reservas WHERE telefono=? AND estado='confirmada'"
                + ("" if incluir_pasadas else " AND fecha>=?") + " ORDER BY fecha, hora",
                (tel,) if incluir_pasadas else (tel, hoy)).fetchall()
        return [dict(f) for f in filas]

    def listar(self, fecha: str, incluir_canceladas: bool = True) -> list[dict]:
        with self._conexion() as c:
            filas = c.execute(
                "SELECT * FROM reservas WHERE fecha=?" + ("" if incluir_canceladas else " AND estado='confirmada'")
                + " ORDER BY hora, mesa", (fecha,)).fetchall()
        return [dict(f) for f in filas]

    def _nuevo_codigo(self, c: sqlite3.Connection) -> str:
        while True:
            codigo = f"{secrets.randbelow(90000) + 10000}"
            if not c.execute("SELECT 1 FROM reservas WHERE codigo=?", (codigo,)).fetchone():
                return codigo

    # ── llamadas (historial de conversación y transcripción) ───────────────
    def cargar_llamada(self, call_sid: str) -> dict | None:
        with self._conexion() as c:
            f = c.execute("SELECT * FROM llamadas WHERE call_sid=?", (call_sid,)).fetchone()
        if not f:
            return None
        d = dict(f)
        d["mensajes"] = json.loads(d.pop("mensajes_json"))
        d["transcripcion"] = json.loads(d["transcripcion"])
        return d

    def guardar_llamada(self, call_sid: str, telefono: str = "", mensajes: list | None = None,
                        transcripcion: list | None = None, resultado: str | None = None,
                        terminada: bool = False) -> None:
        ahora = datetime.now().isoformat(timespec="seconds")
        with self._transaccion() as c:
            existe = c.execute("SELECT 1 FROM llamadas WHERE call_sid=?", (call_sid,)).fetchone()
            if not existe:
                c.execute("INSERT INTO llamadas (call_sid, telefono, inicio) VALUES (?,?,?)",
                          (call_sid, normalizar_telefono(telefono), ahora))
            if mensajes is not None:
                c.execute("UPDATE llamadas SET mensajes_json=? WHERE call_sid=?",
                          (json.dumps(mensajes, ensure_ascii=False), call_sid))
            if transcripcion is not None:
                c.execute("UPDATE llamadas SET transcripcion=? WHERE call_sid=?",
                          (json.dumps(transcripcion, ensure_ascii=False), call_sid))
            if resultado:
                c.execute("UPDATE llamadas SET resultado=? WHERE call_sid=?", (resultado, call_sid))
            if terminada:
                c.execute("UPDATE llamadas SET fin=COALESCE(fin, ?) WHERE call_sid=?", (ahora, call_sid))

    def listar_llamadas(self, limite: int = 50) -> list[dict]:
        with self._conexion() as c:
            filas = c.execute("SELECT call_sid, telefono, inicio, fin, resultado, transcripcion FROM llamadas "
                              "ORDER BY inicio DESC LIMIT ?", (limite,)).fetchall()
        return [dict(f) | {"transcripcion": json.loads(f["transcripcion"])} for f in filas]
