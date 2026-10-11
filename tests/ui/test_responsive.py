"""El sitio en distintos tamaños de pantalla."""

import pytest
from playwright.sync_api import Browser, expect

from pages import InventarioPage, LoginPage

DISPOSITIVOS = {
    "movil": {"viewport": {"width": 375, "height": 667}, "is_mobile": True, "has_touch": True},
    "tablet": {"viewport": {"width": 768, "height": 1024}, "is_mobile": True, "has_touch": True},
    "escritorio": {"viewport": {"width": 1920, "height": 1080}},
}


@pytest.mark.escenario(
    modulo="Responsive",
    funcionalidad="Diseño adaptable",
    descripcion="El inventario se usa sin desplazamiento horizontal",
    resultado_esperado="Menú, carrito y 6 productos visibles; el ancho del documento no supera la pantalla",
)
@pytest.mark.parametrize("dispositivo", DISPOSITIVOS, ids=DISPOSITIVOS.keys())
def test_inventario_adaptable(browser: Browser, base_url, dispositivo):
    contexto = browser.new_context(base_url=base_url, **DISPOSITIVOS[dispositivo])
    try:
        page = contexto.new_page()
        LoginPage(page).abrir().ingresar("standard_user", "secret_sauce")
        inventario = InventarioPage(page)
        expect(inventario.titulo).to_have_text("Products")
        expect(inventario.menu).to_be_visible()
        expect(inventario.link_carrito).to_be_visible()
        expect(inventario.productos).to_have_count(6)
        ancho = DISPOSITIVOS[dispositivo]["viewport"]["width"]
        assert page.evaluate("document.documentElement.scrollWidth") <= ancho
    finally:
        contexto.close()


@pytest.mark.escenario(
    modulo="Responsive",
    funcionalidad="Diseño adaptable",
    descripcion="Comprar desde un móvil",
    resultado_esperado="En 375x667 se completa la compra hasta 'Thank you for your order!'",
    prioridad="Alta",
)
def test_compra_movil(browser: Browser, base_url):
    contexto = browser.new_context(base_url=base_url, **DISPOSITIVOS["movil"])
    try:
        page = contexto.new_page()
        LoginPage(page).abrir().ingresar("standard_user", "secret_sauce")
        inventario = InventarioPage(page)
        inventario.agregar("Sauce Labs Backpack")
        inventario.ir_al_carrito()
        page.get_by_test_id("checkout").tap()
        page.get_by_test_id("firstName").fill("Ana")
        page.get_by_test_id("lastName").fill("Pérez")
        page.get_by_test_id("postalCode").fill("110111")
        page.get_by_test_id("continue").tap()
        page.get_by_test_id("finish").tap()
        expect(page.get_by_test_id("complete-header")).to_have_text("Thank you for your order!")
    finally:
        contexto.close()
