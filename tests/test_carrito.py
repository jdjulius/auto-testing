from decimal import Decimal

import pytest

from app.tienda import CuponInvalido, ErrorTienda, ProductoNoEncontrado, StockInsuficiente


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Agregar productos",
    descripcion="Agregar productos y calcular subtotal",
    resultado_esperado="Subtotal = suma de precio x cantidad",
    prioridad="Alta",
)
def test_subtotal(carrito):
    carrito.agregar("LAP-01")
    carrito.agregar("MOU-01", 2)
    assert carrito.subtotal == Decimal("1551.00")


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Agregar productos",
    descripcion="Acumular cantidades del mismo producto",
    resultado_esperado="Una sola línea con la cantidad sumada",
)
def test_acumular_cantidades(carrito):
    carrito.agregar("MOU-01", 2)
    carrito.agregar("MOU-01", 3)
    assert carrito.lineas == {"MOU-01": 5}


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Agregar productos",
    descripcion="No permitir más unidades que el stock",
    resultado_esperado="Se lanza StockInsuficiente",
    prioridad="Alta",
)
def test_agregar_sin_stock(carrito):
    with pytest.raises(StockInsuficiente):
        carrito.agregar("TEC-01")
    carrito.agregar("LAP-01", 5)
    with pytest.raises(StockInsuficiente):
        carrito.agregar("LAP-01")


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Quitar productos",
    descripcion="Quitar un producto del carrito",
    resultado_esperado="La línea desaparece; quitar uno ausente lanza error",
)
def test_quitar(carrito):
    carrito.agregar("MOU-01")
    carrito.quitar("MOU-01")
    assert carrito.lineas == {}
    with pytest.raises(ProductoNoEncontrado):
        carrito.quitar("MOU-01")


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Total",
    descripcion="Total con IVA sin cupón",
    resultado_esperado="Total = subtotal x 1.19",
    prioridad="Alta",
)
def test_total_con_iva(carrito):
    carrito.agregar("MOU-01", 2)  # 51.00
    assert carrito.total == Decimal("60.69")


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Cupones",
    descripcion="Aplicar cupón válido",
    resultado_esperado="El total refleja el descuento antes del IVA",
    prioridad="Alta",
)
@pytest.mark.parametrize(
    "cupon, esperado",
    [("BIENVENIDA10", Decimal("1606.50")), ("vip25", Decimal("1338.75"))],
    ids=["bienvenida10", "vip25-minusculas"],
)
def test_cupon_valido(carrito, cupon, esperado):
    carrito.agregar("LAP-01")
    carrito.aplicar_cupon(cupon)
    assert carrito.total == esperado


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Cupones",
    descripcion="Rechazar cupón inexistente",
    resultado_esperado="Se lanza CuponInvalido y no hay descuento",
)
def test_cupon_invalido(carrito):
    with pytest.raises(CuponInvalido):
        carrito.aplicar_cupon("GRATIS100")
    assert carrito.descuento == 0


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Checkout",
    descripcion="Confirmar compra",
    resultado_esperado="Se cobra el total, se descuenta stock y el carrito queda vacío",
    prioridad="Crítica",
)
def test_confirmar_compra(carrito, inventario):
    carrito.agregar("LAP-01", 2)
    carrito.aplicar_cupon("BIENVENIDA10")
    assert carrito.confirmar() == Decimal("3213.00")
    assert inventario.obtener("LAP-01").stock == 3
    assert carrito.lineas == {}
    assert carrito.descuento == 0


@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Checkout",
    descripcion="Confirmar carrito vacío",
    resultado_esperado="Se lanza ErrorTienda",
)
def test_confirmar_vacio(carrito):
    with pytest.raises(ErrorTienda, match="vacío"):
        carrito.confirmar()
