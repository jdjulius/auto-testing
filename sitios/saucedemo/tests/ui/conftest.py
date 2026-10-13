import pytest
from playwright.sync_api import Page, Playwright

from pages import CarritoPage, CheckoutPage, InventarioPage, LoginPage

CLAVE = "secret_sauce"


@pytest.fixture(scope="session", autouse=True)
def _atributo_test_id(playwright: Playwright) -> None:
    # saucedemo usa data-test="..." en lugar de data-testid.
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture
def login(page: Page) -> LoginPage:
    return LoginPage(page).abrir()


@pytest.fixture
def inventario(login: LoginPage) -> InventarioPage:
    """Sesión iniciada con standard_user, en la página de productos."""
    login.ingresar("standard_user", CLAVE)
    return InventarioPage(login.page)


@pytest.fixture
def carrito(page: Page) -> CarritoPage:
    return CarritoPage(page)


@pytest.fixture
def checkout(page: Page) -> CheckoutPage:
    return CheckoutPage(page)
