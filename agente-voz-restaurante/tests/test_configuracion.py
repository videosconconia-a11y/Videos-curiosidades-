"""Comprueba que el restaurante configurado (restaurante.yaml) se carga y es coherente."""
from agente_voz.agente import construir_sistema
from agente_voz.config import cargar_restaurante
from agente_voz.reservas import Reservas
from conftest import proximo


def test_restaurante_configurado_es_valido(tmp_path, monkeypatch):
    from conftest import AHORA
    r = cargar_restaurante()
    assert r.nombre and r.direccion and r.mesas
    assert any(r.horario.values()), "no hay ningún día abierto"
    for m in r.mesas:
        assert 1 <= m.min <= m.max
    # Todos los tamaños de grupo hasta el máximo por teléfono tienen alguna mesa
    for personas in range(1, r.max_personas_telefono + 1):
        assert any(m.min <= personas <= m.max for m in r.mesas), f"no hay mesa para {personas}"
    monkeypatch.setattr(Reservas, "ahora", lambda self: AHORA)
    res = Reservas(r, tmp_path / "x.db")
    d = res.consultar_disponibilidad(proximo(4), 2)
    assert d["horas_libres"]
    assert r.nombre in construir_sistema(r)
