import re

from playwright.sync_api import Page


def _monto(texto: str) -> float:
    return float(re.search(r"\$([\d.]+)", texto).group(1))


class CheckoutPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.nombre = page.get_by_test_id("firstName")
        self.apellido = page.get_by_test_id("lastName")
        self.codigo_postal = page.get_by_test_id("postalCode")
        self.continuar = page.get_by_test_id("continue")
        self.error = page.get_by_test_id("error")
        self.subtotal = page.get_by_test_id("subtotal-label")
        self.impuesto = page.get_by_test_id("tax-label")
        self.total = page.get_by_test_id("total-label")
        self.finalizar = page.get_by_test_id("finish")
        self.confirmacion = page.get_by_test_id("complete-header")

    def completar_datos(self, nombre: str, apellido: str, codigo_postal: str) -> None:
        self.nombre.fill(nombre)
        self.apellido.fill(apellido)
        self.codigo_postal.fill(codigo_postal)
        self.continuar.click()

    def montos(self) -> tuple[float, float, float]:
        return (
            _monto(self.subtotal.inner_text()),
            _monto(self.impuesto.inner_text()),
            _monto(self.total.inner_text()),
        )
