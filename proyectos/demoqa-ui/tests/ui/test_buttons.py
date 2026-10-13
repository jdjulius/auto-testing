import pytest
from playwright.sync_api import Page, expect

from pages import ButtonsPage


@pytest.mark.escenario(
    modulo="Buttons",
    funcionalidad="Tipos de clic",
    descripcion="Hacer doble clic en 'Double Click Me'",
    resultado_esperado="Se muestra el mensaje 'You have done a double click'",
    prioridad="Media",
)
def test_doble_clic(page: Page):
    botones = ButtonsPage(page).abrir()
    botones.hacer_doble_clic()
    expect(botones.mensaje_doble_clic).to_have_text("You have done a double click")


@pytest.mark.escenario(
    modulo="Buttons",
    funcionalidad="Tipos de clic",
    descripcion="Hacer clic derecho en 'Right Click Me'",
    resultado_esperado="Se muestra el mensaje 'You have done a right click'",
    prioridad="Media",
)
def test_clic_derecho(page: Page):
    botones = ButtonsPage(page).abrir()
    botones.hacer_clic_derecho()
    expect(botones.mensaje_clic_derecho).to_have_text("You have done a right click")


@pytest.mark.escenario(
    modulo="Buttons",
    funcionalidad="Tipos de clic",
    descripcion="Hacer clic simple en el botón 'Click Me' que no tiene doble clic ni clic derecho",
    resultado_esperado="Se muestra el mensaje 'You have done a dynamic click'",
    prioridad="Media",
)
def test_clic_simple(page: Page):
    botones = ButtonsPage(page).abrir()
    botones.hacer_clic_simple()
    expect(botones.mensaje_clic_simple).to_have_text("You have done a dynamic click")
