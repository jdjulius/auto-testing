import pytest

from app.tienda import Carrito, Inventario, Producto

pytest_plugins = ["auto_testing.plugin", "pytester"]


@pytest.fixture
def inventario() -> Inventario:
    inv = Inventario()
    inv.agregar(Producto("LAP-01", "Laptop", "1500.00", stock=5))
    inv.agregar(Producto("MOU-01", "Mouse", "25.50", stock=20))
    inv.agregar(Producto("TEC-01", "Teclado", "45.00", stock=0))
    return inv


@pytest.fixture
def carrito(inventario: Inventario) -> Carrito:
    return Carrito(inventario)
