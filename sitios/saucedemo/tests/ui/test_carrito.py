import re

import pytest
from playwright.sync_api import expect

from pages import CarritoPage, InventarioPage


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Agregar productos",
    descripcion="Agregar productos actualiza el contador del carrito",
    resultado_esperado="El badge muestra la cantidad de productos agregados",
    prioridad="Alta",
)
def test_agregar_actualiza_badge(inventario: InventarioPage):
    expect(inventario.badge_carrito).to_have_count(0)
    inventario.agregar("Sauce Labs Backpack")
    expect(inventario.badge_carrito).to_have_text("1")
    inventario.agregar("Sauce Labs Bike Light")
    expect(inventario.badge_carrito).to_have_text("2")


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Quitar productos",
    descripcion="Quitar un producto desde el inventario",
    resultado_esperado="El badge desaparece y el botón vuelve a 'Add to cart'",
)
def test_quitar_desde_inventario(inventario: InventarioPage):
    inventario.agregar("Sauce Labs Onesie")
    inventario.quitar("Sauce Labs Onesie")
    expect(inventario.badge_carrito).to_have_count(0)
    expect(inventario.page.get_by_test_id("add-to-cart-sauce-labs-onesie")).to_be_visible()


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Contenido",
    descripcion="El carrito muestra los productos agregados",
    resultado_esperado="Aparecen exactamente los productos agregados",
    prioridad="Alta",
)
def test_contenido_carrito(inventario: InventarioPage, carrito: CarritoPage):
    inventario.agregar("Sauce Labs Backpack")
    inventario.agregar("Sauce Labs Fleece Jacket")
    inventario.ir_al_carrito()
    expect(carrito.page).to_have_url(re.compile(r"/cart\.html$"))
    assert sorted(carrito.lista_nombres()) == ["Sauce Labs Backpack", "Sauce Labs Fleece Jacket"]


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Persistencia",
    descripcion="El carrito se conserva al seguir comprando",
    resultado_esperado="Al volver al inventario el badge mantiene la cantidad",
)
def test_seguir_comprando(inventario: InventarioPage, carrito: CarritoPage):
    inventario.agregar("Sauce Labs Bolt T-Shirt")
    inventario.ir_al_carrito()
    carrito.seguir_comprando.click()
    expect(inventario.page).to_have_url(re.compile(r"/inventory\.html$"))
    expect(inventario.badge_carrito).to_have_text("1")
