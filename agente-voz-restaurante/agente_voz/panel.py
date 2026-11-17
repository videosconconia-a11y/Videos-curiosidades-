"""Panel web sencillo para el personal: ver reservas del día, añadir, cancelar y leer llamadas.

Protegido con usuario y clave (PANEL_USUARIO / PANEL_CLAVE). Ábrelo en /panel.
"""
from __future__ import annotations

from datetime import date, timedelta
from html import escape
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .config import DIAS_BONITOS, MESES
from .reservas import ErrorReserva

ESTILO = """
:root{--fondo:#f7f5f2;--tarjeta:#fff;--texto:#1f1d1a;--suave:#6b665e;--borde:#e4dfd7;--acento:#8a3b12;--ok:#2f6b3a;--mal:#a12a2a}
@media (prefers-color-scheme:dark){:root{--fondo:#171614;--tarjeta:#211f1c;--texto:#eeeae4;--suave:#a39d93;--borde:#38342e;--acento:#e08a5a;--ok:#7cc48a;--mal:#ef8a8a}}
*{box-sizing:border-box}body{margin:0;background:var(--fondo);color:var(--texto);font:16px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:16px;border-bottom:1px solid var(--borde);display:flex;gap:16px;align-items:center;flex-wrap:wrap}
header h1{font-size:20px;margin:0;flex:1}a{color:var(--acento)}main{padding:16px;max-width:1000px;margin:auto}
.tarjeta{background:var(--tarjeta);border:1px solid var(--borde);border-radius:10px;padding:16px;margin-bottom:16px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px 6px;border-bottom:1px solid var(--borde);vertical-align:top}
th{font-size:13px;color:var(--suave);font-weight:600}.cancelada td{opacity:.45;text-decoration:line-through}
.nav{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.cifras{display:flex;gap:24px;flex-wrap:wrap}.cifras b{font-size:24px;display:block}
input,select,button{font:inherit;padding:6px 8px;border:1px solid var(--borde);border-radius:6px;background:var(--fondo);color:var(--texto)}
button{background:var(--acento);color:#fff;border:0;cursor:pointer}button.sec{background:transparent;color:var(--mal);border:1px solid var(--mal)}
form.fila{display:flex;gap:8px;flex-wrap:wrap;align-items:end}form.fila label{display:flex;flex-direction:column;font-size:13px;color:var(--suave)}
.error{color:var(--mal);font-weight:600}.ok{color:var(--ok);font-weight:600}.tabla{overflow-x:auto}
.burbuja{margin:4px 0}.burbuja b{color:var(--suave);font-weight:600}
"""


def _pagina(titulo: str, cuerpo: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(titulo)}</title>
<style>{ESTILO}</style></head><body><header><h1>{escape(titulo)}</h1>
<a href="/panel">Reservas</a><a href="/panel/llamadas">Llamadas</a></header><main>{cuerpo}</main></body></html>""")


def _fecha_larga(d: date) -> str:
    return f"{DIAS_BONITOS[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]} de {d.year}"


def registrar(app: FastAPI, autorizado) -> None:
    @app.get("/panel", response_class=HTMLResponse)
    async def reservas_dia(fecha: str | None = None, msg: str = "", err: str = "", e=Depends(autorizado)):
        try:
            d = date.fromisoformat(fecha) if fecha else e.reservas.ahora().date()
        except ValueError:
            d = e.reservas.ahora().date()
        filas = e.reservas.listar(d.isoformat())
        activas = [f for f in filas if f["estado"] == "confirmada"]
        comensales = sum(f["personas"] for f in activas)
        por_tel = sum(1 for f in activas if f["origen"] == "telefono")
        cuerpo = [f"""<div class="tarjeta nav">
<a href="/panel?fecha={(d - timedelta(days=1)).isoformat()}">← Anterior</a>
<form method="get" action="/panel"><input type="date" name="fecha" value="{d.isoformat()}"> <button>Ver</button></form>
<a href="/panel?fecha={(d + timedelta(days=1)).isoformat()}">Siguiente →</a></div>"""]
        if msg:
            cuerpo.append(f'<p class="ok">{escape(msg)}</p>')
        if err:
            cuerpo.append(f'<p class="error">{escape(err)}</p>')
        cerrado = "" if e.reservas.turnos_del_dia(d) else " · <span class='error'>Cerrado</span>"
        cuerpo.append(f"""<div class="tarjeta"><h2 style="margin-top:0">{_fecha_larga(d)}{cerrado}</h2>
<div class="cifras"><div><b>{len(activas)}</b>reservas</div><div><b>{comensales}</b>comensales</div>
<div><b>{por_tel}</b>hechas por el asistente</div></div></div>""")
        tabla = ["<div class='tarjeta tabla'><table><tr><th>Hora</th><th>Pers.</th><th>Nombre</th><th>Teléfono</th>"
                 "<th>Mesa</th><th>Notas</th><th>Código</th><th></th></tr>"]
        for f in filas:
            boton = ""
            if f["estado"] == "confirmada":
                boton = (f"<form method='post' action='/panel/cancelar' onsubmit=\"return confirm('¿Cancelar esta reserva?')\">"
                         f"<input type='hidden' name='codigo' value='{escape(f['codigo'])}'>"
                         f"<input type='hidden' name='fecha' value='{d.isoformat()}'><button class='sec'>Cancelar</button></form>")
            origen = " 📞" if f["origen"] == "telefono" else ""
            tabla.append(
                f"<tr class='{escape(f['estado'])}'><td>{escape(f['hora'])}</td><td>{f['personas']}</td>"
                f"<td>{escape(f['nombre'])}{origen}</td><td><a href='tel:{escape(f['telefono'])}'>{escape(f['telefono'])}</a></td>"
                f"<td>{escape(f['mesa'])} ({escape(f['zona'])})</td><td>{escape(f['notas'])}</td>"
                f"<td>{escape(f['codigo'])}</td><td>{boton}</td></tr>")
        if not filas:
            tabla.append("<tr><td colspan='8'>No hay reservas este día.</td></tr>")
        tabla.append("</table></div>")
        cuerpo.append("".join(tabla))
        zonas = "".join(f"<option value='{escape(z)}'>{escape(z)}</option>" for z in e.restaurante.zonas)
        cuerpo.append(f"""<div class="tarjeta"><h3 style="margin-top:0">Añadir reserva manual</h3>
<form class="fila" method="post" action="/panel/reservar">
<label>Fecha<input type="date" name="fecha" value="{d.isoformat()}" required></label>
<label>Hora<input type="time" name="hora" step="900" required></label>
<label>Personas<input type="number" name="personas" min="1" max="30" value="2" required style="width:80px"></label>
<label>Nombre<input name="nombre" required></label>
<label>Teléfono<input name="telefono" required></label>
<label>Zona<select name="zona"><option value="">Cualquiera</option>{zonas}</select></label>
<label>Notas<input name="notas"></label><button>Reservar</button></form></div>""")
        return _pagina(f"Reservas · {e.restaurante.nombre}", "".join(cuerpo))

    @app.post("/panel/cancelar")
    async def cancelar(codigo: str = Form(...), fecha: str = Form(""), e=Depends(autorizado)):
        try:
            e.reservas.cancelar_reserva(codigo)
            return RedirectResponse(f"/panel?fecha={fecha}&msg={quote(f'Reserva {codigo} cancelada')}", status_code=303)
        except ErrorReserva as ex:
            return RedirectResponse(f"/panel?fecha={fecha}&err={quote(str(ex))}", status_code=303)

    @app.post("/panel/reservar")
    async def reservar(fecha: str = Form(...), hora: str = Form(...), personas: int = Form(...),
                       nombre: str = Form(...), telefono: str = Form(...), zona: str = Form(""),
                       notas: str = Form(""), e=Depends(autorizado)):
        try:
            r = e.reservas.crear_reserva(fecha, hora, personas, nombre, telefono, notas, zona or None, origen="panel")
            return RedirectResponse(f"/panel?fecha={fecha}&msg={quote(f"Reserva creada: código {r['codigo']}, mesa {r['mesa']}")}",
                                    status_code=303)
        except ErrorReserva as ex:
            return RedirectResponse(f"/panel?fecha={fecha}&err={quote(str(ex))}", status_code=303)

    @app.get("/panel/llamadas", response_class=HTMLResponse)
    async def llamadas(e=Depends(autorizado)):
        partes = []
        for ll in e.reservas.listar_llamadas(100):
            conversacion = "".join(
                f"<div class='burbuja'><b>{'Cliente' if t['quien'] == 'cliente' else 'Asistente'}:</b> {escape(t['texto'])}</div>"
                for t in ll["transcripcion"])
            partes.append(f"""<details class="tarjeta"><summary>{escape(ll['inicio'].replace('T', ' '))} ·
{escape(ll['telefono'] or 'oculto')} · <b>{escape(ll['resultado'] or 'sin resultado')}</b></summary>
{conversacion or '<p>Sin conversación.</p>'}</details>""")
        return _pagina("Llamadas recientes", "".join(partes) or "<p>Todavía no hay llamadas.</p>")
