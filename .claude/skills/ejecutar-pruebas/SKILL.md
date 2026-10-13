---
name: ejecutar-pruebas
description: Ejecutar las pruebas de este monorepo y revisar sus resultados — pytest por proyecto, catálogo y Excel de escenarios, PDF, reporte Allure, GitHub Actions — y resolver problemas de entorno (navegador de Playwright que no descarga o no coincide, sitio bloqueado por la red, pruebas que se cuelgan). Úsala cuando pidan correr, re-ejecutar o validar pruebas, ver resultados o reportes, revisar el CI, o cuando algo falle al ejecutar.
---

# Ejecutar pruebas y revisar resultados

## 1. Dónde y cómo

Siempre **desde la carpeta del proyecto**; su `pytest.ini` define la URL, el
catálogo y los reportes:

```bash
cd proyectos/<proyecto>                 # saucedemo-ui | toolshop-ui | toolshop-api
pip install -r requirements.txt         # la primera vez
pytest                                  # todo, registrando escenarios
pytest -k checkout                      # un grupo
pytest --collect-only -q                # levantar sin ejecutar
pytest --sin-registro --sin-pdf         # pruebas de exploración: no tocar el catálogo
pytest --headed --slowmo 500            # ver el navegador (UI)
```

La librería común se prueba con `cd libs/auto-testing-core && pytest`.

Usa `--sin-registro` mientras depuras o calibras una prueba: así el catálogo solo
recibe resultados de corridas reales.

## 2. Resultados

| Dónde (`proyectos/<p>/reportes/`) | Para qué |
|---|---|
| Resumen de la terminal | IDs nuevos (`+ ESC-…`), totales, `XFAIL` con motivo |
| `escenarios.xlsx` | Catálogo con último estado coloreado (abrir este en Excel, no el CSV) |
| `ejecuciones.csv` | Historial por corrida |
| `reporte.pdf` | Resumen por módulo y fallas que requieren atención |
| Allure | Desde la raíz: `npm run reporte:<proyecto>` → `reportes/allure-report/index.html` |

Al informar resultados, da los números reales (exitosos, fallidos, defectos
conocidos) y separa los fallos de la app de los fallos de la prueba o del entorno.
Si algo no se pudo ejecutar, dilo; no lo des por bueno.

## 3. Problemas comunes

**El navegador de Playwright no descarga (timeout en `cdn.playwright.dev`)**
- Usa el Chrome o Edge instalado: `pytest --browser-channel chrome` (o `msedge`).
- O amplía el tiempo: `PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=600000` y reintenta
  `python -m playwright install chromium`.

**`Executable doesn't exist` (la versión del navegador no coincide con la de Playwright)**
- `python -m playwright install chromium`. En entornos donde ya hay otro Chromium
  instalado y no se puede descargar, se puede apuntar Playwright a una carpeta con
  un enlace al binario existente mediante `PLAYWRIGHT_BROWSERS_PATH`, **sin escribir
  dentro de la carpeta del navegador del sistema**.

**El sitio no responde desde este entorno (proxy 403, sin red)**
- Compruébalo con `curl -sS -o /dev/null -w "%{http_code}" <url>`. Si está bloqueado,
  las pruebas no prueban nada: no inventes resultados. Pide habilitar el dominio
  (configuración de red del entorno) o ejecuta en GitHub Actions y revisa los logs
  del job.

**Una prueba pasa a veces**
- Casi siempre es una espera: se leyó la pantalla antes de que se dibujara. Repite
  la prueba 3 veces, revisa la traza y corrige la espera (skill `escenario-ui`).
  No subas timeouts a ciegas ni la marques como defecto sin confirmarlo.

**La corrida no termina (se cuelga)**
- Ejecuta con `timeout` para no quedarte esperando, y aísla: la misma prueba sin
  plugins opcionales (por ejemplo `--sin-captura-apis`), luego con cada uno. En
  Playwright síncrono, `request.response()` espera la respuesta: una conexión que no
  termina (streaming) bloquea. Si no se resuelve en un par de intentos, detente y
  explica qué se probó; no sigas lanzando corridas que se cuelgan.

## 4. CI (GitHub Actions)

`.github/workflows/tests.yml` tiene un job para la librería y uno por proyecto; cada
uno corre solo si cambió su carpeta o `libs/`. Los artefactos `reportes-<proyecto>`
traen catálogo, PDF, Allure y trazas de fallos. Para revisar un fallo, lee el log del
job (resumen final de pytest) antes de cambiar código.
