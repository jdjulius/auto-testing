# auto-testing

Proyecto de pruebas automatizadas con **pytest** que, además de verificar que
las funcionalidades de una aplicación funcionan correctamente, **levanta los
escenarios de prueba y los guarda de forma incremental en CSV**.

## Estructura

```
app/tienda.py              Aplicación bajo prueba (inventario + carrito de compras)
auto_testing/registro.py   Lectura/escritura incremental de los CSV
auto_testing/plugin.py     Plugin de pytest (marcador @escenario, hooks, opciones)
conftest.py                Activa el plugin y define fixtures
tests/                     Pruebas funcionales y del propio framework
reportes/escenarios.csv    Catálogo de escenarios (versionado)
reportes/ejecuciones.csv   Historial de ejecuciones (local, ignorado por git)
```

## Uso

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

pytest                 # ejecuta las pruebas y actualiza ambos CSV
pytest --collect-only  # solo levanta escenarios nuevos, sin ejecutarlos
pytest --sin-registro  # ejecuta sin tocar los CSV
pytest --escenarios-csv otra/ruta.csv --ejecuciones-csv otra/historial.csv
```

## Cómo funciona el registro incremental

Cada prueba que pytest descubre es un escenario (cada combinación de
`@pytest.mark.parametrize` es un escenario distinto).

**`reportes/escenarios.csv`** — catálogo, una fila por escenario:

| columna | contenido |
|---|---|
| `id` | `ESC-0001`, `ESC-0002`… asignado la primera vez que aparece la prueba (o el `id` que des en el marcador) |
| `nodeid` | identificador pytest de la prueba (clave única) |
| `modulo`, `funcionalidad`, `descripcion`, `resultado_esperado`, `prioridad` | documentación del escenario |
| `fecha_alta` | cuándo se levantó |
| `ultimo_estado`, `ultima_ejecucion` | `EXITOSO`, `FALLIDO`, `ERROR`, `OMITIDO`, `XFAIL`, `XPASS` o `NO_EJECUTADO` |
| `ejecuciones`, `fallos` | contadores acumulados |

Al agregar pruebas nuevas solo se añaden filas con el siguiente ID; las
existentes conservan su ID y su historial (no se duplican).

**`reportes/ejecuciones.csv`** — historial: en cada corrida se agrega una
fila por escenario (`run_id`, `fecha`, `escenario_id`, `estado`,
`duracion_s`, `mensaje` de error), sin reescribir las anteriores.

## Documentar un escenario

```python
@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Cupones",
    descripcion="Aplicar cupón válido",
    resultado_esperado="El total refleja el descuento antes del IVA",
    prioridad="Alta",          # opcional, default "Media"
    id="CP-CUPON-01",          # opcional, default autoincremental
)
def test_cupon_valido(carrito): ...
```

El marcador es opcional: sin él se usa la primera línea del docstring como
descripción y el nombre del archivo como módulo.

## Probar tu propia aplicación

Reemplaza `app/` por tu aplicación (o instálala como dependencia), ajusta las
fixtures de `conftest.py` y escribe pruebas en `tests/`. El plugin funciona
igual con cualquier tipo de prueba (unitarias, de API con `requests`/`httpx`,
o de UI con `pytest-playwright`).

> Nota: si se elimina o renombra una prueba, su fila antigua permanece en el
> catálogo con su último estado, como registro histórico.
