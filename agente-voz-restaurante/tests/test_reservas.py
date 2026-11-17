import threading

import pytest

from agente_voz.reservas import ErrorReserva, normalizar_telefono
from conftest import proximo

VIERNES = proximo(4)
LUNES = proximo(0)


def test_disponibilidad_basica(reservas):
    d = reservas.consultar_disponibilidad(VIERNES, 2, "21:30")
    assert d["hora_pedida_disponible"] is True
    assert "13:00" in d["horas_libres"] and "23:15" in d["horas_libres"]
    assert "17:00" not in d["horas_libres"]


def test_mesa_mas_ajustada(reservas):
    r = reservas.crear_reserva(VIERNES, "21:00", 2, "Laura", "600111222")
    assert r["mesa"] in ("S1", "S2", "T1")  # mesas de 2, no una de 4
    assert r["telefono"] == "+34600111222"
    assert len(r["codigo"]) == 5


def test_se_llena_y_ofrece_alternativas(reservas):
    # Mesas de terraza para 4: T2 y T3. Las llenamos a las 21:00.
    reservas.crear_reserva(VIERNES, "21:00", 4, "A", "600000001", zona="terraza")
    reservas.crear_reserva(VIERNES, "21:00", 4, "B", "600000002", zona="terraza")
    d = reservas.consultar_disponibilidad(VIERNES, 4, "21:00", zona="terraza")
    assert d["hora_pedida_disponible"] is False
    assert d["alternativas_mas_cercanas"]
    # 21:00 + 105 min = 22:45 → a las 22:45 vuelve a haber terraza
    assert "22:45" in d["horas_libres"] and "22:30" not in d["horas_libres"]
    assert "21:00" in d["horas_libres_en_otras_zonas"]["salon"]
    with pytest.raises(ErrorReserva):
        reservas.crear_reserva(VIERNES, "21:30", 4, "C", "600000003", zona="terraza")


def test_grupo_usa_mesas_combinadas(reservas):
    r = reservas.crear_reserva(VIERNES, "14:00", 8, "Grupo", "600000004")
    assert "+" in r["mesa"]
    fisicas = set(r["mesas_fisicas"].split(","))
    # Esas mesas físicas quedan ocupadas para mesas sueltas a la misma hora
    otra = reservas.crear_reserva(VIERNES, "14:00", 4, "Otra", "600000005", zona="salon")
    assert otra["mesa"] not in fisicas


def test_validaciones(reservas):
    with pytest.raises(ErrorReserva, match="cerrado"):
        reservas.consultar_disponibilidad(LUNES, 2)
    with pytest.raises(ErrorReserva, match="pasado"):
        reservas.consultar_disponibilidad("2026-11-01", 2)
    with pytest.raises(ErrorReserva, match="encargado"):
        reservas.consultar_disponibilidad(VIERNES, 15)
    with pytest.raises(ErrorReserva, match="antelación"):
        reservas.consultar_disponibilidad("2027-06-01", 2)
    with pytest.raises(ErrorReserva):
        reservas.crear_reserva(VIERNES, "18:00", 2, "X", "600000006")  # fuera de turno
    with pytest.raises(ErrorReserva, match="Navidad|cerrado"):
        reservas.consultar_disponibilidad("2026-12-25", 2)
    # Hoy (martes) a las 10:00: la comida de hoy aún se puede reservar, pero no dentro de 30 min
    hoy = reservas.consultar_disponibilidad("2026-11-17", 2)
    assert hoy["horas_libres"][0] == "13:00"


def test_no_duplica_reserva_del_mismo_telefono(reservas):
    reservas.crear_reserva(VIERNES, "21:00", 2, "Laura", "600111222")
    with pytest.raises(ErrorReserva, match="ya tiene una reserva"):
        reservas.crear_reserva(VIERNES, "21:30", 2, "Laura", "+34 600 111 222")


def test_buscar_modificar_cancelar(reservas):
    r = reservas.crear_reserva(VIERNES, "21:00", 2, "Laura", "600111222", notas="celiaca")
    assert [x["codigo"] for x in reservas.buscar_reservas(telefono="600 111 222")] == [r["codigo"]]
    m = reservas.modificar_reserva(r["codigo"], hora="22:00", personas=3)
    assert (m["hora"], m["personas"], m["notas"]) == ("22:00", 3, "celiaca")
    c = reservas.cancelar_reserva(r["codigo"])
    assert c["estado"] == "cancelada"
    assert reservas.buscar_reservas(telefono="600111222") == []
    with pytest.raises(ErrorReserva):
        reservas.cancelar_reserva(r["codigo"])


def test_modificar_no_choca_consigo_misma(reservas):
    # Ocupamos todas las mesas de 4 del salón menos la de la reserva que se modifica
    r = reservas.crear_reserva(VIERNES, "21:00", 4, "Yo", "600000010", zona="salon")
    m = reservas.modificar_reserva(r["codigo"], hora="21:15")
    assert m["hora"] == "21:15"


def test_concurrencia_no_reserva_dos_veces_la_misma_mesa(reservas):
    # Solo dejamos libre una mesa para 6 a las 21:00 en el salón
    for i, z in enumerate(["salon", "salon", "salon"]):
        reservas.crear_reserva(VIERNES, "21:00", 4, f"P{i}", f"60000002{i}", zona=z)
    resultados = []

    def reservar(i):
        try:
            resultados.append(reservas.crear_reserva(VIERNES, "21:00", 5, f"C{i}", f"60000003{i}", zona="salon"))
        except ErrorReserva as e:
            resultados.append(e)

    hilos = [threading.Thread(target=reservar, args=(i,)) for i in range(6)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    ok = [x for x in resultados if isinstance(x, dict)]
    assert len(ok) == 1  # solo queda la mesa S6
    fisicas = [set(x["mesas_fisicas"].split(",")) for x in ok]
    for i in range(len(fisicas)):
        for j in range(i + 1, len(fisicas)):
            assert not (fisicas[i] & fisicas[j]), "dos reservas comparten mesa"


def test_normalizar_telefono():
    assert normalizar_telefono("600 11 22 33") == "+34600112233"
    assert normalizar_telefono("0034600112233") == "+34600112233"
    assert normalizar_telefono("+44 7700 900123") == "+447700900123"
    assert normalizar_telefono("") == ""
