import re

import pytest
from playwright.sync_api import Page, expect

from pages import CarritoPage, InventarioPage, LoginPage


def url(ruta: str) -> re.Pattern:
    return re.compile(re.escape(ruta) + r"$")


def abrir_menu(page: Page) -> None:
    page.locator("#react-burger-menu-btn").click()


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Páginas protegidas",
    descripcion="Página protegida sin sesión redirige al login",
    resultado_esperado="Vuelve a / con el mensaje 'You can only access ... when you are logged in'",
    prioridad="Alta",
)
@pytest.mark.parametrize(
    "ruta",
    ["/cart.html", "/checkout-step-one.html", "/checkout-step-two.html",
     "/checkout-complete.html", "/inventory-item.html?id=4"],
    ids=["carrito", "checkout-paso-1", "checkout-paso-2", "checkout-completo", "detalle-producto"],
)
def test_pagina_protegida(page: Page, ruta):
    page.goto(ruta)
    login = LoginPage(page)
    expect(login.boton).to_be_visible()
    expect(login.error).to_contain_text(
        f"You can only access '{ruta.split('?')[0]}' when you are logged in"
    )


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Detalle de producto",
    descripcion="Abrir el detalle de un producto",
    resultado_esperado="Redirige a /inventory-item.html?id=N con el mismo producto",
    prioridad="Alta",
)
@pytest.mark.parametrize("enlace", ["title", "img"], ids=["por-nombre", "por-imagen"])
def test_detalle_producto(inventario: InventarioPage, enlace):
    page = inventario.page
    page.get_by_test_id(f"item-4-{enlace}-link").click()
    expect(page).to_have_url(url("/inventory-item.html?id=4"))
    expect(page.get_by_test_id("inventory-item-name")).to_have_text("Sauce Labs Backpack")


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Detalle de producto",
    descripcion="Volver al inventario desde el detalle",
    resultado_esperado="'Back to products' redirige a /inventory.html",
)
def test_volver_desde_detalle(inventario: InventarioPage):
    page = inventario.page
    page.get_by_test_id("item-4-title-link").click()
    page.get_by_test_id("back-to-products").click()
    expect(page).to_have_url(url("/inventory.html"))
    expect(inventario.productos).to_have_count(6)


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Flujo de compra",
    descripcion="Cancelar en el paso 1 del checkout",
    resultado_esperado="Redirige al carrito (/cart.html)",
)
def test_cancelar_checkout_paso_1(inventario: InventarioPage, carrito: CarritoPage):
    page = inventario.page
    inventario.agregar("Sauce Labs Backpack")
    inventario.ir_al_carrito()
    carrito.checkout.click()
    expect(page).to_have_url(url("/checkout-step-one.html"))
    page.get_by_test_id("cancel").click()
    expect(page).to_have_url(url("/cart.html"))


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Flujo de compra",
    descripcion="Cancelar en el paso 2 del checkout",
    resultado_esperado="Redirige al inventario (/inventory.html) y conserva el carrito",
)
def test_cancelar_checkout_paso_2(inventario: InventarioPage, carrito: CarritoPage, checkout):
    page = inventario.page
    inventario.agregar("Sauce Labs Backpack")
    inventario.ir_al_carrito()
    carrito.checkout.click()
    checkout.completar_datos("Ana", "Pérez", "110111")
    expect(page).to_have_url(url("/checkout-step-two.html"))
    page.get_by_test_id("cancel").click()
    expect(page).to_have_url(url("/inventory.html"))
    expect(inventario.badge_carrito).to_have_text("1")


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Flujo de compra",
    descripcion="Volver al inicio tras completar la compra",
    resultado_esperado="'Back Home' redirige a /inventory.html con el carrito vacío",
)
def test_volver_tras_compra(inventario: InventarioPage, carrito: CarritoPage, checkout):
    page = inventario.page
    inventario.agregar("Sauce Labs Backpack")
    inventario.ir_al_carrito()
    carrito.checkout.click()
    checkout.completar_datos("Ana", "Pérez", "110111")
    checkout.finalizar.click()
    expect(page).to_have_url(url("/checkout-complete.html"))
    page.get_by_test_id("back-to-products").click()
    expect(page).to_have_url(url("/inventory.html"))
    expect(inventario.badge_carrito).to_have_count(0)


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Menú lateral",
    descripcion="'All Items' redirige al inventario",
    resultado_esperado="Desde el carrito, 'All Items' lleva a /inventory.html",
)
def test_menu_all_items(inventario: InventarioPage):
    page = inventario.page
    inventario.ir_al_carrito()
    expect(page).to_have_url(url("/cart.html"))
    abrir_menu(page)
    page.get_by_test_id("inventory-sidebar-link").click()
    expect(page).to_have_url(url("/inventory.html"))


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Menú lateral",
    descripcion="'About' redirige al sitio de Sauce Labs",
    resultado_esperado="Navega a https://saucelabs.com/",
)
def test_menu_about(inventario: InventarioPage):
    page = inventario.page
    abrir_menu(page)
    about = page.get_by_test_id("about-sidebar-link")
    expect(about).to_have_attribute("href", "https://saucelabs.com/")
    about.click()
    page.wait_for_url(re.compile(r"^https://saucelabs\.com/"), wait_until="commit")


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Menú lateral",
    descripcion="'Reset App State' vacía el carrito",
    resultado_esperado="El contador del carrito desaparece",
)
def test_menu_reset(inventario: InventarioPage):
    page = inventario.page
    inventario.agregar("Sauce Labs Backpack")
    expect(inventario.badge_carrito).to_have_text("1")
    abrir_menu(page)
    page.get_by_test_id("reset-sidebar-link").click()
    expect(inventario.badge_carrito).to_have_count(0)


@pytest.mark.escenario(
    modulo="Redirecciones",
    funcionalidad="Redes sociales",
    descripcion="Enlace a red social del pie de página",
    resultado_esperado="Apunta al perfil de Sauce Labs y abre en una pestaña nueva",
)
@pytest.mark.parametrize(
    "red, destino",
    [
        ("X", r"^https://(twitter|x)\.com/saucelabs"),
        ("Facebook", r"^https://www\.facebook\.com/saucelabs"),
        ("LinkedIn", r"^https://www\.linkedin\.com/company/sauce-labs"),
    ],
    ids=["twitter", "facebook", "linkedin"],
)
def test_redes_sociales(inventario: InventarioPage, red, destino):
    page = inventario.page
    enlace = page.get_by_role("contentinfo").get_by_role("link", name=red, exact=True)
    expect(enlace).to_have_attribute("href", re.compile(destino))
    with page.context.expect_page() as nueva:
        enlace.click()
    nueva_pestana = nueva.value
    nueva_pestana.wait_for_url(re.compile(r"^https://"), wait_until="commit")
    dominio = r"^https://(www\.)?(twitter|x|facebook|linkedin)\.com/"
    assert re.match(dominio, nueva_pestana.url), nueva_pestana.url
