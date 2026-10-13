import pytest

from cliente import validar_esquema


@pytest.mark.escenario(
    modulo="Catálogo",
    funcionalidad="Categorías",
    descripcion="GET /categories/tree devuelve el árbol de categorías",
    resultado_esperado="200; cada categoría y subcategoría cumple el esquema",
    prioridad="Alta",
)
def test_arbol_categorias(api):
    respuesta = api.get("/categories/tree")
    assert respuesta.status_code == 200
    arbol = respuesta.json()
    assert arbol, "El árbol de categorías está vacío"
    for categoria in arbol:
        validar_esquema(categoria, "categoria")


@pytest.mark.escenario(
    modulo="Catálogo",
    funcionalidad="Categorías",
    descripcion="Los slugs de las categorías son únicos",
    resultado_esperado="GET /categories no repite ningún slug",
)
def test_slugs_unicos(api):
    categorias = api.get("/categories").json()
    slugs = [c["slug"] for c in categorias]
    assert len(slugs) == len(set(slugs)), sorted(s for s in slugs if slugs.count(s) > 1)


@pytest.mark.escenario(
    modulo="Catálogo",
    funcionalidad="Marcas",
    descripcion="GET /brands devuelve las marcas",
    resultado_esperado="200; al menos una marca; todas cumplen el esquema",
)
def test_marcas(api):
    respuesta = api.get("/brands")
    assert respuesta.status_code == 200
    marcas = respuesta.json()
    assert marcas
    for marca in marcas:
        validar_esquema(marca, "marca")
