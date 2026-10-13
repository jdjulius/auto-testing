import re

import pytest
from playwright.sync_api import expect

from pages import CarritoPage, CheckoutPage, InventarioPage

TASA_IMPUESTO = 0.08


@pytest.fixture
def en_checkout(inventario: InventarioPage, carrito: CarritoPage) -> InventarioPage:
    """Backpack (29.99) + Bike Light (9.99) en el carrito y checkout iniciado."""
    inventario.agregar("Sauce Labs Backpack")
    inventario.agregar("Sauce Labs Bike Light")
    inventario.ir_al_carrito()
    carrito.checkout.click()
    return inventario


@pytest.mark.escenario(
    modulo="Checkout",
    funcionalidad="Compra completa",
    descripcion="Completar una compra de punta a punta",
    resultado_esperado="Se muestra 'Thank you for your order!' y el carrito queda vacío",
    prioridad="Crítica",
)
def test_compra_completa(en_checkout: InventarioPage, checkout: CheckoutPage):
    checkout.completar_datos("Ana", "Pérez", "110111")
    expect(checkout.page).to_have_url(re.compile(r"/checkout-step-two\.html$"))
    checkout.finalizar.click()
    expect(checkout.page).to_have_url(re.compile(r"/checkout-complete\.html$"))
    expect(checkout.confirmacion).to_have_text("Thank you for your order!")
    expect(en_checkout.badge_carrito).to_have_count(0)


@pytest.mark.escenario(
    modulo="Checkout",
    funcionalidad="Resumen",
    descripcion="Calcular subtotal, impuesto (8%) y total",
    resultado_esperado="Subtotal 39.98, impuesto 3.20, total 43.18",
    prioridad="Alta",
)
def test_resumen_montos(en_checkout: InventarioPage, checkout: CheckoutPage):
    checkout.completar_datos("Ana", "Pérez", "110111")
    subtotal, impuesto, total = checkout.montos()
    assert subtotal == pytest.approx(29.99 + 9.99)
    assert impuesto == pytest.approx(round(subtotal * TASA_IMPUESTO, 2))
    assert total == pytest.approx(subtotal + impuesto)


@pytest.mark.escenario(
    modulo="Checkout",
    funcionalidad="Datos del comprador",
    descripcion="Validar campos obligatorios del comprador",
    resultado_esperado="Se muestra el error del campo faltante y no avanza",
    prioridad="Alta",
)
@pytest.mark.parametrize(
    "nombre, apellido, codigo_postal, mensaje",
    [
        ("", "Pérez", "110111", "First Name is required"),
        ("Ana", "", "110111", "Last Name is required"),
        ("Ana", "Pérez", "", "Postal Code is required"),
    ],
    ids=["sin-nombre", "sin-apellido", "sin-codigo-postal"],
)
def test_datos_obligatorios(en_checkout, checkout: CheckoutPage, nombre, apellido,
                            codigo_postal, mensaje):
    checkout.completar_datos(nombre, apellido, codigo_postal)
    expect(checkout.error).to_contain_text(mensaje)
    expect(checkout.page).to_have_url(re.compile(r"/checkout-step-one\.html$"))
