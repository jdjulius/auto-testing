import allure
from playwright.sync_api import Page


class LoginPage:
    URL = "/auth/login"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.email = page.get_by_test_id("email")
        self.clave = page.get_by_test_id("password")
        self.boton = page.get_by_test_id("login-submit")
        self.error = page.get_by_test_id("login-error")
        self.error_email = page.get_by_test_id("email-error")
        self.error_clave = page.get_by_test_id("password-error")

    @allure.step("Abrir el login")
    def abrir(self) -> "LoginPage":
        self.page.goto(self.URL)
        self.boton.wait_for()
        return self

    @allure.step("Iniciar sesión como '{email}'")
    def ingresar(self, email: str, clave: str) -> None:
        self.email.fill(email)
        self.clave.fill(clave)
        self.boton.click()
