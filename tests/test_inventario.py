from decimal import Decimal

import pytest

from app.tienda import Producto, ProductoNoEncontrado, StockInsuficiente


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Alta de productos",
    descripcion="Registrar un producto nuevo",
    resultado_esperado="El producto queda disponible con su precio y stock",
    prioridad="Alta",
)
def test_agregar_producto(inventario):
    inventario.agregar(Producto("MON-01", "Monitor", "300", stock=2))
    producto = inventario.obtener("MON-01")
    assert producto.precio == Decimal("300")
    assert producto.stock == 2
    assert len(inventario) == 4


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Alta de productos",
    descripcion="Rechazar SKU duplicado",
    resultado_esperado="Se lanza ValueError",
    prioridad="Alta",
)
def test_sku_duplicado(inventario):
    with pytest.raises(ValueError, match="ya existe"):
        inventario.agregar(Producto("LAP-01", "Otra laptop", "999"))


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Validación de datos",
    descripcion="Rechazar producto con datos inválidos",
    resultado_esperado="Se lanza ValueError",
    prioridad="Media",
)
@pytest.mark.parametrize(
    "sku, precio, stock",
    [("", "10", 1), ("X-1", "0", 1), ("X-2", "-5", 1), ("X-3", "10", -1)],
    ids=["sku-vacio", "precio-cero", "precio-negativo", "stock-negativo"],
)
def test_producto_invalido(sku, precio, stock):
    with pytest.raises(ValueError):
        Producto(sku, "Inválido", precio, stock=stock)


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Consulta",
    descripcion="Consultar un SKU inexistente",
    resultado_esperado="Se lanza ProductoNoEncontrado",
)
def test_producto_inexistente(inventario):
    with pytest.raises(ProductoNoEncontrado):
        inventario.obtener("NO-EXISTE")


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Movimientos de stock",
    descripcion="Reabastecer y retirar stock",
    resultado_esperado="El stock se actualiza correctamente",
    prioridad="Alta",
)
def test_reabastecer_y_retirar(inventario):
    assert inventario.reabastecer("TEC-01", 10) == 10
    assert inventario.retirar("TEC-01", 4) == 6


@pytest.mark.escenario(
    modulo="Inventario",
    funcionalidad="Movimientos de stock",
    descripcion="Retirar más unidades de las disponibles",
    resultado_esperado="Se lanza StockInsuficiente y el stock no cambia",
    prioridad="Alta",
)
def test_retirar_sin_stock(inventario):
    with pytest.raises(StockInsuficiente):
        inventario.retirar("LAP-01", 6)
    assert inventario.obtener("LAP-01").stock == 5
