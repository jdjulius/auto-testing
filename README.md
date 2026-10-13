# auto-testing

Monorepo de pruebas automatizadas con **pytest**. Cada proyecto (UI o API) es
independiente y todos comparten una librería que **levanta los escenarios de
prueba y los registra de forma incremental** en CSV y Excel, con historial,
reporte PDF y Allure.

> 📐 Por qué esta estructura: [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md)
> 📄 Cómo se levantan y registran los escenarios: [docs/LEVANTAMIENTO_DE_ESCENARIOS.md](docs/LEVANTAMIENTO_DE_ESCENARIOS.md)
> 🌐 Cómo agregar un proyecto para otra aplicación: [docs/ADAPTAR_A_OTRA_WEB.md](docs/ADAPTAR_A_OTRA_WEB.md)

## Estructura

```
libs/
  auto-testing-core/          Librería común (paquete Python instalable)
    src/auto_testing/           registro de escenarios, Excel, PDF, Allure
    src/auto_testing/apis/      captura de APIs consumidas por la UI (experimental)
    tests/                      pruebas de la librería
proyectos/
  saucedemo-ui/               UI de saucedemo.com (Playwright) — 145 escenarios
  toolshop-ui/                UI de practicesoftwaretesting.com (Playwright) — 22 escenarios
  toolshop-api/               API de practicesoftwaretesting.com (httpx, sin navegador) — 29 escenarios
docs/                         documentación
.github/workflows/tests.yml   CI: un job por proyecto, solo si cambió
package.json, allurerc.mjs    reporte Allure (compartido)
```

Cada proyecto tiene lo mismo:

```
proyectos/<proyecto>/
  requirements.txt     sus dependencias (instala también la librería común)
  pytest.ini           su configuración (URL, opciones)
  conftest.py          activa el plugin de escenarios
  config.py            datos y credenciales (por variables de entorno)
  pages/  o  cliente/  Page Objects (UI) o cliente HTTP y esquemas (API)
  tests/ui/ o tests/api/
  reportes/            su catálogo de escenarios, historial, PDF y Allure
```

| Proyecto | Tipo | Qué prueba | Necesita |
|---|---|---|---|
| `saucedemo-ui` | UI | login, inventario, carrito, checkout, redirecciones, pantallas, usuarios especiales, sesión y seguridad, responsive | Playwright |
| `toolshop-ui` | UI | catálogo, búsqueda, orden, categorías, detalle, carrito, login, mapa de pantallas | Playwright |
| `toolshop-api` | API | productos, paginación, búsqueda, filtros, categorías, marcas, login, perfil, permisos, facturas, carrito; esquemas JSON | httpx, jsonschema |

## Uso

Cada proyecto se instala y ejecuta **desde su carpeta**:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     Mac/Linux: source .venv/bin/activate

cd proyectos/toolshop-api
pip install -r requirements.txt       # instala la librería común + lo del proyecto
pytest                                 # ejecuta y registra los escenarios

cd ../saucedemo-ui
pip install -r requirements.txt
python -m playwright install chromium  # solo proyectos UI (o: pytest --browser-channel chrome)
pytest
```

Opciones útiles (todas las de pytest y pytest-playwright funcionan igual):

```bash
pytest --collect-only -q        # levantar escenarios nuevos sin ejecutar
pytest -k login                 # solo un grupo
pytest --headed --slowmo 500    # ver el navegador (UI)
pytest --sin-registro           # sin tocar los CSV
pytest --sin-pdf                # sin generar el PDF
```

Reporte Allure de un proyecto (desde la raíz, con Node.js instalado):

```bash
npm install
npm run reporte:toolshop-api      # o reporte:saucedemo-ui, reporte:toolshop-ui
# abre proyectos/toolshop-api/reportes/allure-report/index.html
```

## Qué genera cada proyecto

| Archivo (en `proyectos/<proyecto>/reportes/`) | Contenido | En git |
|---|---|---|
| `escenarios.csv` y `escenarios.xlsx` | Catálogo: un escenario por fila con ID, capa, módulo, funcionalidad, resultado esperado, prioridad y último estado | Sí |
| `ejecuciones.csv` | Historial de cada corrida | No |
| `reporte.pdf` | Reporte PDF de la corrida | No |
| `allure-results/`, `allure-report/` | Reporte Allure | No |

Cada catálogo tiene su propia numeración (`ESC-0001`…) y una columna **`capa`**
(`UI` o `API`) que sale de la carpeta de la prueba.

## Agregar un proyecto nuevo

1. Copia el proyecto más parecido (`toolshop-ui` para UI, `toolshop-api` para API) a `proyectos/<nuevo>/`.
2. Borra sus `tests/`, `pages/` o `cliente/`, y su `reportes/escenarios.*`.
3. Cambia la URL en `pytest.ini` y los datos en `config.py`.
4. Agrégalo a la matriz de `.github/workflows/tests.yml` y a `package.json`.

La guía completa está en [docs/ADAPTAR_A_OTRA_WEB.md](docs/ADAPTAR_A_OTRA_WEB.md).

## Defectos conocidos

Los defectos reales de las aplicaciones se marcan como `xfail(strict=True)`: quedan
como `XFAIL` en el catálogo y, si se corrigen, la prueba falla para avisar.
Saucedemo tiene 21 (usuarios especiales, una cookie forjada que da acceso, compras
con el carrito vacío, entre otros); la lista está en
`proyectos/saucedemo-ui/reportes/escenarios.xlsx` filtrando el estado `XFAIL`.

## Captura de APIs consumidas por la UI (experimental)

`auto_testing.apis` registra, durante las pruebas de UI, cada endpoint que llama
la página: método, ruta normalizada (`/products/{productId}`), parámetros,
headers, request y response enmascarados, pantalla y escenario. **Está
desactivada** (`capturar_apis = false` en `proyectos/toolshop-ui/pytest.ini`)
porque dentro de pytest la corrida no termina; está pendiente de resolver.
