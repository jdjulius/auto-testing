# auto-testing

Pruebas automatizadas con **pytest + Playwright** sobre
[saucedemo.com](https://www.saucedemo.com/). Además de verificar que las
funcionalidades funcionan, el proyecto **levanta los escenarios de prueba y los
guarda de forma incremental en CSV**.

## Estructura

```
pages/                     Page Objects (login, inventario, carrito, checkout)
tests/ui/                  Pruebas de saucedemo (incluye redirecciones)
tests/framework/           Pruebas del registro de escenarios
auto_testing/registro.py   Lectura/escritura incremental de los CSV
auto_testing/plugin.py     Plugin de pytest (marcador @escenario, hooks, opciones)
auto_testing/reporte_pdf.py  Reporte PDF de la corrida
reportes/escenarios.csv    Catálogo de escenarios (versionado)
reportes/ejecuciones.csv   Historial de ejecuciones (local, ignorado por git)
reportes/reporte.pdf       Reporte PDF de la última corrida (local, ignorado por git)
```

## Escenarios cubiertos

| Módulo | Escenarios |
|---|---|
| Login | login válido; usuario bloqueado, clave incorrecta, usuario inexistente, campos vacíos; acceso sin sesión; logout |
| Inventario | catálogo de 6 productos con precios; ordenar A-Z, Z-A, precio ascendente/descendente |
| Carrito | contador del carrito; quitar producto; contenido del carrito; seguir comprando |
| Checkout | compra completa; subtotal + impuesto 8% + total; campos obligatorios |
| Redirecciones | páginas protegidas sin sesión → login; detalle de producto (por nombre e imagen) y volver; cancelar checkout paso 1 → carrito y paso 2 → inventario; "Back Home" tras la compra; menú All Items, About y Reset App State; enlaces de Twitter, Facebook y LinkedIn |
| Usuarios | login en < 3 s, imágenes, precios, ordenar por precio, agregar los 6 productos y checkout, con cada usuario del sitio |

### Defectos detectados por usuario

`tests/ui/test_usuarios.py` repite las mismas funcionalidades con
`standard_user`, `problem_user`, `performance_glitch_user`, `error_user` y
`visual_user` (`locked_out_user` se cubre en `test_login.py`). Los defectos
conocidos se marcan como `xfail` y quedan como **XFAIL** en el CSV; si un
defecto desaparece, la prueba falla (XPASS estricto) para que se revise.

| Usuario | Defectos |
|---|---|
| problem_user | imágenes repetidas, no ordena, botones "Add to cart" que no funcionan, Last Name no se conserva en el checkout |
| performance_glitch_user | login más lento que el umbral de 3 s (no estricto: depende de la carga) |
| error_user | no ordena, botones "Add to cart" que no funcionan, checkout no se completa |
| visual_user | imágenes que no corresponden, precios distintos al catálogo, lista no ordenada |

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
pytest --sin-pdf             # ejecuta sin generar el PDF
pytest --reporte-pdf otro.pdf

python -m auto_testing.reporte_pdf   # regenera el PDF de la última corrida desde los CSV
```

En GitHub Actions (`.github/workflows/tests.yml`) se ejecuta todo en cada push
y los CSV, capturas y trazas de fallos se publican como artefacto `reportes`.

## Reporte PDF

Al terminar cada corrida se genera `reportes/reporte.pdf` con:

- resumen (total, % de resultado esperado, exitosos, fallidos, defectos conocidos…);
- tabla por módulo;
- fallas que requieren atención (fallidos, errores y defectos que ya no se reproducen);
- detalle de cada escenario: ID, módulo, funcionalidad, resultado esperado,
  prioridad, estado, duración y observación (error o defecto conocido).

En GitHub Actions el PDF se publica en el artefacto `reportes`.

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
