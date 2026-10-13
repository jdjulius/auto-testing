"""Genera un reporte PDF de una corrida a partir de los CSV de escenarios.

Lo usa el plugin al final de cada corrida y también se puede ejecutar a mano
para regenerar el reporte de la última corrida registrada::

    python -m auto_testing.reporte_pdf [--escenarios-csv ...] [--ejecuciones-csv ...] [--salida ...]
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from auto_testing.registro import Ejecucion, Escenario

ESTADOS = ["EXITOSO", "FALLIDO", "ERROR", "XFAIL", "XPASS", "OMITIDO"]
ETIQUETAS = {
    "EXITOSO": "Exitoso",
    "FALLIDO": "Fallido",
    "ERROR": "Error",
    "XFAIL": "Defecto conocido",
    "XPASS": "No reproducido",
    "OMITIDO": "Omitido",
}
COLORES = {
    "EXITOSO": colors.HexColor("#1e7f4f"),
    "FALLIDO": colors.HexColor("#c0392b"),
    "ERROR": colors.HexColor("#8e44ad"),
    "XFAIL": colors.HexColor("#d68910"),
    "XPASS": colors.HexColor("#2471a3"),
    "OMITIDO": colors.HexColor("#7f8c8d"),
}
OSCURO = colors.HexColor("#132322")
GRIS = colors.HexColor("#eef1f1")

_estilos = getSampleStyleSheet()
TITULO = ParagraphStyle("titulo", parent=_estilos["Title"], fontSize=20, textColor=OSCURO)
SUBTITULO = ParagraphStyle("subtitulo", parent=_estilos["Heading2"], textColor=OSCURO, spaceBefore=12)
NORMAL = ParagraphStyle("normal", parent=_estilos["BodyText"], fontSize=9, leading=11)
CELDA = ParagraphStyle("celda", parent=NORMAL, fontSize=7.5, leading=9)
CIFRA = ParagraphStyle("cifra", parent=NORMAL, fontSize=18, leading=22, alignment=TA_CENTER)
ROTULO = ParagraphStyle("rotulo", parent=NORMAL, fontSize=8, alignment=TA_CENTER,
                        textColor=colors.HexColor("#555555"))


def _p(texto, estilo=CELDA) -> Paragraph:
    return Paragraph(escape(str(texto)), estilo)


def _estado(estado: str) -> Paragraph:
    color = COLORES.get(estado, colors.black).hexval()[2:]
    return Paragraph(f'<font color="#{color}"><b>{ETIQUETAS.get(estado, estado)}</b></font>', CELDA)


def _tabla(filas, anchos, cabecera_color=OSCURO) -> Table:
    tabla = Table(filas, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), cabecera_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d0d0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tabla


def generar_pdf(
    salida: Path,
    escenarios: dict[str, Escenario],
    ejecuciones: list[Ejecucion],
    *,
    titulo: str = "Reporte de pruebas automatizadas",
    aplicacion: str = "",
) -> Path:
    """Escribe el PDF de una corrida. ``escenarios`` va indexado por nodeid."""
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    ejecuciones = sorted(ejecuciones, key=lambda e: e.escenario_id)
    conteo = Counter(e.estado for e in ejecuciones)
    total = len(ejecuciones)
    run_id = ejecuciones[0].run_id if ejecuciones else "-"
    fechas = sorted(e.fecha for e in ejecuciones)
    duracion = sum(float(e.duracion_s) for e in ejecuciones)
    # Un defecto conocido que se reproduce es el resultado esperado.
    correctos = conteo["EXITOSO"] + conteo["XFAIL"]
    porcentaje = 100 * correctos / total if total else 0

    doc = SimpleDocTemplate(
        str(salida), pagesize=landscape(A4), title=titulo,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    ancho = doc.width
    historia = [Paragraph(escape(titulo), TITULO)]
    datos = [f"<b>Corrida:</b> {escape(run_id)}"]
    if aplicacion:
        datos.append(f"<b>Aplicación:</b> {escape(aplicacion)}")
    if fechas:
        datos.append(f"<b>Inicio:</b> {fechas[0].replace('T', ' ')}")
    datos.append(f"<b>Duración acumulada:</b> {duracion:.1f} s")
    historia += [Paragraph(" &nbsp;·&nbsp; ".join(datos), NORMAL), Spacer(1, 10)]

    # Resumen en tarjetas
    tarjetas = [("Escenarios", total, OSCURO), ("Resultado esperado", f"{porcentaje:.0f}%", OSCURO)]
    tarjetas += [(ETIQUETAS[e], conteo[e], COLORES[e]) for e in ESTADOS if conteo[e]]
    celdas = [[
        [Paragraph(f'<font color="#{c.hexval()[2:]}"><b>{v}</b></font>', CIFRA), Paragraph(r, ROTULO)]
        for r, v, c in tarjetas
    ]]
    resumen = Table(celdas, colWidths=[ancho / len(tarjetas)] * len(tarjetas))
    resumen.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8d0d0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8d0d0")),
        ("BACKGROUND", (0, 0), (-1, -1), GRIS),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    historia += [resumen, Spacer(1, 4), Paragraph(
        "<i>Resultado esperado = exitosos + defectos conocidos reproducidos. "
        "'Defecto conocido' es una falla ya identificada de la aplicación (xfail).</i>", NORMAL)]

    # Por módulo
    por_modulo: dict[str, Counter] = defaultdict(Counter)
    for e in ejecuciones:
        esc = escenarios.get(e.nodeid)
        por_modulo[esc.modulo if esc else "-"][e.estado] += 1
    filas = [["Módulo", "Total"] + [ETIQUETAS[e] for e in ESTADOS]]
    for modulo in sorted(por_modulo):
        c = por_modulo[modulo]
        filas.append([modulo, sum(c.values())] + [c[e] or "" for e in ESTADOS])
    filas.append(["Total", total] + [conteo[e] or "" for e in ESTADOS])
    tabla_modulos = _tabla(filas, [5 * cm, 2 * cm] + [(ancho - 7 * cm) / len(ESTADOS)] * len(ESTADOS))
    tabla_modulos.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
    ]))
    historia += [KeepTogether([Paragraph("Resumen por módulo", SUBTITULO), tabla_modulos])]

    # Fallas que requieren atención
    atencion = [e for e in ejecuciones if e.estado in ("FALLIDO", "ERROR", "XPASS")]
    historia.append(Paragraph("Fallas que requieren atención", SUBTITULO))
    if atencion:
        filas = [["ID", "Escenario", "Estado", "Detalle"]]
        for e in atencion:
            esc = escenarios.get(e.nodeid)
            filas.append([_p(e.escenario_id), _p(esc.descripcion if esc else e.nodeid),
                          _estado(e.estado), _p(e.mensaje or "-")])
        historia.append(_tabla(filas, [2 * cm, 8 * cm, 3 * cm, ancho - 13 * cm],
                               cabecera_color=COLORES["FALLIDO"]))
    else:
        historia.append(Paragraph("No hubo fallas inesperadas en esta corrida.", NORMAL))

    # Detalle de todos los escenarios
    filas = [["ID", "Módulo", "Funcionalidad", "Escenario", "Resultado esperado",
              "Prioridad", "Estado", "Duración", "Observación"]]
    for e in ejecuciones:
        esc = escenarios.get(e.nodeid)
        filas.append([
            _p(e.escenario_id),
            _p(esc.modulo if esc else ""),
            _p(esc.funcionalidad if esc else ""),
            _p(esc.descripcion if esc else e.nodeid),
            _p(esc.resultado_esperado if esc else ""),
            _p(esc.prioridad if esc else ""),
            _estado(e.estado),
            _p(f"{float(e.duracion_s):.2f} s"),
            _p(e.mensaje),
        ])
    anchos = [1.7, 2.2, 3.0, 5.0, 5.0, 1.6, 2.6, 1.6]
    anchos = [a * cm for a in anchos] + [ancho - sum(anchos) * cm]
    historia += [Paragraph("Detalle de escenarios", SUBTITULO), _tabla(filas, anchos)]

    def pie(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(doc.leftMargin, 0.8 * cm, f"auto-testing · {run_id}")
        canvas.drawRightString(doc.leftMargin + ancho, 0.8 * cm, f"Página {documento.page}")
        canvas.restoreState()

    doc.build(historia, onFirstPage=pie, onLaterPages=pie)
    return salida


# --------------------------------------------------------------------- CLI
def _leer_ultima_corrida(ruta: Path) -> list[Ejecucion]:
    with Path(ruta).open(newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        return []
    ultima = filas[-1]["run_id"]
    return [Ejecucion(**f) for f in filas if f["run_id"] == ultima]


def main(argv: list[str] | None = None) -> None:
    from auto_testing.registro import RegistroEscenarios

    parser = argparse.ArgumentParser(description="Genera el PDF de la última corrida registrada")
    parser.add_argument("--escenarios-csv", default="reportes/escenarios.csv")
    parser.add_argument("--ejecuciones-csv", default="reportes/ejecuciones.csv")
    parser.add_argument("--salida", default="reportes/reporte.pdf")
    parser.add_argument("--aplicacion", default="")
    args = parser.parse_args(argv)

    registro = RegistroEscenarios(Path(args.escenarios_csv), Path(args.ejecuciones_csv))
    ejecuciones = _leer_ultima_corrida(Path(args.ejecuciones_csv))
    if not ejecuciones:
        raise SystemExit("No hay ejecuciones registradas")
    print(generar_pdf(Path(args.salida), registro.escenarios, ejecuciones, aplicacion=args.aplicacion))


if __name__ == "__main__":
    main()
