---
name: levantar-escenarios
description: Levantamiento y registro incremental de escenarios de prueba en este monorepo (catálogo escenarios.csv/xlsx, IDs ESC-XXXX, historial, defectos conocidos con xfail). Úsala siempre que haya que agregar, documentar, renombrar, mover o revisar escenarios de prueba, cuando pregunten qué escenarios hay o faltan, cuando un escenario aparezca duplicado o con ID nuevo inesperado, al marcar un defecto conocido, o al tocar auto_testing/registro.py o auto_testing/plugin.py — aunque no digan "levantamiento".
---

# Levantamiento y registro de escenarios

En este repo **cada prueba de pytest es un escenario**. El plugin `auto_testing.plugin`
(en `libs/auto-testing-core/src/auto_testing/`) lo registra solo: no se edita el
catálogo a mano salvo los casos de la sección 4.

## 1. Dónde vive cada cosa

- Cada proyecto (`proyectos/<proyecto>/`) tiene su propio catálogo en
  `reportes/escenarios.csv` (+ `escenarios.xlsx`, misma información para Excel)
  y su historial en `reportes/ejecuciones.csv`.
- Los comandos se ejecutan **desde la carpeta del proyecto**: el `pytest.ini` de
  esa carpeta es la raíz, y los `nodeid` son relativos a ella.
- La clave de un escenario es su `nodeid`. El ID (`ESC-0001`…) se asigna la primera
  vez que aparece y **nunca se reutiliza**: el siguiente es el mayor existente + 1.

## 2. Documentar un escenario

Toda prueba nueva lleva el marcador; es lo que hace legible el catálogo, el PDF y Allure:

```python
@pytest.mark.escenario(
    modulo="Checkout paso 2",              # agrupación principal
    funcionalidad="Resumen Overview",      # subgrupo
    descripcion="Validar subtotal, impuesto (8%) y total",   # qué se prueba, en una línea
    resultado_esperado="Subtotal = suma de precios; impuesto = 8%; total = subtotal + impuesto",
    prioridad="Crítica",                   # Crítica | Alta | Media (default) | Baja
)
```

- `capa` (UI / API / Framework) no hace falta: sale de la carpeta (`tests/ui`, `tests/api`).
- `resultado_esperado` es el criterio de aceptación: escríbelo verificable
  ("redirige a /cart.html", "422 con error en quantity"), no "funciona bien".
- Las comas y punto y coma en los textos se guardan como ` - ` (Excel en español
  separa los CSV por `;`). Puedes escribir con comas normalmente.

**Parametrizar = varios escenarios.** Cada combinación de `@pytest.mark.parametrize`
es un escenario con la variante entre corchetes. Da siempre `ids=` legibles
(`ids=["sin-nombre", "sin-apellido"]`): son lo que se ve en el catálogo. El
navegador que agrega pytest-playwright se guarda aparte en la columna `navegador`.

## 3. Flujo para agregar escenarios

1. Escribe la prueba con su marcador (ver las skills `escenario-ui` o `escenario-api`).
2. `pytest --collect-only -q` → el resumen final muestra los IDs nuevos
   (`+ ESC-0097  …`). Revisa que **solo** aparezcan los que esperabas: un nuevo
   inesperado casi siempre significa que cambió un `nodeid` (sección 4).
3. Ejecuta (`pytest -k <nombre>` y luego todo).
4. Haz commit de `reportes/escenarios.csv` y `.xlsx` junto con la prueba.

## 4. Mover o renombrar pruebas sin perder el ID

Renombrar una función, cambiar un `ids=` o mover el archivo cambia el `nodeid`:
el registro crearía un escenario nuevo y dejaría el viejo como histórico.
Para conservar ID y contadores, **antes** de ejecutar pytest edita la columna
`nodeid` de esa fila en `reportes/escenarios.csv` con el nombre nuevo
(o hazlo con `auto_testing.registro.RegistroEscenarios` y `guardar()`, que
regenera también el Excel). No borres filas de pruebas eliminadas: son
historial, y borrarlas haría que su ID se reutilice.

## 5. Estados y defectos conocidos

| Estado | Significa |
|---|---|
| EXITOSO / FALLIDO | Pasó / falló una verificación |
| ERROR | Falló un fixture (prueba o entorno, no la app) |
| XFAIL | Defecto conocido que se reprodujo |
| XPASS | Defecto conocido no estricto que no apareció |
| OMITIDO / NO_EJECUTADO | Saltado / levantado pero aún sin correr |

Cuando una prueba descubre un **defecto real de la aplicación**:

```python
@pytest.mark.xfail(strict=True, reason="El sitio permite completar una compra sin productos")
```

- La prueba se escribe con el **comportamiento correcto** como expectativa; el
  motivo describe lo que hace hoy la app. Así, si lo corrigen, el `strict=True`
  hace fallar la prueba y avisa que hay que quitar el `xfail`.
- Usa `strict=False` solo para defectos que dependen del entorno (tiempos de carga).
- Si el defecto afecta solo a algunas variantes (usuarios, datos), márcalas con
  `pytest.param(valor, marks=pytest.mark.xfail(...))`, como `usuarios_para()` en
  `proyectos/saucedemo-ui/tests/ui/test_usuarios.py`.
- Antes de marcar un `xfail`, confirma que es la app y no la prueba: repite la
  prueba y revisa la captura o la traza. Varias veces lo que parecía un defecto era
  una prueba que leía la pantalla antes de que terminara de dibujarse.

## 6. Qué escenarios faltan

Para proponer escenarios nuevos recorre, por pantalla o recurso: caso feliz, cada
campo obligatorio, datos inválidos y límites (vacío, solo espacios, acentos, muy
largos, inyección), permisos y sesión, navegación y cancelar en cada paso, reglas de
negocio (qué **no** se debe permitir) y cada tipo de usuario o rol. La lista completa
está en `docs/ADAPTAR_A_OTRA_WEB.md` (sección "Qué escenarios levantar").
La explicación detallada del registro está en `docs/LEVANTAMIENTO_DE_ESCENARIOS.md`.
