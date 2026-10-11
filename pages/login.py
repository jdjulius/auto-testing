import allure
from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.usuario = page.get_by_test_id("username")
        self.clave = page.get_by_test_id("password")
        self.boton = page.get_by_test_id("login-button")
        self.error = page.get_by_test_id("error")

    @allure.step("Abrir la página de login")
    def abrir(self) -> "LoginPage":
        self.page.goto("/")
        return self

    @allure.step("Iniciar sesión como '{usuario}'")
    def ingresar(self, usuario: str, clave: str) -> None:
        self.usuario.fill(usuario)
        self.clave.fill(clave)
        self.boton.click()
