# auto-testing

Pruebas automatizadas con **pytest + Playwright** sobre
[saucedemo.com](https://www.saucedemo.com/). Además de verificar que las
funcionalidades funcionan, el proyecto **levanta los escenarios de prueba y los
guarda de forma incremental en CSV**.

> 📄 Cómo funciona el levantamiento y registro de escenarios, paso a paso:
> [docs/LEVANTAMIENTO_DE_ESCENARIOS.md](docs/LEVANTAMIENTO_DE_ESCENARIOS.md)
>
> 🌐 Cómo usar este proyecto con otra página web:
> [docs/ADAPTAR_A_OTRA_WEB.md](docs/ADAPTAR_A_OTRA_WEB.md)

## Estructura

```
pages/                     Page Objects (login, inventario, carrito, checkout)
pages/mapa.py              Mapa de pantallas: ruta, título y componentes
tests/ui/                  Pruebas de saucedemo (incluye redirecciones)
tests/framework/           Pruebas del registro de escenarios
auto_testing/registro.py   Lectura/escritura incremental de los CSV
auto_testing/plugin.py     Plugin de pytest (marcador @escenario, hooks, opciones)
auto_testing/reporte_pdf.py  Reporte PDF de la corrida
auto_testing/comprobante_pdf.py  PDF de cada compra realizada en las pruebas
auto_testing/allure_integracion.py  Datos del escenario, capturas y entorno para Allure
allurerc.mjs               Configuración del reporte Allure 3
reportes/escenarios.csv    Catálogo de escenarios (versionado)
reportes/escenarios.xlsx   El mismo catálogo en Excel (versionado)
reportes/ejecuciones.csv   Historial de ejecuciones (local, ignorado por git)
reportes/reporte.pdf       Reporte PDF de la última corrida (local, ignorado por git)
reportes/compras/*.pdf     PDF de las compras de la última corrida (local, ignorado por git)
reportes/allure-results/   Resultados crudos de Allure (local, ignorado por git)
reportes/allure-report/    Reporte Allure HTML (local, ignorado por git)
```

## Escenarios cubiertos

| Módulo | Escenarios |
|---|---|
| Login | login válido; usuario bloqueado, clave incorrecta, usuario inexistente, campos vacíos; acceso sin sesión; logout |
| Inventario | catálogo de 6 productos con precios; ordenar A-Z, Z-A, precio ascendente/descendente |
| Carrito | contador del carrito; quitar producto; contenido del carrito; seguir comprando |
| Checkout | compra completa; subtotal + impuesto 8% + total; campos obligatorios |
| Redirecciones | páginas protegidas sin sesión → login; detalle de producto (por nombre e imagen) y volver; cancelar checkout paso 1 → carrito y paso 2 → inventario; "Back Home" tras la compra; menú All Items, About y Reset App State; enlaces de Twitter, Facebook y LinkedIn |
| Pantallas | ruta, título y componentes de: login, inventario, detalle, carrito, checkout paso 1, paso 2, completo y menú lateral |
| Checkout paso 1 | campos vacíos con placeholder; llenar formulario conserva valores y avanza; cerrar el error |
| Checkout paso 2 | productos, cantidades y precios; pago (SauceCard #31337) y envío (Free Pony Express); subtotal, impuesto 8% y total con 1, 3 y 6 productos |
| Checkout completo | confirmación (encabezado, texto, imagen, Back Home); Back Home vuelve al inventario vacío; **PDF de la compra** |
| Usuarios | login en < 3 s, imágenes, precios, ordenar por precio, agregar los 6 productos, checkout, abrir el detalle correcto y quitar del carrito, con cada usuario del sitio |
| Sesión y seguridad | login con Enter; usuario exacto (mayúsculas/espacios); inyección SQL/XSS; contraseña oculta; cookie de sesión; atrás tras logout; carrito entre sesiones; sin errores de JavaScript; cookie forjada; HTTP de rutas internas |
| Detalle de producto | nombre, precio, descripción e imagen de los 6 productos; agregar/quitar desde el detalle; reflejo en el inventario; id inexistente |
| Carrito y checkout (avanzado) | quitar desde el carrito; cantidades y precios; imágenes y descripciones; Reset App State; carrito vacío; orden al volver; datos en blanco, con acentos y con scripts |
| Responsive | inventario en móvil, tablet y escritorio sin scroll horizontal; compra completa en móvil |

### Defectos detectados por usuario

`tests/ui/test_usuarios.py` repite las mismas funcionalidades con
`standard_user`, `problem_user`, `performance_glitch_user`, `error_user` y
`visual_user` (`locked_out_user` se cubre en `test_login.py`). Los defectos
conocidos se marcan como `xfail` y quedan como **XFAIL** en el CSV; si un
defecto desaparece, la prueba falla (XPASS estricto) para que se revise.

| Usuario | Defectos |
|---|---|
| problem_user | imágenes repetidas, no ordena, botones "Add to cart" y "Remove" que no funcionan, abre el detalle de otro producto, Last Name no se conserva en el checkout |
| performance_glitch_user | login más lento que el umbral de 3 s (no estricto: depende de la carga) |
| error_user | no ordena, botones "Add to cart" y "Remove" que no funcionan, checkout no se completa |
| visual_user | imágenes que no corresponden, precios distintos al catálogo, lista no ordenada |

### Otros defectos del sitio (todos los usuarios)

| Defecto | Escenario |
|---|---|
| Una cookie `session-username` forjada da acceso sin contraseña | `test_sesion.py::test_cookie_forjada` |
| Las rutas internas responden HTTP 404 aunque la página se dibuja | `test_sesion.py::test_rutas_http_200` |
| Se puede completar una compra de $0.00 con el carrito vacío | `test_carrito_avanzado.py::test_checkout_carrito_vacio` |
| El checkout acepta nombre, apellido y código postal en blanco | `test_carrito_avanzado.py::test_datos_solo_espacios` |
| "Reset App State" deja los botones en "Remove" hasta recargar | `test_carrito_avanzado.py::test_reset_restablece_botones` |
| El orden elegido se pierde al volver del detalle | `test_carrito_avanzado.py::test_orden_persiste` |

## Uso

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
npm install                  # CLI de Allure 3 (solo para generar el reporte HTML)

pytest                       # ejecuta todo y actualiza ambos CSV
pytest tests/ui -k login     # solo un grupo
pytest --headed --slowmo 500 # ver el navegador
pytest --browser firefox     # otro navegador
pytest --collect-only        # solo levanta escenarios nuevos, sin ejecutarlos
pytest --sin-registro        # ejecuta sin tocar los CSV
pytest --sin-pdf             # ejecuta sin generar el PDF
pytest --reporte-pdf otro.pdf

python -m auto_testing.reporte_pdf   # regenera el PDF de la última corrida desde los CSV

npm run reporte              # genera el reporte Allure en reportes/allure-report/
npm run reporte:abrir        # lo sirve y lo abre en el navegador
```

En GitHub Actions (`.github/workflows/tests.yml`) se ejecuta todo en cada push
y los CSV, capturas y trazas de fallos se publican como artefacto `reportes`.

## Mapa de pantallas

| Pantalla | Ruta | Componentes (data-test) |
|---|---|---|
| Login | `/` | username, password, login-button, login-credentials, login-password |
| Inventario | `/inventory.html` | title, open-menu, shopping-cart-link, product-sort-container, inventory-list, inventory-item ×6, footer |
| Detalle | `/inventory-item.html?id=N` | back-to-products, inventory-item-name/desc/price, imagen, add-to-cart |
| Carrito | `/cart.html` | title, cart-list, cart-quantity-label, cart-desc-label, inventory-item, continue-shopping, checkout |
| Checkout paso 1 | `/checkout-step-one.html` | title, firstName, lastName, postalCode, cancel, continue |
| Checkout paso 2 | `/checkout-step-two.html` | title, cart-list, payment-info, shipping-info, subtotal/tax/total-label, cancel, finish |
| Checkout completo | `/checkout-complete.html` | title, pony-express, complete-header, complete-text, back-to-products (Back Home) |
| Menú lateral | (todas) | inventory-, about-, logout-, reset-sidebar-link |

El detalle completo está en `pages/mapa.py`; `tests/ui/test_pantallas.py` genera un
escenario por pantalla y, si falta algo, lista todos los componentes ausentes.

## PDF de la compra

`test_pdf_de_la_compra` completa una compra (1, 3 y 6 productos), lee el
resumen del paso 2 y genera `reportes/compras/compra-<carrito>.pdf` con
comprador, pago, envío, productos, subtotal, impuesto, total, la confirmación
y capturas de las pantallas *Overview* y *Complete!*.

## Reporte Allure

[Allure Report](https://allurereport.org/) es la alternativa en Python a Extent
Reports: dashboard con gráficos, agrupación, severidad, pasos, capturas y
adjuntos. Cada corrida de pytest escribe `reportes/allure-results/` y
`npm run reporte` genera `reportes/allure-report/`:

- `index.html`: portada con el resumen de la corrida.
- `awesome/index.html`: reporte detallado, en español, agrupado por
  **módulo → funcionalidad**. Cada escenario muestra:
  - título `ESC-XXXX · descripción` y el resultado esperado;
  - severidad según la prioridad (Crítica → blocker, Alta → critical,
    Media → normal, Baja → minor) y etiquetas con el ID y el navegador;
  - los **pasos** ejecutados (iniciar sesión, agregar al carrito, llenar datos…);
  - la **captura de pantalla** final y, en las compras, el **PDF de la compra**;
  - el error completo cuando falla.
- `dashboard/index.html`: gráficos por estado, severidad y evolución.

Los defectos conocidos (xfail) aparecen como *skipped* en la categoría
"Defectos conocidos de la aplicación". Los metadatos incluyen la aplicación,
el navegador, la versión de Python y el ID de la corrida. Cada archivo HTML es
autocontenido: se abre con doble clic, sin servidor.

En GitHub Actions el reporte se publica en el artefacto `reporte-allure`.

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
