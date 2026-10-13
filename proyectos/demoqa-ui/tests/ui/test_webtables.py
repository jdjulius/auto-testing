import pytest
from playwright.sync_api import Page, expect

from pages import Registro, WebTablesPage

REGISTRO = Registro(
    nombre="Julio", apellido="Velasquez", email="julio.velasquez@example.com",
    edad="30", salario="50000", departamento="QA",
)


@pytest.mark.escenario(
    modulo="Web Tables",
    funcionalidad="Agregar registro",
    descripcion="Completar el formulario con datos válidos y enviarlo",
    resultado_esperado="La tabla muestra una fila nueva con los datos ingresados",
    prioridad="Alta",
)
def test_agregar_registro(page: Page):
    tabla = WebTablesPage(page).abrir()
    tabla.abrir_formulario_nuevo().completar(REGISTRO).enviar_formulario()
    fila = tabla.fila_con_email(REGISTRO.email)
    expect(fila).to_contain_text(REGISTRO.nombre)
    expect(fila).to_contain_text(REGISTRO.apellido)
    expect(fila).to_contain_text(REGISTRO.departamento)


@pytest.mark.escenario(
    modulo="Web Tables",
    funcionalidad="Agregar registro",
    descripcion="Enviar el formulario con un email sin formato válido",
    resultado_esperado="El formulario no se envía: el modal permanece abierto y no se agrega ninguna fila",
    prioridad="Alta",
)
def test_agregar_registro_email_invalido(page: Page):
    tabla = WebTablesPage(page).abrir()
    filas_antes = tabla.filas.count()
    registro_invalido = Registro(
        nombre="Ana", apellido="Gomez", email="correo-sin-formato",
        edad="30", salario="1000", departamento="QA",
    )
    tabla.abrir_formulario_nuevo().completar(registro_invalido).enviar_formulario()
    expect(tabla.modal).to_be_visible()
    expect(tabla.filas).to_have_count(filas_antes)


@pytest.mark.escenario(
    modulo="Web Tables",
    funcionalidad="Editar registro",
    descripcion="Editar el apellido de un registro existente",
    resultado_esperado="La fila muestra el apellido nuevo y conserva el resto de los datos",
    prioridad="Alta",
)
def test_editar_registro(page: Page):
    tabla = WebTablesPage(page).abrir()
    tabla.abrir_formulario_nuevo().completar(REGISTRO).enviar_formulario()
    tabla.abrir_formulario_editar(REGISTRO.email)
    tabla.apellido.fill("Vega")
    tabla.enviar_formulario()
    fila = tabla.fila_con_email(REGISTRO.email)
    expect(fila).to_contain_text("Vega")
    expect(fila).not_to_contain_text(REGISTRO.apellido)


@pytest.mark.escenario(
    modulo="Web Tables",
    funcionalidad="Eliminar registro",
    descripcion="Eliminar un registro existente",
    resultado_esperado="La fila deja de estar en la tabla",
    prioridad="Alta",
)
def test_eliminar_registro(page: Page):
    tabla = WebTablesPage(page).abrir()
    tabla.abrir_formulario_nuevo().completar(REGISTRO).enviar_formulario()
    expect(tabla.fila_con_email(REGISTRO.email)).to_be_visible()
    tabla.eliminar(REGISTRO.email)
    expect(tabla.fila_con_email(REGISTRO.email)).to_have_count(0)


@pytest.mark.escenario(
    modulo="Web Tables",
    funcionalidad="Buscar",
    descripcion="Buscar por un texto que coincide con una sola fila (email)",
    resultado_esperado="Solo queda visible la fila que coincide con la búsqueda",
    prioridad="Media",
)
def test_buscar(page: Page):
    tabla = WebTablesPage(page).abrir()
    tabla.abrir_formulario_nuevo().completar(REGISTRO).enviar_formulario()
    tabla.buscar_texto(REGISTRO.email)
    expect(tabla.filas).to_have_count(1)
    expect(tabla.fila_con_email(REGISTRO.email)).to_be_visible()
