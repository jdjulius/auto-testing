# Arquitectura: monorepo con proyectos independientes

**Estado:** aceptada · **Fecha:** 2026-10-13

## Contexto

El repositorio empezó como un solo proyecto de UI para saucedemo. Luego se sumó
una segunda aplicación (Toolshop) con pruebas de UI **y de API**. Hacía falta
decidir cómo organizar varios proyectos y tipos de prueba sin duplicar el
framework de levantamiento de escenarios.

Requisitos:

- UI y API separadas: las pruebas de API no deben depender de Playwright ni de un navegador.
- Cada proyecto con su configuración, credenciales, catálogo de escenarios y reportes.
- Un solo framework de escenarios (registro CSV/Excel, historial, PDF, Allure) para todos.
- Poder ejecutar y publicar cada proyecto por separado (local y en CI).

## Opciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A. Un proyecto con carpetas `ui/` y `api/`** | Lo más simple | Dependencias y configuración mezcladas (las APIs cargan Playwright); un solo catálogo; no se puede ejecutar ni versionar una parte sola |
| **B. Un repositorio por proyecto (polyrepo)** | Independencia total, permisos por repo | El framework se copia en cada repo y las mejoras se desincronizan; más mantenimiento |
| **C. Monorepo: proyectos independientes + librería común** ✅ | Cada proyecto con sus dependencias, configuración, catálogo y job de CI; el framework vive una sola vez; un cambio en la librería se prueba contra todos los proyectos a la vez | Hay que instalar la librería (`-e ../../libs/auto-testing-core`, incluido en cada `requirements.txt`) |

## Decisión

Opción **C**:

```
libs/auto-testing-core/     paquete Python instalable (import auto_testing)
proyectos/<app>-ui/         un proyecto por aplicación y tipo de prueba
proyectos/<app>-api/
```

- La librería es un paquete con `pyproject.toml`. Cada proyecto la instala en modo
  editable desde su `requirements.txt`, así que un cambio en `libs/` se ve al instante.
- Cada proyecto tiene `pytest.ini` propio, que es su raíz: los `nodeid`, el catálogo y
  los reportes son relativos al proyecto. Por eso mover saucedemo de lugar no cambió
  ningún ID de escenario.
- El plugin se activa de forma explícita en el `conftest.py` de cada proyecto
  (`pytest_plugins = ["auto_testing.plugin"]`), no por *entry point*: un proyecto
  solo carga lo que pide.
- El CI tiene un job para la librería y uno por proyecto; cada uno corre solo si
  cambió su carpeta o la librería, e instala solo lo suyo (sin navegador en API).

## Consecuencias

- Agregar una aplicación es copiar un proyecto de ejemplo y adaptar URL, datos,
  Page Objects o cliente y pruebas. No se toca la librería.
- Una mejora en la librería (por ejemplo, la columna `capa`) llega a todos los
  proyectos y el CI la valida contra cada uno.
- Los catálogos son independientes: cada proyecto numera sus escenarios desde
  `ESC-0001`. Para un panorama global, se combinan los `escenarios.csv` (todos tienen
  las mismas columnas).
- Si algún proyecto necesitara fijar una versión antigua de la librería, se puede
  publicar el paquete (o usar un tag de git) en vez de la ruta editable.
