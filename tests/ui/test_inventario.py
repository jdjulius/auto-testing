import pytest
from playwright.sync_api import expect

from pages import PRODUCTOS, InventarioPage


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Catálogo",
    descripcion="Listar el catálogo completo de productos",
    resultado_esperado="Se muestran los 6 productos con su precio",
    prioridad="Alta",
)
def test_catalogo(inventario: InventarioPage):
    expect(inventario.productos).to_have_count(6)
    catalogo = dict(zip(inventario.lista_nombres(), inventario.lista_precios()))
    assert catalogo == PRODUCTOS


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Ordenamiento",
    descripcion="Ordenar productos",
    resultado_esperado="La lista queda ordenada según el criterio elegido",
    prioridad="Media",
)
@pytest.mark.parametrize(
    "opcion, por_precio, descendente",
    [("az", False, False), ("za", False, True), ("lohi", True, False), ("hilo", True, True)],
    ids=["nombre-a-z", "nombre-z-a", "precio-menor-mayor", "precio-mayor-menor"],
)
def test_ordenar(inventario: InventarioPage, opcion, por_precio, descendente):
    inventario.ordenar(opcion)
    valores = inventario.lista_precios() if por_precio else inventario.lista_nombres()
    assert valores == sorted(valores, reverse=descendente)
    assert len(valores) == 6
