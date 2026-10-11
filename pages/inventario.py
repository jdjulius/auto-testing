from playwright.sync_api import Page


def slug(nombre: str) -> str:
    """'Sauce Labs Backpack' -> 'sauce-labs-backpack' (formato de los data-test)."""
    return nombre.lower().replace(" ", "-")


class InventarioPage:
    URL = "/inventory.html"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.titulo = page.get_by_test_id("title")
        self.productos = page.get_by_test_id("inventory-item")
        self.nombres = page.get_by_test_id("inventory-item-name")
        self.precios = page.get_by_test_id("inventory-item-price")
        self.orden = page.get_by_test_id("product-sort-container")
        self.badge_carrito = page.get_by_test_id("shopping-cart-badge")
        self.link_carrito = page.get_by_test_id("shopping-cart-link")
        self.menu = page.locator("#react-burger-menu-btn")
        self.logout = page.get_by_test_id("logout-sidebar-link")

    def agregar(self, nombre: str) -> None:
        self.page.get_by_test_id(f"add-to-cart-{slug(nombre)}").click()

    def quitar(self, nombre: str) -> None:
        self.page.get_by_test_id(f"remove-{slug(nombre)}").click()

    def ordenar(self, valor: str) -> None:
        self.orden.select_option(valor)

    def lista_nombres(self) -> list[str]:
        return self.nombres.all_inner_texts()

    def lista_precios(self) -> list[float]:
        return [float(p.replace("$", "")) for p in self.precios.all_inner_texts()]

    def ir_al_carrito(self) -> None:
        self.link_carrito.click()

    def cerrar_sesion(self) -> None:
        self.menu.click()
        self.logout.click()
