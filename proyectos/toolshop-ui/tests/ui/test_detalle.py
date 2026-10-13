import re

import pytest
from playwright.sync_api import expect

from pages import CatalogoPage, DetallePage


@pytest.mark.escenario(
    modulo="Detalle de producto",
    funcionalidad="Contenido",
    descripcion="El detalle muestra el mismo nombre y precio que la tarjeta del catálogo",
    resultado_esperado="Ruta /product/{id}; nombre y precio iguales a los del catálogo; descripción no vacía",
    prioridad="Alta",
)
def test_detalle_coincide_con_catalogo(catalogo: CatalogoPage):
    nombre, valor = catalogo.abrir_producto(0)
    detalle = DetallePage(catalogo.page)
    detalle.esperar()
    expect(catalogo.page).to_have_url(re.compile(r"/product/[0-9A-Za-z]+$"))
    expect(detalle.nombre).to_have_text(nombre)
    assert detalle.valor_precio() == valor
    expect(detalle.descripcion).not_to_be_empty()


@pytest.mark.escenario(
    modulo="Detalle de producto",
    funcionalidad="Carrito",
    descripcion="Agregar un producto al carrito desde el detalle",
    resultado_esperado="El contador del carrito muestra la cantidad agregada",
    prioridad="Crítica",
)
@pytest.mark.parametrize("cantidad", [1, 3], ids=["una-unidad", "tres-unidades"])
def test_agregar_al_carrito(catalogo: CatalogoPage, cantidad):
    catalogo.abrir_producto(0)
    detalle = DetallePage(catalogo.page)
    detalle.esperar()
    detalle.agregar_al_carrito(cantidad)
    expect(detalle.contador_carrito).to_have_text(str(cantidad))
