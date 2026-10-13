"""Integración con Allure: vuelca los datos del escenario a cada resultado.

- título: ``ESC-0001 · descripción``
- feature / story: módulo / funcionalidad (agrupación del reporte)
- severity: prioridad (Crítica → blocker, Alta → critical, Media → normal, Baja → minor)
- descripción: resultado esperado
- tags: ID del escenario y navegador
- adjunto: captura de pantalla al final de cada prueba de UI
"""

from __future__ import annotations

import platform
from pathlib import Path

import allure
import pytest

SEVERIDAD = {
    "crítica": allure.severity_level.BLOCKER,
    "critica": allure.severity_level.BLOCKER,
    "alta": allure.severity_level.CRITICAL,
    "media": allure.severity_level.NORMAL,
    "baja": allure.severity_level.MINOR,
}

CATEGORIAS = """[
  {"name": "Defectos conocidos de la aplicación", "matchedStatuses": ["skipped"], "messageRegex": "(?s).*XFAIL.*"},
  {"name": "Fallas de producto", "matchedStatuses": ["failed"]},
  {"name": "Errores de prueba o entorno", "matchedStatuses": ["broken"]},
  {"name": "Omitidos", "matchedStatuses": ["skipped"]}
]
"""


def aplicar_etiquetas(esc) -> None:
    """Se llama en el setup: así las etiquetas quedan aunque falle un fixture."""
    if esc.capa:
        allure.dynamic.epic(esc.capa)
    if esc.modulo:
        allure.dynamic.feature(esc.modulo)
        allure.dynamic.parent_suite(esc.modulo)
    if esc.funcionalidad:
        allure.dynamic.story(esc.funcionalidad)
        allure.dynamic.suite(esc.funcionalidad)
    allure.dynamic.severity(SEVERIDAD.get((esc.prioridad or "media").lower(), allure.severity_level.NORMAL))
    allure.dynamic.tag(esc.id)
    if esc.navegador:
        allure.dynamic.tag(esc.navegador)
    allure.dynamic.label("escenario", esc.id)


def aplicar_titulo(esc) -> None:
    """Se llama en la fase call: allure-pytest fija nombre y descripción al cerrar el setup."""
    allure.dynamic.title(f"{esc.id} · {esc.descripcion}")
    if esc.resultado_esperado:
        allure.dynamic.description(f"**Resultado esperado:** {esc.resultado_esperado}")


def adjuntar_captura(item: pytest.Item, nombre: str = "Captura final") -> None:
    page = getattr(item, "funcargs", {}).get("page")
    if page is None or page.is_closed():
        return
    try:
        allure.attach(page.screenshot(full_page=True), name=nombre,
                      attachment_type=allure.attachment_type.PNG)
    except Exception:  # la captura nunca debe romper la prueba
        pass


def escribir_entorno(alluredir: Path, datos: dict[str, str]) -> None:
    """environment.properties y categories.json para el reporte."""
    alluredir = Path(alluredir)
    alluredir.mkdir(parents=True, exist_ok=True)
    datos = {"Python": platform.python_version(), "Plataforma": platform.platform(), **datos}
    lineas = [f"{k.replace(' ', '_')}={v}" for k, v in datos.items() if v]
    (alluredir / "environment.properties").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    (alluredir / "categories.json").write_text(CATEGORIAS, encoding="utf-8")
