"""Levantamiento de pantallas: un escenario por pantalla de pages/mapa.py."""

import re

import pytest
from playwright.sync_api import Page, expect

from pages.mapa import PANTALLAS, Pantalla

CON_COMPONENTES = [p for p in PANTALLAS if p.componentes]


@pytest.mark.escenario(
    modulo="Pantallas",
    funcionalidad="Mapa de pantallas",
    descripcion="La pantalla muestra todos sus componentes",
    resultado_esperado="Ruta y cada componente del mapa están presentes y visibles",
    prioridad="Alta",
)
@pytest.mark.parametrize("pantalla", CON_COMPONENTES, ids=[p.clave for p in CON_COMPONENTES])
def test_pantalla(page: Page, pantalla: Pantalla):
    page.goto(pantalla.ejemplo)
    expect(page).to_have_url(re.compile(rf"^https?://[^/]+{pantalla.ruta}/?$"))
    if pantalla.titulo:
        expect(page).to_have_title(pantalla.titulo)
    faltantes = []
    for nombre, selector in pantalla.componentes.items():
        try:
            expect(page.locator(selector).first).to_be_visible(timeout=5_000)
        except AssertionError:
            faltantes.append(f"{nombre} [{selector}]")
    assert not faltantes, f"Componentes faltantes en {pantalla.nombre}: {', '.join(faltantes)}"
