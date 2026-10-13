import pytest

import config
from cliente import validar_esquema


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Login",
    descripcion="POST /users/login con credenciales válidas devuelve un token",
    resultado_esperado="200 con access_token de tipo bearer y tiempo de expiración",
    prioridad="Crítica",
)
def test_login_valido(api):
    respuesta = api.post("/users/login", json={"email": config.CLIENTE_EMAIL, "password": config.CLIENTE_CLAVE})
    assert respuesta.status_code == 200
    validar_esquema(respuesta.json(), "token")


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Login",
    descripcion="Login rechazado con datos inválidos",
    resultado_esperado="401 con mensaje de error y sin token",
    prioridad="Alta",
)
@pytest.mark.parametrize(
    "datos",
    [{"email": config.CLIENTE_EMAIL, "password": "clave-incorrecta"},
     {"email": "no-existe@ejemplo.com", "password": "welcome01"},
     {}],
    ids=["clave-incorrecta", "usuario-inexistente", "sin-datos"],
)
def test_login_invalido(api, datos):
    respuesta = api.post("/users/login", json=datos)
    assert respuesta.status_code == 401
    validar_esquema(respuesta.json(), "error")
    assert "access_token" not in respuesta.json()


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Perfil",
    descripcion="GET /users/me con token devuelve el usuario sin su contraseña",
    resultado_esperado="200; cumple el esquema; email del usuario autenticado; no expone password",
    prioridad="Alta",
)
def test_perfil_con_token(api_cliente):
    respuesta = api_cliente.get("/users/me")
    assert respuesta.status_code == 200
    validar_esquema(respuesta.json(), "usuario")
    assert respuesta.json()["email"] == config.CLIENTE_EMAIL


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Autorización",
    descripcion="GET /users/me sin token o con token inválido se rechaza",
    resultado_esperado="401",
    prioridad="Alta",
)
@pytest.mark.parametrize("autorizacion", [None, "Bearer token-invalido"], ids=["sin-token", "token-invalido"])
def test_perfil_sin_autorizacion(api, autorizacion):
    headers = {"Authorization": autorizacion} if autorizacion else {}
    respuesta = api.get("/users/me", headers=headers)
    assert respuesta.status_code == 401


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Autorización",
    descripcion="Un cliente no puede listar a todos los usuarios",
    resultado_esperado="GET /users con token de cliente devuelve 403",
    prioridad="Crítica",
)
def test_cliente_no_lista_usuarios(api_cliente):
    respuesta = api_cliente.get("/users")
    assert respuesta.status_code == 403


@pytest.mark.escenario(
    modulo="Usuarios",
    funcionalidad="Facturas",
    descripcion="El cliente consulta sus facturas",
    resultado_esperado="GET /invoices con token devuelve 200 con una página de facturas",
)
def test_facturas_cliente(api_cliente):
    respuesta = api_cliente.get("/invoices")
    assert respuesta.status_code == 200
    pagina = respuesta.json()
    assert {"current_page", "data", "total"} <= set(pagina)
    assert isinstance(pagina["data"], list)
