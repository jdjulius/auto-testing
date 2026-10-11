"""Pruebas del propio framework: el registro CSV debe ser incremental."""

import csv
import textwrap

import pytest

from auto_testing.registro import RegistroEscenarios


def _leer(ruta):
    with ruta.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.mark.escenario(
    modulo="Framework",
    funcionalidad="Registro CSV",
    descripcion="Asignar IDs consecutivos y no duplicar escenarios",
    resultado_esperado="ESC-0001, ESC-0002; registrar de nuevo no crea filas",
    prioridad="Alta",
)
def test_ids_incrementales(tmp_path):
    esc_csv, ej_csv = tmp_path / "e.csv", tmp_path / "x.csv"
    reg = RegistroEscenarios(esc_csv, ej_csv)
    assert reg.registrar("t::a").id == "ESC-0001"
    assert reg.registrar("t::b").id == "ESC-0002"
    reg.guardar()

    reg2 = RegistroEscenarios(esc_csv, ej_csv)
    assert reg2.registrar("t::a").id == "ESC-0001"
    assert reg2.registrar("t::c").id == "ESC-0003"
    reg2.guardar()
    assert [f["id"] for f in _leer(esc_csv)] == ["ESC-0001", "ESC-0002", "ESC-0003"]


@pytest.mark.escenario(
    modulo="Framework",
    funcionalidad="Registro CSV",
    descripcion="Corridas sucesivas agregan historial y actualizan el catálogo",
    resultado_esperado="Catálogo sin duplicados; historial crece por corrida",
    prioridad="Alta",
)
def test_corridas_sucesivas(pytester):
    pytester.makeconftest('pytest_plugins = ["auto_testing.plugin"]')
    pytester.makepyfile(
        test_demo=textwrap.dedent(
            """
            import pytest

            @pytest.mark.escenario(modulo="Demo", descripcion="pasa")
            def test_ok():
                assert True

            def test_falla():
                '''Falla a propósito'''
                assert 1 == 2
            """
        )
    )
    pytester.runpytest("-p", "no:cacheprovider").assert_outcomes(passed=1, failed=1)
    pytester.runpytest("-p", "no:cacheprovider").assert_outcomes(passed=1, failed=1)

    escenarios = _leer(pytester.path / "reportes" / "escenarios.csv")
    assert len(escenarios) == 2
    por_desc = {e["descripcion"]: e for e in escenarios}
    assert por_desc["pasa"]["ultimo_estado"] == "EXITOSO"
    assert por_desc["Falla a propósito"]["ultimo_estado"] == "FALLIDO"
    assert por_desc["Falla a propósito"]["ejecuciones"] == "2"
    assert por_desc["Falla a propósito"]["fallos"] == "2"

    ejecuciones = _leer(pytester.path / "reportes" / "ejecuciones.csv")
    assert len(ejecuciones) == 4

    # Una prueba nueva solo agrega un escenario con el siguiente ID.
    pytester.makepyfile(test_nuevo="def test_nuevo():\n    pass\n")
    pytester.runpytest("-p", "no:cacheprovider")
    escenarios = _leer(pytester.path / "reportes" / "escenarios.csv")
    assert [e["id"] for e in escenarios] == ["ESC-0001", "ESC-0002", "ESC-0003"]


@pytest.mark.escenario(
    modulo="Framework",
    funcionalidad="Levantamiento",
    descripcion="--collect-only levanta escenarios sin ejecutarlos",
    resultado_esperado="Catálogo con estado NO_EJECUTADO y sin historial",
)
def test_collect_only(pytester):
    pytester.makeconftest('pytest_plugins = ["auto_testing.plugin"]')
    pytester.makepyfile(test_demo="def test_a():\n    pass\n")
    pytester.runpytest("--collect-only", "-p", "no:cacheprovider")
    escenarios = _leer(pytester.path / "reportes" / "escenarios.csv")
    assert escenarios[0]["ultimo_estado"] == "NO_EJECUTADO"
    assert not (pytester.path / "reportes" / "ejecuciones.csv").exists()
