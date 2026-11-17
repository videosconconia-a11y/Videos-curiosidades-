import base64

import pytest
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

from agente_voz.agente import Agente
from agente_voz.app import Estado, crear_app
from agente_voz.config import Ajustes
from conftest import proximo
from falso_claude import FalsoClaude, herramienta, texto


@pytest.fixture
def montar(reservas, monkeypatch, tmp_path):
    def _montar(guion, retraso=0.0, **ajustes):
        monkeypatch.setenv("BASE_DATOS", str(tmp_path / "prueba.db"))
        a = Ajustes()
        a.twilio_auth_token = ajustes.get("token", "")
        a.panel_clave = "secreta"
        a.url_publica = "http://testserver"
        estado = Estado.__new__(Estado)
        estado.ajustes = a
        estado.restaurante = reservas.r
        estado.reservas = reservas
        estado.agente = Agente(reservas.r, reservas, a, cliente=FalsoClaude(guion, retraso=retraso))
        estado.pendientes, estado.esperas, estado.silencios = {}, {}, {}
        return TestClient(crear_app(estado))
    return _montar


def test_llamada_entrante_saluda_y_escucha(montar):
    with montar([]) as c:
        r = c.post("/voz/entrante", data={"CallSid": "CA1", "From": "+34600111222"})
    assert r.status_code == 200
    assert "<Gather" in r.text and 'language="es-ES"' in r.text and "asistente" in r.text
    assert "inteligencia artificial" in r.text


def test_turno_normal(montar):
    with montar([texto("Claro, ¿para cuántas personas?")]) as c:
        c.post("/voz/entrante", data={"CallSid": "CA1", "From": "+34600111222"})
        r = c.post("/voz/respuesta", data={"CallSid": "CA1", "From": "+34600111222", "SpeechResult": "Quiero reservar"})
    assert "¿para cuántas personas?" in r.text and "<Gather" in r.text


def test_turno_lento_dice_un_momento_y_continua(montar, monkeypatch):
    import agente_voz.app as modulo
    monkeypatch.setattr(modulo, "ESPERA_DIRECTA", 0.05)
    with montar([texto("Ya está.")], retraso=0.3) as c:
        r = c.post("/voz/respuesta", data={"CallSid": "CA2", "From": "", "SpeechResult": "hola"})
        assert "Un momento" in r.text and "<Redirect" in r.text
        r = c.post("/voz/continuar", data={"CallSid": "CA2"})
        assert "Ya está." in r.text


def test_silencio(montar):
    with montar([]) as c:
        datos = {"CallSid": "CA3", "From": "", "SpeechResult": ""}
        assert "¿Sigue ahí?" in c.post("/voz/respuesta", data=datos).text
        c.post("/voz/respuesta", data=datos)
        assert "<Hangup" in c.post("/voz/respuesta", data=datos).text


def test_transferencia(montar):
    with montar([herramienta("transferir_llamada", {"motivo": "boda"}), texto("Le paso.")]) as c:
        r = c.post("/voz/respuesta", data={"CallSid": "CA4", "From": "", "SpeechResult": "una boda"})
    assert "<Dial" in r.text and "+34600000000" in r.text


def test_firma_twilio(montar):
    token = "abc123"
    with montar([], token=token) as c:
        datos = {"CallSid": "CA5", "From": "+34600111222"}
        assert c.post("/voz/entrante", data=datos).status_code == 403
        firma = RequestValidator(token).compute_signature("http://testserver/voz/entrante", datos)
        assert c.post("/voz/entrante", data=datos, headers={"X-Twilio-Signature": firma}).status_code == 200


def test_panel(montar, reservas):
    viernes = proximo(4)
    reservas.crear_reserva(viernes, "21:00", 2, "Laura <b>", "600111222")
    auth = {"Authorization": "Basic " + base64.b64encode(b"admin:secreta").decode()}
    with montar([]) as c:
        assert c.get("/panel").status_code == 401
        r = c.get(f"/panel?fecha={viernes}", headers=auth)
        assert r.status_code == 200 and "Laura &lt;b&gt;" in r.text  # HTML escapado
        r = c.post("/panel/reservar", headers=auth, follow_redirects=False, data={
            "fecha": viernes, "hora": "14:00", "personas": "4", "nombre": "Ana", "telefono": "611222333"})
        assert r.status_code == 303 and "err" not in r.headers["location"]
        codigo = reservas.buscar_reservas(telefono="611222333")[0]["codigo"]
        c.post("/panel/cancelar", headers=auth, data={"codigo": codigo, "fecha": viernes})
        assert reservas.buscar_reservas(telefono="611222333") == []
        assert c.get("/panel/llamadas", headers=auth).status_code == 200
