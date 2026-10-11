"""Mismas funcionalidades probadas con cada usuario de saucedemo.

Los usuarios especiales del sitio tienen defectos intencionales. Esos casos
se marcan como ``xfail`` con el defecto esperado: si el defecto aparece, el
escenario queda como XFAIL en el CSV; si deja de aparecer, queda como XPASS.
"""

import re
import time

import pytest
from playwright.sync_api import Page, expect

from pages import PRODUCTOS, CarritoPage, CheckoutPage, InventarioPage, LoginPage

CLAVE = "secret_sauce"
USUARIOS = ["standard_user", "problem_user", "performance_glitch_user", "error_user", "visual_user"]
UMBRAL_LOGIN_S = 3.0

# Defectos conocidos por funcionalidad y usuario.
DEFECTOS = {
    "login_rapido": {
        "performance_glitch_user": "El login tarda varios segundos en responder",
    },
    "imagenes": {
        "problem_user": "Todos los productos muestran la misma imagen",
        "visual_user": "Algunas imágenes de producto no corresponden",
    },
    "precios": {
        "visual_user": "Los precios mostrados no coinciden con el catálogo",
    },
    "ordenar": {
        "problem_user": "El ordenamiento no cambia la lista",
        "error_user": "Ordenar muestra un error y no cambia la lista",
        "visual_user": "Los precios mostrados no quedan ordenados",
    },
    "agregar_todos": {
        "problem_user": "Algunos botones 'Add to cart' no funcionan",
        "error_user": "Algunos botones 'Add to cart' no funcionan",
    },
    "checkout": {
        "problem_user": "El campo Last Name no conserva lo escrito",
        "error_user": "El checkout no se puede completar",
    },
    "detalle": {
        "problem_user": "Al abrir un producto se muestra el detalle de otro",
    },
    "quitar": {
        "problem_user": "El botón 'Remove' no quita el producto del carrito",
        "error_user": "El botón 'Remove' no quita el producto del carrito",
    },
}


# Defectos de tiempo: dependen de la carga del sitio, no se exige que aparezcan.
NO_ESTRICTOS = {"login_rapido"}


def usuarios_para(funcionalidad: str) -> list:
    defectos = DEFECTOS.get(funcionalidad, {})
    estricto = funcionalidad not in NO_ESTRICTOS
    return [
        pytest.param(u, marks=pytest.mark.xfail(reason=defectos[u], strict=estricto))
        if u in defectos
        else u
        for u in USUARIOS
    ]


def iniciar_sesion(page: Page, usuario: str) -> InventarioPage:
    LoginPage(page).abrir().ingresar(usuario, CLAVE)
    inventario = InventarioPage(page)
    expect(inventario.titulo).to_have_text("Products", timeout=15_000)
    return inventario


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Rendimiento de login",
    descripcion=f"Login en menos de {UMBRAL_LOGIN_S:g} s",
    resultado_esperado=f"El inventario aparece antes de {UMBRAL_LOGIN_S:g} segundos",
    prioridad="Media",
)
@pytest.mark.parametrize("usuario", usuarios_para("login_rapido"))
def test_login_rapido(page: Page, usuario):
    login = LoginPage(page).abrir()
    inicio = time.monotonic()
    login.ingresar(usuario, CLAVE)
    expect(page).to_have_url(re.compile(r"/inventory\.html$"), timeout=15_000)
    expect(InventarioPage(page).productos).to_have_count(6, timeout=15_000)
    duracion = time.monotonic() - inicio
    assert duracion < UMBRAL_LOGIN_S, f"El login tardó {duracion:.1f} s"


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Imágenes de productos",
    descripcion="Cada producto muestra su propia imagen",
    resultado_esperado="6 imágenes distintas, ninguna de error (sl-404)",
)
@pytest.mark.parametrize("usuario", usuarios_para("imagenes"))
def test_imagenes_productos(page: Page, usuario):
    iniciar_sesion(page, usuario)
    imagenes = page.locator("img.inventory_item_img")
    expect(imagenes).to_have_count(6)
    fuentes = [imagenes.nth(i).get_attribute("src") for i in range(6)]
    assert not [f for f in fuentes if "sl-404" in f], f"Imágenes de error: {fuentes}"
    assert len(set(fuentes)) == 6, f"Imágenes repetidas: {fuentes}"


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Precios",
    descripcion="Los precios coinciden con el catálogo",
    resultado_esperado="Cada producto muestra su precio oficial",
    prioridad="Alta",
)
@pytest.mark.parametrize("usuario", usuarios_para("precios"))
def test_precios(page: Page, usuario):
    inventario = iniciar_sesion(page, usuario)
    expect(inventario.productos).to_have_count(6)
    assert dict(zip(inventario.lista_nombres(), inventario.lista_precios())) == PRODUCTOS


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Ordenamiento",
    descripcion="Ordenar por precio de mayor a menor",
    resultado_esperado="Los precios quedan en orden descendente",
)
@pytest.mark.parametrize("usuario", usuarios_para("ordenar"))
def test_ordenar_precio(page: Page, usuario):
    inventario = iniciar_sesion(page, usuario)
    inventario.ordenar("hilo")
    precios = inventario.lista_precios()
    assert precios == sorted(precios, reverse=True), f"Orden obtenido: {precios}"


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Carrito",
    descripcion="Agregar los 6 productos al carrito",
    resultado_esperado="El contador muestra 6 y el carrito lista los 6 productos",
    prioridad="Alta",
)
@pytest.mark.parametrize("usuario", usuarios_para("agregar_todos"))
def test_agregar_todos(page: Page, usuario):
    inventario = iniciar_sesion(page, usuario)
    for nombre in PRODUCTOS:
        inventario.agregar(nombre)
    expect(inventario.badge_carrito).to_have_text("6")
    inventario.ir_al_carrito()
    assert sorted(CarritoPage(page).lista_nombres()) == sorted(PRODUCTOS)


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Checkout",
    descripcion="Completar una compra",
    resultado_esperado="Se muestra 'Thank you for your order!'",
    prioridad="Crítica",
)
@pytest.mark.parametrize("usuario", usuarios_para("checkout"))
def test_checkout(page: Page, usuario):
    inventario = iniciar_sesion(page, usuario)
    inventario.agregar("Sauce Labs Backpack")
    inventario.ir_al_carrito()
    CarritoPage(page).checkout.click()
    checkout = CheckoutPage(page)
    checkout.completar_datos("Ana", "Pérez", "110111")
    expect(page).to_have_url(re.compile(r"/checkout-step-two\.html$"))
    checkout.finalizar.click()
    expect(checkout.confirmacion).to_have_text("Thank you for your order!")


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Detalle de producto",
    descripcion="Abrir el detalle muestra el producto elegido",
    resultado_esperado="Al pulsar 'Sauce Labs Backpack' se abre su detalle (id=4)",
    prioridad="Alta",
)
@pytest.mark.parametrize("usuario", usuarios_para("detalle"))
def test_detalle_correcto(page: Page, usuario):
    iniciar_sesion(page, usuario)
    page.get_by_test_id("item-4-title-link").click()
    expect(page.get_by_test_id("back-to-products")).to_be_visible()
    expect(page.get_by_test_id("inventory-item-name")).to_have_text("Sauce Labs Backpack")
    expect(page).to_have_url(re.compile(r"/inventory-item\.html\?id=4$"))


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Carrito",
    descripcion="Quitar un producto del carrito",
    resultado_esperado="Tras 'Remove' el contador desaparece",
    prioridad="Alta",
)
@pytest.mark.parametrize("usuario", usuarios_para("quitar"))
def test_quitar_producto(page: Page, usuario):
    inventario = iniciar_sesion(page, usuario)
    inventario.agregar("Sauce Labs Backpack")
    expect(inventario.badge_carrito).to_have_text("1")
    inventario.quitar("Sauce Labs Backpack")
    expect(inventario.badge_carrito).to_have_count(0, timeout=3_000)
