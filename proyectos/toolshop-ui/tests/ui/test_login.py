import re

import pytest
from playwright.sync_api import expect

import config
from pages import LoginPage


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Inicio de sesión",
    descripcion="Iniciar sesión con el usuario cliente",
    resultado_esperado="Redirige a /account con el título 'My account'",
    prioridad="Crítica",
)
def test_login_valido(page):
    login = LoginPage(page).abrir()
    login.ingresar(config.CLIENTE_EMAIL, config.CLIENTE_CLAVE)
    expect(page).to_have_url(re.compile(r"/account$"))
    expect(page.get_by_test_id("page-title")).to_have_text("My account")


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Validación",
    descripcion="Rechazar una contraseña incorrecta",
    resultado_esperado="Muestra 'Invalid email or password' y permanece en el login",
    prioridad="Alta",
)
def test_login_clave_incorrecta(page):
    login = LoginPage(page).abrir()
    login.ingresar(config.CLIENTE_EMAIL, "clave-incorrecta")
    expect(login.error).to_have_text("Invalid email or password")
    expect(page).to_have_url(re.compile(r"/auth/login$"))


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Validación",
    descripcion="Campos obligatorios del login",
    resultado_esperado="'Email is required' y 'Password is required'",
)
def test_login_campos_obligatorios(page):
    login = LoginPage(page).abrir()
    login.boton.click()
    expect(login.error_email).to_have_text("Email is required")
    expect(login.error_clave).to_have_text("Password is required")


@pytest.mark.escenario(
    modulo="Login",
    funcionalidad="Cierre de sesión",
    descripcion="Cerrar sesión desde el menú",
    resultado_esperado="Vuelve al login y el menú muestra 'Sign in'",
)
def test_logout(sesion):
    sesion.get_by_test_id("nav-menu").click()
    sesion.get_by_test_id("nav-sign-out").click()
    expect(sesion.get_by_test_id("nav-sign-in")).to_be_visible()
