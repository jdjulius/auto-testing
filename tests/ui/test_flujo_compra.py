"""Flujo de compra paso a paso: formulario, resumen, confirmación y PDF de la compra."""

import re
from datetime import datetime

import pytest
from playwright.sync_api import expect

from auto_testing.comprobante_pdf import generar_comprobante
from pages import PRODUCTOS, CarritoPage, CheckoutPage, InventarioPage

TASA_IMPUESTO = 0.08
PAGO = "SauceCard #31337"
ENVIO = "Free Pony Express Delivery!"
COMPRADOR = {"nombre": "Ana María", "apellido": "Pérez-Gómez", "codigo_postal": "110111"}

CARRITOS = {
    "un-producto": ["Sauce Labs Onesie"],
    "tres-productos": ["Sauce Labs Backpack", "Sauce Labs Bike Light", "Sauce Labs Bolt T-Shirt"],
    "todos": list(PRODUCTOS),
}


def url(ruta: str) -> re.Pattern:
    return re.compile(re.escape(ruta) + r"$")


def ir_a_checkout(inventario: InventarioPage, productos: list[str]) -> CheckoutPage:
    for nombre in productos:
        inventario.agregar(nombre)
    inventario.ir_al_carrito()
    CarritoPage(inventario.page).checkout.click()
    expect(inventario.page).to_have_url(url("/checkout-step-one.html"))
    return CheckoutPage(inventario.page)


# ------------------------------------------------------------ paso 1
@pytest.mark.escenario(
    modulo="Checkout paso 1",
    funcionalidad="Formulario Your Information",
    descripcion="El formulario muestra sus campos vacíos con placeholder",
    resultado_esperado="First Name, Last Name y Zip/Postal Code vacíos con su placeholder",
)
def test_paso1_formulario_inicial(inventario: InventarioPage):
    checkout = ir_a_checkout(inventario, ["Sauce Labs Backpack"])
    expect(checkout.titulo).to_have_text("Checkout: Your Information")
    for campo, placeholder in [
        (checkout.nombre, "First Name"),
        (checkout.apellido, "Last Name"),
        (checkout.codigo_postal, "Zip/Postal Code"),
    ]:
        expect(campo).to_be_editable()
        expect(campo).to_have_value("")
        expect(campo).to_have_attribute("placeholder", placeholder)


@pytest.mark.escenario(
    modulo="Checkout paso 1",
    funcionalidad="Formulario Your Information",
    descripcion="Llenar el formulario conserva los valores y avanza al paso 2",
    resultado_esperado="Los campos muestran lo escrito y 'Continue' lleva a /checkout-step-two.html",
    prioridad="Alta",
)
def test_paso1_llenar_formulario(inventario: InventarioPage):
    checkout = ir_a_checkout(inventario, ["Sauce Labs Backpack"])
    checkout.llenar_datos(COMPRADOR["nombre"], COMPRADOR["apellido"], COMPRADOR["codigo_postal"])
    expect(checkout.nombre).to_have_value(COMPRADOR["nombre"])
    expect(checkout.apellido).to_have_value(COMPRADOR["apellido"])
    expect(checkout.codigo_postal).to_have_value(COMPRADOR["codigo_postal"])
    checkout.continuar.click()
    expect(inventario.page).to_have_url(url("/checkout-step-two.html"))


@pytest.mark.escenario(
    modulo="Checkout paso 1",
    funcionalidad="Formulario Your Information",
    descripcion="Cerrar el mensaje de error del formulario",
    resultado_esperado="El error desaparece al pulsar la X",
)
def test_paso1_cerrar_error(inventario: InventarioPage):
    checkout = ir_a_checkout(inventario, ["Sauce Labs Backpack"])
    checkout.continuar.click()
    expect(checkout.error).to_contain_text("First Name is required")
    inventario.page.get_by_test_id("error-button").click()
    expect(checkout.error).to_have_count(0)


# ------------------------------------------------------------ paso 2
@pytest.mark.escenario(
    modulo="Checkout paso 2",
    funcionalidad="Resumen Overview",
    descripcion="Validar productos, cantidades y precios del resumen",
    resultado_esperado="Cada producto aparece con cantidad 1 y su precio de catálogo",
    prioridad="Alta",
)
@pytest.mark.parametrize("productos", CARRITOS.values(), ids=CARRITOS.keys())
def test_paso2_productos(inventario: InventarioPage, productos):
    checkout = ir_a_checkout(inventario, productos)
    checkout.completar_datos(COMPRADOR["nombre"], COMPRADOR["apellido"], COMPRADOR["codigo_postal"])
    expect(checkout.titulo).to_have_text("Checkout: Overview")
    resumen = checkout.resumen()
    assert sorted(l.nombre for l in resumen.lineas) == sorted(productos)
    for linea in resumen.lineas:
        assert linea.cantidad == 1, linea
        assert linea.precio == PRODUCTOS[linea.nombre], linea


@pytest.mark.escenario(
    modulo="Checkout paso 2",
    funcionalidad="Resumen Overview",
    descripcion="Validar información de pago y envío",
    resultado_esperado=f"Pago '{PAGO}' y envío '{ENVIO}'",
)
def test_paso2_pago_envio(inventario: InventarioPage):
    checkout = ir_a_checkout(inventario, ["Sauce Labs Backpack"])
    checkout.completar_datos(COMPRADOR["nombre"], COMPRADOR["apellido"], COMPRADOR["codigo_postal"])
    expect(inventario.page.get_by_test_id("payment-info-label")).to_have_text("Payment Information:")
    expect(checkout.pago).to_have_text(PAGO)
    expect(inventario.page.get_by_test_id("shipping-info-label")).to_have_text("Shipping Information:")
    expect(checkout.envio).to_have_text(ENVIO)
    expect(inventario.page.get_by_test_id("total-info-label")).to_have_text("Price Total")


@pytest.mark.escenario(
    modulo="Checkout paso 2",
    funcionalidad="Resumen Overview",
    descripcion="Validar subtotal, impuesto (8%) y total",
    resultado_esperado="Subtotal = suma de precios; impuesto = 8% redondeado; total = subtotal + impuesto",
    prioridad="Crítica",
)
@pytest.mark.parametrize("productos", CARRITOS.values(), ids=CARRITOS.keys())
def test_paso2_totales(inventario: InventarioPage, productos):
    checkout = ir_a_checkout(inventario, productos)
    checkout.completar_datos(COMPRADOR["nombre"], COMPRADOR["apellido"], COMPRADOR["codigo_postal"])
    resumen = checkout.resumen()
    esperado = round(sum(PRODUCTOS[n] for n in productos), 2)
    assert resumen.subtotal == pytest.approx(esperado)
    assert resumen.subtotal == pytest.approx(sum(l.precio * l.cantidad for l in resumen.lineas))
    assert resumen.impuesto == pytest.approx(round(esperado * TASA_IMPUESTO, 2))
    assert resumen.total == pytest.approx(round(resumen.subtotal + resumen.impuesto, 2))


# ------------------------------------------------------------ completo
@pytest.mark.escenario(
    modulo="Checkout completo",
    funcionalidad="Confirmación",
    descripcion="La confirmación muestra encabezado, texto, imagen y Back Home",
    resultado_esperado="'Thank you for your order!', texto de despacho, imagen y botón 'Back Home'",
    prioridad="Alta",
)
def test_completo_confirmacion(inventario: InventarioPage):
    checkout = ir_a_checkout(inventario, ["Sauce Labs Backpack"])
    checkout.completar_datos(COMPRADOR["nombre"], COMPRADOR["apellido"], COMPRADOR["codigo_postal"])
    checkout.finalizar.click()
    expect(inventario.page).to_have_url(url("/checkout-complete.html"))
    expect(checkout.titulo).to_have_text("Checkout: Complete!")
    expect(checkout.confirmacion).to_have_text("Thank you for your order!")
    expect(checkout.texto_confirmacion).to_contain_text("Your order has been dispatched")
    expect(checkout.imagen_confirmacion).to_be_visible()
    expect(checkout.volver_inicio).to_have_text("Back Home")
    expect(inventario.badge_carrito).to_have_count(0)


@pytest.mark.escenario(
    modulo="Checkout completo",
    funcionalidad="Back Home",
    descripcion="'Back Home' vuelve al inventario con el carrito vacío",
    resultado_esperado="Redirige a /inventory.html, sin contador y con todos los botones 'Add to cart'",
    prioridad="Alta",
)
def test_completo_back_home(inventario: InventarioPage):
    checkout = ir_a_checkout(inventario, ["Sauce Labs Backpack", "Sauce Labs Onesie"])
    checkout.completar_datos(COMPRADOR["nombre"], COMPRADOR["apellido"], COMPRADOR["codigo_postal"])
    checkout.finalizar.click()
    checkout.volver_inicio.click()
    expect(inventario.page).to_have_url(url("/inventory.html"))
    expect(inventario.badge_carrito).to_have_count(0)
    expect(inventario.page.get_by_role("button", name="Add to cart")).to_have_count(6)


@pytest.mark.escenario(
    modulo="Checkout completo",
    funcionalidad="PDF de la compra",
    descripcion="Generar el PDF de la compra",
    resultado_esperado="Se genera un comprobante PDF con productos, pago, envío, totales y capturas",
    prioridad="Alta",
)
@pytest.mark.parametrize("nombre_carrito", CARRITOS)
def test_pdf_de_la_compra(inventario: InventarioPage, nombre_carrito, pytestconfig):
    page = inventario.page
    checkout = ir_a_checkout(inventario, CARRITOS[nombre_carrito])
    checkout.completar_datos(COMPRADOR["nombre"], COMPRADOR["apellido"], COMPRADOR["codigo_postal"])
    resumen = checkout.resumen()
    assert len(resumen.lineas) == len(CARRITOS[nombre_carrito])
    captura_resumen = page.screenshot(full_page=True)
    checkout.finalizar.click()
    expect(checkout.confirmacion).to_have_text("Thank you for your order!")
    confirmacion = checkout.confirmacion.inner_text()
    captura_confirmacion = page.screenshot(full_page=True)

    salida = pytestconfig.rootpath / "reportes" / "compras" / f"compra-{nombre_carrito}.pdf"
    generar_comprobante(
        salida,
        lineas=[(l.nombre, l.cantidad, l.precio) for l in resumen.lineas],
        pago=resumen.pago,
        envio=resumen.envio,
        subtotal=resumen.subtotal,
        impuesto=resumen.impuesto,
        total=resumen.total,
        comprador=COMPRADOR,
        confirmacion=confirmacion,
        datos={"Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Sitio": page.url},
        capturas=[("Checkout: Overview", captura_resumen),
                  ("Checkout: Complete!", captura_confirmacion)],
    )
    contenido = salida.read_bytes()
    assert contenido.startswith(b"%PDF") and len(contenido) > 10_000
