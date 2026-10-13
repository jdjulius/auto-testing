"""Levantamiento de pantallas: un escenario por pantalla de pages/mapa.py."""

import re

import pytest
from playwright.sync_api import Page, expect

from pages import CarritoPage, CheckoutPage, InventarioPage, LoginPage
from pages.mapa import PANTALLAS, Pantalla

CLAVE = "secret_sauce"


def _llegar(page: Page, clave: str) -> None:
    """Lleva el navegador al estado en que se ve la pantalla."""
    login = LoginPage(page).abrir()
    if clave == "login":
        return
    login.ingresar("standard_user", CLAVE)
    inventario = InventarioPage(page)
    expect(inventario.titulo).to_have_text("Products")
    if clave == "inventario":
        return
    if clave == "menu":
        inventario.menu.click()
        return
    if clave == "detalle":
        page.get_by_test_id("item-4-title-link").click()
        return
    inventario.agregar("Sauce Labs Backpack")
    inventario.ir_al_carrito()
    if clave == "carrito":
        return
    CarritoPage(page).checkout.click()
    if clave == "checkout-paso-1":
        return
    checkout = CheckoutPage(page)
    checkout.completar_datos("Ana", "Pérez", "110111")
    if clave == "checkout-paso-2":
        return
    checkout.finalizar.click()


@pytest.mark.escenario(
    modulo="Pantallas",
    funcionalidad="Mapa de pantallas",
    descripcion="La pantalla muestra todos sus componentes",
    resultado_esperado="Ruta, título y cada componente del mapa están presentes y visibles",
    prioridad="Alta",
)
@pytest.mark.parametrize("pantalla", PANTALLAS, ids=[p.clave for p in PANTALLAS])
def test_pantalla(page: Page, pantalla: Pantalla):
    _llegar(page, pantalla.clave)
    expect(page).to_have_url(re.compile(re.escape(pantalla.ruta) + r"$"))
    if pantalla.titulo:
        expect(page.get_by_test_id("title")).to_have_text(pantalla.titulo)

    # Se revisan todos los componentes antes de fallar, para ver el mapa completo.
    faltantes = []
    for nombre, test_id in pantalla.componentes.items():
        try:
            expect(page.get_by_test_id(test_id).first).to_be_visible(timeout=3_000)
        except AssertionError:
            faltantes.append(f"{nombre} [{test_id}]")
    for nombre, (test_id, cantidad) in pantalla.repetidos.items():
        try:
            expect(page.get_by_test_id(test_id)).to_have_count(cantidad, timeout=3_000)
        except AssertionError:
            real = page.get_by_test_id(test_id).count()
            faltantes.append(f"{nombre} [{test_id}] x{real} (esperado x{cantidad})")
    assert not faltantes, f"Componentes faltantes en {pantalla.nombre}: {', '.join(faltantes)}"
