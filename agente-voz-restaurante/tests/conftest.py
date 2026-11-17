from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agente_voz.config import cargar_restaurante  # noqa: E402
from agente_voz.reservas import Reservas  # noqa: E402

# "Ahora" fijo para las pruebas: martes 17 de noviembre de 2026 a las 10:00.
AHORA = datetime(2026, 11, 17, 10, 0)


def proximo(dia_semana: int) -> str:
    """Fecha ISO del próximo día de la semana (0 = lunes) a partir de AHORA (sin contar hoy)."""
    d = AHORA.date() + timedelta(days=1)
    while d.weekday() != dia_semana:
        d += timedelta(days=1)
    return d.isoformat()


@pytest.fixture
def restaurante():
    # Las pruebas usan siempre el ejemplo genérico, así no dependen del restaurante configurado.
    return cargar_restaurante(Path(__file__).resolve().parent.parent / "ejemplos" / "casa-ejemplo.yaml")


@pytest.fixture
def reservas(restaurante, tmp_path, monkeypatch):
    monkeypatch.setattr(Reservas, "ahora", lambda self: AHORA)
    return Reservas(restaurante, tmp_path / "prueba.db")


assert date(2026, 11, 17).weekday() == 1  # martes
