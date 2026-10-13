import re

import pytest
from playwright.sync_api import Page, expect

from pages import TextBoxPage


@pytest.mark.escenario(
    modulo="Text Box",
    funcionalidad="Completar formulario",
    descripcion="Completar los 4 campos con datos válidos y enviar",
    resultado_esperado="El resultado muestra nombre, email y ambas direcciones tal como se escribieron",
    prioridad="Alta",
)
def test_completar_formulario(page: Page):
    texto = TextBoxPage(page).abrir()
    texto.completar(
        nombre="Julio Velasquez",
        email="julio@example.com",
        actual="Av. Siempre Viva 123",
        permanente="Calle Falsa 456",
    )
    texto.enviar_formulario()
    expect(texto.output).to_contain_text("Julio Velasquez")
    expect(texto.output).to_contain_text("julio@example.com")
    expect(texto.output).to_contain_text("Av. Siempre Viva 123")
    expect(texto.output).to_contain_text("Calle Falsa 456")


@pytest.mark.escenario(
    modulo="Text Box",
    funcionalidad="Completar formulario",
    descripcion="Enviar con un email sin formato válido",
    resultado_esperado="El campo Email se marca con error y el resultado no incluye la línea de Email",
    prioridad="Alta",
)
def test_email_invalido(page: Page):
    texto = TextBoxPage(page).abrir()
    texto.completar(nombre="Julio Velasquez", email="correo-invalido")
    texto.enviar_formulario()
    expect(texto.email).to_have_class(re.compile(r"\bfield-error\b"))
    expect(texto.output_nombre).to_be_visible()
    expect(texto.output_email).to_have_count(0)


@pytest.mark.escenario(
    modulo="Text Box",
    funcionalidad="Completar formulario",
    descripcion="Enviar el formulario sin completar ningún campo",
    resultado_esperado="No se agrega ninguna línea de resultado",
    prioridad="Media",
)
def test_enviar_vacio(page: Page):
    texto = TextBoxPage(page).abrir()
    texto.enviar_formulario()
    expect(texto.output).to_be_empty()
