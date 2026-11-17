import asyncio

from agente_voz.agente import Agente, construir_sistema, limpiar_para_voz
from agente_voz.config import Ajustes
from conftest import proximo
from falso_claude import FalsoClaude, Mensaje, herramienta, texto

VIERNES = proximo(4)


def crear(restaurante, reservas, guion, **kw):
    cliente = FalsoClaude(guion)
    return Agente(restaurante, reservas, Ajustes(), cliente=cliente, **kw), cliente


def test_reserva_completa(restaurante, reservas):
    avisos = []
    agente, cliente = crear(restaurante, reservas, [
        herramienta("consultar_disponibilidad", {"fecha": VIERNES, "personas": 2, "hora": "21:30"}),
        texto("Sí, tengo mesa a las nueve y media. ¿A nombre de quién?"),
        herramienta("crear_reserva", {"fecha": VIERNES, "hora": "21:30", "personas": 2,
                                      "nombre": "Laura", "telefono": "+34600111222"}, "t2"),
        texto("**Hecho**. Su código es uno, dos, tres."),
    ], al_reservar=lambda r, tipo: avisos.append((r["codigo"], tipo)))

    r1 = asyncio.run(agente.responder("CA1", "Quiero mesa para dos el viernes a las nueve y media", "+34600111222"))
    assert r1.accion == "seguir" and "nueve y media" in r1.texto

    # El primer mensaje lleva el contexto con la fecha y el teléfono
    primero = cliente.messages.peticiones[0]["messages"][0]["content"]
    assert "Contexto de la llamada" in primero and "+34600111222" in primero and VIERNES in primero
    # Parámetros de la API
    p = cliente.messages.peticiones[0]
    assert p["model"] == "claude-opus-5-5" and p["output_config"] == {"effort": "low"}
    assert p["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in p["betas"]

    r2 = asyncio.run(agente.responder("CA1", "A nombre de Laura, sí, confírmela", "+34600111222"))
    assert r2.texto == "Hecho. Su código es uno, dos, tres."  # sin asteriscos
    assert r2.resultado == "reserva"
    guardadas = reservas.buscar_reservas(telefono="600111222")
    assert len(guardadas) == 1 and guardadas[0]["hora"] == "21:30"
    assert avisos == [(guardadas[0]["codigo"], "creada")]

    llamada = reservas.cargar_llamada("CA1")
    assert [t["quien"] for t in llamada["transcripcion"]] == ["asistente", "cliente", "asistente", "cliente", "asistente"]
    # Historial válido: user, assistant(tool_use), user(tool_result), assistant, user, ...
    roles = [m["role"] for m in llamada["mensajes"]]
    assert roles == ["user", "assistant", "user", "assistant", "user", "assistant", "user", "assistant"]


def test_error_de_herramienta_vuelve_a_claude(restaurante, reservas):
    agente, cliente = crear(restaurante, reservas, [
        herramienta("consultar_disponibilidad", {"fecha": proximo(0), "personas": 2}),
        texto("Los lunes cerramos. ¿Le viene bien el martes?"),
    ])
    r = asyncio.run(agente.responder("CA2", "Mesa el lunes", "600111222"))
    assert "lunes" in r.texto
    resultado = cliente.messages.peticiones[1]["messages"][-1]["content"][0]
    assert resultado["is_error"] is True and "cerrado" in resultado["content"]


def test_colgar_y_transferir(restaurante, reservas):
    agente, _ = crear(restaurante, reservas, [
        herramienta("colgar", {"motivo": "se despide"}), texto("Gracias por llamar, hasta luego."),
        herramienta("transferir_llamada", {"motivo": "evento"}, "t9"), texto("Le paso con el encargado."),
    ])
    r = asyncio.run(agente.responder("CA3", "Nada más, gracias", ""))
    assert r.accion == "colgar"
    r = asyncio.run(agente.responder("CA4", "Quiero organizar una boda", ""))
    assert r.accion == "transferir" and r.resultado == "transferida"


def test_fallo_de_la_api_pasa_con_persona_y_no_rompe_historial(restaurante, reservas):
    agente, _ = crear(restaurante, reservas, [RuntimeError("caída"), texto("Dígame.")])
    r = asyncio.run(agente.responder("CA5", "Hola", ""))
    assert r.accion == "transferir" and r.resultado == "error"
    assert reservas.cargar_llamada("CA5")["mensajes"] == []


def test_rechazo(restaurante, reservas):
    agente, _ = crear(restaurante, reservas, [Mensaje([], "refusal")])
    r = asyncio.run(agente.responder("CA6", "algo raro", ""))
    assert r.accion == "transferir"
    assert reservas.cargar_llamada("CA6")["mensajes"] == []


def test_contexto_avisa_de_reservas_existentes(restaurante, reservas):
    reservas.crear_reserva(VIERNES, "14:00", 3, "Pepe", "600999888")
    agente, cliente = crear(restaurante, reservas, [texto("Dígame.")])
    asyncio.run(agente.responder("CA7", "Hola", "+34600999888"))
    assert "ya tiene reservas" in cliente.messages.peticiones[0]["messages"][0]["content"]


def test_sistema_y_limpieza(restaurante):
    s = construir_sistema(restaurante)
    assert restaurante.nombre in s and "lunes: cerrado" in s and "Calle Mayor" in s
    assert limpiar_para_voz("- **Hola**\n- que tal") == "Hola que tal"
