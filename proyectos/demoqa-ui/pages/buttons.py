import allure
from playwright.sync_api import Page


class ButtonsPage:
    URL = "/buttons"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.doble_clic = page.locator("#doubleClickBtn")
        self.clic_derecho = page.locator("#rightClickBtn")
        # El botón "Click Me" tiene un id aleatorio distinto en cada carga de la página.
        self.clic_simple = page.get_by_role("button", name="Click Me", exact=True)
        self.mensaje_doble_clic = page.locator("#doubleClickMessage")
        self.mensaje_clic_derecho = page.locator("#rightClickMessage")
        self.mensaje_clic_simple = page.locator("#dynamicClickMessage")

    @allure.step("Abrir Buttons")
    def abrir(self) -> "ButtonsPage":
        self.page.goto(self.URL)
        self.clic_simple.wait_for()
        return self

    @allure.step("Hacer doble clic")
    def hacer_doble_clic(self) -> None:
        self.doble_clic.dblclick()

    @allure.step("Hacer clic derecho")
    def hacer_clic_derecho(self) -> None:
        self.clic_derecho.click(button="right")

    @allure.step("Hacer clic simple")
    def hacer_clic_simple(self) -> None:
        self.clic_simple.click()
