from playwright.sync_api import Page


class CarritoPage:
    URL = "/cart.html"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.items = page.get_by_test_id("inventory-item")
        self.nombres = page.get_by_test_id("inventory-item-name")
        self.seguir_comprando = page.get_by_test_id("continue-shopping")
        self.checkout = page.get_by_test_id("checkout")

    def lista_nombres(self) -> list[str]:
        return self.nombres.all_inner_texts()
