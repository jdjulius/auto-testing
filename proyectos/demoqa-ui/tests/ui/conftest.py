# DemoQA usa atributos "id" normales en sus componentes (no data-test/data-cy),
# así que no hace falta fijar set_test_id_attribute aquí.

import pytest
from playwright.sync_api import Page

_DOMINIOS_PUBLICIDAD = (
    "googlesyndication.com",
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "adservice.google.com",
    "ezoic.net",
    "toolsqa.com",  # banner de "Selenium Online Training" y afines
)


@pytest.fixture(autouse=True)
def _sin_publicidad(page: Page) -> None:
    """Bloquea la publicidad de DemoQA: el banner lateral se superpone a
    componentes reales (p. ej. los botones de editar/borrar en Web Tables) e
    intercepta el clic, lo que hace fallar la prueba sin que sea un defecto
    de la app bajo prueba.
    """
    page.route(
        lambda url: any(dominio in url for dominio in _DOMINIOS_PUBLICIDAD),
        lambda ruta: ruta.abort(),
    )
