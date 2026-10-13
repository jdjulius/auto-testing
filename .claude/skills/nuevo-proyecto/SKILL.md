---
name: nuevo-proyecto
description: Agregar al monorepo un proyecto de pruebas nuevo para otra aplicación o capa (UI con Playwright o API con httpx) reutilizando la librería común auto-testing-core — estructura, requirements, pytest.ini, conftest, config, CI y Allure. Úsala cuando pidan probar otra página web, otra API, separar UI de API, o crear un proyecto en proyectos/, aunque digan "otro sitio" o "otra app" sin decir "proyecto".
---

# Proyecto nuevo en el monorepo

La arquitectura y su porqué están en `docs/ARQUITECTURA.md`. Resumen: la librería
común vive en `libs/auto-testing-core/` y cada proyecto en `proyectos/<app>-<capa>/`
(`-ui` o `-api`) es independiente: dependencias, configuración, catálogo y CI propios.
**No modifiques la librería para un proyecto concreto**: lo específico va en el proyecto.

## 1. Partir del proyecto más parecido

| Nuevo | Copia | Borra |
|---|---|---|
| UI | `proyectos/toolshop-ui/` | `tests/ui/test_*.py`, `pages/*.py` (salvo la idea de `mapa.py`), `reportes/` |
| API | `proyectos/toolshop-api/` | `tests/api/test_*.py`, `esquemas/*.json`, `reportes/` |

Nombre: `<app>-ui` o `<app>-api`, en minúsculas con guiones.

## 2. Archivos del proyecto

- `requirements.txt` — siempre `-e ../../libs/auto-testing-core[allure]` más lo
  propio (`pytest-playwright` para UI; `httpx` y `jsonschema` para API).
- `pytest.ini` — `testpaths = tests`, `base_url` (UI), `addopts` con
  `--alluredir=reportes/allure-results --clean-alluredir` (y `-p no:playwright` en API),
  y el marcador `escenario`.
- `conftest.py` — `pytest_plugins = ["auto_testing.plugin"]`. Es el conftest raíz del
  proyecto, por eso el plugin va aquí y no en `tests/`.
- `config.py` — URL y credenciales **por variables de entorno** (`os.environ.get`), con
  valores por defecto solo para usuarios de prueba públicos. Nunca claves reales en el código.
- UI: `tests/ui/conftest.py` con `set_test_id_attribute(...)` si el sitio usa
  `data-test`/`data-cy`, y fixtures de estado (sesión iniciada, etc.).
- API: `cliente/api.py` (copiado), `esquemas/`, `tests/api/conftest.py` con `api`,
  `token`, `api_cliente` y fixtures que crean y borran datos.

## 3. Integrarlo al monorepo

1. `.github/workflows/tests.yml`: agrega el proyecto al filtro `dorny/paths-filter`
   (su carpeta + `libs/auto-testing-core/**`) y a la matriz `proyecto` con
   `navegador: true|false`.
2. `package.json`: script `reporte:<proyecto>` igual a los existentes.
3. `README.md`: fila en la tabla de proyectos.
4. Si necesita credenciales en CI, agrégalas como *secrets* del repo y pásalas en
   el paso `pytest` como `env:`.

## 4. Verificar

```bash
cd proyectos/<proyecto>
pip install -r requirements.txt
python -m playwright install chromium     # solo UI
pytest --collect-only -q                  # debe empezar en ESC-0001
pytest
cd ../.. && npm run reporte:<proyecto>
```

Haz commit de `reportes/escenarios.csv` y `reportes/escenarios.xlsx` (los demás
archivos de `reportes/` los ignora git). Luego sigue con las skills `relevar-pantallas`,
`escenario-ui` o `escenario-api`.

Antes de probar una aplicación, confirma que hay permiso: lo ideal es un ambiente
de QA con usuarios y datos de prueba, nunca datos personales o pagos reales.
