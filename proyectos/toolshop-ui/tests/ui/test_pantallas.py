"""Levantamiento de pantallas: un escenario por pantalla de pages/mapa.py."""

import re

import pytest
from playwright.sync_api import Page, expect

import config
from pages import CatalogoPage, LoginPage
from pages.mapa import PANTALLAS, Pantalla

CON_COMPONENTES = [p for p in PANTALLAS if p.componentes]


def _llegar(page: Page, pantalla: Pantalla) -> None:
    if pantalla.requiere_sesion:
        LoginPage(page).abrir().ingresar(config.CLIENTE_EMAIL, config.CLIENTE_CLAVE)
        expect(page).to_have_url(re.compile(r"/account$"))
    if pantalla.clave == "detalle":
        CatalogoPage(page).abrir().abrir_producto(0)
        expect(page.get_by_test_id("add-to-cart")).to_be_visible()
    elif pantalla.ejemplo:
        page.goto(pantalla.ejemplo)


@pytest.mark.escenario(
    modulo="Pantallas",
    funcionalidad="Mapa de pantallas",
    descripcion="La pantalla muestra todos sus componentes",
    resultado_esperado="Ruta, título y cada componente del mapa están presentes y visibles",
    prioridad="Alta",
)
@pytest.mark.parametrize("pantalla", CON_COMPONENTES, ids=[p.clave for p in CON_COMPONENTES])
def test_pantalla(page: Page, pantalla: Pantalla):
    _llegar(page, pantalla)
    expect(page).to_have_url(re.compile(rf"^https?://[^/]+{pantalla.ruta}/?$"))
    if pantalla.titulo:
        expect(page.get_by_test_id("page-title")).to_have_text(pantalla.titulo)
    faltantes = []
    for nombre, test_id in pantalla.componentes.items():
        try:
            expect(page.get_by_test_id(test_id).first).to_be_visible(timeout=5_000)
        except AssertionError:
            faltantes.append(f"{nombre} [{test_id}]")
    assert not faltantes, f"Componentes faltantes en {pantalla.nombre}: {', '.join(faltantes)}"
