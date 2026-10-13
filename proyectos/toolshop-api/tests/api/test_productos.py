import uuid

import pytest

import config
from cliente import validar_esquema


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Listado",
    descripcion="GET /products devuelve la primera página del catálogo",
    resultado_esperado="200; cumple el esquema de página; 1 a per_page productos; total >= productos de la página",
    prioridad="Alta",
)
def test_listar_productos(api):
    respuesta = api.get("/products")
    assert respuesta.status_code == 200
    pagina = respuesta.json()
    validar_esquema(pagina, "pagina_productos")
    assert pagina["current_page"] == 1
    assert 1 <= len(pagina["data"]) <= pagina["per_page"]
    assert pagina["total"] >= len(pagina["data"])


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Listado",
    descripcion="Paginación: la página 2 trae productos distintos a la 1",
    resultado_esperado="200 con current_page = 2 y ningún producto repetido",
)
def test_paginacion(api):
    pagina1 = api.get("/products", params={"page": 1}).json()
    respuesta = api.get("/products", params={"page": 2})
    assert respuesta.status_code == 200
    pagina2 = respuesta.json()
    assert pagina2["current_page"] == 2
    assert not {p["id"] for p in pagina1["data"]} & {p["id"] for p in pagina2["data"]}


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Listado",
    descripcion="Página fuera de rango devuelve una lista vacía",
    resultado_esperado="200 sin productos en data",
)
def test_pagina_fuera_de_rango(api):
    ultima = api.get("/products").json()["last_page"]
    respuesta = api.get("/products", params={"page": ultima + 50})
    assert respuesta.status_code == 200
    assert respuesta.json()["data"] == []


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Listado",
    descripcion="El listado responde dentro del umbral de tiempo",
    resultado_esperado=f"GET /products responde en menos de {config.UMBRAL_RESPUESTA_S:g} s",
)
def test_tiempo_respuesta(api):
    respuesta = api.get("/products")
    assert respuesta.status_code == 200
    assert respuesta.elapsed.total_seconds() < config.UMBRAL_RESPUESTA_S


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Detalle",
    descripcion="GET /products/{productId} devuelve el producto pedido",
    resultado_esperado="200; cumple el esquema; mismo id, nombre y precio que en el listado; incluye specs",
    prioridad="Alta",
)
def test_detalle_producto(api, producto):
    respuesta = api.get(f"/products/{producto['id']}")
    assert respuesta.status_code == 200
    detalle = respuesta.json()
    validar_esquema(detalle, "producto")
    assert (detalle["id"], detalle["name"], detalle["price"]) == (producto["id"], producto["name"], producto["price"])
    assert "specs" in detalle


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Detalle",
    descripcion="Un producto inexistente devuelve 404",
    resultado_esperado="404 con mensaje de error",
)
def test_producto_inexistente(api):
    respuesta = api.get("/products/01ZZZZZZZZZZZZZZZZZZZZZZZZ")
    assert respuesta.status_code == 404
    validar_esquema(respuesta.json(), "error")


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Relacionados",
    descripcion="GET /products/{productId}/related devuelve otros productos",
    resultado_esperado="200 con una lista de productos que no incluye al producto consultado",
)
def test_productos_relacionados(api, producto):
    respuesta = api.get(f"/products/{producto['id']}/related")
    assert respuesta.status_code == 200
    relacionados = respuesta.json()
    assert isinstance(relacionados, list)
    assert producto["id"] not in {p["id"] for p in relacionados}


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Búsqueda",
    descripcion="Buscar por un término existente",
    resultado_esperado="200; cumple el esquema; todos los resultados contienen el término en el nombre o la descripción",
    prioridad="Alta",
)
def test_buscar(api, producto):
    termino = producto["name"].split()[0]
    respuesta = api.get("/products/search", params={"q": termino})
    assert respuesta.status_code == 200
    resultado = respuesta.json()
    validar_esquema(resultado, "pagina_productos")
    assert resultado["total"] >= 1
    for p in resultado["data"]:
        assert termino.lower() in f"{p['name']} {p['description']}".lower(), p["name"]


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Búsqueda",
    descripcion="Buscar un término inexistente no devuelve resultados",
    resultado_esperado="200 con total = 0",
)
def test_buscar_sin_resultados(api):
    respuesta = api.get("/products/search", params={"q": f"zz-{uuid.uuid4().hex[:10]}"})
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 0


@pytest.mark.escenario(
    modulo="Productos",
    funcionalidad="Filtros",
    descripcion="QUERY /products filtra por categoría (como lo hace la UI)",
    resultado_esperado="200 con menos productos que el catálogo completo y al menos uno",
)
def test_filtrar_por_categoria(api):
    total = api.get("/products").json()["total"]
    respuesta = api.query("/products", json={"page": "1", "by_category_slug": "hand-tools"})
    assert respuesta.status_code == 200
    filtrado = respuesta.json()
    validar_esquema(filtrado, "pagina_productos")
    assert 1 <= filtrado["total"] < total
