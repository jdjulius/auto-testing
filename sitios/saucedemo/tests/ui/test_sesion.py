"""Login avanzado, sesión y seguridad."""

import re

import pytest
from playwright.sync_api import Page, expect

from pages import InventarioPage, LoginPage

CLAVE = "secret_sauce"
COOKIE = "session-username"


def _cookies(page: Page) -> dict[str, str]:
    return {c["name"]: c["value"] for c in page.context.cookies()}


# ------------------------------------------------------------ login avanzado
@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Inicio de sesión",
    descripcion="Iniciar sesión con la tecla Enter",
    resultado_esperado="Enter en el campo contraseña envía el formulario y abre el inventario",
)
def test_login_con_enter(login: LoginPage):
    login.usuario.fill("standard_user")
    login.clave.fill(CLAVE)
    login.clave.press("Enter")
    expect(login.page).to_have_url(re.compile(r"/inventory\.html$"))


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Validación de credenciales",
    descripcion="El usuario distingue mayúsculas y no recorta espacios",
    resultado_esperado="Se rechaza con 'Username and password do not match'",
)
@pytest.mark.parametrize(
    "usuario",
    ["Standard_User", "STANDARD_USER", " standard_user", "standard_user "],
    ids=["mayusculas-inicial", "todo-mayusculas", "espacio-inicial", "espacio-final"],
)
def test_usuario_exacto(login: LoginPage, usuario):
    login.ingresar(usuario, CLAVE)
    expect(login.error).to_contain_text("Username and password do not match")


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Seguridad",
    descripcion="Intentos de inyección en el login se rechazan sin ejecutarse",
    resultado_esperado="Muestra el error de credenciales y no se ejecuta ningún script",
    prioridad="Alta",
)
@pytest.mark.parametrize(
    "usuario, clave",
    [("' OR '1'='1", "' OR '1'='1"), ("<script>alert('xss')</script>", CLAVE),
     ("admin'--", "x"), ("standard_user", "' OR 1=1 --")],
    ids=["sql-or", "xss-script", "sql-comentario", "sql-en-clave"],
)
def test_login_inyeccion(login: LoginPage, usuario, clave):
    dialogos = []
    login.page.on("dialog", lambda d: (dialogos.append(d.message), d.dismiss()))
    login.ingresar(usuario, clave)
    expect(login.error).to_contain_text("Username and password do not match")
    expect(login.page).not_to_have_url(re.compile(r"/inventory\.html$"))
    assert dialogos == [], f"Se ejecutó un script: {dialogos}"


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Formulario de login",
    descripcion="La contraseña se oculta al escribir",
    resultado_esperado="El campo contraseña es de tipo password",
)
def test_clave_oculta(login: LoginPage):
    expect(login.clave).to_have_attribute("type", "password")


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Formulario de login",
    descripcion="Cerrar el mensaje de error del login",
    resultado_esperado="La X oculta el mensaje de error",
)
def test_cerrar_error_login(login: LoginPage):
    login.ingresar("standard_user", "mala")
    expect(login.error).to_be_visible()
    login.page.get_by_test_id("error-button").click()
    expect(login.error).to_have_count(0)


# ------------------------------------------------------------ sesión
@pytest.mark.escenario(
    modulo="Sesión",
    funcionalidad="Cookie de sesión",
    descripcion="El login crea la cookie de sesión y el logout la elimina",
    resultado_esperado="Cookie session-username=standard_user tras el login; sin cookie tras el logout",
    prioridad="Alta",
)
def test_cookie_sesion(inventario: InventarioPage):
    expect(inventario.titulo).to_have_text("Products")
    assert _cookies(inventario.page).get(COOKIE) == "standard_user"
    inventario.cerrar_sesion()
    expect(LoginPage(inventario.page).boton).to_be_visible()
    assert COOKIE not in _cookies(inventario.page)


@pytest.mark.escenario(
    modulo="Sesión",
    funcionalidad="Cierre de sesión",
    descripcion="Volver atrás tras cerrar sesión no muestra el inventario",
    resultado_esperado="El botón Atrás lleva al login con el mensaje de acceso restringido",
    prioridad="Alta",
)
def test_atras_tras_logout(inventario: InventarioPage):
    expect(inventario.titulo).to_have_text("Products")
    inventario.cerrar_sesion()
    expect(LoginPage(inventario.page).boton).to_be_visible()
    inventario.page.go_back()
    expect(LoginPage(inventario.page).error).to_contain_text("when you are logged in")
    expect(inventario.productos).to_have_count(0)


@pytest.mark.escenario(
    modulo="Sesión",
    funcionalidad="Persistencia del carrito",
    descripcion="El carrito se conserva al cerrar e iniciar sesión de nuevo",
    resultado_esperado="Tras logout y login con el mismo usuario el contador sigue en 1",
)
def test_carrito_entre_sesiones(inventario: InventarioPage):
    inventario.agregar("Sauce Labs Backpack")
    expect(inventario.badge_carrito).to_have_text("1")
    inventario.cerrar_sesion()
    LoginPage(inventario.page).ingresar("standard_user", CLAVE)
    expect(inventario.badge_carrito).to_have_text("1")


@pytest.mark.escenario(
    modulo="Sesión",
    funcionalidad="Seguridad",
    descripcion="No se puede entrar sin contraseña creando la cookie de sesión",
    resultado_esperado="Con una cookie session-username forjada se redirige al login",
    prioridad="Crítica",
)
@pytest.mark.xfail(
    strict=True,
    reason="Defecto de seguridad: la sesión depende solo de una cookie del navegador; "
           "una cookie forjada da acceso sin contraseña",
)
def test_cookie_forjada(page: Page):
    page.context.add_cookies([{
        "name": COOKIE, "value": "standard_user", "domain": "www.saucedemo.com", "path": "/",
    }])
    page.goto(InventarioPage.URL)
    expect(LoginPage(page).boton).to_be_visible(timeout=5_000)


@pytest.mark.escenario(
    modulo="Sesión",
    funcionalidad="Rutas",
    descripcion="Las páginas internas responden HTTP 200 al abrirlas directamente",
    resultado_esperado="Cargar /inventory.html o /cart.html con sesión devuelve 200",
)
@pytest.mark.xfail(
    strict=True,
    reason="El servidor responde 404 a las rutas internas de la SPA aunque la página se dibuja",
)
@pytest.mark.parametrize("ruta", ["/inventory.html", "/cart.html"], ids=["inventario", "carrito"])
def test_rutas_http_200(inventario: InventarioPage, ruta):
    expect(inventario.titulo).to_have_text("Products")
    respuesta = inventario.page.goto(ruta)
    assert respuesta is not None and respuesta.status == 200, respuesta and respuesta.status


@pytest.mark.escenario(
    modulo="Sesión",
    funcionalidad="Estabilidad",
    descripcion="Una compra completa no produce errores de JavaScript",
    resultado_esperado="Ningún error no controlado (pageerror) desde el login hasta la confirmación",
    prioridad="Alta",
)
def test_sin_errores_js(page: Page):
    errores = []
    page.on("pageerror", lambda e: errores.append(str(e)))
    LoginPage(page).abrir().ingresar("standard_user", CLAVE)
    inventario = InventarioPage(page)
    inventario.agregar("Sauce Labs Backpack")
    inventario.ir_al_carrito()
    page.get_by_test_id("checkout").click()
    page.get_by_test_id("firstName").fill("Ana")
    page.get_by_test_id("lastName").fill("Pérez")
    page.get_by_test_id("postalCode").fill("110111")
    page.get_by_test_id("continue").click()
    page.get_by_test_id("finish").click()
    expect(page.get_by_test_id("complete-header")).to_have_text("Thank you for your order!")
    assert errores == [], errores
