import pytest

from cliente import validar_esquema


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Crear",
    descripcion="POST /carts crea un carrito vacío",
    resultado_esperado="201 con id; GET del carrito devuelve 200 sin productos",
    prioridad="Alta",
)
def test_crear_carrito(api, carrito):
    respuesta = api.get(f"/carts/{carrito}")
    assert respuesta.status_code == 200
    validar_esquema(respuesta.json(), "carrito")
    assert respuesta.json()["cart_items"] == []


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Agregar productos",
    descripcion="Agregar un producto con cantidad al carrito",
    resultado_esperado="POST /carts/{cartId} devuelve 200; el carrito tiene el producto con la cantidad pedida",
    prioridad="Crítica",
)
def test_agregar_producto(api, carrito, producto):
    respuesta = api.post(f"/carts/{carrito}", json={"product_id": producto["id"], "quantity": 2})
    assert respuesta.status_code == 200
    contenido = api.get(f"/carts/{carrito}").json()
    validar_esquema(contenido, "carrito")
    items = {i["product_id"]: i["quantity"] for i in contenido["cart_items"]}
    assert items == {producto["id"]: 2}


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Validaciones",
    descripcion="Rechazar cantidades menores a 1",
    resultado_esperado="422 con el error del campo quantity",
    prioridad="Alta",
)
@pytest.mark.parametrize("cantidad", [0, -1], ids=["cero", "negativa"])
def test_cantidad_invalida(api, carrito, producto, cantidad):
    respuesta = api.post(f"/carts/{carrito}", json={"product_id": producto["id"], "quantity": cantidad})
    assert respuesta.status_code == 422
    assert "quantity" in respuesta.json().get("errors", {})


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Quitar productos",
    descripcion="Quitar un producto del carrito",
    resultado_esperado="DELETE /carts/{cartId}/product/{productId} devuelve 204 y el carrito queda vacío",
)
def test_quitar_producto(api, carrito, producto):
    api.post(f"/carts/{carrito}", json={"product_id": producto["id"], "quantity": 1})
    respuesta = api.delete(f"/carts/{carrito}/product/{producto['id']}")
    assert respuesta.status_code == 204
    assert api.get(f"/carts/{carrito}").json()["cart_items"] == []


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Borrar",
    descripcion="Borrar el carrito",
    resultado_esperado="DELETE /carts/{cartId} devuelve 204 y después el carrito no existe (404)",
)
def test_borrar_carrito(api):
    id_carrito = api.post("/carts").json()["id"]
    respuesta = api.delete(f"/carts/{id_carrito}")
    assert respuesta.status_code == 204
    assert api.get(f"/carts/{id_carrito}").status_code == 404


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Consultar",
    descripcion="Un carrito inexistente devuelve 404",
    resultado_esperado="404 con mensaje de error",
)
def test_carrito_inexistente(api):
    respuesta = api.get("/carts/01ZZZZZZZZZZZZZZZZZZZZZZZZ")
    assert respuesta.status_code == 404
    validar_esquema(respuesta.json(), "error")
