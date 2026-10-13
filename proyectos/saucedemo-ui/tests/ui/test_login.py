import re

import pytest
from playwright.sync_api import Page, expect

from pages import InventarioPage, LoginPage

CLAVE = "secret_sauce"


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Inicio de sesión",
    descripcion="Iniciar sesión con usuario válido",
    resultado_esperado="Redirige a /inventory.html y muestra 'Products'",
    prioridad="Crítica",
)
def test_login_exitoso(login: LoginPage):
    login.ingresar("standard_user", CLAVE)
    expect(login.page).to_have_url(re.compile(r"/inventory\.html$"))
    expect(InventarioPage(login.page).titulo).to_have_text("Products")


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Inicio de sesión",
    descripcion="Rechazar credenciales inválidas",
    resultado_esperado="Se muestra un error y no se accede al inventario",
    prioridad="Alta",
)
@pytest.mark.parametrize(
    "usuario, clave, mensaje",
    [
        ("locked_out_user", CLAVE, "Sorry, this user has been locked out."),
        ("standard_user", "clave_incorrecta", "Username and password do not match"),
        ("usuario_inexistente", CLAVE, "Username and password do not match"),
        ("", CLAVE, "Username is required"),
        ("standard_user", "", "Password is required"),
    ],
    ids=["usuario-bloqueado", "clave-incorrecta", "usuario-inexistente",
         "usuario-vacio", "clave-vacia"],
)
def test_login_fallido(login: LoginPage, usuario, clave, mensaje):
    login.ingresar(usuario, clave)
    expect(login.error).to_be_visible()
    expect(login.error).to_contain_text(mensaje)
    expect(login.page).not_to_have_url(re.compile(r"/inventory\.html$"))


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Control de acceso",
    descripcion="Impedir el acceso directo al inventario sin sesión",
    resultado_esperado="Vuelve al login con el mensaje de acceso restringido",
    prioridad="Alta",
)
def test_acceso_sin_sesion(page: Page):
    page.goto(InventarioPage.URL)
    error = LoginPage(page).error
    expect(error).to_contain_text("You can only access '/inventory.html' when you are logged in")


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Cierre de sesión",
    descripcion="Cerrar sesión desde el menú lateral",
    resultado_esperado="Vuelve al login y el inventario deja de ser accesible",
    prioridad="Alta",
)
def test_logout(inventario: InventarioPage):
    inventario.cerrar_sesion()
    login = LoginPage(inventario.page)
    expect(login.boton).to_be_visible()
    inventario.page.goto(InventarioPage.URL)
    expect(login.error).to_be_visible()
