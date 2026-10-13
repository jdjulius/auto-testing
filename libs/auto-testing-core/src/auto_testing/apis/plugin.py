"""Plugin de pytest: registra las APIs que consume la UI durante las pruebas.

Se activa por sitio en ``pytest.ini``::

    capturar_apis = true
    apis_hosts_propios =
        api.mi-aplicacion.com
    apis_excluir =
        /cdn-cgi/
    apis_pantallas = pages.mapa:pantalla_de_ruta     # opcional
    apis_openapi = https://api.mi-aplicacion.com/openapi.json   # opcional

y en ``conftest.py``: ``pytest_plugins = ["auto_testing.plugin", "auto_testing.apis.plugin"]``.
Cada prueba que usa el fixture ``page`` queda observada; al final de la corrida se
actualiza ``reportes/apis/``.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from auto_testing.apis.captura import CapturaPrueba, ConfigCaptura
from auto_testing.apis.catalogo import CatalogoApis

_CATALOGO = pytest.StashKey[CatalogoApis]()
_CONFIG = pytest.StashKey[ConfigCaptura]()


def pytest_addoption(parser: pytest.Parser) -> None:
    grupo = parser.getgroup("auto-testing-apis", "Captura de APIs consumidas por la UI")
    grupo.addoption("--capturar-apis", action="store_true", default=None,
                    help="Registrar las APIs que consume la UI (también: capturar_apis = true en pytest.ini)")
    grupo.addoption("--sin-captura-apis", action="store_true", default=False,
                    help="No registrar APIs aunque pytest.ini lo active")
    grupo.addoption("--apis-dir", default=None,
                    help="Carpeta del catálogo de APIs (default: reportes/apis)")
    parser.addini("capturar_apis", "Registrar las APIs que consume la UI", type="bool", default=False)
    parser.addini("apis_hosts_propios", "Hosts de la API propia (admite *)", type="linelist", default=[])
    parser.addini("apis_excluir", "Expresiones regulares de URLs que no se registran", type="linelist", default=[])
    parser.addini("apis_pantallas", "Función 'modulo:funcion' que da el nombre de la pantalla para una ruta", default="")
    parser.addini("apis_openapi", "URL o archivo del OpenAPI de la API propia, para comparar", default="")


def _activa(config: pytest.Config) -> bool:
    if config.getoption("--sin-captura-apis") or hasattr(config, "workerinput"):
        return False
    return bool(config.getoption("--capturar-apis") or config.getini("capturar_apis"))


def pytest_configure(config: pytest.Config) -> None:
    if not _activa(config):
        return
    resolver = None
    referencia = config.getini("apis_pantallas")
    if referencia:
        modulo, _, funcion = referencia.partition(":")
        resolver = getattr(importlib.import_module(modulo), funcion)
    config.stash[_CONFIG] = ConfigCaptura(
        hosts_propios=config.getini("apis_hosts_propios"),
        excluir=config.getini("apis_excluir"),
        resolver_pantalla=resolver,
    )
    carpeta = config.getoption("--apis-dir") or Path(config.rootpath) / "reportes" / "apis"
    config.stash[_CATALOGO] = CatalogoApis(Path(carpeta))


@pytest.fixture(autouse=True)
def _captura_apis(request: pytest.FixtureRequest):
    config = request.config
    if _CATALOGO not in config.stash or "page" not in request.fixturenames:
        yield
        return
    from auto_testing.plugin import _CLAVE, _CLAVE_RUN

    page = request.getfixturevalue("page")
    registro = config.stash.get(_CLAVE, None)
    esc = registro.escenarios.get(request.node.nodeid) if registro else None
    captura = CapturaPrueba(config.stash[_CONFIG], esc.id if esc else "", request.node.nodeid)
    captura.iniciar(page.context)
    yield
    # Este teardown corre antes de que se cierre el navegador: las respuestas siguen disponibles.
    llamadas = captura.terminar()
    catalogo = config.stash[_CATALOGO]
    run_id = config.stash.get(_CLAVE_RUN, "")
    for llamada in llamadas:
        catalogo.registrar(llamada, run_id=run_id)
    _adjuntar_allure(config, llamadas)


def _adjuntar_allure(config: pytest.Config, llamadas: list[dict]) -> None:
    if not llamadas or not getattr(config.option, "allure_report_dir", None):
        return
    try:
        import allure
    except ImportError:
        return
    resumen = [
        {"pantalla": ll["pantalla"], "tipo": ll["tipo"], "metodo": ll["request"]["metodo"],
         "url": ll["request"]["url"], "status": ll["response"]["status"],
         "duracion_ms": ll["response"]["duracion_ms"]}
        for ll in llamadas
    ]
    allure.attach(json.dumps(resumen, ensure_ascii=False, indent=2), name=f"APIs consumidas ({len(resumen)})",
                  attachment_type=allure.attachment_type.JSON)


def _cargar_openapi(referencia: str, raiz: Path) -> dict | None:
    if not referencia:
        return None
    try:
        if referencia.startswith(("http://", "https://")):
            import urllib.request

            with urllib.request.urlopen(referencia, timeout=20) as r:
                return json.load(r)
        return json.loads((raiz / referencia).read_text("utf-8"))
    except Exception as error:  # el OpenAPI es opcional: sin él no se marca 'documentado'
        print(f"\nauto-testing: no se pudo leer el OpenAPI ({error})")
        return None


def pytest_sessionfinish(session: pytest.Session) -> None:
    config = session.config
    catalogo = config.stash.get(_CATALOGO, None)
    if catalogo is None:
        return
    especificacion = _cargar_openapi(config.getini("apis_openapi"), Path(config.rootpath))
    no_documentados = no_consumidos = None
    if especificacion and catalogo.endpoints:
        no_documentados, no_consumidos = catalogo.comparar_openapi(
            especificacion, config.getini("apis_hosts_propios"))
    if catalogo.endpoints:
        catalogo.guardar(no_consumidos=no_consumidos, no_documentados=no_documentados)
    config.stash[_CATALOGO] = catalogo


def pytest_terminal_summary(terminalreporter, config: pytest.Config) -> None:
    catalogo = config.stash.get(_CATALOGO, None)
    if catalogo is None or not catalogo.endpoints:
        return
    propios = [e for e in catalogo.endpoints.values() if e.tipo == "propio"]
    terminalreporter.section("auto-testing: APIs consumidas por la UI")
    terminalreporter.write_line(
        f"Catálogo: {catalogo.ruta_csv} ({len(catalogo.endpoints)} endpoints, "
        f"{len(propios)} propios, {len(catalogo.nuevos)} nuevos)")
    for ep in catalogo.nuevos:
        terminalreporter.write_line(f"  + {ep.id}  {ep.metodo:6} {ep.ruta}  [{ep.tipo}]  {ep.pantallas}")
