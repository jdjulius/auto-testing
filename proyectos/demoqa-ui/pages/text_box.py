import allure
from playwright.sync_api import Page


class TextBoxPage:
    URL = "/text-box"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.nombre = page.locator("#userName")
        self.email = page.locator("#userEmail")
        self.direccion_actual = page.locator("#currentAddress")
        self.direccion_permanente = page.locator("#permanentAddress")
        self.enviar = page.locator("#submit")
        self.output = page.locator("#output")
        self.output_nombre = page.locator("#output #name")
        self.output_email = page.locator("#output #email")

    @allure.step("Abrir Text Box")
    def abrir(self) -> "TextBoxPage":
        self.page.goto(self.URL)
        self.enviar.wait_for()
        return self

    @allure.step("Completar el formulario")
    def completar(self, nombre: str = "", email: str = "", actual: str = "", permanente: str = "") -> "TextBoxPage":
        if nombre:
            self.nombre.fill(nombre)
        if email:
            self.email.fill(email)
        if actual:
            self.direccion_actual.fill(actual)
        if permanente:
            self.direccion_permanente.fill(permanente)
        return self

    @allure.step("Enviar el formulario")
    def enviar_formulario(self) -> None:
        self.enviar.click()
