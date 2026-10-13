import allure
from playwright.sync_api import Page, expect

from pages.catalogo import precio


class DetallePage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.nombre = page.get_by_test_id("product-name")
        self.precio = page.get_by_test_id("unit-price")
        self.descripcion = page.get_by_test_id("product-description")
        self.cantidad = page.get_by_test_id("quantity")
        self.aumentar = page.get_by_test_id("increase-quantity")
        self.agregar = page.get_by_test_id("add-to-cart")
        self.contador_carrito = page.get_by_test_id("cart-quantity")

    def esperar(self) -> None:
        expect(self.agregar).to_be_visible()
        expect(self.precio).not_to_be_empty()

    def valor_precio(self) -> float:
        return precio(self.precio.inner_text())

    @allure.step("Agregar {cantidad} unidad(es) al carrito")
    def agregar_al_carrito(self, cantidad: int = 1) -> None:
        for _ in range(cantidad - 1):
            self.aumentar.click()
        expect(self.cantidad).to_have_value(str(cantidad))
        self.agregar.click()
