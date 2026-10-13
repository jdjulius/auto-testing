"""Pantalla de detalle de producto (/inventory-item.html?id=N)."""

import re

import pytest
from playwright.sync_api import expect

from pages import PRODUCTOS, InventarioPage
from pages.inventario import slug

# id de la URL -> producto (relevado del sitio)
IDS = {
    0: "Sauce Labs Bike Light",
    1: "Sauce Labs Bolt T-Shirt",
    2: "Sauce Labs Onesie",
    3: "Test.allTheThings() T-Shirt (Red)",
    4: "Sauce Labs Backpack",
    5: "Sauce Labs Fleece Jacket",
}


@pytest.mark.escenario(
    modulo="Detalle de producto",
    funcionalidad="Contenido",
    descripcion="El detalle muestra nombre, descripción, precio e imagen del producto",
    resultado_esperado="Nombre y precio iguales al catálogo; descripción no vacía; imagen con alt = nombre",
    prioridad="Alta",
)
@pytest.mark.parametrize("item_id", IDS, ids=[f"id-{i}" for i in IDS])
def test_detalle_contenido(inventario: InventarioPage, item_id):
    page = inventario.page
    nombre = IDS[item_id]
    page.get_by_test_id(f"item-{item_id}-title-link").click()
    expect(page).to_have_url(re.compile(rf"/inventory-item\.html\?id={item_id}$"))
    # La URL cambia antes de que se dibuje el detalle: esperar un componente propio.
    expect(page.get_by_test_id("back-to-products")).to_be_visible()
    expect(page.get_by_test_id("inventory-item-name")).to_have_text(nombre)
    expect(page.get_by_test_id("inventory-item-price")).to_have_text(f"${PRODUCTOS[nombre]}")
    expect(page.get_by_test_id("inventory-item-desc")).not_to_be_empty()
    imagen = page.locator(".inventory_details_img")
    expect(imagen).to_have_attribute("alt", nombre)


@pytest.mark.escenario(
    modulo="Detalle de producto",
    funcionalidad="Carrito desde el detalle",
    descripcion="Agregar y quitar el producto desde su detalle",
    resultado_esperado="Add to cart pone el contador en 1 y cambia a Remove; Remove lo deja en 0",
    prioridad="Alta",
)
def test_detalle_agregar_quitar(inventario: InventarioPage):
    page = inventario.page
    page.get_by_test_id("item-5-title-link").click()
    page.get_by_test_id("add-to-cart").click()
    expect(inventario.badge_carrito).to_have_text("1")
    expect(page.get_by_test_id("remove")).to_be_visible()
    page.get_by_test_id("remove").click()
    expect(inventario.badge_carrito).to_have_count(0)
    expect(page.get_by_test_id("add-to-cart")).to_be_visible()


@pytest.mark.escenario(
    modulo="Detalle de producto",
    funcionalidad="Carrito desde el detalle",
    descripcion="Lo agregado en el detalle se refleja en el inventario",
    resultado_esperado="Al volver, el producto muestra el botón Remove en la lista",
)
def test_detalle_refleja_en_inventario(inventario: InventarioPage):
    page = inventario.page
    page.get_by_test_id("item-5-title-link").click()
    page.get_by_test_id("add-to-cart").click()
    page.get_by_test_id("back-to-products").click()
    expect(page.get_by_test_id(f"remove-{slug(IDS[5])}")).to_be_visible()


@pytest.mark.escenario(
    modulo="Detalle de producto",
    funcionalidad="Producto inexistente",
    descripcion="Un id de producto inexistente muestra 'ITEM NOT FOUND'",
    resultado_esperado="La pantalla de detalle informa que el producto no existe",
)
def test_detalle_inexistente(inventario: InventarioPage):
    expect(inventario.titulo).to_have_text("Products")
    inventario.page.goto("/inventory-item.html?id=99")
    expect(inventario.page.get_by_test_id("back-to-products")).to_be_visible()
    expect(inventario.page.get_by_test_id("inventory-item-name")).to_have_text("ITEM NOT FOUND")
