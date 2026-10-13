from dataclasses import dataclass

import allure
from playwright.sync_api import Page


@dataclass(frozen=True)
class Registro:
    nombre: str
    apellido: str
    email: str
    edad: str
    salario: str
    departamento: str


class WebTablesPage:
    URL = "/webtables"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.agregar = page.locator("#addNewRecordButton")
        self.buscar = page.locator("#searchBox")
        self.modal = page.locator("#registration-form-modal")
        self.nombre = page.locator("#firstName")
        self.apellido = page.locator("#lastName")
        self.email = page.locator("#userEmail")
        self.edad = page.locator("#age")
        self.salario = page.locator("#salary")
        self.departamento = page.locator("#department")
        self.enviar = page.locator("#registration-form-modal #submit")
        self.filas = page.locator("table tbody tr")

    @allure.step("Abrir Web Tables")
    def abrir(self) -> "WebTablesPage":
        self.page.goto(self.URL)
        self.agregar.wait_for()
        return self

    @allure.step("Abrir el formulario de nuevo registro")
    def abrir_formulario_nuevo(self) -> "WebTablesPage":
        self.agregar.click()
        self.modal.wait_for()
        return self

    @allure.step("Abrir el formulario de edición de la fila con email '{email}'")
    def abrir_formulario_editar(self, email: str) -> "WebTablesPage":
        fila = self.page.locator("table tbody tr", has_text=email)
        fila.get_by_title("Edit").click()
        self.modal.wait_for()
        return self

    @allure.step("Completar el formulario de registro")
    def completar(self, registro: Registro) -> "WebTablesPage":
        self.nombre.fill(registro.nombre)
        self.apellido.fill(registro.apellido)
        self.email.fill(registro.email)
        self.edad.fill(registro.edad)
        self.salario.fill(registro.salario)
        self.departamento.fill(registro.departamento)
        return self

    @allure.step("Enviar el formulario de registro")
    def enviar_formulario(self) -> None:
        self.enviar.click()

    @allure.step("Eliminar la fila con email '{email}'")
    def eliminar(self, email: str) -> None:
        fila = self.page.locator("table tbody tr", has_text=email)
        fila.get_by_title("Delete").click()

    @allure.step("Buscar '{texto}'")
    def buscar_texto(self, texto: str) -> "WebTablesPage":
        self.buscar.fill(texto)
        return self

    def fila_con_email(self, email: str):
        return self.page.locator("table tbody tr", has_text=email)
