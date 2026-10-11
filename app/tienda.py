"""Aplicación de ejemplo bajo prueba: inventario y carrito de compras.

Reemplaza este módulo (o apunta las pruebas a tu propia aplicación) para
reutilizar el framework de registro de escenarios.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

IVA = Decimal("0.19")

CUPONES = {
    "BIENVENIDA10": Decimal("0.10"),
    "VIP25": Decimal("0.25"),
}


class ErrorTienda(Exception):
    """Error base de la aplicación."""


class ProductoNoEncontrado(ErrorTienda):
    pass


class StockInsuficiente(ErrorTienda):
    pass


class CuponInvalido(ErrorTienda):
    pass


def _redondear(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class Producto:
    sku: str
    nombre: str
    precio: Decimal
    stock: int = 0

    def __post_init__(self) -> None:
        if not self.sku or not self.sku.strip():
            raise ValueError("El SKU es obligatorio")
        self.precio = Decimal(str(self.precio))
        if self.precio <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        if self.stock < 0:
            raise ValueError("El stock no puede ser negativo")


class Inventario:
    def __init__(self) -> None:
        self._productos: dict[str, Producto] = {}

    def agregar(self, producto: Producto) -> None:
        if producto.sku in self._productos:
            raise ValueError(f"El SKU {producto.sku} ya existe")
        self._productos[producto.sku] = producto

    def obtener(self, sku: str) -> Producto:
        try:
            return self._productos[sku]
        except KeyError:
            raise ProductoNoEncontrado(sku) from None

    def reabastecer(self, sku: str, cantidad: int) -> int:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        producto = self.obtener(sku)
        producto.stock += cantidad
        return producto.stock

    def retirar(self, sku: str, cantidad: int) -> int:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        producto = self.obtener(sku)
        if cantidad > producto.stock:
            raise StockInsuficiente(
                f"{sku}: solicitado {cantidad}, disponible {producto.stock}"
            )
        producto.stock -= cantidad
        return producto.stock

    def __len__(self) -> int:
        return len(self._productos)


@dataclass
class Carrito:
    inventario: Inventario
    lineas: dict[str, int] = field(default_factory=dict)
    descuento: Decimal = Decimal("0")

    def agregar(self, sku: str, cantidad: int = 1) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        producto = self.inventario.obtener(sku)
        total_pedido = self.lineas.get(sku, 0) + cantidad
        if total_pedido > producto.stock:
            raise StockInsuficiente(
                f"{sku}: solicitado {total_pedido}, disponible {producto.stock}"
            )
        self.lineas[sku] = total_pedido

    def quitar(self, sku: str) -> None:
        if sku not in self.lineas:
            raise ProductoNoEncontrado(sku)
        del self.lineas[sku]

    def aplicar_cupon(self, codigo: str) -> None:
        codigo = codigo.strip().upper()
        if codigo not in CUPONES:
            raise CuponInvalido(codigo)
        self.descuento = CUPONES[codigo]

    @property
    def subtotal(self) -> Decimal:
        return _redondear(
            sum(
                (self.inventario.obtener(sku).precio * cant for sku, cant in self.lineas.items()),
                Decimal("0"),
            )
        )

    @property
    def total(self) -> Decimal:
        con_descuento = self.subtotal * (1 - self.descuento)
        return _redondear(con_descuento * (1 + IVA))

    def confirmar(self) -> Decimal:
        """Descuenta el stock y vacía el carrito. Devuelve el total cobrado."""
        if not self.lineas:
            raise ErrorTienda("El carrito está vacío")
        total = self.total
        for sku, cantidad in self.lineas.items():
            self.inventario.retirar(sku, cantidad)
        self.lineas.clear()
        self.descuento = Decimal("0")
        return total
