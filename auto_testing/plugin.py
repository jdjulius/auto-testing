"""Plugin de pytest que levanta escenarios y registra sus resultados en CSV.

Uso en una prueba::

    @pytest.mark.escenario(
        modulo="Carrito",
        funcionalidad="Cupones",
        descripcion="Aplicar un cupón válido",
        resultado_esperado="El total refleja el 10% de descuento",
        prioridad="Alta",
    )
    def test_cupon_valido(): ...

El marcador es opcional: sin él, el escenario se documenta con el docstring
de la prueba y el nombre del archivo como módulo.
"""

from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path

import pytest

from auto_testing.registro import Ejecucion, RegistroEscenarios, ahora

_CLAVE = pytest.StashKey[RegistroEscenarios]()
_CLAVE_EJECUCIONES = pytest.StashKey[dict]()
_CLAVE_RUN = pytest.StashKey[str]()


def pytest_addoption(parser: pytest.Parser) -> None:
    grupo = parser.getgroup("auto-testing", "Registro de escenarios en CSV")
    grupo.addoption(
        "--escenarios-csv",
        default=None,
        help="Ruta del catálogo de escenarios (default: reportes/escenarios.csv)",
    )
    grupo.addoption(
        "--ejecuciones-csv",
        default=None,
        help="Ruta del historial de ejecuciones (default: reportes/ejecuciones.csv)",
    )
    grupo.addoption(
        "--sin-registro",
        action="store_true",
        default=False,
        help="No escribir los CSV de escenarios/ejecuciones",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "escenario(id=None, modulo='', funcionalidad='', descripcion='', "
        "resultado_esperado='', prioridad='Media'): documenta el escenario de prueba",
    )
    if config.getoption("--sin-registro"):
        return
    # Con pytest-xdist solo el proceso principal escribe los CSV.
    if hasattr(config, "workerinput"):
        return
    raiz = Path(config.rootpath)
    escenarios = config.getoption("--escenarios-csv") or raiz / "reportes" / "escenarios.csv"
    ejecuciones = config.getoption("--ejecuciones-csv") or raiz / "reportes" / "ejecuciones.csv"
    config.stash[_CLAVE] = RegistroEscenarios(Path(escenarios), Path(ejecuciones))
    config.stash[_CLAVE_EJECUCIONES] = {}
    config.stash[_CLAVE_RUN] = datetime.now().strftime("RUN-%Y%m%d-%H%M%S")


def _documentacion(item: pytest.Item) -> dict:
    marcador = item.get_closest_marker("escenario")
    datos = dict(marcador.kwargs) if marcador else {}
    if not datos.get("descripcion"):
        doc = inspect.getdoc(getattr(item, "function", None)) or ""
        datos["descripcion"] = doc.splitlines()[0] if doc else item.name
    if not datos.get("modulo"):
        datos["modulo"] = Path(str(item.path)).stem.removeprefix("test_")
    callspec = getattr(item, "callspec", None)
    if callspec is not None:
        # Cada combinación parametrizada es su propio escenario.
        datos["descripcion"] = f"{datos['descripcion']} [{callspec.id}]"
        if datos.get("id"):
            datos["id"] = f"{datos['id']}[{callspec.id}]"
    return datos


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    registro = config.stash.get(_CLAVE, None)
    if registro is None:
        return
    for item in items:
        registro.registrar(item.nodeid, **_documentacion(item))
    # Se guarda ya en la colección: `pytest --collect-only` sirve para
    # levantar escenarios sin ejecutarlos.
    registro.guardar()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    resultado = yield
    report = resultado.get_result()
    registro = item.config.stash.get(_CLAVE, None)
    if registro is None:
        return
    ejecuciones: dict = item.config.stash[_CLAVE_EJECUCIONES]

    estado = None
    if report.when == "setup" and report.failed:
        estado = "ERROR"
    elif report.skipped and report.when in ("setup", "call"):
        estado = "XFAIL" if hasattr(report, "wasxfail") else "OMITIDO"
    elif report.when == "call":
        if hasattr(report, "wasxfail"):
            estado = "XPASS" if report.passed else "XFAIL"
        else:
            estado = "EXITOSO" if report.passed else "FALLIDO"
    elif report.when == "teardown" and report.failed and item.nodeid in ejecuciones:
        ejecuciones[item.nodeid].estado = "ERROR"
        ejecuciones[item.nodeid].mensaje = _mensaje(report)
        return
    if estado is None:
        return

    esc = registro.escenarios.get(item.nodeid)
    if esc is None:
        return
    ejecuciones[item.nodeid] = Ejecucion(
        run_id=item.config.stash[_CLAVE_RUN],
        fecha=ahora(),
        escenario_id=esc.id,
        nodeid=item.nodeid,
        estado=estado,
        duracion_s=round(report.duration, 4),
        mensaje=_mensaje(report) if estado in ("FALLIDO", "ERROR", "OMITIDO") else "",
    )


def _mensaje(report: pytest.TestReport) -> str:
    if report.skipped and isinstance(report.longrepr, tuple):
        return str(report.longrepr[2])[:300]
    crash = getattr(report.longrepr, "reprcrash", None)
    texto = crash.message if crash is not None else str(report.longrepr or "")
    return " ".join(texto.split())[:300]


def pytest_sessionfinish(session: pytest.Session) -> None:
    config = session.config
    registro = config.stash.get(_CLAVE, None)
    if registro is None:
        return
    ejecuciones: dict = config.stash[_CLAVE_EJECUCIONES]
    for ej in ejecuciones.values():
        registro.registrar_resultado(ej.nodeid, ej.estado, ej.fecha)
    registro.guardar()
    registro.agregar_ejecuciones(list(ejecuciones.values()))


def pytest_terminal_summary(terminalreporter, config: pytest.Config) -> None:
    registro = config.stash.get(_CLAVE, None)
    if registro is None:
        return
    terminalreporter.section("auto-testing: escenarios")
    terminalreporter.write_line(
        f"Catálogo: {registro.ruta_escenarios} "
        f"({len(registro.escenarios)} escenarios, {len(registro.nuevos)} nuevos)"
    )
    for esc in registro.nuevos:
        terminalreporter.write_line(f"  + {esc.id}  {esc.descripcion}")
    terminalreporter.write_line(f"Historial: {registro.ruta_ejecuciones}")
