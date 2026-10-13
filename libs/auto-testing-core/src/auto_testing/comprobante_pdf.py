"""PDF de comprobante de una compra realizada durante las pruebas."""

from __future__ import annotations

import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OSCURO = colors.HexColor("#132322")
GRIS = colors.HexColor("#eef1f1")
VERDE = colors.HexColor("#1e7f4f")

_estilos = getSampleStyleSheet()
TITULO = ParagraphStyle("titulo", parent=_estilos["Title"], textColor=OSCURO)
SUBTITULO = ParagraphStyle("subtitulo", parent=_estilos["Heading3"], textColor=OSCURO)
NORMAL = ParagraphStyle("normal", parent=_estilos["BodyText"], fontSize=9.5, leading=12)


def _dinero(valor: float) -> str:
    return f"${valor:,.2f}"


def generar_comprobante(
    salida: Path,
    *,
    lineas: list[tuple[str, int, float]],
    pago: str,
    envio: str,
    subtotal: float,
    impuesto: float,
    total: float,
    comprador: dict[str, str],
    confirmacion: str,
    datos: dict[str, str] | None = None,
    capturas: list[tuple[str, bytes]] | None = None,
) -> Path:
    """Escribe el comprobante. ``lineas`` son (producto, cantidad, precio unitario);
    ``capturas`` son (título, PNG) que se anexan al final."""
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(salida), pagesize=A4, title="Comprobante de compra",
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
    )
    ancho = doc.width
    h = [Paragraph("Comprobante de compra", TITULO)]
    h.append(Paragraph(f'<font color="#{VERDE.hexval()[2:]}"><b>{escape(confirmacion)}</b></font>',
                       ParagraphStyle("ok", parent=NORMAL, fontSize=12, alignment=1)))
    h.append(Spacer(1, 12))

    info = [[Paragraph("<b>Comprador</b>", NORMAL),
             Paragraph(escape(f"{comprador.get('nombre', '')} {comprador.get('apellido', '')}"), NORMAL)],
            [Paragraph("<b>Código postal</b>", NORMAL), Paragraph(escape(comprador.get("codigo_postal", "")), NORMAL)],
            [Paragraph("<b>Medio de pago</b>", NORMAL), Paragraph(escape(pago), NORMAL)],
            [Paragraph("<b>Envío</b>", NORMAL), Paragraph(escape(envio), NORMAL)]]
    for clave, valor in (datos or {}).items():
        info.append([Paragraph(f"<b>{escape(clave)}</b>", NORMAL), Paragraph(escape(valor), NORMAL)])
    tabla_info = Table(info, colWidths=[4.5 * cm, ancho - 4.5 * cm])
    tabla_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d0d0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    h += [tabla_info, Spacer(1, 14), Paragraph("Productos", SUBTITULO)]

    filas = [["Producto", "Cantidad", "Precio unitario", "Importe"]]
    for nombre, cantidad, precio in lineas:
        filas.append([Paragraph(escape(nombre), NORMAL), cantidad, _dinero(precio), _dinero(cantidad * precio)])
    filas += [
        ["", "", "Subtotal", _dinero(subtotal)],
        ["", "", "Impuesto", _dinero(impuesto)],
        ["", "", "Total", _dinero(total)],
    ]
    n = len(lineas)
    productos = Table(filas, colWidths=[ancho - 9 * cm, 2.5 * cm, 3.5 * cm, 3 * cm], repeatRows=1)
    productos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, n), [colors.white, GRIS]),
        ("LINEABOVE", (2, n + 1), (-1, n + 1), 0.5, OSCURO),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (2, -1), (-1, -1), 1, OSCURO),
        ("GRID", (0, 0), (-1, n), 0.25, colors.HexColor("#c8d0d0")),
    ]))
    h.append(productos)

    for titulo, png in capturas or []:
        imagen = Image(io.BytesIO(png))
        escala = min(ancho / imagen.imageWidth, 15 * cm / imagen.imageHeight)
        imagen.drawWidth, imagen.drawHeight = imagen.imageWidth * escala, imagen.imageHeight * escala
        h += [Spacer(1, 14), Paragraph(escape(titulo), SUBTITULO), imagen]

    doc.build(h)
    return salida
