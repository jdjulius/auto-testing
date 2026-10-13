import pytest
from playwright.sync_api import Playwright


@pytest.fixture(scope="session", autouse=True)
def _atributo_test_id(playwright: Playwright) -> None:
    # Toolshop usa data-test="..." en lugar de data-testid.
    playwright.selectors.set_test_id_attribute("data-test")
