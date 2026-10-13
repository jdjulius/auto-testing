import re

import pytest
from playwright.sync_api import expect

from pages import CatalogoPage


@pytest.mark.escenario(
    modulo="Catálogo",
    funcionalidad="Listado",
    descripcion="La home muestra productos con nombre y precio",
    resultado_esperado="Al menos un producto; cada tarjeta tiene nombre no vacío y precio mayor que 0",
    prioridad="Alta",
)
def test_productos_con_nombre_y_precio(catalogo: CatalogoPage):
    nombres, precios = catalogo.lista_nombres(), catalogo.lista_precios()
    assert nombres and len(nombres) == len(precios)
    assert all(nombres) and all(p > 0 for p in precios)


@pytest.mark.escenario(
    modulo="Catálogo",
    funcionalidad="Búsqueda",
    descripcion="Buscar un producto por su nombre",
    resultado_esperado="Se muestra 'Searched for' con el término y aparece un producto con ese nombre",
    prioridad="Alta",
)
def test_buscar(catalogo: CatalogoPage):
    termino = catalogo.lista_nombres()[0].split()[0]
    catalogo.buscar(termino)
    catalogo.esperar_productos()
    # La búsqueda también mira la descripción: basta con que algún nombre lo contenga.
    assert any(termino.lower() in n.lower() for n in catalogo.lista_nombres())


@pytest.mark.escenario(
    modulo="Catálogo",
    funcionalidad="Ordenamiento",
    descripcion="Ordenar productos",
    resultado_esperado="La lista queda ordenada según el criterio elegido",
)
@pytest.mark.parametrize(
    "opcion, por_precio, descendente",
    [("name,asc", False, False), ("name,desc", False, True),
     ("price,asc", True, False), ("price,desc", True, True)],
    ids=["nombre-a-z", "nombre-z-a", "precio-menor-mayor", "precio-mayor-menor"],
)
def test_ordenar(catalogo: CatalogoPage, opcion, por_precio, descendente):
    catalogo.ordenar(opcion)
    valores = catalogo.lista_precios() if por_precio else [n.lower() for n in catalogo.lista_nombres()]
    assert valores == sorted(valores, reverse=descendente), valores


@pytest.mark.escenario(
    modulo="Catálogo",
    funcionalidad="Categorías",
    descripcion="Abrir una categoría desde la URL",
    resultado_esperado="/category/hand-tools muestra el título 'Category: Hand Tools' y productos",
)
def test_categoria(page):
    catalogo = CatalogoPage(page).abrir("/category/hand-tools")
    expect(catalogo.titulo).to_have_text("Category: Hand Tools")
    assert catalogo.lista_nombres()
    expect(page).to_have_url(re.compile(r"/category/hand-tools$"))
