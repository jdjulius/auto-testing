import pytest
from playwright.sync_api import Playwright


@pytest.fixture(scope="session", autouse=True)
def _atributo_test_id(playwright: Playwright) -> None:
    # Toolshop usa data-test="..." en lugar de data-testid.
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture
def catalogo(page):
    from pages import CatalogoPage

    return CatalogoPage(page).abrir()


@pytest.fixture
def sesion(page):
    """Sesión iniciada con el usuario cliente de prueba, en /account."""
    import re

    from playwright.sync_api import expect

    import config
    from pages import LoginPage

    login = LoginPage(page).abrir()
    login.ingresar(config.CLIENTE_EMAIL, config.CLIENTE_CLAVE)
    expect(page).to_have_url(re.compile(r"/account$"))
    return page
