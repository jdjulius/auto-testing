import pytest
from playwright.sync_api import Page, expect

from pages import AlertsPage


@pytest.mark.escenario(
    modulo="Alerts",
    funcionalidad="Alert simple",
    descripcion="Disparar el alert simple",
    resultado_esperado="El mensaje del alert es 'You clicked a button'",
    prioridad="Alta",
)
def test_alert_simple(page: Page):
    alerts = AlertsPage(page).abrir()
    mensaje = alerts.disparar_alert()
    assert mensaje == "You clicked a button"


@pytest.mark.escenario(
    modulo="Alerts",
    funcionalidad="Confirm",
    descripcion="Aceptar el confirm",
    resultado_esperado="El mensaje es 'Do you confirm action?' y el resultado 'You selected Ok'",
    prioridad="Alta",
)
def test_confirm_aceptar(page: Page):
    alerts = AlertsPage(page).abrir()
    mensaje = alerts.responder_confirm(aceptar=True)
    assert mensaje == "Do you confirm action?"
    expect(alerts.resultado_confirm).to_have_text("You selected Ok")


@pytest.mark.escenario(
    modulo="Alerts",
    funcionalidad="Confirm",
    descripcion="Cancelar el confirm",
    resultado_esperado="El resultado es 'You selected Cancel'",
    prioridad="Alta",
)
def test_confirm_cancelar(page: Page):
    alerts = AlertsPage(page).abrir()
    alerts.responder_confirm(aceptar=False)
    expect(alerts.resultado_confirm).to_have_text("You selected Cancel")


@pytest.mark.escenario(
    modulo="Alerts",
    funcionalidad="Prompt",
    descripcion="Responder el prompt con un texto",
    resultado_esperado="El resultado es 'You entered <texto>'",
    prioridad="Alta",
)
def test_prompt(page: Page):
    alerts = AlertsPage(page).abrir()
    alerts.responder_prompt("Julio")
    expect(alerts.resultado_prompt).to_have_text("You entered Julio")
