import pytest

import config
from cliente import ClienteApi


@pytest.fixture(scope="session")
def api():
    """Cliente anónimo de la API."""
    cliente = ClienteApi(config.API_URL, timeout=config.TIMEOUT_S)
    yield cliente
    cliente.cerrar()


@pytest.fixture(scope="session")
def token(api) -> str:
    """Token del usuario cliente de prueba (se pide una vez por corrida)."""
    respuesta = api.post("/users/login", json={"email": config.CLIENTE_EMAIL, "password": config.CLIENTE_CLAVE})
    assert respuesta.status_code == 200, f"No se pudo iniciar sesión: {respuesta.status_code} {respuesta.text}"
    return respuesta.json()["access_token"]


@pytest.fixture(scope="session")
def api_cliente(api, token):
    """Cliente autenticado como el usuario cliente."""
    cliente = api.con_token(token)
    yield cliente
    cliente.cerrar()


@pytest.fixture(scope="session")
def producto(api) -> dict:
    """Un producto real del catálogo (los datos del sitio público cambian: no se fijan)."""
    respuesta = api.get("/products")
    assert respuesta.status_code == 200
    return respuesta.json()["data"][0]


@pytest.fixture
def carrito(api):
    """Carrito nuevo; se borra al terminar la prueba."""
    respuesta = api.post("/carts")
    assert respuesta.status_code == 201, respuesta.text
    id_carrito = respuesta.json()["id"]
    yield id_carrito
    api.delete(f"/carts/{id_carrito}")
