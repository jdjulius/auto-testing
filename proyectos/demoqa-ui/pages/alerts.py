import allure
from playwright.sync_api import Dialog, Page


class AlertsPage:
    URL = "/alerts"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.boton_alert = page.locator("#alertButton")
        self.boton_alert_demorado = page.locator("#timerAlertButton")
        self.boton_confirm = page.locator("#confirmButton")
        # Id real del sitio: "promt" (con error de tipeo) en vez de "prompt".
        self.boton_prompt = page.locator("#promtButton")
        self.resultado_confirm = page.locator("#confirmResult")
        self.resultado_prompt = page.locator("#promptResult")

    @allure.step("Abrir Alerts")
    def abrir(self) -> "AlertsPage":
        self.page.goto(self.URL)
        self.boton_alert.wait_for()
        return self

    @allure.step("Disparar el alert simple")
    def disparar_alert(self) -> str:
        with self.page.expect_event("dialog") as evento:
            self.boton_alert.click()
        dialogo: Dialog = evento.value
        mensaje = dialogo.message
        dialogo.accept()
        return mensaje

    @allure.step("Responder el confirm: {aceptar}")
    def responder_confirm(self, aceptar: bool) -> str:
        with self.page.expect_event("dialog") as evento:
            self.boton_confirm.click()
        dialogo: Dialog = evento.value
        mensaje = dialogo.message
        if aceptar:
            dialogo.accept()
        else:
            dialogo.dismiss()
        return mensaje

    @allure.step("Responder el prompt")
    def responder_prompt(self, texto: str) -> None:
        with self.page.expect_event("dialog") as evento:
            self.boton_prompt.click()
        dialogo: Dialog = evento.value
        dialogo.accept(texto)
