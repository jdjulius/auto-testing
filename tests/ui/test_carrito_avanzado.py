"""Carrito, inventario y checkout: casos adicionales y defectos relevados."""

import re

import pytest
from playwright.sync_api import expect

from pages import PRODUCTOS, CarritoPage, CheckoutPage, InventarioPage


def abrir_menu(inventario: InventarioPage) -> None:
    inventario.menu.click()


# ------------------------------------------------------------ carrito
@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Quitar productos",
    descripcion="Quitar un producto desde la página del carrito",
    resultado_esperado="El producto desaparece de la lista y el contador baja",
    prioridad="Alta",
)
def test_quitar_desde_carrito(inventario: InventarioPage, carrito: CarritoPage):
    inventario.agregar("Sauce Labs Backpack")
    inventario.agregar("Sauce Labs Onesie")
    inventario.ir_al_carrito()
    inventario.page.get_by_test_id("remove-sauce-labs-backpack").click()
    expect(carrito.items).to_have_count(1)
    expect(carrito.nombres).to_have_text(["Sauce Labs Onesie"])
    expect(inventario.badge_carrito).to_have_text("1")


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Contenido",
    descripcion="El carrito muestra cantidad 1 y el precio de catálogo de cada producto",
    resultado_esperado="Cada línea tiene QTY 1 y su precio oficial",
)
def test_carrito_cantidades_precios(inventario: InventarioPage, carrito: CarritoPage):
    for nombre in PRODUCTOS:
        inventario.agregar(nombre)
    inventario.ir_al_carrito()
    expect(carrito.items).to_have_count(6)
    for i in range(6):
        item = carrito.items.nth(i)
        nombre = item.get_by_test_id("inventory-item-name").inner_text()
        expect(item.get_by_test_id("item-quantity")).to_have_text("1")
        expect(item.get_by_test_id("inventory-item-price")).to_have_text(f"${PRODUCTOS[nombre]}")


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Reset App State",
    descripcion="'Reset App State' restablece los botones de la lista",
    resultado_esperado="Tras el reset todos los productos vuelven a mostrar 'Add to cart'",
)
@pytest.mark.xfail(
    strict=True,
    reason="Reset vacía el carrito pero los botones siguen en 'Remove' hasta recargar la página",
)
def test_reset_restablece_botones(inventario: InventarioPage):
    inventario.agregar("Sauce Labs Backpack")
    inventario.agregar("Sauce Labs Onesie")
    abrir_menu(inventario)
    inventario.page.get_by_test_id("reset-sidebar-link").click()
    expect(inventario.badge_carrito).to_have_count(0)
    expect(inventario.page.locator("[data-test^=remove-]")).to_have_count(0, timeout=3_000)


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Reglas de negocio",
    descripcion="No se puede comprar con el carrito vacío",
    resultado_esperado="El checkout con el carrito vacío se bloquea o muestra un aviso",
    prioridad="Alta",
)
@pytest.mark.xfail(
    strict=True,
    reason="El sitio permite completar una compra de $0.00 sin productos",
)
def test_checkout_carrito_vacio(inventario: InventarioPage, carrito: CarritoPage):
    inventario.ir_al_carrito()
    expect(carrito.items).to_have_count(0)
    carrito.checkout.click()
    checkout = CheckoutPage(inventario.page)
    if "checkout-step-one" in inventario.page.url:
        checkout.completar_datos("Ana", "Pérez", "110111")
    if "checkout-step-two" in inventario.page.url:
        checkout.finalizar.click()
    expect(inventario.page).not_to_have_url(re.compile(r"/checkout-complete\.html$"), timeout=3_000)


# ------------------------------------------------------------ inventario
@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Imágenes",
    descripcion="Las imágenes de los productos cargan y tienen texto alternativo",
    resultado_esperado="6 imágenes con ancho natural > 0 y alt igual al nombre del producto",
)
def test_imagenes_cargan(inventario: InventarioPage):
    expect(inventario.productos).to_have_count(6)
    imagenes = inventario.page.locator("img.inventory_item_img")
    # Esperar a que el navegador termine de cargar las imágenes (máx. 10 s).
    try:
        inventario.page.wait_for_function(
            "() => [...document.querySelectorAll('img.inventory_item_img')]"
            ".every(i => i.complete && i.naturalWidth > 0)",
            timeout=10_000,
        )
    except Exception:
        pass  # la verificación de abajo muestra qué imágenes no cargaron
    datos = imagenes.evaluate_all(
        "els => els.map(e => ({alt: e.alt, ancho: e.naturalWidth, completa: e.complete}))"
    )
    assert sorted(d["alt"] for d in datos) == sorted(PRODUCTOS)
    assert all(d["completa"] and d["ancho"] > 0 for d in datos), datos


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Catálogo",
    descripcion="Cada producto tiene descripción y botón 'Add to cart'",
    resultado_esperado="6 descripciones no vacías y 6 botones 'Add to cart'",
)
def test_descripciones_y_botones(inventario: InventarioPage):
    descripciones = inventario.page.get_by_test_id("inventory-item-desc")
    expect(descripciones).to_have_count(6)
    assert all(t.strip() for t in descripciones.all_inner_texts())
    expect(inventario.page.get_by_role("button", name="Add to cart")).to_have_count(6)


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Ordenamiento",
    descripcion="El orden elegido se conserva al volver del detalle",
    resultado_esperado="Tras abrir un detalle y volver, sigue 'Price (high to low)'",
)
@pytest.mark.xfail(strict=True, reason="Al volver del detalle el orden vuelve a 'Name (A to Z)'")
def test_orden_persiste(inventario: InventarioPage):
    inventario.ordenar("hilo")
    inventario.page.get_by_test_id("item-4-title-link").click()
    inventario.page.get_by_test_id("back-to-products").click()
    expect(inventario.productos).to_have_count(6)
    expect(inventario.orden).to_have_value("hilo")


# ------------------------------------------------------------ checkout
@pytest.mark.escenario(
    modulo="Checkout paso 1",
    funcionalidad="Validaciones",
    descripcion="Rechazar datos del comprador formados solo por espacios",
    resultado_esperado="Muestra un error y no avanza al paso 2",
    prioridad="Alta",
)
@pytest.mark.xfail(strict=True, reason="El formulario acepta nombre, apellido y código postal en blanco")
def test_datos_solo_espacios(inventario: InventarioPage, carrito: CarritoPage, checkout: CheckoutPage):
    inventario.agregar("Sauce Labs Onesie")
    inventario.ir_al_carrito()
    carrito.checkout.click()
    checkout.completar_datos("   ", "   ", "   ")
    expect(checkout.error).to_be_visible(timeout=3_000)


@pytest.mark.escenario(
    modulo="Checkout paso 1",
    funcionalidad="Validaciones",
    descripcion="Aceptar nombres con acentos, apóstrofos y guiones",
    resultado_esperado="Avanza al paso 2 con datos como 'José Ñúñez', \"O'Brien\" o 'Pérez-Gómez'",
)
@pytest.mark.parametrize(
    "nombre, apellido, codigo_postal",
    [("José", "Ñúñez", "110111"), ("Mary-Ann", "O'Brien", "SW1A 1AA"), ("Zoë", "Pérez-Gómez", "08001")],
    ids=["acentos", "apostrofo-guion", "dieresis"],
)
def test_datos_caracteres_especiales(inventario, carrito, checkout, nombre, apellido, codigo_postal):
    inventario.agregar("Sauce Labs Onesie")
    inventario.ir_al_carrito()
    carrito.checkout.click()
    checkout.completar_datos(nombre, apellido, codigo_postal)
    expect(inventario.page).to_have_url(re.compile(r"/checkout-step-two\.html$"))


@pytest.mark.escenario(
    modulo="Checkout paso 1",
    funcionalidad="Seguridad",
    descripcion="Un script en los datos del comprador no se ejecuta",
    resultado_esperado="Avanza al paso 2 sin abrir ningún diálogo",
    prioridad="Alta",
)
def test_datos_xss(inventario: InventarioPage, carrito: CarritoPage, checkout: CheckoutPage):
    dialogos = []
    inventario.page.on("dialog", lambda d: (dialogos.append(d.message), d.dismiss()))
    inventario.agregar("Sauce Labs Onesie")
    inventario.ir_al_carrito()
    carrito.checkout.click()
    checkout.completar_datos("<script>alert('xss')</script>", "<img src=x onerror=alert(1)>", "110111")
    checkout.finalizar.click()
    expect(checkout.confirmacion).to_have_text("Thank you for your order!")
    assert dialogos == [], dialogos
