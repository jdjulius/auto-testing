# auto-testing

Pruebas automatizadas con **pytest + Playwright** sobre
[saucedemo.com](https://www.saucedemo.com/). Además de verificar que las
funcionalidades funcionan, el proyecto **levanta los escenarios de prueba y los
guarda de forma incremental en CSV**.

## Estructura

```
pages/                     Page Objects (login, inventario, carrito, checkout)
tests/ui/                  Pruebas de saucedemo
tests/framework/           Pruebas del registro de escenarios
auto_testing/registro.py   Lectura/escritura incremental de los CSV
auto_testing/plugin.py     Plugin de pytest (marcador @escenario, hooks, opciones)
reportes/escenarios.csv    Catálogo de escenarios (versionado)
reportes/ejecuciones.csv   Historial de ejecuciones (local, ignorado por git)
```

## Escenarios cubiertos

| Módulo | Escenarios |
|---|---|
| Login | login válido; usuario bloqueado, clave incorrecta, usuario inexistente, campos vacíos; acceso sin sesión; logout |
| Inventario | catálogo de 6 productos con precios; ordenar A-Z, Z-A, precio ascendente/descendente |
| Carrito | contador del carrito; quitar producto; contenido del carrito; seguir comprando |
| Checkout | compra completa; subtotal + impuesto 8% + total; campos obligatorios |

## Uso

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

pytest                       # ejecuta todo y actualiza ambos CSV
pytest tests/ui -k login     # solo un grupo
pytest --headed --slowmo 500 # ver el navegador
pytest --browser firefox     # otro navegador
pytest --collect-only        # solo levanta escenarios nuevos, sin ejecutarlos
pytest --sin-registro        # ejecuta sin tocar los CSV
```

En GitHub Actions (`.github/workflows/tests.yml`) se ejecuta todo en cada push
y los CSV, capturas y trazas de fallos se publican como artefacto `reportes`.

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
| `navegador` | navegador con el que corre (pruebas de UI) |
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
    modulo="Checkout",
    funcionalidad="Compra completa",
    descripcion="Completar una compra de punta a punta",
    resultado_esperado="Se muestra 'Thank you for your order!'",
    prioridad="Crítica",       # opcional, default "Media"
    id="CP-CHECKOUT-01",       # opcional, default autoincremental
)
def test_compra_completa(en_checkout, checkout): ...
```

El marcador es opcional: sin él se usa la primera línea del docstring como
descripción y el nombre del archivo como módulo.

> Nota: si se elimina o renombra una prueba, su fila antigua permanece en el
> catálogo con su último estado, como registro histórico.
