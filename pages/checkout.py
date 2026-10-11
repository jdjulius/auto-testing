import re
from dataclasses import dataclass

from playwright.sync_api import Page, expect


def _monto(texto: str) -> float:
    return float(re.search(r"\$([\d.]+)", texto).group(1))


@dataclass
class LineaCompra:
    nombre: str
    cantidad: int
    precio: float


@dataclass
class ResumenCompra:
    """Lo que muestra el paso 2 del checkout (Overview)."""

    lineas: list[LineaCompra]
    pago: str
    envio: str
    subtotal: float
    impuesto: float
    total: float


class CheckoutPage:
    """Pasos 1 (Your Information), 2 (Overview) y Complete del checkout."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.titulo = page.get_by_test_id("title")
        self.cancelar = page.get_by_test_id("cancel")
        # Paso 1
        self.nombre = page.get_by_test_id("firstName")
        self.apellido = page.get_by_test_id("lastName")
        self.codigo_postal = page.get_by_test_id("postalCode")
        self.continuar = page.get_by_test_id("continue")
        self.error = page.get_by_test_id("error")
        # Paso 2
        self.items = page.get_by_test_id("inventory-item")
        self.pago = page.get_by_test_id("payment-info-value")
        self.envio = page.get_by_test_id("shipping-info-value")
        self.subtotal = page.get_by_test_id("subtotal-label")
        self.impuesto = page.get_by_test_id("tax-label")
        self.total = page.get_by_test_id("total-label")
        self.finalizar = page.get_by_test_id("finish")
        # Completo
        self.confirmacion = page.get_by_test_id("complete-header")
        self.texto_confirmacion = page.get_by_test_id("complete-text")
        self.imagen_confirmacion = page.get_by_test_id("pony-express")
        self.volver_inicio = page.get_by_test_id("back-to-products")

    def llenar_datos(self, nombre: str, apellido: str, codigo_postal: str) -> None:
        self.nombre.fill(nombre)
        self.apellido.fill(apellido)
        self.codigo_postal.fill(codigo_postal)

    def completar_datos(self, nombre: str, apellido: str, codigo_postal: str) -> None:
        self.llenar_datos(nombre, apellido, codigo_postal)
        self.continuar.click()

    def montos(self) -> tuple[float, float, float]:
        return (
            _monto(self.subtotal.inner_text()),
            _monto(self.impuesto.inner_text()),
            _monto(self.total.inner_text()),
        )

    def resumen(self) -> ResumenCompra:
        # Esperar a que el Overview esté cargado: count() no espera por sí solo.
        expect(self.titulo).to_have_text("Checkout: Overview")
        expect(self.items.first).to_be_visible()
        lineas = []
        for i in range(self.items.count()):
            item = self.items.nth(i)
            lineas.append(LineaCompra(
                nombre=item.get_by_test_id("inventory-item-name").inner_text(),
                cantidad=int(item.get_by_test_id("item-quantity").inner_text()),
                precio=_monto(item.get_by_test_id("inventory-item-price").inner_text()),
            ))
        subtotal, impuesto, total = self.montos()
        return ResumenCompra(
            lineas=lineas,
            pago=self.pago.inner_text(),
            envio=self.envio.inner_text(),
            subtotal=subtotal,
            impuesto=impuesto,
            total=total,
        )
